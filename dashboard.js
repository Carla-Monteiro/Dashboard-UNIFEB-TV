// ========================================
// LÓGICA DO DASHBOARD DE CHAMADOS
// ========================================

// Variáveis globais
let chamadosAtivos = [];
let chamadosConcluidos = [];
let chamadosAtivosFiltrados = [];
let tempoAtualizado = 0;

// ========================================
// FUNÇÕES DE INICIALIZAÇÃO
// ========================================

/**
 * Inicializar o dashboard
 */
async function inicializar() {
  console.log('🚀 Inicializando dashboard...');

  try {
    // Carregar dados
    await carregarDados();

    // Renderizar tabelas
    renderizarTabelas();

    // Atualizar tempo
    atualizarTempo();

    // Configurar auto-refresh
    setInterval(carregarDados, AUTO_REFRESH_INTERVAL);
    setInterval(atualizarTempo, 1000);

    console.log('✅ Dashboard inicializado com sucesso!');
  } catch (error) {
    console.error('❌ Erro ao inicializar:', error);
    mostraErro('Erro ao inicializar o dashboard. Tente recarregar a página.');
  }
}

/**
 * Carrega os dados da API
 */
async function carregarDados() {
  try {
    const dados = await carregarTodosDados();

    chamadosAtivos = dados.chamadosAtivos || [];
    chamadosConcluidos = dados.chamadosConcluidos || [];
    chamadosAtivosFiltrados = [...chamadosAtivos];

    // Atualizar stats
    atualizarStats(dados.estatisticas);

    // Re-renderizar se necessário
    if (document.getElementById('tabela-ativos').innerHTML.includes('Carregando')) {
      renderizarTabelas();
    }

    tempoAtualizado = 0;
  } catch (error) {
    console.error('❌ Erro ao carregar dados:', error);
  }
}

// ========================================
// FUNÇÕES DE RENDERIZAÇÃO
// ========================================

/**
 * Renderizar tabelas de chamados
 */
function renderizarTabelas() {
  renderizarTabelaAtivos();
  renderizarTabelaConcluidos();
  atualizarStats();
}

/**
 * Renderizar tabela de chamados ativos
 */
function renderizarTabelaAtivos() {
  const tbody = document.getElementById('tabela-ativos');

  if (chamadosAtivosFiltrados.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Nenhum chamado encontrado</td></tr>';
    return;
  }

  tbody.innerHTML = chamadosAtivosFiltrados.map(chamado => `
    <tr onclick="abrirDetalhes('${chamado.id}')">
      <td><strong>${chamado.id}</strong></td>
      <td>${chamado.titulo}</td>
      <td>${chamado.solicitante}</td>
      <td><span class="badge ${STATUS_CONFIG[chamado.status]?.class || 'badge-aberto'}">${chamado.status}</span></td>
      <td><span class="badge ${PRIORIDADE_CONFIG[chamado.prioridade]?.class || 'badge-media'}">${chamado.prioridade}</span></td>
      <td>${formatarData(chamado.data_criacao)}</td>
    </tr>
  `).join('');
}

/**
 * Renderizar tabela de chamados concluídos
 */
function renderizarTabelaConcluidos() {
  const tbody = document.getElementById('tabela-concluidos');

  if (chamadosConcluidos.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Nenhum chamado concluído ainda</td></tr>';
    return;
  }

  tbody.innerHTML = chamadosConcluidos.map(chamado => {
    try {
      const dataFormatada = chamado.data_conclusao ?
        (typeof chamado.data_conclusao === 'string' && chamado.data_conclusao.includes('/') ?
          chamado.data_conclusao :
          formatarData(chamado.data_conclusao)) :
        'N/A';

      return `
        <tr onclick="abrirDetalhes('${chamado.id}')">
          <td><strong>${chamado.id || 'N/A'}</strong></td>
          <td>${chamado.titulo || 'N/A'}</td>
          <td>${chamado.solicitante || 'N/A'}</td>
          <td>${chamado.categoria || 'Outra'}</td>
          <td>${dataFormatada}</td>
          <td>${chamado.avaliacao || '⭐⭐⭐⭐'}</td>
        </tr>
      `;
    } catch (error) {
      console.error('Erro ao renderizar chamado:', chamado, error);
      return `<tr><td colspan="6">Erro ao carregar chamado</td></tr>`;
    }
  }).join('');
}

/**
 * Atualizar cards de estatísticas
 */
function atualizarStats(stats = null) {
  if (!stats) {
    // Calcular stats dos dados carregados
    stats = {
      abertos: chamadosAtivos.filter(c => c.status === 'Aberto').length,
      andamento: chamadosAtivos.filter(c => c.status === 'Em Andamento').length,
      concluidos: chamadosConcluidos.length,
      vencidos: chamadosAtivos.filter(c => c.status === 'Vencido').length
    };
  }

  document.getElementById('stat-abertos').textContent = stats.abertos || 0;
  document.getElementById('stat-andamento').textContent = stats.andamento || 0;
  document.getElementById('stat-concluidos').textContent = stats.concluidos || 0;
  document.getElementById('stat-vencidos').textContent = stats.vencidos || 0;
  document.getElementById('alert-count').textContent = stats.vencidos || 0;
}

// ========================================
// FUNÇÕES DE INTERAÇÃO
// ========================================

/**
 * Abrir modal com detalhes do chamado
 */
function abrirDetalhes(id) {
  const chamado = chamadosAtivos.find(c => c.id === id);
  if (!chamado) return;

  document.getElementById('modal-id').textContent = chamado.id;
  document.getElementById('modal-titulo').textContent = chamado.titulo;
  document.getElementById('modal-subtitulo').textContent = chamado.id;
  document.getElementById('modal-titulo-campo').textContent = chamado.titulo;
  document.getElementById('modal-solicitante').textContent = chamado.solicitante || 'N/A';
  document.getElementById('modal-status').textContent = chamado.status;
  document.getElementById('modal-status').className = `badge ${STATUS_CONFIG[chamado.status]?.class || 'badge-aberto'}`;
  document.getElementById('modal-prioridade').textContent = chamado.prioridade;
  document.getElementById('modal-prioridade').className = `badge ${PRIORIDADE_CONFIG[chamado.prioridade]?.class || 'badge-media'}`;
  document.getElementById('modal-data-criacao').textContent = formatarData(chamado.data_criacao);
  document.getElementById('modal-prazo').textContent = formatarData(chamado.data_prazo);

  // Renderizar timeline
  const timeline = (chamado.historico || []).map(h => `
    <div class="timeline-item">
      <div class="timeline-dot"></div>
      <div>
        <div class="timeline-text">${h.acao}</div>
        <div class="timeline-time">${h.tempo}</div>
      </div>
    </div>
  `).join('');
  document.getElementById('modal-timeline').innerHTML = timeline || '<p class="timeline-text">Sem histórico disponível</p>';

  document.getElementById('modal').classList.add('active');
}

/**
 * Fechar modal
 */
function fecharModal() {
  document.getElementById('modal').classList.remove('active');
}

/**
 * Trocar entre abas
 */
function switchTab(index) {
  const tabs = document.querySelectorAll('.tab');
  const contents = document.querySelectorAll('.tab-content');

  tabs.forEach(t => t.classList.remove('active'));
  contents.forEach(c => c.classList.remove('active'));

  tabs[index].classList.add('active');
  contents[index].classList.add('active');

  // Re-renderizar tabelas para garantir que os dados apareçam
  renderizarTabelas();
}

/**
 * Selecionar categoria na sidebar
 */
function selectCategory(element) {
  document.querySelectorAll('.sidebar-item').forEach(item => {
    item.classList.remove('active');
  });
  element.classList.add('active');
}

/**
 * Sincronizar dados
 */
async function sincronizar() {
  console.log('🔄 Sincronizando dados...');
  const btn = event.target;
  btn.disabled = true;
  btn.textContent = '⏳ Sincronizando...';

  try {
    await carregarDados();
    renderizarTabelas();
    alert('✅ Dados sincronizados com sucesso!');
  } catch (error) {
    alert('❌ Erro ao sincronizar dados');
    console.error(error);
  } finally {
    btn.disabled = false;
    btn.textContent = '📡 Sincronizar';
  }
}

/**
 * Filtrar por status
 */
function filterByStatus(status) {
  document.getElementById('filter-status').value = status;
  aplicarFiltros();
  switchTab(0);
}

/**
 * Aplicar filtros na tabela
 */
function aplicarFiltros() {
  const status = document.getElementById('filter-status').value;
  const prioridade = document.getElementById('filter-prioridade').value;
  const busca = document.getElementById('filter-busca').value.toLowerCase();

  chamadosAtivosFiltrados = chamadosAtivos.filter(c => {
    const matchStatus = !status || c.status === status;
    const matchPrioridade = !prioridade || c.prioridade === prioridade;
    const matchBusca = !busca ||
      c.id.toLowerCase().includes(busca) ||
      c.titulo.toLowerCase().includes(busca) ||
      (c.solicitante || '').toLowerCase().includes(busca);

    return matchStatus && matchPrioridade && matchBusca;
  });

  renderizarTabelaAtivos();
}

// ========================================
// FUNÇÕES AUXILIARES
// ========================================

/**
 * Formatar data
 */
function formatarData(data) {
  if (!data) return 'N/A';
  try {
    const d = new Date(data);
    return d.toLocaleDateString('pt-BR');
  } catch {
    return data;
  }
}

/**
 * Atualizar contador de tempo
 */
function atualizarTempo() {
  tempoAtualizado++;
  if (tempoAtualizado > 60) tempoAtualizado = 1;
  document.getElementById('time-update').textContent = tempoAtualizado;
}

/**
 * Mostrar erro
 */
function mostraErro(mensagem) {
  const tbody = document.getElementById('tabela-ativos');
  tbody.innerHTML = `<tr><td colspan="6"><div class="error">❌ ${mensagem}</div></td></tr>`;
}

// ========================================
// EVENT LISTENERS
// ========================================

// Fechar modal ao clicar fora
document.addEventListener('click', function(event) {
  const modal = document.getElementById('modal');
  if (event.target === modal) {
    fecharModal();
  }
});

// ========================================
// INICIAR QUANDO PÁGINA CARREGAR
// ========================================

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', inicializar);
} else {
  inicializar();
}

console.log('✅ Dashboard.js carregado');
