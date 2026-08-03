#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 UNIFEB BACKEND - QR CODE SUPPORT V3.0
✅ Cria chamados no SharePoint
✅ Suporta 3 tipos: Manutenção, NAEM, TI
✅ Power Automate dispara emails automáticos
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(app)

# ========== CONFIGURAÇÕES ==========
GRAPH_API = "https://graph.microsoft.com/v1.0"
SHAREPOINT_DOMAIN = "unifeb.sharepoint.com"
SITE_PATH = "/sites/SuporteDTI"
LIST_NAME = "Chamados"

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')

# ========== CONSTANTES ==========
NOMES_SETORES = {
    'manutencao': 'Manutenção Predial',
    'naem': 'Multimídia (NAEM)',
    'ti': 'TI / Internet'
}

# ========== FUNÇÕES AUXILIARES ==========

def obter_token():
    """Obtém access token do SharePoint"""
    try:
        url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
        dados = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        resposta = requests.post(url, data=dados, timeout=10)
        if resposta.status_code == 200:
            return resposta.json().get('access_token')
        logger.error(f"Erro autenticação: {resposta.text}")
        return None
    except Exception as e:
        logger.error(f"Erro ao obter token: {e}")
        return None

def obter_ids_sharepoint():
    """Obtém Site ID e List ID do SharePoint"""
    try:
        token = obter_token()
        if not token:
            return None, None
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # Obter Site ID
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_resp = requests.get(site_url, headers=headers, timeout=10)
        if site_resp.status_code != 200:
            logger.error(f"Erro ao obter site: {site_resp.text}")
            return None, None
        
        site_id = site_resp.json().get('id')
        
        # Obter List ID
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_resp = requests.get(list_url, headers=headers, timeout=10)
        if list_resp.status_code != 200:
            logger.error(f"Erro ao obter lista: {list_resp.text}")
            return None, None
        
        list_id = list_resp.json().get('id')
        return site_id, list_id
        
    except Exception as e:
        logger.error(f"Erro ao obter IDs: {e}")
        return None, None

# ========== ROTAS ==========

@app.route('/api/criar-manutencao', methods=['POST'])
def criar_chamado():
    """
    Cria chamado no SharePoint via QR Code
    Tipos: manutencao, naem, ti
    """
    try:
        dados = request.get_json()
        
        # Validar dados
        email = dados.get('email', '').strip()
        bloco = dados.get('bloco', '').strip()
        sala = dados.get('sala', '').strip()
        tipo = dados.get('tipo', '').strip()  # manutencao, naem, ti
        categoria = dados.get('categoria', '').strip()
        descricao = dados.get('descricao', '').strip()
        
        if not all([email, bloco, sala, tipo, categoria, descricao]):
            return jsonify({'erro': 'Dados incompletos'}), 400
        
        if tipo not in NOMES_SETORES:
            return jsonify({'erro': 'Tipo inválido'}), 400
        
        # Obter tokens e IDs
        token = obter_token()
        if not token:
            return jsonify({'erro': 'Erro de autenticação'}), 500
        
        site_id, list_id = obter_ids_sharepoint()
        if not site_id or not list_id:
            return jsonify({'erro': 'Erro ao acessar SharePoint'}), 500
        
        # Preparar dados para SharePoint
        headers = {'Authorization': f'Bearer {token}'}
        
        # Incrementar ID automaticamente
        items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$select=id&$orderby=id desc&$top=1"
        items_resp = requests.get(items_url, headers=headers, timeout=10)
        
        proximo_id = 1
        if items_resp.status_code == 200:
            items = items_resp.json().get('value', [])
            if items:
                try:
                    ultimo_id = int(items[0].get('fields', {}).get('id', 0) or 0)
                    proximo_id = ultimo_id + 1
                except:
                    proximo_id = len(items) + 1
        
        # Preparar payload
        payload = {
            "fields": {
                "id": str(proximo_id),
                "Title": f"[{NOMES_SETORES[tipo]}] {categoria}",
                "Solicitante": email,
                "Email": email,
                "Bloco": bloco,
                "Sala": sala,
                "Categoria": categoria,
                "Descricao": descricao,
                "Tipo": NOMES_SETORES[tipo],
                "TipoInterno": tipo,
                "SetordeAtendimento": NOMES_SETORES[tipo],
                "Status": "Aberto",
                "Prioridade": "Média",
                "Origem": "QRCode",
                "Created": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        # Criar item no SharePoint
        create_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items"
        create_resp = requests.post(create_url, headers=headers, json=payload, timeout=10)
        
        if create_resp.status_code not in [200, 201]:
            logger.error(f"Erro ao criar item: {create_resp.text}")
            return jsonify({'erro': 'Erro ao criar chamado'}), 500
        
        item_id = create_resp.json().get('id')
        
        logger.info(f"✅ Chamado criado: #{proximo_id} | Tipo: {tipo} | ID SharePoint: {item_id}")
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Chamado criado com sucesso!',
            'chamado_id': proximo_id,
            'item_id': item_id
        }), 201
        
    except Exception as e:
        logger.error(f"Erro em criar_chamado: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/api/concluir-chamado', methods=['POST'])
def concluir_chamado():
    """
    Conclui um chamado (usado pelo botão no email)
    """
    try:
        dados = request.get_json()
        chamado_id = dados.get('chamado_id')
        
        if not chamado_id:
            return jsonify({'erro': 'ID do chamado não fornecido'}), 400
        
        token = obter_token()
        site_id, list_id = obter_ids_sharepoint()
        
        if not token or not site_id or not list_id:
            return jsonify({'erro': 'Erro de autenticação'}), 500
        
        # Buscar o item
        headers = {'Authorization': f'Bearer {token}'}
        search_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields&$filter=fields/id eq '{chamado_id}'"
        search_resp = requests.get(search_url, headers=headers, timeout=10)
        
        if search_resp.status_code != 200 or not search_resp.json().get('value'):
            return jsonify({'erro': 'Chamado não encontrado'}), 404
        
        item = search_resp.json().get('value')[0]
        item_sp_id = item.get('id')
        
        # Atualizar status
        update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_sp_id}"
        update_payload = {
            "fields": {
                "Status": "Concluído"
            }
        }
        
        update_resp = requests.patch(update_url, headers=headers, json=update_payload, timeout=10)
        
        if update_resp.status_code not in [200, 204]:
            return jsonify({'erro': 'Erro ao atualizar'}), 500
        
        logger.info(f"✅ Chamado #{chamado_id} concluído")
        
        return jsonify({'sucesso': True, 'mensagem': 'Chamado concluído!'}), 200
        
    except Exception as e:
        logger.error(f"Erro em concluir_chamado: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
