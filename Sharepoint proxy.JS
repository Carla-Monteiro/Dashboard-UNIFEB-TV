const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
app.use(cors());
app.use(express.json());

const SHAREPOINT_SITE = 'https://unifeb.sharepoint.com/sites/SuporteDTI';
const SHAREPOINT_LIST = 'Chamados';

const cache = new Map();
const CACHE_DURATION = 5 * 60 * 1000;

app.get('/api/chamados', async (req, res) => {
    try {
        const numero = req.query.numero;
        if (!numero) {
            return res.status(400).json({ error: 'Número do chamado é obrigatório' });
        }

        const cacheKey = `chamado-${numero}`;
        const cached = cache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
            return res.json(cached.data);
        }

        const apiUrl = `${SHAREPOINT_SITE}/_api/web/lists/getbytitle('${SHAREPOINT_LIST}')/items?$filter=ID_Numero eq '${numero}' or Title eq '${numero}'&$top=1`;

        const response = await axios.get(apiUrl, {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            auth: {
                username: process.env.SHAREPOINT_USER,
                password: process.env.SHAREPOINT_PASSWORD
            }
        });

        if (response.data.value.length === 0) {
            return res.status(404).json({ error: 'Chamado não encontrado' });
        }

        const chamado = response.data.value[0];
        cache.set(cacheKey, { data: chamado, timestamp: Date.now() });
        res.json(chamado);

    } catch (erro) {
        console.error('Erro:', erro.message);
        res.status(500).json({ error: 'Erro ao buscar dados', details: erro.message });
    }
});

app.get('/health', (req, res) => {
    res.json({ status: 'OK', timestamp: new Date() });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`✅ Proxy SharePoint na porta ${PORT}`);
});