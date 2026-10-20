# ============================================================
# executar_leitor.ps1
# Wrapper que roda o leitor.py e grava log com data/hora.
# Isso resolve o problema mais comum do Task Scheduler:
# quando o script falha silenciosamente, ninguém vê o motivo.
# Com esse log, dá pra abrir o arquivo e ver exatamente o que houve.
# ============================================================

# 1) AJUSTE ESTE CAMINHO se a pasta do projeto não for esta:
$Pasta = "C:\Users\carla.monteiro\Documents\AutomaçãoImpressoras"

$LogDir = Join-Path $Pasta "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$DataHoje = Get-Date -Format "yyyy-MM-dd"
$LogFile = Join-Path $LogDir "leitor_$DataHoje.log"

Set-Location $Pasta

"==================================================" | Out-File -Append -FilePath $LogFile
"Execucao iniciada em $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -Append -FilePath $LogFile
"==================================================" | Out-File -Append -FilePath $LogFile

# Roda o Python e joga TUDO (saida normal + erros) pro log
python leitor.py *>> $LogFile

"Execucao finalizada em $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -Append -FilePath $LogFile