"""
=============================================================================
  MONITOR DIARIO DE ACORDAOS DO TCU - ALVES CARNEIRO ADVOCACIA
=============================================================================

  Roda todo dia as 17:30 (tarefa "AlvesCarneiro - Acordaos TCU"), le os
  acordaos novos na API de Dados Abertos do TCU, filtra os que interessam ao
  publico do escritorio (temas em config/termos_tcu.py) e os que CITAM CLIENTE,
  pede a IA o entendimento de cada um e envia o relatorio por e-mail.

  Uso:
    python OPERACIONAL/monitor_tcu.py                     # coleta, analisa e envia
    python OPERACIONAL/monitor_tcu.py --sem-enviar        # rodada de coleta (9h-15h)
    python OPERACIONAL/monitor_tcu.py --desde 01/11/2026  # janela maior (1a carga)
    python OPERACIONAL/monitor_tcu.py --sem-ia            # so palavra-chave
    python OPERACIONAL/monitor_tcu.py testar              # testa API do TCU e do Claude
    python OPERACIONAL/monitor_tcu.py fichar 2026-11-03 3 7
        -> vira ficha-rascunho na BASE_CONHECIMENTO os itens 3 e 7 do relatorio
           daquele dia. So os itens que a Dra. Fabiana marcar.

  Fonte: https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos
  (oficial, sem autenticacao). O texto integral vem em RTF do e-TCU.

  Rede: o TCU NAO responde por IPv6 desta maquina e recusa conexao por algum
  tempo apos rajadas de requisicoes. Por isso: IPv4 forcado, pausa entre
  downloads, novas tentativas e FILA - acordao cujo texto nao baixou fica
  pendente e entra no relatorio do dia seguinte. Nada se perde em silencio.

  Clientes: SYNC/espelhamento/snapshot.json (foto do ADVBOX das 07:30) +
  config/tcu_clientes_extra.txt. Nenhuma chamada ao ADVBOX aqui.

  Saidas em OPERACIONAL/relatorios_tcu/ (nao versionado - tem nome de cliente).
  O relatorio e PARA REVISAO da Dra. Fabiana: acordao so vai para peca depois
  de lido no inteiro teor.
=============================================================================
"""
import os
import re
import io
import sys
import json
import time
import socket
import argparse
import unicodedata
from datetime import date, datetime, timedelta

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(RAIZ, 'config', '.env'))

import requests
import urllib3.util.connection as _u3conn

from config import termos_tcu

# O TCU publica AAAA mas nao responde por IPv6 nesta rede: sem isto cada
# conexao espera ~21s pelo IPv6 antes de tentar o IPv4 (e as vezes desiste).
_u3conn.allowed_gai_family = lambda: socket.AF_INET

API_TCU = 'https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos'
API_CLAUDE = 'https://api.anthropic.com/v1/messages'
MODELO = os.getenv('TCU_MODELO', 'claude-sonnet-5-5').strip() or 'claude-sonnet-5-5'

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'relatorios_tcu')
PASTA_TEXTOS = os.path.join(PASTA, '_textos')
ARQ_ESTADO = os.path.join(PASTA, '_estado.json')
SNAPSHOT_ADVBOX = os.path.join(RAIZ, 'SYNC', 'espelhamento', 'snapshot.json')
CLIENTES_EXTRA = os.path.join(RAIZ, 'config', 'tcu_clientes_extra.txt')
PASTA_FICHAS = os.path.join(RAIZ, 'BASE_CONHECIMENTO', 'MILITAR')

PAUSA_TCU = 4            # segundos entre requisicoes ao TCU (o servidor de
                         # documentos derruba a conexao apos ~50 seguidas)
POR_PAGINA = 100
MAX_PAGINAS = 30         # trava de seguranca da paginacao
MAX_DOWNLOADS = 45       # por rodada; o resto fica na fila para a proxima
                         # (rodadas de coleta as 9h/11h/13h/15h + envio as 17:30)
MAX_TENTATIVAS = 6       # downloads falhos antes de desistir do acordao
JANELA_PADRAO = 7        # dias: acordao oficializado com atraso ainda entra
LIMITE_TRECHO = 20000    # caracteres enviados a IA por acordao

ESCRITORIO = os.getenv('ESCRITORIO_NOME', 'Alves Carneiro Advocacia e Consultoria Juridica')


# ============================================================
# UTIL
# ============================================================

def normalizar(texto):
    t = unicodedata.normalize('NFKD', texto or '')
    t = ''.join(c for c in t if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', t).lower().strip()


def _data_br(s):
    return datetime.strptime(s, '%d/%m/%Y').date()


def _ler_json(caminho, padrao):
    if not os.path.exists(caminho):
        return padrao
    with io.open(caminho, encoding='utf-8') as f:
        return json.load(f)


def _gravar_json(caminho, dados):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    tmp = caminho + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    os.replace(tmp, caminho)


# ============================================================
# TCU
# ============================================================

_sessao = requests.Session()
_sessao.headers['Accept'] = 'application/json'


def _get_tcu(url, params=None, tentativas=4):
    """GET com nova tentativa. O TCU recusa conexao por um tempo depois de
    rajadas; esperar mais a cada falha costuma resolver."""
    erro = None
    for n in range(tentativas):
        try:
            r = _sessao.get(url, params=params, timeout=(25, 120))
            if r.status_code == 200:
                time.sleep(PAUSA_TCU)
                return r
            erro = 'HTTP %d' % r.status_code
        except requests.RequestException as e:
            erro = '%s' % type(e).__name__
        time.sleep(10 * (n + 1))
    raise ConnectionError('TCU nao respondeu (%s): %s' % (erro, url))


def listar_acordaos(desde):
    """Acordaos com sessao a partir de `desde`. A API devolve do mais recente
    para o mais antigo e nao filtra por data: pagina ate passar da janela."""
    achados = []
    for pagina in range(MAX_PAGINAS):
        r = _get_tcu(API_TCU, {'inicio': pagina * POR_PAGINA, 'quantidade': POR_PAGINA})
        lote = r.json() or []
        if not lote:
            break
        antigos = 0
        for a in lote:
            try:
                d = _data_br(a.get('dataSessao') or '')
            except ValueError:
                d = None
            if d and d < desde:
                antigos += 1
                continue
            achados.append(a)
        # A API entrega em lotes por sessao, nao em ordem estrita de data (a 1a
        # Camara de uma semana pode vir antes do Plenario da seguinte): so para
        # quando a pagina INTEIRA ja e anterior a janela.
        if antigos == len(lote):
            break
    return achados


def rtf_para_texto(rtf):
    """Conversor RTF -> texto suficiente para o RTF do e-TCU (sem dependencia)."""
    padrao = re.compile(r"\\([a-z]{1,32})(-?\d{1,10})?[ ]?|\\'([0-9a-f]{2})|\\([^a-z])|([{}])|[\r\n]+|(.)",
                        re.I | re.S)
    destinos = {
        'fonttbl', 'colortbl', 'stylesheet', 'info', 'pict', 'object', 'header', 'footer',
        'headerl', 'headerr', 'headerf', 'footerl', 'footerr', 'footerf', 'listtable',
        'listoverridetable', 'rsidtbl', 'generator', 'xmlnstbl', 'themedata', 'datastore',
        'latentstyles', 'colorschememapping', 'fldinst', 'shpinst', 'nonshppict', 'bkmkstart',
        'bkmkend', 'field', 'filetbl', 'revtbl', 'pgdsctbl', 'mmathPr', 'wgrffmtfilter',
        'author', 'operator', 'title', 'subject', 'keywords', 'comment', 'doccomm', 'company',
        'creatim', 'revtim', 'printim', 'buptim', 'userprops', 'docvar', 'listtext', 'pntext',
        'pntxta', 'pntxtb', 'ftnsep', 'ftnsepc', 'aftnsep', 'aftnsepc', 'atnid', 'atnauthor',
        'annotation', 'xe', 'tc', 'blipuid', 'passwordhash', 'protusertbl', 'mmathPict',
    }
    especiais = {'par': '\n', 'sect': '\n\n', 'page': '\n\n', 'line': '\n', 'tab': '\t',
                 'cell': ' | ', 'row': '\n', 'emdash': '\u2014', 'endash': '\u2013',
                 'bullet': '\u2022', 'lquote': '\u2018', 'rquote': '\u2019',
                 'ldblquote': '\u201c', 'rdblquote': '\u201d'}
    pilha, ignorar, uc, pular, saida = [], False, 1, 0, []
    for m in padrao.finditer(rtf):
        palavra, arg, hexa, simb, chave, ch = m.groups()
        if chave:
            pular = 0
            if chave == '{':
                pilha.append((uc, ignorar))
            elif pilha:
                uc, ignorar = pilha.pop()
        elif simb:
            pular = 0
            if simb == '*':
                ignorar = True
            elif not ignorar:
                if simb == '~':
                    saida.append(' ')
                elif simb in '{}' or simb == chr(92):
                    saida.append(simb)
        elif palavra:
            pular = 0
            if palavra in destinos:
                ignorar = True
            elif ignorar:
                pass
            elif palavra in especiais:
                saida.append(especiais[palavra])
            elif palavra == 'uc':
                uc = int(arg)
            elif palavra == 'u':
                c = int(arg)
                saida.append(chr(c + 0x10000 if c < 0 else c))
                pular = uc
        elif hexa:
            if pular:
                pular -= 1
            elif not ignorar:
                saida.append(bytes([int(hexa, 16)]).decode('cp1252', errors='replace'))
        elif ch:
            if pular:
                pular -= 1
            elif not ignorar:
                saida.append(ch)
    texto = ''.join(saida).replace('\xa0', ' ')
    texto = re.sub(r'[ \t]+', ' ', texto)
    return re.sub(r'\n\s*\n+', '\n\n', texto).strip()


class FormatoDesconhecido(ValueError):
    """Arquivo baixou mas nao e RTF, DOCX nem PDF - nao e bloqueio do TCU."""


def conteudo_para_texto(dados):
    """O formato se decide pelo CONTEUDO: o e-TCU entrega .docx com nome .rtf."""
    if dados[:5] == b'{\\rtf':
        return rtf_para_texto(dados.decode('latin-1'))
    if dados[:2] == b'PK':
        import docx
        doc = docx.Document(io.BytesIO(dados))
        partes = [p.text for p in doc.paragraphs]
        for tabela in doc.tables:
            for linha in tabela.rows:
                partes.append(' | '.join(c.text for c in linha.cells))
        return re.sub(r'\n\s*\n+', '\n\n', '\n'.join(partes)).strip()
    if dados[:5] == b'%PDF-':
        import pymupdf
        with pymupdf.open(stream=dados, filetype='pdf') as d:
            texto = '\n'.join(p.get_text() for p in d)
        texto = re.sub(r'[ \t]+', ' ', texto)
        return re.sub(r'\n\s*\n+', '\n\n', texto).strip()
    raise FormatoDesconhecido('formato desconhecido (inicio %r)' % dados[:8])


def texto_do_acordao(a):
    """Texto integral, com cache em disco (o RTF nao muda depois de oficializado)."""
    caminho = os.path.join(PASTA_TEXTOS, '%s.txt' % a['key'])
    if os.path.exists(caminho):
        with io.open(caminho, encoding='utf-8') as f:
            return f.read()
    url = a.get('urlArquivo') or a.get('urlArquivoPdf')
    # Acordao com relatorio e voto vem do SAGAS, cujo servlet de RTF nao
    # responde (timeout de 120s); o PDF do mesmo documento baixa normalmente.
    if url and '/sagas/' in url and a.get('urlArquivoPdf'):
        url = a['urlArquivoPdf']
    if not url:
        raise ValueError('acordao sem urlArquivo')
    # O link da API (/sisdoc/) so redireciona para /egestao/: ir direto poupa
    # metade das requisicoes ao servidor que bloqueia.
    r = _get_tcu(url.replace('/sisdoc/ObterDocumentoSisdoc', '/egestao/ObterDocumentoSisdoc'),
                 tentativas=2)
    texto = conteudo_para_texto(r.content)
    os.makedirs(PASTA_TEXTOS, exist_ok=True)
    with io.open(caminho, 'w', encoding='utf-8') as f:
        f.write(texto)
    return texto


# ============================================================
# CLIENTES
# ============================================================

def carregar_clientes():
    """[(nome_exibicao, nome_normalizado, cpf_digitos, n_palavras)] - so pessoa
    fisica com nome de 2+ palavras. Nome de 2 palavras sai marcado para conferir."""
    brutos = []
    snap = _ler_json(SNAPSHOT_ADVBOX, {})
    for c in (snap.get('clientes') or {}).values():
        brutos.append((c.get('name') or '', re.sub(r'\D', '', c.get('identification') or '')))
    if os.path.exists(CLIENTES_EXTRA):
        with io.open(CLIENTES_EXTRA, encoding='utf-8') as f:
            for linha in f:
                linha = linha.split('#', 1)[0].strip()
                if linha:
                    nome, _, cpf = linha.partition(';')
                    brutos.append((nome.strip(), re.sub(r'\D', '', cpf)))

    ignorar = [re.compile(p) for p in termos_tcu.NOMES_IGNORADOS]
    vistos, clientes = set(), []
    for nome, cpf in brutos:
        # no TCU o instituidor aparece pelo nome, nao como "espolio de"
        n = re.sub(r'^espolio d[aeo]s? ', '', normalizar(nome))
        n = re.sub(r'[^a-z ]', ' ', n).split()
        palavras = [p for p in n if len(p) >= 2 and p not in termos_tcu.CONECTIVOS_NOME]
        n = ' '.join(n)
        if len(palavras) < 2 or any(len(p) < 3 for p in palavras[:1] + palavras[-1:]) \
                or n in vistos or any(p.search(n) for p in ignorar):
            continue
        vistos.add(n)
        clientes.append((nome.strip(), n, cpf if len(cpf) == 11 else '', len(palavras)))
    return clientes, bool(snap)


def clientes_citados(texto_norm, texto_bruto, clientes):
    """Cliente citado por nome completo (palavra inteira) ou CPF completo."""
    cpfs = {re.sub(r'\D', '', c) for c in re.findall(r'\d{3}\.\d{3}\.\d{3}-\d{2}', texto_bruto)}
    achados = []
    for nome, n, cpf, n_palavras in clientes:
        por_cpf = bool(cpf) and cpf in cpfs
        por_nome = re.search(r'\b%s\b' % re.escape(n), texto_norm) is not None
        if por_cpf or por_nome:
            achados.append({'nome': nome,
                            'por': 'CPF' if por_cpf else 'nome',
                            'conferir': not por_cpf and n_palavras < 3})
    return achados


# ============================================================
# TRIAGEM POR PALAVRA-CHAVE
# ============================================================

_TEMAS = {t: [re.compile(p) for p in ps] for t, ps in termos_tcu.TEMAS.items()}
_PESSOAL = [re.compile(p) for p in termos_tcu.INDICIOS_ATO_PESSOAL]


def triar(texto_norm):
    """{tema: [posicoes]} dos temas que bateram."""
    temas = {}
    for tema, padroes in _TEMAS.items():
        pos = [m.start() for p in padroes for m in p.finditer(texto_norm)]
        if pos:
            temas[tema] = sorted(pos)
    return temas


def trechos_relevantes(texto_norm, texto_bruto, temas, citados):
    """Cabecalho + janelas em volta dos achados. O texto normalizado tem o mesmo
    comprimento do bruto so por aproximacao, entao as janelas sao largas."""
    if len(texto_bruto) <= LIMITE_TRECHO:
        return texto_bruto
    escala = len(texto_bruto) / max(len(texto_norm), 1)
    posicoes = [p for ps in temas.values() for p in ps[:6]]
    for c in citados:
        m = re.search(re.escape(normalizar(c['nome'])), texto_norm)
        if m:
            posicoes.append(m.start())
    janelas = [(0, 2500)]
    for p in sorted(posicoes):
        c = int(p * escala)
        janelas.append((max(0, c - 1200), c + 1200))
    janelas.sort()
    unidas = []
    for ini, fim in janelas:
        if unidas and ini <= unidas[-1][1]:
            unidas[-1] = (unidas[-1][0], max(unidas[-1][1], fim))
        else:
            unidas.append((ini, fim))
    partes, total = [], 0
    for ini, fim in unidas:
        bloco = texto_bruto[ini:fim]
        if total + len(bloco) > LIMITE_TRECHO:
            break
        partes.append(bloco)
        total += len(bloco)
    return '\n[...]\n'.join(partes)


# ============================================================
# ANALISE PELA IA
# ============================================================

PROMPT_SISTEMA = """Voce analisa acordaos do Tribunal de Contas da Uniao para o escritorio \
Alves Carneiro Advocacia (Rio de Janeiro), que defende MILITARES das Forcas Armadas, \
PENSIONISTAS militares e APOSENTADOS. Interessam: controle de legalidade de atos de pessoal \
(reforma, reserva, pensao militar), habilitacao inicial de pensao (Lei 3.765/60, MP 2.215-10, \
filhas, companheira, Acordao 2.225/2019), cumulacao de duas aposentadorias com pensao militar, \
cumulacao de cargo militar com professor ou medico/profissional de saude, fator redutor e \
abate-teto, decadencia (Tema 445 STF), boa-fe e dispensa de devolucao (Sumula 106 TCU), \
isencao de IR por molestia grave.

Responda SO com um objeto JSON, sem texto fora dele:
{"tema": "assunto em ate 8 palavras",
 "entendimento": "o que o TCU decidiu e por que, em 2 a 3 frases objetivas",
 "posicao": "favoravel" | "desfavoravel" | "neutro",
 "relevancia": "alta" | "media" | "baixa",
 "fundamentos": ["dispositivos, sumulas e precedentes citados pelo proprio acordao"],
 "uso_sugerido": "em que tipo de caso do escritorio isto serve, numa frase",
 "clientes": [{"nome": "...", "situacao": "o que o acordao decidiu sobre esta pessoa"}]}

Regras:
- "posicao" e do ponto de vista do militar/pensionista/aposentado.
- "relevancia" baixa: registro rotineiro de ato legal, sem tese nem fundamento novo. \
Alta: ilegalidade, negativa de registro, tese sobre cumulacao, redutor, habilitacao, \
decadencia ou devolucao.
- "clientes": preencher so para os nomes listados como clientes que aparecem no texto; \
lista vazia se nao houver.
- Nao invente fundamento: so o que esta no texto. O texto pode vir em trechos ("[...]")."""


def _chave_claude():
    return os.getenv('ANTHROPIC_API_KEY', '').strip()


def analisar_ia(a, trecho, citados):
    nomes = ', '.join(c['nome'] for c in citados) or 'nenhum'
    conteudo = ('%s\nRelator: %s | Sessao: %s\nClientes do escritorio procurados neste texto: %s\n\n'
                'TEXTO DO ACORDAO:\n%s' % (a.get('titulo'), a.get('relator'),
                                           a.get('dataSessao'), nomes, trecho))
    r = requests.post(API_CLAUDE, timeout=(20, 180), headers={
        'x-api-key': _chave_claude(), 'anthropic-version': '2023-06-01',
        'content-type': 'application/json'}, json={
        'model': MODELO, 'max_tokens': 1200, 'system': PROMPT_SISTEMA,
        'messages': [{'role': 'user', 'content': conteudo}]})
    if r.status_code != 200:
        raise RuntimeError('Claude HTTP %d: %s' % (r.status_code, r.text[:300]))
    texto = ''.join(b.get('text', '') for b in r.json().get('content', []))
    m = re.search(r'\{.*\}', texto, re.S)
    if not m:
        raise ValueError('resposta da IA sem JSON')
    return json.loads(m.group(0))


# ============================================================
# COLETA
# ============================================================

def coletar(desde, usar_ia=True, max_downloads=MAX_DOWNLOADS):
    estado = _ler_json(ARQ_ESTADO, {'vistos': {}, 'fila': {}})
    vistos, fila = estado['vistos'], estado['fila']
    clientes, tem_snapshot = carregar_clientes()
    avisos = []
    if not tem_snapshot:
        avisos.append('snapshot do ADVBOX nao encontrado - clientes nao foram procurados')

    print('Consultando a API do TCU (sessoes desde %s)...' % desde.strftime('%d/%m/%Y'))
    lista = listar_acordaos(desde)
    novos = [a for a in lista if a['key'] not in vistos and a['key'] not in fila]
    for a in novos:
        fila[a['key']] = a
    print('  %d acordao(s) na janela, %d novo(s), %d na fila para ler'
          % (len(lista), len(novos), len(fila)))

    itens, falhas_texto, falhas_ia, descartados, seguidas = [], 0, 0, 0, 0
    desistidos = []
    ia_ativa = usar_ia and bool(_chave_claude())
    # Acordao de interesse que saiu sem resumo (sem chave ou IA falhou) espera
    # aqui e e reanalisado na 1a execucao com IA - o texto ja esta em cache.
    sem_ia = estado.setdefault('sem_ia', {})
    if ia_ativa and sem_ia:
        print('  %d acordao(s) de dias anteriores aguardando resumo da IA' % len(sem_ia))
        fila.update(sem_ia)
        sem_ia.clear()
    if usar_ia and not ia_ativa:
        avisos.append('ANTHROPIC_API_KEY vazia no config/.env - relatorio so por palavra-chave '
                      '(os acordaos de interesse serao resumidos quando a chave for preenchida)')

    for n, (key, a) in enumerate(list(fila.items())):
        if n >= max_downloads:
            avisos.append('limite de %d downloads atingido - o resto segue na fila' % max_downloads)
            break
        try:
            texto = texto_do_acordao(a)
        except Exception as e:
            falhas_texto += 1
            print('  [fila] %s: %s' % (a.get('titulo'), e), flush=True)
            # O que falhou vai para o FIM da fila: sem isto os mesmos 3 da frente
            # falhavam em toda rodada e travaram a fila de 05 a 11/11/2026.
            a['_tentativas'] = a.get('_tentativas', 0) + 1
            del fila[key]
            if a['_tentativas'] >= MAX_TENTATIVAS:
                desistidos.append(a)
                vistos[key] = date.today().isoformat()
            else:
                fila[key] = a
            if isinstance(e, FormatoDesconhecido):
                continue            # arquivo estranho nao e sinal de bloqueio
            seguidas += 1
            if seguidas >= 3:
                # Servidor de documentos bloqueou: insistir so prolonga o bloqueio.
                avisos.append('servidor de documentos do TCU parou de responder - %d acordao(s) '
                              'seguem na fila para a proxima rodada' % len(fila))
                break
            continue
        seguidas = 0

        if n and n % 20 == 0:
            _gravar_json(ARQ_ESTADO, estado)   # execucao interrompida nao relê tudo
            print('  ... %d lidos' % n, flush=True)
        tnorm = normalizar(texto)
        temas = triar(tnorm)
        citados = clientes_citados(tnorm, texto, clientes)
        del fila[key]
        vistos[key] = date.today().isoformat()
        if not temas and not citados:
            descartados += 1
            continue

        item = {k: a.get(k) for k in ('key', 'titulo', 'tipo', 'numeroAcordao', 'anoAcordao',
                                      'colegiado', 'dataSessao', 'relator', 'urlAcordao',
                                      'urlArquivoPdf')}
        item['temas'] = list(temas)
        item['clientes_citados'] = citados
        item['ato_pessoal'] = any(p.search(tnorm) for p in _PESSOAL)
        if ia_ativa:
            try:
                item['ia'] = analisar_ia(a, trechos_relevantes(tnorm, texto, temas, citados), citados)
            except Exception as e:
                falhas_ia += 1
                item['ia_erro'] = str(e)[:200]
                print('  [IA] %s: %s' % (a.get('titulo'), e))
                if falhas_ia >= 3 and not any('ia' in i for i in itens):
                    ia_ativa = False   # 3 falhas e nenhum acerto: chave/modelo errado
                    avisos.append('IA desligada nesta execucao apos 3 falhas: %s' % str(e)[:150])
        if usar_ia and 'ia' not in item:
            sem_ia[key] = a
        itens.append(item)
        print('  + %s - %s%s' % (item['titulo'], ', '.join(item['temas']) or '-',
                                 ' | CLIENTE: ' + ', '.join(c['nome'] for c in citados)
                                 if citados else ''))

    # memoria de vistos: so os ultimos 60 dias (a janela de busca e bem menor)
    corte = (date.today() - timedelta(days=60)).isoformat()
    estado['vistos'] = {k: v for k, v in vistos.items() if v >= corte}
    estado['fila'] = fila
    _gravar_json(ARQ_ESTADO, estado)

    for a in desistidos:
        avisos.append('texto nao baixou apos %d tentativas - conferir a mao: %s (%s)'
                      % (MAX_TENTATIVAS, a.get('titulo'), a.get('urlAcordao')))
    if falhas_ia:
        avisos.append('IA falhou em %d acordao(s) - aparecem so com a palavra-chave' % falhas_ia)
    return {'hoje': date.today(), 'itens': ordenar(itens), 'lidos': len(lista),
            'descartados': descartados, 'fila': len(fila), 'avisos': avisos,
            'ia': ia_ativa, 'n_clientes': len(clientes)}


_PESO = {'alta': 0, 'media': 1, 'baixa': 2}


def _ordem(i):
    rel = (i.get('ia') or {}).get('relevancia', 'media')
    return (0 if i['clientes_citados'] else 1, _PESO.get(rel, 1), i.get('colegiado') or '',
            -int(i.get('numeroAcordao') or 0))


def ordenar(itens, primeiro=1):
    """Cliente citado primeiro; depois relevancia; e numera o relatorio."""
    itens = sorted(itens, key=_ordem)
    for n, i in enumerate(itens, primeiro):
        i['n'] = n
    return itens


# ============================================================
# RELATORIO
# ============================================================

MESES = ['', 'janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho', 'julho',
         'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
ROTULO_POS = {'favoravel': 'FAVORAVEL', 'desfavoravel': 'DESFAVORAVEL', 'neutro': 'neutro'}


def _secoes(itens):
    com_cliente = [i for i in itens if i['clientes_citados']]
    resto = [i for i in itens if not i['clientes_citados']]
    destaque = [i for i in resto if (i.get('ia') or {}).get('relevancia', 'media') != 'baixa']
    rotina = [i for i in resto if (i.get('ia') or {}).get('relevancia') == 'baixa']
    return (('CLIENTES DO ESCRITORIO CITADOS', com_cliente),
            ('ENTENDIMENTOS RELEVANTES', destaque),
            ('ROTINA (registro sem tese nova)', rotina))


def montar_texto(d):
    hoje = d['hoje']
    L = ['=' * 72, '  ACORDAOS DO TCU - %d de %s de %d' % (hoje.day, MESES[hoje.month], hoje.year),
         '  %s' % ESCRITORIO, '=' * 72, '',
         '  %d acordao(s) lido(s), %d de interesse, %d descartado(s)%s'
         % (d['lidos'], len(d['itens']), d['descartados'],
            ', %d na fila' % d['fila'] if d['fila'] else ''), '']
    for a in d['avisos']:
        L.append('  AVISO: %s' % a)
    if d['avisos']:
        L.append('')
    if not d['itens']:
        L.append('  Nenhum acordao de interesse hoje.')
    for titulo, lista in _secoes(d['itens']):
        if not lista:
            continue
        L += ['', '-' * 72, '  %s (%d)' % (titulo, len(lista)), '-' * 72]
        for i in lista:
            ia = i.get('ia') or {}
            L.append('')
            L.append('[%d] %s - %s - Rel. %s' % (i['n'], i['titulo'], i['dataSessao'], i['relator']))
            if ia:
                L.append('    %s | %s | relevancia %s' % (ia.get('tema', ''),
                         ROTULO_POS.get(ia.get('posicao'), ia.get('posicao', '')),
                         ia.get('relevancia', '')))
                L.append('    %s' % ia.get('entendimento', ''))
                if ia.get('fundamentos'):
                    L.append('    Fundamentos: %s' % '; '.join(ia['fundamentos']))
                if ia.get('uso_sugerido'):
                    L.append('    Uso: %s' % ia['uso_sugerido'])
            else:
                L.append('    Temas: %s' % ', '.join(i['temas']))
            for c in i['clientes_citados']:
                sit = next((x.get('situacao') for x in ia.get('clientes', [])
                            if normalizar(x.get('nome')) == normalizar(c['nome'])), '')
                L.append('    CLIENTE: %s (por %s%s)%s' % (c['nome'], c['por'],
                         ', homonimo? conferir' if c['conferir'] else '',
                         ' - %s' % sit if sit else ''))
            L.append('    %s' % i['urlAcordao'])
    L += ['', '=' * 72,
          '  Para virar ficha na BASE_CONHECIMENTO, pedir: "ficha os itens 3 e 7 do',
          '  relatorio do TCU de %s" (ou: python OPERACIONAL/monitor_tcu.py fichar %s 3 7).'
          % (hoje.strftime('%d/%m'), hoje.isoformat()),
          '  Resumo feito por IA: ler o inteiro teor antes de citar em peca.',
          '  PRONTO PARA REVISAO DA DRA. FABIANA.']
    return '\n'.join(L)


def _esc(s):
    return (str(s or '')).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def montar_html(d):
    hoje = d['hoje']
    cor = {'favoravel': '#1b7a3a', 'desfavoravel': '#b00020', 'neutro': '#666'}
    H = ['<html><body style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#222;">',
         '<h2 style="color:#1f3864;margin:0 0 4px 0;">Acordaos do TCU &mdash; %s</h2>'
         % hoje.strftime('%d/%m/%Y'),
         '<p style="margin:0 0 14px 0;color:#555;">%d lido(s) &middot; <strong>%d de interesse'
         '</strong> &middot; %d descartado(s)%s</p>'
         % (d['lidos'], len(d['itens']), d['descartados'],
            ' &middot; %d na fila' % d['fila'] if d['fila'] else '')]
    for a in d['avisos']:
        H.append('<p style="background:#fff4e5;border-left:4px solid #e69500;padding:6px 10px;'
                 'margin:4px 0;">%s</p>' % _esc(a))
    if not d['itens']:
        H.append('<p>Nenhum acordao de interesse hoje.</p>')
    for titulo, lista in _secoes(d['itens']):
        if not lista:
            continue
        H.append('<h3 style="background:#DBE5F1;padding:6px 10px;margin:22px 0 8px 0;'
                 'font-size:15px;"><em>%s (%d)</em></h3>' % (_esc(titulo), len(lista)))
        for i in lista:
            ia = i.get('ia') or {}
            H.append('<div style="margin:0 0 14px 0;padding-bottom:10px;border-bottom:1px solid #e6e6e6;">')
            H.append('<p style="margin:0;"><strong>[%d] <a href="%s">%s</a></strong> '
                     '<span style="color:#666;">&middot; %s &middot; Rel. %s</span></p>'
                     % (i['n'], _esc(i['urlAcordao']), _esc(i['titulo']), _esc(i['dataSessao']),
                        _esc(i['relator'])))
            if ia:
                pos = ia.get('posicao', '')
                H.append('<p style="margin:3px 0;"><strong>%s</strong> &middot; '
                         '<span style="color:%s;font-weight:bold;">%s</span> &middot; '
                         'relevancia %s</p>' % (_esc(ia.get('tema')), cor.get(pos, '#666'),
                                                _esc(ROTULO_POS.get(pos, pos)),
                                                _esc(ia.get('relevancia'))))
                H.append('<p style="margin:3px 0;">%s</p>' % _esc(ia.get('entendimento')))
                if ia.get('fundamentos'):
                    H.append('<p style="margin:3px 0;color:#555;font-size:12px;">Fundamentos: %s</p>'
                             % _esc('; '.join(ia['fundamentos'])))
                if ia.get('uso_sugerido'):
                    H.append('<p style="margin:3px 0;color:#555;font-size:12px;">Uso: %s</p>'
                             % _esc(ia['uso_sugerido']))
            else:
                H.append('<p style="margin:3px 0;color:#555;">Temas: %s</p>' % _esc(', '.join(i['temas'])))
            for c in i['clientes_citados']:
                sit = next((x.get('situacao') for x in ia.get('clientes', [])
                            if normalizar(x.get('nome')) == normalizar(c['nome'])), '')
                H.append('<p style="margin:3px 0;color:#b00020;"><strong>CLIENTE: %s</strong> '
                         '(por %s%s)%s</p>' % (_esc(c['nome']), c['por'],
                                               ', homonimo? conferir' if c['conferir'] else '',
                                               ' &mdash; %s' % _esc(sit) if sit else ''))
            H.append('</div>')
    H.append('<p style="margin-top:22px;color:#888;font-size:11px;border-top:1px solid #ddd;'
             'padding-top:10px;">Para virar ficha na Base de Conhecimento, responda com os '
             'numeros dos itens (ex.: "ficha os itens 3 e 7 do relatorio do TCU de %s"). '
             'Resumo feito por IA a partir do texto oficial do TCU: ler o inteiro teor antes de '
             'citar em peca. <strong>PRONTO PARA REVISAO DA DRA. FABIANA.</strong></p>'
             % hoje.strftime('%d/%m'))
    H.append('</body></html>')
    return '\n'.join(H)


# ============================================================
# FICHAR (so os itens marcados)
# ============================================================

def _slug(s):
    return re.sub(r'[^a-z0-9]+', '-', normalizar(s)).strip('-')


def fichar(dia, numeros):
    arq = os.path.join(PASTA, 'tcu-%s.json' % dia)
    if not os.path.exists(arq):
        print('Relatorio de %s nao encontrado em %s' % (dia, PASTA))
        return 1
    itens = {i['n']: i for i in _ler_json(arq, {}).get('itens', [])}
    os.makedirs(PASTA_FICHAS, exist_ok=True)
    criadas = 0
    for n in numeros:
        i = itens.get(n)
        if not i:
            print('  [%d] nao existe no relatorio de %s' % (n, dia))
            continue
        ia = i.get('ia') or {}
        nome = 'tcu-acordao-%s-%s-%s.md' % (i['numeroAcordao'], i['anoAcordao'], _slug(i['colegiado']))
        caminho = os.path.join(PASTA_FICHAS, nome)
        if os.path.exists(caminho):
            print('  [%d] ja existe: %s - nao sobrescrevi' % (n, caminho))
            continue
        # A ficha e versionada: nome de cliente NAO entra aqui (fica so no relatorio).
        fundamentos = '\n'.join('| %s | citado no acordao | conferir |' % f
                                for f in ia.get('fundamentos', [])) or '| <...> | <...> | <...> |'
        cliente = ('\n> Este acordao cita cliente do escritorio - ver o relatorio do TCU de %s, '
                   'item %d.\n' % (dia, n)) if i['clientes_citados'] else ''
        conteudo = """---
titulo: %(titulo)s
area: MILITAR
origem:
  tipo: jurisprudencia
  autor: TCU - Min. %(relator)s
  instituicao: Tribunal de Contas da Uniao - %(colegiado)s
  data: %(sessao)s
original: %(url)s
extraido: OPERACIONAL/relatorios_tcu/_textos/%(key)s.txt
status: RASCUNHO
conferida_por: -
conferida_em: -
---

# %(titulo)s

## Do que trata
%(tema)s. %(entendimento)s
%(cliente)s
Posicao para o militar/pensionista: **%(posicao)s**. Resumo gerado por IA no monitor
diario do TCU - conferir no inteiro teor antes de usar.

## Teses aproveitaveis

### 1. %(tema)s
- **Quando cabe:** %(uso)s
- **Fundamento:** %(fund_linha)s
- **Como se argumenta:** <preencher na conferencia>
- **Contra-argumento tipico da Uniao:** <preencher na conferencia>

## Dispositivos citados
| Dispositivo | O que estabelece | Onde usar |
|---|---|---|
%(fundamentos)s

## Jurisprudencia citada
| Tribunal / Tema | Ementa ou tese fixada (resumo) | Verificado? |
|---|---|---|
| TCU, %(titulo)s | %(entendimento)s | nao |

> Fonte oficial (TCU), mas o resumo e da IA: marcar `sim` so depois de ler o inteiro teor.

## Armadilhas e prazos
<preencher na conferencia>

## Observacoes da Dra. Fabiana
<preencher na conferencia>
""" % {'titulo': i['titulo'], 'relator': i['relator'], 'colegiado': i['colegiado'],
       'sessao': i['dataSessao'], 'url': i['urlAcordao'], 'key': i['key'],
       'tema': ia.get('tema') or ', '.join(i['temas']),
       'entendimento': ia.get('entendimento') or '<ler o acordao e resumir>',
       'cliente': cliente, 'posicao': ia.get('posicao') or 'a definir',
       'uso': ia.get('uso_sugerido') or '<preencher>',
       'fund_linha': '; '.join(ia.get('fundamentos', [])) or '<preencher>',
       'fundamentos': fundamentos}
        with io.open(caminho, 'w', encoding='utf-8', newline='\n') as f:
            f.write(conteudo)
        criadas += 1
        print('  [%d] ficha criada: %s' % (n, os.path.relpath(caminho, RAIZ)))
    if criadas:
        indice = os.path.join(RAIZ, 'UTILS', 'gerar_indice_teses.py')
        if os.path.exists(indice):
            os.system('"%s" -X utf8 "%s"' % (sys.executable, indice))
    return 0


# ============================================================
# TESTE
# ============================================================

def testar():
    print('1. API do TCU...')
    r = _get_tcu(API_TCU, {'inicio': 0, 'quantidade': 1})
    a = r.json()[0]
    print('   OK - mais recente: %s (%s)' % (a['titulo'], a['dataSessao']))
    print('2. Texto integral (RTF)...')
    t = texto_do_acordao(a)
    print('   OK - %d caracteres. Inicio:\n   %s' % (len(t), t[:300].replace('\n', ' ')))
    print('3. Clientes...')
    cl, snap = carregar_clientes()
    print('   %d cliente(s) para procurar%s' % (len(cl), '' if snap else ' (SEM snapshot do ADVBOX)'))
    print('4. API do Claude (%s)...' % MODELO)
    if not _chave_claude():
        print('   ANTHROPIC_API_KEY vazia no config/.env')
        return 1
    tn = normalizar(t)
    print('   OK - %s' % json.dumps(analisar_ia(a, trechos_relevantes(tn, t, triar(tn), []), []),
                                     ensure_ascii=False)[:400])
    return 0


# ============================================================
# MAIN
# ============================================================

def main():
    ap = argparse.ArgumentParser(description='Monitor diario de acordaos do TCU')
    ap.add_argument('comando', nargs='?', default='rodar', choices=('rodar', 'testar', 'fichar'))
    ap.add_argument('args', nargs='*', help='fichar: AAAA-MM-DD n1 n2 ...')
    ap.add_argument('--desde', help='DD/MM/AAAA (padrao: ultimos %d dias)' % JANELA_PADRAO)
    ap.add_argument('--sem-enviar', action='store_true', help='gera e salva, nao envia')
    ap.add_argument('--sem-ia', action='store_true', help='so triagem por palavra-chave')
    ap.add_argument('--max', type=int, default=MAX_DOWNLOADS, help='maximo de downloads')
    args = ap.parse_args()

    if args.comando == 'testar':
        return testar()
    if args.comando == 'fichar':
        if len(args.args) < 2:
            ap.error('uso: fichar AAAA-MM-DD n1 [n2 ...]')
        return fichar(args.args[0], [int(x) for x in args.args[1:]])

    desde = _data_br(args.desde) if args.desde else date.today() - timedelta(days=JANELA_PADRAO)
    try:
        d = coletar(desde, usar_ia=not args.sem_ia, max_downloads=args.max)
    except ConnectionError as e:
        # Nem a listagem saiu: avisa por e-mail mesmo assim, para nao parecer
        # que "nao houve acordao".
        d = {'hoje': date.today(), 'itens': [], 'lidos': 0, 'descartados': 0, 'fila': 0,
             'avisos': ['TCU fora do ar: %s. Tenta de novo amanha, sem perder nada.' % e],
             'ia': False, 'n_clientes': 0}

    texto, html = montar_texto(d), montar_html(d)
    print()
    print(texto)

    os.makedirs(PASTA, exist_ok=True)
    dia = d['hoje'].isoformat()
    # Reexecucao no mesmo dia SOMA aos itens ja salvos, sem renumerar: o numero
    # que ja saiu por e-mail e o que a Dra. Fabiana usa para pedir a ficha.
    arq_json = os.path.join(PASTA, 'tcu-%s.json' % dia)
    anteriores = _ler_json(arq_json, {}).get('itens', [])
    if anteriores:
        velhos = {i['key']: i for i in anteriores}
        for i in d['itens']:
            if i['key'] in velhos:      # reanalisado (ex.: agora com IA): mesmo numero
                i['n'] = velhos[i['key']]['n']
                velhos[i['key']] = i
        novos = ordenar([i for i in d['itens'] if i['key'] not in {a['key'] for a in anteriores}],
                        primeiro=max(i['n'] for i in anteriores) + 1)
        d['itens'] = sorted(list(velhos.values()) + novos, key=_ordem)
        texto, html = montar_texto(d), montar_html(d)
    _gravar_json(arq_json, {'gerado_em': datetime.now().isoformat(timespec='seconds'),
                            'itens': d['itens'], 'avisos': d['avisos']})
    caminho = os.path.join(PASTA, 'tcu-%s.txt' % dia)
    with io.open(caminho, 'w', encoding='utf-8', newline='\n') as f:
        f.write(texto + '\n')
    print('\n  Copia salva em: %s' % caminho)

    n_cli = sum(1 for i in d['itens'] if i['clientes_citados'])
    assunto = 'Acordaos TCU - %s - %d de interesse%s' % (
        d['hoje'].strftime('%d/%m/%Y'), len(d['itens']),
        ' (%d com CLIENTE)' % n_cli if n_cli else '')
    if args.sem_enviar:
        print('  --sem-enviar: nada enviado. Assunto: %s' % assunto)
        return 0

    import prazos_diario
    cfg, faltando = prazos_diario._config_smtp()
    para = os.getenv('TCU_EMAIL_PARA', '').strip()
    if para:
        cfg['para'] = para
        faltando = [f for f in faltando if f != 'para']
    if faltando:
        rotulos = {'host': 'SMTP_HOST', 'user': 'SMTP_USER', 'senha': 'SMTP_PASSWORD',
                   'para': 'TCU_EMAIL_PARA'}
        print('\n  AVISO: e-mail NAO enviado - falta no config/.env: %s'
              % ', '.join(rotulos[f] for f in faltando))
        return 1
    try:
        destinos = prazos_diario.enviar_email(assunto, texto, html, cfg)
        print('\n  E-mail enviado para: %s' % ', '.join(destinos))
    except Exception as e:
        print('\n  ERRO ao enviar e-mail: %s: %s' % (type(e).__name__, e))
        print('  O relatorio esta salvo em %s - nada foi perdido.' % caminho)
        return 1
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.exit(main())
