#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SERVIDOR PYTHON CUSTOMIZADO
Abre index.html por padrão (melhor que http.server)
"""

import os
import http.server
import socketserver

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Se acessar raiz, servir index.html
        if self.path == '/':
            self.path = '/index.html'
        
        # Servir o arquivo
        return super().do_GET()

# Mudar para a pasta certa
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Criar servidor
with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print("\n" + "="*60)
    print("🎯 SERVIDOR DASHBOARD UNIFEB")
    print("="*60)
    print(f"\n✅ Servidor rodando em: http://localhost:{PORT}")
    print(f"📺 Abra seu navegador: http://localhost:{PORT}")
    print(f"\n⚠️  Deixe este terminal aberto!")
    print("="*60 + "\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⏹️  Servidor parado")
        print("✅ Até logo!")
