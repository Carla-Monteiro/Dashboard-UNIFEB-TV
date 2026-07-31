#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SINCRONIZADOR CONTÍNUO - RODANDO 24/7 NO RENDER
✅ Sincroniza a cada 10 segundos
✅ Roda em background sem bloquear o backend
"""

import os
import requests
import json
import time
from datetime import datetime
import threading

# Credenciais
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')

SHAREPOINT_DOMAIN = "unifeb.sharepoint.com"
SITE_PATH = "/sites/SuporteDTI"
LIST_NAME = "Chamados"
GRAPH_API = "https://graph.microsoft.com/v1.0"
JSON_FILE = "chamados_sync.json"

SLA_HORAS = {'Alta': 2, 'Média': 8, 'Baixa': 24}

# ========== MAPEAMENTO DE DEPARTAMENTOS ==========
EMAIL_SETOR_MAPPING = {
    'almoxarifado': 'Almoxarifado',
    'biblioteca': 'Biblioteca',
    'coordenacao': 'Coordenação de Professores',
    'clinica': 'Clínica Odontológica',
    'colegio': 'Colégio FEB',
    'dti': 'Departamento de Tecnologia',
    'matricula': 'Matrícula',
    'coordenacao_lab': 'Coordenação Laboratórios',
    'laboratorio': 'Coordenação Laboratórios',
    'manutencao': 'Manutenção',
    'cpa': 'Comissão Própria de Avaliação (CPA)',
    'neu': 'NEU',
    'marketing': 'Marketing',
    'nape': 'NAPE',
    'npj': 'Núcleo Práticas Jurídicas',
    'financeiro': 'Atendimento Financeiro',
    'pradm': 'PRADM',
    'dejur': 'Departamento Jurídico - DEJUR',
    'proaluno': 'Pró Aluno',
    'reitoria': 'Reitoria',
    'rh': 'RH',
    'secretaria': 'Secretaria',
    'conselho': 'Conselho Curador',
    'clivet': 'Clínica Medicina Veterinária',
    'sala_professor': 'Sala Atendimento Professor ao Aluno',
    'cartorio': 'Cartório - Núcleo Práticas Jurídicas',
    'sala_professores': 'Sala dos Professores',
    'ouvidoria': 'Ouvidoria',
    'sustentabilidade': 'Núcleo de Sustentabilidade',
    'labinfo': 'Laboratórios de Informática',
    'fisio': 'Clínica de Fisioterapia',
    'nac': 'NAC',
}

def extrair_setor_do_email(email):
    """Extrai o setor baseado no padrão do email (nome.setor@feb.br)"""
    try:
        if not email:
            return None
        
        email_lower = email.lower().strip()
        if '@' not in email_lower or '.' not in email_lower:
            return None
        
        # Extrair parte antes do @
        parte_email = email_lower.split('@')[0]
        
        # Extrair última parte após ponto
        departamento_sigla = parte_email.split('.')[-1]
        
        setor = EMAIL_SETOR_MAPPING.get(departamento_sigla)
        if setor:
            print(f"✅ Setor extraído do email '{email}': {setor}")
        return setor
        
    except Exception as e:
        print(f"❌ Erro ao extrair setor: {e}")
        return None

def preencher_setores_faltantes(items, headers):
    """Detecta chamados sem setor e preenche automaticamente baseado no email"""
    try:
        for item in items:
            item_id = item.get('id')
            setor_atual = item.get('fields', {}).get('SetordeAtendimento', '').strip()
            email = item.get('fields', {}).get('Email', '').strip()
            
            # Se não tem setor mas tem email, preencher automaticamente
            if not setor_atual and email:
                setor_novo = extrair_setor_do_email(email)
                if setor_novo:
                    print(f"\n🔄 Preenchendo setor para chamado #{item.get('fields', {}).get('Title')}")
                    # Atualizar no SharePoint
                    site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
                    site_response = requests.get(site_url, headers=headers, timeout=10)
                    site_id = site_response.json().get('id')
                    
                    list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
                    list_response = requests.get(list_url, headers=headers, timeout=10)
                    list_id = list_response.json().get('id')
                    
                    update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
                    payload = {
                        "fields": {
                            "SetordeAtendimento": setor_novo
                        }
                    }
                    
                    update_response = requests.patch(update_url, headers=headers, json=payload, timeout=10)
                    if update_response.status_code in [200, 204]:
                        print(f"✅ Setor atualizado para: {setor_novo}")
                    else:
                        print(f"❌ Erro ao atualizar: {update_response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao preencher setores: {e}")

def sincronizar():
    """Função que sincroniza com SharePoint"""
    try:
        # ========== AUTENTICAR ==========
        auth_url = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token'
        auth_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        
        response = requests.post(auth_url, data=auth_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Erro autenticação: {response.status_code}")
            return False
        
        access_token = response.json().get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # ========== OBTER SITE E LIST ID ==========
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        if site_response.status_code != 200:
            return False
        
        site_id = site_response.json().get('id')
        
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        if list_response.status_code != 200:
            return False
        
        list_id = list_response.json().get('id')
        
        # ========== BUSCAR ITENS ==========
        items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields&$top=100"
        items_response = requests.get(items_url, headers=headers, timeout=10)
        
        if items_response.status_code != 200:
            return False
        
        items = items_response.json().get('value', [])
        
        # ========== PREENCHER SETORES FALTANTES AUTOMATICAMENTE ==========
        print("\n🔍 Verificando chamados sem setor...")
        preencher_setores_faltantes(items, headers)
        
        # ========== PROCESSAR ITENS ==========
        def calcular_sla(data_abertura_str, prioridade, status):
            try:
                if status and ('concluído' in status.lower() or 'resolvido' in status.lower()):
                    return False, 0, 'Concluído', '0h'
                
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
            except:
                return False, 0, "Erro", "0h"
        
        chamados = []
        
        for item in items:
            fields = item.get('fields', {})
            
            id_valor = str(fields.get('id') or '')
            titulo = fields.get('Title') or ''
            
            if not id_valor or id_valor == '0' or not titulo or len(titulo.strip()) < 3:
                continue
            
            setor = (
                fields.get('SetordeAtendimento') or
                fields.get('SetorDeAtendimento') or 
                fields.get('Setor de Atendimento') or 
                'Geral'
            )
            
            prioridade = fields.get('Prioridade') or 'Média'
            status = fields.get('Status') or 'Aberto'
            data_abertura = fields.get('Created') or ''
            
            sla_vencido, horas_aberto, atraso_str, aberto_str = calcular_sla(
                data_abertura, prioridade, status
            )
            
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
        output = {
            "atualizado_em": datetime.now().isoformat(),
            "total_chamados": len(chamados),
            "chamados": chamados
        }
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Sincronizado: {len(chamados)} chamados")
        return True
        
    except Exception as e:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Erro na sincronização: {e}")
        return False


def sincronizar_continuamente():
    """Loop que sincroniza continuamente"""
    print("🚀 Iniciando sincronização contínua...")
    print(f"📊 A cada 10 segundos\n")
    
    while True:
        try:
            sincronizar()
        except Exception as e:
            print(f"❌ Erro no loop: {e}")
        
        time.sleep(10)  # Aguarda 10 segundos


if __name__ == "__main__":
    # Rodar em thread background
    thread = threading.Thread(target=sincronizar_continuamente, daemon=True)
    thread.start()
    
    print("✅ Sincronização iniciada em background!")
    print("   Backend pode rodar normalmente...\n")
    
    # Manter a thread viva
    while True:
        time.sleep(1)
