# Script de Deploy - Integração de Satisfação com Dados Reais
# Execute este script no PowerShell como administrador

Write-Host "🚀 DEPLOY - Integração de Satisfação com Dados Reais" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
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

# Verificar status
Write-Host "📊 Status do Git:" -ForegroundColor Cyan
git status
Write-Host ""

# Adicionar arquivo modificado
Write-Host "📝 Adicionando arquivo modificado..." -ForegroundColor Cyan
git add index.html
Write-Host ""

# Fazer commit
Write-Host "💾 Fazendo commit..." -ForegroundColor Cyan
git commit -m "feat: integrar dados reais de satisfação do SharePoint

- Aba Satisfação agora carrega pesquisas reais da lista PesquisasSatisfacao
- Função carregarPesquisas() chama endpoint /api/pesquisas
- Tabela exibe: ID Chamado, Solicitante, Avaliação (⭐), Comentário, Data
- Conversão de avaliação numérica para estrelas (1-5)
- Fallback com mensagem quando não há pesquisas

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
    Write-Host ""
    Write-Host "📊 Status final:" -ForegroundColor Cyan
    git log --oneline -3
} else {
    Write-Host "❌ Erro no push" -ForegroundColor Red
    Write-Host "Verifique sua conexão com GitHub" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Script finalizado!" -ForegroundColor Green
