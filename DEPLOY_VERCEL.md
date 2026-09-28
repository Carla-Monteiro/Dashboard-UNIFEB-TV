# 🚀 Deploy no Vercel - Dashboard UNIFEB

## Opção 1: Deploy Frontend no Vercel (RECOMENDADO)

### Passo 1: Instalar Vercel CLI
```bash
npm install -g vercel
```

### Passo 2: Logar na Vercel
```bash
vercel login
```

### Passo 3: Fazer Deploy
```bash
cd C:\Users\carla.monteiro\Documents\Dashboard-UNIFEB-TV
vercel
```

Siga as instruções:
- **Project name**: Dashboard-UNIFEB-TV
- **Directory**: ./ (raiz)
- **Build command**: (deixe em branco)

### Passo 4: URL Pública
Você receberá uma URL como:
```
https://dashboard-unifeb-tv.vercel.app
```

---

## ⚠️ IMPORTANTE: API Backend

A API Python (`form_handler.py`) precisa estar rodando em um servidor!

### Opção A: Render.com (RECOMENDADO - Gratuito)

1. **Ir em**: https://render.com
2. **Criar conta** com GitHub
3. **Clique em "New +"** → **Web Service**
4. **Conectar GitHub** e selecionar seu repositório
5. **Configurar:**
   - **Name**: dashboard-unifeb-tv
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python form_handler.py`
6. **Deploy!**

Você receberá uma URL como:
```
https://dashboard-unifeb-tv.onrender.com
```

---

## 🔗 Atualizar URL da API

No arquivo `config.js`, altere:

```javascript
// DE:
const API_BASE_URL = 'http://localhost:10000/api';

// PARA:
const API_BASE_URL = 'https://dashboard-unifeb-tv.onrender.com/api';
```

---

## 📝 Criar `requirements.txt`

Na raiz da pasta, crie um arquivo `requirements.txt`:

```
Flask==2.3.2
Flask-CORS==4.0.0
python-dotenv==1.0.0
requests==2.31.0
```

Depois:
```bash
git add requirements.txt
git commit -m "Adicionar requirements.txt para deploy"
git push origin main
```

---

## 🎯 URLs Finais

**Frontend (Vercel)**:
```
https://seu-projeto.vercel.app
```

**Backend (Render)**:
```
https://seu-projeto.onrender.com
```

---

## 📌 Variáveis de Ambiente no Render

1. **Ir em Settings** do seu projeto no Render
2. **Environment** 
3. **Adicionar:**
   - `CLIENT_ID` = (seu valor)
   - `CLIENT_SECRET` = (seu valor)
   - `TENANT_ID` = (seu valor)
   - `DASHBOARD_PASSWORD` = (sua senha)

---

## ✅ Checklist Deploy

- [ ] CLI Vercel instalado
- [ ] Logado na Vercel
- [ ] Deploy frontend feito
- [ ] Conta Render criada
- [ ] Deploy backend feito
- [ ] `requirements.txt` criado e commitado
- [ ] Variáveis de ambiente configuradas
- [ ] `config.js` atualizado com URL do backend
- [ ] Fazer novo commit e push
- [ ] Testar em produção

---

## 🧪 Testar em Produção

1. Abra: `https://seu-projeto.vercel.app`
2. Abra o Console (F12)
3. Faça login como antes
4. Dashboard deve carregar com dados do SharePoint!

---

## 🆘 Troubleshooting

### "CORS Error"
- Verificar se a API está rodando
- Verificar variáveis de ambiente no Render
- Verificar URL no config.js

### "API não responde"
- Ir no Render e verificar logs
- Verificar se CLIENT_ID/CLIENT_SECRET estão corretos
- Reiniciar o serviço no Render

### "Dados não aparecem"
- Verificar token de autenticação
- Ver console do navegador (F12)
- Checar logs da API no Render

---

## 💡 Dicas

- Use `vercel --prod` para fazer deploy em produção
- Monitorar logs no Render: `https://dashboard.render.com`
- O Render oferece 750 horas/mês grátis
- Vercel oferece hosting gratuito permanente

---

## 📱 Acessar de Qualquer Lugar

Depois de deployado, você pode acessar:
- 🖥️ **Desktop**: https://seu-projeto.vercel.app
- 📱 **Mobile**: mesma URL
- 🌍 **De qualquer lugar**: funciona!

---

**Pronto para produção!** 🚀
