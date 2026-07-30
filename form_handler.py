#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API Backend para Gerenciar Chamados - Versão Corrigida"""

import os
import json
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
    auth_url = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token'
    auth_data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default',
        'grant_type': 'client_credentials'
    }
    
    try:
        response = requests.post(auth_url, data=auth_data, timeout=10)
        if response.status_code != 200:
            return None
        return response.json().get('access_token')
    except:
        return None

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "ok", "service": "unifeb-backend"}), 200

@app.route('/api/criar-chamado', methods=['POST'])
def criar_chamado():
    """Criar novo chamado"""
    try:
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Falha na autenticação"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # Obter Site ID
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        if site_response.status_code != 200:
            return jsonify({"status": "erro", "mensagem": "Erro ao acessar SharePoint"}), 400
        
        site_id = site_response.json().get('id')
        
        # Obter List ID
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        if list_response.status_code != 200:
            return jsonify({"status": "erro", "mensagem": "Erro ao acessar lista"}), 400
        
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
            return jsonify({"status": "erro", "mensagem": f"Erro: {response.status_code}"}), response.status_code
    
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/editar-chamado/<item_id>', methods=['PATCH'])
def editar_chamado(item_id):
    """Editar chamado"""
    try:
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Falha na autenticação"}), 401
        
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
            return jsonify({"status": "sucesso", "mensagem": "Chamado atualizado!"}), 200
        else:
            return jsonify({"status": "erro", "mensagem": f"Erro: {response.status_code}"}), response.status_code
    
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/deletar-chamado/<item_id>', methods=['DELETE'])
def deletar_chamado(item_id):
    """Deletar chamado"""
    try:
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Falha na autenticação"}), 401
        
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
            return jsonify({"status": "sucesso", "mensagem": "Chamado deletado!"}), 200
        else:
            return jsonify({"status": "erro", "mensagem": f"Erro: {response.status_code}"}), response.status_code
    
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
