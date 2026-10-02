# Script de Deploy Final - Dashboard UNIFEB
# Execute este script no PowerShell como administrador

Write-Host "🚀 DEPLOY FINAL - Dashboard UNIFEB" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Ir para a pasta do projeto
cd "C:\Users\carla.monteiro\Documents\Dashboard-UNIFEB-TV"

# Verificar se estamos no repositório correto
if (!(Test-Path ".git")) {
    Write-Host "❌ Erro: Não encontrei a pasta .git" -ForegroundColor Red
    Write-Host "Certifique-se de estar em: C:\Users\carla.monteiro\Documents\Dashboard-UNIFEB-TV" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Pasta correta encontrada" -ForegroundColor Green
Write-Host ""

# Copiar os arquivos atualizados
Write-Host "📋 Copiando arquivos atualizados..." -ForegroundColor Cyan

# Tentar copiar do diretório do usuário (se tiver os arquivos lá)
# Se não tiver, vai usar os que já existem

if (Test-Path "C:\Users\carla.monteiro\Downloads\dashboard-final-correto-v2.html") {
    Copy-Item "C:\Users\carla.monteiro\Downloads\dashboard-final-correto-v2.html" -Destination "index.html" -Force
    Write-Host "✅ Dashboard atualizado" -ForegroundColor Green
}

if (Test-Path "C:\Users\carla.monteiro\Downloads\form_handler.py") {
    Copy-Item "C:\Users\carla.monteiro\Downloads\form_handler.py" -Destination "form_handler.py" -Force
    Write-Host "✅ Backend atualizado" -ForegroundColor Green
}

Write-Host ""

# Verificar status
Write-Host "📊 Status do Git:" -ForegroundColor Cyan
git status

Write-Host ""
Write-Host "📝 Adicionando arquivos modificados..." -ForegroundColor Cyan
git add index.html form_handler.py

Write-Host ""
Write-Host "💾 Fazendo commit..." -ForegroundColor Cyan
git commit -m "feat: inteligência de categorização completa + API com origem e setor

- Backend retorna campos 'Origem' e 'SetordeAtendimento'
- Dashboard categoriza chamados com inteligência baseada em 3 critérios
- Chamados QR Code e Email categorizados corretamente
- Tabelas exibem categorias inteligentes (não 'Outra')

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01ModGiexBKwgZrU35U2snM8"

if ($?) {
    Write-Host "✅ Commit realizado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Erro no commit (pode ser que não haja mudanças)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Fazendo push para GitHub..." -ForegroundColor Cyan
git push origin main

if ($?) {
    Write-Host "✅ Push realizado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 DEPLOY CONCLUÍDO!" -ForegroundColor Green
    Write-Host ""
    Write-Host "⏱️  Vercel fará deploy em segundos" -ForegroundColor Cyan
    Write-Host "⏱️  Render fará redeploy em ~2 minutos" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📊 Status final:" -ForegroundColor Cyan
    git log --oneline -5
} else {
    Write-Host "❌ Erro no push" -ForegroundColor Red
    Write-Host "Verifique sua conexão com GitHub" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Script finalizado!" -ForegroundColor Green
