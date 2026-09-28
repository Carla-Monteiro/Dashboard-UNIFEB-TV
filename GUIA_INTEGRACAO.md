# 🎯 Guia de Integração - Dashboard com SharePoint

## ✅ Status Atual

Você tem:
- ✅ **SharePoint** como banco de dados
- ✅ **form_handler.py** rodando com autenticação OAuth2
- ✅ **Endpoint `/api/chamados`** que retorna todos os chamados
- ✅ **Dashboard HTML** pronto para usar
- ✅ **3 novos endpoints** prontos para copiar

## 📋 O que falta

Adicionar 3 novos endpoints ao seu `form_handler.py`:
1. `GET /api/chamados/ativos` - Chamados não concluídos
2. `GET /api/chamados/concluidos` - Apenas concluídos
3. `GET /api/chamados/stats` - Contagem por status

---

## 🚀 PASSO A PASSO DE INTEGRAÇÃO

### **Passo 1: Copiar o arquivo de endpoints**

Abra o arquivo `endpoints_dashboard.py` que foi criado na sua pasta:
```
C:\Users\carla.monteiro\Documents\Dashboard-UNIFEB-TV\endpoints_dashboard.py
```

### **Passo 2: Adicionar ao form_handler.py**

Abra seu `form_handler.py` e, antes do final do arquivo (antes de `if __name__ == '__main__':`), adicione:

```python
# ========================================
# ENDPOINTS PARA DASHBOARD
# ========================================

# Cole aqui TODO o conteúdo de endpoints_dashboard.py
# (sem as linhas de comentário do topo)

```

### **Passo 3: Configurar a URL no Dashboard**

Edite `config.js` e altere a linha:

```javascript
const API_BASE_URL = 'http://localhost:5000/api'; // Altere a porta se necessário
```

Para sua URL real (porta que seu `form_handler.py` roda):

```javascript
const API_BASE_URL = 'http://localhost:5000/api'; // Exemplo: se rodar em porta 5000
```

### **Passo 4: Testar Localmente**

#### Terminal 1 - Rodar API Python:
```bash
cd C:\Users\carla.monteiro\Documents\Dashboard-UNIFEB-TV
python form_handler.py
# Deve aparecer: "Running on http://localhost:5000"
```

#### Terminal 2 - Rodar Servidor HTTP:
```bash
cd C:\Users\carla.monteiro\Documents\Dashboard-UNIFEB-TV
python -m http.server 8000
# Deve aparecer: "Serving HTTP on port 8000"
```

#### Abrir no Navegador:
```
http://localhost:8000/dashboard_chamados.html
```

### **Passo 5: Fazer Login no Dashboard**

1. Abra `dashboard_chamados.html`
2. Você verá um formulário de login
3. **Problema**: O dashboard ainda não tem a parte de login integrada

---

## ⚠️ PRÓXIMO PASSO: ADICIONAR LOGIN

Para o dashboard conseguir fazer requisições autenticadas, você precisa:

1. **Criar uma página de login** (ou adicionar ao HTML existente)
2. **Guardar o token** no localStorage
3. **Enviar o token** em todas as requisições

### Solução Temporária (para testar):

Edite `config.js` e adicione seu token manualmente:

```javascript
// TEMPORÁRIO - Adicione um token válido aqui depois do login
const AUTH_TOKEN = 'seu-token-aqui'; // Pegar após fazer login em /api/login

/**
 * Buscar chamados ativos da API
 */
async function buscarChamadosAtivos() {
  try {
    const response = await fetch(ENDPOINTS.chamadosAtivos, {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json'
      }
    });
    // ... resto do código
  }
}
```

---

## 🔐 Sistema de Login Completo

Para integração completa, preciso criar uma página de login que:

1. Faz POST para `/api/login` com a senha
2. Recebe o token
3. Guarda no localStorage
4. Usa em todas as requisições

**Quer que eu crie a página de login também?** Avisa!

---

## 📊 Estrutura de Dados Esperada

Seu endpoint atual (`/api/chamados`) retorna:
```json
[
  {
    "id": "item_id",
    "titulo": "Título do chamado",
    "solicitante": "Nome",
    "email": "email@unifeb.br",
    "status": "Aberto",
    "prioridade": "Média",
    "dataAbertura": "2024-09-28T10:00:00",
    "descricao": "...",
    "categoria": "TI / Internet",
    "historico": [...]
  }
]
```

Os novos endpoints transformam isso em:

### `/api/chamados/ativos`
```json
[
  {
    "id": "item_id",
    "titulo": "Título do chamado",
    "solicitante": "Nome",
    "email": "email@unifeb.br",
    "status": "Aberto",  // normalizado
    "prioridade": "Alta", // normalizado
    "categoria": "TI",
    "data_criacao": "28/09/2024",
    "data_prazo": "30/09/2024",
    "descricao": "...",
    "historico": [...]
  }
]
```

### `/api/chamados/stats`
```json
{
  "abertos": 12,
  "andamento": 1,
  "concluidos": 28,
  "vencidos": 13
}
```

---

## 🐛 Troubleshooting

### "Erro 401 - Não autorizado"
- Seu token expirou ou é inválido
- Faça login novamente em `/api/login`

### "Nenhum chamado encontrado"
- Verifique se há chamados no SharePoint
- Confirme que a autenticação está funcionando

### "CORS Error"
- Já está resolvido: seu `form_handler.py` tem `CORS(app)`

### "API não responde"
- Verifique se `form_handler.py` está rodando
- Confirme a porta (default: 5000)

---

## ✅ Checklist Final

- [ ] Copiei os endpoints de `endpoints_dashboard.py` para `form_handler.py`
- [ ] Configurei a URL em `config.js`
- [ ] Testei localmente (2 terminais + navegador)
- [ ] Dashboard aparece
- [ ] Dados aparecem nas tabelas

**Se tudo funcionar, passa para o próximo passo!** 🚀

---

## 📞 Precisa de Ajuda?

Me avisa se:
- Tiver erro ao adicionar os endpoints
- Quiser criar a página de login
- Quiser adicionar mais funcionalidades
- Tiver alguma dúvida sobre a integração

**Vamos de passo em passo!** 💪
