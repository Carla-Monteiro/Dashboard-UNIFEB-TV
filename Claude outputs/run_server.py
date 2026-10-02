#!/usr/bin/env python3
"""
Servidor local para o Dashboard UNIFEB
Execute: python3 run_server.py
Depois abra: http://localhost:8000
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8000
DIRECTORY = str(Path(__file__).parent)

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Adicionar headers para evitar CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

if __name__ == '__main__':
    os.chdir(DIRECTORY)
    Handler = MyHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"✅ Servidor rodando em: http://localhost:{PORT}")
        print(f"📁 Diretório: {DIRECTORY}")
        print(f"📄 Arquivo: http://localhost:{PORT}/index.html")
        print(f"\n⏹️  Pressione CTRL+C para parar o servidor\n")
        httpd.serve_forever()
