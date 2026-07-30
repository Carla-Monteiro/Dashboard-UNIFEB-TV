import azure.functions as func
import requests
import json
import os

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function que recebe webhook do SharePoint
    e dispara GitHub Actions workflow
    """
    
    try:
        # Validar que é chamado POST
        if req.method != 'POST':
            return func.HttpResponse(
                "Apenas POST é aceito",
                status_code=400
            )
        
        # Variáveis de ambiente (configurar no Azure)
        GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
        GITHUB_REPO = "Carla-Monteiro/Dashboard-UNIFEB-TV"
        GITHUB_WORKFLOW = "sync-sharepoint.yml"
        
        if not GITHUB_TOKEN:
            return func.HttpResponse(
                "GITHUB_TOKEN não configurado",
                status_code=400
            )
        
        # Disparar workflow GitHub
        url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW}/dispatches"
        
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'ref': 'main'
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 204:
            return func.HttpResponse(
                json.dumps({
                    "status": "sucesso",
                    "mensagem": "Workflow GitHub disparado com sucesso"
                }),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({
                    "status": "erro",
                    "mensagem": f"Erro ao disparar workflow: {response.status_code}",
                    "detalhes": response.text
                }),
                status_code=response.status_code,
                mimetype="application/json"
            )
    
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "status": "erro",
                "mensagem": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
