"""
Integracao com a API do Jurisprudencias.ai - Alves Carneiro Advocacia e Consultoria Juridica

Busca textual de jurisprudencia em 54 bases (STF, STJ, TST, TRF1-6, todos os TJs,
TRTs e CARF) e consulta da ementa integral pelo numero do processo.

Spec:  https://jurisprudencias.ai/openapi.json (OpenAPI 3.1)
Base:  https://jurisprudencias.ai/api/v1
Auth:  Authorization: Bearer jur_... (config/.env -> JURISPRUDENCIAS_API_TOKEN)
Token: https://jurisprudencias.ai/api-tokens

COTA: 5 consultas POR DIA (cabecalho x-ratelimit-limit), zerando a meia-noite de
Brasilia. /courts nao conta. Por isso:
- toda resposta de busca/consulta fica em cache local (INTEGRACOES/_cache_jurisprudencias/, nao versionado),
  e a mesma pergunta nao gasta cota de novo no mesmo dia (busca) ou nunca (ementa);
- 429 NAO e repetido: a cota so volta no dia seguinte, e repetir so desperdica.
- a cota restante da ultima chamada fica em ultima_cota().

Jurisprudencia daqui e PISTA, nao fonte oficial: antes de entrar em peca, abrir o
`url` (site do tribunal) e conferir - regra do CLAUDE.md / base-conhecimento-cursos.md.

Sintaxe de busca (websearch do PostgreSQL):
    "frase exata"   termo1 termo2 (exige todos)   a b OR c (= "a e b" ou "c")
    -termo / NOT termo (exclui).  Parenteses sao IGNORADOS.

Uso (linha de comando):
    python INTEGRACOES/jurisprudencias_integration.py                 # teste (nao gasta cota)
    python INTEGRACOES/jurisprudencias_integration.py tribunais
    python INTEGRACOES/jurisprudencias_integration.py buscar trf2 "\"pensao militar\" teto soma" \
        --julg-de 01/01/2022 --ordem julgamento --pagina 0
    python INTEGRACOES/jurisprudencias_integration.py consultar stj "REsp 1814919"
    python INTEGRACOES/jurisprudencias_integration.py cota
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time

import requests

BASE_URL = 'https://jurisprudencias.ai/api/v1'
RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
CACHE_DIR = os.path.join(RAIZ, 'INTEGRACOES', '_cache_jurisprudencias')  # nao versionado
FUSO_BR = dt.timezone(dt.timedelta(hours=-3))

ORDENS = {'publicacao': 'publication_date', 'julgamento': 'trial_date',
          'publication_date': 'publication_date', 'trial_date': 'trial_date'}

_ultima_cota = {}


class CotaEsgotada(RuntimeError):
    """429: a cota diaria acabou. Volta a meia-noite de Brasilia."""


class NaoEncontrado(LookupError):
    """404 no lookup: o numero nao existe naquela base (ou esta em outro formato)."""


# ------------------------------------------------------------------ auxiliares

def _token():
    token = os.getenv('JURISPRUDENCIAS_API_TOKEN')
    if not token:
        raise RuntimeError('JURISPRUDENCIAS_API_TOKEN nao encontrado no config/.env')
    return token


def tribunal_id(nome):
    """'TRF-2', 'trf 2', 'TJ/RJ' -> 'trf2', 'tjrj'."""
    return re.sub(r'[^a-z0-9]', '', str(nome).lower())


def _data_iso(valor):
    """Aceita DD/MM/AAAA ou AAAA-MM-DD; devolve AAAA-MM-DD."""
    if not valor:
        return None
    valor = valor.strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return dt.datetime.strptime(valor, fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    raise ValueError(f'Data invalida: {valor!r} (use DD/MM/AAAA)')


def _registrar_cota(resp):
    h = resp.headers
    if 'x-ratelimit-limit' in h:
        reset = h.get('x-ratelimit-reset')
        _ultima_cota.update({
            'limite': int(h['x-ratelimit-limit']),
            'restante': int(h.get('x-ratelimit-remaining', 0)),
            'renova_em': (dt.datetime.fromtimestamp(int(reset), FUSO_BR).strftime('%d/%m/%Y %H:%M')
                          if reset else None),
        })
        _gravar_json(os.path.join(CACHE_DIR, '_cota.json'),
                     dict(_ultima_cota, consultado_em=dt.datetime.now(FUSO_BR).isoformat()))


def ultima_cota():
    """Cota da ultima chamada que consumiu cota (desta execucao ou da anterior)."""
    if _ultima_cota:
        return dict(_ultima_cota)
    return _ler_json(os.path.join(CACHE_DIR, '_cota.json'))


def _ler_json(caminho):
    try:
        with open(caminho, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _gravar_json(caminho, dados):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)


def _chave_cache(endpoint, params, por_dia):
    base = json.dumps([endpoint, sorted((params or {}).items())], ensure_ascii=False)
    if por_dia:  # busca: resultado muda com o tempo, vale so no dia
        base += dt.datetime.now(FUSO_BR).strftime('|%Y-%m-%d')
    return os.path.join(CACHE_DIR, hashlib.sha1(base.encode()).hexdigest()[:20] + '.json')


def _get(endpoint, params=None, cache=None, retries=2):
    """GET com cache. cache: None (sem), 'dia' (busca) ou 'sempre' (ementa)."""
    caminho = _chave_cache(endpoint, params, cache == 'dia') if cache else None
    if caminho:
        guardado = _ler_json(caminho)
        if guardado is not None:
            return guardado

    headers = {'Authorization': f'Bearer {_token()}', 'Accept': 'application/json',
               'User-Agent': 'AlvesCarneiro-Automacoes/1.0'}
    espera = 2
    for tentativa in range(retries + 1):
        try:
            resp = requests.get(f'{BASE_URL}{endpoint}', headers=headers,
                                params=params, timeout=60)
        except requests.exceptions.RequestException as e:
            if tentativa < retries:
                time.sleep(espera)
                espera *= 2
                continue
            raise RuntimeError(f'Jurisprudencias.ai: conexao falhou ({e})') from e
        if resp.status_code >= 500 and tentativa < retries:
            time.sleep(espera)
            espera *= 2
            continue
        break

    _registrar_cota(resp)
    try:
        corpo = resp.json()
    except ValueError:
        corpo = {}
    erro = (corpo.get('error') or {}) if isinstance(corpo, dict) else {}
    msg = erro.get('message') or resp.text[:300]

    if resp.status_code == 429:
        renova = (ultima_cota() or {}).get('renova_em') or 'meia-noite (Brasilia)'
        raise CotaEsgotada(f'Cota diaria do Jurisprudencias.ai esgotada. Renova em {renova}.')
    if resp.status_code == 404:
        raise NaoEncontrado(msg)
    if resp.status_code == 401:
        raise RuntimeError(f'Jurisprudencias.ai: token invalido ou ausente ({msg})')
    if resp.status_code >= 400:
        raise RuntimeError(f'Jurisprudencias.ai {resp.status_code}: {msg}')

    if caminho:
        _gravar_json(caminho, corpo)
    return corpo


# ------------------------------------------------------------------ API

def listar_tribunais():
    """[{id, name, abbreviation, decisions_count}] - nao gasta cota."""
    return _get('/courts')['data']


def buscar(tribunal, q, pagina=0, ordem='publicacao', pub_de=None, pub_ate=None,
           julg_de=None, julg_ate=None):
    """Busca textual. Devolve {data: [DecisionSummary], meta, links}.

    Gasta 1 de cota (salvo se a mesma busca ja foi feita hoje - cache).
    Datas em DD/MM/AAAA ou AAAA-MM-DD. ordem: 'publicacao' | 'julgamento'.
    """
    params = {'q': q, 'page': int(pagina), 'sort_by': ORDENS[ordem]}
    for nome, valor in (('pub_from', pub_de), ('pub_to', pub_ate),
                        ('trial_from', julg_de), ('trial_to', julg_ate)):
        if valor:
            params[nome] = _data_iso(valor)
    return _get(f'/courts/{tribunal_id(tribunal)}/decisions', params, cache='dia')


def consultar(tribunal, numero):
    """Ementa integral pelo numero do processo (DecisionFull).

    Gasta 1 de cota na primeira vez; depois vem do cache. Levanta NaoEncontrado
    se o numero nao existir naquela base - o formato do numero e o da propria base
    (ex.: STF usa 'ARE 1615390'; copie o process_number devolvido pela busca).
    """
    return _get(f'/courts/{tribunal_id(tribunal)}/decisions/lookup',
                {'n': numero.strip()}, cache='sempre')['data']


# ------------------------------------------------------------------ saida legivel

def formatar_resultado(item, completo=False):
    linhas = [f'{item.get("process_number")} - {item.get("process_type") or ""}'.rstrip(' -'),
              f'  Relator: {item.get("rapporteur") or "-"} | {item.get("adjudicating_body") or "-"}',
              f'  Julgamento: {item.get("trial_date") or "-"} | Publicacao: {item.get("publication_date") or "-"}']
    texto = item.get('summary') if completo else item.get('excerpt')
    if texto:
        linhas.append('  ' + (texto if completo else texto[:500] + ('...' if len(texto) > 500 else '')))
    if item.get('url'):
        linhas.append(f'  Fonte (conferir antes de citar): {item["url"]}')
    return '\n'.join(linhas)


def _imprimir_cota():
    c = ultima_cota()
    if c:
        print(f'\nCota: {c["restante"]}/{c["limite"]} restantes hoje (renova {c.get("renova_em")})')


def testar_conexao():
    tribs = listar_tribunais()
    total = sum(t.get('decisions_count') or 0 for t in tribs)
    print(f'Conectado ao Jurisprudencias.ai. {len(tribs)} bases, {total:,} decisoes.'.replace(',', '.'))
    destaque = [t for t in tribs if t['id'] in ('stf', 'stj', 'trf2', 'tjrj')]
    for t in destaque:
        print(f'  {t["id"]:<6} {t["name"]:<45} {t["decisions_count"]:>10}')
    print('(teste nao gasta cota)')
    _imprimir_cota()
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description='Jurisprudencias.ai - busca de jurisprudencia')
    sub = p.add_subparsers(dest='cmd')
    sub.add_parser('testar')
    sub.add_parser('tribunais')
    sub.add_parser('cota')
    b = sub.add_parser('buscar')
    b.add_argument('tribunal')
    b.add_argument('q')
    b.add_argument('--pagina', type=int, default=0)
    b.add_argument('--ordem', choices=['publicacao', 'julgamento'], default='publicacao')
    b.add_argument('--pub-de')
    b.add_argument('--pub-ate')
    b.add_argument('--julg-de')
    b.add_argument('--julg-ate')
    b.add_argument('--json', action='store_true')
    c = sub.add_parser('consultar')
    c.add_argument('tribunal')
    c.add_argument('numero')
    c.add_argument('--json', action='store_true')
    a = p.parse_args(argv)

    try:
        if a.cmd in (None, 'testar'):
            return testar_conexao()
        if a.cmd == 'tribunais':
            for t in listar_tribunais():
                print(f'{t["id"]:<6} {t["abbreviation"]:<6} {t["decisions_count"]:>10}  {t["name"]}')
            return 0
        if a.cmd == 'cota':
            c = ultima_cota()
            print(json.dumps(c, ensure_ascii=False, indent=1) if c else 'Nenhuma consulta registrada ainda.')
            return 0
        if a.cmd == 'buscar':
            r = buscar(a.tribunal, a.q, a.pagina, a.ordem, a.pub_de, a.pub_ate, a.julg_de, a.julg_ate)
            if a.json:
                print(json.dumps(r, ensure_ascii=False, indent=1))
            else:
                m = r.get('meta', {})
                print(f'{tribunal_id(a.tribunal).upper()} - pagina {m.get("page")} '
                      f'({len(r["data"])} itens; total {m.get("total") or "?"}; '
                      f'proxima: {"sim" if m.get("has_next_page") else "nao"})\n')
                for item in r['data']:
                    print(formatar_resultado(item) + '\n')
            _imprimir_cota()
            return 0
        if a.cmd == 'consultar':
            d = consultar(a.tribunal, a.numero)
            print(json.dumps(d, ensure_ascii=False, indent=1) if a.json else formatar_resultado(d, completo=True))
            _imprimir_cota()
            return 0
    except CotaEsgotada as e:
        print(e, file=sys.stderr)
        return 3
    except NaoEncontrado as e:
        print(f'Nao encontrado: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(RAIZ, 'config', '.env'))
    except ImportError:
        pass
    sys.exit(main())
