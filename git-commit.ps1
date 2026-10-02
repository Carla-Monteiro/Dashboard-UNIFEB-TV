# Script para fazer commit e push do Dashboard para o GitHub
# Execute no PowerShell na pasta: C:\Users\carla.monteiro\Documents\Dashboard-UNIFEB-TV

cd C:\Users\carla.monteiro\Documents\Dashboard-UNIFEB-TV

Write-Host "📦 Adicionando arquivos ao Git..." -ForegroundColor Green
git add dashboard_chamados.html config.js dashboard.js README_DASHBOARD.md GUIA_INTEGRACAO.md form_handler.py

Write-Host "📝 Verificando status..." -ForegroundColor Yellow
git status

Write-Host "`n💬 Fazendo commit..." -ForegroundColor Green
git commit -m "Adicionar dashboard dinâmico com integração completa de API e SharePoint

- Interface moderna com tema escuro (sidebar, abas, modal)
- 3 novos endpoints: /api/chamados/ativos, /api/chamados/concluidos, /api/chamados/stats
- Integração com SharePoint via Microsoft Graph API
- Filtros funcionais (status, prioridade, busca)
- Auto-refresh a cada 30 segundos
- Dados em tempo real do banco SharePoint
- Suporte a login com token de autenticação
- Design responsivo (desktop, tablet, mobile)"

Write-Host "`n🚀 Fazendo push para GitHub..." -ForegroundColor Cyan
git push origin main

Write-Host "`n✅ PRONTO! Dashboard enviado para o GitHub!" -ForegroundColor Green
Write-Host "Acesse: https://github.com/Carla-Monteiro/Dashboard-UNIFEB-TV" -ForegroundColor Cyan
