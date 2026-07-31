#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API Backend para Gerenciar Chamados - Render Ready"""

import os
import json
import sys
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import sys
sys.path.insert(0, '/home/claude')
try:
    from alertas import verificar_alertas_criticos
    from relatorios import calcular_metricas, gerar_relatorio_excel
except:
    pass

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')

# ========== MAPEAMENTO COMPLETO DE DEPARTAMENTOS POR EMAIL ==========
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

SHAREPOINT_DOMAIN = "unifeb.sharepoint.com"
SITE_PATH = "/sites/SuporteDTI"
LIST_NAME = "Chamados"
GRAPH_API = "https://graph.microsoft.com/v1.0"

def extrair_setor_do_email(email):
    """Extrai o setor baseado no padrão do email (nome.setor@feb.br)"""
    print(f"\n🔍 [DEBUG] Extraindo setor do email: '{email}'")
    
    try:
        if not email:
            print("❌ Email vazio")
            return 'Geral'
            
        email_lower = email.lower().strip()
        print(f"📧 Email normalizado: '{email_lower}'")
        
        if '@' not in email_lower:
            print("❌ Email sem @")
            return 'Geral'
        
        # Extrair parte antes do @
        parte_email = email_lower.split('@')[0]
        print(f"📝 Parte do email: '{parte_email}'")
        
        if '.' not in parte_email:
            print("❌ Sem ponto no email")
            return 'Geral'
        
        # Extrair última parte após ponto
        departamento_sigla = parte_email.split('.')[-1]
        print(f"🏢 Departamento extraído: '{departamento_sigla}'")
        print(f"🗺️  Mapeamento disponível: {list(EMAIL_SETOR_MAPPING.keys())}")
        
        setor = EMAIL_SETOR_MAPPING.get(departamento_sigla, 'Geral')
        print(f"✅ Setor final: '{setor}'")
        return setor
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 'Geral'

app = Flask(__name__)
CORS(app)

def get_access_token():
    """Obter token de acesso do Azure AD"""
    try:
        auth_url = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token'
        auth_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        response = requests.post(auth_url, data=auth_data, timeout=10)
        if response.status_code != 200:
            print(f"Auth error: {response.status_code}")
            return None
        return response.json().get('access_token')
    except Exception as e:
        print(f"Auth exception: {e}")
        return None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

# ========== ENDPOINT NOVO: Retornar Chamados Sincronizados ==========
@app.route('/api/chamados', methods=['GET'])
def get_chamados():
    """Retorna os chamados sincronizados do arquivo JSON"""
    try:
        with open('chamados_sync.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
            return jsonify(dados), 200
    except FileNotFoundError:
        return jsonify({"chamados": [], "total_chamados": 0}), 200
    except Exception as e:
        print(f"Erro ao ler chamados_sync.json: {e}")
        return jsonify({"chamados": [], "total_chamados": 0}), 200

@app.route('/api/criar-chamado', methods=['POST'])
def criar_chamado():
    try:
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Autenticação falhou"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        
        if site_response.status_code != 200:
            return jsonify({"status": "erro", "mensagem": "SharePoint error"}), 400
        
        site_id = site_response.json().get('id')
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        
        if list_response.status_code != 200:
            return jsonify({"status": "erro", "mensagem": "List error"}), 400
        
        list_id = list_response.json().get('id')
        data = request.json
        create_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items"
        
        payload = {
            "fields": {
                "Title": data.get('titulo'),
                "Descricao": data.get('descricao'),
                "Solicitante": data.get('solicitante'),
                "Email": data.get('email'),
                "SetordeAtendimento": extrair_setor_do_email(data.get('email', '')),
                "Prioridade": data.get('prioridade'),
                "Status": "Aberto"
            }
        }
        
        response = requests.post(create_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code in [200, 201]:
            return jsonify({"status": "sucesso", "mensagem": "Chamado criado!"}), 201
        else:
            return jsonify({"status": "erro", "mensagem": "Criar falhou"}), response.status_code
    
    except Exception as e:
        print(f"Create error: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/editar-chamado/<item_id>', methods=['PATCH'])
def editar_chamado(item_id):
    try:
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Autenticação falhou"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        site_id = site_response.json().get('id')
        
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        list_id = list_response.json().get('id')
        
        data = request.json
        update_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
        
        payload = {
            "fields": {
                "Title": data.get('titulo'),
                "Descricao": data.get('descricao'),
                "SetordeAtendimento": data.get('setor'),
                "Prioridade": data.get('prioridade'),
                "Status": data.get('status')
            }
        }
        
        response = requests.patch(update_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            # ✅ NOVO: Retornar os dados atualizados para o frontend atualizar IMEDIATAMENTE
            chamado_atualizado = {
                "id": item_id,
                "titulo": data.get('titulo'),
                "solicitante": data.get('solicitante', ''),
                "status": data.get('status'),
                "prioridade": data.get('prioridade'),
                "setorAtendimento": data.get('setor'),
                "descricao": data.get('descricao'),
                "data": data.get('data', '')
            }
            return jsonify({
                "status": "sucesso", 
                "mensagem": "✅ Atualizado com sucesso!",
                "chamado": chamado_atualizado
            }), 200
        else:
            return jsonify({"status": "erro", "mensagem": "Update falhou"}), response.status_code
    
    except Exception as e:
        print(f"Update error: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/deletar-chamado/<item_id>', methods=['DELETE'])
def deletar_chamado(item_id):
    try:
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Autenticação falhou"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        site_id = site_response.json().get('id')
        
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        list_id = list_response.json().get('id')
        
        delete_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items/{item_id}"
        response = requests.delete(delete_url, headers=headers, timeout=10)
        
        if response.status_code == 204:
            return jsonify({"status": "sucesso", "mensagem": "Deletado!"}), 200
        else:
            return jsonify({"status": "erro", "mensagem": "Delete falhou"}), response.status_code
    
    except Exception as e:
        print(f"Delete error: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

# ========== NOVOS ENDPOINTS: ALERTAS, MÉTRICAS E RELATÓRIOS ==========

@app.route('/api/alertas', methods=['GET'])
def get_alertas():
    """Retorna chamados com SLA crítico (< 1h)"""
    try:
        with open('chamados_sync.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        chamados = dados.get('chamados', [])
        alertas = verificar_alertas_criticos(chamados)
        
        return jsonify({
            "alertas": alertas,
            "total_alertas": len(alertas),
            "data": datetime.now().isoformat()
        }), 200
    except Exception as e:
        print(f"Alertas error: {e}")
        return jsonify({"alertas": []}), 200

@app.route('/api/metricas', methods=['GET'])
def get_metricas():
    """Retorna KPIs para dashboard executivo"""
    try:
        with open('chamados_sync.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        chamados = dados.get('chamados', [])
        metricas = calcular_metricas(chamados)
        
        return jsonify(metricas), 200
    except Exception as e:
        print(f"Metricas error: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/api/export-excel', methods=['GET'])
def export_excel():
    """Exportar relatório em Excel"""
    try:
        with open('chamados_sync.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        chamados = dados.get('chamados', [])
        excel_file = gerar_relatorio_excel(chamados)
        
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
        print(f"Export error: {e}")
        return jsonify({"erro": str(e)}), 500


# ========== SISTEMA QR CODE #SuporteUNIFEB - MANUTENÇÃO ==========

# MAPEAMENTO DE CATEGORIAS E EMAILS
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

def gerar_numero_chamado():
    """Gera número único do chamado"""
    return datetime.now().strftime('%Y%m%d%H%M%S')

def obter_roteamento(categoria):
    """Obtém emails de destino"""
    if categoria in CATEGORIAS_ROTEAMENTO:
        return CATEGORIAS_ROTEAMENTO[categoria]
    return {'tipo': 'ti', 'emails': ['suporte.dti@feb.br']}

def gerar_html_email(numero, bloco, sala, solicitante, email_solicitante, categoria, descricao, tipo):
    """Gera HTML do email"""
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
                .badge {{ display: inline-block; padding: 5px 15px; background: #ffa500; color: white; border-radius: 20px; font-weight: bold; }}
                .descricao-box {{ background: #f5f5f5; padding: 15px; border-left: 4px solid #ffa500; margin-top: 20px; border-radius: 5px; }}
                .numero {{ font-size: 24px; color: #ffa500; font-weight: bold; margin: 10px 0; }}
                .footer {{ background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #999; border-radius: 0 0 10px 10px; }}
                .instrucoes {{ background: #e8f5e9; padding: 15px; border-radius: 5px; margin-top: 15px; color: #2e7d32; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="icon">{icons[tipo]}</div>
                    <h1>Novo Aviso de {nome_setor}</h1>
                </div>
                
                <div class="content">
                    <div class="numero">Chamado #: {numero}</div>
                    
                    <h2 style="color: #1a237e; margin-bottom: 20px;">Detalhes do Aviso</h2>
                    
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
                    
                    <div class="info-row">
                        <span class="label">⚙️ Tipo:</span>
                        <span class="value"><span class="badge">{categoria}</span></span>
                    </div>
                    
                    <div class="descricao-box">
                        <strong>📝 Descrição Detalhada:</strong><br><br>
                        {descricao.replace(chr(10), '<br>')}
                    </div>
                    
                    <div class="instrucoes">
                        <strong>ℹ️ Próximos Passos:</strong><br>
                        1. Verifique o problema<br>
                        2. Resolva quando possível<br>
                        3. Marque como "Concluído" no Dashboard/SharePoint<br>
                        4. Sistema enviará pesquisa de satisfação automaticamente<br><br>
                        <strong>⏰ Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                    </div>
                </div>
                
                <div class="footer">
                    <p>Sistema #SuporteUNIFEB | Gerenciamento em Tempo Real</p>
                    <p>Não é necessário responder este e-mail. Use o Dashboard para gerenciar o chamado.</p>
                </div>
            </div>
        </body>
    </html>
    """
    return html

def enviar_emails_suporte(numero, bloco, sala, solicitante, email_solicitante, categoria, descricao, tipo, emails_destino):
    """Envia emails para os responsáveis"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        html = gerar_html_email(numero, bloco, sala, solicitante, email_solicitante, categoria, descricao, tipo)
        
        for email_destino in emails_destino:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = f"[AVISO #{numero}] {categoria} - {bloco}/{sala}"
                msg['From'] = "suporte.dti@feb.br"
                msg['To'] = email_destino
                
                msg.attach(MIMEText(html, 'html'))
                
                server = smtplib.SMTP("smtp.office365.com", 587)
                server.starttls()
                server.login("suporte.dti@feb.br", os.getenv('EMAIL_PASSWORD'))
                server.send_message(msg)
                server.quit()
                
                print(f"✅ Email enviado para {email_destino}")
            except Exception as e:
                print(f"❌ Erro ao enviar para {email_destino}: {e}")
    except Exception as e:
        print(f"❌ Erro em enviar_emails_suporte: {e}")

@app.route('/api/criar-manutencao', methods=['POST'])
def criar_manutencao():
    """Endpoint para criar aviso via QR Code"""
    try:
        data = request.json
        email = data.get('email')
        bloco = data.get('bloco')
        sala = data.get('sala')
        tipo = data.get('tipo')
        categoria = data.get('categoria')
        descricao = data.get('descricao')
        
        # Validar campos
        if not all([email, bloco, sala, tipo, categoria, descricao]):
            return jsonify({"status": "erro", "mensagem": "Campos obrigatórios faltando"}), 400
        
        # Gerar número único
        numero = gerar_numero_chamado()
        
        # Obter roteamento
        roteamento = obter_roteamento(categoria)
        emails_destino = roteamento['emails']
        tipo_problema = roteamento['tipo']
        
        # Extrair nome do email
        solicitante = email.split('@')[0].replace('.', ' ').title()
        
        # 1. SALVAR NO SHAREPOINT
        token = get_access_token()
        if not token:
            return jsonify({"status": "erro", "mensagem": "Falha ao conectar"}), 401
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # URLs do SharePoint
        site_url = f"{GRAPH_API}/sites/{SHAREPOINT_DOMAIN}:{SITE_PATH}"
        site_response = requests.get(site_url, headers=headers, timeout=10)
        site_id = site_response.json().get('id')
        
        list_url = f"{GRAPH_API}/sites/{site_id}/lists/{LIST_NAME}"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        list_id = list_response.json().get('id')
        
        create_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items"
        
        # Payload
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
        
        response = requests.post(create_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code not in [200, 201]:
            return jsonify({"status": "erro", "mensagem": "Erro ao salvar no SharePoint"}), 400
        
        # 2. ENVIAR EMAILS
        enviar_emails_suporte(numero, bloco, sala, solicitante, email, categoria, descricao, tipo_problema, emails_destino)
        
        return jsonify({
            "status": "sucesso",
            "mensagem": "Aviso enviado com sucesso!",
            "numero": numero
        }), 201
        
    except Exception as e:
        print(f"Erro em criar_manutencao: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
