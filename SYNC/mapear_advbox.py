"""
=============================================================================
  MAPA COMPLETO DO ADVBOX - ALVES CARNEIRO ADVOCACIA E CONSULTORIA JURIDICA
=============================================================================

  Extrai TUDO o que a API do ADVBOX entrega - clientes, processos, financeiro,
  tarefas, movimentacoes e dados de referencia - e grava em JSON, CSV e um
  relatorio legivel. Serve de inventario da migracao para o Infinitum e de
  copia de seguranca do que existe hoje no ADVBOX.

  SOMENTE LEITURA. Nenhuma funcao daqui escreve no ADVBOX.

  Uso:
    python SYNC/mapear_advbox.py                 # etapas essenciais
    python SYNC/mapear_advbox.py --completo      # + historico/andamento por processo
    python SYNC/mapear_advbox.py --so-relatorio  # regera CSV/MD do cache, sem rede
    python SYNC/mapear_advbox.py --limpar-cache  # descarta o cache e recomeca

  POR QUE E DEMORADO (e resumivel)
  O ADVBOX limita GET a 30/min, entao ha pausa de 2,1s entre chamadas; cada
  GET /posts leva ~60s. Detalhar 309 clientes custa ~11 min; o historico por
  processo (3 chamadas x 216 processos) passa de 20 min. Por isso cada etapa
  grava cache em mapa_advbox/cache/ e, ao rodar de novo, so busca o que falta -
  pode ser interrompido sem perder trabalho.

  ARMADILHAS JA CONHECIDAS (nao "consertar" sem ler)
  - GET /customers e INCOMPLETO: omite ~100 clientes reais e mistura parte
    contraria. A lista verdadeira de clientes sai da UNIAO entre /customers e
    os customers[] de cada processo.
  - Com filtro, o totalCount de /posts vem MAIOR que o conjunto filtrado
    (8 registros com totalCount=9), entao a paginacao para em pagina curta.
  - /movements usa DD/MM/YYYY; o resto da API usa YYYY-MM-DD.

  Saidas em SYNC/mapa_advbox/ (nao versionado - dado pessoal de cliente):
    mapa.json          tudo junto
    MAPA.md            relatorio legivel
    clientes.csv  processos.csv  transacoes.csv  tarefas.csv
    cache/             caches por etapa (resumivel)
=============================================================================
"""
import os
import sys
import io
import csv
import json
import time
import argparse
from datetime import datetime
from collections import Counter, defaultdict

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(RAIZ, 'INTEGRACOES'))

from dotenv import load_dotenv
load_dotenv(os.path.join(RAIZ, 'config', '.env'))

from advbox_integration import _request, listar_transacoes, listar_tarefas

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mapa_advbox')
CACHE = os.path.join(PASTA, 'cache')

PAUSA = 2.1          # limite do ADVBOX: 30 GET/min
LIMITE_PAGINA = 100


# ============================================================
# INFRA
# ============================================================

def _ler(nome, padrao=None):
    caminho = os.path.join(CACHE, nome)
    if not os.path.exists(caminho):
        return padrao
    try:
        with io.open(caminho, encoding='utf-8') as f:
            return json.load(f)
    except (ValueError, OSError):
        return padrao


def _gravar(nome, dados, pasta=None):
    destino = pasta or CACHE
    os.makedirs(destino, exist_ok=True)
    caminho = os.path.join(destino, nome)
    tmp = caminho + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dados, f, ensure_ascii=False, indent=1, default=str)
    os.replace(tmp, caminho)
    return caminho


def _paginar(endpoint, params=None, rotulo=''):
    """Paginacao segura: para em pagina curta, sem confiar no totalCount."""
    todos = []
    offset = 0
    while True:
        p = dict(params or {})
        p.update({'limit': LIMITE_PAGINA, 'offset': offset})
        data = _request('GET', endpoint, params=p) or {}
        registros = data.get('data', []) or []
        todos.extend(registros)
        total = data.get('totalCount', 0)
        if rotulo:
            print('    %s: %d (totalCount=%s)' % (rotulo, len(todos), total))
        if len(registros) < LIMITE_PAGINA or not registros or len(todos) >= total:
            return todos
        offset += LIMITE_PAGINA
        time.sleep(PAUSA)


def _get(endpoint):
    """GET unitario, tolerante a falha - devolve (dados, erro)."""
    try:
        return _request('GET', endpoint), None
    except Exception as e:
        return None, '%s: %s' % (type(e).__name__, e)


# ============================================================
# ETAPAS
# ============================================================

def etapa_settings():
    cache = _ler('settings.json')
    if cache:
        print('  Settings: do cache')
        return cache
    print('  Settings (dados de referencia)...')
    d = _request('GET', '/settings') or {}
    fin = d.get('financial') or {}
    if isinstance(fin, dict):
        for k in ('banks', 'categories', 'cost_centers', 'departments'):
            d.setdefault(k, fin.get(k, []))
    _gravar('settings.json', d)
    return d


def etapa_processos():
    cache = _ler('processos.json')
    if cache:
        print('  Processos: %d do cache' % len(cache))
        return cache
    print('  Processos...')
    lista = _paginar('/lawsuits', rotulo='processos')
    d = {str(p['id']): p for p in lista}
    _gravar('processos.json', d)
    return d


def etapa_transacoes():
    cache = _ler('transacoes.json')
    if cache:
        print('  Transacoes: %d do cache' % len(cache))
        return cache
    print('  Financeiro...')
    d = {str(t['id']): t for t in listar_transacoes()}
    _gravar('transacoes.json', d)
    return d


def etapa_clientes(processos):
    """Uniao de /customers com os customers[] dos processos, e detalhe de cada um.
    Resumivel: grava o cache a cada 10 clientes detalhados."""
    detalhes = _ler('clientes.json', {}) or {}
    rasos = {}

    for p in processos.values():
        for c in p.get('customers') or []:
            cid = str(c.get('customer_id'))
            if cid and cid != 'None':
                rasos[cid] = {'customer_id': c.get('customer_id'), 'name': c.get('name'),
                              'identification': c.get('identification'),
                              '_veio_de': 'processo'}
    try:
        for c in _paginar('/customers', rotulo='clientes (listagem)'):
            cid = str(c['id'])
            if cid in rasos:
                rasos[cid]['_veio_de'] = 'ambos'
            else:
                rasos[cid] = {'customer_id': c['id'], 'name': c.get('name'),
                              'identification': c.get('identification'),
                              '_veio_de': 'listagem'}
    except Exception as e:
        print('    AVISO: listagem /customers falhou (%s); segue com os dos processos' % e)

    faltam = [cid for cid in rasos if cid not in detalhes]
    print('  Clientes: %d no total, %d ja detalhados, %d a buscar (~%d min)'
          % (len(rasos), len(detalhes), len(faltam), round(len(faltam) * PAUSA / 60)))

    erros = _ler('clientes_erros.json', {}) or {}
    for i, cid in enumerate(faltam, 1):
        time.sleep(PAUSA)
        d, erro = _get('/customers/%s' % cid)
        if d:
            d['_veio_de'] = rasos[cid].get('_veio_de')
            detalhes[cid] = d
            erros.pop(cid, None)
        else:
            erros[cid] = erro
            detalhes[cid] = dict(rasos[cid], _detalhe_falhou=erro)
        if i % 10 == 0 or i == len(faltam):
            _gravar('clientes.json', detalhes)
            _gravar('clientes_erros.json', erros)
            print('    %d/%d' % (i, len(faltam)))

    _gravar('clientes.json', detalhes)
    _gravar('clientes_erros.json', erros)
    return detalhes, rasos


def etapa_tarefas():
    cache = _ler('tarefas.json')
    if cache is not None:
        print('  Tarefas: %d do cache' % len(cache))
        return cache
    print('  Tarefas (/posts - ~60s por pagina, tenha paciencia)...')
    try:
        lista = listar_tarefas()
    except Exception as e:
        print('    AVISO: /posts falhou (%s)' % e)
        lista = []
    _gravar('tarefas.json', lista)
    return lista


def etapa_movimentacoes():
    cache = _ler('movimentacoes.json')
    if cache is not None:
        print('  Movimentacoes: %d do cache' % len(cache))
        return cache
    print('  Ultimas movimentacoes...')
    try:
        lista = _paginar('/last_movements', rotulo='movimentacoes')
    except Exception as e:
        print('    AVISO: /last_movements falhou (%s)' % e)
        lista = []
    _gravar('movimentacoes.json', lista)
    return lista


def etapa_aniversariantes():
    cache = _ler('aniversariantes.json')
    if cache is not None:
        return cache
    d, erro = _get('/customers/birthdays')
    lista = (d or {}).get('data', []) if not erro else []
    _gravar('aniversariantes.json', lista)
    return lista


def etapa_detalhe_processos(processos):
    """Por processo: andamentos (/movements) e historico de tarefas (/history).
    3 chamadas por processo - o que torna esta etapa a mais longa."""
    det = _ler('detalhe_processos.json', {}) or {}
    faltam = [pid for pid in processos if pid not in det]
    print('  Detalhe por processo: %d ja feitos, %d a buscar (~%d min)'
          % (len(det), len(faltam), round(len(faltam) * 2 * PAUSA / 60)))

    for i, pid in enumerate(faltam, 1):
        registro = {}
        time.sleep(PAUSA)
        d, erro = _get('/movements/%s' % pid)
        registro['andamentos'] = (d or {}).get('data', []) if not erro else []
        if erro:
            registro['andamentos_erro'] = erro
        time.sleep(PAUSA)
        d, erro = _get('/history/%s' % pid)
        registro['historico_tarefas'] = (d or {}).get('data', []) if not erro else []
        if erro:
            registro['historico_erro'] = erro
        det[pid] = registro
        if i % 10 == 0 or i == len(faltam):
            _gravar('detalhe_processos.json', det)
            print('    %d/%d' % (i, len(faltam)))

    _gravar('detalhe_processos.json', det)
    return det


# ============================================================
# CSV
# ============================================================

def _csv(nome, cabecalho, linhas):
    caminho = os.path.join(PASTA, nome)
    with io.open(caminho, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(cabecalho)
        w.writerows(linhas)
    print('    %s (%d linhas)' % (nome, len(linhas)))


def _txt(v):
    if v is None:
        return ''
    return str(v).replace('\r', ' ').replace('\n', ' | ').strip()


def gerar_csvs(clientes, processos, transacoes, tarefas):
    print('  Gerando CSVs...')

    _csv('clientes.csv',
         ['id', 'nome', 'cpf_cnpj', 'rg', 'nascimento', 'sexo', 'estado_civil',
          'profissao', 'email', 'telefone', 'celular', 'rua', 'bairro', 'cidade',
          'uf', 'cep', 'origem', 'anotacoes', 'fonte', 'detalhe_falhou'],
         [[cid, _txt(c.get('name')), _txt(c.get('identification')), _txt(c.get('document')),
           _txt(c.get('birthdate')), _txt(c.get('gender')), _txt(c.get('civil_status')),
           _txt(c.get('occupation')), _txt(c.get('email')), _txt(c.get('phone')),
           _txt(c.get('cellphone')), _txt(c.get('street')), _txt(c.get('region')),
           _txt(c.get('city')), _txt(c.get('state')), _txt(c.get('postalcode')),
           _txt(c.get('origin')), _txt(c.get('notes') or c.get('note')),
           _txt(c.get('_veio_de')), _txt(c.get('_detalhe_falhou'))]
          for cid, c in sorted(clientes.items(), key=lambda kv: _txt(kv[1].get('name')))])

    _csv('processos.csv',
         ['id', 'numero_processo', 'protocolo', 'pasta', 'grupo', 'tipo', 'fase',
          'etapa', 'responsavel', 'data_processo', 'encerrado_em', 'honorarios_esperados',
          'honorarios_recebidos', 'contingencia', 'clientes', 'anotacoes'],
         [[pid, _txt(p.get('process_number')), _txt(p.get('protocol_number')),
           _txt(p.get('folder')), _txt(p.get('group')), _txt(p.get('type')),
           _txt(p.get('stage')), _txt(p.get('step')), _txt(p.get('responsible')),
           _txt(p.get('process_date')), _txt(p.get('status_closure')),
           _txt(p.get('fees_expec')), _txt(p.get('fees_money')), _txt(p.get('contingency')),
           _txt(', '.join(c.get('name', '') for c in (p.get('customers') or []))),
           _txt(p.get('notes'))]
          for pid, p in sorted(processos.items(), key=lambda kv: _txt(kv[1].get('group')))])

    _csv('transacoes.csv',
         ['id', 'tipo', 'valor', 'vencimento', 'pagamento', 'competencia', 'categoria',
          'descricao', 'cliente', 'cpf_cnpj', 'processo', 'responsavel',
          'banco_debito', 'banco_credito', 'centro_custo', 'interna', 'recorrente'],
         [[tid, _txt(t.get('entry_type')), _txt(t.get('amount')), _txt(t.get('date_due')),
           _txt(t.get('date_payment')), _txt(t.get('competence')), _txt(t.get('category')),
           _txt(t.get('description')), _txt(t.get('name')), _txt(t.get('identification')),
           _txt(t.get('process_number')), _txt(t.get('responsible')),
           _txt(t.get('debit_bank')), _txt(t.get('credit_bank')),
           _txt(t.get('cost_center')), _txt(t.get('is_internal')),
           _txt(t.get('is_recurrent'))]
          for tid, t in sorted(transacoes.items(), key=lambda kv: _txt(kv[1].get('date_due')))])

    linhas = []
    for t in tarefas:
        proc = t.get('lawsuit') or {}
        pend = [u for u in (t.get('users') or []) if not u.get('completed')]
        linhas.append([
            t.get('id'), _txt(t.get('task')), _txt(t.get('date')),
            _txt(t.get('date_deadline')),
            'pendente' if pend else 'concluida',
            _txt(', '.join(u.get('name', '') for u in (t.get('users') or []))),
            _txt(proc.get('process_number')),
            _txt(', '.join(c.get('name', '') for c in (proc.get('customers') or []))),
            _txt(t.get('notes')), _txt(t.get('created_at'))])
    _csv('tarefas.csv',
         ['id', 'tipo', 'data', 'prazo', 'situacao', 'destinatarios', 'processo',
          'clientes', 'anotacoes', 'criada_em'], linhas)


# ============================================================
# RELATORIO
# ============================================================

def _f(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _brl(v):
    # pt-BR: milhar com ponto, decimal com virgula. Formata em en-US e troca os
    # separadores; sem isso o valor sai "R$ 283509,39", ilegivel num relatorio.
    return 'R$ ' + ('{:,.2f}'.format(v).replace(',', '#').replace('.', ',').replace('#', '.'))


def _tabela(L, titulo, contador, rotulo_col, limite=None):
    itens = contador.most_common(limite)
    if not itens:
        return
    L.append('### %s' % titulo)
    L.append('')
    L.append('| %s | Qtd |' % rotulo_col)
    L.append('|---|---:|')
    for nome, n in itens:
        L.append('| %s | %d |' % (nome or '(vazio)', n))
    L.append('')


def gerar_relatorio(settings, clientes, rasos, processos, transacoes, tarefas,
                    movimentacoes, detalhe, aniversariantes):
    L = []
    L.append('# Mapa do ADVBOX — Alves Carneiro Advocacia e Consultoria Jurídica')
    L.append('')
    L.append('Extraído em %s pela API do ADVBOX (somente leitura).'
             % datetime.now().strftime('%d/%m/%Y às %H:%M'))
    L.append('')

    # ---- panorama ----
    ativos = [p for p in processos.values() if not p.get('status_closure')]
    receitas = [t for t in transacoes.values() if t.get('entry_type') == 'income']
    despesas = [t for t in transacoes.values() if t.get('entry_type') == 'expense']
    pendentes = [t for t in tarefas
                 if any(not u.get('completed') for u in (t.get('users') or []))]
    com_detalhe = sum(1 for c in clientes.values() if not c.get('_detalhe_falhou'))

    L.append('## Panorama')
    L.append('')
    L.append('| | |')
    L.append('|---|---:|')
    L.append('| Clientes (e partes) | %d |' % len(clientes))
    L.append('| &nbsp;&nbsp;com cadastro completo lido | %d |' % com_detalhe)
    L.append('| Processos | %d |' % len(processos))
    L.append('| &nbsp;&nbsp;ativos (sem encerramento) | %d |' % len(ativos))
    L.append('| &nbsp;&nbsp;encerrados | %d |' % (len(processos) - len(ativos)))
    L.append('| Lançamentos financeiros | %d |' % len(transacoes))
    L.append('| &nbsp;&nbsp;receitas | %d |' % len(receitas))
    L.append('| &nbsp;&nbsp;despesas | %d |' % len(despesas))
    L.append('| Tarefas | %d |' % len(tarefas))
    L.append('| &nbsp;&nbsp;pendentes | %d |' % len(pendentes))
    L.append('| Movimentações (últimas) | %d |' % len(movimentacoes))
    if detalhe:
        and_tot = sum(len(d.get('andamentos') or []) for d in detalhe.values())
        hist_tot = sum(len(d.get('historico_tarefas') or []) for d in detalhe.values())
        L.append('| Andamentos por processo | %d |' % and_tot)
        L.append('| Histórico de tarefas | %d |' % hist_tot)
    L.append('')

    # ---- origem dos clientes (a pegadinha do /customers) ----
    fontes = Counter(c.get('_veio_de') or '?' for c in clientes.values())
    L.append('## De onde vieram os clientes')
    L.append('')
    L.append('A listagem `GET /customers` do ADVBOX é incompleta e mistura parte '
             'contrária. A lista real é a união dela com os clientes citados em cada '
             'processo — e a diferença abaixo mostra o tamanho do problema.')
    L.append('')
    L.append('| Fonte | Qtd |')
    L.append('|---|---:|')
    L.append('| Só na listagem `/customers` | %d |' % fontes.get('listagem', 0))
    L.append('| Só nos processos | %d |' % fontes.get('processo', 0))
    L.append('| Nas duas | %d |' % fontes.get('ambos', 0))
    L.append('')
    so_proc = fontes.get('processo', 0)
    if so_proc:
        L.append('> **%d registros não apareciam na listagem de clientes** e só foram '
                 'achados pelos processos. Quem migrar confiando só em `/customers` '
                 'perde esses.' % so_proc)
        L.append('')

    # ---- financeiro ----
    L.append('## Financeiro')
    L.append('')
    tot_r = sum(_f(t.get('amount')) for t in receitas)
    tot_d = sum(_f(t.get('amount')) for t in despesas)
    pagos_r = sum(_f(t.get('amount')) for t in receitas if t.get('date_payment'))
    aberto_r = tot_r - pagos_r
    L.append('| | Valor |')
    L.append('|---|---:|')
    L.append('| Receitas lançadas | %s |' % _brl(tot_r))
    L.append('| &nbsp;&nbsp;já recebidas | %s |' % _brl(pagos_r))
    L.append('| &nbsp;&nbsp;**a receber** | **%s** |' % _brl(aberto_r))
    L.append('| Despesas lançadas | %s |' % _brl(tot_d))
    L.append('| Resultado (receitas - despesas) | %s |' % _brl(tot_r - tot_d))
    L.append('')
    L.append('> Valores **nominais**, pelo que está lançado no ADVBOX. Receita sem '
             '`date_payment` conta como a receber.')
    L.append('')

    porcomp = defaultdict(lambda: [0.0, 0.0])
    for t in transacoes.values():
        comp = t.get('competence') or (t.get('date_due') or '')[:7]
        i = 0 if t.get('entry_type') == 'income' else 1
        porcomp[comp][i] += _f(t.get('amount'))
    if porcomp:
        L.append('### Por competência')
        L.append('')
        L.append('| Competência | Receitas | Despesas | Saldo |')
        L.append('|---|---:|---:|---:|')
        for comp in sorted(porcomp, reverse=True)[:18]:
            r, d = porcomp[comp]
            L.append('| %s | %s | %s | %s |' % (comp or '(vazia)', _brl(r), _brl(d), _brl(r - d)))
        L.append('')

    _tabela(L, 'Categorias de receita', Counter(
        _txt(t.get('category')) for t in receitas), 'Categoria', 15)
    _tabela(L, 'Categorias de despesa', Counter(
        _txt(t.get('category')) for t in despesas), 'Categoria', 15)

    # ---- acervo ----
    L.append('## Acervo de processos')
    L.append('')
    _tabela(L, 'Por área (grupo)', Counter(_txt(p.get('group')) for p in processos.values()), 'Grupo')
    _tabela(L, 'Por tipo', Counter(_txt(p.get('type')) for p in processos.values()), 'Tipo', 25)
    _tabela(L, 'Por etapa', Counter(_txt(p.get('step')) for p in ativos), 'Etapa (ativos)')
    _tabela(L, 'Por fase', Counter(_txt(p.get('stage')) for p in ativos), 'Fase (ativos)', 25)
    _tabela(L, 'Por responsável', Counter(_txt(p.get('responsible')) for p in processos.values()), 'Responsável')

    honor = sum(_f(p.get('fees_expec')) for p in processos.values())
    receb = sum(_f(p.get('fees_money')) for p in processos.values())
    conting = sum(_f(p.get('contingency')) for p in processos.values())
    L.append('### Honorários registrados nos processos')
    L.append('')
    L.append('| | Valor |')
    L.append('|---|---:|')
    L.append('| Honorários esperados (`fees_expec`) | %s |' % _brl(honor))
    L.append('| Honorários recebidos (`fees_money`) | %s |' % _brl(receb))
    L.append('| Contingência | %s |' % _brl(conting))
    L.append('')
    L.append('> Estes campos são do cadastro do processo e **não** se somam às '
             'transações do financeiro — são controles distintos no ADVBOX.')
    L.append('')

    sem_numero = [p for p in ativos if not p.get('process_number')]
    L.append('### Qualidade do cadastro')
    L.append('')
    L.append('| Situação | Qtd |')
    L.append('|---|---:|')
    L.append('| Processos ativos sem número | %d |' % len(sem_numero))
    L.append('| Processos sem cliente vinculado | %d |'
             % sum(1 for p in processos.values() if not (p.get('customers') or [])))
    L.append('| Clientes sem CPF/CNPJ | %d |'
             % sum(1 for c in clientes.values() if not c.get('identification')))
    L.append('| Clientes sem telefone e sem e-mail | %d |'
             % sum(1 for c in clientes.values()
                   if not (c.get('cellphone') or c.get('phone') or c.get('email'))))
    L.append('')

    # ---- tarefas ----
    if tarefas:
        L.append('## Tarefas')
        L.append('')
        _tabela(L, 'Tipos mais usados', Counter(_txt(t.get('task')) for t in tarefas), 'Tipo', 20)
        resp = Counter()
        for t in pendentes:
            for u in (t.get('users') or []):
                if not u.get('completed'):
                    resp[_txt(u.get('name'))] += 1
        _tabela(L, 'Pendentes por responsável', resp, 'Responsável')
        com_prazo = [t for t in pendentes if t.get('date_deadline')]
        L.append('Das %d tarefas pendentes, **%d têm prazo** e %d não têm data nenhuma.'
                 % (len(pendentes), len(com_prazo), len(pendentes) - len(com_prazo)))
        L.append('')

    # ---- referencia ----
    L.append('## Dados de referência (`/settings`)')
    L.append('')
    L.append('| Tabela | Itens |')
    L.append('|---|---:|')
    for chave, rotulo in (('users', 'Usuários'), ('origins', 'Origens de cliente'),
                          ('tasks', 'Tipos de tarefa'), ('stages', 'Fases'),
                          ('lawsuit_types', 'Tipos de processo'), ('banks', 'Contas bancárias'),
                          ('categories', 'Categorias financeiras'),
                          ('cost_centers', 'Centros de custo'), ('departments', 'Departamentos')):
        v = settings.get(chave)
        if isinstance(v, list):
            L.append('| %s | %d |' % (rotulo, len(v)))
    L.append('')
    for u in settings.get('users') or []:
        L.append('- **%s** (ID %s) — %s' % (u.get('name'), u.get('id'), _txt(u.get('email'))))
    L.append('')

    if aniversariantes:
        L.append('## Aniversariantes do mês')
        L.append('')
        for a in aniversariantes:
            L.append('- %s — %s' % (_txt(a.get('name')), _txt(a.get('birthdate'))))
        L.append('')

    # ---- falhas ----
    erros = _ler('clientes_erros.json', {}) or {}
    if erros:
        L.append('## Cadastros que não foram lidos')
        L.append('')
        L.append('%d cliente(s) recusaram o detalhamento; o CSV traz só nome e CPF '
                 'deles, com a falha na coluna `detalhe_falhou`.' % len(erros))
        L.append('')

    L.append('---')
    L.append('')
    L.append('Arquivos desta extração: `mapa.json` (tudo), `clientes.csv`, '
             '`processos.csv`, `transacoes.csv`, `tarefas.csv`. Os CSV abrem no Excel '
             '(separador `;`, UTF-8 com BOM).')
    L.append('')
    L.append('**Contém dado pessoal de cliente** — a pasta não é versionada no git.')

    caminho = os.path.join(PASTA, 'MAPA.md')
    with io.open(caminho, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    print('    MAPA.md')
    return caminho


# ============================================================
# MAIN
# ============================================================

def main():
    ap = argparse.ArgumentParser(description='Mapa completo do ADVBOX (somente leitura)')
    ap.add_argument('--completo', action='store_true',
                    help='inclui andamento e historico de tarefas de cada processo (lento)')
    ap.add_argument('--so-relatorio', action='store_true',
                    help='regera CSV e MAPA.md a partir do cache, sem acessar a rede')
    ap.add_argument('--limpar-cache', action='store_true', help='descarta o cache e recomeca')
    args = ap.parse_args()

    os.makedirs(CACHE, exist_ok=True)

    if args.limpar_cache:
        for n in os.listdir(CACHE):
            os.remove(os.path.join(CACHE, n))
        print('Cache descartado.')

    t0 = time.time()
    print('=' * 72)
    print('  MAPA DO ADVBOX%s' % ('  (--so-relatorio: sem rede)' if args.so_relatorio else ''))
    print('=' * 72)

    if args.so_relatorio:
        settings = _ler('settings.json', {}) or {}
        processos = _ler('processos.json', {}) or {}
        transacoes = _ler('transacoes.json', {}) or {}
        clientes = _ler('clientes.json', {}) or {}
        tarefas = _ler('tarefas.json', []) or []
        movimentacoes = _ler('movimentacoes.json', []) or []
        detalhe = _ler('detalhe_processos.json', {}) or {}
        aniversariantes = _ler('aniversariantes.json', []) or []
        rasos = {}
        if not processos:
            print('Cache vazio - rode sem --so-relatorio primeiro.')
            return 1
    else:
        settings = etapa_settings()
        processos = etapa_processos()
        transacoes = etapa_transacoes()
        clientes, rasos = etapa_clientes(processos)
        tarefas = etapa_tarefas()
        movimentacoes = etapa_movimentacoes()
        aniversariantes = etapa_aniversariantes()
        detalhe = etapa_detalhe_processos(processos) if args.completo else (
            _ler('detalhe_processos.json', {}) or {})

    print('\n  Montando saidas...')
    gerar_csvs(clientes, processos, transacoes, tarefas)
    caminho_md = gerar_relatorio(settings, clientes, rasos, processos, transacoes,
                                 tarefas, movimentacoes, detalhe, aniversariantes)

    _gravar('mapa.json', {
        'extraido_em': datetime.now().isoformat(timespec='seconds'),
        'settings': settings, 'clientes': clientes, 'processos': processos,
        'transacoes': transacoes, 'tarefas': tarefas,
        'movimentacoes': movimentacoes, 'detalhe_processos': detalhe,
        'aniversariantes': aniversariantes,
    }, pasta=PASTA)
    print('    mapa.json')

    print('\n' + '=' * 72)
    print('  Pronto em %d min %ds' % divmod(int(time.time() - t0), 60))
    print('  Pasta: %s' % PASTA)
    print('  Relatorio: %s' % caminho_md)
    print('=' * 72)
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.exit(main())
