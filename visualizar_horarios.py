#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualizar Horários dos Chamados - #SuporteUNIFEB
Apenas lista os chamados e mostra seus horários
"""

import requests

# Credenciais
CLIENT_ID = "100ba4af-831a-4d3c-8e96-60e683f0152a"
CLIENT_SECRET = "P338Q~zC04Td8P1rk_srVCl-pS2wlzWzSGl9da3T"
TENANT_ID = "62a0e447-20c2-41be-8e60-893b78364660"

GRAPH_API = "https://graph.microsoft.com/v1.0"
SHAREPOINT_DOMAIN = "unifeb.sharepoint.com"
SITE_PATH = "/sites/SuporteDTI"
LIST_NAME = "Chamados"

print("=" * 100)
print("📋 VISUALIZAR HORÁRIOS DOS CHAMADOS - #SuporteUNIFEB")
print("=" * 100)
print()

def get_access_token():
    """Obter token de acesso"""
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
        print(f"❌ Erro ao obter token: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return None

def obter_site_e_lista(headers):
    """Obter ID do site e da lista"""
    try:
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        if site_response.status_code != 200:
            print(f"❌ Erro ao conectar site: {site_response.status_code}")
            return None, None
        site_id = site_response.json().get('id')

        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        if list_response.status_code != 200:
            print(f"❌ Erro ao conectar lista: {list_response.status_code}")
            return None, None
        list_id = list_response.json().get('id')

        return site_id, list_id
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None, None

def visualizar_chamados():
    """Buscar e mostrar todos os chamados com seus horários"""
    print("🔐 Autenticando no SharePoint...")
    token = get_access_token()
    if not token:
        print("❌ Falha ao autenticar")
        return

    headers = {'Authorization': f'Bearer {token}'}
    
    print("📍 Conectando ao site e lista...")
    site_id, list_id = obter_site_e_lista(headers)
    if not site_id or not list_id:
        print("❌ Falha ao conectar SharePoint")
        return

    print(f"✅ Conectado! Site ID: {site_id}")
    print(f"✅ Lista ID: {list_id}")
    print()

    # Buscar todos os itens
    print("📥 Buscando chamados...")
    items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields"
    items_response = requests.get(items_url, headers=headers, timeout=10)

    if items_response.status_code != 200:
        print(f"❌ Erro ao buscar itens: {items_response.status_code}")
        return

    items = items_response.json().get('value', [])
    print(f"✅ {len(items)} chamados encontrados")
    print()

    # Exibir tabela
    print("=" * 100)
    print(f"{'Número':<12} {'Título':<35} {'DataAbertura (SharePoint)':<35} {'Status':<15}")
    print("=" * 100)

    chamados_utc = 0
    chamados_sp = 0

    for item in items:
        fields = item.get('fields', {})
        numero = fields.get('NumeroChamado', '?')
        titulo = fields.get('Title', '?')[:32]
        data_abertura = fields.get('DataAbertura', '?')
        status = fields.get('Status', '?')

        # Identificar se é UTC ou São Paulo
        if data_abertura.endswith('Z') or '+00:00' in str(data_abertura):
            tipo = '❌ UTC'
            chamados_utc += 1
        else:
            tipo = '✅ SP'
            chamados_sp += 1

        print(f"{numero:<12} {titulo:<35} {data_abertura:<35} {tipo:<15}")

    print("=" * 100)
    print()
    print("📊 RESUMO:")
    print(f"   ✅ Chamados em São Paulo (corretos): {chamados_sp}")
    print(f"   ❌ Chamados em UTC (precisam corrigir): {chamados_utc}")
    print("=" * 100)
    print()

    if chamados_utc > 0:
        print(f"💡 Você tem {chamados_utc} chamado(s) que podem ser corrigidos!")
        print("   Use o script: python corrigir_chamados_simples.py")
    else:
        print("✅ Todos os chamados estão corretos!")

if __name__ == '__main__':
    visualizar_chamados()
