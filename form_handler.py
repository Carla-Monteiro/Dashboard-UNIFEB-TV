#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API Backend para Gerenciar Chamados - Render Ready com Endpoint de Chamados"""

import os
import json
import sys
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')

SHAREPOINT_DOMAIN = "unifeb.sharepoint.com"
SITE_PATH = "/sites/SuporteDTI"
LIST_NAME = "Chamados"
GRAPH_API = "https://graph.microsoft.com/v1.0"

app = Flask(__name__)
CORS(app)

def get_access_token():
    """Obter token de acesso do Azure AD"""
    try:
        auth_url = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token'
        auth_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        response = requests.post(auth_url, data=auth_data, timeout=10)
        if response.status_code != 200:
            print(f"Auth error: {response.status_code}")
            return None
        return response.json().get('access_token')
    except Exception as e:
        print(f"Auth exception: {e}")
        return None

# ========== ENDPOINT NOVO: Retornar Chamados Sincronizados ==========
@app.route('/api/chamados', methods=['GET'])
def get_chamados():
    """Retorna os chamados sincronizados do arquivo JSON"""
    try:
        with open('chamados_sync.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
            return jsonify(dados), 200
    except FileNotFoundError:
        return jsonify({"chamados": [], "total_chamados": 0}), 200
    except Exception as e:
        print(f"Erro ao ler chamados_sync.json: {e}")
        return jsonify({"chamados": [], "total_chamados": 0}), 200

# ========== ENDPOINTS ANTIGOS (Manter funcionando) ==========

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/api/criar-chamado', methods=['POST'])
def criar_chamado():
    try:
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Autenticação falhou"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        
        if site_response.status_code != 200:
            return jsonify({"status": "erro", "mensagem": "SharePoint error"}), 400
        
        site_id = site_response.json().get('id')
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        
        if list_response.status_code != 200:
            return jsonify({"status": "erro", "mensagem": "List error"}), 400
        
        list_id = list_response.json().get('id')
        data = request.json
        create_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items"
        
        payload = {
            "fields": {
                "Title": data.get('titulo'),
                "Descricao": data.get('descricao'),
                "Solicitante": data.get('solicitante'),
                "Email": data.get('email'),
                "SetordeAtendimento": data.get('setor'),
                "Prioridade": data.get('prioridade'),
                "Status": "Aberto"
            }
        }
        
        response = requests.post(create_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code in [200, 201]:
            return jsonify({"status": "sucesso", "mensagem": "Chamado criado!"}), 201
        else:
            return jsonify({"status": "erro", "mensagem": "Criar falhou"}), response.status_code
    
    except Exception as e:
        print(f"Create error: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/editar-chamado/<item_id>', methods=['PATCH'])
def editar_chamado(item_id):
    try:
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Autenticação falhou"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        site_id = site_response.json().get('id')
        
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        list_id = list_response.json().get('id')
        
        data = request.json
        update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
        
        payload = {
            "fields": {
                "Title": data.get('titulo'),
                "Descricao": data.get('descricao'),
                "SetordeAtendimento": data.get('setor'),
                "Prioridade": data.get('prioridade'),
                "Status": data.get('status')
            }
        }
        
        response = requests.patch(update_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            return jsonify({
                "status": "sucesso", 
                "mensagem": "✅ Atualizado com sucesso!"
            }), 200
        else:
            return jsonify({"status": "erro", "mensagem": "Update falhou"}), response.status_code
    
    except Exception as e:
        print(f"Update error: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/deletar-chamado/<item_id>', methods=['DELETE'])
def deletar_chamado(item_id):
    try:
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Autenticação falhou"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        site_id = site_response.json().get('id')
        
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        list_id = list_response.json().get('id')
        
        delete_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
        response = requests.delete(delete_url, headers=headers, timeout=10)
        
        if response.status_code == 204:
            return jsonify({"status": "sucesso", "mensagem": "Deletado!"}), 200
        else:
            return jsonify({"status": "erro", "mensagem": "Delete falhou"}), response.status_code
    
    except Exception as e:
        print(f"Delete error: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
