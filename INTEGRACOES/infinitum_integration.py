"""
Integracao com a API publica do Infinitum - Alves Carneiro Advocacia e Consultoria Juridica

Docs:  https://docs.infinitum.app.br/guide
Base:  https://public.infinitum.app.br/api/v1/public
Auth:  cabecalho X-Public-Token (config/.env -> INFINITUM_API_TOKEN)
Org:   config/.env -> INFINITUM_ORG_ID (067c892a-a938-450c-9966-22fd296b1263)

Paginacao: ?page=N&limit=M; a resposta traz {data, total, page, limit}.
Rate limit nao documentado: 429 e tratado com espera exponencial.

LIMITE DE ESCRITA (mesma regra do ADVBOX e do espelhamento):
- Este modulo tem funcoes de escrita, mas NENHUM fluxo as chama sozinho.
  So se grava no Infinitum com pedido explicito da Dra. Fabiana.
- completar_registro() so preenche campo VAZIO - nunca sobrescreve o que ja
  esta no Infinitum (Filiacao e Protocolo Forcas Armadas sao da Dra. Fabiana).
- Card sem "ID Advbox" nasceu no Infinitum e nao se toca pelo espelhamento.
- Nao ha funcao de apagar card ou registro, de proposito.

Teste de conexao (so leitura):
    python INTEGRACOES/infinitum_integration.py
"""
import os
import sys
import time
import unicodedata
import requests

INFINITUM_BASE_URL = 'https://public.infinitum.app.br/api/v1/public'

# IDs fixos do escritorio (conferidos na API em 04/11/2026)
DB_CLIENTES = '67b7b6a1-f36a-426e-81ba-76e445196893'
DB_PROCESSOS_CENTRALIZADO = 'a43e0c1f-45ea-4d1d-bac8-e3b627604f7a'
DB_PUBLICACOES = '51a66ce0-4ef3-43e1-94cb-d40ea0a2433c'
POP_PROCESSOS = 'd443035a-d2d5-4f74-a661-40ef2d5dc3a8'
POP_CRM_COMERCIAL = 'a5c30880-3fc7-4aa4-9777-f1c1ebd65fd2'
POP_CONTROLADORIA = 'd104b124-bcbd-41b0-993e-c3e34b15eec8'
POP_FINANCEIRO_ADVBOX = 'c5a05a21-1971-40b3-8652-a3b1391be5f1'

_cache_campos = {}


def _norm(texto):
    if texto is None:
        return ''
    s = unicodedata.normalize('NFKD', str(texto))
    return ''.join(c for c in s if not unicodedata.combining(c)).upper().strip()


def _so_digitos(texto):
    return ''.join(c for c in str(texto or '') if c.isdigit())


def _token():
    token = os.getenv('INFINITUM_API_TOKEN')
    if not token:
        raise RuntimeError('INFINITUM_API_TOKEN nao encontrado no config/.env')
    return token


def org_id():
    return os.getenv('INFINITUM_ORG_ID') or '067c892a-a938-450c-9966-22fd296b1263'


def _request(method, endpoint, params=None, json_data=None, retries=3):
    url = f'{INFINITUM_BASE_URL}{endpoint}'
    headers = {'X-Public-Token': _token(), 'Accept': 'application/json',
               'Content-Type': 'application/json',
               'User-Agent': 'AlvesCarneiro-Automacoes/1.0'}
    espera = 2
    for tentativa in range(retries + 1):
        try:
            resp = requests.request(method, url, headers=headers, params=params,
                                    json=json_data, timeout=60)
        except requests.exceptions.RequestException as e:
            if tentativa < retries:
                time.sleep(espera)
                espera *= 2
                continue
            raise RuntimeError(f'Infinitum: conexao falhou ({e})') from e
        if resp.status_code == 429 or (resp.status_code >= 500 and tentativa < retries):
            time.sleep(int(resp.headers.get('Retry-After', espera)))
            espera *= 2
            continue
        if resp.status_code >= 400:
            try:
                corpo = resp.json()
                msg = corpo.get('error') or corpo.get('message') or resp.text
            except ValueError:
                msg = resp.text
            raise RuntimeError(f'Infinitum {method} {endpoint} -> HTTP {resp.status_code}: {msg}')
        return resp.json() if resp.text else {}
    raise RuntimeError(f'Infinitum {method} {endpoint}: tentativas esgotadas')


def _lista(resposta):
    """A API devolve a lista em 'data' (e, segundo a doc, as vezes 'cards'/'records')."""
    for chave in ('data', 'cards', 'records'):
        if isinstance(resposta.get(chave), list):
            return resposta[chave]
    return []


def _paginar(endpoint, params=None, limite=100):
    todos, pagina = [], 1
    while True:
        p = dict(params or {}, page=pagina, limit=limite)
        resp = _request('GET', endpoint, params=p)
        itens = _lista(resp)
        todos.extend(itens)
        total = resp.get('total') or (resp.get('pagination') or {}).get('total')
        if len(itens) < limite or (total is not None and len(todos) >= total):
            return todos
        pagina += 1


# ------------------------------------------------------------------ leitura

def listar_organizacoes():
    return _lista(_request('GET', '/organizations/my'))


def listar_usuarios():
    return _lista(_request('GET', '/organization-users', params={'organization_id': org_id()}))


def listar_pops():
    return _lista(_request('GET', f'/organizations/{org_id()}/pops'))


def listar_fases(pop_id):
    return _lista(_request('GET', f'/pops/{pop_id}/phases'))


def listar_campos_pop(pop_id):
    return _lista(_request('GET', '/pop-fields/by-pop', params={'pop_id': pop_id}))


def listar_cards(pop_id, phase_id=None):
    params = {'organization_id': org_id(), 'pop_id': pop_id}
    if phase_id:
        params['phase_id'] = phase_id
    return _paginar('/cards', params)


def obter_card(card_id):
    return _request('GET', f'/cards/{card_id}')


def valor_card(card, rotulo):
    """Valor de um campo do card pelo rotulo ('Nº do processo (CNJ)', 'ID Advbox')."""
    alvo = _norm(rotulo)
    for v in card.get('values') or []:
        if _norm(v.get('field_label') or v.get('label')) == alvo:
            return v.get('value')
    return None


def buscar_card_por_id_advbox(id_advbox, pop_id=POP_PROCESSOS):
    for card in listar_cards(pop_id):
        if str(valor_card(card, 'ID Advbox') or '').strip() == str(id_advbox):
            return card
    return None


def listar_databases():
    return _lista(_request('GET', '/databases', params={'organization_id': org_id()}))


def listar_campos_database(database_id):
    if database_id not in _cache_campos:
        _cache_campos[database_id] = _paginar('/database-fields', {'database_id': database_id})
    return _cache_campos[database_id]


def listar_registros(database_id):
    return _paginar('/database-records', {'database_id': database_id})


def valores_legiveis(registro, database_id):
    """Os registros guardam valores ora pelo UUID do campo, ora pela chave
    ('cpf', 'field_15'). Devolve tudo pela chave, para ler sem adivinhar."""
    por_uuid = {c['id']: c['field_id'] for c in listar_campos_database(database_id)}
    saida = {}
    for k, v in (registro.get('values') or {}).items():
        chave = por_uuid.get(k, k)
        if v not in (None, '') or chave not in saida:
            saida[chave] = v
    return saida


def buscar_cliente(termo):
    """Busca no cadastro Clientes por CPF (so digitos) ou por parte do nome.
    Devolve lista de (registro, valores_legiveis)."""
    digitos = _so_digitos(termo)
    alvo = _norm(termo)
    achados = []
    for r in listar_registros(DB_CLIENTES):
        val = valores_legiveis(r, DB_CLIENTES)
        if len(digitos) == 11 and _so_digitos(val.get('cpf')) == digitos:
            achados.append((r, val))
        elif len(digitos) != 11 and alvo and alvo in _norm(val.get('nome') or r.get('title')):
            achados.append((r, val))
    return achados


def obter_tarefa(task_id):
    return _request('GET', f'/tasks/{task_id}')


# ------------------------------------------------------------------ escrita
# So com pedido explicito da Dra. Fabiana. Nenhum fluxo chama isto sozinho.

def criar_card(pop_id, phase_id, titulo, valores=None, descricao=None, prioridade=None):
    """valores: dict {field_id: valor} com os IDs dos campos do POP."""
    corpo = {'pop_id': pop_id, 'phase_id': phase_id, 'title': titulo,
             'values': [{'field_id': k, 'value': v} for k, v in (valores or {}).items()]}
    if descricao:
        corpo['description'] = descricao
    if prioridade:
        corpo['priority'] = prioridade
    return _request('POST', '/cards', json_data=corpo)


def atualizar_card(card_id, **campos):
    return _request('PUT', f'/cards/{card_id}', json_data=campos)


def mover_card(card_id, phase_id):
    return _request('PUT', f'/cards/{card_id}/move', json_data={'phase_id': phase_id})


def criar_registro(database_id, titulo, valores):
    """valores: dict {chave_do_campo: valor}, ex. {'nome': ..., 'cpf': ...}."""
    return _request('POST', '/database-records',
                    json_data={'database_id': database_id, 'title': titulo, 'values': valores})


def completar_registro(registro, database_id, novos_valores):
    """Preenche SO os campos vazios. Devolve (atualizados, ignorados) - os
    ignorados ja tinham valor no Infinitum e ficaram como estavam."""
    atuais = valores_legiveis(registro, database_id)
    atualizar, ignorados = {}, {}
    for chave, valor in novos_valores.items():
        if valor in (None, ''):
            continue
        if atuais.get(chave) not in (None, ''):
            ignorados[chave] = valor
        else:
            atualizar[chave] = valor
    if atualizar:
        _request('PUT', f'/database-records/{registro["id"]}', json_data={'values': atualizar})
    return atualizar, ignorados


def concluir_tarefa(task_id):
    return _request('POST', f'/tasks/{task_id}/complete')


# ------------------------------------------------------------------ teste

def testar_conexao():
    orgs = listar_organizacoes()
    print(f'Conectado. Organizacoes visiveis: {len(orgs)}')
    for o in orgs:
        marca = ' <- INFINITUM_ORG_ID' if o['id'] == org_id() else ''
        print(f'  {o["name"]} ({o["id"]}){marca}')
    print('\nPOPs:')
    for p in listar_pops():
        print(f'  {p["name"]:<28} {p["type"]:<8} {p["id"]}')
    print('\nDatabases:')
    for d in listar_databases():
        print(f'  {d["name"]:<28} {d.get("records_count", "?"):>4} registros  {d["id"]}')
    return 0


if __name__ == '__main__':
    raiz = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(raiz, 'config', '.env'))
    except ImportError:
        pass
    sys.exit(testar_conexao())
