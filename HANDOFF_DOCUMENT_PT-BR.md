╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║         📋 HANDOFF DOCUMENT - DASHBOARD UNIFEB TV                   ║
║                                                                      ║
║    Guia Completo para Novo Administrador do Sistema                 ║
║                                                                      ║
║    Versão 1.0 - 31/07/2026                                          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 ÍNDICE

1. VISÃO GERAL DO SISTEMA
2. ACESSOS E CREDENCIAIS
3. COMO O SISTEMA FUNCIONA
4. OPERAÇÕES DIÁRIAS
5. COMO FAZER DEPLOY
6. TROUBLESHOOTING
7. CONTATOS IMPORTANTES
8. MODIFICAÇÕES COMUNS
9. SEGURANÇA E BACKUPS
10. ROTEIROS PASSO A PASSO

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ VISÃO GERAL DO SISTEMA

O Dashboard UNIFEB TV é um sistema de gerenciamento de chamados em tempo 
real que sincroniza com SharePoint da UNIFEB.

COMPONENTES:
├─ Frontend (Vercel) - Interface web
├─ Backend (Render) - API e sincronização
├─ SharePoint - Base de dados
└─ GitHub - Versionamento de código

FUNCIONAMENTO BÁSICO:
1. Chamados são criados via email (suporte.dti@feb.br)
2. SharePoint armazena os dados
3. sync_loop.py sincroniza a cada 10 segundos
4. Dashboard mostra em tempo real
5. Usuários acompanham e gerenciam chamados

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2️⃣ ACESSOS E CREDENCIAIS

⚠️ IMPORTANTE: Guardar em local seguro (LastPass, KeePass, ou similar)

───────────────────────────────────────────────────────────────────────
A. ACESSOS PÚBLICOS (Não precisam senha)
───────────────────────────────────────────────────────────────────────

Dashboard (Público):
  URL: https://dashboard-unifeb-tv.vercel.app/index.html
  Acesso: Qualquer pessoa pode acessar e ver os chamados

GitHub (Repositório):
  URL: https://github.com/Carla-Monteiro/Dashboard-UNIFEB-TV
  Acesso: Público (ler código)

───────────────────────────────────────────────────────────────────────
B. ACESSOS ADMINISTRATIVOS
───────────────────────────────────────────────────────────────────────

🔑 GitHub (Modificar código)
  URL: https://github.com/Carla-Monteiro/Dashboard-UNIFEB-TV
  Conta: [INSERIR EMAIL DO NOVO ADMIN]
  Acesso: Precisa ser adicionado como colaborador
  Como adicionar: Settings → Collaborators → Add people

🔑 Vercel (Deploy Frontend)
  URL: https://vercel.com
  Conta: carla.monteiro@unifeb.br (ou [NOVA CONTA])
  Projeto: dashboard-unifeb-tv
  Token: [PEDIR PARA CARLA OU GERAR NOVO]
  Como acessar: Vercel → Settings → Tokens

🔑 Render (Deploy Backend)
  URL: https://render.com
  Conta: carla.monteiro@unifeb.br (ou [NOVA CONTA])
  Serviço: unifeb-backend
  Variáveis de ambiente: Ver seção C abaixo

───────────────────────────────────────────────────────────────────────
C. CREDENCIAIS SHAREPOINT (.env)
───────────────────────────────────────────────────────────────────────

⚠️ NUNCA compartilhar por email ou chat não seguro!

Arquivo: .env (na raiz do projeto)
Local: C:\Users\[SEU_USER]\Dashboard-UNIFEB-TV\.env

Conteúdo:
───────────────────────────────────────────────────────────────────────
CLIENT_ID=100ba4af-831a-4d3c-8e96-60e683f0152a
CLIENT_SECRET=P338Q~zC04Td8P1rk_srVCl-pS2wlzWzSGl9da3T
TENANT_ID=62a0e447-20c2-41be-8e60-893b78364660
SHAREPOINT_DOMAIN=unifeb.sharepoint.com
SITE_PATH=/sites/SuporteDTI
LIST_NAME=Chamados
───────────────────────────────────────────────────────────────────────

⚠️ IMPORTANTE:
- Essas credenciais permitem ACESSAR E MODIFICAR dados do SharePoint
- Nunca fazer commit do .env no GitHub
- O .gitignore já protege, mas verifique sempre
- Se vazar, solicitar novo CLIENT_SECRET no Azure

Como acessar o Azure para gerar novo SECRET:
1. Acesse: https://portal.azure.com
2. Vá em: Azure Active Directory
3. Clique em: App registrations
4. Procure por: Dashboard UNIFEB TV (ou similar)
5. Clique em: Certificates & secrets
6. Gere um novo CLIENT_SECRET
7. COPIE IMEDIATAMENTE (não consegue ver novamente!)
8. Atualize no .env e faça deploy

───────────────────────────────────────────────────────────────────────
D. EMAIL CORPORATIVO
───────────────────────────────────────────────────────────────────────

Email de alertas: suporte.dti@feb.br
Senha: [SOLICITAR PARA RH OU TI]

Este email recebe:
- Alertas de SLA crítico
- Notificações de chamados vencidos
- Logs do sistema

Arquivo de configuração: alertas.py (linhas 15-16)
Para modificar, editar e fazer deploy novamente

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3️⃣ COMO O SISTEMA FUNCIONA

FLUXO DE DADOS:

┌─────────────────────────────────────────────────────────────────┐
│ 1. EMAIL RECEBIDO (suporte.dti@feb.br)                          │
│    └─ Exemplo: carla.dti@feb.br envia chamado                   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. SHAREPOINT CRIA CHAMADO                                      │
│    └─ ID, Título, Descrição, Email, Status                     │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. SYNC_LOOP.PY SINCRONIZA (A CADA 10 SEGUNDOS)                 │
│    ├─ Conecta ao SharePoint via API                            │
│    ├─ Busca todos os chamados                                  │
│    ├─ Detecta chamados SEM SETOR                               │
│    ├─ EXTRAI SETOR DO EMAIL                                   │
│    │  (carla.dti@feb.br → Departamento de Tecnologia)          │
│    ├─ ATUALIZA SETOR NO SHAREPOINT                             │
│    ├─ Verifica SLA (Alta=2h, Média=8h, Baixa=24h)              │
│    └─ Salva em chamados_sync.json                              │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. BACKEND FLASK SERVE OS DADOS                                 │
│    ├─ GET /api/chamados ← Dashboard busca                      │
│    ├─ GET /api/alertas ← Alertas de SLA                        │
│    ├─ GET /api/metricas ← KPIs                                 │
│    └─ GET /api/export-excel ← Relatório                        │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. DASHBOARD VERCEL RENDERIZA                                   │
│    ├─ Tabela de chamados atualizada                            │
│    ├─ Gráficos em tempo real                                   │
│    ├─ Dashboard Executivo com KPIs                             │
│    └─ Alertas visuais para SLA crítico                         │
└─────────────────────────────────────────────────────────────────┘

SINCRONIZAÇÃO SLA:

Alta:   2 horas  (🔴 vermelho se vencido)
Média:  8 horas  (🟡 amarelo se vencido)
Baixa:  24 horas (🟢 verde se vencido)

PREENCHIMENTO AUTOMÁTICO DE SETOR:

Email:                  → Setor no Dashboard:
carla.dti@feb.br       → Departamento de Tecnologia
joao.rh@feb.br         → RH
maria.financeiro@feb.br → Atendimento Financeiro
[etc - ver lista completa em form_handler.py]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4️⃣ OPERAÇÕES DIÁRIAS

MONITORAR O SISTEMA:

Diariamente:
✅ Acessar https://dashboard-unifeb-tv.vercel.app/index.html
✅ Verificar se status é "🟢 Sincronizado" (topo direito)
✅ Clicar em aba "🎯 Executivo" para ver KPIs
✅ Verificar se há chamados com "SLA VENCIDO"
✅ Se houver, entrar em contato com setor responsável

Semanalmente:
✅ Gerar relatório em Excel: botão "📥 Exportar Excel"
✅ Verificar logs do Render para erros
✅ Confirmar que sync_loop.py está rodando

Mensalmente:
✅ Fazer backup do SharePoint
✅ Revisar setores e adicionar novos se necessário
✅ Verificar credenciais (CLIENT_SECRET não expira?)

ALERTAS AUTOMÁTICOS:

Se receber email em suporte.dti@feb.br com assunto "🚨 ALERTA: X Chamado(s) com SLA Crítico":
1. Abrir dashboard
2. Ir para aba "🎯 Executivo"
3. Ver seção "⚠️ Chamados Críticos (< 1h)"
4. Tomar ação conforme necessário

QUANDO ALGO NÃO SINCRONIZA:

Se vir "🔴 Erro" em vez de "🟢 Sincronizado":
1. Aguardar 30 segundos
2. Apertar F5 (recarregar)
3. Se persistir, ver seção "TROUBLESHOOTING"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5️⃣ COMO FAZER DEPLOY

DEPLOY AUTOMÁTICO (RECOMENDADO):

1. Modificar código localmente
2. Fazer git commit e git push
3. Vercel/Render fazem deploy automaticamente (~2 min)
4. Sistema atualiza online

PASSO A PASSO:

```bash
# 1. Entrar na pasta
cd C:\Users\[SEU_USER]\Dashboard-UNIFEB-TV

# 2. Ver o que mudou
git status

# 3. Adicionar mudanças
git add .

# 4. Commit com mensagem clara
git commit -m "Fix: Descrição do que foi mudado"

# 5. Push para GitHub
git push

# 6. Aguardar 2-3 minutos
# Render e Vercel farão deploy automaticamente
# Você receberá email de confirmação
```

DEPLOY MANUAL (SE AUTOMÁTICO FALHAR):

Vercel (Frontend):
1. Acesse: https://vercel.com
2. Clique em: dashboard-unifeb-tv
3. Clique em: Deployments
4. Clique em: Redeploy (botão)
5. Selecione: Production
6. Aguarde 1-2 minutos

Render (Backend):
1. Acesse: https://render.com
2. Clique em: unifeb-backend
3. Clique em: Manual Deploy (botão azul)
4. Clique em: Deploy latest commit
5. Aguarde 2-3 minutos
6. Verifique logs

TESTE APÓS DEPLOY:

1. Abrir dashboard em nova aba (Ctrl+Shift+N)
2. Ver se mudanças foram aplicadas
3. Verificar console (F12) para erros
4. Se houver erro, ver logs do Render

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6️⃣ TROUBLESHOOTING

PROBLEMA: Dashboard não carrega

Solução:
1. Limpar cache (Ctrl+Shift+Del)
2. Apertar F5 (recarregar)
3. Tentar em navegador privado
4. Se persistir, verificar console (F12) para mensagens de erro

────────────────────────────────────────────────────────────────────

PROBLEMA: Status mostra "🔴 Erro" em vez de "🟢 Sincronizado"

Solução:
1. Aguardar 30 segundos
2. Apertar F5
3. Verificar se Render está online (https://render.com)
4. Se backend está em "red" ou "suspended", fazer redeploy manual
5. Verificar .env - credenciais podem estar expiradas

────────────────────────────────────────────────────────────────────

PROBLEMA: Chamados não aparecem na tabela

Solução:
1. Abrir console (F12)
2. Ver se tem erro de CORS (Cross-Origin)
3. Se tiver, verificar form_handler.py linha com CORS
4. Verificar se backend está respondendo: 
   https://unifeb-backend.onrender.com/api/chamados
5. Se retornar JSON, problema está no frontend
6. Se retornar erro, problema está no backend

────────────────────────────────────────────────────────────────────

PROBLEMA: Setor não preenche automaticamente

Solução:
1. Verificar email do chamado
2. Confirmar que email segue formato: nome.departamento@feb.br
3. Verificar se departamento está no mapeamento (form_handler.py)
4. Se não estiver, adicionar novo (ver seção "Adicionar novo departamento")
5. Fazer deploy
6. Aguardar próxima sincronização (10 segundos)

────────────────────────────────────────────────────────────────────

PROBLEMA: SLA não está calculando corretamente

Solução:
1. Verificar formato da data no SharePoint (deve ser ISO 8601)
2. Verificar timezone (usar UTC)
3. Verificar sync_loop.py função calcular_sla
4. Se for problema de hora, ver seção "Corrigir hora"

────────────────────────────────────────────────────────────────────

PROBLEMA: Excel não gera ou está vazio

Solução:
1. Verificar se openpyxl está instalado (requirements.txt)
2. Fazer deploy: git add . → git commit → git push
3. Verificar se há chamados no dashboard (Excel só funciona com dados)
4. Se erro 500, verificar logs do Render (F12)

────────────────────────────────────────────────────────────────────

PROBLEMA: Emails de alerta não chegam

Solução:
1. Verificar email corporativo suporte.dti@feb.br
2. Verificar pasta de Spam/Lixo
3. Verificar senha do email em alertas.py
4. Se password_error, gerar novo app password:
   https://account.microsoft.com/security/app-passwords
5. Atualizar em alertas.py
6. Fazer deploy

────────────────────────────────────────────────────────────────────

PROBLEMA: Render diz "Port binding failed"

Solução:
1. Ir para Render → unifeb-backend → Settings
2. Verificar "Start Command": deve ser "bash start.sh"
3. Se diferente, corrigir
4. Clicar em "Redeploy"

────────────────────────────────────────────────────────────────────

PROBLEMA: GitHub diz "Merge conflict"

Solução:
1. Não fazer push sem fazer git pull primeiro
2. Se tiver conflito:
   git pull
   (resolver conflitos nos arquivos)
   git add .
   git commit -m "Merge: Resolver conflitos"
   git push

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7️⃣ CONTATOS IMPORTANTES

PESSOAS:

Carla Monteiro (Criadora do sistema)
  Email: carla.monteiro@unifeb.br
  WhatsApp: [INSERIR]
  Disponível para: Dúvidas técnicas

RH (Questões de acesso)
  Email: rh@unifeb.br
  Para: Resetar senha email corporativo

TI SharePoint (Problemas com SharePoint)
  Email: ti@unifeb.br
  Para: Credenciais expiradas, erros de permissão

SERVIÇOS ONLINE:

GitHub
  https://github.com
  Status: https://www.githubstatus.com

Vercel
  https://vercel.com
  Status: https://www.vercel-status.com

Render
  https://render.com
  Status: https://render.statuspage.io

Microsoft Azure
  https://portal.azure.com
  Para: Renovar CLIENT_SECRET do SharePoint

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

8️⃣ MODIFICAÇÕES COMUNS

ADICIONAR NOVO DEPARTAMENTO:

Exemplo: Adicionar "Marketing" com email "marketing"

Passo 1: Abrir form_handler.py
Passo 2: Procurar por "EMAIL_SETOR_MAPPING" (linha ~45)
Passo 3: Adicionar nova linha:
  'marketing': 'Marketing',

Passo 4: Abrir sync_loop.py
Passo 5: Procurar por "EMAIL_SETOR_MAPPING" (linha ~30)
Passo 6: Adicionar mesma linha:
  'marketing': 'Marketing',

Passo 7: Salvar ambos arquivos
Passo 8: Terminal:
  git add form_handler.py sync_loop.py
  git commit -m "Feature: Adicionar departamento Marketing"
  git push

Passo 9: Aguardar 2-3 minutos para deploy
Passo 10: Testar com email marketing.xxx@feb.br

────────────────────────────────────────────────────────────────────

MODIFICAR PRAZO SLA:

Exemplo: Mudar Alta de 2 horas para 3 horas

Passo 1: Abrir sync_loop.py
Passo 2: Procurar por "SLA_HORAS = {'Alta': 2" (linha ~27)
Passo 3: Mudar para "SLA_HORAS = {'Alta': 3"
Passo 4: Salvar
Passo 5: Terminal:
  git add sync_loop.py
  git commit -m "Config: Alterar SLA Alta para 3 horas"
  git push

Passo 6: Fazer redeploy manual no Render

────────────────────────────────────────────────────────────────────

ALTERAR CORES DAS BADGES (Status):

Arquivo: index.html
Procurar por: .badge-media, .badge-andamento, .badge-concluido

Exemplo de cores:
  Azul: #2196F3
  Verde: #4CAF50
  Vermelho: #f44336
  Laranja: #FF5722
  Amarelo: #FFC107

Editar e fazer deploy

────────────────────────────────────────────────────────────────────

MODIFICAR INTERVALO DE SINCRONIZAÇÃO:

Padrão: 10 segundos

Arquivo: sync_loop.py
Procurar por: time.sleep(10)
Mudar para: time.sleep(60) para 60 segundos

Fazer deploy

⚠️ Cuidado: Sincronizar muito frequentemente pode sobrecarregar SharePoint

────────────────────────────────────────────────────────────────────

ADICIONAR NOVO CAMPO NO FORMULÁRIO:

Exemplo: Adicionar campo "Telefone"

Passo 1: Editar index.html (formulário)
Passo 2: Editar form_handler.py (backend)
Passo 3: Editar sync_loop.py (sincronização)
Passo 4: Atualizar SharePoint para aceitar novo campo

⚠️ Complexo! Pedir ajuda de desenvolvedor

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

9️⃣ SEGURANÇA E BACKUPS

SEGURANÇA:

✅ SEMPRE
  └─ Guardar .env em local seguro
  └─ Nunca fazer commit do .env
  └─ Nunca compartilhar CLIENT_SECRET
  └─ Usar 2FA no GitHub e Vercel
  └─ Revisar quem tem acesso ao repositório

❌ NUNCA
  └─ Colocar .env no GitHub
  └─ Compartilhar credenciais por email
  └─ Usar mesma senha em vários serviços
  └─ Deixar terminal aberto com git bash

BACKUPS:

SharePoint (Automático):
  └─ Microsoft mantém backups
  └─ Dados estão seguros

GitHub (Automático):
  └─ GitHub mantém histórico de versões
  └─ Recuperar versão antiga: git revert

Backup Manual (Recomendado mensal):
  1. Exportar dados do SharePoint (Excel)
  2. Fazer git clone para outro local
  3. Guardar em pendrive ou nuvem

RENOVAR CREDENCIAIS:

CLIENT_SECRET (Azure):
  └─ Válido por: 2 anos
  └─ Quando renovar: Antes de expirar
  └─ Como renovar: Ver seção "Acessos e Credenciais"

Password Email (Corporativo):
  └─ Válido por: Conforme política da UNIFEB
  └─ Quando renovar: Conforme notificação
  └─ Como renovar: Solicitar ao RH

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔟 ROTEIROS PASSO A PASSO

CENÁRIO 1: Dashboard não está sincronizando

Passo 1: Abrir dashboard
Passo 2: Ver topo direito - qual é o status?
  └─ Se 🟢 Sincronizado: OK, não tem problema
  └─ Se 🔴 Erro: Continuar com próximos passos

Passo 3: Apertar F5 para recarregar
Passo 4: Aguardar 10 segundos
Passo 5: Se ainda 🔴 Erro:
  └─ Abrir console (F12)
  └─ Procurar por mensagens de erro vermelhas
  └─ Anotar a mensagem exata

Passo 6: Verificar se backend está online:
  └─ Abrir: https://unifeb-backend.onrender.com/api/chamados
  └─ Se vê JSON com dados: Backend ok
  └─ Se vê erro 404/500: Backend offline

Passo 7: Se backend offline:
  └─ Ir para: https://render.com
  └─ Logar com suas credenciais
  └─ Clicar em: unifeb-backend
  └─ Ver status no topo (Red/Green)
  └─ Se red: Clicar em "Manual Deploy"

Passo 8: Se backend estava offline:
  └─ Aguardar deploy (2-3 minutos)
  └─ Voltar ao dashboard
  └─ Apertar F5

Passo 9: Se ainda não funcionar:
  └─ Verificar logs do Render:
    1. Render → unifeb-backend
    2. Clique em "Logs"
    3. Procure por mensagens de erro vermelhas
    4. Tire screenshot
    5. Envie para Carla Monteiro

────────────────────────────────────────────────────────────────────

CENÁRIO 2: Um departamento não está recebendo setor automático

Passo 1: Qual é o departamento?
  └─ Exemplo: Marketing

Passo 2: Qual é o email?
  └─ Exemplo: joao.marketing@feb.br

Passo 3: Verificar se está mapeado:
  └─ Abrir form_handler.py
  └─ Procurar por "EMAIL_SETOR_MAPPING"
  └─ Procurar por 'marketing'
  └─ Se não estiver, adicionar (ver seção "Adicionar novo departamento")

Passo 4: Criar teste:
  └─ Enviar email de teste para suporte.dti@feb.br
  └─ Com "marketing" no email: teste.marketing@feb.br

Passo 5: Aguardar 10 segundos
Passo 6: Abrir dashboard e procurar novo chamado
Passo 7: Verificar se setor foi preenchido
  └─ Se sim: Problema resolvido!
  └─ Se não: Ir para próximo passo

Passo 8: Verificar logs do Render:
  └─ Render → unifeb-backend → Logs
  └─ Procurar por "Setor extraído"
  └─ Se não aparecer: Sync não rodou ou teve erro
  └─ Fazer redeploy manual no Render

────────────────────────────────────────────────────────────────────

CENÁRIO 3: Preciso gerar relatório urgente

Passo 1: Abrir dashboard
  └─ https://dashboard-unifeb-tv.vercel.app/index.html

Passo 2: Clicar na aba "🎯 Executivo"
  └─ Aguardar carregar (2-3 segundos)

Passo 3: Clicar no botão "📥 Exportar Excel"
  └─ Arquivo vai baixar automaticamente

Passo 4: Abrir arquivo baixado
  └─ Renomear se necessário
  └─ Editar se necessário
  └─ Compartilhar com quem precisa

Passo 5: Se arquivo não baixou:
  └─ Verificar se há dados no dashboard
  └─ Se sim, tentar novamente
  └─ Se não, aguardar sincronização (F5)

────────────────────────────────────────────────────────────────────

CENÁRIO 4: Recebi alerta de SLA crítico

Passo 1: Abrir email com alerta
  └─ Verificar ID do chamado
  └─ Exemplo: #405

Passo 2: Abrir dashboard
  └─ https://dashboard-unifeb-tv.vercel.app/index.html

Passo 3: Clicar na aba "🎯 Executivo"

Passo 4: Procurar na seção "⚠️ Chamados Críticos (< 1h)"
  └─ Encontrar o chamado #405

Passo 5: Anotar:
  └─ Título do chamado
  └─ Setor responsável
  └─ Tempo faltante

Passo 6: Contatar setor responsável
  └─ Informar que SLA está crítico
  └─ Solicitar ação imediata

Passo 7: Após resolução:
  └─ Atualizar status no dashboard
  └─ Se resolvido: Mudar para "Concluído"

────────────────────────────────────────────────────────────────────

CENÁRIO 5: Preciso fazer uma mudança no código

Passo 1: Clonar repositório (primeira vez):
  git clone https://github.com/Carla-Monteiro/Dashboard-UNIFEB-TV

Passo 2: Entrar na pasta:
  cd Dashboard-UNIFEB-TV

Passo 3: Criar branch para mudança:
  git checkout -b feature/sua-mudanca

Passo 4: Fazer mudanças
  └─ Editar arquivo
  └─ Testar localmente

Passo 5: Commit:
  git add [arquivo_modificado]
  git commit -m "Feature: Descrição da mudança"

Passo 6: Push para GitHub:
  git push origin feature/sua-mudanca

Passo 7: Criar Pull Request (PR):
  └─ Ir para: https://github.com/Carla-Monteiro/Dashboard-UNIFEB-TV
  └─ Clicar em: Pull requests
  └─ Clicar em: New pull request
  └─ Selecionar sua branch
  └─ Descrever mudança
  └─ Clicar em: Create pull request

Passo 8: Revisar e merge:
  └─ Se código está OK: Merge para main
  └─ Render/Vercel farão deploy automaticamente

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 SUPORTE FINAL

Se tiver dúvidas que este documento não responde:

1. Verificar README.md (documentação técnica)
2. Procurar em comentários do código
3. Verificar logs (Render, Vercel, console do navegador)
4. Contatar Carla Monteiro para orientação

Bom trabalho! 🚀

═══════════════════════════════════════════════════════════════════════
Versão 1.0 - Criado: 31/07/2026
Próxima revisão recomendada: 31/08/2026
═══════════════════════════════════════════════════════════════════════
