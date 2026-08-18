#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Versão: 12.0 - Recupera preenchimento automático de setor por email (nome.setor@feb.br)"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import requests
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
                "DataAbertura": data_abertura_iso
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


@app.route('/api/chamados', methods=['GET'])
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
        
        update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
        update_payload = {"fields": {"Status": "Concluído"}}
        
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
                "DataAbertura": data_abertura_iso
            }
        }

        response = requests.post(create_url, headers=headers, json=payload, timeout=10)

        if response.status_code not in [200, 201]:
            logger.error(f"❌ Erro ao criar: {response.status_code} - {response.text}")
            return jsonify({"status": "erro", "mensagem": "Erro ao salvar no SharePoint"}), 400

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

        if not campos:
            return jsonify({"status": "erro", "mensagem": "Nenhum campo para atualizar"}), 400

        update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
        update_payload = {"fields": campos}

        update_response = requests.patch(update_url, headers=headers, json=update_payload, timeout=10)

        if update_response.status_code not in [200, 204]:
            logger.error(f"❌ Erro ao atualizar: {update_response.status_code} - {update_response.text}")
            return jsonify({"status": "erro", "mensagem": "Erro ao atualizar no SharePoint"}), 400

        logger.info(f"✅ Chamado ID={item_id} atualizado com sucesso")
        return jsonify({"status": "sucesso", "mensagem": "✅ Chamado atualizado com sucesso!"}), 200

    except Exception as e:
        logger.error(f"❌ ERRO em editar_chamado: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@app.route('/api/deletar-chamado/<item_id>', methods=['DELETE', 'OPTIONS'])
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
            return jsonify({"status": "erro", "mensagem": "Erro ao deletar no SharePoint"}), 400

        logger.info(f"✅ Chamado ID={item_id} deletado com sucesso")
        return jsonify({"status": "sucesso", "mensagem": "✅ Chamado deletado com sucesso!"}), 200

    except Exception as e:
        logger.error(f"❌ ERRO em deletar_chamado: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@app.route('/api/pesquisas', methods=['GET'])
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
        for item in items:
            fields = item.get('fields', {})
            pesquisas.append({
                'id': item.get('id'),
                'avaliacao': fields.get('Avaliacao', ''),
                'comentario': fields.get('Comentários', ''),
                'numeroChamado': fields.get('NumeroChamado', ''),
                'dataResposta': fields.get('Created', datetime.now().isoformat()),
            })

        logger.info(f"✅ {len(pesquisas)} pesquisas de satisfação retornadas")
        return jsonify(pesquisas), 200

    except Exception as e:
        logger.error(f"ERRO em obter_pesquisas: {e}")
        return jsonify([]), 200


@app.route('/api/debug/campos-pesquisas', methods=['GET'])
def debug_campos_pesquisas():
    """DEBUG: Retorna todos os campos brutos da primeira pesquisa do SharePoint"""
    try:
        token = get_access_token()
        if not token:
            return jsonify({"erro": "Token não obtido"}), 200

        headers = {'Authorization': f'Bearer {token}'}
        site_id, list_id = obter_site_e_lista(headers, LISTA_PESQUISAS)
        if not site_id or not list_id:
            return jsonify({"erro": "Site ou List ID não encontrado"}), 200

        items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields"
        items_response = requests.get(items_url, headers=headers, timeout=10)

        if items_response.status_code != 200:
            return jsonify({"erro": f"Erro {items_response.status_code}"}), 200

        items = items_response.json().get('value', [])

        if not items:
            return jsonify({"mensagem": "Nenhuma pesquisa encontrada"}), 200

        # Retornar TODOS os campos da primeira pesquisa
        primeiro_item = items[0]
        campos = primeiro_item.get('fields', {})

        debug_response = {
            "mensagem": "🔍 CAMPOS BRUTOS DA PRIMEIRA PESQUISA NO SHAREPOINT",
            "total_campos": len(campos),
            "campos": {}
        }

        for chave, valor in sorted(campos.items()):
            valor_str = str(valor)[:150] if valor else "(vazio)"
            debug_response["campos"][chave] = valor_str

        return jsonify(debug_response), 200

    except Exception as e:
        logger.error(f"ERRO em debug_campos_pesquisas: {e}")
        return jsonify({"erro": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)