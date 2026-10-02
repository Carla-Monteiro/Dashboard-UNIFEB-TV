# 🎯 Script para instalar os arquivos atualizados e fazer commit

Write-Host "📋 Instalando arquivos atualizados..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$pasta = "C:\Users\carla.monteiro\Documents\Dashboard-UNIFEB-TV"

# Verificar se pasta existe
if (!(Test-Path $pasta)) {
    Write-Host "❌ Pasta não encontrada: $pasta" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Pasta encontrada: $pasta" -ForegroundColor Green
Write-Host ""

# Copiar arquivos
Write-Host "📦 Copiando arquivos..." -ForegroundColor Cyan

# Você precisa colocar os arquivos em um local temporário primeiro
# Por exemplo: Downloads

$downloads = "$env:USERPROFILE\Downloads"
$indexOrigem = "$downloads\index.html"
$formOrigem = "$downloads\form_handler.py"

if (!(Test-Path $indexOrigem)) {
    Write-Host "⚠️  Arquivo não encontrado: $indexOrigem" -ForegroundColor Yellow
    Write-Host "   Certifique-se de que os arquivos foram salvos em Downloads" -ForegroundColor Yellow
    Read-Host "Pressione ENTER para continuar"
}

if (Test-Path $indexOrigem) {
    Copy-Item $indexOrigem "$pasta\index.html" -Force
    Write-Host "✅ index.html copiado" -ForegroundColor Green
}

if (Test-Path $formOrigem) {
    Copy-Item $formOrigem "$pasta\form_handler.py" -Force
    Write-Host "✅ form_handler.py copiado" -ForegroundColor Green
}

Write-Host ""
Write-Host "🔄 Navegando para pasta..." -ForegroundColor Cyan
cd $pasta

Write-Host ""
Write-Host "📊 Status do Git:" -ForegroundColor Cyan
git status

Write-Host ""
Write-Host "📝 Adicionando arquivos..." -ForegroundColor Cyan
git add index.html form_handler.py

Write-Host ""
Write-Host "💾 Fazendo commit..." -ForegroundColor Cyan
git commit -m "fix: satisfação com dados REAIS do SharePoint

- Dashboard carrega dados reais via /api/pesquisas
- Backend permite acesso público ao endpoint
- Tabela exibe: ID | Solicitante | Avaliação | Comentário | Data
- Conversão automática de avaliação numérica (1-5) → Estrelas

Mudanças:
- index.html: nova função carregarPesquisas()
- form_handler.py: removido @requer_login do /api/pesquisas"

if ($?) {
    Write-Host "✅ Commit realizado!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Fazendo PUSH..." -ForegroundColor Cyan
    git push origin main

    if ($?) {
        Write-Host "✅ PUSH realizado com sucesso!" -ForegroundColor Green
        Write-Host ""
        Write-Host "🎉 DEPLOY INICIADO!" -ForegroundColor Green
        Write-Host ""
        Write-Host "⏱️  Aguarde:" -ForegroundColor Yellow
        Write-Host "  - Render: ~1-2 minutos para backend" -ForegroundColor Cyan
        Write-Host "  - Vercel: ~10-20 segundos para frontend" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📊 Status (últimos commits):" -ForegroundColor Cyan
        git log --oneline -3
    } else {
        Write-Host "❌ Erro no PUSH" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  Erro no commit" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Script finalizado!" -ForegroundColor Green
