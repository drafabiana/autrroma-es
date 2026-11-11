# -*- coding: utf-8 -*-
"""
Motor de calculo do abate-teto (art. 37, XI, da CF/88).

O QUE ESTE MODULO CALCULA
-------------------------
Para cada competencia (mes/ano) e para cada vinculo do cliente (cada matricula,
pensao ou provento), apura:

    base computavel = somatorio das parcelas REMUNERATORIAS BRUTAS
                      (exclui indenizatorias, direitos sociais e assistenciais)

    glosa devida    = max(0, base computavel - teto do mes)

e confronta a glosa devida com a glosa que o orgao pagador efetivamente
descontou, produzindo a diferenca a restituir.

OS TRES TEMAS DO STF QUE DECIDEM O CASO
---------------------------------------
Nao basta invocar o teto por vinculo: qual tema rege depende da NATUREZA de
cada vinculo e, havendo pensao, da DATA DO OBITO do instituidor.

Temas 377 (RE 612.975) e 384 (RE 602.043) - julgados em conjunto em 27/04/2020:
    "Nos casos autorizados constitucionalmente de acumulacao de cargos,
    empregos e funcoes, a incidencia do artigo 37, inciso XI, da Constituicao
    Federal, pressupoe a consideracao de cada um dos vinculos formalizados,
    afastada a observancia do teto remuneratorio quanto ao somatorio dos
    ganhos do agente publico."
    -> Alcanca CARGOS, EMPREGOS E FUNCOES do proprio agente. Teto POR VINCULO.

Tema 359 (RE 602.584) - julgado em 06/08/2020, o mesmo Relator:
    "Ocorrida a morte do instituidor da pensao em momento posterior ao da
    Emenda Constitucional no 19/1998, o teto constitucional previsto no inciso
    XI do artigo 37 da Constituicao Federal incide sobre o somatorio de
    remuneracao ou provento e pensao percebida por servidor."
    -> Alcanca PENSAO somada a remuneracao/provento PROPRIO, quando o obito e
       posterior a 04/06/1998. Teto sobre a SOMA.

O proprio acordao do RE 602.584 separa as duas situacoes: "Ja agora, o conflito
de interesses diz respeito a institutos distintos, a saber: remuneracao e
pensao; proventos e pensao."

Por isso este modulo NAO escolhe o criterio mais favoravel: ele agrupa os
vinculos conforme o tema aplicavel (ver agrupar_para_teto) e apura tres numeros
por competencia:

  glosa_criterio_vinculo    cada vinculo isolado (377/384 puro) - piso do pedido
  glosa_criterio_soma       tudo somado - o que a Administracao costuma aplicar
  glosa_criterio_aplicavel  o agrupamento que os tres temas determinam

A diferenca entre o APLICAVEL e o que a folha efetivamente descontou e o que se
pede. Usar o "por vinculo" como se fosse sempre a resposta certa e o caminho
mais curto para perder a acao em que ha pensao com obito pos-EC 19/1998.

REGRA DE OURO DO ESCRITORIO
---------------------------
O teto incide sobre o valor BRUTO, antes de IR e contribuicao previdenciaria
(Res. CNJ 14/2006, art. 1o, par. unico). O campo TOTAL do contracheque e do
espelho da ficha financeira do CPEx e o LIQUIDO - usa-lo como base subestima a
glosa e invalida o calculo. Ver validar_bruto().
"""
import os
import sys
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "config"))

from teto_constitucional import teto_vigente  # noqa: E402
from rubricas import (  # noqa: E402
    classificar, e_gratificacao_natalina, COMPUTAVEL, NAO_COMPUTAVEL, DESCONTO,
    ABATE_TETO, ABATE_TETO_RETROATIVO,
)

CRITERIO_VINCULO = "VINCULO"
CRITERIO_SOMA = "SOMA"
CRITERIO_APLICAVEL = "APLICAVEL"

# Natureza do vinculo - decide qual tema do STF o alcanca.
PROPRIO = "PROPRIO"   # cargo, emprego, funcao ou provento da propria aposentadoria
PENSAO = "PENSAO"     # pensao deixada por instituidor

# ---------------------------------------------------------------------------
# Marco temporal do Tema 359: qual emenda separa o "antes" do "depois".
#
# EC 19, de 4/06/1998 (publicada em 5/06/1998) - reforma administrativa. E a
#   emenda que a TESE do Tema 359 menciona literalmente.
# EC 20, de 15/12/1998 (publicada em 16/12/1998) - reforma da previdencia.
#   Foi ela que acrescentou o art. 40, par. 11, da CF - o dispositivo que manda
#   aplicar o limite do art. 37, XI, "a soma total dos proventos de inatividade"
#   - e que, nas palavras do voto vencido do Min. CELSO DE MELLO no proprio
#   RE 602.584, foi quando "o provento de pensao passou a constar expressamente
#   do limite estabelecido no art. 37, inciso XI, da Constituicao Federal".
#
# O escritorio sustenta a EC 20 nos casos em que o instituidor faleceu entre as
# duas emendas. Como as duas leituras existem, a calculadora apura SEMPRE pelos
# dois marcos e reporta os dois numeros quando divergem - ver zona_cinzenta.
EC_19 = date(1998, 6, 4)
EC_20 = date(1998, 12, 15)

MARCO_EC19 = "EC19"   # leitura literal da tese do Tema 359
MARCO_EC20 = "EC20"   # tese do escritorio: art. 40, par. 11, da CF

MARCOS = {
    MARCO_EC19: {
        "data": EC_19,
        "rotulo": "EC 19/1998 (4/06/1998)",
        "fundamento": "redação literal da tese do Tema 359",
    },
    MARCO_EC20: {
        "data": EC_20,
        "rotulo": "EC 20/1998 (15/12/1998)",
        "fundamento": (
            "art. 40, § 11, da CF, acrescentado pela EC 20/1998 — foi quando a "
            "pensão passou a constar expressamente do limite do art. 37, XI "
            "(voto do Min. Celso de Mello no RE 602.584)"),
    },
}

CENTAVO = Decimal("0.01")


def _d(valor):
    """Converte para Decimal com 2 casas. Aceita '1.234,56', '1234.56', numero."""
    if isinstance(valor, Decimal):
        return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)
    if isinstance(valor, str):
        texto = valor.strip().replace("R$", "").replace(" ", "")
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        valor = texto or "0"
    return Decimal(str(valor)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


@dataclass
class Parcela:
    """Uma linha do contracheque."""
    descricao: str
    valor: Decimal
    codigo: str = ""
    coluna: str = None          # "receita" | "desconto" | None (deduzir)
    natureza: str = ""          # preenchido pela classificacao
    fundamento: str = ""
    conferir: bool = False

    def __post_init__(self):
        self.valor = _d(self.valor)
        if not self.natureza:
            resultado = classificar(self.descricao, self.codigo, self.coluna)
            self.natureza = resultado["natureza"]
            self.fundamento = resultado["fundamento"]
            self.conferir = resultado["conferir"]


@dataclass
class Vinculo:
    """Um vinculo do cliente numa competencia: uma matricula, pensao ou provento.

    Cada vinculo e uma unidade de incidencia do teto no criterio do STF. Dois
    vinculos so podem ser tratados separadamente se a acumulacao for LICITA -
    o fundamento da licitude vai em 'fundamento_acumulacao' e aparece na
    memoria de calculo.
    """
    nome: str                       # "Pensao militar - instituidor Cel. Fulano"
    orgao: str = ""                 # "Exercito Brasileiro / CPEx"
    matricula: str = ""             # PREC-CP, SIAPE, etc.
    parcelas: list = field(default_factory=list)
    fundamento_acumulacao: str = ""
    natureza: str = PROPRIO         # PROPRIO | PENSAO - ver agrupar_para_teto
    obito_instituidor: date = None  # so para PENSAO: decide o Tema 359

    def brutas(self):
        return [p for p in self.parcelas if p.natureza in (COMPUTAVEL, NAO_COMPUTAVEL)]

    def total_bruto(self):
        return _d(sum((p.valor for p in self.brutas()), Decimal("0")))

    def base_computavel(self):
        return _d(sum(
            (p.valor for p in self.parcelas if p.natureza == COMPUTAVEL), Decimal("0")))

    def total_nao_computavel(self):
        return _d(sum(
            (p.valor for p in self.parcelas if p.natureza == NAO_COMPUTAVEL), Decimal("0")))

    def total_natalina(self):
        """13o salario pago na competencia.

        Fica FORA da base mensal - somar o 13o ao mes estoura o teto num mes em
        que nao ha excesso. O confronto do 13o com o teto e feito em separado,
        segundo a regra do orgao pagador, e esta calculadora apenas o destaca.
        """
        return _d(sum(
            (p.valor for p in self.parcelas
             if p.natureza == NAO_COMPUTAVEL and e_gratificacao_natalina(p.descricao)),
            Decimal("0")))

    def total_descontos(self):
        return _d(sum(
            (p.valor for p in self.parcelas if p.natureza == DESCONTO), Decimal("0")))

    def glosa_aplicada(self):
        """Abate-teto do proprio mes, ja descontado pelo orgao pagador."""
        return _d(sum(
            (p.valor for p in self.parcelas if p.natureza == ABATE_TETO), Decimal("0")))

    def glosa_retroativa(self):
        """Abate-teto de meses anteriores cobrado nesta competencia.

        Fica fora do confronto mensal com o teto - senao o mes em que o orgao
        pagador cobrou os atrasados apareceria com uma glosa absurda - mas entra
        no total do que foi retido do cliente.
        """
        return _d(sum(
            (p.valor for p in self.parcelas if p.natureza == ABATE_TETO_RETROATIVO),
            Decimal("0")))

    def pendencias(self):
        return [p for p in self.parcelas if p.conferir]


@dataclass
class Competencia:
    """Um mes de referencia, com todos os vinculos do cliente."""
    mes: int
    ano: int
    vinculos: list = field(default_factory=list)

    @property
    def rotulo(self):
        return "%02d/%04d" % (self.mes, self.ano)

    @property
    def data(self):
        return date(self.ano, self.mes, 1)


def agrupar_para_teto(vinculos, marco=MARCO_EC19):
    """Agrupa os vinculos conforme o tema do STF que os alcanca.

    Cada grupo e uma unidade de incidencia do teto: o limite e conferido sobre
    a soma das bases dentro do grupo. Um grupo com um so vinculo equivale ao
    teto por vinculo.

    Regras, extraidas das teses:

    a) Vinculos PROPRIOS (cargo, emprego, funcao, proventos da propria
       aposentadoria): cada um e um grupo - Temas 377 e 384.

    b) PENSAO com obito do instituidor POSTERIOR ao marco somada a
       remuneracao/provento proprio: um unico grupo - Tema 359.

    c) PENSAO com obito ANTERIOR ou IGUAL ao marco: grupo isolado. O Tema 359
       so alcanca obito posterior a emenda.

       O marco e EC 19 (4/06/1998) ou EC 20 (15/12/1998), conforme o parametro
       'marco' - ver a nota sobre MARCOS no inicio do modulo.

    d) Duas ou mais PENSOES, sem vinculo proprio: grupos isolados, marcados
       como CONTROVERTIDO - o Tema 359 fala em "remuneracao ou provento e
       pensao", nao em pensao com pensao. E a hipotese do acervo do escritorio
       (duas pensoes militares, art. 29 da Lei 3.765/60 na redacao original).

    e) Pensao sem a data do obito informada: tratada como posterior a EC 19
       (leitura conservadora, que produz a glosa MAIOR) e marcada para conferir.

    Devolve lista de dicts: nome, vinculos, tema, fundamento, controvertido.
    """
    proprios = [v for v in vinculos if v.natureza != PENSAO]
    pensoes = [v for v in vinculos if v.natureza == PENSAO]

    data_marco = MARCOS[marco]["data"]
    rotulo_marco = MARCOS[marco]["rotulo"]
    pensoes_pos = [v for v in pensoes
                   if v.obito_instituidor is None or v.obito_instituidor > data_marco]
    pensoes_pre = [v for v in pensoes
                   if v.obito_instituidor is not None and v.obito_instituidor <= data_marco]
    sem_data = [v for v in pensoes if v.obito_instituidor is None]

    grupos = []

    if pensoes_pos and proprios:
        # Tema 359: pensao + provento/remuneracao propria -> soma.
        nomes = [v.nome for v in proprios + pensoes_pos]
        grupos.append({
            "nome": " + ".join(nomes),
            "vinculos": proprios + pensoes_pos,
            "tema": "Tema 359 (RE 602.584)",
            "fundamento": (
                "Óbito do instituidor posterior à %s: o teto incide sobre o "
                "somatório de remuneração ou provento e pensão" % rotulo_marco),
            "controvertido": len(proprios) > 1 or bool(sem_data),
        })
    else:
        for vinculo in proprios:
            grupos.append({
                "nome": vinculo.nome,
                "vinculos": [vinculo],
                "tema": "Temas 377 e 384 (RE 612.975 e RE 602.043)",
                "fundamento": (
                    "Acumulação constitucionalmente autorizada: o teto é aferido "
                    "em cada vínculo formalizado, não sobre a soma"),
                "controvertido": False,
            })
        for vinculo in pensoes_pos:
            grupos.append({
                "nome": vinculo.nome,
                "vinculos": [vinculo],
                "tema": "Tema 359 (RE 602.584) - alcance controvertido",
                "fundamento": (
                    "Pensão sem remuneração ou provento próprio a somar. O Tema "
                    "359 alcança “remuneração ou provento e pensão”, não pensão "
                    "com pensão — sustentar os Temas 377 e 384"),
                "controvertido": True,
            })

    for vinculo in pensoes_pre:
        grupos.append({
            "nome": vinculo.nome,
            "vinculos": [vinculo],
            "tema": "Tema 359 (RE 602.584), a contrario",
            "fundamento": (
                "Óbito do instituidor anterior à %s: fora do alcance do Tema "
                "359, o teto não incide sobre a soma" % rotulo_marco),
            "controvertido": False,
        })

    return grupos


def calcular_competencia(competencia, marco=MARCO_EC19):
    """Apura a glosa de uma competencia pelos dois criterios.

    Retorna um dict com o detalhamento por vinculo e os dois totais.
    """
    faixa = teto_vigente(competencia.data)
    teto = faixa["valor"]

    detalhe_vinculos = []
    for vinculo in competencia.vinculos:
        base = vinculo.base_computavel()
        excedente = base - teto
        glosa = excedente if excedente > 0 else Decimal("0.00")
        detalhe_vinculos.append({
            "nome": vinculo.nome,
            "orgao": vinculo.orgao,
            "matricula": vinculo.matricula,
            "fundamento_acumulacao": vinculo.fundamento_acumulacao,
            "total_bruto": vinculo.total_bruto(),
            "nao_computavel": vinculo.total_nao_computavel(),
            "base_computavel": base,
            "descontos": vinculo.total_descontos(),
            "glosa_por_vinculo": _d(glosa),
            "glosa_aplicada": vinculo.glosa_aplicada(),
            "glosa_retroativa": vinculo.glosa_retroativa(),
            "natalina": vinculo.total_natalina(),
            "parcelas": vinculo.parcelas,
            "pendencias": vinculo.pendencias(),
        })

    base_somada = _d(sum((v["base_computavel"] for v in detalhe_vinculos), Decimal("0")))
    excedente_soma = base_somada - teto
    glosa_soma = _d(excedente_soma if excedente_soma > 0 else Decimal("0.00"))
    glosa_por_vinculo = _d(sum((v["glosa_por_vinculo"] for v in detalhe_vinculos), Decimal("0")))

    # Criterio aplicavel: agrupa os vinculos conforme o tema do STF que os
    # alcanca e confere o teto sobre a base de cada grupo. Apura pelos DOIS
    # marcos temporais do Tema 359 - o escolhido e o outro - para que a
    # divergencia entre as duas leituras fique sempre visivel.
    def apurar_por_marco(qual):
        grupos = []
        for grupo in agrupar_para_teto(competencia.vinculos, qual):
            base_grupo = _d(sum((v.base_computavel() for v in grupo["vinculos"]), Decimal("0")))
            excedente = base_grupo - teto
            grupos.append({
                "nome": grupo["nome"],
                "tema": grupo["tema"],
                "fundamento": grupo["fundamento"],
                "controvertido": grupo["controvertido"],
                "vinculos": [v.nome for v in grupo["vinculos"]],
                "base": base_grupo,
                "glosa": _d(excedente if excedente > 0 else Decimal("0.00")),
            })
        return grupos, _d(sum((g["glosa"] for g in grupos), Decimal("0")))

    outro_marco = MARCO_EC20 if marco == MARCO_EC19 else MARCO_EC19
    detalhe_grupos, glosa_aplicavel = apurar_por_marco(marco)
    grupos_alt, glosa_alternativa = apurar_por_marco(outro_marco)

    # Obito entre as duas emendas: as leituras divergem e o caso e sensivel.
    zona_cinzenta = [
        v.nome for v in competencia.vinculos
        if v.natureza == PENSAO and v.obito_instituidor is not None
        and EC_19 < v.obito_instituidor <= EC_20
    ]
    glosa_aplicada = _d(sum((v["glosa_aplicada"] for v in detalhe_vinculos), Decimal("0")))
    glosa_retroativa = _d(sum((v["glosa_retroativa"] for v in detalhe_vinculos), Decimal("0")))
    natalina = _d(sum((v["natalina"] for v in detalhe_vinculos), Decimal("0")))

    # Quanto foi glosado a mais do que a tese do escritorio admite.
    diferenca_criterios = _d(glosa_soma - glosa_por_vinculo)
    # Quanto o orgao pagador descontou a mais do que os temas do STF autorizam.
    # Entra tambem o que foi cobrado como atrasado: aquilo tambem saiu do bolso
    # do cliente. Quando ha atrasados, conferir a quais competencias se referem,
    # para nao pedir duas vezes o mesmo mes.
    a_restituir = _d(glosa_aplicada + glosa_retroativa - glosa_aplicavel)
    if a_restituir < 0:
        a_restituir = Decimal("0.00")

    conferencia = _conferir_glosa(glosa_aplicada, glosa_aplicavel)
    conferencia_alt = _conferir_glosa(glosa_aplicada, glosa_alternativa)

    return {
        "competencia": competencia.rotulo,
        "data": competencia.data,
        "teto": teto,
        "teto_fonte": faixa["fonte"],
        "teto_observacao": faixa["observacao"],
        "vinculos": detalhe_vinculos,
        "base_somada": base_somada,
        "glosa_criterio_soma": glosa_soma,
        "glosa_criterio_vinculo": glosa_por_vinculo,
        "glosa_criterio_aplicavel": glosa_aplicavel,
        "glosa_criterio_alternativo": glosa_alternativa,
        "marco": marco,
        "marco_rotulo": MARCOS[marco]["rotulo"],
        "marco_alternativo": outro_marco,
        "marco_alternativo_rotulo": MARCOS[outro_marco]["rotulo"],
        "zona_cinzenta": zona_cinzenta,
        "grupos": detalhe_grupos,
        "grupos_alternativos": grupos_alt,
        "conferencia": conferencia,
        "conferencia_alternativa": conferencia_alt,
        "glosa_aplicada": glosa_aplicada,
        "glosa_retroativa": glosa_retroativa,
        "natalina": natalina,
        "diferenca_entre_criterios": diferenca_criterios,
        "a_restituir": a_restituir,
        "pendencias": [p for v in detalhe_vinculos for p in v["pendencias"]],
    }


TOLERANCIA = Decimal("0.05")   # centavos de arredondamento da folha

# Vereditos da conferencia da glosa lancada pelo orgao pagador.
GLOSA_CORRETA = "CORRETA"
GLOSA_INDEVIDA = "INDEVIDA"        # descontou sem que houvesse excesso
GLOSA_A_MAIOR = "A MAIOR"          # descontou mais do que o devido
GLOSA_A_MENOR = "A MENOR"          # descontou menos do que o devido
GLOSA_NAO_LANCADA = "NAO LANCADA"  # havia excesso e nada foi descontado
SEM_GLOSA = "SEM GLOSA"            # nao havia excesso e nada foi descontado


def _conferir_glosa(aplicada, devida):
    """Confronta o que o orgao pagador descontou com o que os temas autorizam.

    E a auditoria do mes: diz se a Forca lancou a glosa certa, a maior, a menor,
    indevidamente, ou se deixou de lancar.
    """
    diferenca = _d(aplicada - devida)
    if abs(diferenca) <= TOLERANCIA:
        veredito = SEM_GLOSA if devida == 0 and aplicada == 0 else GLOSA_CORRETA
    elif devida == 0:
        veredito = GLOSA_INDEVIDA
    elif aplicada == 0:
        veredito = GLOSA_NAO_LANCADA
    elif diferenca > 0:
        veredito = GLOSA_A_MAIOR
    else:
        veredito = GLOSA_A_MENOR
    return {
        "veredito": veredito,
        "aplicada": _d(aplicada),
        "devida": _d(devida),
        "diferenca": diferenca,
    }


def calcular_periodo(competencias, data_ajuizamento=None, marco=MARCO_EC19):
    """Apura um periodo inteiro e aplica o corte prescricional quinquenal.

    data_ajuizamento : date da propositura (ou da prevista). Competencias
                       anteriores a 5 anos dessa data saem marcadas como
                       prescritas (Decreto 20.910/1932, art. 1o) e nao entram
                       nos totais.
    """
    corte = None
    if data_ajuizamento:
        corte = date(data_ajuizamento.year - 5, data_ajuizamento.month, 1)

    linhas = []
    for competencia in sorted(competencias, key=lambda c: c.data):
        resultado = calcular_competencia(competencia, marco)
        resultado["prescrita"] = bool(corte and resultado["data"] < corte)
        linhas.append(resultado)

    ativas = [linha for linha in linhas if not linha["prescrita"]]

    def soma(chave):
        return _d(sum((linha[chave] for linha in ativas), Decimal("0")))

    return {
        "linhas": linhas,
        "data_ajuizamento": data_ajuizamento,
        "corte_prescricional": corte,
        "competencias_apuradas": len(ativas),
        "competencias_prescritas": len(linhas) - len(ativas),
        "total_glosa_criterio_soma": soma("glosa_criterio_soma"),
        "total_glosa_criterio_vinculo": soma("glosa_criterio_vinculo"),
        "total_glosa_criterio_aplicavel": soma("glosa_criterio_aplicavel"),
        "total_glosa_criterio_alternativo": soma("glosa_criterio_alternativo"),
        "marco": marco,
        "marco_rotulo": MARCOS[marco]["rotulo"],
        "marco_fundamento": MARCOS[marco]["fundamento"],
        "marco_alternativo_rotulo": MARCOS[
            MARCO_EC20 if marco == MARCO_EC19 else MARCO_EC19]["rotulo"],
        "zona_cinzenta": sorted({nome for linha in ativas for nome in linha["zona_cinzenta"]}),
        "meses_com_glosa": [
            linha for linha in ativas
            if linha["glosa_aplicada"] > 0 or linha["glosa_retroativa"] > 0],
        "meses_com_divergencia": [
            linha for linha in ativas
            if linha["conferencia"]["veredito"] not in (GLOSA_CORRETA, SEM_GLOSA)],
        "total_glosa_aplicada": soma("glosa_aplicada"),
        "total_glosa_retroativa": soma("glosa_retroativa"),
        "total_natalina": soma("natalina"),
        "total_diferenca_entre_criterios": soma("diferenca_entre_criterios"),
        "total_a_restituir": soma("a_restituir"),
        "total_retido": _d(soma("glosa_aplicada") + soma("glosa_retroativa")),
        "pendencias": [p for linha in linhas for p in linha["pendencias"]],
    }


def validar_bruto(vinculo, total_informado):
    """Confere o bruto apurado contra um total informado no contracheque.

    Devolve (ok, mensagem). Serve para pegar o erro mais comum: usar o campo
    TOTAL do espelho do CPEx, que e o LIQUIDO, como se fosse o bruto.
    """
    total_informado = _d(total_informado)
    bruto = vinculo.total_bruto()
    liquido = _d(bruto - vinculo.total_descontos()
                 - vinculo.glosa_aplicada() - vinculo.glosa_retroativa())

    if total_informado == bruto:
        return True, "Total informado confere com o bruto apurado (%s)." % fmt(bruto)
    if total_informado == liquido:
        return False, (
            "ATENCAO: o total informado (%s) e o LIQUIDO, nao o bruto. O teto "
            "incide sobre o bruto de %s (Res. CNJ 14/2006, art. 1o, par. unico)."
            % (fmt(total_informado), fmt(bruto))
        )
    return False, (
        "Total informado (%s) nao bate nem com o bruto (%s) nem com o liquido "
        "(%s) apurados. Conferir as rubricas lancadas."
        % (fmt(total_informado), fmt(bruto), fmt(liquido))
    )


def fmt(valor):
    """Formata Decimal no padrao brasileiro: R$ 1.234,56."""
    texto = "{:,.2f}".format(_d(valor))
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")
