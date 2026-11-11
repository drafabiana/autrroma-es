# -*- coding: utf-8 -*-
"""
Classificacao das rubricas do contracheque para fins de teto constitucional.

Tres perguntas por rubrica:
  1. E receita ou desconto?
  2. Se e receita, ENTRA na base do teto (remuneratoria) ou NAO ENTRA
     (indenizatoria / direito social / assistencial)?
  3. E a propria rubrica de abate-teto ja aplicada pelo orgao pagador?

Fundamento da exclusao:
  - CF/88, art. 37, par. 11 (EC 47/2005): "Nao serao computadas, para efeito dos
    limites remuneratorios de que trata o inciso XI do caput deste artigo, as
    parcelas de carater indenizatorio previstas em lei."
  - Resolucao CNJ 14/2006, art. 4o: rol das verbas excluidas do teto.
  - STF, ADI 1.404-MC: parcelas indenizatorias nao integram a remuneracao para
    fins de teto (entendimento anterior mesmo a EC 47/2005).

REGRA DE SEGURANCA: rubrica desconhecida entra na base como COMPUTAVEL e sai
marcada para conferencia. Errar para o lado de incluir produz uma glosa MAIOR e
um pedido MENOR - defensavel. Errar para o lado de excluir infla o pedido do
cliente e derruba a credibilidade do calculo em juizo.
"""
import re
import unicodedata

# Naturezas possiveis de uma rubrica.
COMPUTAVEL = "COMPUTAVEL"          # receita que entra na base do teto
NAO_COMPUTAVEL = "NAO_COMPUTAVEL"  # receita fora da base (art. 37, par. 11)
DESCONTO = "DESCONTO"              # desconto comum (IR, FUSEX, pensao, emprestimo)
ABATE_TETO = "ABATE_TETO"          # a glosa do proprio mes, ja praticada
ABATE_TETO_RETROATIVO = "ABATE_TETO_RETROATIVO"  # glosa de meses anteriores,
#                                    cobrada de uma vez: entra no total retido,
#                                    mas NAO no confronto mensal com o teto.


def _chave(texto):
    """Normaliza para comparacao: sem acento, maiusculo, espaco unico."""
    if texto is None:
        return ""
    sem_acento = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento.upper()).strip()


# ---------------------------------------------------------------------------
# Rubricas de abate-teto (a glosa em si). Testadas ANTES de tudo.
# ---------------------------------------------------------------------------
# Referencia ao proprio art. 37, XI - e assim que o CPEx nomeia a glosa desde
# 2026: rubrica I40, descricao "DA A.37 XI CF/88".
_REFERENCIA_TETO = r"(ABATE[ \-]?TETO|TETO CONSTITUCIONAL|TETO REMUNERATORIO|A\.? ?37,? ?XI|ART\.? ?37,? ?XI|\bI40\b)"

PADROES_ABATE_TETO = [
    r"ABATE[ \-]?TETO",
    r"\bTETO CONSTITUCIONAL\b",
    r"\bTETO REMUNERATORIO\b",
    r"\bDESC(ONTO)? TETO\b",
    r"\bREDUTOR (SALARIAL|CONSTITUCIONAL|TETO)\b",
    r"\bLIMITE CONSTITUCIONAL\b",
    r"\bA\.? ?37,? ?XI\b",
    r"\bART\.? ?37,? ?XI\b",
]

# Glosa de meses passados cobrada de uma vez. No CPEx: rubrica I39, descricao
# "DA I40 AT" (atrasados da rubrica I40).
# >>> Leitura inferida dos contracheques de 2026 do escritorio; confirmar com o
# >>> CPEx antes de usar o valor como retroativo em peca.
PADROES_ABATE_TETO_RETROATIVO = [
    _REFERENCIA_TETO + r".*\b(AT|ATRAS\w*|EXERC\w* ANT\w*)\b",
    r"\b(AT|ATRAS\w*|EXERC\w* ANT\w*)\b.*" + _REFERENCIA_TETO,
]

# Codigos de rubrica do CPEx observados nos contracheques do escritorio.
CODIGOS_CPEX = {
    "I40": ABATE_TETO,              # "DA A.37 XI CF/88" - glosa do mes
    "I39": ABATE_TETO_RETROATIVO,   # "DA I40 AT" - atrasados da glosa
}

# ---------------------------------------------------------------------------
# Receitas que NAO entram na base do teto.
# (padrao, fundamento, conferir)
# ---------------------------------------------------------------------------
PADROES_NAO_COMPUTAVEL = [
    # --- indenizatorias tipicas (CF art. 37, par. 11; Res. CNJ 14/2006, art. 4o)
    (r"\bAJUDA DE CUSTO\b",
     "Indenizatoria - CF art. 37, par. 11; Res. CNJ 14/2006, art. 4o", False),
    (r"\bDIARIAS?\b",
     "Indenizatoria - CF art. 37, par. 11; Res. CNJ 14/2006, art. 4o", False),
    (r"\bAUX(ILIO)?[ \-]?FARDAMENTO\b",
     "Indenizatoria - MP 2.215-10/2001; CF art. 37, par. 11", False),
    (r"\bAUX(ILIO)?[ \-]?ALIMENTAC",
     "Indenizatoria - Res. CNJ 14/2006, art. 4o, III", False),
    (r"\bAUX(ILIO)?[ \-]?TRANSPORTE\b",
     "Indenizatoria - Res. CNJ 14/2006, art. 4o, III", False),
    (r"\bIND(EN)?[ \.]?(IZACAO )?DE TRANSPORTE\b",
     "Indenizatoria - Res. CNJ 14/2006, art. 4o, III", False),
    (r"\bAUX(ILIO)?[ \-]?MORADIA\b",
     "Indenizatoria - Res. CNJ 14/2006, art. 4o, III", False),
    (r"\bAUX(ILIO)?[ \-]?(PRE[ \-]?ESCOLAR|CRECHE)\b",
     "Indenizatoria - Res. CNJ 14/2006, art. 4o, III", False),
    (r"\bAUX(ILIO)?[ \-]?NATALIDADE\b",
     "Indenizatoria - Res. CNJ 14/2006, art. 4o", False),
    (r"\bAUX(ILIO)?[ \-]?FUNERAL\b",
     "Indenizatoria - Res. CNJ 14/2006, art. 4o", False),
    (r"\bAUX(ILIO)?[ \-]?SAUDE\b",
     "Indenizatoria (ressarcimento de plano) - Res. CNJ 14/2006, art. 4o", True),
    (r"\bASSIST(ENCIA)? (PRE[ \-]?ESCOLAR|MEDICA)\b",
     "Indenizatoria/assistencial - Res. CNJ 14/2006, art. 4o", True),
    (r"\bTRANSPORTE (DE )?(MUDANCA|BAGAGEM)\b",
     "Indenizatoria - CF art. 37, par. 11", False),
    # --- direitos sociais (CF art. 7o c/c art. 39, par. 3o) - Res. CNJ 14/2006, art. 4o, II
    # O CPEx lanca o 13o como "ADIC NATAL" e, na antecipacao de junho, como
    # "ADIC NATAL-1 PAR". Somar isso a base do mes estoura o teto num mes em
    # que nao ha excesso nenhum - e o erro que mais infla uma glosa.
    (r"\b(13o?|DECIMO TERCEIRO)\b|\b(GRAT|ADIC)\w*\.? ?NATAL\w*",
     "Gratificacao natalina - fora da base mensal; o confronto com o teto e feito em separado",
     False),
    (r"\b(ADIC(IONAL)? DE FERIAS|1/3 DE FERIAS|TERCO DE FERIAS|ABONO PECUNIARIO)\b",
     "Adicional de ferias - Res. CNJ 14/2006, art. 4o, II", False),
    (r"\bADIC(IONAL)? NOTURNO\b",
     "Direito social - Res. CNJ 14/2006, art. 4o, II", False),
    (r"\b(INSALUBRIDADE|PERICULOSIDADE|ATIV(IDADE)? PENOSA|IRRADIACAO IONIZANTE|RAIOS X)\b",
     "Adicional de atividade nociva - Res. CNJ 14/2006, art. 4o, II", True),
    (r"\b(HORA EXTRA|SERVICO EXTRAORDINARIO)\b",
     "Direito social - Res. CNJ 14/2006, art. 4o, II", False),
    # --- assistenciais / previdenciarias
    (r"\bSAL(ARIO)?[ \-]?FAMILIA\b",
     "Beneficio assistencial/previdenciario - nao integra a remuneracao", False),
    (r"\bABONO (DE )?PERMANENCIA\b",
     "Excluido do teto - Res. CNJ 14/2006, art. 4o, IV", False),
    # --- devolucoes e verbas que nao sao remuneracao do mes
    (r"\b(RESTITUICAO|DEVOLUCAO) (DE )?(I\.?R\.?|IMPOSTO DE RENDA)\b",
     "Devolucao de tributo - nao e remuneracao", False),
    (r"\bDESCONTOS? INDEVIDOS?\b",
     "Ressarcimento - nao e remuneracao", True),
]

# ---------------------------------------------------------------------------
# Receitas que ENTRAM na base do teto (parcelas remuneratorias).
# Listadas para dar fundamento explicito na memoria de calculo.
# ---------------------------------------------------------------------------
PADROES_COMPUTAVEL = [
    (r"\bSOLDO\b",
     "Parcela remuneratoria basica do militar - MP 2.215-10/2001, art. 3o", False),
    (r"\b(PROVENTO|VENCIMENTO) BASICO\b",
     "Parcela remuneratoria basica", False),
    (r"\bSUBSIDIO\b",
     "Parcela remuneratoria basica", False),
    (r"\bPENSAO\b",
     "Especie remuneratoria alcancada pelo art. 37, XI, da CF", False),
    (r"\bADIC(IONAL)?[ \.]?(TP|T\.?)? ?(SV|SERV)",
     "Adicional de tempo de servico - remuneratorio", False),
    (r"\bANUENIO|\bTRIENIO|\bQUINQUENIO",
     "Vantagem pessoal - alcancada expressamente pelo art. 37, XI", False),
    (r"\bADIC(IONAL)?[ \.]? ?HAB",
     "Adicional de habilitacao - remuneratorio", False),
    (r"\bADIC(IONAL)?[ \.]? ?MIL",
     "Adicional militar - remuneratorio", False),
    (r"\bAD(IC(IONAL)?)?[ \.]? ?(C )?ORG.*VOO|\bH ?VOO\b",
     "Adicional de compensacao organica - remuneratorio", False),
    (r"\bADIC(IONAL)?[ \.]? ?(DISPONIB|COMPENS)",
     "Adicional de disponibilidade militar - remuneratorio", False),
    (r"\bADIC(IONAL)?[ \.]? ?PERMANENCIA\b",
     "Adicional de permanencia - remuneratorio", False),
    (r"\bGRAT(IF(ICACAO)?)?[ \.]? ?(REPRESENTACAO|LOCALIDADE|CONDICAO ESPECIAL)",
     "Gratificacao remuneratoria", False),
    (r"\bRT ?- ?RETRIB|\bRETRIB(UICAO)? POR TITULACAO",
     "Retribuicao por titulacao - remuneratoria", False),
    (r"\bVPNI\b|\bVANTAGEM PESSOAL\b|\bOPCAO\b|\bART\.? ?193\b",
     "Vantagem pessoal - o art. 37, XI, da CF alcanca as vantagens pessoais ou de "
     "qualquer outra natureza (STF, RE 606.358, Tema 257)", False),
    (r"\bGRAT(IF(ICACAO)?)?[ \.]? ?DESEMPENHO|\bGDPGPE\b|\bGEAP\b",
     "Gratificacao de desempenho - remuneratoria", False),
    (r"\bFUNCAO COMISSIONADA\b|\bFG\b|\bCD-?\d",
     "Retribuicao de cargo/funcao - remuneratoria", False),
]

# ---------------------------------------------------------------------------
# Descontos (nunca entram na base).
# ---------------------------------------------------------------------------
PADROES_DESCONTO = [
    r"\bI\.?R\.?\b", r"\bIMPOSTO DE RENDA\b", r"\bIRRF\b",
    r"\bFUSEX\b", r"\bFUNSA\b", r"\bPASS\b",
    r"\bP ?MIL\b", r"\bPENSAO MILITAR\b",
    r"\bCONT.*SEGURIDADE\b", r"\bPSS\b", r"\bPREVIDENCIA\b", r"\bFUNPRESP\b",
    r"\bEMPREST", r"\bCONSIGNA", r"\bMENSALIDADE\b", r"\bSINDICAL\b",
    r"\bGBOEX\b", r"\bFUNCEB\b", r"\bFUNDACAO OSORIO\b", r"\bASSIST(ENCIA)? JURID",
    r"\bTAXA\b", r"\bPENSAO ALIMENT", r"\bPLANO DE SAUDE\b", r"\bODONTO\b",
]

# Prefixos de codigo do CPEx / Exercito Brasileiro (Centro de Pagamento do Exercito):
#   B.. e C.. = receitas   |   Z.. = descontos
# Confirmado nas fichas financeiras e contracheques do escritorio.
PREFIXO_CODIGO_CPEX = {"B": "receita", "C": "receita", "Z": "desconto"}


PADRAO_NATALINA = r"\b(13o?|DECIMO TERCEIRO)\b|\b(GRAT|ADIC)\w*\.? ?NATAL\w*"


def e_gratificacao_natalina(descricao):
    """Diz se a rubrica e 13o salario / gratificacao natalina.

    Serve para reporta-la a parte: ela fica fora da base MENSAL, e o confronto
    do 13o com o teto e feito separadamente, segundo a regra do orgao pagador.
    """
    return bool(re.search(PADRAO_NATALINA, _chave(descricao)))


def classificar(descricao, codigo=None, coluna=None):
    """Classifica uma rubrica do contracheque.

    descricao : texto da rubrica (ex.: "ADIC TP SV", "AUXILIO-ALIMENTACAO")
    codigo    : codigo da folha, quando houver (ex.: "C03", "Z01")
    coluna    : "receita" ou "desconto", quando o layout ja separa as colunas

    Retorna dict com natureza, fundamento e conferir (bool).
    """
    texto = _chave(descricao)
    cod = _chave(codigo)

    # 1. A propria glosa ja aplicada pelo orgao pagador - pelo codigo do CPEx
    #    ou pela descricao. Retroativo antes do corrente: "DA I40 AT" casa com
    #    os dois conjuntos de padroes e o retroativo e o mais especifico.
    if cod in CODIGOS_CPEX:
        natureza = CODIGOS_CPEX[cod]
        return {
            "natureza": natureza,
            "fundamento": "Rubrica %s do CPEx - %s" % (
                cod,
                "glosa de abate-teto do mes" if natureza == ABATE_TETO
                else "atrasados de abate-teto de meses anteriores"),
            "conferir": natureza == ABATE_TETO_RETROATIVO,
        }
    for padrao in PADROES_ABATE_TETO_RETROATIVO:
        if re.search(padrao, texto):
            return {
                "natureza": ABATE_TETO_RETROATIVO,
                "fundamento": "Atrasados de abate-teto de meses anteriores, "
                              "cobrados nesta competencia",
                "conferir": True,
            }
    for padrao in PADROES_ABATE_TETO:
        if re.search(padrao, texto):
            return {
                "natureza": ABATE_TETO,
                "fundamento": "Glosa de abate-teto ja praticada pelo orgao pagador",
                "conferir": False,
            }

    # 2. Coluna/codigo dizem que e desconto -> nunca entra na base.
    #    A coluna do contracheque, quando informada, prevalece sobre qualquer
    #    deducao por codigo ou por nome da rubrica.
    if coluna == "desconto":
        e_desconto = True
    elif coluna == "receita":
        e_desconto = False
    else:
        e_desconto = PREFIXO_CODIGO_CPEX.get(cod[:1]) == "desconto" if cod else False
        if not e_desconto:
            for padrao in PADROES_DESCONTO:
                if re.search(padrao, texto):
                    e_desconto = True
                    break
    if e_desconto:
        return {
            "natureza": DESCONTO,
            "fundamento": "Desconto - o teto incide sobre o valor BRUTO "
                          "(Res. CNJ 14/2006, art. 1o, par. unico)",
            "conferir": False,
        }

    # 3. Receita fora da base do teto.
    for padrao, fundamento, conferir in PADROES_NAO_COMPUTAVEL:
        if re.search(padrao, texto):
            return {"natureza": NAO_COMPUTAVEL, "fundamento": fundamento, "conferir": conferir}

    # 4. Receita dentro da base do teto.
    for padrao, fundamento, conferir in PADROES_COMPUTAVEL:
        if re.search(padrao, texto):
            return {"natureza": COMPUTAVEL, "fundamento": fundamento, "conferir": conferir}

    # 5. Desconhecida: entra na base e sai marcada para conferencia manual.
    return {
        "natureza": COMPUTAVEL,
        "fundamento": "Rubrica nao cadastrada - incluida na base por seguranca",
        "conferir": True,
    }
