# Dashboard UNIFEB TV 📺

Dashboard em tempo real para gerenciamento de chamados do SharePoint da UNIFEB, otimizado para exibição em TV.

## ✨ Features

- 📊 **Sincronização automática** com SharePoint (a cada 5 minutos)
- 📈 **Gráficos em tempo real** (Status, Prioridade, Setor)
- 🎯 **SLA dinâmico** por prioridade (Alta=2h, Média=8h, Baixa=24h)
- 🔄 **Auto-refresh** a cada 5 segundos
- 🎨 **Interface moderna** otimizada para TV
- 📱 **Responsivo** para desktop e mobile

## 📋 Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)
- Acesso ao SharePoint UNIFEB

## 🚀 Instalação

### 1. Clonar repositório

```bash
git clone https://github.com/Carla-Monteiro/Dashboard-UNIFEB-TV.git
cd Dashboard-UNIFEB-TV
```

### 2. Instalar dependências

```bash
pip install -r requirements-tv.txt
```

### 3. Executar sincronizador (Terminal 1)

```bash
python sync_sharepoint_tv.py
```

Isso vai sincronizar os chamados do SharePoint e gerar `chamados_sync.json`.

### 4. Executar servidor web (Terminal 2)

```bash
python -m http.server 8000
```

### 5. Abrir no navegador

```
http://localhost:8000/index.html
```

## 📂 Estrutura de Arquivos

```
Dashboard-UNIFEB-TV/
├── index.html                  # Dashboard UI (HTML/CSS/JS)
├── logo-UNIFEB.png             # Logo da instituição
├── chamados_sync.json          # Dados sincronizados (gerado)
├── sync_sharepoint_tv.py       # Script de sincronização
├── servidor.py                 # Servidor HTTP customizado
├── requirements-tv.txt         # Dependências Python
├── README.md                   # Esta documentação
└── .gitignore                  # Arquivos ignorados pelo Git
```

## 🔧 Configuração SharePoint

As credenciais do SharePoint estão configuradas no `sync_sharepoint_tv.py`:

```python
CLIENT_ID = "seu_client_id"
CLIENT_SECRET = "seu_client_secret"
TENANT_ID = "seu_tenant_id"
```

## 📊 Dados do JSON

O arquivo `chamados_sync.json` contém:

```json
{
  "atualizado_em": "ISO datetime",
  "total_chamados": 2,
  "chamados": [
    {
      "id": "363",
      "titulo": "Troca de toner",
      "solicitante": "Carla Monteiro",
      "status": "Aberto",
      "prioridade": "Alta",
      "setorAtendimento": "Matrícula",
      "descricao": "...",
      "data": "ISO datetime",
      "slaVencido": true,
      "slaAtraso": "142h 59min",
      "slaAberto": "166h 59min",
      "slaHoras": 2
    }
  ]
}
```

## 🎨 Interface

### Abas Disponíveis
- **📋 Chamados Detalhados** - Tabela com todos os chamados
- **📊 Gráficos** - Estatísticas e visualizações

### Filtros
- Status (Aberto, Em andamento, Resolvido)
- Prioridade (Alta, Média, Baixa)
- Busca por ID, Título ou Solicitante

## ⏰ SLA por Prioridade

| Prioridade | SLA |
|-----------|-----|
| 🔴 Alta   | 2h  |
| 🟡 Média  | 8h  |
| 🟢 Baixa  | 24h |

## 🔄 Sincronização

O script `sync_sharepoint_tv.py`:
- ✅ Autentica no Azure AD
- ✅ Lê chamados do SharePoint
- ✅ Filtra lixo/testes
- ✅ Calcula SLA dinamicamente
- ✅ Salva em `chamados_sync.json`
- ✅ Executa a cada 5 minutos

## 📱 Responsividade

- **Desktop (1920px+)** - Layout completo com 3 colunas de gráficos
- **Tablet (768px-1200px)** - 1 coluna de gráficos
- **Mobile (<768px)** - Interface otimizada para telas pequenas

## 🐛 Troubleshooting

### Chamados não aparecem
- Verifique as credenciais do SharePoint
- Confirme que o campo de ID é `id` (minúsculo)
- Confirme que o campo de Setor é `SetordeAtendimento`

### Logo não aparece
- Certifique-se que `logo-UNIFEB.png` está na mesma pasta do `index.html`

### Porta 8000 em uso
```bash
python -m http.server 9000
```

## 📝 Licença

MIT License - veja LICENSE para detalhes

## 👥 Autor

Carla Monteiro - UNIFEB

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no GitHub.

---

**Última atualização:** 29/07/2026 ✨
