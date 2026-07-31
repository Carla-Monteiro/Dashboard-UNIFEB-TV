#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚨 SISTEMA DE ALERTAS - SLA CRÍTICO
Monitora chamados com SLA < 1h e envia notificações
"""

import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configurações de email - OFFICE 365 / OUTLOOK CORPORATIVO
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
EMAIL_FROM = "suporte.dti@feb.br"  # ← Seu email corporativo
EMAIL_PASSWORD = "#SuporteNst2026"  # ← Sua senha do email corporativo (não precisa de "senha de app")

def calcular_tempo_restante(data_abertura_str, prioridade):
    """Calcular quanto tempo falta para vencer SLA"""
    try:
        data_abertura = datetime.fromisoformat(data_abertura_str.replace('Z', '+00:00'))
        agora = datetime.now(data_abertura.tzinfo) if data_abertura.tzinfo else datetime.now()
        
        SLA_HORAS = {'Alta': 2, 'Média': 8, 'Baixa': 24}
        sla_horas = SLA_HORAS.get(prioridade, 8)
        
        tempo_decorrido = (agora - data_abertura).total_seconds() / 3600
        tempo_restante = sla_horas - tempo_decorrido
        
        return tempo_restante, tempo_decorrido > sla_horas
    except:
        return 0, False

def verificar_alertas_criticos(chamados):
    """Verificar chamados com SLA crítico (< 1h)"""
    alertas = []
    
    for chamado in chamados:
        tempo_restante, vencido = calcular_tempo_restante(
            chamado.get('data', ''),
            chamado.get('prioridade', 'Média')
        )
        
        # Se vencido ou falta < 1h
        if vencido or (tempo_restante >= 0 and tempo_restante < 1):
            alertas.append({
                'id': chamado.get('id'),
                'titulo': chamado.get('titulo'),
                'prioridade': chamado.get('prioridade'),
                'setor': chamado.get('setorAtendimento'),
                'vencido': vencido,
                'tempo_restante_minutos': int(tempo_restante * 60) if tempo_restante > 0 else 0,
                'status': 'CRÍTICO' if tempo_restante < 0 else 'ATENÇÃO'
            })
    
    return alertas

def enviar_email_alerta(alertas, email_destino):
    """Enviar email com alertas de SLA crítico"""
    if not alertas:
        return True
    
    try:
        # Montar HTML do email
        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; }}
                    .header {{ background-color: #d32f2f; color: white; padding: 20px; text-align: center; }}
                    .alert {{ background-color: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 10px 0; }}
                    .critico {{ background-color: #ff5252; color: white; padding: 10px; border-radius: 5px; }}
                    .atencao {{ background-color: #ff9800; color: white; padding: 10px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚨 ALERTA DE SLA CRÍTICO</h1>
                        <p>Dashboard UNIFEB TV - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                    </div>
                    
                    <p>Você tem <strong>{len(alertas)} chamado(s) com SLA crítico</strong> que precisam de atenção imediata!</p>
        """
        
        for alerta in alertas:
            html += f"""
            <div class="alert">
                <div class="{alerta['status'].lower()}">
                    {alerta['status']} - Chamado #{alerta['id']}
                </div>
                <p><strong>Título:</strong> {alerta['titulo']}</p>
                <p><strong>Prioridade:</strong> {alerta['prioridade']}</p>
                <p><strong>Setor:</strong> {alerta['setor']}</p>
            """
            
            if alerta['vencido']:
                html += f"<p style='color: red;'><strong>⚠️ VENCIDO!</strong></p>"
            else:
                html += f"<p style='color: orange;'><strong>⏰ Faltam {alerta['tempo_restante_minutos']} minutos</strong></p>"
            
            html += "</div>"
        
        html += """
                    <p>Acesse o dashboard para mais detalhes: 
                    <a href="https://dashboard-unifeb-tv.vercel.app/index.html">Dashboard UNIFEB</a></p>
                </div>
            </body>
        </html>
        """
        
        # Enviar email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚨 ALERTA: {len(alertas)} Chamado(s) com SLA Crítico"
        msg['From'] = EMAIL_FROM
        msg['To'] = email_destino
        
        parte_html = MIMEText(html, 'html')
        msg.attach(parte_html)
        
        # Conectar e enviar
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email enviado para {email_destino}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        return False

def salvar_historico_alertas(alertas):
    """Salvar histórico de alertas em JSON"""
    try:
        historico = {
            'data': datetime.now().isoformat(),
            'total_alertas': len(alertas),
            'alertas': alertas
        }
        
        with open('historico_alertas.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(historico, ensure_ascii=False) + '\n')
        
        return True
    except:
        return False

if __name__ == "__main__":
    # Teste
    with open('chamados_sync.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    alertas = verificar_alertas_criticos(dados.get('chamados', []))
    
    if alertas:
        print(f"🚨 {len(alertas)} alerta(s) crítico(s) encontrado(s)!")
        for alerta in alertas:
            print(f"  - #{alerta['id']}: {alerta['titulo']}")
