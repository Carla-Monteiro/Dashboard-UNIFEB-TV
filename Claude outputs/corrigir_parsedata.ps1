# Script para corrigir parseData no index.html
# Execute este script na pasta do Dashboard

$caminhoArquivo = "C:\Users\carla.monteiro\Documents\Dashboard-UNIFEB-TV\index.html"

# Verificar se arquivo existe
if (-not (Test-Path $caminhoArquivo)) {
    Write-Host "❌ Arquivo não encontrado: $caminhoArquivo"
    exit
}

Write-Host "📝 Corrigindo parseData no arquivo..."

# Ler o arquivo
$conteudo = Get-Content $caminhoArquivo -Raw

# Substituir a função parseData
$parseDataAntiga = @"
const parseData = (dataStr) => {
                if (!dataStr) return new Date(0);
                try {
                    let d;
                    if (dataStr.includes('/')) {
                        const [dia, mes, ano] = dataStr.split('/');
                        if (dia && mes && ano) {
                            d = new Date(parseInt(ano), parseInt(mes) - 1, parseInt(dia));
                        }
                    }
                    if (!d || isNaN(d.getTime())) {
                        d = new Date(dataStr);
                    }
                    return isNaN(d.getTime()) ? new Date(0) : d;
                } catch (e) {
                    return new Date(0);
                }
            }
"@

$parseDataNova = @"
const parseData = (dataStr) => {
                if (!dataStr) return new Date(0);
                try {
                    let d;
                    if (dataStr.includes('/')) {
                        // Extrair apenas a parte da data (antes do espaço ou dois pontos)
                        const dataParte = dataStr.split(' ')[0]; // Pega "DD/MM/YYYY"
                        const [dia, mes, ano] = dataParte.split('/');
                        if (dia && mes && ano) {
                            // Extrair hora se houver
                            let horas = 0, minutos = 0;
                            if (dataStr.includes(':')) {
                                const horaParte = dataStr.split(' ')[1]; // Pega "HH:MM"
                                if (horaParte) {
                                    const [h, m] = horaParte.split(':');
                                    horas = parseInt(h) || 0;
                                    minutos = parseInt(m) || 0;
                                }
                            }
                            d = new Date(parseInt(ano), parseInt(mes) - 1, parseInt(dia), horas, minutos);
                        }
                    }
                    if (!d || isNaN(d.getTime())) {
                        d = new Date(dataStr);
                    }
                    return isNaN(d.getTime()) ? new Date(0) : d;
                } catch (e) {
                    return new Date(0);
                }
            }
"@

# Fazer a substituição
if ($conteudo.Contains($parseDataAntiga)) {
    $conteudo = $conteudo.Replace($parseDataAntiga, $parseDataNova)

    # Salvar o arquivo
    Set-Content -Path $caminhoArquivo -Value $conteudo -Encoding UTF8

    Write-Host "✅ parseData corrigida com sucesso!"
    Write-Host ""
    Write-Host "📋 Próximos passos:"
    Write-Host "1. git add index.html"
    Write-Host "2. git commit -m '🔧 Corrigir: parseData para extrair hora'"
    Write-Host "3. git push"
    Write-Host "4. Recarregue o dashboard (Ctrl+F5)"
} else {
    Write-Host "⚠️ Não consegui encontrar a função parseData para substituir"
    Write-Host "O arquivo pode já estar corrigido!"
}
