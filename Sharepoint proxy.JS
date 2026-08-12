const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
app.use(cors());
app.use(express.json());

// Configurações do SharePoint
const SHAREPOINT_SITE = 'https://unifeb.sharepoint.com/sites/SuporteDTI';
const SHAREPOINT_LIST = 'Chamados';

// Variáveis de ambiente (OAuth do Azure)
const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_SECRET = process.env.CLIENT_SECRET;
const TENANT_ID = process.env.TENANT_ID;

// Cache simples
const cache = new Map();
const CACHE_DURATION = 5 * 60 * 1000;
let accessToken = null;
let tokenExpiry = null;

// Obter token de acesso
async function getAccessToken() {
    // Se o token ainda é válido, retornar
    if (accessToken && tokenExpiry && Date.now() < tokenExpiry) {
        return accessToken;
    }

    try {
        const tokenUrl = `https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token`;

        const response = await axios.post(tokenUrl,
            `client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}&scope=https://graph.microsoft.com/.default&grant_type=client_credentials`,
            {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            }
        );

        accessToken = response.data.access_token;
        // Definir expiração 5 minutos antes
        tokenExpiry = Date.now() + (response.data.expires_in * 1000) - (5 * 60 * 1000);

        console.log('✅ Token de acesso obtido com sucesso');
        return accessToken;

    } catch (erro) {
        console.error('❌ Erro ao obter token:', erro.message);
        throw new Error('Falha ao autenticar com Azure AD');
    }
}

app.get('/api/chamados', async (req, res) => {
    try {
        const numero = req.query.numero;

        if (!numero) {
            return res.status(400).json({ error: 'Número do chamado é obrigatório' });
        }

        // Verificar cache
        const cacheKey = `chamado-${numero}`;
        const cached = cache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
            console.log(`📦 Retornando do cache: ${numero}`);
            return res.json(cached.data);
        }

        // Obter token de acesso
        const token = await getAccessToken();

        // Buscar do SharePoint via Microsoft Graph
        const graphUrl = `https://graph.microsoft.com/v1.0/sites/unifeb.sharepoint.com:/sites/SuporteDTI:/lists/Chamados/items`;

        console.log(`🔍 Buscando chamado: ${numero}`);

        const response = await axios.get(graphUrl, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json'
            },
            params: {
                $filter: `fields/ID_Numero eq '${numero}' or fields/Title eq '${numero}'`,
                $top: 1
            }
        });

        if (!response.data.value || response.data.value.length === 0) {
            // Tentar busca alternativa
            const response2 = await axios.get(`${graphUrl}?$search="${numero}"&$top=5`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/json'
                }
            });

            if (!response2.data.value || response2.data.value.length === 0) {
                return res.status(404).json({ error: `Chamado ${numero} não encontrado` });
            }

            const chamado = response2.data.value[0];
            cache.set(cacheKey, { data: chamado, timestamp: Date.now() });
            return res.json(chamado);
        }

        const chamado = response.data.value[0];

        // Armazenar em cache
        cache.set(cacheKey, {
            data: chamado,
            timestamp: Date.now()
        });

        res.json(chamado);

    } catch (erro) {
        console.error('Erro ao buscar do SharePoint:', erro.message);
        res.status(500).json({
            error: 'Erro ao buscar dados',
            details: erro.message
        });
    }
});

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'OK',
        timestamp: new Date(),
        authenticated: !!accessToken
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`✅ Proxy SharePoint rodando na porta ${PORT}`);
    console.log(`📍 Site: ${SHAREPOINT_SITE}`);
    console.log(`📊 Lista: ${SHAREPOINT_LIST}`);
});