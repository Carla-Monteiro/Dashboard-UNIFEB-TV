# ========================================
# NOVOS ENDPOINTS PARA O DASHBOARD
# ========================================
#
# Adicione estas funções ao seu form_handler.py
# Estas funções usam a estrutura já existente
# para retornar os dados no formato esperado pelo dashboard

@app.route('/api/chamados/ativos', methods=['GET', 'OPTIONS'])
@requer_login
def obter_chamados_ativos():
    """Retorna apenas chamados com status diferente de 'Concluído'"""
    try:
        token = get_access_token()
        if not token:
            return jsonify([]), 200

        headers = {'Authorization': f'Bearer {token}'}
        site_id, list_id = obter_site_e_lista(headers)
        if not site_id or not list_id:
            return jsonify([]), 200

        items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields"
        items_response = requests.get(items_url, headers=headers, timeout=10)

        if items_response.status_code != 200:
            return jsonify([]), 200

        items = items_response.json().get('value', [])
        setores_preenchidos = preencher_setores_faltantes(items, headers, site_id, list_id)

        chamados = []
        for item in items:
            fields = item.get('fields', {})
            status = fields.get('Status', 'Aberto')

            # Filtra apenas chamados NÃO concluídos
            if status.lower() == 'concluído':
                continue

            item_id = item.get('id')
            setor = fields.get('SetordeAtendimento', '') or setores_preenchidos.get(item_id, '')

            # Normalizar status para o dashboard
            status_normalizado = normalizar_status(status)
            prioridade_normalizada = normalizar_prioridade(fields.get('Prioridade', 'Média'))

            chamado = {
                'id': item_id,
                'titulo': fields.get('Title', ''),
                'solicitante': fields.get('Solicitante', ''),
                'email': fields.get('Email', ''),
                'status': status_normalizado,
                'prioridade': prioridade_normalizada,
                'categoria': fields.get('Categoria', 'Outra'),
                'data_criacao': formatar_data_iso(fields.get('DataAbertura', datetime.now().isoformat())),
                'data_prazo': formatar_data_iso(fields.get('DataAbertura', datetime.now().isoformat())),
                'descricao': fields.get('Descricao', ''),
                'setor': setor,
                'historico': parse_historico(fields.get('Historico'))
            }
            chamados.append(chamado)

        logger.info(f"✅ {len(chamados)} chamados ativos retornados para dashboard")
        return jsonify(chamados), 200

    except Exception as e:
        logger.error(f"ERRO em obter_chamados_ativos: {e}")
        return jsonify([]), 200


@app.route('/api/chamados/concluidos', methods=['GET', 'OPTIONS'])
@requer_login
def obter_chamados_concluidos():
    """Retorna apenas chamados com status 'Concluído'"""
    try:
        token = get_access_token()
        if not token:
            return jsonify([]), 200

        headers = {'Authorization': f'Bearer {token}'}
        site_id, list_id = obter_site_e_lista(headers)
        if not site_id or not list_id:
            return jsonify([]), 200

        items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields"
        items_response = requests.get(items_url, headers=headers, timeout=10)

        if items_response.status_code != 200:
            return jsonify([]), 200

        items = items_response.json().get('value', [])

        chamados = []
        for item in items:
            fields = item.get('fields', {})
            status = fields.get('Status', 'Aberto')

            # Filtra apenas chamados concluídos
            if status.lower() != 'concluído':
                continue

            item_id = item.get('id')

            chamado = {
                'id': item_id,
                'titulo': fields.get('Title', ''),
                'solicitante': fields.get('Solicitante', ''),
                'email': fields.get('Email', ''),
                'categoria': fields.get('Categoria', 'Outra'),
                'data_conclusao': formatar_data_iso(fields.get('Modified', datetime.now().isoformat())),
                'avaliacao': '⭐⭐⭐⭐'  # Você pode adicionar um campo de avaliação no SharePoint depois
            }
            chamados.append(chamado)

        logger.info(f"✅ {len(chamados)} chamados concluídos retornados para dashboard")
        return jsonify(chamados), 200

    except Exception as e:
        logger.error(f"ERRO em obter_chamados_concluidos: {e}")
        return jsonify([]), 200


@app.route('/api/chamados/stats', methods=['GET', 'OPTIONS'])
@requer_login
def obter_stats_chamados():
    """Retorna estatísticas de chamados (contagem por status)"""
    try:
        token = get_access_token()
        if not token:
            return jsonify({
                'abertos': 0,
                'andamento': 0,
                'concluidos': 0,
                'vencidos': 0
            }), 200

        headers = {'Authorization': f'Bearer {token}'}
        site_id, list_id = obter_site_e_lista(headers)
        if not site_id or not list_id:
            return jsonify({
                'abertos': 0,
                'andamento': 0,
                'concluidos': 0,
                'vencidos': 0
            }), 200

        items_url = f"{GRAPH_API}/sites/{site_id}/lists/{list_id}/items?$expand=fields"
        items_response = requests.get(items_url, headers=headers, timeout=10)

        if items_response.status_code != 200:
            return jsonify({
                'abertos': 0,
                'andamento': 0,
                'concluidos': 0,
                'vencidos': 0
            }), 200

        items = items_response.json().get('value', [])

        stats = {
            'abertos': 0,
            'andamento': 0,
            'concluidos': 0,
            'vencidos': 0
        }

        for item in items:
            fields = item.get('fields', {})
            status = fields.get('Status', 'Aberto').lower()
            prioridade = fields.get('Prioridade', 'Média')

            if status == 'concluído':
                stats['concluidos'] += 1
            elif status == 'em andamento':
                stats['andamento'] += 1
            elif status == 'aberto':
                stats['abertos'] += 1

            # Verificar se está vencido (SLA ultrapassado)
            # Você pode ajustar a lógica conforme suas regras de SLA
            if status != 'concluído' and prioridade == 'Crítica':
                # Exemplo simplificado - adapte conforme sua lógica de SLA
                stats['vencidos'] += 0  # Ajuste conforme necessário

        logger.info(f"✅ Stats: {stats}")
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"ERRO em obter_stats_chamados: {e}")
        return jsonify({
            'abertos': 0,
            'andamento': 0,
            'concluidos': 0,
            'vencidos': 0
        }), 200


# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def normalizar_status(status):
    """Converte status do SharePoint para formato do dashboard"""
    status_lower = status.lower() if status else ''

    mapa_status = {
        'aberto': 'Aberto',
        'em andamento': 'Em Andamento',
        'em processo': 'Em Andamento',
        'aguardando': 'Aguardando',
        'aguardando cliente': 'Aguardando',
        'concluído': 'Concluído',
        'concluido': 'Concluído',
        'resolvido': 'Concluído',
        'vencido': 'Vencido'
    }

    return mapa_status.get(status_lower, status or 'Aberto')


def normalizar_prioridade(prioridade):
    """Converte prioridade para formato padronizado"""
    prioridade_lower = prioridade.lower() if prioridade else ''

    mapa_prioridade = {
        'crítica': 'Crítica',
        'alta': 'Alta',
        'media': 'Média',
        'médica': 'Média',
        'normal': 'Média',
        'baixa': 'Baixa'
    }

    return mapa_prioridade.get(prioridade_lower, prioridade or 'Média')


def formatar_data_iso(data_str):
    """Converte data ISO para formato DD/MM/YYYY"""
    try:
        if not data_str:
            return datetime.now().strftime('%d/%m/%Y')

        # Se for ISO format
        if 'T' in data_str:
            dt = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
            # Converter para timezone de São Paulo
            tz_sp = ZoneInfo('America/Sao_Paulo')
            dt_sp = dt.astimezone(tz_sp)
            return dt_sp.strftime('%d/%m/%Y')

        return data_str
    except Exception as e:
        logger.error(f"Erro ao formatar data {data_str}: {e}")
        return datetime.now().strftime('%d/%m/%Y')
