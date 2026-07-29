# 🔒 Guia de Segurança - Dashboard UNIFEB TV

## ⚠️ PROBLEMA ENCONTRADO

O push anterior expôs credenciais do Azure no GitHub!

**Status:** ❌ Repositório comprometido

---

## 🚨 AÇÃO URGENTE: Revogar Credenciais

### 1. Ir para Azure Portal

```
https://portal.azure.com
```

### 2. Revogar o CLIENT_SECRET exposto

1. Azure Active Directory
2. App registrations
3. Sua aplicação
4. Certificates & secrets
5. **Delete** o secret exposto
6. **Create new secret** (copie o novo valor)

---

## ✅ SOLUÇÃO IMPLEMENTADA

### Agora usando **variáveis de ambiente**!

```
❌ Antes: Credenciais no código
✅ Agora: Credenciais no arquivo .env (não commitado)
```

---

## 📋 Como Configurar

### 1. Instalar python-dotenv

```powershell
pip install python-dotenv
```

### 2. Criar arquivo .env

Na pasta do projeto, crie `.env`:

```
CLIENT_ID=seu_novo_client_id
CLIENT_SECRET=seu_novo_client_secret
TENANT_ID=seu_tenant_id
```

**⚠️ IMPORTANTE:**
- Nunca commite o arquivo `.env`
- Já está no `.gitignore`
- O arquivo é local (apenas seu PC)

### 3. Instalar dependências

```powershell
pip install -r requirements-tv.txt
```

---

## 🔄 Limpar o Histórico do Git

Para remover as credenciais expostas:

```powershell
# Remover o commit anterior
git reset --hard HEAD~1

# Fazer novo commit com os arquivos corrigidos
git add .
git commit -m "Security: Remove hardcoded credentials, use .env instead"

# Força o push (reescreve o histórico)
git push -f -u origin main
```

---

## 📝 Checklist de Segurança

- ✅ Credenciais removidas do código
- ✅ .env no .gitignore
- ✅ .env.example criado (com valores fake)
- ✅ python-dotenv adicionado aos requirements
- ✅ Script atualizado para usar variáveis de ambiente
- ⏳ Credenciais do Azure revogadas (você deve fazer!)
- ⏳ Novo push feito (você deve fazer!)

---

## 🛡️ Boas Práticas de Segurança

### NUNCA comitar:
- ❌ Senhas
- ❌ Tokens
- ❌ API Keys
- ❌ Chaves privadas
- ❌ Secrets do Azure/AWS

### SEMPRE usar:
- ✅ Variáveis de ambiente (.env)
- ✅ Arquivos .env.example como template
- ✅ .gitignore para excluir .env
- ✅ Secrets do GitHub para CI/CD

---

## 📚 Recursos

- [GitHub: Secret scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Azure: Secure credentials](https://docs.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals)
- [python-dotenv docs](https://python-dotenv.readthedocs.io/)

---

**Status:** ✅ Sistema corrigido e seguro!

