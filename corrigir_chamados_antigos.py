#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrigir Timezone de Chamados Antigos - #SuporteUNIFEB (Versão Simplificada)
Converte datas que foram salvas em UTC para o timezone correto (America/Sao_Paulo)
"""

import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# ⚠️ CREDENCIAIS (copie do seu .env)
CLIENT_ID = "100ba4af-831a-4d3c-8e96-60e683f0152a"
CLIENT_SECRET = "P338Q~zC04Td8P1rk_srVCl-pS2wlzWzSGl9da3T"
TENANT_ID = "62a0e447-20c2-41be-8e60-893b78364660"

GRAPH_API = "https://graph.microsoft.com/v1.0"
SHAREPOINT_DOMAIN = "unifeb.sharepoint.com"
SITE_PATH = "/sites/SuporteDTI"
LIST_NAME = "Chamados"

print("=" * 80)
print("🔧 CORRIGIR TIMEZONE DE CHAMADOS ANTIGOS - #SuporteUNIFEB")
print("=" * 80)
print()

def get_access_token():
    """Obter token de acesso da Microsoft"""
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

def converter_utc_para_sp(data_utc_str):
    """
    Converte data em UTC para São Paulo
    Entrada: "2026-08-06T18:30:00Z" (UTC)
    Saída: "2026-08-06T15:30:00-03:00" (São Paulo)
    """
    try:
        # Parser a data UTC
        dt_utc = datetime.fromisoformat(data_utc_str.replace('Z', '+00:00'))
        
        # Converter para São Paulo
        tz_sp = ZoneInfo('America/Sao_Paulo')
        dt_sp = dt_utc.astimezone(tz_sp)
        
        # Retornar em ISO format
        return dt_sp.isoformat()
    except Exception as e:
        print(f"❌ Erro ao converter {data_utc_str}: {e}")
        return None

def corrigir_chamados():
    """Buscar e corrigir todos os chamados com data errada"""
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
    print("📥 Buscando todos os chamados...")
    items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields"
    items_response = requests.get(items_url, headers=headers, timeout=10)

    if items_response.status_code != 200:
        print(f"❌ Erro ao buscar itens: {items_response.status_code}")
        return

    items = items_response.json().get('value', [])
    print(f"✅ {len(items)} chamados encontrados")
    print()

    # Filtrar chamados que precisam ser corrigidos
    chamados_para_corrigir = []
    for item in items:
        fields = item.get('fields', {})
        data_abertura = fields.get('DataAbertura')
        
        # Verificar se é uma data em UTC (termina com Z ou +00:00)
        if data_abertura and (data_abertura.endswith('Z') or '+00:00' in data_abertura):
            chamados_para_corrigir.append({
                'id': item.get('id'),
                'numero': fields.get('NumeroChamado', '?'),
                'titulo': fields.get('Title', '?'),
                'data_antiga': data_abertura
            })

    if not chamados_para_corrigir:
        print("✅ ÓTIMO! Nenhum chamado com data em UTC encontrado!")
        print("   Todos os chamados já estão com o timezone correto!")
        return

    print(f"⚠️  {len(chamados_para_corrigir)} chamado(s) com data em UTC encontrado(s)")
    print()

    # Mostrar preview
    print("📋 PREVIEW DOS CHAMADOS QUE SERÃO CORRIGIDOS:")
    print("-" * 80)
    for i, chamado in enumerate(chamados_para_corrigir[:5], 1):
        data_nova = converter_utc_para_sp(chamado['data_antiga'])
        print(f"{i}. {chamado['numero']} - {chamado['titulo']}")
        print(f"   Antes: {chamado['data_antiga']}")
        print(f"   Depois: {data_nova}")
        print()

    if len(chamados_para_corrigir) > 5:
        print(f"   ... e mais {len(chamados_para_corrigir) - 5} chamado(s)")
        print()

    # Confirmar
    resposta = input("❓ Tem certeza que quer corrigir esses chamados? (sim/não): ").strip().lower()
    if resposta not in ['sim', 's', 'y', 'yes']:
        print("❌ Operação cancelada")
        return

    print()
    print("🔄 Corrigindo chamados...")
    print("-" * 80)

    sucesso = 0
    erro = 0

    for chamado in chamados_para_corrigir:
        try:
            data_nova = converter_utc_para_sp(chamado['data_antiga'])
            if not data_nova:
                print(f"❌ {chamado['numero']} - Erro ao converter data")
                erro += 1
                continue

            # Atualizar no SharePoint
            update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{chamado['id']}"
            update_payload = {
                "fields": {
                    "DataAbertura": data_nova
                }
            }

            update_response = requests.patch(
                update_url,
                headers=headers,
                json=update_payload,
                timeout=10
            )

            if update_response.status_code in [200, 204]:
                print(f"✅ {chamado['numero']} - Corrigido!")
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
    print(f"   ✅ Corrigidos com sucesso: {sucesso}")
    print(f"   ❌ Erros: {erro}")
    print("=" * 80)
    print()

    if sucesso > 0:
        print("🎉 Chamados corrigidos! Recarregue o Dashboard para ver as mudanças.")
    else:
        print("⚠️  Nenhum chamado foi corrigido.")

if __name__ == '__main__':
    corrigir_chamados()
