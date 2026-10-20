#!/usr/bin/env python3
"""
Debug - Mostrar campos EXATOS do Microsoft Forms no SharePoint
Carla Monteiro - Dashboard UNIFEB TV
"""

import os
import sys
import json
from dotenv import load_dotenv
import requests

# Carregar .env
load_dotenv()

# Importar funções necessárias
sys.path.insert(0, os.path.dirname(__file__))

try:
    from form_handler import (
        get_access_token,
        obter_site_e_lista,
        GRAPH_API,
        LISTA_PESQUISAS
    )

    print("\n" + "="*70)
    print("🔍 DEBUG - CAMPOS EXATOS DO MICROSOFT FORMS (PESQUISAS)")
    print("="*70 + "\n")

    # Obter token
    token = get_access_token()
    if not token:
        print("❌ Erro: Não consegui obter token do Microsoft")
        sys.exit(1)

    print("✅ Token obtido\n")

    headers = {'Authorization': f'Bearer {token}'}

    # Obter site e lista
    site_id, list_id = obter_site_e_lista(headers, LISTA_PESQUISAS)
    if not site_id or not list_id:
        print("❌ Erro: Não consegui obter site_id ou list_id")
        sys.exit(1)

    print(f"✅ Site ID: {site_id}")
    print(f"✅ List ID: {list_id}\n")

    # Buscar items
    items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields"
    items_response = requests.get(items_url, headers=headers, timeout=10)

    if items_response.status_code != 200:
        print(f"❌ Erro ao buscar items: {items_response.status_code}")
        print(items_response.text)
        sys.exit(1)

    items = items_response.json().get('value', [])

    print(f"✅ {len(items)} respostas encontradas\n")

    if items:
        print("="*70)
        print("📋 PRIMEIRO ITEM - CAMPOS BRUTOS:")
        print("="*70)

        primeiro_item = items[0]
        fields = primeiro_item.get('fields', {})

        print("\n✨ TODOS OS CAMPOS DISPONÍVEIS:\n")

        for chave, valor in sorted(fields.items()):
            # Mostrar valor resumido
            valor_str = str(valor)
            if len(valor_str) > 80:
                valor_str = valor_str[:77] + "..."

            print(f"  '{chave}' = {valor_str}")

        print("\n" + "="*70)
        print("🎯 CAMPOS QUE PARECEM SER 'COMENTÁRIO':")
        print("="*70 + "\n")

        campos_comentario = {}
        for chave, valor in fields.items():
            if isinstance(valor, str) and valor.strip():  # Se tem valor de texto
                if any(palavra in chave.lower() for palavra in ['coment', 'comment', 'resposta', 'sugestão', 'observ']):
                    campos_comentario[chave] = valor
                    print(f"⭐ '{chave}'")
                    print(f"   Valor: {valor[:100]}\n")

        if not campos_comentario:
            print("⚠️ Nenhum campo óbvio de comentário encontrado")
            print("   Campos com TEXTO não vazio (possíveis comentários):")
            for chave, valor in fields.items():
                if isinstance(valor, str) and valor.strip() and len(valor) > 10:
                    print(f"   → '{chave}': {valor[:80]}...")

        print("\n" + "="*70)
        print("💡 SOLUÇÃO:")
        print("="*70)
        print("""
1. Procure acima pelo campo que contém o comentário real
2. Copie o nome EXATO (case-sensitive!)
3. Edite form_handler.py linha 723:

   Mude:
   'comentario': fields.get('Comentários', ''),

   Para (exemplo):
   'comentario': fields.get('NOME_REAL_AQUI', ''),

4. Salve e faça: git add . && git commit -m "Fix" && git push origin main
5. Deploy automático no Render
""")

except Exception as e:
    print(f"❌ Erro: {e}")
    print(f"Tipo: {type(e).__name__}")
    import traceback
    traceback.print_exc()