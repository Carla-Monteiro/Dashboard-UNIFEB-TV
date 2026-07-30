# 🎯 Dashboard UNIFEB - Controle de Chamados

**Gerenciamento em Tempo Real de Chamados do SharePoint**

---

## 📊 Características

✅ **Sincronização Automática** - A cada 3 minutos via GitHub Actions  
✅ **Dashboard em Tempo Real** - Interface moderna e responsiva  
✅ **Cálculo de SLA** - Alta (2h), Média (8h), Baixa (24h)  
✅ **Dados do SharePoint** - Sincroniza 4 chamados com setores corretos  
✅ **Deploy Automático** - Vercel atualiza dashboard automaticamente  

---

## 🚀 Sincronização

### Local (Manual)

```bash
python sync_sharepoint_tv.py
```

Digite as credenciais quando solicitado:
```
CLIENT_ID: 100ba4af-831a-4d3c-8e96-60e683f0152a
CLIENT_SECRET: P338Q~zC04Td8P1rk_srVCl-pS2wlzWzSGl9da3T
TENANT_ID: 62a0e447-20c2-41be-8e60-893b78364660
```

### Automático (GitHub Actions)

- ✅ Executa a cada 3 minutos
- ✅ Sincroniza chamados do SharePoint
- ✅ Faz commit e push automático
- ✅ Vercel faz deploy

---

## 📁 Estrutura do Projeto

```
Dashboard-UNIFEB-TV/
├── .github/
│   └── workflows/
│       └── sync-sharepoint.yml
├── index.html
├── chamados_sync.json
├── sync_sharepoint_tv.py
├── sync_github.py
├── requirements.txt
├── README.md
├── .env
└── .gitignore
```

---

## 🔧 Requisitos

- Python 3.11+
- Bibliotecas: `requests`
- Credenciais Azure AD configuradas em `.env`

---

## 📝 Credenciais (.env)

```
CLIENT_ID=100ba4af-831a-4d3c-8e96-60e683f0152a
CLIENT_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TENANT_ID=62a0e447-20c2-41be-8e60-893b78364660
SHAREPOINT_DOMAIN=unifeb.sharepoint.com
SITE_PATH=/sites/SuporteDTI
LIST_NAME=Chamados
```

⚠️ **NUNCA fazer commit do .env!**

---

## 📊 Dashboard

Acesse: https://dashboard-unifeb-tv.vercel.app/index.html

Mostra:
- 4 Chamados sincronizados
- SetordeAtendimento (Matrícula, Ouvidoria, Colégio FEB, Núcleo Práticas Jurídicas)
- Prioridades (Alta, Média)
- Status (Aberto, Em andamento)
- SLA calculado dinamicamente

---

## 🎊 Pronto para Produção

✅ Dashboard funcional 24/7  
✅ Sincronização automática a cada 3 minutos  
✅ Deploy contínuo via Vercel  
✅ Segurança: credenciais em GitHub Secrets  

---

**Desenvolvido com ❤️ para UNIFEB**
