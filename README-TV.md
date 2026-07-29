# 🎯 Dashboard UNIFEB - TV Tempo Real

## 📋 O QUE É

Dashboard que mostra chamados do SharePoint **em tempo real** na TV.

```
SharePoint (dados reais)
    ↓
Python Script (sincroniza a cada 5 min)
    ↓
JSON (chamados_sync.json)
    ↓
GitHub + Vercel
    ↓
📺 Dashboard na TV!
```

---

## 🚀 INSTALAÇÃO RÁPIDA

### **1. Instalar Dependências**

```bash
pip install -r requirements-tv.txt
```

### **2. Copiar Logo UNIFEB**

Coloque o arquivo `logo-UNIFEB.png` na mesma pasta

### **3. Primeira Sincronização**

```bash
python sync_sharepoint_tv.py
```

Vai gerar `chamados_sync.json` com os dados reais

### **4. Abrir Dashboard**

```bash
# Opção 1: Abrir arquivo local
file:///caminho/para/Dashboard-UNIFEB-TV/index.html

# Opção 2: Com servidor Python (melhor)
python -m http.server 8000
# Depois: http://localhost:8000
```

---

## 📦 ARQUIVOS

| Arquivo | Função |
|---------|--------|
| **index.html** | Dashboard (abra no navegador) |
| **sync_sharepoint_tv.py** | Script que sincroniza (execute no terminal) |
| **chamados_sync.json** | Dados atualizados (gerado automaticamente) |
| **logo-UNIFEB.png** | Logo da instituição |
| **requirements-tv.txt** | Dependências Python |

---

## ⚙️ COMO FUNCIONA

### **Script Python**

1. Autentica no Azure (usando credenciais)
2. Conecta ao SharePoint
3. Lê lista "Chamados"
4. **Salva em JSON** cada 5 minutos
5. Continuamente

```
Terminal rodando:
🚀 Script sincroniza SharePoint a cada 5 minutos
📝 Atualiza chamados_sync.json
✅ Dashboard vê dados novos
```

### **Dashboard HTML**

1. Carrega `chamados_sync.json`
2. Mostra tabela com filtros
3. Atualiza a cada 5 segundos (verifica mudanças)
4. Exibe logo UNIFEB
5. Pronto para TV!

---

## 🎨 FUNCIONALIDADES

✅ **Filtros:**
- Status (Aberto, Em andamento, Resolvido, Fechado)
- Prioridade (Alta, Média, Baixa)
- Busca (ID, Título, Solicitante)

✅ **Tabela com:**
- ID do chamado
- Título
- Solicitante
- Prioridade (com cores)
- Status (com cores)
- Setor
- Data de abertura
- Descrição
- SLA Vencido

✅ **Design:**
- Cores UNIFEB (azul + laranja)
- Responsivo (TV, desktop, tablet)
- Logo no topo
- Atualização automática

---

## 🔄 SINCRONIZAÇÃO AUTOMÁTICA

### **Primeira Vez**

```bash
python sync_sharepoint_tv.py
```

Vai:
1. Sincronizar agora
2. Agendar próximas (a cada 5 min)
3. Rodar indefinidamente

**Deixe rodando!**

### **Se Fechar**

Simplesmente execute de novo:
```bash
python sync_sharepoint_tv.py
```

Vai sincronizar imediatamente e continuar

---

## 📺 USAR NA TV

### **Opção 1: Abrir Navegador**

```
URL: http://seu-dominio.vercel.app
ou
URL: http://localhost:8000
```

Deixar em fullscreen (F11)

### **Opção 2: GitHub + Vercel (Recomendado!)**

Veja seção abaixo

---

## 🚀 PUBLICAR NO GITHUB + VERCEL

### **1. Criar Repositório GitHub**

```bash
cd Dashboard-UNIFEB-TV

git init
git add .
git commit -m "🚀 Dashboard UNIFEB TV"
git branch -M main
git remote add origin https://github.com/seu-usuario/Dashboard-UNIFEB-TV
git push -u origin main
```

### **2. Fazer Deploy no Vercel**

1. Acesse: https://vercel.com
2. "Import Project"
3. Selecione repositório GitHub
4. Importar
5. Deploy automático!

**Resultado:**
```
https://seu-projeto.vercel.app
```

---

## 🔐 CREDENCIAIS

O script usa:

```python
CLIENT_ID="100ba4af-831a-4d3c-8e96-60e683f0152a"
CLIENT_SECRET="seu_client_secret_aqui"
TENANT_ID="62a0e447-20c2-41be-8e60-893b78364660"
```

**⚠️ Segurança:** Se compartilhar repositório, coloque credenciais em `.env`

---

## 📊 DADOS

Campos do JSON:
- `id`: ID do chamado (#363, #364, etc)
- `titulo`: Título do chamado
- `solicitante`: Quem abriu
- `status`: Aberto, Em andamento, Resolvido, Fechado
- `prioridade`: Alta, Média, Baixa
- `setor`: Departamento
- `descricao`: Descrição do chamado
- `data`: Data de abertura
- `slaVencido`: Verdadeiro se SLA venceu
- `slaAviso`: Aviso de SLA próximo

---

## 🐛 TROUBLESHOOTING

### **Erro: "Arquivo chamados_sync.json não encontrado"**

Execute o script primeiro:
```bash
python sync_sharepoint_tv.py
```

### **Dashboard não atualiza**

Aguarde 5 segundos (intervalo de verificação)

### **Erro de autenticação no script**

Verifique credenciais Azure no código

### **Logo não aparece**

Coloque `logo-UNIFEB.png` na mesma pasta

---

## ✅ CHECKLIST

- [ ] Python 3.8+ instalado?
- [ ] `pip install -r requirements-tv.txt` executado?
- [ ] `logo-UNIFEB.png` está na pasta?
- [ ] Rodei `python sync_sharepoint_tv.py` (primeira vez)?
- [ ] Abri `index.html` no navegador?
- [ ] Dashboard mostra chamados?
- [ ] Filtros funcionam?
- [ ] Logo aparece?

Se todos ✅, está **PRONTO PARA TV!** 🎉

---

## 🎊 RESULTADO FINAL

```
┌─────────────────────────────────────────┐
│          📺 Dashboard UNIFEB             │
│                                         │
│  🟢 Sincronizado • 2 chamados • 11:30   │
│                                         │
│  Filtros: Status | Prioridade | Busca  │
│                                         │
│  Tabela com:                            │
│  • #363 - Troca de toner (Aberto)      │
│  • #364 - Instalação Office (Em anda)  │
│                                         │
│  Com cores, SLA, descrição, etc        │
│  Atualiza automaticamente!              │
└─────────────────────────────────────────┘
```

**Perfeito para TV!** 📺✨

---

## 📞 SUPORTE

Qualquer erro:
1. Verifique credenciais Azure
2. Verifique se SharePoint está acessível
3. Verifique se logo UNIFEB existe
4. Recarregue o navegador

---

**Tudo pronto! Aproveite!** 🚀
