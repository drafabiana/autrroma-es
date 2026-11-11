"""
=============================================================================
  ESPELHAMENTO ADVBOX -> INFINITUM (semiautomatico) - ALVES CARNEIRO ADVOCACIA
=============================================================================

  Vigencia: ate 30/11/2026, enquanto o escritorio usa os dois sistemas.

  Este script so LE o ADVBOX. Tira uma foto (processos, clientes,
  financeiro e ultimas movimentacoes), compara com a foto anterior e acumula as
  diferencas numa fila de pendencias. Quem grava no Infinitum e o Claude, pelo
  conector ou por INTEGRACOES/infinitum_integration.py (API publica, token em
  config/.env desde 04/11/2026), so quando a Dra. Fabiana pede "aplica o
  espelhamento".

  Uso:
    python SYNC/advbox_infinitum.py                    # coleta (tarefa diaria)
    python SYNC/advbox_infinitum.py --linha-de-base    # 1a foto, sem gerar pendencia
    python SYNC/advbox_infinitum.py pendencias         # lista o que falta aplicar
    python SYNC/advbox_infinitum.py marcar 12 13 14    # marca pendencias como aplicadas

  Regras do espelhamento (decididas em 03/11/2026):
  - So ADVBOX -> Infinitum. O que nasce no Infinitum (cards sem "ID Advbox")
    nao e tocado.
  - Nunca sobrescrever campo preenchido no Infinitum: o ADVBOX so completa vazio.
    Filiacao e Protocolo Forcas Armadas sao da Dra. Fabiana; cliente novo entra
    com "Nao informada" / "Nao se aplica".
  - Senha gov e demais anotacoes do cliente vao para Observacoes.
  - Chave: processo -> campo "ID Advbox" do card; cliente -> "Migrado do Advbox
    (ID nnnn)" nas Observacoes.
  - A listagem GET /customers do ADVBOX e INCOMPLETA (omite ~100 clientes
    reais) e mistura parte contraria. Cliente novo e detectado pelos processos
    e buscado por ID.

  Saidas em SYNC/espelhamento/ (nao versionado - tem dado pessoal):
    snapshot.json          foto mais recente
    pendencias.json        fila acumulada (pendente / aplicado)
    relatorio-AAAA-MM-DD.md  o que mudou na coleta do dia
    _log-execucao.txt      log da tarefa agendada
=============================================================================
"""
import os
import sys
import json
import time
import argparse
from datetime import datetime

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(RAIZ, 'INTEGRACOES'))

from dotenv import load_dotenv
load_dotenv(os.path.join(RAIZ, 'config', '.env'))

from advbox_integration import _request, listar_transacoes

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'espelhamento')
ARQ_SNAPSHOT = os.path.join(PASTA, 'snapshot.json')
ARQ_PENDENCIAS = os.path.join(PASTA, 'pendencias.json')

# Campos do processo que o card do Infinitum espelha. Mudanca em outro campo
# nao gera pendencia.
CAMPOS_PROCESSO = ['process_number', 'protocol_number', 'folder', 'type', 'group',
                   'stage', 'step', 'responsible', 'process_date', 'status_closure',
                   'fees_expec', 'fees_money', 'contingency', 'notes', 'customers']


def _ler(caminho, padrao):
    if not os.path.exists(caminho):
        return padrao
    with open(caminho, encoding='utf-8') as f:
        return json.load(f)


def _gravar(caminho, dados):
    tmp = caminho + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=1, default=str)
    os.replace(tmp, caminho)


def _paginar(endpoint, limite=100):
    todos = []
    offset = 0
    while True:
        data = _request('GET', endpoint, params={'limit': limite, 'offset': offset}) or {}
        registros = data.get('data', [])
        todos.extend(registros)
        if len(registros) < limite or len(todos) >= data.get('totalCount', 0):
            return todos
        offset += limite


def tirar_foto(clientes_conhecidos, detalhar=True):
    """Le o ADVBOX inteiro. clientes_conhecidos: dict id->cliente da foto anterior,
    para buscar por ID so quem e novo."""
    print('  Processos...')
    processos = {str(p['id']): p for p in _paginar('/lawsuits')}
    print(f'    {len(processos)}')

    print('  Financeiro...')
    transacoes = {str(t['id']): t for t in listar_transacoes()}

    print('  Ultimas movimentacoes...')
    try:
        movs = _paginar('/last_movements')
    except Exception as e:  # movimentacao e acessorio: nao derruba a coleta
        print(f'    falhou ({e}); segue sem movimentacoes')
        movs = None

    # Clientes: os que aparecem nos processos + os da listagem (que e incompleta,
    # mas pega cliente cadastrado antes de ter processo).
    vistos = {}
    for p in processos.values():
        for c in p.get('customers') or []:
            vistos[str(c['customer_id'])] = c
    try:
        for c in _paginar('/customers'):
            vistos.setdefault(str(c['id']), {'customer_id': c['id'], 'name': c.get('name')})
    except Exception as e:
        print(f'    listagem de clientes falhou ({e}); segue so com os dos processos')

    clientes = {}
    novos = [i for i in vistos if i not in clientes_conhecidos]
    print(f'  Clientes: {len(vistos)} ({len(novos)} novos a detalhar)')
    for cid in vistos:
        if cid in clientes_conhecidos:
            clientes[cid] = clientes_conhecidos[cid]
            continue
        if not detalhar:  # linha de base: o Infinitum ja foi conferido, nao precisa do detalhe
            clientes[cid] = vistos[cid]
            continue
        time.sleep(2.1)  # limite do ADVBOX: 30 GET/min
        try:
            clientes[cid] = _request('GET', f'/customers/{cid}') or vistos[cid]
        except Exception:
            clientes[cid] = vistos[cid]

    return {'data': datetime.now().isoformat(timespec='seconds'),
            'processos': processos, 'transacoes': transacoes,
            'clientes': clientes,
            'movimentacoes': {_chave_mov(m): m for m in movs} if movs is not None else None}


def _chave_mov(m):
    # /last_movements nao traz id proprio
    return f'{m.get("lawsuit_id")}|{m.get("date")}|{m.get("title")}'


def _papeis(processo):
    return sorted(str(c['customer_id']) for c in processo.get('customers') or [])


def comparar(antiga, nova):
    """Devolve a lista de eventos (sem numeracao) entre duas fotos."""
    ev = []
    pa, pn = antiga['processos'], nova['processos']
    for pid, p in pn.items():
        if pid not in pa:
            ev.append({'tipo': 'processo_novo', 'id_advbox': pid, 'dados': p})
            continue
        mud = {}
        for campo in CAMPOS_PROCESSO:
            a, b = pa[pid].get(campo), p.get(campo)
            if campo == 'customers':
                a, b = _papeis(pa[pid]), _papeis(p)
            if a != b:
                mud[campo] = {'de': pa[pid].get(campo), 'para': p.get(campo)}
        if mud:
            ev.append({'tipo': 'processo_alterado', 'id_advbox': pid,
                       'titulo': _titulo(p), 'mudancas': mud})
    for pid in pa:
        if pid not in pn:
            ev.append({'tipo': 'processo_removido', 'id_advbox': pid, 'titulo': _titulo(pa[pid])})

    ta, tn = antiga['transacoes'], nova['transacoes']
    for tid, t in tn.items():
        if tid not in ta:
            ev.append({'tipo': 'financeiro_novo', 'id_advbox': tid, 'dados': t})
        elif t != ta[tid]:
            mud = {k: {'de': ta[tid].get(k), 'para': t.get(k)}
                   for k in set(t) | set(ta[tid]) if t.get(k) != ta[tid].get(k)}
            ev.append({'tipo': 'financeiro_alterado', 'id_advbox': tid, 'mudancas': mud})
    for tid in ta:
        if tid not in tn:
            ev.append({'tipo': 'financeiro_removido', 'id_advbox': tid, 'dados': ta[tid]})

    for cid, c in nova['clientes'].items():
        if cid not in antiga['clientes']:
            ev.append({'tipo': 'cliente_novo', 'id_advbox': cid, 'dados': c,
                       'aviso': 'conferir se e cliente ou parte contraria'})

    ma, mn = antiga.get('movimentacoes'), nova.get('movimentacoes')
    if ma is not None and mn is not None:
        for mid, m in mn.items():
            if mid not in ma:
                ev.append({'tipo': 'movimentacao_nova', 'id_advbox': str(m.get('lawsuit_id')),
                           'dados': m})
    return ev


def _titulo(p):
    nomes = ', '.join(c.get('name', '') for c in p.get('customers') or [])
    num = p.get('process_number') or p.get('protocol_number') or 'sem numero'
    return f'{nomes} - {num}'


def _resumo(e):
    t = e['tipo']
    if t == 'processo_novo':
        return f'Processo novo {e["id_advbox"]}: {_titulo(e["dados"])} ({e["dados"].get("type")})'
    if t == 'processo_alterado':
        partes = []
        for campo, m in e['mudancas'].items():
            if campo == 'customers':
                partes.append('partes alteradas')
            elif campo == 'notes':
                partes.append('anotacoes alteradas')
            else:
                partes.append(f'{campo}: {m["de"]} -> {m["para"]}')
        return f'Processo {e["id_advbox"]} ({e["titulo"]}): ' + '; '.join(partes)
    if t == 'processo_removido':
        return f'Processo {e["id_advbox"]} sumiu do ADVBOX ({e["titulo"]}) - NAO apagar card sem ordem'
    if t == 'cliente_novo':
        d = e['dados']
        return f'Cliente novo {e["id_advbox"]}: {d.get("name")} ({d.get("identification") or "sem CPF"}) - {e["aviso"]}'
    if t.startswith('financeiro'):
        d = e.get('dados') or {}
        desc = d.get('description') or d.get('category') or ''
        return f'{t.replace("_", " ").capitalize()} {e["id_advbox"]} {desc}'.strip()
    if t == 'movimentacao_nova':
        d = e['dados']
        titulo = ' '.join(str(d.get('title') or '').split())[:100]
        return f'Movimentacao {d.get("date")} no processo {e["id_advbox"]} ({d.get("customers")}): {titulo}'
    return f'{t} {e["id_advbox"]}'


def coletar(linha_de_base=False):
    os.makedirs(PASTA, exist_ok=True)
    antiga = _ler(ARQ_SNAPSHOT, None)
    if antiga is None and not linha_de_base:
        print('Nao ha foto anterior. Rode primeiro com --linha-de-base.')
        return 2

    print(f'Espelhamento ADVBOX -> Infinitum - coleta {datetime.now():%d/%m/%Y %H:%M}')
    nova = tirar_foto((antiga or {}).get('clientes', {}), detalhar=not linha_de_base)

    if linha_de_base:
        _gravar(ARQ_SNAPSHOT, nova)
        print(f'Linha de base gravada: {len(nova["processos"])} processos, '
              f'{len(nova["clientes"])} clientes, {len(nova["transacoes"])} lancamentos.')
        return 0

    eventos = comparar(antiga, nova)
    fila = _ler(ARQ_PENDENCIAS, [])
    prox = max((e['n'] for e in fila), default=0) + 1
    for e in eventos:
        e.update({'n': prox, 'detectado_em': nova['data'], 'status': 'pendente'})
        prox += 1
    fila.extend(eventos)
    _gravar(ARQ_PENDENCIAS, fila)
    _gravar(ARQ_SNAPSHOT, nova)  # so depois da fila: se cair no meio, a proxima coleta repete

    rel = os.path.join(PASTA, f'relatorio-{datetime.now():%Y-%m-%d}.md')
    with open(rel, 'a', encoding='utf-8') as f:
        f.write(f'# Espelhamento ADVBOX -> Infinitum - {datetime.now():%d/%m/%Y %H:%M}\n\n')
        if not eventos:
            f.write('Nenhuma mudanca no ADVBOX desde a coleta anterior.\n\n')
        for e in eventos:
            f.write(f'- [{e["n"]}] {_resumo(e)}\n')
        f.write('\n')
    pend = sum(1 for e in fila if e['status'] == 'pendente')
    print(f'{len(eventos)} mudancas novas; {pend} pendencias aguardando aplicacao no Infinitum.')
    print(f'Relatorio: {rel}')
    return 0


def listar_pendencias():
    fila = [e for e in _ler(ARQ_PENDENCIAS, []) if e['status'] == 'pendente']
    if not fila:
        print('Nenhuma pendencia. Infinitum em dia com o ADVBOX (ate a ultima coleta).')
        return 0
    print(f'{len(fila)} pendencias:')
    for e in fila:
        print(f'  [{e["n"]}] {e["detectado_em"][:10]}  {_resumo(e)}')
    return 0


def marcar(numeros, nota=''):
    fila = _ler(ARQ_PENDENCIAS, [])
    alvo = {int(n) for n in numeros}
    feitos = 0
    for e in fila:
        if e['n'] in alvo and e['status'] == 'pendente':
            e.update({'status': 'aplicado', 'aplicado_em': datetime.now().isoformat(timespec='seconds')})
            if nota:
                e['nota'] = nota
            feitos += 1
    _gravar(ARQ_PENDENCIAS, fila)
    print(f'{feitos} pendencias marcadas como aplicadas.')
    return 0


def main():
    ap = argparse.ArgumentParser(description='Espelhamento ADVBOX -> Infinitum (so leitura no ADVBOX)')
    ap.add_argument('acao', nargs='?', default='coletar', choices=['coletar', 'pendencias', 'marcar'])
    ap.add_argument('numeros', nargs='*', help='numeros das pendencias (acao marcar)')
    ap.add_argument('--linha-de-base', action='store_true', help='grava a 1a foto sem gerar pendencia')
    ap.add_argument('--nota', default='', help='observacao ao marcar (ex.: "ignorado - parte contraria")')
    a = ap.parse_args()
    if a.acao == 'pendencias':
        return listar_pendencias()
    if a.acao == 'marcar':
        return marcar(a.numeros, a.nota)
    return coletar(a.linha_de_base)


if __name__ == '__main__':
    sys.exit(main())
