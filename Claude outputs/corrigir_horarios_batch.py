#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir horários de chamados de e-mail em batch
Conecta ao SharePoint, busca e-mails no Exchange, compara horários e atualiza
"""

import requests
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================================
# CONFIGURAÇÕES
# ========================================

GRAPH_API = "https://graph.microsoft.com/v1.0"
SHAREPOINT_DOMAIN = "unifeb.sharepoint.com"
SITE_PATH = "/sites/SuporteDTI"
LIST_NAME = "Chamados"

class CorretorHorariosEmail:
    """Corrige horários de chamados baseado em e-mails do Exchange"""

    def __init__(self, access_token: str):
        """
        Inicializa com token de acesso

        Args:
            access_token: Token JWT válido para Microsoft Graph API
        """
        self.token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        self.chamados_corrigidos = 0
        self.chamados_ja_corretos = 0
        self.chamados_nao_encontrados = 0

    def obter_site_e_lista(self) -> Tuple[Optional[str], Optional[str]]:
        """Obtém IDs do site e da lista"""
        try:
            # Buscar site
            site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
            site_response = requests.get(site_url, headers=self.headers, timeout=10)

            if site_response.status_code != 200:
                logger.error(f"❌ Erro ao conectar site: {site_response.status_code}")
                logger.error(f"   Resposta: {site_response.text}")
                return None, None

            site_id = site_response.json().get('id')
            logger.info(f"✅ Site encontrado: {site_id}")

            # Buscar lista
            list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
            list_response = requests.get(list_url, headers=self.headers, timeout=10)

            if list_response.status_code != 200:
                logger.error(f"❌ Erro ao conectar lista '{LIST_NAME}': {list_response.status_code}")
                logger.error(f"   Resposta: {list_response.text}")
                return None, None

            list_id = list_response.json().get('id')
            logger.info(f"✅ Lista encontrada: {list_id}")

            return site_id, list_id

        except Exception as e:
            logger.error(f"❌ Erro ao obter site e lista: {e}")
            return None, None

    def obter_chamados_email(self, site_id: str, list_id: str) -> List[Dict]:
        """Obtém todos os chamados com Origem = 'E-mail Suporte'"""
        try:
            # Filtro para chamados de e-mail
            filter_query = "fields/Origem eq 'E-mail Suporte'"
            items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields&$filter={filter_query}"

            logger.info(f"🔍 Buscando chamados com filtro: {filter_query}")
            items_response = requests.get(items_url, headers=self.headers, timeout=10)

            if items_response.status_code != 200:
                logger.error(f"❌ Erro ao buscar chamados: {items_response.status_code}")
                logger.error(f"   Resposta: {items_response.text}")
                return []

            chamados = items_response.json().get('value', [])
            logger.info(f"✅ {len(chamados)} chamados de e-mail encontrados")

            return chamados

        except Exception as e:
            logger.error(f"❌ Erro ao obter chamados: {e}")
            return []

    def buscar_email_no_exchange(self, email_solicitante: str, assunto: str) -> Optional[Dict]:
        """Busca o e-mail no Exchange pelo solicitante e assunto"""
        try:
            # Escapar caracteres especiais no assunto
            assunto_escaped = assunto.replace("'", "''")

            filter_query = f"from/emailAddress/address eq '{email_solicitante}' and subject eq '{assunto_escaped}'"
            mail_url = f"{GRAPH_API}/me/messages?$filter={filter_query}&$orderby=receivedDateTime desc&$top=1"

            response = requests.get(mail_url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                logger.warning(f"⚠️ Erro ao buscar e-mail: {response.status_code}")
                return None

            emails = response.json().get('value', [])

            if emails:
                logger.info(f"✅ E-mail encontrado: {assunto}")
                return emails[0]
            else:
                logger.warning(f"⚠️ E-mail NÃO encontrado: {assunto}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao buscar e-mail: {e}")
            return None

    def converter_horario_email(self, received_datetime_str: str) -> Optional[str]:
        """Converte horário ISO do e-mail para formato DD/MM/YYYY HH:MM (São Paulo)"""
        try:
            # Parse ISO format
            dt = datetime.fromisoformat(received_datetime_str.replace('Z', '+00:00'))

            # Converter para São Paulo (UTC-3 com ajuste)
            tz_sp = timezone(timedelta(hours=-7))
            dt_sp = dt.astimezone(tz_sp)

            return dt_sp.strftime('%d/%m/%Y %H:%M')
        except Exception as e:
            logger.error(f"❌ Erro ao converter horário: {e}")
            return None

    def atualizar_chamado(self, site_id: str, list_id: str, item_id: str, nova_hora: str) -> bool:
        """Atualiza o DataAbertura do chamado no SharePoint"""
        try:
            url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}/fields"

            data = {"DataAbertura": nova_hora}

            response = requests.patch(url, headers=self.headers, json=data, timeout=10)

            if response.status_code in [200, 204]:
                logger.info(f"✅ Chamado {item_id} atualizado para {nova_hora}")
                self.chamados_corrigidos += 1
                return True
            else:
                logger.error(f"❌ Erro ao atualizar: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar: {e}")
            return False

    def processar_chamados(self, site_id: str, list_id: str):
        """Processa todos os chamados e corrige horários"""

        chamados = self.obter_chamados_email(site_id, list_id)

        if not chamados:
            logger.warning("⚠️ Nenhum chamado de e-mail encontrado")
            return

        for idx, chamado in enumerate(chamados, 1):
            try:
                fields = chamado.get('fields', {})

                item_id = chamado.get('id')
                titulo = fields.get('Title', '')
                email_solicitante = fields.get('Email', '')
                data_abertura_atual = fields.get('DataAbertura', '')

                logger.info(f"\n📋 [{idx}/{len(chamados)}] Processando: {titulo}")
                logger.info(f"   ID: {item_id} | Email: {email_solicitante}")

                # Buscar e-mail no Exchange
                email = self.buscar_email_no_exchange(email_solicitante, titulo)

                if not email:
                    self.chamados_nao_encontrados += 1
                    continue

                # Extrair horário correto
                received_time = email.get('receivedDateTime', '')
                hora_correta = self.converter_horario_email(received_time)

                if not hora_correta:
                    logger.warning(f"⚠️ Não conseguiu converter horário do e-mail")
                    continue

                # Comparar horários
                if data_abertura_atual == hora_correta:
                    logger.info(f"✓ Horário já está correto: {hora_correta}")
                    self.chamados_ja_corretos += 1
                else:
                    logger.warning(f"⚠️ Horário incorreto!")
                    logger.warning(f"   Atual: {data_abertura_atual}")
                    logger.warning(f"   Correto: {hora_correta}")

                    # Atualizar chamado
                    self.atualizar_chamado(site_id, list_id, item_id, hora_correta)

            except Exception as e:
                logger.error(f"❌ Erro processando chamado: {e}")
                continue

        # Resumo
        self.exibir_resumo(len(chamados))

    def exibir_resumo(self, total):
        """Exibe resumo do processamento"""
        print("\n" + "="*60)
        print("📊 RESUMO DO PROCESSAMENTO")
        print("="*60)
        print(f"✅ Chamados CORRIGIDOS: {self.chamados_corrigidos}")
        print(f"✓ Chamados já CORRETOS: {self.chamados_ja_corretos}")
        print(f"❌ E-mails NÃO ENCONTRADOS: {self.chamados_nao_encontrados}")
        print(f"📋 TOTAL PROCESSADO: {total}")
        print("="*60 + "\n")


def main():
    """Função principal"""

    print("\n" + "="*60)
    print("🚀 CORRETOR DE HORÁRIOS DE CHAMADOS DE E-MAIL")
    print("="*60 + "\n")

    # Pedir token
    print("📝 Digite o token de acesso do Microsoft (Bearer token):")
    print("   (Você pode gerar com: Get-AzAccessToken -ResourceUrl 'https://graph.microsoft.com' -AsSecureString)")
    print()

    access_token = input("Token: ").strip()

    if not access_token:
        logger.error("❌ Token não fornecido!")
        sys.exit(1)

    # Inicializar corretor
    corretor = CorretorHorariosEmail(access_token)

    # Obter site e lista
    logger.info("🔗 Conectando ao SharePoint...")
    site_id, list_id = corretor.obter_site_e_lista()

    if not site_id or not list_id:
        logger.error("❌ Não foi possível conectar ao SharePoint!")
        sys.exit(1)

    # Processar chamados
    logger.info("\n⏱️ Iniciando correção de horários...\n")
    corretor.processar_chamados(site_id, list_id)

    print("\n✨ Processamento finalizado!")


if __name__ == "__main__":
    main()
