#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SINCRONIZADOR UNIFEB - VERSÃO FUNCIONAL
✅ Sem problemas de encoding
✅ Credenciais digitadas manualmente
✅ Syncroniza com SharePoint
"""

import requests
import json
from datetime import datetime

print("\n" + "="*80)
print("🚀 SINCRONIZADOR UNIFEB - DASHBOARD TV")
print("="*80 + "\n")

# ========== PEDIR CREDENCIAIS ==========
print("📋 Digite suas credenciais do Azure:\n")
CLIENT_ID = input("CLIENT_ID: ").strip()
CLIENT_SECRET = input("CLIENT_SECRET: ").strip()
TENANT_ID = input("TENANT_ID: ").strip()

SHAREPOINT_DOMAIN = "unifeb.sharepoint.com"
SITE_PATH = "/sites/SuporteDTI"
LIST_NAME = "Chamados"
GRAPH_API = "https://graph.microsoft.com/v1.0"
JSON_FILE = "chamados_sync.json"

SLA_HORAS = {'Alta': 2, 'Média': 8, 'Baixa': 24}

print("\n" + "="*80)
print("✅ Sincronização Iniciada")
print("="*80 + "\n")

# ========== AUTENTICAR ==========
print("🔐 Autenticando no Azure AD...")
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
        print(f"❌ Erro: {response.status_code}")
        print(f"Resposta: {response.text}")
        exit(1)
    
    access_token = response.json().get('access_token')
    print("✅ Autenticado com sucesso!\n")
    
except Exception as e:
    print(f"❌ Erro de autenticação: {e}")
    exit(1)

# ========== OBTER SITE E LIST ID ==========
headers = {'Authorization': f'Bearer {access_token}'}

print("📍 Obtendo Site ID...")
site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
site_response = requests.get(site_url, headers=headers, timeout=10)

if site_response.status_code != 200:
    print(f"❌ Erro ao obter site: {site_response.status_code}")
    exit(1)

site_id = site_response.json().get('id')
print(f"✅ Site ID: {site_id}\n")

print("📍 Obtendo List ID...")
list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
list_response = requests.get(list_url, headers=headers, timeout=10)

if list_response.status_code != 200:
    print(f"❌ Erro ao obter lista: {list_response.status_code}")
    exit(1)

list_id = list_response.json().get('id')
print(f"✅ List ID: {list_id}\n")

# ========== BUSCAR ITENS ==========
print("📋 Buscando chamados do SharePoint...")
items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields&$top=100"

try:
    items_response = requests.get(items_url, headers=headers, timeout=10)
    
    if items_response.status_code != 200:
        print(f"❌ Erro ao ler itens: {items_response.status_code}")
        exit(1)
    
    items = items_response.json().get('value', [])
    print(f"✅ {len(items)} chamado(s) encontrado(s)\n")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    exit(1)

# ========== PROCESSAR ITENS ==========
def calcular_sla(data_abertura_str, prioridade, status):
    """Calcula SLA"""
    try:
        if status and 'resolvido' in status.lower():
            return False, 0, 'Resolvido', '0h'
        
        data_abertura = datetime.fromisoformat(data_abertura_str.replace('Z', '+00:00'))
        agora = datetime.now(data_abertura.tzinfo) if data_abertura.tzinfo else datetime.now()
        
        diferenca = agora - data_abertura
        horas_aberto = diferenca.total_seconds() / 3600
        minutos_aberto = int((horas_aberto % 1) * 60)
        horas_aberto_int = int(horas_aberto)
        
        sla_horas = SLA_HORAS.get(prioridade, 8)
        sla_vencido = horas_aberto > sla_horas
        
        if sla_vencido:
            atraso = horas_aberto - sla_horas
            atraso_horas = int(atraso)
            atraso_minutos = int((atraso % 1) * 60)
            atraso_str = f"{atraso_horas}h {atraso_minutos}min"
        else:
            atraso_str = "No prazo"
        
        if horas_aberto_int < 1:
            aberto_str = f"{minutos_aberto}min"
        else:
            aberto_str = f"{horas_aberto_int}h {minutos_aberto}min"
        
        return sla_vencido, horas_aberto, atraso_str, aberto_str
        
    except Exception as e:
        return False, 0, "Erro", "0h"

print("⚙️  Processando chamados...\n")

chamados = []

for item in items:
    fields = item.get('fields', {})
    
    id_valor = str(fields.get('id') or '')
    titulo = fields.get('Title') or ''
    
    if not id_valor or id_valor == '0' or id_valor == 'None':
        continue
    
    if not titulo or len(titulo.strip()) < 3:
        continue
    
    # Buscar SetordeAtendimento
    setor = (
        fields.get('SetordeAtendimento') or
        fields.get('SetorDeAtendimento') or 
        fields.get('Setor de Atendimento') or 
        fields.get('Escolhas') or
        fields.get('Setor') or 
        'Geral'
    )
    
    prioridade = fields.get('Prioridade') or 'Média'
    status = fields.get('Status') or 'Aberto'
    data_abertura = fields.get('Created') or fields.get('DataAbertura') or ''
    
    sla_vencido, horas_aberto, atraso_str, aberto_str = calcular_sla(
        data_abertura, prioridade, status
    )
    
    print(f"   ✅ #{id_valor} | {titulo[:40]:<40} | {setor}")
    
    chamado = {
        "id": id_valor,
        "titulo": titulo,
        "solicitante": fields.get('Solicitante') or '',
        "status": status,
        "prioridade": prioridade,
        "setorAtendimento": setor,
        "descricao": fields.get('Descricao') or '',
        "data": data_abertura,
        "slaVencido": sla_vencido,
        "slaAtraso": atraso_str,
        "slaAberto": aberto_str,
        "slaHoras": SLA_HORAS.get(prioridade, 8)
    }
    
    chamados.append(chamado)

# ========== SALVAR JSON ==========
print(f"\n💾 Salvando {len(chamados)} chamado(s) em JSON...\n")

output = {
    "atualizado_em": datetime.now().isoformat(),
    "total_chamados": len(chamados),
    "chamados": chamados
}

with open(JSON_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("="*80)
print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
print("="*80)
print(f"\n📊 {len(chamados)} chamado(s) sincronizado(s)")
print(f"📁 Arquivo salvo: {JSON_FILE}\n")
