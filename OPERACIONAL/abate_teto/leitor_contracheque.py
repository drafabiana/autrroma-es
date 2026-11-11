# -*- coding: utf-8 -*-
"""
Leitura de contracheque em PDF para a calculadora de abate-teto.

Suporta hoje o COMPROVANTE MENSAL DE RENDIMENTOS do CPEx (Centro de Pagamento
do Exercito) - o layout dos contracheques de militares e pensionistas do
Exercito, em que cada linha traz codigo, descricao, info complementar, prazo e
o valor em uma de tres colunas (Receitas / Despesas / Liquido).

A leitura e por COORDENADA, nao por ordem do texto: o PDF do CPEx traz a marca
de agua ("Acessado por: ...") intercalada no meio das linhas, e qualquer parser
que confie na ordem do texto mistura as rubricas com o carimbo.

NAO SUPORTA (leitura manual ou CSV):
  - ficha financeira anual do CPEx: os arquivos do escritorio sao digitalizacoes
    de baixa qualidade, sem camada de texto confiavel;
  - contracheque SIAPE (servidor civil): o layout separa rotulos e valores em
    blocos distantes. Para esses, usar o CSV (ver carregar_csv).

Toda leitura automatica e um RASCUNHO: conferir contra o PDF antes de assinar
qualquer calculo. A funcao devolve tambem os totais impressos no contracheque,
justamente para o confronto (ver calculadora.validar_bruto).
"""
import csv
import os
import re
import unicodedata

MOEDA = re.compile(r"^\d{1,3}(\.\d{3})*,\d{2}$")
CODIGO = re.compile(r"^[A-Z][A-Z0-9]{2}$")


def _sem_acento(texto):
    forma = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in forma if not unicodedata.combining(c)).upper()


def _linhas_do_pdf(caminho):
    """Devolve as linhas do PDF como [(y, [(x, palavra), ...]), ...].

    Prefere o PyMuPDF - e nao por gosto: no contracheque do CPEx cada linha da
    tabela e um BLOCO proprio e a marca de agua ("Acessado por: ...") e outro
    bloco, sobreposto no mesmo y. Agrupando por bloco, a marca de agua sai
    sozinha; agrupando so por y, ela entra no meio da descricao da rubrica.
    O pdfplumber (extrator padrao do repositorio) fica como alternativa e
    agrupa por y - suficiente para PDF sem marca de agua.
    """
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            pymupdf = None

    if pymupdf is not None:
        linhas = []
        for pagina in pymupdf.open(caminho):
            blocos = {}
            for palavra in pagina.get_text("words"):
                x0, y0, _x1, _y1, texto, bloco = palavra[0], palavra[1], palavra[2], palavra[3], palavra[4], palavra[5]
                blocos.setdefault(bloco, []).append((float(x0), float(y0), texto))
            for bloco in sorted(blocos):
                itens = blocos[bloco]
                y = min(i[1] for i in itens)
                linhas.append((y, sorted([(i[0], i[2]) for i in itens], key=lambda i: i[0])))
        return sorted(linhas, key=lambda l: l[0])

    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError(
            "Nenhum extrator de PDF instalado. Rode: pip install pdfplumber"
        )
    palavras = []
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            palavras.extend(
                (float(p["x0"]), float(p["top"]), p["text"]) for p in pagina.extract_words()
            )
    return _agrupar_por_y(palavras)


def _agrupar_por_y(palavras, tolerancia=3.0):
    """Agrupa palavras em linhas por proximidade vertical."""
    linhas = []
    for x0, y0, texto in sorted(palavras, key=lambda p: (p[1], p[0])):
        if linhas and abs(y0 - linhas[-1][0]) <= tolerancia:
            linhas[-1][1].append((x0, texto))
        else:
            linhas.append((y0, [(x0, texto)]))
    return [(y, sorted(itens, key=lambda i: i[0])) for y, itens in linhas]


def ler_contracheque_cpex(caminho):
    """Le um comprovante mensal de rendimentos do CPEx.

    Retorna dict com: nome, matricula (PREC-CP), competencia ('MM/AAAA'),
    parcelas (lista de dicts codigo/descricao/valor/coluna) e os totais
    impressos (total_receitas, total_despesas, total_liquido).
    """
    linhas = _linhas_do_pdf(caminho)
    faixas = _faixas_de_colunas(linhas)
    if not faixas:
        raise ValueError(
            "Nao encontrei o cabecalho Receitas/Despesas/Liquido em %s - o "
            "arquivo provavelmente nao e um contracheque do CPEx." % os.path.basename(caminho)
        )

    parcelas = []
    totais = {}
    for _y, itens in linhas:
        # O codigo da rubrica e o token de 3 caracteres alinhado a coluna
        # "Codigo" do cabecalho. Ancorar na coluna, e nao num x fixo: o CPEx
        # mudou o recuo da tabela em 2026 e um limiar fixo derruba as rubricas.
        codigos = [
            (x, t) for x, t in itens
            if CODIGO.match(t) and abs(x - faixas["codigo"]) <= 40
        ]
        valores = [(x, t) for x, t in itens if MOEDA.match(t)]
        if not valores:
            continue

        if codigos:
            # A descricao vai do fim da coluna de codigo ate o inicio da coluna
            # "Info Complementar". Nao filtrar por formato: ha descricao que e
            # ela propria um codigo ("DA I40 AT" remete a rubrica I40).
            x_codigo = min(x for x, t in codigos)
            descricao = " ".join(
                t for x, t in itens if x_codigo + 15 <= x < faixas["info"]
            ).strip()
            x_valor, texto_valor = valores[0]
            coluna = _coluna(x_valor, faixas)
            if coluna == "liquido":
                continue
            parcelas.append({
                "codigo": min(codigos, key=lambda c: c[0])[1],
                "descricao": descricao,
                "valor": texto_valor,
                "coluna": "receita" if coluna == "receita" else "desconto",
            })
        elif len(valores) >= 3 and any(t == "R$" for x, t in itens):
            # Linha de totais do rodape.
            for x_valor, texto_valor in valores:
                coluna = _coluna(x_valor, faixas)
                totais["total_" + {"receita": "receitas", "desconto": "despesas",
                                   "liquido": "liquido"}[coluna]] = texto_valor

    cabecalho = _cabecalho_cpex(linhas)
    cabecalho.update(totais)
    cabecalho["parcelas"] = parcelas
    cabecalho["arquivo"] = os.path.basename(caminho)
    return cabecalho


def _faixas_de_colunas(linhas):
    """Localiza os x dos titulos Receitas / Despesas / Liquido."""
    for _y, itens in linhas:
        textos = {_sem_acento(t): x for x, t in itens}
        if "RECEITAS" in textos and "DESPESAS" in textos and "LIQUIDO" in textos:
            return {
                "codigo": textos.get("CODIGO", 40.0),
                "info": textos.get("INFO", 200.0),
                "receita": textos["RECEITAS"],
                "desconto": textos["DESPESAS"],
                "liquido": textos["LIQUIDO"],
            }
    return None


def _coluna(x, faixas):
    """Diz em qual coluna um valor caiu, pelo x mais proximo do titulo."""
    limite_rd = (faixas["receita"] + faixas["desconto"]) / 2
    limite_dl = (faixas["desconto"] + faixas["liquido"]) / 2
    if x < limite_rd:
        return "receita"
    if x < limite_dl:
        return "desconto"
    return "liquido"


MESES = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6,
    "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11,
    "DEZEMBRO": 12,
}


def _cabecalho_cpex(linhas):
    """Extrai nome, PREC-CP e competencia do cabecalho."""
    dados = {"nome": "", "matricula": "", "competencia": ""}
    y_rotulo_prec = None

    for y, itens in linhas:
        texto = _sem_acento(" ".join(t for x, t in itens))

        # O mes e o ano ficam na mesma linha do rotulo MES, mas nem sempre lado
        # a lado: em 2026 o PDF traz "FEVEREIRO  MES  2026". Por isso procura-se
        # o nome do mes e o ano na linha, sem exigir que sejam vizinhos.
        if not dados["competencia"]:
            ano = re.search(r"\b(19|20)\d{2}\b", texto)
            if ano:
                for nome_mes, numero in MESES.items():
                    if re.search(r"\b%s\b" % nome_mes, texto):
                        dados["competencia"] = "%02d/%s" % (numero, ano.group(0))
                        break

        if "PREC-CP" in texto and y_rotulo_prec is None:
            y_rotulo_prec = y

    # O PREC-CP e o nome vem na primeira linha de dados abaixo do rotulo:
    # numeros na coluna da esquerda, nome em maiusculas ao lado.
    if y_rotulo_prec is not None:
        for y, itens in linhas:
            if y <= y_rotulo_prec:
                continue
            esquerda = [t for x, t in itens if x < 85]
            nome = [t for x, t in itens if 85 <= x < 400]
            if esquerda and nome and all(t.isdigit() for t in esquerda) \
                    and any(len(t) > 2 and t.isalpha() for t in nome):
                dados["matricula"] = " ".join(esquerda).strip()
                dados["nome"] = " ".join(nome).strip()
                break
    return dados


# ---------------------------------------------------------------------------
# Caminho universal e seguro: CSV digitado ou colado a mao.
# ---------------------------------------------------------------------------
CABECALHO_CSV = ["competencia", "vinculo", "codigo", "descricao", "valor", "coluna"]


def carregar_csv(caminho):
    """Le um CSV de rubricas no formato do escritorio.

    Colunas: competencia;vinculo;codigo;descricao;valor;coluna
      competencia -> MM/AAAA
      vinculo     -> nome do vinculo (uma matricula/pensao/provento)
      coluna      -> receita | desconto | (vazio, para deduzir pela descricao)

    Separador ';' (padrao do Excel em portugues) ou ','.
    """
    with open(caminho, "r", encoding="utf-8-sig", newline="") as arquivo:
        amostra = arquivo.read(4096)
        arquivo.seek(0)
        separador = ";" if amostra.count(";") >= amostra.count(",") else ","
        linhas = list(csv.DictReader(arquivo, delimiter=separador))

    faltando = [c for c in ("competencia", "vinculo", "descricao", "valor")
                if linhas and c not in linhas[0]]
    if faltando:
        raise ValueError(
            "CSV sem as colunas obrigatorias: %s. Esperado: %s"
            % (", ".join(faltando), ";".join(CABECALHO_CSV))
        )
    return linhas


def modelo_csv(caminho):
    """Grava um CSV de exemplo, pronto para preencher."""
    exemplo = [
        ["02/2025", "Pensao militar (Exercito)", "C01", "SOLDO (MAJ)", "11.088,00", "receita"],
        ["02/2025", "Pensao militar (Exercito)", "C03", "ADIC TP SV", "4.435,20", "receita"],
        ["02/2025", "Pensao militar (Exercito)", "Z01", "FUSEX", "698,54", "desconto"],
        ["02/2025", "Aposentadoria (UFRJ)", "", "PROVENTO BASICO", "9.462,03", "receita"],
        ["02/2025", "Aposentadoria (UFRJ)", "", "ABATE TETO", "1.500,00", "desconto"],
    ]
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(CABECALHO_CSV)
        escritor.writerows(exemplo)
    return caminho
