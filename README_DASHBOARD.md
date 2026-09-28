# Dashboard de Controle de Chamados - UNIFEB

## 📋 Descrição

Dashboard interativo em tempo real para gerenciamento de chamados do suporte UNIFEB. Interface moderna com tema escuro, integração com API de dados e funcionalidades avançadas.

## 🎯 Características

✅ **Dados em Tempo Real** - Integração com sua API/banco de dados
✅ **Interface Responsiva** - Funciona em desktop e mobile
✅ **Tema Escuro Moderno** - Design profissional
✅ **Filtros Avançados** - Status, prioridade, busca por texto
✅ **Modal Detalhado** - Veja histórico e detalhes de cada chamado
✅ **Auto-atualização** - Sincroniza dados automaticamente a cada 30s
✅ **Abas Dinâmicas** - Separa chamados ativos de concluídos

## 📁 Estrutura de Arquivos

```
seu-projeto/
├── dashboard_chamados.html     # Interface principal
├── config.js                   # Configuração e API
├── dashboard.js                # Lógica e funcionalidades
└── README_DASHBOARD.md         # Este arquivo
```

## 🚀 Como Usar

### 1️⃣ Copiar os arquivos
Coloque os 3 arquivos na raiz do seu projeto:
- `dashboard_chamados.html`
- `config.js`
- `dashboard.js`

### 2️⃣ Abrir no navegador
```bash
# Opção 1: Abrir o arquivo diretamente
start dashboard_chamados.html

# Opção 2: Usar um servidor local (recomendado)
python -m http.server 8000
# Então abra: http://localhost:8000/dashboard_chamados.html
```

### 3️⃣ Configurar a API
Edite o arquivo `config.js`:

```javascript
// Altere a URL para sua API
const API_BASE_URL = 'http://seu-servidor.com/api';
```

## 🔌 Integração com API

### Formato esperado dos dados

O dashboard espera receber dados neste formato de sua API:

#### Chamados Ativos (GET `/api/chamados/ativos`)

```json
[
  {
    "id": "#001",
    "titulo": "Erro ao acessar SharePoint",
    "solicitante": "João Silva",
    "email": "joao@unifeb.com",
    "status": "Aberto",
    "prioridade": "Alta",
    "categoria": "TI",
    "data_criacao": "2024-09-28",
    "data_prazo": "2024-09-30",
    "descricao": "Descrição do chamado...",
    "historico": [
      {
        "acao": "Ticket criado",
        "tempo": "2 horas atrás"
      },
      {
        "acao": "Atribuído ao técnico",
        "tempo": "1 hora atrás"
      }
    ]
  }
]
```

#### Estatísticas (GET `/api/chamados/stats`)

```json
{
  "abertos": 12,
  "andamento": 1,
  "concluidos": 28,
  "vencidos": 13
}
```

#### Chamados Concluídos (GET `/api/chamados/concluidos`)

```json
[
  {
    "id": "#U001",
    "titulo": "Reset de senha",
    "solicitante": "Carlos Mendes",
    "categoria": "TI",
    "data_conclusao": "2024-09-20",
    "avaliacao": "⭐⭐⭐⭐⭐"
  }
]
```

## 🔧 Adaptar sua API Python

Se você está usando `form_handler.py`, adicione estes endpoints:

```python
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# Endpoint: Chamados ativos
@app.route('/api/chamados/ativos', methods=['GET'])
def get_chamados_ativos():
    """Retorna todos os chamados com status diferente de 'Concluído'"""
    chamados = []  # Buscar do banco de dados
    return jsonify(chamados)

# Endpoint: Chamados concluídos
@app.route('/api/chamados/concluidos', methods=['GET'])
def get_chamados_concluidos():
    """Retorna chamados com status 'Concluído'"""
    chamados = []  # Buscar do banco de dados
    return jsonify(chamados)

# Endpoint: Estatísticas
@app.route('/api/chamados/stats', methods=['GET'])
def get_stats():
    """Retorna contagem de chamados por status"""
    stats = {
        'abertos': count_by_status('Aberto'),
        'andamento': count_by_status('Em Andamento'),
        'concluidos': count_by_status('Concluído'),
        'vencidos': count_vencidos()
    }
    return jsonify(stats)

# Endpoint: Detalhe de um chamado
@app.route('/api/chamados/<id>', methods=['GET'])
def get_chamado_detalhe(id):
    """Retorna detalhes de um chamado específico"""
    chamado = {}  # Buscar do banco de dados
    return jsonify(chamado)
```

## 📊 Exemplos de Status e Prioridades

### Status disponíveis:
- 📂 **Aberto** - Novo chamado
- ⏳ **Em Andamento** - Sendo atendido
- ⏸️ **Aguardando** - Aguardando cliente
- ✅ **Concluído** - Finalizado
- 🚨 **Vencido** - SLA ultrapassado

### Prioridades:
- 🔴 **Crítica** - Vermelho
- 🔴 **Alta** - Vermelho
- 🟠 **Média** - Laranja
- 🟢 **Baixa** - Verde

## 🔄 Atualizações Automáticas

O dashboard atualiza os dados automaticamente a cada **30 segundos** (configurável em `config.js`):

```javascript
const AUTO_REFRESH_INTERVAL = 30000; // em milissegundos
```

Para alterar o intervalo:
```javascript
const AUTO_REFRESH_INTERVAL = 60000; // 60 segundos
```

## 🐛 Solução de Problemas

### "API não respondendo"
- Verifique se a URL em `config.js` está correta
- Certifique-se que seu servidor está rodando
- Verifique o console do navegador (F12) para erros

### "Nenhum chamado encontrado"
- Verifique se sua API está retornando dados
- Confirme que o formato dos dados está correto
- Use o console (F12) para ver as requisições

### "Modal não abre"
- Tente recarregar a página (F5)
- Verifique se há erros no console
- Limpe o cache do navegador (Ctrl+Shift+Del)

## 📝 Notas Importantes

1. **CORS**: Se está em um servidor diferente, configure CORS na sua API:
```python
from flask_cors import CORS
CORS(app)
```

2. **Autenticação**: Se sua API requer autenticação, adicione em `config.js`:
```javascript
const headers = {
  'Authorization': 'Bearer seu-token-aqui',
  'Content-Type': 'application/json'
};
```

3. **Segurança**: Nunca exponha tokens ou senhas no JavaScript. Use variáveis de ambiente.

## 🎨 Customizar Cores

Edite as variáveis CSS no início de `dashboard_chamados.html`:

```css
:root {
  --gold: #ffa500;      /* Cor primária */
  --green: #10b981;     /* Verde de sucesso */
  --red: #ef5350;       /* Vermelho de erro */
  --blue: #60a5fa;      /* Azul de info */
}
```

## 📱 Responsividade

O dashboard é totalmente responsivo e funciona em:
- ✅ Desktop (1920px+)
- ✅ Tablet (768px - 1024px)
- ✅ Mobile (< 768px)

## 📞 Suporte

Se encontrar problemas:
1. Verifique o console do navegador (F12 > Console)
2. Veja os logs de rede (F12 > Network)
3. Consulte a documentação da API

## 📄 Licença

Este código é fornecido como está para uso interno da UNIFEB.

---

**Última atualização**: Setembro 2024
**Versão**: 1.0
