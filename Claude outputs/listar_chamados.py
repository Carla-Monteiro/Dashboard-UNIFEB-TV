#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para listar TODOS os chamados e ver os valores de Origem
"""

import requests
import json
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GRAPH_API = "https://graph.microsoft.com/v1.0"
SHAREPOINT_DOMAIN = "unifeb.sharepoint.com"
SITE_PATH = "/sites/SuporteDTI"
LIST_NAME = "Chamados"

def listar_chamados(access_token: str):
    """Lista todos os chamados"""

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Prefer': 'HonorNonIndexedQueriesWarningMayFailRandomly'
    }

    # Obter site
    site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
    site_response = requests.get(site_url, headers=headers, timeout=10)
    site_id = site_response.json().get('id')

    # Obter lista
    list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
    list_response = requests.get(list_url, headers=headers, timeout=10)
    list_id = list_response.json().get('id')

    # Listar chamados SEM FILTRO
    items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields&$top=100"

    print("\n" + "="*80)
    print("📋 LISTANDO TODOS OS CHAMADOS")
    print("="*80 + "\n")

    items_response = requests.get(items_url, headers=headers, timeout=10)
    chamados = items_response.json().get('value', [])

    print(f"Total de chamados: {len(chamados)}\n")

    for idx, chamado in enumerate(chamados, 1):
        fields = chamado.get('fields', {})
        titulo = fields.get('Title', 'SEM TÍTULO')
        origem = fields.get('Origem', 'VAZIO/NULL')
        email = fields.get('Email', '')

        print(f"{idx}. [{chamado.get('id')}] {titulo}")
        print(f"   Email: {email}")
        print(f"   Origem: '{origem}'")
        print()

    # Estatísticas
    print("="*80)
    print("📊 ESTATÍSTICAS DE ORIGEM:\n")

    origens = {}
    for chamado in chamados:
        fields = chamado.get('fields', {})
        origem = fields.get('Origem', 'VAZIO/NULL')
        origens[origem] = origens.get(origem, 0) + 1

    for origem, count in sorted(origens.items(), key=lambda x: x[1], reverse=True):
        print(f"  '{origem}': {count} chamados")

    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    print("📝 Digite o token:")
    token = input("Token: ").strip()

    if token:
        listar_chamados(token)
    else:
        print("❌ Token não fornecido")
