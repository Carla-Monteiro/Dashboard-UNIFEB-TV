#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Versão: 12.0 - Recupera preenchimento automático de setor por email (nome.setor@feb.br)"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import re
import hmac
import hashlib
import requests
from functools import wraps
from datetime import datetime, timedelta, timezone, date
from zoneinfo import ZoneInfo
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

GRAPH_API = "https://graph.microsoft.com/v1.0"
SHAREPOINT_DOMAIN = "unifeb.sharepoint.com"
SITE_PATH = "/sites/SuporteDTI"
LIST_NAME = "Chamados"
LISTA_PESQUISAS = "PesquisasSatisfacao"

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')

# Senhas do Dashboard — configuradas como variável de ambiente no Render
# (Environment Variables), NUNCA no código-fonte / GitHub.
# DASHBOARD_PASSWORD = senha da administradora (acesso completo, inclusive excluir chamados).
# DASHBOARD_PASSWORD_ESTAGIARIO = senha opcional pra dar acesso a outra pessoa
# (ex: estagiário) sem revelar a senha principal. Esse papel pode ver e editar
# chamados, mas NÃO pode excluir. Se essa variável não existir/estiver vazia,
# só a senha principal funciona (comportamento igual ao de antes).
DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD')
DASHBOARD_PASSWORD_ESTAGIARIO = os.getenv('DASHBOARD_PASSWORD_ESTAGIARIO')


def _tokens_por_papel():
    """Mapeia token de sessão (sha256 da senha) -> papel ('admin' ou
    'estagiario'), a partir das senhas configuradas no ambiente. Cada senha
    configurada gera seu próprio token — assim o navegador nunca guarda a
    senha em texto puro, só o token, e ele muda sozinho se a senha mudar."""
    # Ordem importa: se por engano as duas senhas forem iguais (mesmo hash),
    # a entrada 'admin' é inserida por último e vence — igual à ordem de
    # checagem em login_dashboard() (admin checado primeiro). Assim a
    # administradora nunca fica trancada fora de uma ação por causa de uma
    # senha duplicada.
    mapa = {}
    if DASHBOARD_PASSWORD_ESTAGIARIO:
        mapa[hashlib.sha256(DASHBOARD_PASSWORD_ESTAGIARIO.encode('utf-8')).hexdigest()] = 'estagiario'
    if DASHBOARD_PASSWORD:
        mapa[hashlib.sha256(DASHBOARD_PASSWORD.encode('utf-8')).hexdigest()] = 'admin'
    return mapa


def _papel_do_token(token_enviado, tokens_validos):
    """Compara o token enviado com cada token válido usando comparação seira
    (hmac.compare_digest), devolvendo o papel correspondente ou None."""
    if not token_enviado:
        return None
    for token_valido, papel in tokens_validos.items():
        if hmac.compare_digest(token_enviado, token_valido):
            return papel
    return None


def requer_login(f):
    """Decorator: protege endpoints do Dashboard exigindo o header
    'Authorization: Bearer <token>' obtido via POST /api/login. Aceita
    qualquer papel válido (admin ou estagiario) e disponibiliza o papel em
    request.papel_usuario para quem precisar checar depois (ex: requer_admin)."""
    @wraps(f)
    def decorado(*args, **kwargs):
        if request.method == 'OPTIONS':
            return '', 200

        tokens_validos = _tokens_por_papel()
        if not tokens_validos:
            logger.error("❌ Nenhuma senha do Dashboard configurada no ambiente (Render)")
            return jsonify({"status": "erro", "mensagem": "Login não configurado no servidor"}), 500

        auth_header = request.headers.get('Authorization', '')
        token_enviado = auth_header.replace('Bearer ', '').strip()
        papel = _papel_do_token(token_enviado, tokens_validos)

        if not papel:
            return jsonify({"status": "erro", "mensagem": "Não autorizado. Faça login novamente."}), 401

        request.papel_usuario = papel
        return f(*args, **kwargs)
    return decorado


def requer_admin(f):
    """Como requer_login, mas além de exigir login válido, exige o papel
    'admin' — bloqueia o papel 'estagiario'. Usado em ações irreversíveis
    como excluir chamado."""
    @requer_login
    @wraps(f)
    def decorado(*args, **kwargs):
        if request.method == 'OPTIONS':
            return '', 200
        if getattr(request, 'papel_usuario', None) != 'admin':
            return jsonify({"status": "erro", "mensagem": "Ação disponível apenas para o administrador."}), 403
        return f(*args, **kwargs)
    return decorado

NOMES_SETORES = {
    'manutencao': 'Manutenção Predial',
    'naem': 'Multimídia (NAEM)',
    'ti': 'TI / Internet'
}

# Mapeamento usado para PREENCHER AUTOMATICAMENTE o Setor de Atendimento
# quando um chamado chega sem esse campo definido (ex: chamados abertos
# por e-mail, cujo endereço segue o padrão nome.setor@feb.br)
EMAIL_SETOR_MAPPING = {
    'almoxarifado': 'Almoxarifado',
    'biblioteca': 'Biblioteca',
    'coordenacao': 'Coordenação de Professores',
    'clinica': 'Clínica Odontológica',
    'colegio': 'Colégio FEB',
    'dti': 'Departamento de Tecnologia',
    'matricula': 'Matrícula',
    'coordenacao_lab': 'Coordenação Laboratórios',
    'laboratorio': 'Coordenação Laboratórios',
    'manutencao': 'Manutenção',
    'cpa': 'Comissão Própria de Avaliação (CPA)',
    'neu': 'NEU',
    'marketing': 'Marketing',
    'nape': 'NAPE',
    'npj': 'Núcleo Práticas Jurídicas',
    'financeiro': 'Atendimento Financeiro',
    'pradm': 'PRADM',
    'dejur': 'Departamento Jurídico - DEJUR',
    'proaluno': 'Pró Aluno',
    'reitoria': 'Reitoria',
    'rh': 'RH',
    'secretaria': 'Secretaria',
    'conselho': 'Conselho Curador',
    'clivet': 'Clínica Medicina Veterinária',
    'sala_professor': 'Sala Atendimento Professor ao Aluno',
    'cartorio': 'Cartório - Núcleo Práticas Jurídicas',
    'sala_professores': 'Sala dos Professores',
    'ouvidoria': 'Ouvidoria',
    'sustentabilidade': 'Núcleo de Sustentabilidade',
    'labinfo': 'Laboratórios de Informática',
    'fisio': 'Clínica de Fisioterapia',
    'nac': 'NAC',
}

CATEGORIAS_ROTEAMENTO = {
    '💡 Energia Elétrica': {'tipo': 'manutencao'},
    '❄️ Ar Condicionado': {'tipo': 'manutencao'},
    '🔐 Fechadura/Porta': {'tipo': 'manutencao'},
    '🪟 Janela': {'tipo': 'manutencao'},
    '🔘 Interruptores': {'tipo': 'manutencao'},
    '🚪 Outra': {'tipo': 'manutencao'},
    '📽️ Projetor': {'tipo': 'naem'},
    '🎮 Controle Projetor': {'tipo': 'naem'},
    '📺 Cabo VGA': {'tipo': 'naem'},
    '🔌 Adaptador VGA/HDMI': {'tipo': 'naem'},
    '📡 Cabo HDMI': {'tipo': 'naem'},
    '🔊 Cabos de Som': {'tipo': 'naem'},
    '❄️ Controle A/C': {'tipo': 'naem'},
    '📻 Outro': {'tipo': 'naem'},
    '🌐 TI / Internet': {'tipo': 'ti'},
    '💻 Computador': {'tipo': 'ti'},
    '⌨️ Teclado': {'tipo': 'ti'},
    '🖱️ Mouse': {'tipo': 'ti'},
    '📞 Telefone': {'tipo': 'ti'},
    '🔴 Outro': {'tipo': 'ti'},
}

def get_access_token():
    try:
        url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json().get('access_token')
        logger.error(f"Erro ao obter token: {response.text}")
        return None
    except Exception as e:
        logger.error(f"Exceção: {e}")
        return None

def gerar_numero_chamado():
    return datetime.now().strftime('%Y%m%d%H%M%S')

def obter_roteamento(categoria):
    if categoria in CATEGORIAS_ROTEAMENTO:
        return CATEGORIAS_ROTEAMENTO[categoria]
    return {'tipo': 'ti'}

def obter_site_e_lista(headers, nome_lista=None):
    """Helper: retorna (site_id, list_id) ou (None, None) em caso de erro.
    Se nome_lista não for informado, usa a lista padrão 'Chamados'."""
    lista = nome_lista or LIST_NAME
    site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
    site_response = requests.get(site_url, headers=headers, timeout=10)
    if site_response.status_code != 200:
        logger.error(f"❌ Erro ao conectar site: {site_response.status_code}")
        return None, None
    site_id = site_response.json().get('id')

    list_url = f"{GRAPH_API}/sites/{site_id}/lists/{lista}"
    list_response = requests.get(list_url, headers=headers, timeout=10)
    if list_response.status_code != 200:
        logger.error(f"❌ Erro ao conectar lista '{lista}': {list_response.status_code}")
        return None, None
    list_id = list_response.json().get('id')

    return site_id, list_id

@app.route('/api/criar-manutencao', methods=['POST', 'OPTIONS'])
def criar_manutencao():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info("INICIANDO criar_manutencao")
        
        data = request.json
        email = data.get('email', '').strip()
        bloco = data.get('bloco', '').strip()
        sala = data.get('sala', '').strip()
        tipo = data.get('tipo', '').strip()
        categoria = data.get('categoria', '').strip()
        descricao = data.get('descricao', '').strip()
        
        if not all([email, bloco, sala, tipo, categoria, descricao]):
            return jsonify({"status": "erro", "mensagem": "Campos obrigatórios faltando"}), 400
        
        roteamento = obter_roteamento(categoria)
        tipo_problema = roteamento['tipo']
        solicitante = email.split('@')[0].replace('.', ' ').title()
        
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Falha ao conectar SharePoint"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        
        site_id, list_id = obter_site_e_lista(headers)
        if not site_id or not list_id:
            return jsonify({"status": "erro", "mensagem": "Erro ao conectar SharePoint"}), 400
        
        create_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items"
        
        # Usar fuso horário de São Paulo (UTC-3/-2)
        tz_sp = ZoneInfo('America/Sao_Paulo')
        agora = datetime.now(tz=tz_sp)
        # Converter para UTC para enviar ao SharePoint
        agora_utc = agora.astimezone(timezone.utc)
        data_abertura_iso = agora_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        payload = {
            "fields": {
                "Title": f"{categoria} - {bloco}/{sala}",
                "Descricao": descricao,
                "Solicitante": solicitante,
                "Email": email,
                "Bloco": bloco,
                "Sala": sala,
                "Categoria": categoria,
                "SetordeAtendimento": NOMES_SETORES.get(tipo_problema, 'Geral'),
                "Prioridade": "Média",
                "Status": "Aberto",
                "Origem": "QR Code",
                "DataAbertura": data_abertura_iso,
                "Historico": json.dumps([montar_entrada_historico("Chamado aberto")], ensure_ascii=False)
            }
        }
        
        response = requests.post(create_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code not in [200, 201]:
            logger.error(f"❌ Erro ao criar item: {response.status_code} - {response.text}")
            return jsonify({"status": "erro", "mensagem": "Erro ao salvar"}), 400
        
        # Captura o ID real do item criado no SharePoint (usado como "número do chamado")
        item_criado = response.json()
        numero = item_criado.get('id', '')
        
        # Grava o NumeroChamado formatado (ex: CH-0995) de volta no item
        try:
            numero_formatado = f"CH-{int(numero):04d}"
            update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{numero}"
            requests.patch(
                update_url,
                headers=headers,
                json={"fields": {"NumeroChamado": numero_formatado}},
                timeout=10
            )
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível gravar NumeroChamado: {e}")
        
        logger.info(f"✅ Chamado #{numero} criado com sucesso")
        return jsonify({
            "status": "sucesso",
            "mensagem": "✅ Aviso enviado com sucesso!",
            "numero": numero
        }), 201
        
    except Exception as e:
        logger.error(f"ERRO em criar_manutencao: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

def extrair_setor_do_email(email):
    """Extrai o setor baseado no padrão do email (nome.setor@feb.br)"""
    try:
        if not email:
            return None

        email_lower = email.lower().strip()
        if '@' not in email_lower or '.' not in email_lower:
            return None

        parte_email = email_lower.split('@')[0]
        departamento_sigla = parte_email.split('.')[-1]

        setor = EMAIL_SETOR_MAPPING.get(departamento_sigla)
        if setor:
            logger.info(f"✅ Setor extraído do email '{email}': {setor}")
        return setor

    except Exception as e:
        logger.warning(f"⚠️ Erro ao extrair setor do email '{email}': {e}")
        return None


def preencher_setores_faltantes(items, headers, site_id, list_id):
    """Detecta chamados sem 'SetordeAtendimento' e preenche automaticamente
    com base no padrão do e-mail (nome.setor@feb.br). Atualiza no SharePoint
    e retorna um dict {item_id: setor_novo} para refletir na resposta atual
    sem precisar esperar a próxima consulta."""
    setores_preenchidos = {}
    try:
        for item in items:
            item_id = item.get('id')
            fields = item.get('fields', {})
            setor_atual = (fields.get('SetordeAtendimento') or '').strip()
            email = (fields.get('Email') or '').strip()

            if not setor_atual and email:
                setor_novo = extrair_setor_do_email(email)
                if setor_novo:
                    update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
                    update_response = requests.patch(
                        update_url,
                        headers=headers,
                        json={"fields": {"SetordeAtendimento": setor_novo}},
                        timeout=10
                    )
                    if update_response.status_code in [200, 204]:
                        logger.info(f"✅ Setor preenchido automaticamente para chamado #{item_id}: {setor_novo}")
                        setores_preenchidos[item_id] = setor_novo
                    else:
                        logger.warning(f"⚠️ Falha ao preencher setor do chamado #{item_id}: {update_response.status_code}")
    except Exception as e:
        logger.error(f"❌ Erro em preencher_setores_faltantes: {e}")

    return setores_preenchidos


@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login_dashboard():
    """Login do Dashboard. Recebe {"senha": "..."} e devolve um token de
    sessão (derivado da senha) e o papel correspondente ('admin' ou
    'estagiario'), pra usar no header Authorization das próximas chamadas.
    As senhas corretas ficam só nas variáveis de ambiente DASHBOARD_PASSWORD
    e DASHBOARD_PASSWORD_ESTAGIARIO do Render — nunca no código."""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.json or {}
        senha_enviada = str(data.get('senha', ''))

        if not DASHBOARD_PASSWORD and not DASHBOARD_PASSWORD_ESTAGIARIO:
            logger.error("❌ Nenhuma senha do Dashboard configurada no ambiente (Render)")
            return jsonify({"status": "erro", "mensagem": "Login não configurado no servidor"}), 500

        papel = None
        if senha_enviada and DASHBOARD_PASSWORD and hmac.compare_digest(senha_enviada, DASHBOARD_PASSWORD):
            papel = 'admin'
        elif senha_enviada and DASHBOARD_PASSWORD_ESTAGIARIO and hmac.compare_digest(senha_enviada, DASHBOARD_PASSWORD_ESTAGIARIO):
            papel = 'estagiario'

        if not papel:
            return jsonify({"status": "erro", "mensagem": "Senha incorreta"}), 401

        token = hashlib.sha256(senha_enviada.encode('utf-8')).hexdigest()
        return jsonify({"status": "sucesso", "token": token, "papel": papel}), 200

    except Exception as e:
        logger.error(f"❌ ERRO em login_dashboard: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro ao processar login"}), 500


def parse_historico(bruto):
    """Converte o texto JSON guardado no campo 'Historico' do SharePoint em
    uma lista de eventos [{texto, data}, ...]. Tolera campo vazio/ausente
    (lista ainda sem essa coluna) e JSON inválido, devolvendo lista vazia."""
    if not bruto:
        return []
    try:
        eventos = json.loads(bruto)
        return eventos if isinstance(eventos, list) else []
    except Exception:
        return []


def montar_entrada_historico(texto):
    tz_sp = ZoneInfo('America/Sao_Paulo')
    return {"texto": texto, "data": datetime.now(tz=tz_sp).isoformat()}


def limitar_historico(lista, maximo=20):
    """Mantém só os N eventos mais recentes do histórico antes de gravar no
    SharePoint. Evita que o campo cresça sem limite pra sempre — o que mais
    cedo ou mais tarde estoura o tamanho máximo da coluna (e estoura BEM
    cedo, com poucos eventos, se a coluna 'Historico' tiver sido criada como
    'Uma linha de texto', que tem limite de só 255 caracteres, em vez de
    'Várias linhas de texto')."""
    if not isinstance(lista, list):
        return []
    return lista[-maximo:]


def extrair_erro_graph(response):
    """Tenta extrair uma mensagem de erro legível da resposta da Microsoft
    Graph API (SharePoint), pra devolver pro Dashboard um motivo mais claro
    do que só "Erro ao salvar" — por exemplo, um campo que estourou o
    tamanho máximo da coluna. Se não conseguir entender a resposta, devolve
    string vazia (o chamador mantém a mensagem genérica)."""
    try:
        corpo = response.json()
        return (corpo.get('error') or {}).get('message', '') or ''
    except Exception:
        return ''


def extrair_id_numerico(numero):
    """Extrai o ID numérico do SharePoint a partir de um número de chamado
    no formato 'CH-0123' (ou já numérico). Mesma lógica usada no rastreador."""
    if not numero:
        return None
    numero = str(numero).strip()
    numero = re.sub(r'^CH-', '', numero, flags=re.IGNORECASE)
    numero = re.sub(r'^0+(?=\d)', '', numero)
    return numero or None


@app.route('/api/chamado/<numero>', methods=['GET'])
def obter_chamado_unico(numero):
    """Endpoint PÚBLICO usado pela página de rastreamento (rastreador.html).
    Devolve os dados de UM ÚNICO chamado (por número) — nunca a lista
    completa. Não exige login, pois o link já é enviado só para quem abriu
    aquele chamado, mas por isso mesmo devolve apenas o necessário para a
    tela de acompanhamento (sem solicitante/e-mail/bloco/sala/categoria)."""
    try:
        item_id = extrair_id_numerico(numero)
        if not item_id:
            return jsonify({"status": "erro", "mensagem": "Número inválido"}), 400

        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Falha ao conectar SharePoint"}), 401

        headers = {'Authorization': f'Bearer {token}'}
        site_id, list_id = obter_site_e_lista(headers)
        if not site_id or not list_id:
            return jsonify({"status": "erro", "mensagem": "Erro ao conectar SharePoint"}), 400

        item_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}?$expand=fields"
        item_response = requests.get(item_url, headers=headers, timeout=10)

        if item_response.status_code != 200:
            return jsonify({"status": "erro", "mensagem": "Chamado não encontrado"}), 404

        fields = item_response.json().get('fields', {})

        chamado = {
            'numero': fields.get('NumeroChamado') or f"CH-{int(item_id):04d}",
            'titulo': fields.get('Title', ''),
            'status': fields.get('Status', 'Aberto'),
            'prioridade': fields.get('Prioridade', 'Média'),
            'descricao': fields.get('Descricao', ''),
            'dataAbertura': fields.get('DataAbertura', ''),
        }
        return jsonify({"status": "sucesso", "chamado": chamado}), 200

    except Exception as e:
        logger.error(f"❌ ERRO em obter_chamado_unico: {e}")
        return jsonify({"status": "erro", "mensagem": "Chamado não encontrado"}), 404


@app.route('/api/chamados', methods=['GET'])
@requer_login
def obter_chamados():
    """Retorna lista de todos os chamados do SharePoint"""
    try:
        token = get_access_token()
        if not token:
            return jsonify([]), 200
        
        headers = {'Authorization': f'Bearer {token}'}
        site_id, list_id = obter_site_e_lista(headers)
        if not site_id or not list_id:
            return jsonify([]), 200
        
        items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields"
        items_response = requests.get(items_url, headers=headers, timeout=10)
        
        if items_response.status_code != 200:
            return jsonify([]), 200
        
        items = items_response.json().get('value', [])

        # Preenche automaticamente o setor de chamados que chegaram sem esse
        # campo (tipicamente chamados abertos por e-mail, ex: carla.dti@feb.br)
        setores_preenchidos = preencher_setores_faltantes(items, headers, site_id, list_id)
        
        chamados = []
        for item in items:
            fields = item.get('fields', {})
            item_id = item.get('id')
            setor = fields.get('SetordeAtendimento', '') or setores_preenchidos.get(item_id, '')
            chamado = {
                'id': item_id,
                'titulo': fields.get('Title', ''),
                'solicitante': fields.get('Solicitante', ''),
                'email': fields.get('Email', ''),
                'status': fields.get('Status', 'Aberto'),
                'prioridade': fields.get('Prioridade', 'Normal'),
                'dataAbertura': fields.get('DataAbertura', datetime.now().isoformat()),
                'descricao': fields.get('Descricao', ''),
                'bloco': fields.get('Bloco', ''),
                'sala': fields.get('Sala', ''),
                'categoria': fields.get('Categoria', ''),
                'setor': setor,
                'setorAtendimento': setor,
                'numeroChamado': fields.get('NumeroChamado', ''),
                'data': fields.get('DataAbertura', datetime.now().isoformat()),
                # Campos novos (Responsável / Histórico). Se a coluna ainda não
                # existir na lista do SharePoint, 'fields.get' simplesmente
                # devolve o padrão — nada quebra até a coluna ser criada.
                'responsavel': fields.get('Responsavel', ''),
                'historico': parse_historico(fields.get('Historico')),
                # 'Origem' identifica como o chamado foi aberto ('QR Code',
                # 'Dashboard', ou vazio pra chamados que chegam por e-mail via
                # automação — ver comentário acima sobre setor preenchido
                # automaticamente pra esses mesmos chamados).
                'origem': fields.get('Origem', ''),
            }
            chamados.append(chamado)
        
        logger.info(f"✅ {len(chamados)} chamados retornados")
        return jsonify(chamados), 200
        
    except Exception as e:
        logger.error(f"ERRO em obter_chamados: {e}")
        return jsonify([]), 200

def pagina_confirmacao(sucesso, mensagem, item_id=None):
    """Gera uma página HTML simples e bonita de confirmação/erro,
    usada como retorno visual ao clicar no botão 'Marcar como Resolvido'."""
    cor_principal = "#00c864" if sucesso else "#ff6464"
    icone = "✅" if sucesso else "⚠️"
    titulo = "Chamado Concluído!" if sucesso else "Ops, algo deu errado"
    subtitulo = f"Chamado #{item_id} foi marcado como concluído com sucesso." if sucesso else mensagem

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>#SuporteUNIFEB</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #1a2a5e 0%, #2a3a7e 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .card {{
                background: #fff;
                border-radius: 16px;
                padding: 50px 40px;
                max-width: 420px;
                width: 100%;
                text-align: center;
                box-shadow: 0 20px 50px rgba(0,0,0,0.3);
            }}
            .icone {{
                font-size: 64px;
                margin-bottom: 20px;
            }}
            .titulo {{
                font-size: 24px;
                font-weight: bold;
                color: {cor_principal};
                margin-bottom: 12px;
            }}
            .subtitulo {{
                font-size: 15px;
                color: #555;
                line-height: 1.5;
                margin-bottom: 25px;
            }}
            .rodape {{
                font-size: 12px;
                color: #999;
                border-top: 1px solid #eee;
                padding-top: 18px;
                margin-top: 10px;
            }}
            .fechar-aviso {{
                font-size: 13px;
                color: #888;
                margin-top: 8px;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icone">{icone}</div>
            <div class="titulo">{titulo}</div>
            <div class="subtitulo">{subtitulo}</div>
            <div class="fechar-aviso">Você já pode fechar esta aba.</div>
            <div class="rodape">Sistema #SuporteUNIFEB &bull; Gerenciamento em Tempo Real</div>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/api/concluir-chamado', methods=['GET', 'OPTIONS'])
def concluir_chamado():
    """Conclui um chamado e retorna uma página HTML de confirmação (amigável para clique em email).
    Aceita DOIS modos:
      - ?id=123        -> atualiza DIRETO o item pelo ID do SharePoint (recomendado / usado pelo QR Code)
      - ?numero=XXXX   -> procura pelo número embutido no Title (modo antigo / e-mail dos funcionários)
    Para integrações que precisam de JSON puro, adicione ?formato=json na URL.
    """
    if request.method == 'OPTIONS':
        return '', 200

    quer_json = request.args.get('formato') == 'json'

    try:
        item_id_direto = request.args.get('id')
        numero = request.args.get('numero')

        if not item_id_direto and not numero:
            logger.warning("❌ Nem 'id' nem 'numero' foram informados")
            if quer_json:
                return jsonify({"status": "erro", "mensagem": "Informe 'id' ou 'numero'"}), 400
            return pagina_confirmacao(False, "Informe o número do chamado."), 400

        token = get_access_token()
        if not token:
            logger.error("❌ Falha ao obter token")
            if quer_json:
                return jsonify({"status": "erro", "mensagem": "Falha ao conectar"}), 401
            return pagina_confirmacao(False, "Falha ao conectar com o SharePoint."), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        
        site_id, list_id = obter_site_e_lista(headers)
        if not site_id or not list_id:
            if quer_json:
                return jsonify({"status": "erro", "mensagem": "Erro ao conectar SharePoint"}), 400
            return pagina_confirmacao(False, "Erro ao conectar com o SharePoint."), 400

        # ===== MODO 1: ID direto do SharePoint (usado pelo QR Code) =====
        if item_id_direto:
            item_id = item_id_direto
            logger.info(f"🔄 Concluindo chamado por ID direto: {item_id}")
        # ===== MODO 2: busca por número embutido no Title (usado pelo e-mail) =====
        else:
            logger.info(f"🔄 Processando conclusão do chamado #{numero} (busca por Title)")
            query_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$filter=contains(fields/Title, '{numero}')"
            query_response = requests.get(query_url, headers=headers, timeout=10)
            if query_response.status_code != 200:
                logger.error(f"❌ Erro na query: {query_response.status_code}")
                if quer_json:
                    return jsonify({"status": "erro", "mensagem": "Erro ao procurar chamado"}), 400
                return pagina_confirmacao(False, "Erro ao procurar o chamado."), 400
            
            items = query_response.json().get('value', [])
            if not items:
                logger.warning(f"❌ Chamado #{numero} não encontrado")
                if quer_json:
                    return jsonify({"status": "erro", "mensagem": "Chamado não encontrado"}), 404
                return pagina_confirmacao(False, "Chamado não encontrado."), 404
            
            item = items[0]
            item_id = item.get('id')

        logger.info(f"✅ Atualizando chamado ID={item_id}")

        # Busca o histórico atual para acrescentar o novo evento sem apagar
        # os anteriores (se a coluna 'Historico' ainda não existir, retorna
        # vazio e seguimos normalmente).
        historico_atual = []
        try:
            item_atual_response = requests.get(
                f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}?$expand=fields",
                headers=headers, timeout=10
            )
            if item_atual_response.status_code == 200:
                historico_atual = parse_historico(item_atual_response.json().get('fields', {}).get('Historico'))
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível ler histórico atual do chamado #{item_id}: {e}")

        historico_atual.append(montar_entrada_historico("Chamado concluído"))

        update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
        update_payload = {"fields": {
            "Status": "Concluído",
            "Historico": json.dumps(limitar_historico(historico_atual), ensure_ascii=False)
        }}

        update_response = requests.patch(update_url, headers=headers, json=update_payload, timeout=10)
        
        if update_response.status_code not in [200, 204]:
            logger.error(f"❌ Erro ao atualizar: {update_response.status_code}")
            if quer_json:
                return jsonify({"status": "erro", "mensagem": "Erro ao atualizar chamado"}), 400
            return pagina_confirmacao(False, "Erro ao atualizar o chamado no SharePoint."), 400
        
        logger.info(f"✅ Chamado ID={item_id} concluído com sucesso!")
        
        if quer_json:
            return jsonify({
                "status": "sucesso",
                "mensagem": "✅ Chamado concluído com sucesso!",
                "id": item_id,
                "timestamp": datetime.now().isoformat()
            }), 200

        return pagina_confirmacao(True, "", item_id), 200
        
    except Exception as e:
        logger.error(f"❌ ERRO em concluir_chamado: {e}")
        if quer_json:
            return jsonify({"status": "erro", "mensagem": str(e)}), 500
        return pagina_confirmacao(False, "Ocorreu um erro inesperado. Tente novamente."), 500


# ============================================================
# ✅ NOVOS ENDPOINTS - Usados pelo Dashboard (index.html)
# ============================================================

@app.route('/api/criar-chamado', methods=['POST', 'OPTIONS'])
@requer_login
def criar_chamado_dashboard():
    """Cria um chamado manualmente pelo Dashboard"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.json
        titulo = data.get('titulo', '').strip()
        descricao = data.get('descricao', '').strip()
        solicitante = data.get('solicitante', '').strip()
        email = data.get('email', '').strip()
        setor = data.get('setor', '').strip()
        prioridade = data.get('prioridade', 'Média').strip()

        if not titulo or not solicitante or not setor:
            return jsonify({"status": "erro", "mensagem": "Campos obrigatórios faltando"}), 400

        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Falha ao conectar SharePoint"}), 401

        headers = {'Authorization': f'Bearer {token}'}
        site_id, list_id = obter_site_e_lista(headers)
        if not site_id or not list_id:
            return jsonify({"status": "erro", "mensagem": "Erro ao conectar SharePoint"}), 400

        create_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items"

        # Usar fuso horário de São Paulo (UTC-3/-2)
        tz_sp = ZoneInfo('America/Sao_Paulo')
        agora = datetime.now(tz=tz_sp)
        # Converter para UTC para enviar ao SharePoint
        agora_utc = agora.astimezone(timezone.utc)
        data_abertura_iso = agora_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

        payload = {
            "fields": {
                "Title": titulo,
                "Descricao": descricao,
                "Solicitante": solicitante,
                "Email": email,
                "SetordeAtendimento": setor,
                "Prioridade": prioridade,
                "Status": "Aberto",
                "Origem": "Dashboard",
                "DataAbertura": data_abertura_iso,
                "Historico": json.dumps([montar_entrada_historico("Chamado aberto")], ensure_ascii=False)
            }
        }

        response = requests.post(create_url, headers=headers, json=payload, timeout=10)

        if response.status_code not in [200, 201]:
            logger.error(f"❌ Erro ao criar: {response.status_code} - {response.text}")
            detalhe = extrair_erro_graph(response)
            mensagem = "Erro ao salvar no SharePoint" + (f": {detalhe}" if detalhe else "")
            return jsonify({"status": "erro", "mensagem": mensagem}), 400

        item_criado = response.json()
        novo_id = item_criado.get('id', '')
        try:
            numero_formatado = f"CH-{int(novo_id):04d}"
            update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{novo_id}"
            requests.patch(
                update_url,
                headers=headers,
                json={"fields": {"NumeroChamado": numero_formatado}},
                timeout=10
            )
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível gravar NumeroChamado: {e}")

        logger.info(f"✅ Chamado '{titulo}' criado via Dashboard")
        return jsonify({"status": "sucesso", "mensagem": "✅ Chamado criado com sucesso!"}), 201

    except Exception as e:
        logger.error(f"❌ ERRO em criar_chamado_dashboard: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@app.route('/api/editar-chamado/<item_id>', methods=['PATCH', 'OPTIONS'])
@requer_login
def editar_chamado(item_id):
    """Edita um chamado existente pelo Dashboard (usa o ID direto do SharePoint)"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.json
        logger.info(f"🔄 Editando chamado ID={item_id} | dados={data}")

        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Falha ao conectar SharePoint"}), 401

        headers = {'Authorization': f'Bearer {token}'}
        site_id, list_id = obter_site_e_lista(headers)
        if not site_id or not list_id:
            return jsonify({"status": "erro", "mensagem": "Erro ao conectar SharePoint"}), 400

        # Monta apenas os campos que vieram preenchidos
        campos = {}
        if 'titulo' in data and data['titulo']:
            campos['Title'] = data['titulo']
        if 'descricao' in data:
            campos['Descricao'] = data['descricao']
        if 'solicitante' in data:
            campos['Solicitante'] = data['solicitante']
        if 'email' in data:
            campos['Email'] = data['email']
        if 'setor' in data:
            campos['SetordeAtendimento'] = data['setor']
        if 'prioridade' in data:
            campos['Prioridade'] = data['prioridade']
        if 'status' in data:
            campos['Status'] = data['status']
        if 'responsavel' in data:
            campos['Responsavel'] = data['responsavel']
        if 'historico' in data and isinstance(data['historico'], list):
            campos['Historico'] = json.dumps(limitar_historico(data['historico']), ensure_ascii=False)

        if not campos:
            return jsonify({"status": "erro", "mensagem": "Nenhum campo para atualizar"}), 400

        update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
        update_payload = {"fields": campos}

        update_response = requests.patch(update_url, headers=headers, json=update_payload, timeout=10)

        if update_response.status_code not in [200, 204]:
            logger.error(f"❌ Erro ao atualizar: {update_response.status_code} - {update_response.text}")
            detalhe = extrair_erro_graph(update_response)
            mensagem = "Erro ao atualizar no SharePoint" + (f": {detalhe}" if detalhe else "")
            return jsonify({"status": "erro", "mensagem": mensagem}), 400

        logger.info(f"✅ Chamado ID={item_id} atualizado com sucesso")
        return jsonify({"status": "sucesso", "mensagem": "✅ Chamado atualizado com sucesso!"}), 200

    except Exception as e:
        logger.error(f"❌ ERRO em editar_chamado: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@app.route('/api/deletar-chamado/<item_id>', methods=['DELETE', 'OPTIONS'])
@requer_admin
def deletar_chamado(item_id):
    """Deleta um chamado pelo Dashboard (usa o ID direto do SharePoint)"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        logger.info(f"🗑️ Deletando chamado ID={item_id}")

        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Falha ao conectar SharePoint"}), 401

        headers = {'Authorization': f'Bearer {token}'}
        site_id, list_id = obter_site_e_lista(headers)
        if not site_id or not list_id:
            return jsonify({"status": "erro", "mensagem": "Erro ao conectar SharePoint"}), 400

        delete_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
        delete_response = requests.delete(delete_url, headers=headers, timeout=10)

        if delete_response.status_code not in [200, 204]:
            logger.error(f"❌ Erro ao deletar: {delete_response.status_code} - {delete_response.text}")
            detalhe = extrair_erro_graph(delete_response)
            mensagem = "Erro ao deletar no SharePoint" + (f": {detalhe}" if detalhe else "")
            return jsonify({"status": "erro", "mensagem": mensagem}), 400

        logger.info(f"✅ Chamado ID={item_id} deletado com sucesso")
        return jsonify({"status": "sucesso", "mensagem": "✅ Chamado deletado com sucesso!"}), 200

    except Exception as e:
        logger.error(f"❌ ERRO em deletar_chamado: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@app.route('/api/pesquisas', methods=['GET'])
@requer_login
def obter_pesquisas():
    """Retorna todas as respostas da Pesquisa de Satisfação (lista PesquisasSatisfacao)"""
    try:
        token = get_access_token()
        if not token:
            return jsonify([]), 200

        headers = {'Authorization': f'Bearer {token}'}
        site_id, list_id = obter_site_e_lista(headers, LISTA_PESQUISAS)
        if not site_id or not list_id:
            return jsonify([]), 200

        items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields"
        items_response = requests.get(items_url, headers=headers, timeout=10)

        if items_response.status_code != 200:
            return jsonify([]), 200

        items = items_response.json().get('value', [])

        pesquisas = []
        for idx, item in enumerate(items):
            fields = item.get('fields', {})

            # DEBUG: Imprimir campos da primeira resposta
            if idx == 0:
                logger.info(f"🔍 DEBUG - Campos brutos da primeira pesquisa:")
                for chave, valor in fields.items():
                    valor_resumido = str(valor)[:100] if valor else "(vazio)"
                    logger.info(f"   '{chave}' = {valor_resumido}")
            pesquisas.append({
                'id': item.get('id'),
                'avaliacao': fields.get('Avaliacao', ''),
                'comentario': fields.get('Comentario') or fields.get('comentario') or fields.get('Comentários') or '',
                'numeroChamado': fields.get('NumeroChamado', ''),
                'dataResposta': fields.get('Created', datetime.now().isoformat()),
            })

        logger.info(f"✅ {len(pesquisas)} pesquisas de satisfação retornadas")
        return jsonify(pesquisas), 200

    except Exception as e:
        logger.error(f"ERRO em obter_pesquisas: {e}")
        return jsonify([]), 200


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)