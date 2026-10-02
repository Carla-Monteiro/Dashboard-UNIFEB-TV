#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar token de acesso do Microsoft Graph
Usa Device Code Flow - mais fácil que ter que instalar módulos Azure
"""

import requests
import time
import webbrowser
from urllib.parse import urljoin

# Cliente ID público do Microsoft Graph Explorer (funciona pra teste)
CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"

def gerar_token():
    """Gera token usando Device Code Flow"""

    print("\n" + "="*60)
    print("🔐 GERADOR DE TOKEN - Microsoft Graph")
    print("="*60 + "\n")

    # Step 1: Solicitar device code
    print("📋 Solicitando código de autorização...")

    device_code_response = requests.post(
        "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode",
        data={
            "client_id": CLIENT_ID,
            "scope": "https://graph.microsoft.com/.default offline_access"
        }
    )

    if device_code_response.status_code != 200:
        print("❌ Erro ao solicitar código")
        print(device_code_response.text)
        return None

    device_data = device_code_response.json()
    device_code = device_data.get("device_code")
    user_code = device_data.get("user_code")
    verification_uri = device_data.get("verification_uri")
    expires_in = device_data.get("expires_in", 900)
    interval = device_data.get("interval", 5)

    print(f"✅ Código gerado!\n")
    print("="*60)
    print("🔗 ABRA ESTE LINK NO NAVEGADOR:")
    print(f"   {verification_uri}\n")
    print("📝 DIGITE ESTE CÓDIGO:")
    print(f"   {user_code}")
    print("="*60)
    print()

    # Tentar abrir o navegador automaticamente
    try:
        webbrowser.open(verification_uri)
        print("✅ Navegador aberto automaticamente!")
    except:
        print("⚠️ Não conseguiu abrir o navegador automaticamente.")
        print("   Abra o link acima manualmente.")

    print("\n⏳ Aguardando confirmação (timeout em " + str(expires_in) + " segundos)...\n")

    # Step 2: Polling para obter token
    start_time = time.time()

    while time.time() - start_time < expires_in:
        try:
            token_response = requests.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "client_id": CLIENT_ID,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code
                },
                timeout=5
            )

            if token_response.status_code == 200:
                token_data = token_response.json()
                access_token = token_data.get("access_token")

                print("="*60)
                print("✅ TOKEN OBTIDO COM SUCESSO!")
                print("="*60)
                print()
                print("🔑 Seu token (copie todo ele):\n")
                print(access_token)
                print("\n" + "="*60)
                print()
                print("💡 Próximas instruções:")
                print("   1. Copie o token acima")
                print("   2. Execute: python corrigir_horarios_batch.py")
                print("   3. Cole o token quando pedir")
                print()

                return access_token

            elif token_response.status_code == 400:
                error_data = token_response.json()
                error = error_data.get("error")

                if error == "authorization_pending":
                    print("⏳ Ainda aguardando confirmação no navegador...")
                    time.sleep(interval)
                elif error == "expired_token":
                    print("❌ Código expirou! Tente novamente.")
                    return None
                else:
                    print(f"❌ Erro: {error}")
                    print(error_data.get("error_description"))
                    return None
            else:
                print(f"❌ Erro inesperado: {token_response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print("⏳ Ainda aguardando...")
            time.sleep(interval)
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None

    print("❌ Timeout! Código expirou.")
    return None

if __name__ == "__main__":
    token = gerar_token()

    if token:
        # Salvar em arquivo pra facilitar
        with open("token.txt", "w") as f:
            f.write(token)
        print("💾 Token salvo em 'token.txt'")
    else:
        print("❌ Falha ao gerar token")
