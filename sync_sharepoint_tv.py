#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SINCRONIZADOR SHAREPOINT → JSON
✅ Sincroniza a cada 5 minutos
✅ Gera chamados_sync.json
✅ Calcula SLA dinamicamente
⚠️  Usa variáveis de ambiente para segurança
✅ CORRIGIDO: Campo "Escolhas" para Setor de Atendimento
"""

import os
import requests
import json
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv

# ========== CARREGAR .env ==========
load_dotenv()

# ========== CREDENCIAIS (via .env) ==========
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')

# ========== SHAREPOINT ==========
SHAREPOINT_DOMAIN = os.getenv('SHAREPOINT_DOMAIN', 'unifeb.sharepoint.com')
SITE_PATH = os.getenv('SITE_PATH', '/sites/SuporteDTI')
LIST_NAME = os.getenv('LIST_NAME', 'Chamados')
GRAPH_API = "https://graph.microsoft.com/v1.0"
JSON_FILE = os.getenv('JSON_FILE', 'chamados_sync.json')

# ========== VARIÁVEIS GLOBAIS ==========
access_token = None
site_id = None
list_id = None

# ========== SLA POR PRIORIDADE (HORAS) ==========
SLA_HORAS = {
    'Alta': 2,
    'Média': 8,
    'Baixa': 24
}

# ========== VALIDAR CREDENCIAIS ==========
def validar_credenciais():
    """Verifica se as credenciais foram configuradas"""
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        print("\n❌ ERRO: Credenciais não configuradas!")
        print("📝 Passos:")
        print("   1. Copie o arquivo '.env.example' → '.env'")
        print("   2. Abra '.env' e preencha com suas credenciais do Azure")
        print("   3. NUNCA commite o arquivo '.env' no Git!")
        print("\n💡 Guia: https://docs.microsoft.com/en-us/azure/active-directory/")
        exit(1)
    print("✅ Credenciais carregadas do .env")

# ========== AUTENTICAÇÃO ==========
def autenticar_azure():
    """Obtém token OAuth2 do Azure"""
    global access_token
    
    print("🔐 Autenticando no Azure AD...")
    auth_url = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token'
    auth_data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default',
        'grant_type': 'client_credentials'
    }
    
    try:
        response = requests.post(auth_url, data=auth_data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erro: {response.status_code}")
            return False
        
        access_token = response.json().get('access_token')
        print("✅ Autenticado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

# ========== OBTER IDS ==========
def obter_site_e_lista():
    """Obtém Site ID e List ID do SharePoint"""
    global site_id, list_id
    
    print("📍 Obtendo Site ID e List ID...")
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        # Site ID
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=30)
        
        if site_response.status_code != 200:
            print(f"❌ Erro ao obter site: {site_response.status_code}")
            return False
        
        site_id = site_response.json().get('id')
        print(f"✅ Site ID obtido")
        
        # List ID
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=30)
        
        if list_response.status_code != 200:
            print(f"❌ Erro ao obter lista: {list_response.status_code}")
            return False
        
        list_id = list_response.json().get('id')
        print(f"✅ List ID obtido")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

# ========== CALCULAR SLA ==========
def calcular_sla(data_abertura_str, prioridade, status):
    """Calcula se SLA foi vencido"""
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
        print(f"   ⚠️  Erro ao calcular SLA: {e}")
        return False, 0, "Erro", "0h"

# ========== SINCRONIZAR ==========
def sincronizar():
    """Sincroniza dados do SharePoint para JSON"""
    
    print("\n" + "="*70)
    print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - SINCRONIZANDO...")
    print("="*70)
    
    try:
        if not autenticar_azure():
            print("❌ Falha na autenticação!")
            return False
        
        if not obter_site_e_lista():
            print("❌ Falha ao obter IDs!")
            return False
        
        print("\n📋 Lendo chamados do SharePoint...")
        
        headers = {'Authorization': f'Bearer {access_token}'}
        items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields"
        
        response = requests.get(items_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erro ao ler itens: {response.status_code}")
            return False
        
        items = response.json().get('value', [])
        print(f"✅ {len(items)} item(ns) encontrado(s)")
        
        chamados = []
        
        for item in items:
            fields = item.get('fields', {})
            
            id_valor = str(fields.get('id') or fields.get('ID') or fields.get('Id') or '')
            id_valor = str(id_valor).strip()
            
            titulo = fields.get('Title') or fields.get('Titulo') or ''
            
            if not id_valor or id_valor == '0' or id_valor == 'None':
                continue
            
            if not titulo or len(titulo.strip()) < 3:
                continue
            
            titulo_lower = titulo.lower()
            TERMOS_LIXO = [
                'flow', 'automate', 'power', 'erro', 'error', 'falha', 'failed',
                'desenvolvimento', 'habilidades', 'learn', 'training', 'microsoft',
                'power automate', 'flow result', 'microsoft flow', 'noreply',
                'notification', 'notificação', 'teste', 'test', 'demo'
            ]
            
            if any(termo in titulo_lower for termo in TERMOS_LIXO):
                continue
            
            # ✅ CORRIGIDO: "Escolhas" é o campo correto!
            setor = (
                fields.get('Escolhas') or  # ← CAMPO CORRETO NO SHAREPOINT
                fields.get('SetordeAtendimento') or
                fields.get('SetorDeAtendimento') or 
                fields.get('Setor de Atendimento') or 
                fields.get('SetorAtendimento') or 
                fields.get('Setor') or 
                'Geral'
            )
            
            prioridade = fields.get('Prioridade') or 'Média'
            status = fields.get('Status') or 'Aberto'
            data_abertura = fields.get('Created') or fields.get('created') or ''
            
            sla_vencido, horas_aberto, atraso_str, aberto_str = calcular_sla(
                data_abertura, prioridade, status
            )
            
            print(f"   ✅ #{id_valor} - {titulo[:40]} | Setor: {setor} | SLA: {'VENCIDO' if sla_vencido else 'OK'}")
            
            chamado = {
                "id": id_valor,
                "titulo": titulo,
                "solicitante": fields.get('Solicitante') or fields.get('Author') or '',
                "status": status,
                "prioridade": prioridade,
                "setorAtendimento": setor,
                "descricao": fields.get('Descricao') or fields.get('Description') or '',
                "data": data_abertura,
                "slaVencido": sla_vencido,
                "slaAtraso": atraso_str,
                "slaAberto": aberto_str,
                "slaHoras": SLA_HORAS.get(prioridade, 8)
            }
            
            chamados.append(chamado)
        
        print(f"\n💾 Salvando {len(chamados)} chamado(s) em JSON...")
        
        output = {
            "atualizado_em": datetime.now().isoformat(),
            "total_chamados": len(chamados),
            "chamados": chamados
        }
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Arquivo '{JSON_FILE}' salvo!")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        print("="*70 + "\n")
        return False

# ========== AGENDADOR ==========
def agendar_sincronizacao():
    """Agenda sincronização a cada 5 minutos"""
    
    print("\n🕐 AGENDA DE SINCRONIZAÇÃO")
    print("="*70)
    print("✅ Primeira sincronização: AGORA")
    print("✅ Próximas sincronizações: a cada 5 minutos")
    print("📍 Horário do sistema:", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    print("💡 Dica: Deixe este terminal aberto!")
    print("="*70 + "\n")
    
    sincronizar()
    
    schedule.every(5).minutes.do(sincronizar)
    
    print("🚀 Aguardando próxima sincronização...\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Sincronização parada pelo usuário")
        print("✅ Até logo!")

# ========== MAIN ==========
if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎯 SINCRONIZADOR UNIFEB - DASHBOARD TV")
    print("📊 SLA: Alta=2h | Média=8h | Baixa=24h")
    print("✅ CORRIGIDO: Campo 'Escolhas' para Setor de Atendimento")
    print("="*70 + "\n")
    
    validar_credenciais()
    agendar_sincronizacao()
