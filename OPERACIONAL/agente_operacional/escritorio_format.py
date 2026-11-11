"""
Motor de formatacao FIEL ao padrao de pecas do escritorio.

Especificacoes MEDIDAS nas pecas reais protocoladas pela Dra. Fabiana
(fonte: "emenda de uniao estavel (peca-modelo)", militar/
familia, no timbrado Alves Carneiro). Substitui o padrao Ebrima 12pt anterior, que
vinha das iniciais antigas do escritorio. Ver .claude/rules/padroes-documentos.md.
  Pagina A4
  Margens: top 2.5cm | bottom 2.5cm | left 3cm | right 3cm
  Distancia do cabecalho/rodape: 0.5cm (faixa do timbrado)
  Fonte: Segoe UI
  Corpo: 11 pt
  Citacoes: 11 pt em italico, recuo esquerdo 4 cm
  Espacamento entre linhas: "Pelo menos" 15 pt
  Topicos: tabela 1x1, estilo Table Grid, fundo DBE5F1, texto negrito + italico
  Recuo 1a linha do corpo: 2.5 cm
  space_before e space_after: 0 (sem espaco explicito entre paragrafos)
  Alinhamento padrao: justificado
  Endereçamento: bold, justificado, sem recuo
  Nome da acao: centralizado, bold, maiusculo
  Titulos de secao (1 - DA ... / I - DA ... / EMENTA): tabela azul, bold + italico
  Fecho ("Nestes Termos," / "Pede e Espera Deferimento." / local e data): centralizado
  Assinatura: centralizada, bold, nome em maiusculas + linha OAB

Mantem o timbrado (cabecalho/logo/rodape) intacto - apenas limpa o body.
O timbrado e fornecido pelo escritorio em config/timbrado_modelo.docx.
"""
import re
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Timbrado fornecido pelo escritorio (placeholder: config/timbrado_modelo.docx)
_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_PATH = _ROOT / 'config' / 'timbrado_modelo.docx'
REFERENCIAS_DIR = Path(__file__).parent / 'REFERENCIAS'

# Valores medidos nas pecas reais do escritorio (ver docstring do modulo).
FONTE = 'Segoe UI'
TAM_CORPO = Pt(11)
TAM_CITACAO = Pt(11)
RECUO_PRIMEIRA = Cm(2.5)        # recuo de 1a linha, medido na peca real
RECUO_CITACAO_ESQ = Cm(4.0)
# "Pelo menos 15 pontos" no dialogo Paragrafo do Word (w:lineRule="atLeast").
ENTRELINHAS = Pt(15)
AZUL_TOPICO = 'DBE5F1'          # fundo das tabelas de topico
LARGURA_TEXTO = Cm(15.0)        # 21cm de A4 menos as margens de 3cm
MARG_TOP = Cm(2.5)
MARG_BOT = Cm(2.5)              # 2.5cm: o rodape do timbrado ocupa a faixa inferior
MARG_LEFT = Cm(3.0)
MARG_RIGHT = Cm(3.0)


# ============================================================
# DETECTORES DE TIPO DE BLOCO
# ============================================================

NOMES_PECA_CENTRALIZADO = {
    'RECLAMACAO TRABALHISTA', 'RECLAMAÇÃO TRABALHISTA',
    'RECLAMATORIA TRABALHISTA', 'RECLAMATÓRIA TRABALHISTA',
    'CONTESTACAO', 'CONTESTAÇÃO',
    'REPLICA', 'RÉPLICA',
    'RAZOES FINAIS', 'RAZÕES FINAIS',
    'MEMORIAIS', 'MEMORIAIS ESCRITOS',
    'RECURSO ORDINARIO', 'RECURSO ORDINÁRIO',
    'RECURSO DE REVISTA',
    'CONTRARRAZOES', 'CONTRARRAZÕES',
    'CONTRARRAZOES DE APELACAO', 'CONTRARRAZOES DE APELACAO CIVEL',
    'EMBARGOS DE DECLARACAO', 'EMBARGOS DE DECLARAÇÃO',
    'AGRAVO DE INSTRUMENTO', 'AGRAVO INTERNO',
    'PETICAO INICIAL', 'PETIÇÃO INICIAL',
    'MANIFESTACAO', 'MANIFESTAÇÃO',
    'PARECER', 'PARECER JURIDICO', 'PARECER JURÍDICO',
    'REQUERIMENTO', 'REQUERIMENTO ADMINISTRATIVO',
    'RECURSO ADMINISTRATIVO', 'DEFESA ADMINISTRATIVA',
    # Relatorio mensal ao cliente - ver .claude/rules/relatorio-processual.md
    'RELATORIO PROCESSUAL', 'RELATÓRIO PROCESSUAL',
    'RELATORIO PROCESSUAL ADMINISTRATIVO', 'RELATÓRIO PROCESSUAL ADMINISTRATIVO',
    # Parecer de calculo - ver .claude/rules/abate-teto.md
    'PARECER DE CALCULO', 'PARECER DE CÁLCULO',
    'PARECER DE CALCULO - ABATE-TETO', 'PARECER DE CÁLCULO - ABATE-TETO',
}


def _normalizar_acento(s):
    return (s.upper().replace('Ç', 'C').replace('Á', 'A').replace('Ã', 'A')
            .replace('É', 'E').replace('Ê', 'E').replace('Í', 'I').replace('Ó', 'O')
            .replace('Õ', 'O').replace('Ô', 'O').replace('Ú', 'U'))


def _eh_nome_peca(linha):
    s = linha.strip()
    s_limpo = re.sub(r'[\.\:\-—\s]+$', '', s)
    return _normalizar_acento(s_limpo) in NOMES_PECA_CENTRALIZADO


_RE_TITULO_SECAO_NUM = re.compile(
    r'^(?:[IVXLCDM]+(?:\.[IVXLCDM\d]+)*\.?|\d+(?:\.\d+)*\.?)\s+\S',
)
_RE_SUBTITULO = re.compile(r'^[A-Za-z0-9]\)\s+[A-Za-zÀ-ÿ]')


TITULOS_SEM_NUMERO = {'EMENTA', 'PRELIMINARMENTE', 'SINTESE FATICA', 'CONCLUSAO'}


def _eh_titulo_secao(linha):
    s = linha.strip()
    if not s or len(s) < 5 or len(s) > 250:
        return False
    # Topicos que aparecem sem numeracao (EMENTA e afins) tambem vao para a tabela.
    if _normalizar_acento(re.sub(r'[\.\:\-\s]+$', '', s)) in TITULOS_SEM_NUMERO:
        return True
    if _RE_TITULO_SECAO_NUM.match(s):
        resto = re.sub(r'^(?:[IVXLCDM]+(?:\.[IVXLCDM\d]+)*\.?|\d+(?:\.\d+)*\.?)\s+', '', s)
        return len(resto) >= 3
    return False


def _eh_subtitulo(linha):
    s = linha.strip()
    if not s or len(s) < 5 or len(s) > 200:
        return False
    return bool(_RE_SUBTITULO.match(s))


def _eh_enderecamento(linha):
    """Enderecamento judicial (EXCELENTISSIMO...) ou administrativo/militar
    (ILUSTRISSIMO SENHOR COMANDANTE..., AO JUIZO DA...)."""
    s = linha.strip().upper()
    return s.startswith((
        'EXCELENTISSIMO', 'EXCELENTÍSSIMO', 'EXMO', 'EXMA',
        'ILUSTRISSIMO', 'ILUSTRÍSSIMA', 'ILUSTRÍSSIMO', 'ILUSTRISSIMA',
        'ILMO', 'ILMA', 'AO JUIZO', 'AO JUÍZO', 'AO EXCELENTISSIMO',
        'AO EXCELENTÍSSIMO', 'AO ILUSTRISSIMO', 'AO ILUSTRÍSSIMO',
        'AO SENHOR COMANDANTE', 'A SUA EXCELENCIA', 'A SUA EXCELÊNCIA',
    ))


def _eh_pedido_final(linha):
    # padrao "a)", "b)", "aa)", "bb)" no inicio
    return bool(re.match(r'^[a-z]{1,2}\)\s+', linha.strip()))


_FECHOS = {
    'NESTES TERMOS', 'TERMOS EM QUE', 'NESTES TERMOS PEDE DEFERIMENTO',
    'PEDE E ESPERA DEFERIMENTO', 'PEDE DEFERIMENTO', 'ESPERA DEFERIMENTO',
    'REQUER DEFERIMENTO', 'REQUER E ESPERA DEFERIMENTO',
    'PEDE E AGUARDA DEFERIMENTO', 'AGUARDA DEFERIMENTO',
}

_RE_LOCAL_DATA = re.compile(
    r'^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\.\']{2,40},\s*\d{1,2}\s+de\s+[A-Za-zç]+\s+de\s+\d{4}\.?$',
    re.IGNORECASE,
)

_RE_LINHA_OAB = re.compile(r'^OAB\s*/?\s*[A-Z]{2}\s*n?[ºo°]?\.?\s*[\d\.\-]+$', re.IGNORECASE)


def _eh_fecho(linha):
    """"Nestes Termos," / "Pede e Espera Deferimento." - centralizado."""
    s = re.sub(r'[\.\,\:\;\s]+$', '', linha.strip())
    return _normalizar_acento(s) in _FECHOS


def _eh_local_data(linha):
    """"Rio de Janeiro, 23 de marco de 2022." - centralizado."""
    return bool(_RE_LOCAL_DATA.match(linha.strip()))


def _eh_linha_assinatura(linha):
    """Nome da advogada em maiusculas ou linha "OAB/RJ 188.762" - centralizado, bold."""
    s = linha.strip()
    if _RE_LINHA_OAB.match(s):
        return True
    # Nome proprio em MAIUSCULAS, sem digitos e sem pontuacao de frase
    if 3 <= len(s) <= 70 and s == s.upper() and not re.search(r'[\d\.\,\:\;\?\!]', s):
        return len(s.split()) >= 2
    return False


_RE_CITACAO_INICIO = re.compile(
    r'^(?:["“«]|s[uú]mula\s+\d+|oj\s+\d+|tese\s+\d+|tema\s+\d+'
    r'|art(?:igo)?\.?\s+\d+(?:[,\.\-\s][^—\-:]*)?[—\-:])',
    re.IGNORECASE,
)


def _eh_citacao(linha):
    s = linha.strip()
    if not s:
        return False
    if s.startswith(('"', '"', '“', '«')):
        return True
    if len(s) >= 30 and _RE_CITACAO_INICIO.match(s):
        return True
    return False


# ============================================================
# RENDERIZADORES
# ============================================================

def _ajustar_margens(doc):
    for s in doc.sections:
        s.top_margin = MARG_TOP
        s.bottom_margin = MARG_BOT
        s.left_margin = MARG_LEFT
        s.right_margin = MARG_RIGHT


def _limpar_corpo(doc):
    body = doc.element.body
    for el in list(body):
        tag = el.tag.split('}')[-1]
        if tag in ('p', 'tbl'):
            body.remove(el)


def _estilo_run(run, *, size=TAM_CORPO, bold=False, italic=False):
    run.font.name = FONTE
    run.font.size = size
    run.font.color.rgb = RGBColor(0, 0, 0)
    run.bold = bold
    run.italic = italic


def _padrao_paragrafo(p, *, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, recuo_primeira=True, left_indent=None):
    p.alignment = alinhamento
    pf = p.paragraph_format
    # Ordem importa: atribuir um Length a line_spacing deixa a regra em EXACTLY;
    # a regra AT_LEAST tem de ser fixada depois.
    pf.line_spacing = ENTRELINHAS
    pf.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
    # Explicito em 0: o estilo Normal do timbrado traz after=10pt herdado do Word,
    # e as pecas reais do escritorio nao usam espaco entre paragrafos.
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    if recuo_primeira:
        pf.first_line_indent = RECUO_PRIMEIRA
    if left_indent is not None:
        pf.left_indent = left_indent


def _add_texto_inline(p, texto, *, size=TAM_CORPO, negrito_total=False, italic_total=False):
    """Adiciona texto a um paragrafo respeitando markup **bold** e _italic_."""
    pos = 0
    pattern = re.compile(r'(\*\*([^*]+)\*\*|_([^_\n]+)_)')
    for m in pattern.finditer(texto):
        if m.start() > pos:
            r = p.add_run(texto[pos:m.start()])
            _estilo_run(r, size=size, bold=negrito_total, italic=italic_total)
        if m.group(2):
            r = p.add_run(m.group(2))
            _estilo_run(r, size=size, bold=True, italic=italic_total)
        elif m.group(3):
            r = p.add_run(m.group(3))
            _estilo_run(r, size=size, bold=negrito_total, italic=True)
        pos = m.end()
    if pos < len(texto):
        r = p.add_run(texto[pos:])
        _estilo_run(r, size=size, bold=negrito_total, italic=italic_total)


def _add_paragrafo_corpo(doc, texto):
    p = doc.add_paragraph()
    _padrao_paragrafo(p, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, recuo_primeira=True)
    _add_texto_inline(p, texto)
    return p


def _sombrear_celula(cell, fill):
    """Preenche a celula com uma cor solida (w:shd)."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    tcPr.append(shd)


def _add_paragrafo_titulo_secao(doc, texto):
    """Titulo de secao: tabela 1x1 de fundo azul claro, texto em negrito e italico.

    Padrao medido na "emenda de uniao estavel (peca-modelo)": cada topico (EMENTA,
    I- DA JUSTICA GRATUITA, II- ...) e uma tabela de uma celula, estilo Table Grid,
    preenchida com DBE5F1.
    """
    # Duas tabelas coladas sao fundidas numa so pelo Word ao abrir o arquivo, o que
    # juntaria dois topicos na mesma caixa azul. Um paragrafo vazio entre elas evita.
    anteriores = [el for el in doc.element.body
                  if el.tag.split('}')[-1] in ('p', 'tbl')]
    if anteriores and anteriores[-1].tag.split('}')[-1] == 'tbl':
        sep = doc.add_paragraph()
        _padrao_paragrafo(sep, recuo_primeira=False)
    # Normaliza hifen para travessao longo na numeracao "I - "
    texto = re.sub(r'^([IVX\d\.]+)\s*[-]\s+', r'\1 – ', texto, count=1)
    tabela = doc.add_table(rows=1, cols=1)
    tabela.style = 'Table Grid'
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabela.autofit = False
    celula = tabela.rows[0].cells[0]
    celula.width = LARGURA_TEXTO
    _sombrear_celula(celula, AZUL_TOPICO)
    p = celula.paragraphs[0]
    _padrao_paragrafo(p, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, recuo_primeira=False)
    _add_texto_inline(p, texto, negrito_total=True, italic_total=True)
    return tabela
def _add_paragrafo_subtitulo(doc, texto):
    """Subtitulo a), b), c): justificado, bold, sem recuo (mesmo padrao secao)."""
    p = doc.add_paragraph()
    _padrao_paragrafo(p, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, recuo_primeira=False)
    _add_texto_inline(p, texto, negrito_total=True)
    return p


def _add_paragrafo_nome_peca(doc, texto):
    """Nome da peca (RECLAMATORIA TRABALHISTA): centralizado, bold."""
    p = doc.add_paragraph()
    _padrao_paragrafo(p, alinhamento=WD_ALIGN_PARAGRAPH.CENTER, recuo_primeira=False)
    _add_texto_inline(p, texto, negrito_total=True)
    return p


def _add_paragrafo_enderecamento(doc, texto):
    """EXCELENTISSIMO ... : justificado, bold, sem recuo."""
    p = doc.add_paragraph()
    _padrao_paragrafo(p, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, recuo_primeira=False)
    _add_texto_inline(p, texto, negrito_total=True)
    return p


def _add_paragrafo_pedido(doc, texto):
    """Pedidos finais a), b), c): justificado, negrito, sem recuo.

    Mesmo tratamento de _add_paragrafo_subtitulo: os dois detectores casam com
    o mesmo padrao "a) ...", e so o comprimento decide qual deles pega a linha.
    Renderizar igual evita que uma mesma lista de pedidos saia metade em negrito
    e metade sem. Padrao medido nas pecas reais - ver padroes-documentos.md.
    """
    p = doc.add_paragraph()
    _padrao_paragrafo(p, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, recuo_primeira=False)
    _add_texto_inline(p, texto, negrito_total=True)
    return p


def _add_paragrafo_fecho(doc, texto, *, negrito=False):
    """Fecho, local/data e assinatura: centralizados, sem recuo."""
    p = doc.add_paragraph()
    _padrao_paragrafo(p, alinhamento=WD_ALIGN_PARAGRAPH.CENTER, recuo_primeira=False)
    _add_texto_inline(p, texto, negrito_total=negrito)
    return p


def _add_paragrafo_citacao(doc, texto):
    """Citacao em bloco: justificado, recuo esquerdo 4cm, 10pt, italico."""
    p = doc.add_paragraph()
    _padrao_paragrafo(p, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY,
                     recuo_primeira=False, left_indent=RECUO_CITACAO_ESQ)
    # Tudo em 10pt italico
    r = p.add_run(texto)
    _estilo_run(r, size=TAM_CITACAO, italic=True)
    return p


# ============================================================
# RENDERIZADOR PRINCIPAL
# ============================================================

def gerar_peca_escritorio(texto_peca: str, output_path):
    """Gera DOCX no timbrado seguindo a formatacao padrao do escritorio."""
    if not Path(TEMPLATE_PATH).exists():
        raise FileNotFoundError(
            f'Timbrado nao encontrado: {TEMPLATE_PATH}. '
            f'O escritorio deve fornecer o timbrado DELE em config/timbrado_modelo.docx.'
        )

    doc = Document(str(TEMPLATE_PATH))
    _ajustar_margens(doc)
    _limpar_corpo(doc)

    # Quebra em blocos (separados por linhas em branco)
    linhas = [l.rstrip() for l in texto_peca.split('\n')]
    blocos = []
    atual = []
    for l in linhas:
        if l.strip():
            atual.append(l)
        else:
            if atual:
                blocos.append('\n'.join(atual))
                atual = []
    if atual:
        blocos.append('\n'.join(atual))

    # A partir do fecho ("Nestes Termos,"), tudo o que vem depois e bloco de
    # fecho/assinatura: centralizado, sem recuo (padrao das pecas reais).
    em_fecho = False

    for bloco in blocos:
        unica = '\n' not in bloco
        if unica and (_eh_fecho(bloco) or _eh_local_data(bloco)):
            em_fecho = True
            _add_paragrafo_fecho(doc, bloco)
        elif em_fecho and unica and _eh_linha_assinatura(bloco):
            _add_paragrafo_fecho(doc, bloco, negrito=True)
        elif unica and _eh_enderecamento(bloco):
            _add_paragrafo_enderecamento(doc, bloco)
        elif unica and _eh_nome_peca(bloco):
            _add_paragrafo_nome_peca(doc, bloco)
        elif unica and _eh_titulo_secao(bloco):
            _add_paragrafo_titulo_secao(doc, bloco)
        elif unica and _eh_subtitulo(bloco):
            _add_paragrafo_subtitulo(doc, bloco)
        elif unica and _eh_pedido_final(bloco):
            _add_paragrafo_pedido(doc, bloco)
        elif _eh_citacao(bloco):
            _add_paragrafo_citacao(doc, bloco)
        else:
            _add_paragrafo_corpo(doc, bloco)

    out = Path(output_path)
    doc.save(str(out))
    return out
