# 🚀 SINCRONIZAÇÃO CONTÍNUA NO RENDER (24/7)

## 🎯 O QUE FOI CRIADO:

Em vez de depender de GitHub Actions (que não funciona), vamos rodar a sincronização **diretamente no Render**, junto com o backend!

---

## 📦 ARQUIVOS NOVOS:

1. **sync_loop.py** - Script que sincroniza continuamente (a cada 10 segundos)
2. **start.sh** - Script que inicia backend + sincronização
3. **Procfile** - Configuração do Render para usar o start.sh

---

## ✅ COMO IMPLEMENTAR:

### Passo 1: Copiar os arquivos para sua pasta

```
C:\Users\carla.monteiro\Dashboard-UNIFEB-TV\

Copie para lá:
✅ sync_loop.py
✅ start.sh
✅ Procfile (substituir o antigo)
```

---

### Passo 2: Fazer upload no GitHub

```bash
cd C:\Users\carla.monteiro\Dashboard-UNIFEB-TV

git add sync_loop.py start.sh Procfile

git commit -m "Feature: Sincronização contínua 24/7 no Render"

git push
```

---

### Passo 3: Render faz redeploy automaticamente

1. Acesse: https://render.com
2. Clique em **unifeb-backend**
3. Aguarde **2-3 minutos**
4. Render vai:
   - ✅ Detectar novo Procfile
   - ✅ Rodar o start.sh
   - ✅ Iniciar sync_loop.py em background
   - ✅ Iniciar form_handler.py em foreground

---

## 🔍 COMO VERIFICAR SE ESTÁ FUNCIONANDO:

### 1️⃣ Verificar Logs do Render

1. Acesse: https://render.com
2. Clique em **unifeb-backend**
3. Vá em **Logs**
4. Procure por:
   ```
   ✅ Sincronização iniciada em background!
   1️⃣  Iniciando sincronização contínua...
   2️⃣  Iniciando backend Flask...
   ✅ [HH:MM:SS] Sincronizado: X chamados
   ```

---

### 2️⃣ Verificar Health do Backend

Acesse:
```
https://unifeb-backend.onrender.com/health
```

Deve retornar:
```json
{"status":"ok"}
```

---

## 🔄 COMO FUNCIONA AGORA:

```
ANTES (não funcionava):
GitHub Actions → (cron a cada 3 min) → ❌ Não rodava
                                    ❌ GitHub Actions bugado

DEPOIS (funcionando 24/7):
Render start.sh
    ├── sync_loop.py (background)
    │   └── Sincroniza a cada 10 segundos
    │       └── Salva chamados_sync.json
    │
    └── form_handler.py (foreground)
        └── Backend API rodando na porta 10000
```

---

## ⏱️ FLUXO COMPLETO:

```
1. Você edita um chamado no dashboard
2. Backend salva no SharePoint (PATCH)
3. Backend retorna: "sucesso"
4. Frontend recarrega JSON (chamados_sync.json)
5. Dashboard atualiza com dados NOVOS ⚡

E SIMULTANEAMENTE:

1. sync_loop.py roda a cada 10 segundos
2. Sincroniza TODOS os chamados do SharePoint
3. Salva em chamados_sync.json (atualizado constantemente)
```

---

## 📊 BENEFÍCIOS:

✅ **Sincronização 24/7** (sem depender de GitHub Actions)  
✅ **A cada 10 segundos** (muito rápido!)  
✅ **Tudo no Render** (um servidor só)  
✅ **Dados sempre atualizados** (sem delay)  
✅ **Backend + Sincronização juntos**  

---

## 🚀 PRÓXIMOS PASSOS:

1. ✅ Upload dos 3 arquivos no GitHub
2. ✅ Git push
3. ✅ Render faz redeploy (2-3 minutos)
4. ✅ Verificar logs do Render
5. ✅ Testar no dashboard!

---

## ⚠️ NOTA IMPORTANTE:

Se o Render ficar muito lento (sincronização + backend):
- Mudar intervalo de `10 segundos` para `30 segundos` em `sync_loop.py`
- Mudar linha: `time.sleep(10)` para `time.sleep(30)`

Mas 10 segundos deve funcionar bem!

---

**Pronto para implementar? Manda fazer o upload!** 🎊
