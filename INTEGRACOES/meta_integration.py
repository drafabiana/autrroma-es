"""
Integracao com a Meta Marketing API (Facebook/Instagram Ads) - Alves Carneiro Advocacia

Docs:  https://developers.facebook.com/docs/marketing-apis
Base:  https://graph.facebook.com/{META_API_VERSION}
Auth:  token de USUARIO DE SISTEMA (app "AUTOMACOES"), nao expira
       config/.env -> META_ACCESS_TOKEN, META_API_VERSION, META_AD_ACCOUNT_ID, META_PAGE_ID

PRE-REQUISITO (Gerenciador de Negocios -> Configuracoes -> Usuarios do sistema):
o usuario de sistema "AUTOMACOES" precisa ter recebido acesso a conta de anuncios,
a pagina do Facebook e a conta do Instagram. Sem isso a API responde lista vazia
(foi o que aconteceu no teste de 11/11/2026).

LIMITE DE ESCRITA (mesma regra do ADVBOX e do Infinitum):
- Nenhum fluxo cria ou altera campanha sozinho; so com pedido explicito da Dra. Fabiana.
- Tudo o que este modulo cria nasce PAUSADO. Ativar (gastar dinheiro) e ato humano,
  feito no Gerenciador de Anuncios ou com ativar() sob pedido explicito.
- Nao ha funcao de apagar, de proposito.

PUBLICIDADE DA ADVOCACIA (Provimento OAB 205/2021 + Codigo de Etica, arts. 39-47):
impulsionamento e permitido para conteudo INFORMATIVO; e vedado prometer resultado,
mercantilizar (preco, desconto, "gratis" como chamariz), captar clientela e usar
superlativo. conferir_texto_oab() aponta termos de risco ANTES de criar o anuncio -
e um filtro, nao parecer: o texto final e revisado pela Dra. Fabiana.

Teste de conexao (so leitura):
    python INTEGRACOES/meta_integration.py
"""
import os
import re
import sys
import time
import unicodedata
import requests

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_RAIZ, 'config', '.env'))
except ImportError:
    pass


def _versao():
    return os.getenv('META_API_VERSION') or 'v21.0'


def _base():
    return f'https://graph.facebook.com/{_versao()}'


def _token():
    t = os.getenv('META_ACCESS_TOKEN')
    if not t:
        raise RuntimeError('META_ACCESS_TOKEN nao encontrado no config/.env')
    return t


def conta_padrao():
    conta = (os.getenv('META_AD_ACCOUNT_ID') or '').strip()
    if not conta:
        raise RuntimeError('META_AD_ACCOUNT_ID vazio no config/.env - rode o teste de '
                           'conexao para listar as contas visiveis')
    return conta if conta.startswith('act_') else f'act_{conta}'


def _request(method, endpoint, params=None, data=None, retries=3):
    url = endpoint if endpoint.startswith('http') else f'{_base()}{endpoint}'
    params = dict(params or {})
    params['access_token'] = _token()
    espera = 5
    for tentativa in range(retries + 1):
        try:
            resp = requests.request(method, url, params=params, data=data, timeout=90)
        except requests.exceptions.RequestException as e:
            if tentativa < retries:
                time.sleep(espera)
                espera *= 2
                continue
            raise RuntimeError(f'Meta: conexao falhou ({type(e).__name__})') from None
        corpo = resp.json() if resp.content else {}
        if resp.ok:
            return corpo
        erro = corpo.get('error', {})
        # 4/17/32/613 = limite de chamadas; 2 = erro temporario
        if erro.get('code') in (2, 4, 17, 32, 613) and tentativa < retries:
            time.sleep(espera)
            espera *= 2
            continue
        msg = erro.get('error_user_msg') or erro.get('message') or resp.text[:300]
        raise RuntimeError(f'Meta {resp.status_code} (code {erro.get("code")}): {msg}')


def _paginar(endpoint, params=None, limite=500):
    itens, corpo = [], _request('GET', endpoint, params=params)
    while True:
        itens.extend(corpo.get('data', []))
        prox = corpo.get('paging', {}).get('next')
        if not prox or len(itens) >= limite:
            return itens[:limite]
        corpo = _request('GET', prox)


# --------------------------------------------------------------------------- leitura

def diagnostico():
    """Quem e o token, que permissoes tem e que ativos enxerga."""
    eu = _request('GET', '/me', {'fields': 'id,name'})
    perms = [p['permission'] for p in _request('GET', '/me/permissions')['data']
             if p.get('status') == 'granted']
    return {'usuario': eu, 'permissoes': perms,
            'contas_anuncio': listar_contas(), 'paginas': listar_paginas()}


def listar_contas():
    campos = 'id,name,account_status,currency,timezone_name,amount_spent,business{id,name}'
    contas = _paginar('/me/adaccounts', {'fields': campos})
    if not contas:
        contas = _paginar('/me/assigned_ad_accounts', {'fields': campos})
    return contas


def listar_paginas():
    campos = 'id,name,instagram_business_account{id,username}'
    paginas = _paginar('/me/accounts', {'fields': campos})
    if not paginas:
        paginas = _paginar('/me/assigned_pages', {'fields': campos})
    return paginas


def listar_campanhas(conta=None, so_ativas=False):
    params = {'fields': 'id,name,objective,status,effective_status,daily_budget,'
                        'lifetime_budget,start_time,stop_time,created_time'}
    if so_ativas:
        params['effective_status'] = '["ACTIVE"]'
    return _paginar(f'/{conta or conta_padrao()}/campaigns', params)


def listar_conjuntos(campanha_id):
    return _paginar(f'/{campanha_id}/adsets', {
        'fields': 'id,name,status,effective_status,daily_budget,optimization_goal,'
                  'targeting,start_time,end_time'})


def listar_anuncios(objeto_id):
    """Anuncios de uma campanha, conjunto ou conta."""
    return _paginar(f'/{objeto_id}/ads', {
        'fields': 'id,name,status,effective_status,creative{id,name,body,title}'})


def insights(objeto_id=None, periodo='last_30d', nivel='campaign', inicio=None, fim=None):
    """Desempenho: gasto, alcance, cliques, CPC, CTR, leads e conversas iniciadas.

    periodo: today, yesterday, last_7d, last_30d, this_month, last_month, maximum...
    inicio/fim (AAAA-MM-DD) substituem o periodo.
    """
    params = {'level': nivel,
              'fields': 'campaign_name,adset_name,ad_name,spend,impressions,reach,clicks,'
                        'cpc,ctr,cpm,actions,cost_per_action_type'}
    if inicio and fim:
        params['time_range'] = f'{{"since":"{inicio}","until":"{fim}"}}'
    else:
        params['date_preset'] = periodo
    return _paginar(f'/{objeto_id or conta_padrao()}/insights', params)


def resultados(linha):
    """Extrai leads e conversas de WhatsApp/Messenger da lista 'actions'."""
    acoes = {a['action_type']: float(a['value']) for a in linha.get('actions', [])}
    leads = acoes.get('lead', 0) + acoes.get('onsite_conversion.lead_grouped', 0)
    conversas = acoes.get('onsite_conversion.messaging_conversation_started_7d', 0)
    return {'leads': int(leads), 'conversas': int(conversas)}


# --------------------------------------------------------------------- conformidade OAB

_TERMOS_RISCO = [
    (r'\bgarant\w*', 'promessa de resultado'),
    (r'\b100 ?%', 'promessa de resultado'),
    (r'\b(ganhe|ganha|vitoria certa|causa ganha|sucesso certo)\b', 'promessa de resultado'),
    (r'\b(gratis|gratuit\w*|sem custo)\b', 'mercantilizacao (gratuidade como chamariz)'),
    # "desconto" sozinho e o desconto em folha da pensao - so barra o sentido comercial
    (r'\b(desconto (especial|exclusivo|de \d+|nos honorarios)|\d+ ?% de desconto|promocao|'
     r'oferta|imperdivel|black friday|so hoje)\b', 'mercantilizacao'),
    (r'r\$ ?\d', 'preco/valor no anuncio (mercantilizacao)'),
    (r'\b(melhor|maior|numero 1|n[oº] ?1|lider|o mais)\b', 'superlativo / comparacao'),
    (r'\b(contrate ja|ligue agora|nao perca|ultimas vagas|corra)\b', 'apelo de captacao'),
    (r'\b(milhoes recuperados|ja ganhamos|casos ganhos)\b', 'divulgacao de resultado'),
]


def _sem_acento(s):
    s = unicodedata.normalize('NFKD', s or '')
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()


def conferir_texto_oab(*textos):
    """Lista de (trecho, motivo) com termos de risco no texto do anuncio."""
    achados = []
    for texto in textos:
        t = _sem_acento(texto)
        for padrao, motivo in _TERMOS_RISCO:
            for m in re.finditer(padrao, t):
                achados.append((m.group(0), motivo))
    return achados


# ----------------------------------------------- escrita (SO com pedido explicito)

def criar_campanha(nome, objetivo='OUTCOME_LEADS', orcamento_diario_reais=None,
                   conta=None, categorias_especiais=None):
    """Cria campanha PAUSADA. Objetivos ODAX: OUTCOME_LEADS, OUTCOME_ENGAGEMENT,
    OUTCOME_TRAFFIC, OUTCOME_AWARENESS. Orcamento aqui = CBO (no nivel da campanha)."""
    dados = {'name': nome, 'objective': objetivo, 'status': 'PAUSED',
             'special_ad_categories': str(categorias_especiais or []).replace("'", '"')}
    if orcamento_diario_reais:
        dados['daily_budget'] = int(round(float(orcamento_diario_reais) * 100))
        dados['bid_strategy'] = 'LOWEST_COST_WITHOUT_CAP'
    else:
        dados['is_adset_budget_sharing_enabled'] = 'false'
    return _request('POST', f'/{conta or conta_padrao()}/campaigns', data=dados)


def criar_conjunto(campanha_id, nome, publico, otimizacao='CONVERSATIONS',
                   orcamento_diario_reais=None, destino='WHATSAPP', inicio=None,
                   pagina_id=None, conta=None):
    """Cria conjunto PAUSADO.

    publico: dict de targeting da Meta, ex.:
      {"geo_locations": {"cities": [{"key": "...", "radius": 40, "distance_unit": "kilometer"}]},
       "age_min": 50, "age_max": 65,
       "targeting_automation": {"advantage_audience": 0}}
    destino WHATSAPP + otimizacao CONVERSATIONS = anuncio de clique para WhatsApp.
    """
    import json
    dados = {'name': nome, 'campaign_id': campanha_id, 'status': 'PAUSED',
             'billing_event': 'IMPRESSIONS', 'optimization_goal': otimizacao,
             'targeting': json.dumps(publico)}
    if destino:
        dados['destination_type'] = destino
    pagina = pagina_id or os.getenv('META_PAGE_ID')
    if pagina:
        dados['promoted_object'] = json.dumps({'page_id': pagina})
    if orcamento_diario_reais:
        dados['daily_budget'] = int(round(float(orcamento_diario_reais) * 100))
        dados['bid_strategy'] = 'LOWEST_COST_WITHOUT_CAP'
    if inicio:
        dados['start_time'] = inicio
    return _request('POST', f'/{conta or conta_padrao()}/adsets', data=dados)


def subir_imagem(caminho, conta=None):
    """Envia imagem para a biblioteca da conta; devolve o image_hash."""
    with open(caminho, 'rb') as f:
        resp = requests.post(f'{_base()}/{conta or conta_padrao()}/adimages',
                             params={'access_token': _token()},
                             files={'filename': (os.path.basename(caminho), f)}, timeout=120)
    corpo = resp.json()
    if not resp.ok:
        raise RuntimeError(f'Meta: falha ao subir imagem: {corpo.get("error", {}).get("message")}')
    return next(iter(corpo['images'].values()))['hash']


def criar_anuncio(conjunto_id, nome, texto, titulo, image_hash, link,
                  chamada='WHATSAPP_MESSAGE', pagina_id=None, instagram_id=None,
                  conta=None, ignorar_alerta_oab=False):
    """Cria criativo + anuncio PAUSADO. Recusa se conferir_texto_oab() apontar risco,
    salvo ignorar_alerta_oab=True (decisao da Dra. Fabiana)."""
    import json
    alertas = conferir_texto_oab(texto, titulo)
    if alertas and not ignorar_alerta_oab:
        lista = '; '.join(f'"{t}" ({m})' for t, m in alertas)
        raise ValueError(f'Texto com termos de risco para a OAB: {lista}')
    pagina = pagina_id or os.getenv('META_PAGE_ID')
    if not pagina:
        raise RuntimeError('META_PAGE_ID vazio no config/.env')
    spec = {'page_id': pagina,
            'link_data': {'message': texto, 'name': titulo, 'link': link,
                          'image_hash': image_hash,
                          'call_to_action': {'type': chamada, 'value': {'link': link}}}}
    if instagram_id or os.getenv('META_INSTAGRAM_ID'):
        spec['instagram_user_id'] = instagram_id or os.getenv('META_INSTAGRAM_ID')
    conta = conta or conta_padrao()
    criativo = _request('POST', f'/{conta}/adcreatives',
                        data={'name': f'{nome} - criativo',
                              'object_story_spec': json.dumps(spec)})
    return _request('POST', f'/{conta}/ads',
                    data={'name': nome, 'adset_id': conjunto_id, 'status': 'PAUSED',
                          'creative': json.dumps({'creative_id': criativo['id']})})


def pausar(objeto_id):
    """Pausa campanha, conjunto ou anuncio (sempre seguro - para de gastar)."""
    return _request('POST', f'/{objeto_id}', data={'status': 'PAUSED'})


def ativar(objeto_id):
    """ATIVA (passa a gastar). So com pedido explicito da Dra. Fabiana."""
    return _request('POST', f'/{objeto_id}', data={'status': 'ACTIVE'})


# --------------------------------------------------------------------------- teste

if __name__ == '__main__':
    try:
        d = diagnostico()
    except RuntimeError as e:
        print(f'FALHOU: {e}')
        sys.exit(1)
    print(f'Token OK - usuario: {d["usuario"]["name"]} ({d["usuario"]["id"]})')
    print(f'Permissoes: {", ".join(d["permissoes"])}')
    print(f'\nContas de anuncio visiveis: {len(d["contas_anuncio"])}')
    for c in d['contas_anuncio']:
        print(f'  {c["id"]}  {c.get("name")}  status={c.get("account_status")}  '
              f'{c.get("currency")}  gasto total={c.get("amount_spent")}')
    print(f'\nPaginas visiveis: {len(d["paginas"])}')
    for p in d['paginas']:
        ig = p.get('instagram_business_account') or {}
        print(f'  {p["id"]}  {p.get("name")}  Instagram: {ig.get("username", "-")} ({ig.get("id", "-")})')
    if not d['contas_anuncio'] or not d['paginas']:
        print('\nATENCAO: o usuario de sistema ainda nao recebeu os ativos. No Gerenciador de '
              'Negocios: Configuracoes > Usuarios do sistema > AUTOMACOES > Atribuir ativos '
              '(conta de anuncios, pagina e Instagram, com controle total).')
