#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir horários de chamados baseado nos e-mails recebidos
Busca a hora real do e-mail no Exchange e atualiza DataAbertura no SharePoint
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========================================
# CONFIGURAÇÕES
# ========================================

# Substitua com suas credenciais/tokens
SHAREPOINT_SITE_URL = "https://unifeb.sharepoint.com/sites/SuporteDTI"
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

# Será preciso de um token de acesso válido
# Você pode obter usando Azure AD / Microsoft Identity

class EmailHorarioCorretor:
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

    def obter_chamados_email(self) -> List[Dict]:
        """Obtém todos os chamados com Origem = 'E-mail Suporte'"""
        try:
            # Obter site ID
            site_response = requests.get(
                f"{GRAPH_API_BASE}/sites/root:/sites/SuporteDTI",
                headers=self.headers
            )
            site_id = site_response.json()['id']

            # Obter lista ID
            lists_response = requests.get(
                f"{GRAPH_API_BASE}/sites/{site_id}/lists?$filter=displayName eq 'Chamados'",
                headers=self.headers
            )
            list_id = lists_response.json()['value'][0]['id']

            # Obter chamados com Origem = 'E-mail Suporte'
            filter_query = "fields/Origem eq 'E-mail Suporte'"
            items_url = f"{GRAPH_API_BASE}/sites/{site_id}/lists/{list_id}/items?$expand=fields&$filter={filter_query}"

            items_response = requests.get(items_url, headers=self.headers)
            chamados = items_response.json().get('value', [])

            logger.info(f"✅ {len(chamados)} chamados de e-mail encontrados")
            return chamados

        except Exception as e:
            logger.error(f"❌ Erro ao obter chamados: {e}")
            return []

    def buscar_email_no_exchange(self, email_solicitante: str, assunto: str) -> Optional[Dict]:
        """
        Busca o e-mail no Exchange pelo solicitante e assunto

        Args:
            email_solicitante: E-mail de quem enviou
            assunto: Assunto do e-mail (título do chamado)

        Returns:
            Dicionário com dados do e-mail ou None se não encontrar
        """
        try:
            # Buscar e-mail com filtro: from + subject
            filter_query = f"from/emailAddress/address eq '{email_solicitante}' and subject eq '{assunto}'"
            mail_url = f"{GRAPH_API_BASE}/me/messages?$filter={filter_query}&$orderby=receivedDateTime desc&$top=1"

            response = requests.get(mail_url, headers=self.headers)
            emails = response.json().get('value', [])

            if emails:
                logger.info(f"✅ E-mail encontrado: {assunto}")
                return emails[0]
            else:
                logger.warning(f"⚠️ E-mail NÃO encontrado: {assunto} (de {email_solicitante})")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao buscar e-mail: {e}")
            return None

    def converter_horario_email(self, received_datetime_str: str) -> str:
        """
        Converte horário ISO do e-mail para formato DD/MM/YYYY HH:MM

        Args:
            received_datetime_str: Horário em ISO format (ex: 2026-10-02T07:54:00Z)

        Returns:
            Horário formatado: DD/MM/YYYY HH:MM
        """
        try:
            # Parse ISO format
            dt = datetime.fromisoformat(received_datetime_str.replace('Z', '+00:00'))

            # Converter para São Paulo (UTC-3)
            tz_sp = dt.astimezone().tzinfo
            from datetime import timezone, timedelta as td
            tz_sp = timezone(td(hours=-3))
            dt_sp = dt.astimezone(tz_sp)

            return dt_sp.strftime('%d/%m/%Y %H:%M')
        except Exception as e:
            logger.error(f"❌ Erro ao converter horário: {e}")
            return None

    def horarios_compatíveis(self, hora1: str, hora2: str, margem_minutos: int = 5) -> bool:
        """
        Verifica se dois horários são compatíveis (mesma hora, com margem)

        Args:
            hora1: Primeiro horário (DD/MM/YYYY HH:MM)
            hora2: Segundo horário (DD/MM/YYYY HH:MM)
            margem_minutos: Margem de diferença aceita

        Returns:
            True se forem iguais (com margem), False caso contrário
        """
        try:
            dt1 = datetime.strptime(hora1, '%d/%m/%Y %H:%M')
            dt2 = datetime.strptime(hora2, '%d/%m/%Y %H:%M')

            diferenca = abs((dt1 - dt2).total_seconds() / 60)
            return diferenca <= margem_minutos
        except:
            return False

    def atualizar_chamado(self, site_id: str, list_id: str, item_id: str, nova_hora: str) -> bool:
        """
        Atualiza o DataAbertura do chamado no SharePoint

        Args:
            site_id: ID do site
            list_id: ID da lista
            item_id: ID do item (chamado)
            nova_hora: Novo horário (DD/MM/YYYY HH:MM)

        Returns:
            True se atualizado com sucesso
        """
        try:
            url = f"{GRAPH_API_BASE}/sites/{site_id}/lists/{list_id}/items/{item_id}/fields"

            data = {
                "DataAbertura": nova_hora
            }

            response = requests.patch(url, headers=self.headers, json=data)

            if response.status_code in [200, 204]:
                logger.info(f"✅ Chamado {item_id} atualizado para {nova_hora}")
                self.chamados_corrigidos += 1
                return True
            else:
                logger.error(f"❌ Erro ao atualizar chamado {item_id}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar: {e}")
            return False

    def processar_chamados(self):
        """Processa todos os chamados e corrige horários"""

        chamados = self.obter_chamados_email()

        if not chamados:
            logger.warning("⚠️ Nenhum chamado de e-mail encontrado")
            return

        for chamado in chamados:
            try:
                fields = chamado.get('fields', {})

                # Extrair informações
                item_id = chamado.get('id')
                titulo = fields.get('Title', '')
                email_solicitante = fields.get('Email', '')
                data_abertura_atual = fields.get('DataAbertura', '')

                logger.info(f"📋 Processando: ID {item_id} - {titulo}")

                # Buscar e-mail
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
                if self.horarios_compatíveis(data_abertura_atual, hora_correta):
                    logger.info(f"✓ Horário já está correto: {hora_correta}")
                    self.chamados_ja_corretos += 1
                else:
                    logger.warning(f"❌ Horário incorreto! Atual: {data_abertura_atual} → Correto: {hora_correta}")
                    # TODO: Descomentar quando token estiver pronto
                    # self.atualizar_chamado(site_id, list_id, item_id, hora_correta)

            except Exception as e:
                logger.error(f"❌ Erro processando chamado: {e}")
                continue

        # Resumo
        self.exibir_resumo()

    def exibir_resumo(self):
        """Exibe resumo do processamento"""
        total = self.chamados_corrigidos + self.chamados_ja_corretos + self.chamados_nao_encontrados

        print("\n" + "="*50)
        print("📊 RESUMO DO PROCESSAMENTO")
        print("="*50)
        print(f"✅ Chamados CORRIGIDOS: {self.chamados_corrigidos}")
        print(f"✓ Chamados já CORRETOS: {self.chamados_ja_corretos}")
        print(f"❌ E-mails NÃO ENCONTRADOS: {self.chamados_nao_encontrados}")
        print(f"📋 TOTAL PROCESSADO: {total}")
        print("="*50 + "\n")


# ========================================
# FUNÇÃO PRINCIPAL
# ========================================

def main():
    """Função principal"""

    print("\n🚀 Iniciando correção de horários...\n")

    # TODO: Obter token válido
    # access_token = obter_token_do_azure()

    # Por enquanto, você precisa passar o token manualmente
    access_token = input("📝 Digite o token de acesso (Bearer token): ").strip()

    if not access_token:
        logger.error("❌ Token não fornecido!")
        return

    # Inicializar corretor
    corretor = EmailHorarioCorretor(access_token)

    # Processar chamados
    corretor.processar_chamados()

    print("\n✨ Processamento finalizado!")


if __name__ == "__main__":
    main()
