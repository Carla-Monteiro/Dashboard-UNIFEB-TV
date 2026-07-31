#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMPORTANTE: Este arquivo substitui o form_handler.py existente
Versão: 2.0 - Com suporte a QR Code #SuporteUNIFEB
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import requests
from datetime import datetime, timedelta
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import openpyxl
from io import BytesIO
from dotenv import load_dotenv
import logging
import threading  # ← NOVO!

# Setup logging para debug
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(app)

# ========== CONSTANTES ==========
GRAPH_API = "https://graph.microsoft.com/v1.0"
SHAREPOINT_DOMAIN = "unifeb.sharepoint.com"
SITE_PATH = "/sites/SuporteDTI"
LIST_NAME = "Chamados"

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'suporte.dti@feb.br')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# ========== ROTEAMENTO QR CODE ==========

CATEGORIAS_ROTEAMENTO = {
    # MANUTENÇÃO
    '💡 Energia Elétrica': {'tipo': 'manutencao', 'emails': ['mendes.engenharia@feb.br', 'suporte.dti@feb.br']},
    '❄️ Ar Condicionado': {'tipo': 'manutencao', 'emails': ['mendes.engenharia@feb.br', 'suporte.dti@feb.br']},
    '🔐 Fechadura/Porta': {'tipo': 'manutencao', 'emails': ['mendes.engenharia@feb.br', 'suporte.dti@feb.br']},
    '🪟 Janela': {'tipo': 'manutencao', 'emails': ['mendes.engenharia@feb.br', 'suporte.dti@feb.br']},
    '🔘 Interruptores': {'tipo': 'manutencao', 'emails': ['mendes.engenharia@feb.br', 'suporte.dti@feb.br']},
    '🚪 Outra': {'tipo': 'manutencao', 'emails': ['mendes.engenharia@feb.br', 'suporte.dti@feb.br']},
    
    # NAEM
    '📽️ Projetor': {'tipo': 'naem', 'emails': ['naem@feb.br', 'suporte.dti@feb.br']},
    '🎮 Controle Projetor': {'tipo': 'naem', 'emails': ['naem@feb.br', 'suporte.dti@feb.br']},
    '📺 Cabo VGA': {'tipo': 'naem', 'emails': ['naem@feb.br', 'suporte.dti@feb.br']},
    '🔌 Adaptador VGA/HDMI': {'tipo': 'naem', 'emails': ['naem@feb.br', 'suporte.dti@feb.br']},
    '📡 Cabo HDMI': {'tipo': 'naem', 'emails': ['naem@feb.br', 'suporte.dti@feb.br']},
    '🔊 Cabos de Som': {'tipo': 'naem', 'emails': ['naem@feb.br', 'suporte.dti@feb.br']},
    '❄️ Controle A/C': {'tipo': 'naem', 'emails': ['naem@feb.br', 'suporte.dti@feb.br']},
    '📻 Outro': {'tipo': 'naem', 'emails': ['naem@feb.br', 'suporte.dti@feb.br']},
    
    # TI
    '🌐 Internet/Wi-Fi': {'tipo': 'ti', 'emails': ['suporte.dti@feb.br']},
    '💻 Computador': {'tipo': 'ti', 'emails': ['suporte.dti@feb.br']},
    '⌨️ Teclado': {'tipo': 'ti', 'emails': ['suporte.dti@feb.br']},
    '🖱️ Mouse': {'tipo': 'ti', 'emails': ['suporte.dti@feb.br']},
    '📞 Telefone': {'tipo': 'ti', 'emails': ['suporte.dti@feb.br']},
    '🔴 Outro': {'tipo': 'ti', 'emails': ['suporte.dti@feb.br']},
}

NOMES_SETORES = {
    'manutencao': 'Manutenção Predial',
    'naem': 'Multimídia (NAEM)',
    'ti': 'TI / Internet'
}

# ========== FUNÇÕES AUXILIARES ==========

def get_access_token():
    """Obtém token do SharePoint"""
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
        logger.error(f"Exceção get_access_token: {e}")
        return None

def gerar_numero_chamado():
    """Gera número único do chamado"""
    return datetime.now().strftime('%Y%m%d%H%M%S')

def obter_roteamento(categoria):
    """Obtém emails de destino"""
    if categoria in CATEGORIAS_ROTEAMENTO:
        return CATEGORIAS_ROTEAMENTO[categoria]
    return {'tipo': 'ti', 'emails': ['suporte.dti@feb.br']}

def enviar_email(destinatario, assunto, html):
    """Envia email via SMTP"""
    try:
        logger.info(f"[EMAIL] Iniciando envio para: {destinatario}")
        logger.info(f"[EMAIL] Assunto: {assunto}")
        logger.info(f"[EMAIL] EMAIL_FROM: {EMAIL_FROM}")
        logger.info(f"[EMAIL] EMAIL_PASSWORD: {'*' * len(EMAIL_PASSWORD) if EMAIL_PASSWORD else 'NÃO CONFIGURADO!'}")
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = assunto
        msg['From'] = EMAIL_FROM
        msg['To'] = destinatario
        
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        logger.info(f"[EMAIL] Mensagem montada")
        
        try:
            logger.info(f"[EMAIL] Conectando ao servidor SMTP: smtp.office365.com:587")
            server = smtplib.SMTP("smtp.office365.com", 587, timeout=10)
            logger.info(f"[EMAIL] ✅ Conectado ao servidor!")
        except Exception as e:
            logger.error(f"[EMAIL] ❌ ERRO ao conectar: {e}", exc_info=True)
            return False
        
        try:
            logger.info(f"[EMAIL] Iniciando TLS...")
            server.starttls()
            logger.info(f"[EMAIL] ✅ TLS iniciado!")
        except Exception as e:
            logger.error(f"[EMAIL] ❌ ERRO ao iniciar TLS: {e}", exc_info=True)
            server.quit()
            return False
        
        try:
            logger.info(f"[EMAIL] Fazendo login com: {EMAIL_FROM}")
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            logger.info(f"[EMAIL] ✅ Login bem-sucedido!")
        except Exception as e:
            logger.error(f"[EMAIL] ❌ ERRO ao fazer login: {e}", exc_info=True)
            server.quit()
            return False
        
        try:
            logger.info(f"[EMAIL] Enviando mensagem...")
            server.send_message(msg)
            logger.info(f"[EMAIL] ✅ Mensagem enviada!")
        except Exception as e:
            logger.error(f"[EMAIL] ❌ ERRO ao enviar: {e}", exc_info=True)
            server.quit()
            return False
        
        try:
            server.quit()
            logger.info(f"[EMAIL] ✅ Conexão fechada")
        except Exception as e:
            logger.error(f"[EMAIL] ⚠️ ERRO ao fechar conexão: {e}")
        
        logger.info(f"✅ [EMAIL] Email enviado com sucesso para {destinatario}")
        return True
        
    except Exception as e:
        logger.error(f"❌ [EMAIL] ERRO GERAL: {e}", exc_info=True)
        return False

def enviar_emails_background(numero, email_solicitante, emails_destino, html_solicitante, html_responsavel, categoria, bloco, sala, solicitante):
    """Envia emails em thread separada (não bloqueia resposta)"""
    def _enviar():
        try:
            logger.info(f"[THREAD-{numero}] ========== INICIANDO ENVIO DE EMAILS ==========")
            logger.info(f"[THREAD-{numero}] Chamado: {numero}")
            logger.info(f"[THREAD-{numero}] Solicitante: {email_solicitante}")
            logger.info(f"[THREAD-{numero}] Responsáveis: {emails_destino}")
            
            # Email para solicitante
            logger.info(f"[THREAD-{numero}] Enviando email para SOLICITANTE...")
            result1 = enviar_email(email_solicitante, f"✅ Chamado #{numero} Aberto", html_solicitante)
            if result1:
                logger.info(f"[THREAD-{numero}] ✅ Email solicitante enviado!")
            else:
                logger.error(f"[THREAD-{numero}] ❌ Falha ao enviar email solicitante!")
            
            # Emails para responsáveis
            logger.info(f"[THREAD-{numero}] Enviando emails para RESPONSÁVEIS...")
            for email_destino in emails_destino:
                logger.info(f"[THREAD-{numero}] Enviando para: {email_destino}")
                result = enviar_email(email_destino, f"[AVISO #{numero}] {categoria} - {bloco}/{sala}", html_responsavel)
                if result:
                    logger.info(f"[THREAD-{numero}] ✅ Email responsável enviado para {email_destino}")
                else:
                    logger.error(f"[THREAD-{numero}] ❌ Falha ao enviar para {email_destino}")
            
            logger.info(f"[THREAD-{numero}] ========== CONCLUSÃO DE ENVIO DE EMAILS ==========")
        except Exception as e:
            logger.error(f"[THREAD-{numero}] ❌ ERRO GERAL NA THREAD: {e}", exc_info=True)
    
    # Cria thread e executa sem bloquear
    logger.info(f"[MAIN] Criando thread para envio de emails do chamado {numero}")
    thread = threading.Thread(target=_enviar, daemon=True, name=f"email-{numero}")
    thread.start()
    logger.info(f"[MAIN] Thread iniciada: {thread.name}")

def gerar_html_confirmacao_solicitante(numero, solicitante, bloco, sala, categoria):
    """Email SIMPLES para solicitante - SEM botão"""
    html = f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1a237e, #283593); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ padding: 20px; }}
                .numero {{ font-size: 28px; color: #ffa500; font-weight: bold; text-align: center; margin: 20px 0; }}
                .info {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .footer {{ background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #999; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>#SuporteUNIFEB</h1>
                </div>
                
                <div class="content">
                    <h2 style="color: #1a237e;">✅ Chamado Aberto com Sucesso!</h2>
                    
                    <p>Olá <strong>{solicitante}</strong>,</p>
                    
                    <p>Obrigado por reportar o problema! Seu chamado foi registrado no sistema e nossa equipe já foi notificada.</p>
                    
                    <div class="numero">#{numero}</div>
                    
                    <div class="info">
                        <strong>Detalhes do seu chamado:</strong><br><br>
                        📍 <strong>Bloco:</strong> {bloco}<br>
                        🚪 <strong>Sala:</strong> {sala}<br>
                        ⚙️ <strong>Problema:</strong> {categoria}<br>
                    </div>
                    
                    <p><strong>Próximas etapas:</strong></p>
                    <ul>
                        <li>Nossa equipe analisará o problema</li>
                        <li>Você receberá uma atualização em breve</li>
                        <li>Assim que concluído, enviaremos uma pesquisa de satisfação</li>
                    </ul>
                    
                    <p><strong>Guarde este número para referência:</strong> <span style="color: #ffa500; font-size: 18px;">#{numero}</span></p>
                </div>
                
                <div class="footer">
                    <p>Sistema #SuporteUNIFEB | Gerenciamento em Tempo Real</p>
                </div>
            </div>
        </body>
    </html>
    """
    return html

def gerar_html_responsavel_com_botao(numero, bloco, sala, solicitante, email_solicitante, categoria, descricao, tipo):
    """Email para mendes/naem/dti COM BOTÃO CONCLUIR"""
    nome_setor = NOMES_SETORES.get(tipo, 'Suporte')
    icons = {'manutencao': '🔧', 'naem': '📡', 'ti': '💻'}
    
    html = f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1a237e, #283593); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                .icon {{ font-size: 40px; margin-bottom: 10px; }}
                h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 20px; }}
                .info-row {{ display: flex; margin-bottom: 15px; }}
                .label {{ font-weight: bold; color: #1a237e; width: 140px; }}
                .value {{ color: #333; flex: 1; }}
                .numero {{ font-size: 28px; color: #ffa500; font-weight: bold; text-align: center; margin: 15px 0; }}
                .descricao-box {{ background: #f5f5f5; padding: 15px; border-left: 4px solid #ffa500; margin: 15px 0; border-radius: 5px; }}
                .botao-concluir {{ text-align: center; margin: 30px 0; }}
                .botao-concluir a {{ background: #4caf50; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block; }}
                .botao-concluir a:hover {{ background: #45a049; }}
                .footer {{ background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #999; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="icon">{icons[tipo]}</div>
                    <h1>Novo Aviso de {nome_setor}</h1>
                </div>
                
                <div class="content">
                    <div class="numero">Chamado #{numero}</div>
                    
                    <div class="info-row">
                        <span class="label">📍 Bloco:</span>
                        <span class="value"><strong>{bloco}</strong></span>
                    </div>
                    
                    <div class="info-row">
                        <span class="label">🚪 Sala:</span>
                        <span class="value"><strong>{sala}</strong></span>
                    </div>
                    
                    <div class="info-row">
                        <span class="label">👤 Solicitante:</span>
                        <span class="value"><strong>{solicitante}</strong></span>
                    </div>
                    
                    <div class="info-row">
                        <span class="label">📧 Email:</span>
                        <span class="value"><strong>{email_solicitante}</strong></span>
                    </div>
                    
                    <div class="descricao-box">
                        <strong>⚙️ Tipo de Problema:</strong> {categoria}<br><br>
                        <strong>📝 Descrição:</strong><br>
                        {descricao.replace(chr(10), '<br>')}
                    </div>
                    
                    <p><strong>Quando o problema for resolvido, clique no botão abaixo:</strong></p>
                    
                    <div class="botao-concluir">
                        <a href="https://unifeb-backend.onrender.com/api/concluir-chamado?numero={numero}">
                            ✅ Marcar como Concluído
                        </a>
                    </div>
                    
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        Se o botão não funcionar, acesse:<br>
                        https://unifeb-backend.onrender.com/api/concluir-chamado?numero={numero}
                    </p>
                </div>
                
                <div class="footer">
                    <p>Sistema #SuporteUNIFEB | Gerenciamento em Tempo Real</p>
                </div>
            </div>
        </body>
    </html>
    """
    return html

# ========== ENDPOINTS EXISTENTES (MANTER TUDO) ==========

@app.route('/api/chamados', methods=['GET'])
def get_chamados():
    """Retorna todos os chamados do sync_loop.json"""
    try:
        if os.path.exists('chamados_sync.json'):
            with open('chamados_sync.json', 'r', encoding='utf-8') as f:
                chamados = json.load(f)
            return jsonify(chamados), 200
        else:
            return jsonify([]), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/alertas', methods=['GET'])
def get_alertas():
    """Retorna chamados com SLA crítico"""
    try:
        if os.path.exists('chamados_sync.json'):
            with open('chamados_sync.json', 'r', encoding='utf-8') as f:
                chamados = json.load(f)
            alertas = [c for c in chamados if c.get('slaEmRisco')]
            return jsonify(alertas), 200
        else:
            return jsonify([]), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/metricas', methods=['GET'])
def get_metricas():
    """Retorna métricas do dashboard"""
    try:
        if os.path.exists('chamados_sync.json'):
            with open('chamados_sync.json', 'r', encoding='utf-8') as f:
                chamados = json.load(f)
            
            total = len(chamados)
            vencidos = len([c for c in chamados if c.get('slaVencido')])
            abertos = len([c for c in chamados if c.get('status') == 'Aberto'])
            resolvidos = len([c for c in chamados if c.get('status') == 'Concluído'])
            
            return jsonify({
                "total": total,
                "slaVencido": vencidos,
                "percentualVencido": round((vencidos / total * 100) if total > 0 else 0, 2),
                "abertos": abertos,
                "resolvidos": resolvidos
            }), 200
        else:
            return jsonify({"erro": "Sem dados"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/export-excel', methods=['GET'])
def export_excel():
    """Exporta relatório em Excel"""
    try:
        if not os.path.exists('chamados_sync.json'):
            return jsonify({"erro": "Sem dados"}), 404
        
        with open('chamados_sync.json', 'r', encoding='utf-8') as f:
            chamados = json.load(f)
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Chamados"
        
        headers = ['ID', 'Título', 'Status', 'Prioridade', 'Data Abertura', 'Solicitante', 'Email']
        ws.append(headers)
        
        for chamado in chamados:
            ws.append([
                chamado.get('id', ''),
                chamado.get('titulo', ''),
                chamado.get('status', ''),
                chamado.get('prioridade', ''),
                chamado.get('dataAbertura', ''),
                chamado.get('solicitante', ''),
                chamado.get('email', '')
            ])
        
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        if excel_file:
            return send_file(
                excel_file,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'relatorio_chamados_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
        else:
            return jsonify({"erro": "Erro ao gerar Excel"}), 500
            
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({"erro": str(e)}), 500

# ========== NOVO ENDPOINT QR CODE ==========

@app.route('/api/criar-manutencao', methods=['POST', 'OPTIONS'])
def criar_manutencao():
    """Endpoint para criar aviso via QR Code"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info("=" * 60)
        logger.info("INICIANDO criar_manutencao")
        
        data = request.json
        logger.info(f"Dados recebidos: {data}")
        
        email = data.get('email', '').strip()
        bloco = data.get('bloco', '').strip()
        sala = data.get('sala', '').strip()
        tipo = data.get('tipo', '').strip()
        categoria = data.get('categoria', '').strip()
        descricao = data.get('descricao', '').strip()
        
        # Validação
        if not all([email, bloco, sala, tipo, categoria, descricao]):
            logger.warning("Campos obrigatórios faltando")
            return jsonify({"status": "erro", "mensagem": "Campos obrigatórios faltando"}), 400
        
        # Gerar número
        numero = gerar_numero_chamado()
        logger.info(f"Número chamado gerado: {numero}")
        
        # Obter roteamento
        roteamento = obter_roteamento(categoria)
        emails_destino = roteamento['emails']
        tipo_problema = roteamento['tipo']
        logger.info(f"Roteamento: {emails_destino}, Tipo: {tipo_problema}")
        
        # Extrair nome
        solicitante = email.split('@')[0].replace('.', ' ').title()
        logger.info(f"Solicitante: {solicitante}")
        
        # 1. SALVAR NO SHAREPOINT
        logger.info("Tentando conectar SharePoint...")
        token = get_access_token()
        if not token:
            logger.error("Falha ao obter token SharePoint")
            return jsonify({"status": "erro", "mensagem": "Falha ao conectar SharePoint"}), 401
        
        logger.info("Token obtido com sucesso")
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # Obter site ID
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        logger.info(f"Acessando site: {site_url}")
        site_response = requests.get(site_url, headers=headers, timeout=10)
        logger.info(f"Site response status: {site_response.status_code}")
        
        if site_response.status_code != 200:
            logger.error(f"Erro ao obter site: {site_response.text}")
            return jsonify({"status": "erro", "mensagem": "Erro ao conectar site SharePoint"}), 400
        
        site_id = site_response.json().get('id')
        logger.info(f"Site ID: {site_id}")
        
        # Obter list ID
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        logger.info(f"Acessando lista: {list_url}")
        list_response = requests.get(list_url, headers=headers, timeout=10)
        logger.info(f"List response status: {list_response.status_code}")
        
        if list_response.status_code != 200:
            logger.error(f"Erro ao obter lista: {list_response.text}")
            return jsonify({"status": "erro", "mensagem": "Erro ao conectar lista SharePoint"}), 400
        
        list_id = list_response.json().get('id')
        logger.info(f"List ID: {list_id}")
        
        # Criar item
        create_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items"
        logger.info(f"Criando item em: {create_url}")
        
        payload = {
            "fields": {
                "Title": f"[{numero}] {categoria} - {bloco}/{sala}",
                "Descricao": descricao,
                "Solicitante": solicitante,
                "Email": email,
                "SetordeAtendimento": NOMES_SETORES.get(tipo_problema, 'Geral'),
                "Prioridade": "Alta",
                "Status": "Aberto"
            }
        }
        
        logger.info(f"Payload: {payload}")
        response = requests.post(create_url, headers=headers, json=payload, timeout=10)
        logger.info(f"Create response status: {response.status_code}")
        
        if response.status_code not in [200, 201]:
            logger.error(f"Erro ao criar item: {response.text}")
            return jsonify({"status": "erro", "mensagem": "Erro ao salvar no SharePoint"}), 400
        
        logger.info("Item criado com sucesso no SharePoint")
        
        # 2. EMAILS: DESATIVADO - Power Automate vai fazer!
        logger.info("Emails desativados - Power Automate vai rotear automaticamente")
        
        return jsonify({
            "status": "sucesso",
            "mensagem": "✅ Aviso enviado com sucesso!",
            "numero": numero
        }), 201
        
    except Exception as e:
        logger.error(f"❌ ERRO GERAL: {e}", exc_info=True)
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

# ========== ENDPOINT CONCLUIR CHAMADO ==========

@app.route('/api/concluir-chamado', methods=['GET'])
def concluir_chamado():
    """Marca chamado como concluído e dispara pesquisa"""
    try:
        numero = request.args.get('numero')
        logger.info(f"Concluindo chamado: {numero}")
        
        if not numero:
            return jsonify({"status": "erro", "mensagem": "Número não informado"}), 400
        
        # 1. OBTER TOKEN DO SHAREPOINT
        token = get_access_token()
        if not token:
            logger.error("Falha ao obter token SharePoint")
            return jsonify({"status": "erro", "mensagem": "Falha ao conectar"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # 2. OBTER ITEM PELO TÍTULO (contém o número)
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        site_id = site_response.json().get('id')
        
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        list_id = list_response.json().get('id')
        
        # Query para encontrar item com o número
        query_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$filter=contains(fields/Title, '{numero}')"
        query_response = requests.get(query_url, headers=headers, timeout=10)
        
        if query_response.status_code != 200:
            logger.error(f"Erro ao procurar item: {query_response.text}")
            return jsonify({"status": "erro", "mensagem": "Item não encontrado"}), 404
        
        items = query_response.json().get('value', [])
        if not items:
            logger.error(f"Chamado não encontrado: {numero}")
            return jsonify({"status": "erro", "mensagem": "Chamado não encontrado"}), 404
        
        item = items[0]
        item_id = item.get('id')
        email_solicitante = item.get('fields', {}).get('Email', '')
        titulo = item.get('fields', {}).get('Title', '')
        
        logger.info(f"Item encontrado: {item_id}, Email: {email_solicitante}")
        
        # 3. ATUALIZAR STATUS PARA "CONCLUÍDO"
        update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
        update_payload = {
            "fields": {
                "Status": "Concluído"
            }
        }
        
        update_response = requests.patch(update_url, headers=headers, json=update_payload, timeout=10)
        
        if update_response.status_code not in [200, 204]:
            logger.error(f"Erro ao atualizar: {update_response.text}")
            return jsonify({"status": "erro", "mensagem": "Erro ao atualizar SharePoint"}), 400
        
        logger.info(f"Status atualizado para Concluído: {numero}")
        
        # 4. ENVIAR EMAIL DE PESQUISA EM BACKGROUND
        if email_solicitante:
            html_pesquisa = f"""
            <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                        .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ background: linear-gradient(135deg, #1a237e, #283593); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                        .content {{ padding: 20px; }}
                        .opcoes {{ margin: 20px 0; }}
                        .botao {{ display: inline-block; padding: 10px 20px; margin: 5px; border-radius: 5px; text-decoration: none; font-weight: bold; }}
                        .otimo {{ background: #4caf50; color: white; }}
                        .bom {{ background: #2196F3; color: white; }}
                        .ruim {{ background: #f44336; color: white; }}
                        .footer {{ background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #999; border-radius: 0 0 10px 10px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>#SuporteUNIFEB</h1>
                        </div>
                        
                        <div class="content">
                            <h2 style="color: #1a237e;">✅ Seu Chamado foi Concluído!</h2>
                            
                            <p>Olá,</p>
                            
                            <p>Seu chamado <strong>#{numero}</strong> foi resolvido com sucesso!</p>
                            
                            <p><strong>Como você avalia o atendimento?</strong></p>
                            
                            <div class="opcoes">
                                <a href="https://unifeb-backend.onrender.com/api/registrar-pesquisa?numero={numero}&avaliacao=otimo" class="botao otimo">⭐ Ótimo</a>
                                <a href="https://unifeb-backend.onrender.com/api/registrar-pesquisa?numero={numero}&avaliacao=bom" class="botao bom">👍 Bom</a>
                                <a href="https://unifeb-backend.onrender.com/api/registrar-pesquisa?numero={numero}&avaliacao=ruim" class="botao ruim">👎 Ruim</a>
                            </div>
                            
                            <p>Sua avaliação nos ajuda a melhorar! 😊</p>
                        </div>
                        
                        <div class="footer">
                            <p>Sistema #SuporteUNIFEB | Gerenciamento em Tempo Real</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Enviar em background
            thread = threading.Thread(
                target=lambda: enviar_email(email_solicitante, f"📊 Pesquisa de Satisfação - Chamado #{numero}", html_pesquisa),
                daemon=True
            )
            thread.start()
            logger.info(f"Thread iniciada para enviar pesquisa: {email_solicitante}")
        
        return jsonify({
            "status": "sucesso",
            "mensagem": "✅ Chamado concluído! Pesquisa enviada ao solicitante."
        }), 200
        
    except Exception as e:
        logger.error(f"Erro em concluir_chamado: {e}", exc_info=True)
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/registrar-pesquisa', methods=['GET'])
def registrar_pesquisa():
    """Registra avaliação da pesquisa"""
    try:
        numero = request.args.get('numero')
        avaliacao = request.args.get('avaliacao')
        
        logger.info(f"Pesquisa registrada - Chamado: {numero}, Avaliação: {avaliacao}")
        
        # TODO: Salvar avaliação no SharePoint
        
        html_obrigado = f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; text-align: center; padding: 40px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .icon {{ font-size: 60px; margin-bottom: 20px; }}
                    h1 {{ color: #1a237e; }}
                    p {{ color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">🙏</div>
                    <h1>Obrigado!</h1>
                    <p>Sua avaliação foi registrada e nos ajudará a melhorar nossos serviços.</p>
                </div>
            </body>
        </html>
        """
        
        return html_obrigado, 200, {'Content-Type': 'text/html; charset=utf-8'}
        
    except Exception as e:
        logger.error(f"Erro em registrar_pesquisa: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
