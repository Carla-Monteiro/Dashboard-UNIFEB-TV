#!/usr/bin/env python3
"""
Debug Simples - Listar campos do form_handler.py
"""

import re

# Ler o arquivo form_handler.py
with open('form_handler.py', 'r', encoding='utf-8') as f:
    conteudo = f.read()

print("\n" + "="*70)
print("🔍 ANALISANDO form_handler.py")
print("="*70 + "\n")

# Procurar por fields.get ou equivalente
linhas = conteudo.split('\n')

print("📋 CAMPOS MAPEADOS NO BACKEND:\n")

encontrado = False
for i, linha in enumerate(linhas, 1):
    if "fields.get" in linha or "'comentario'" in linha or "'avaliacao'" in linha or "'numeroChamado'" in linha:
        if "fields.get" in linha:
            encontrado = True
            print(f"  Linha {i}: {linha.strip()}")

if not encontrado:
    print("  ⚠️ Não encontrei 'fields.get'")
    print("\n  Procurando por outras referências:")

    for i, linha in enumerate(linhas, 1):
        if "'comentario'" in linha.lower() or "'comment'" in linha.lower():
            print(f"  Linha {i}: {linha.strip()}")

print("\n" + "="*70)
print("✏️ PRÓXIMO PASSO:")
print("="*70)
print("""
1. Abra form_handler.py no VS Code (ou editor)
2. Procure por: Ctrl+F → "comentario"
3. Veja qual é o nome real do campo (pode ser 'Comentários', 'Comment', etc)
4. Corrija para o nome correto

Ou me mostre a saída acima que ajudo a corrigir!
""")