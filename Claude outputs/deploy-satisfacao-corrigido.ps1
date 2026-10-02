# 🎯 Script de Deploy FINAL - Dados Reais de Satisfação
# Execute este script NO PowerShell da sua máquina para fazer PUSH

Write-Host "🚀 DEPLOY FINAL - Satisfação com Dados REAIS" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Ir para a pasta do projeto
cd "C:\Users\carla.monteiro\Documents\Dashboard-UNIFEB-TV"

# Verificar se estamos no repositório correto
if (!(Test-Path ".git")) {
    Write-Host "❌ Erro: Não encontrei a pasta .git" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Pasta correta encontrada" -ForegroundColor Green
Write-Host ""

# Mostrar o que vai ser feito push
Write-Host "📊 Commits a fazer push:" -ForegroundColor Cyan
git log origin/main..HEAD --oneline
Write-Host ""

# Fazer push
Write-Host "🚀 Fazendo PUSH para GitHub..." -ForegroundColor Cyan
git push origin main

if ($?) {
    Write-Host "✅ PUSH realizado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 DEPLOY COMPLETO!" -ForegroundColor Green
    Write-Host ""
    Write-Host "⏱️  Render redeploy (~1-2 minutos para backend)" -ForegroundColor Cyan
    Write-Host "⏱️  Vercel redeploy (~10-20 segundos para frontend)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📊 Status final (últimos 3 commits):" -ForegroundColor Cyan
    git log --oneline -3
} else {
    Write-Host "❌ Erro no push" -ForegroundColor Red
    Write-Host "Verifique sua conexão com GitHub" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Script finalizado!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 O que muda depois do deploy:" -ForegroundColor Yellow
Write-Host "  ✨ Aba 'Satisfação' carrega dados REAIS do SharePoint" -ForegroundColor Green
Write-Host "  ✨ Sem necessidade de autenticação no backend" -ForegroundColor Green
Write-Host "  ✨ Dados mostram: ID | Solicitante | Avaliação | Comentário | Data" -ForegroundColor Green
