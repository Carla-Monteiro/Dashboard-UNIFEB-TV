#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Versão: 9.0 - DataAbertura+NumeroChamado gravados no SharePoint | Dashboard: data+hora e Salas de Aula"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import requests
from datetime import datetime, timedelta
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

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')

NOMES_SETORES = {
    'manutencao': 'Manutenção Predial',
    'naem': 'Multimídia (NAEM)',
    'ti': 'TI / Internet'
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

def obter_site_e_lista(headers):
    """Helper: retorna (site_id, list_id) ou (None, None) em caso de erro"""
    site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
    site_response = requests.get(site_url, headers=headers, timeout=10)
    if site_response.status_code != 200:
        logger.error(f"❌ Erro ao conectar site: {site_response.status_code}")
        return None, None
    site_id = site_response.json().get('id')

    list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
    list_response = requests.get(list_url, headers=headers, timeout=10)
    if list_response.status_code != 200:
        logger.error(f"❌ Erro ao conectar lista: {list_response.status_code}")
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
        
        agora = datetime.now()
        data_abertura_iso = agora.strftime('%Y-%m-%dT%H:%M:%SZ')
        
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
        
        chamados = []
        for item in items:
            fields = item.get('fields', {})
            chamado = {
                'id': item.get('id'),
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
                'setor': fields.get('SetordeAtendimento', ''),
                'setorAtendimento': fields.get('SetordeAtendimento', ''),
                'numeroChamado': fields.get('NumeroChamado', ''),
                'data': fields.get('DataAbertura', datetime.now().isoformat()),
            }
            chamados.append(chamado)
        
        logger.info(f"✅ {len(chamados)} chamados retornados")
        return jsonify(chamados), 200
        
    except Exception as e:
        logger.error(f"ERRO em obter_chamados: {e}")
        return jsonify([]), 200

@app.route('/api/concluir-chamado', methods=['GET', 'OPTIONS'])
def concluir_chamado():
    """Conclui um chamado e retorna JSON (sem abrir página).
    Aceita DOIS modos:
      - ?id=123        -> atualiza DIRETO o item pelo ID do SharePoint (recomendado / usado pelo QR Code)
      - ?numero=XXXX   -> procura pelo número embutido no Title (modo antigo / e-mail dos funcionários)
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        item_id_direto = request.args.get('id')
        numero = request.args.get('numero')

        if not item_id_direto and not numero:
            logger.warning("❌ Nem 'id' nem 'numero' foram informados")
            return jsonify({"status": "erro", "mensagem": "Informe 'id' ou 'numero'"}), 400

        token = get_access_token()
        if not token:
            logger.error("❌ Falha ao obter token")
            return jsonify({"status": "erro", "mensagem": "Falha ao conectar"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        
        site_id, list_id = obter_site_e_lista(headers)
        if not site_id or not list_id:
            return jsonify({"status": "erro", "mensagem": "Erro ao conectar SharePoint"}), 400

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
                return jsonify({"status": "erro", "mensagem": "Erro ao procurar chamado"}), 400
            
            items = query_response.json().get('value', [])
            if not items:
                logger.warning(f"❌ Chamado #{numero} não encontrado")
                return jsonify({"status": "erro", "mensagem": "Chamado não encontrado"}), 404
            
            item = items[0]
            item_id = item.get('id')

        logger.info(f"✅ Atualizando chamado ID={item_id}")
        
        update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
        update_payload = {"fields": {"Status": "Concluído"}}
        
        update_response = requests.patch(update_url, headers=headers, json=update_payload, timeout=10)
        
        if update_response.status_code not in [200, 204]:
            logger.error(f"❌ Erro ao atualizar: {update_response.status_code}")
            return jsonify({"status": "erro", "mensagem": "Erro ao atualizar chamado"}), 400
        
        logger.info(f"✅ Chamado ID={item_id} concluído com sucesso!")
        
        return jsonify({
            "status": "sucesso",
            "mensagem": "✅ Chamado concluído com sucesso!",
            "id": item_id,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ ERRO em concluir_chamado: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


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

        data_abertura_iso = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

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


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
