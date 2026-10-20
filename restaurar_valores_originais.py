#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Restaurar Valores Originais Corretos em UTC
Script que corrige os chamados para os valores ORIGINAIS que estavam certos
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

print("=" * 80)
print("🔧 RESTAURAR VALORES ORIGINAIS CORRETOS - #SuporteUNIFEB")
print("=" * 80)
print()

# Dados ORIGINAIS CORRETOS que precisam ser restaurados
DADOS_ORIGINAIS = {
    "CH-1085": "2026-08-05T23:43:45Z",  # Original correto
    "CH-1086": "2026-08-06T16:06:31Z",  # Original correto
}

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

def restaurar_valores():
    """Restaurar todos os chamados com valores originais"""
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

    print(f"✅ Conectado!")
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

    # Encontrar os chamados que precisam ser restaurados
    chamados_para_restaurar = []
    for item in items:
        fields = item.get('fields', {})
        numero = fields.get('NumeroChamado', '?')
        titulo = fields.get('Title', '?')
        
        if numero in DADOS_ORIGINAIS:
            chamados_para_restaurar.append({
                'id': item.get('id'),
                'numero': numero,
                'titulo': titulo,
                'valor_original': DADOS_ORIGINAIS[numero]
            })

    if not chamados_para_restaurar:
        print("✅ Nenhum chamado para restaurar encontrado!")
        return

    print(f"📋 CHAMADOS A RESTAURAR:")
    print("-" * 80)
    for chamado in chamados_para_restaurar:
        print(f"✓ {chamado['numero']} - {chamado['titulo']}")
        print(f"  Valor original correto: {chamado['valor_original']}")
        print()

    # Confirmar
    resposta = input("❓ Tem certeza que quer restaurar esses chamados? (sim/não): ").strip().lower()
    if resposta not in ['sim', 's', 'y', 'yes']:
        print("❌ Operação cancelada")
        return

    print()
    print("🔄 Restaurando chamados...")
    print("-" * 80)

    sucesso = 0
    erro = 0

    for chamado in chamados_para_restaurar:
        try:
            # Atualizar no SharePoint
            update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{chamado['id']}"
            update_payload = {
                "fields": {
                    "DataAbertura": chamado['valor_original']
                }
            }

            update_response = requests.patch(
                update_url,
                headers=headers,
                json=update_payload,
                timeout=10
            )

            if update_response.status_code in [200, 204]:
                print(f"✅ {chamado['numero']} - Restaurado!")
                sucesso += 1
            else:
                print(f"❌ {chamado['numero']} - Erro ao atualizar: {update_response.status_code}")
                erro += 1

        except Exception as e:
            print(f"❌ {chamado['numero']} - Exceção: {e}")
            erro += 1

    print()
    print("=" * 80)
    print("📊 RESULTADO:")
    print(f"   ✅ Restaurados com sucesso: {sucesso}")
    print(f"   ❌ Erros: {erro}")
    print("=" * 80)
    print()

    if sucesso > 0:
        print("🎉 Chamados restaurados! Aguarde 30 segundos e recarregue o Dashboard.")
    else:
        print("⚠️  Nenhum chamado foi restaurado.")

if __name__ == '__main__':
    restaurar_valores()
