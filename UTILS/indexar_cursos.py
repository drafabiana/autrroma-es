# -*- coding: utf-8 -*-
"""
Indexador da Base de Conhecimento - material de curso, apostila, livro e palestra.

Varre a pasta de cursos no Google Drive, extrai o texto de cada material para
BASE_CONHECIMENTO/_extraido/, cria uma ficha-rascunho na area correspondente e
regenera BASE_CONHECIMENTO/INDICE.md.

O original NUNCA e copiado para o repositorio - so o texto extraido (nao versionado)
e a ficha destilada (versionada). Ver .claude/rules/base-conhecimento-cursos.md.

Alves Carneiro Advocacia e Consultoria Juridica.

Uso:
    python UTILS/indexar_cursos.py                    # indexa tudo que for novo
    python UTILS/indexar_cursos.py --dry-run          # mostra o que faria, sem escrever
    python UTILS/indexar_cursos.py --pasta "G:/Meu Drive/CURSOS/IBIJUS"
    python UTILS/indexar_cursos.py --reextrair        # refaz o texto de _extraido/

Ficha ja existente NUNCA e sobrescrita - o trabalho de destilacao e da IA e da
Dra. Fabiana, e um reindex nao pode apaga-lo.
"""
import os
import re
import sys
import argparse
import unicodedata
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, 'BASE_CONHECIMENTO')
EXTRAIDO = os.path.join(BASE, '_extraido')
MODELO = os.path.join(BASE, '_MODELO_FICHA.md')
INDICE = os.path.join(BASE, 'INDICE.md')

CURSOS_DIR = os.environ.get('CURSOS_DIR', r'G:\Meu Drive\CURSOS')

AREAS = ['PREVIDENCIARIO', 'MILITAR', 'PROCESSUAL', '_A_CLASSIFICAR']

EXT_TEXTO = {'.pdf', '.docx', '.doc', '.rtf', '.pptx', '.txt', '.md'}
EXT_MIDIA = {'.mp4', '.avi', '.mkv', '.mov', '.mp3', '.m4a', '.wav', '.ogg'}
EXT_IMAGEM = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff'}

# Palavras que identificam a area. Acento e caixa sao ignorados na comparacao.
PALAVRAS_AREA = {
    'MILITAR': [
        'militar', 'pmerj', 'cbmerj', 'exercito', 'marinha', 'aeronautica',
        'conselho de disciplina', 'conselho de justificacao', 'justificacao',
        'processo administrativo disciplinar', 'sindicancia',
        'praca', 'oficial', 'reforma', 'licenciamento', 'preteri',
        'pensao militar', 'estatuto dos militares', 'junta de inspecao',
        'forcas armadas', 'caserna', 'disciplina militar',
    ],
    'PREVIDENCIARIO': [
        'previdenciari', 'inss', 'aposentadoria', 'bpc', 'loas',
        'beneficio assistencial', 'auxilio-doenca', 'auxilio doenca',
        'incapacidade', 'pensao por morte', 'salario-maternidade',
        'tempo de contribuicao', 'carencia', 'revisao da vida toda',
        'certidao de tempo de contribuicao', 'aposentadoria especial',
        'ltcat', 'rgps', 'rpps', 'ec 103', 'lei 8.213', 'lei 8213',
        'segurado especial', 'rural', 'isencao de ir', 'isencao do imposto',
    ],
    'PROCESSUAL': [
        'cpc', 'codigo de processo civil', 'recurso', 'apelacao', 'agravo',
        'embargos', 'mandado de seguranca', 'juizado especial',
        'juizado federal', 'tutela de urgencia', 'tutela antecipada',
        'competencia', 'honorarios', 'cumprimento de sentenca', 'execucao',
        'pericia', 'quesitos', 'preliminar', 'contestacao',
    ],
}


# ---------------------------------------------------------------- utilidades

def sem_acento(texto):
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def slug(texto, limite=80):
    t = sem_acento(texto).lower()
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')
    return t[:limite] or 'material'


def classificar(caminho, texto):
    """Escolhe a area pela contagem de palavras-chave no caminho e no texto."""
    # O caminho (nome do curso + nome do arquivo) pesa mais que o corpo: um curso
    # de previdenciario cita 'recurso' o tempo todo sem ser material processual.
    alvo_caminho = sem_acento(caminho).lower()
    alvo_texto = sem_acento(texto[:60000]).lower()

    placar = {}
    for area, palavras in PALAVRAS_AREA.items():
        pontos = 0
        for p in palavras:
            pontos += alvo_caminho.count(p) * 10
            pontos += min(alvo_texto.count(p), 20)
        placar[area] = pontos

    melhor = max(placar, key=placar.get)
    if placar[melhor] == 0:
        return '_A_CLASSIFICAR', placar
    return melhor, placar


# ---------------------------------------------------------------- extracao

def _extrair_pdf(caminho):
    # pdfplumber e o extrator padrao do repositorio (ja esta no requirements);
    # pypdf fica de alternativa para quando ele nao estiver disponivel.
    paginas = None
    try:
        import logging
        import pdfplumber
        # Apostila escaneada dispara dezenas de avisos de fonte do pdfminer que
        # nao mudam o resultado e escondem a saida util do indexador.
        logging.getLogger('pdfminer').setLevel(logging.ERROR)
        try:
            with pdfplumber.open(caminho) as pdf:
                paginas = [(p.extract_text() or '') for p in pdf.pages]
        except Exception as e:
            return None, 'falha ao ler PDF: %s' % e
    except ImportError:
        pass

    if paginas is None:
        try:
            from pypdf import PdfReader
        except ImportError:
            return None, 'nem pdfplumber nem pypdf instalados (pip install pdfplumber)'
        try:
            reader = PdfReader(caminho)
            paginas = [(p.extract_text() or '') for p in reader.pages]
        except Exception as e:
            return None, 'falha ao ler PDF: %s' % e

    texto = '\n\n'.join(paginas).strip()
    if len(texto) < 200:
        return None, ('PDF sem camada de texto (digitalizado), %d paginas - '
                      'precisa leitura visual' % len(paginas))
    return texto, None


def _extrair_docx(caminho):
    try:
        import docx
    except ImportError:
        return None, 'python-docx nao instalado (pip install python-docx)'
    try:
        d = docx.Document(caminho)
    except Exception as e:
        return None, 'falha ao ler DOCX: %s' % e
    partes = [p.text for p in d.paragraphs]
    for tab in d.tables:
        for linha in tab.rows:
            partes.append(' | '.join(c.text for c in linha.cells))
    return '\n'.join(partes).strip(), None


def _extrair_pptx(caminho):
    try:
        from pptx import Presentation
    except ImportError:
        return None, 'python-pptx nao instalado (pip install python-pptx)'
    try:
        pres = Presentation(caminho)
    except Exception as e:
        return None, 'falha ao ler PPTX: %s' % e
    partes = []
    for i, slide in enumerate(pres.slides, 1):
        partes.append('--- slide %d ---' % i)
        for shape in slide.shapes:
            if shape.has_text_frame:
                partes.append(shape.text_frame.text)
    texto = '\n'.join(partes).strip()
    if len(texto) < 100:
        return None, 'slides sem texto (imagens) - precisa leitura visual'
    return texto, None


def _extrair_word_com(caminho):
    """.doc e .rtf antigos: so o Word consegue abrir nesta maquina."""
    try:
        import win32com.client
    except ImportError:
        return None, 'pywin32 nao instalado - .doc/.rtf exigem Word COM (pip install pywin32)'
    word = None
    try:
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False
        doc = word.Documents.Open(os.path.abspath(caminho), ReadOnly=True)
        texto = doc.Content.Text
        doc.Close(False)
        return texto.strip(), None
    except Exception as e:
        return None, 'Word COM falhou: %s' % e
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass


def _extrair_txt(caminho):
    for enc in ('utf-8', 'cp1252', 'latin-1'):
        try:
            with open(caminho, 'r', encoding=enc) as f:
                return f.read().strip(), None
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return None, 'falha ao ler texto: %s' % e
    return None, 'nao foi possivel decodificar o arquivo'


def extrair_texto(caminho):
    """Retorna (texto, motivo_da_falha). Um dos dois e sempre None."""
    ext = os.path.splitext(caminho)[1].lower()
    if ext == '.pdf':
        return _extrair_pdf(caminho)
    if ext == '.docx':
        return _extrair_docx(caminho)
    if ext == '.pptx':
        return _extrair_pptx(caminho)
    if ext in ('.doc', '.rtf'):
        return _extrair_word_com(caminho)
    if ext in ('.txt', '.md'):
        return _extrair_txt(caminho)
    if ext in EXT_MIDIA:
        return None, 'video/audio - sem transcricao automatica nesta maquina'
    if ext in EXT_IMAGEM:
        return None, 'imagem - esta maquina nao tem OCR, precisa leitura visual'
    return None, 'extensao %s nao suportada' % ext


# ---------------------------------------------------------------- ficha

def frontmatter(caminho_ficha):
    """Le o frontmatter YAML raso de uma ficha. Dicionario simples chave->valor."""
    dados = {}
    try:
        with open(caminho_ficha, 'r', encoding='utf-8') as f:
            linhas = f.read().split('\n')
    except Exception:
        return dados
    if not linhas or linhas[0].strip() != '---':
        return dados
    for linha in linhas[1:]:
        if linha.strip() == '---':
            break
        m = re.match(r'^\s*(\w+):\s*(.*)$', linha)
        if m:
            dados[m.group(1)] = m.group(2).strip()
    return dados


def montar_ficha(titulo, area, original, extraido, curso):
    hoje = datetime.now().strftime('%d/%m/%Y')
    cabecalho = [
        '---',
        'titulo: %s' % titulo,
        'area: %s' % area,
        'origem:',
        '  tipo: curso',
        '  autor: <preencher>',
        '  instituicao: %s' % (curso or '<preencher>'),
        '  data: <preencher - MM/YYYY do material>',
        'original: %s' % original,
        'extraido: %s' % extraido,
        'status: RASCUNHO',
        'conferida_por: -',
        'conferida_em: -',
        'indexado_em: %s' % hoje,
        '---',
        '',
        '# %s' % titulo,
        '',
        '> **FICHA NAO DESTILADA.** O indexador so criou o esqueleto e extraiu o texto',
        '> para `%s`. Pedir para a IA destilar e, so depois,' % extraido,
        '> submeter a conferencia da Dra. Fabiana.',
        '',
    ]
    # O corpo vem do modelo, a partir da secao "Do que trata".
    corpo = ''
    if os.path.exists(MODELO):
        with open(MODELO, 'r', encoding='utf-8') as f:
            texto_modelo = f.read()
        pos = texto_modelo.find('## Do que trata')
        if pos >= 0:
            corpo = texto_modelo[pos:]
    return '\n'.join(cabecalho) + '\n' + corpo


# ---------------------------------------------------------------- indice

ROTULOS = {
    'PREVIDENCIARIO': 'Previdenciario',
    'MILITAR': 'Militar',
    'PROCESSUAL': 'Processual',
    '_A_CLASSIFICAR': 'A classificar',
}


def regenerar_indice(fichas, pendentes):
    """Reescreve INDICE.md inteiro a partir das fichas em disco."""
    por_area = {a: [] for a in AREAS}
    for f in fichas:
        por_area.setdefault(f['area'], []).append(f)

    linhas = [
        '# Indice da Base de Conhecimento',
        '',
        '> Arquivo **gerado** por `UTILS/indexar_cursos.py` - nao editar a mao, a',
        '> proxima indexacao sobrescreve. O que se edita e a ficha de cada material.',
        '',
        'Ultima indexacao: %s' % datetime.now().strftime('%d/%m/%Y %H:%M'),
        '',
        '**Status:** `RASCUNHO` = ficha criada, ainda nao destilada ou nao conferida.',
        '`CONFERIDA` = lida e validada pela Dra. Fabiana - so esta vale como fundamentacao.',
        '',
    ]

    for area in AREAS:
        itens = sorted(por_area.get(area, []), key=lambda x: x['titulo'].lower())
        linhas.append('## %s' % ROTULOS.get(area, area))
        linhas.append('')
        if area == '_A_CLASSIFICAR' and not itens:
            linhas.append('_(nenhum material pendente de classificacao)_')
            linhas.append('')
            continue
        linhas.append('| Ficha | Origem | Assunto | Status |')
        linhas.append('|---|---|---|---|')
        if not itens:
            linhas.append('| _(vazio)_ | | | |')
        for it in itens:
            linhas.append('| [%s](%s/%s) | %s | %s | %s |' % (
                it['titulo'], area, it['arquivo'],
                it.get('curso') or '-',
                it.get('assunto') or '-',
                it.get('status') or 'RASCUNHO',
            ))
        linhas.append('')

    linhas += [
        '## Pendentes de leitura visual',
        '',
        'Material em `%s` que o indexador nao conseguiu extrair - PDF digitalizado sem' % CURSOS_DIR,
        'camada de texto, slide em imagem, video ou audio. Esta maquina nao tem OCR;',
        'PDF digitalizado precisa ser lido pela IA com a tool Read e o parametro `pages`.',
        '',
        '| Arquivo | Motivo |',
        '|---|---|',
    ]
    if not pendentes:
        linhas.append('| _(vazio)_ | |')
    for p in sorted(pendentes, key=lambda x: x['arquivo'].lower()):
        linhas.append('| `%s` | %s |' % (p['arquivo'], p['motivo']))
    linhas.append('')

    return '\n'.join(linhas)


def varrer_fichas():
    """Le as fichas ja existentes no repositorio."""
    achadas = []
    for area in AREAS:
        pasta = os.path.join(BASE, area)
        if not os.path.isdir(pasta):
            continue
        for nome in sorted(os.listdir(pasta)):
            if not nome.endswith('.md'):
                continue
            fm = frontmatter(os.path.join(pasta, nome))
            achadas.append({
                'area': area,
                'arquivo': nome,
                'titulo': fm.get('titulo') or nome[:-3],
                'status': fm.get('status', 'RASCUNHO'),
                'curso': fm.get('instituicao'),
                'assunto': fm.get('assunto'),
            })
    return achadas


# ---------------------------------------------------------------- principal

def indexar(pasta, dry_run=False, reextrair=False):
    if not os.path.isdir(pasta):
        print('Pasta de cursos nao encontrada: %s' % pasta)
        print('Criar a pasta no Drive (ou apontar outra com --pasta) e rodar de novo.')
        return 1

    if not dry_run:
        for area in AREAS:
            os.makedirs(os.path.join(BASE, area), exist_ok=True)
        os.makedirs(EXTRAIDO, exist_ok=True)

    novos, existentes, pendentes = [], [], []

    for raiz, dirs, arquivos in os.walk(pasta):
        dirs[:] = [d for d in dirs if not d.startswith(('.', '_'))]
        for nome in sorted(arquivos):
            if nome.startswith(('.', '~$')):
                continue
            ext = os.path.splitext(nome)[1].lower()
            if ext not in EXT_TEXTO | EXT_MIDIA | EXT_IMAGEM:
                continue

            caminho = os.path.join(raiz, nome)
            rel = os.path.relpath(caminho, pasta)
            curso = rel.split(os.sep)[0] if os.sep in rel else ''
            titulo = os.path.splitext(nome)[0]
            base_slug = slug(('%s %s' % (curso, titulo)).strip())

            texto, motivo = extrair_texto(caminho)
            if texto is None:
                pendentes.append({'arquivo': rel, 'motivo': motivo})
                print('  [pendente] %s -> %s' % (rel, motivo))
                continue

            area, _placar = classificar(rel, texto)
            ficha_nome = '%s.md' % base_slug
            extraido_rel = 'BASE_CONHECIMENTO/_extraido/%s.txt' % base_slug
            extraido_path = os.path.join(EXTRAIDO, '%s.txt' % base_slug)

            # A ficha pode ter sido movida de area a mao - procurar em todas.
            ja_tem_ficha = any(
                os.path.exists(os.path.join(BASE, a, ficha_nome)) for a in AREAS
            )

            if not dry_run and (reextrair or not os.path.exists(extraido_path)):
                with open(extraido_path, 'w', encoding='utf-8') as f:
                    f.write(texto)

            if ja_tem_ficha:
                existentes.append(rel)
                print('  [ja indexado] %s' % rel)
                continue

            if not dry_run:
                conteudo = montar_ficha(titulo, area, caminho, extraido_rel, curso)
                with open(os.path.join(BASE, area, ficha_nome), 'w', encoding='utf-8') as f:
                    f.write(conteudo)
            novos.append({'rel': rel, 'area': area, 'ficha': ficha_nome})
            print('  [novo] %s -> %s/%s (%d mil caracteres)' % (
                rel, area, ficha_nome, len(texto) // 1000))

    if not dry_run:
        with open(INDICE, 'w', encoding='utf-8') as f:
            f.write(regenerar_indice(varrer_fichas(), pendentes))

    print('')
    print('Resumo%s:' % (' (DRY-RUN, nada foi escrito)' if dry_run else ''))
    print('  fichas novas .............. %d' % len(novos))
    print('  ja indexados .............. %d' % len(existentes))
    print('  pendentes (sem texto) ..... %d' % len(pendentes))
    if novos:
        print('')
        print('Proximo passo: pedir a destilacao das fichas novas. Elas estao marcadas')
        print('RASCUNHO e nao valem como fundamentacao ate a Dra. Fabiana conferir.')
    return 0


def main():
    ap = argparse.ArgumentParser(
        description='Indexa material de curso do Drive na BASE_CONHECIMENTO.')
    ap.add_argument('--pasta', default=CURSOS_DIR,
                    help='pasta de cursos (default: %s)' % CURSOS_DIR)
    ap.add_argument('--dry-run', action='store_true',
                    help='mostra o que faria, sem escrever nada')
    ap.add_argument('--reextrair', action='store_true',
                    help='refaz o texto em _extraido/ mesmo se ja existir')
    args = ap.parse_args()

    print('Indexando: %s' % args.pasta)
    print('')
    return indexar(args.pasta, dry_run=args.dry_run, reextrair=args.reextrair)


if __name__ == '__main__':
    sys.exit(main())
