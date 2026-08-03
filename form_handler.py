#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Versão: 4.0 - Com /api/chamados + fix na query URL"""

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
    '🌐 Internet/Wi-Fi': {'tipo': 'ti'},
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
        
        numero = gerar_numero_chamado()
        roteamento = obter_roteamento(categoria)
        tipo_problema = roteamento['tipo']
        solicitante = email.split('@')[0].replace('.', ' ').title()
        
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Falha ao conectar SharePoint"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        
        if site_response.status_code != 200:
            return jsonify({"status": "erro", "mensagem": "Erro ao conectar site"}), 400
        
        site_id = site_response.json().get('id')
        
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        
        if list_response.status_code != 200:
            return jsonify({"status": "erro", "mensagem": "Erro ao conectar lista"}), 400
        
        list_id = list_response.json().get('id')
        
        create_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items"
        
        payload = {
            "fields": {
                "Title": f"[{numero}] {categoria} - {bloco}/{sala}",
                "Descricao": descricao,
                "Solicitante": solicitante,
                "Email": email,
                "Bloco": bloco,
                "Sala": sala,
                "Categoria": categoria,
                "SetordeAtendimento": NOMES_SETORES.get(tipo_problema, 'Geral'),
                "Prioridade": "Alta",
                "Status": "Aberto",
                "Origem": "QR Code"
            }
        }
        
        response = requests.post(create_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code not in [200, 201]:
            return jsonify({"status": "erro", "mensagem": "Erro ao salvar"}), 400
        
        return jsonify({
            "status": "sucesso",
            "mensagem": "✅ Aviso enviado com sucesso!",
            "numero": numero
        }), 201
        
    except Exception as e:
        logger.error(f"ERRO: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/chamados', methods=['GET'])
def obter_chamados():
    """Retorna lista de todos os chamados do SharePoint"""
    try:
        token = get_access_token()
        if not token:
            return jsonify([]), 200
        
        headers = {'Authorization': f'Bearer {token}'}
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        
        if site_response.status_code != 200:
            return jsonify([]), 200
        
        site_id = site_response.json().get('id')
        
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        
        if list_response.status_code != 200:
            return jsonify([]), 200
        
        list_id = list_response.json().get('id')
        
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
            }
            chamados.append(chamado)
        
        logger.info(f"✅ {len(chamados)} chamados retornados")
        return jsonify(chamados), 200
        
    except Exception as e:
        logger.error(f"ERRO em obter_chamados: {e}")
        return jsonify([]), 200

@app.route('/api/concluir-chamado', methods=['GET'])
def concluir_chamado():
    try:
        numero = request.args.get('numero')
        if not numero:
            return jsonify({"status": "erro", "mensagem": "Número não informado"}), 400
        
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Falha ao conectar"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        site_id = site_response.json().get('id')
        
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        list_id = list_response.json().get('id')
        
        query_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$filter=contains(fields/Title, '{numero}')"
        query_response = requests.get(query_url, headers=headers, timeout=10)
        
        items = query_response.json().get('value', [])
        if not items:
            return jsonify({"status": "erro", "mensagem": "Chamado não encontrado"}), 404
        
        item = items[0]
        item_id = item.get('id')
        
        update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
        update_payload = {"fields": {"Status": "Concluído"}}
        
        update_response = requests.patch(update_url, headers=headers, json=update_payload, timeout=10)
        
        if update_response.status_code not in [200, 204]:
            return jsonify({"status": "erro", "mensagem": "Erro ao atualizar"}), 400
        
        return jsonify({
            "status": "sucesso",
            "mensagem": "✅ Chamado concluído!"
        }), 200
        
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
