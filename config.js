// ========================================
// CONFIGURAÇÃO DO DASHBOARD DE CHAMADOS
// ========================================

// URL DA API - ALTERE PARA SUA URL REAL
const API_BASE_URL = 'http://localhost:5000/api'; // Altere conforme sua API

// Endpoints disponíveis
const ENDPOINTS = {
  chamadosAtivos: `${API_BASE_URL}/chamados/ativos`,
  chamadosConcluidos: `${API_BASE_URL}/chamados/concluidos`,
  estatisticas: `${API_BASE_URL}/chamados/stats`,
  detalhe: (id) => `${API_BASE_URL}/chamados/${id}`,
  criar: `${API_BASE_URL}/chamados/criar`,
  atualizar: (id) => `${API_BASE_URL}/chamados/${id}/atualizar`
};

// ========================================
// FUNÇÕES DE REQUISIÇÃO À API
// ========================================

/**
 * Buscar chamados ativos da API
 */
async function buscarChamadosAtivos() {
  try {
    console.log('🔄 Buscando chamados ativos...');
    const response = await fetch(ENDPOINTS.chamadosAtivos);

    if (!response.ok) {
      throw new Error(`Erro ${response.status}: ${response.statusText}`);
    }

    const dados = await response.json();
    console.log('✅ Chamados ativos carregados:', dados.length);
    return dados;
  } catch (error) {
    console.error('❌ Erro ao buscar chamados ativos:', error);
    return [];
  }
}

/**
 * Buscar chamados concluídos da API
 */
async function buscarChamadosConcluidos() {
  try {
    console.log('🔄 Buscando chamados concluídos...');
    const response = await fetch(ENDPOINTS.chamadosConcluidos);

    if (!response.ok) {
      throw new Error(`Erro ${response.status}: ${response.statusText}`);
    }

    const dados = await response.json();
    console.log('✅ Chamados concluídos carregados:', dados.length);
    return dados;
  } catch (error) {
    console.error('❌ Erro ao buscar chamados concluídos:', error);
    return [];
  }
}

/**
 * Buscar estatísticas dos chamados
 */
async function buscarEstatisticas() {
  try {
    console.log('🔄 Buscando estatísticas...');
    const response = await fetch(ENDPOINTS.estatisticas);

    if (!response.ok) {
      throw new Error(`Erro ${response.status}: ${response.statusText}`);
    }

    const dados = await response.json();
    console.log('✅ Estatísticas carregadas:', dados);
    return dados;
  } catch (error) {
    console.error('❌ Erro ao buscar estatísticas:', error);
    return {
      abertos: 0,
      andamento: 0,
      concluidos: 0,
      vencidos: 0
    };
  }
}

/**
 * Carregar todos os dados do dashboard
 */
async function carregarTodosDados() {
  try {
    const [ativos, concluidos, stats] = await Promise.all([
      buscarChamadosAtivos(),
      buscarChamadosConcluidos(),
      buscarEstatisticas()
    ]);

    return {
      chamadosAtivos: ativos,
      chamadosConcluidos: concluidos,
      estatisticas: stats
    };
  } catch (error) {
    console.error('❌ Erro ao carregar todos os dados:', error);
    return {
      chamadosAtivos: [],
      chamadosConcluidos: [],
      estatisticas: { abertos: 0, andamento: 0, concluidos: 0, vencidos: 0 }
    };
  }
}

// ========================================
// CONFIGURAÇÃO DE SINCRONIZAÇÃO
// ========================================

// Intervalo de atualização automática (em ms)
const AUTO_REFRESH_INTERVAL = 30000; // 30 segundos

// Mapeamento de status para cores e ícones
const STATUS_CONFIG = {
  'Aberto': { icon: '📂', class: 'badge-aberto', cor: '#ffa500' },
  'Em Andamento': { icon: '⏳', class: 'badge-andamento', cor: '#60a5fa' },
  'Aguardando': { icon: '⏸️', class: 'badge-andamento', cor: '#60a5fa' },
  'Concluído': { icon: '✅', class: 'badge-concluido', cor: '#10b981' },
  'Vencido': { icon: '🚨', class: 'badge-vencido', cor: '#ef5350' }
};

// Mapeamento de prioridades
const PRIORIDADE_CONFIG = {
  'Crítica': { class: 'badge-alta', cor: '#ef5350' },
  'Alta': { class: 'badge-alta', cor: '#ef5350' },
  'Média': { class: 'badge-media', cor: '#ffa500' },
  'Baixa': { class: 'badge-baixa', cor: '#10b981' }
};

// ========================================
// EXEMPLO DE RESPOSTA DA API ESPERADA
// ========================================

/**
 * Formato esperado dos dados de chamados ativos:
 *
 * [
 *   {
 *     "id": "#001",
 *     "titulo": "Título do chamado",
 *     "solicitante": "Nome do solicitante",
 *     "email": "email@dominio.com",
 *     "status": "Aberto",
 *     "prioridade": "Alta",
 *     "categoria": "TI",
 *     "data_criacao": "2024-09-28",
 *     "data_prazo": "2024-09-30",
 *     "descricao": "Descrição detalhada do chamado",
 *     "historico": [
 *       { "acao": "Ticket criado", "tempo": "2 horas atrás" },
 *       { "acao": "Atribuído ao técnico", "tempo": "1 hora atrás" }
 *     ]
 *   }
 * ]
 */

/**
 * Formato esperado das estatísticas:
 *
 * {
 *   "abertos": 12,
 *   "andamento": 1,
 *   "concluidos": 28,
 *   "vencidos": 13
 * }
 */

console.log('✅ Config.js carregado - API:', API_BASE_URL);
