# 🔍 Verificar status do deploy

Write-Host "🔍 Verificando status do git..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

cd "C:\Users\carla.monteiro\Documents\Dashboard-UNIFEB-TV"

Write-Host "📊 Status do Git:" -ForegroundColor Cyan
git status
Write-Host ""

Write-Host "📝 Últimos 5 commits:" -ForegroundColor Cyan
git log --oneline -5
Write-Host ""

Write-Host "🌐 Commits remotos (últimos 5):" -ForegroundColor Cyan
git log origin/main --oneline -5
Write-Host ""

# Verificar se há commits locais não-pushados
Write-Host "⚠️  Commits não-pushados:" -ForegroundColor Yellow
$local_commits = git log origin/main..HEAD --oneline
if ($local_commits) {
    Write-Host $local_commits -ForegroundColor Yellow
} else {
    Write-Host "✅ Nenhum commit não-pushado. Tudo sincronizado!" -ForegroundColor Green
}

Write-Host ""
Write-Host "🚀 Aguarde ~2 minutos para o Render redeployar" -ForegroundColor Cyan
Write-Host "📱 Depois acesse: https://controle-chamados.vercel.app" -ForegroundColor Cyan
