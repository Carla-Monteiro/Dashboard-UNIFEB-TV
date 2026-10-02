# 🎯 Deploy FINAL - Satisfação com Comentários REAIS do SharePoint
# Execute este script NO PowerShell da sua máquina para fazer PUSH

Write-Host "🚀 DEPLOY FINAL - Satisfação com Dados REAIS (incluindo Comentários)" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan
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

# Mostrar status
Write-Host "📊 Status do Git:" -ForegroundColor Cyan
git status
Write-Host ""

# Adicionar arquivos atualizados
Write-Host "📝 Adicionando form_handler.py (com comentário REAL)..." -ForegroundColor Cyan
git add form_handler.py

# Fazer commit
Write-Host "💾 Fazendo commit..." -ForegroundColor Cyan
git commit -m "feat: satisfação com comentários REAIS do SharePoint

- Backend retorna campo 'comentario' da lista PesquisasSatisfacao
- Frontend exibe comentários na tabela de satisfação
- Dados completos: ID | Avaliação | Comentário | Data | Solicitante

Mudanças:
- form_handler.py: /api/pesquisas agora retorna comentario real"

if ($?) {
    Write-Host "✅ Commit realizado!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Fazendo PUSH para GitHub..." -ForegroundColor Cyan
    git push origin main

    if ($?) {
        Write-Host "✅ PUSH realizado com sucesso!" -ForegroundColor Green
        Write-Host ""
        Write-Host "🎉 DEPLOY INICIADO!" -ForegroundColor Green
        Write-Host ""
        Write-Host "⏱️  Aguarde:" -ForegroundColor Yellow
        Write-Host "  - Render: ~1-2 minutos para backend redeployar" -ForegroundColor Cyan
        Write-Host "  - Vercel: ~10-20 segundos para frontend redeployar" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📊 Status (últimos commits):" -ForegroundColor Cyan
        git log --oneline -3
        Write-Host ""
        Write-Host "✨ Após o deploy, acesse https://controle-chamados.vercel.app" -ForegroundColor Green
        Write-Host "✨ Aba 'Satisfação' mostrará comentários REAIS!" -ForegroundColor Green
    } else {
        Write-Host "❌ Erro no PUSH" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  Erro no commit (talvez nenhuma mudança detectada)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Script finalizado!" -ForegroundColor Green
