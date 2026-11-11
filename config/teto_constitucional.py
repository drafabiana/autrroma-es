# -*- coding: utf-8 -*-
"""
Teto remuneratorio constitucional - subsidio mensal de Ministro do STF.

Art. 37, XI, da CF/88: a remuneracao, os proventos, as pensoes ou outra especie
remuneratoria, percebidos cumulativamente ou nao, incluidas as vantagens pessoais
ou de qualquer outra natureza, NAO PODEM EXCEDER o subsidio mensal, em especie,
dos Ministros do Supremo Tribunal Federal.

Este modulo e a UNICA fonte do valor do teto no repositorio. Nenhuma automacao
hardcoda o valor: todas chamam teto_vigente(competencia).

O valor e sempre BRUTO (antes de IR e contribuicao previdenciaria) - Resolucao
CNJ 14/2006, art. 1o, paragrafo unico. Comparar o teto com o LIQUIDO do
contracheque e o erro mais comum nesse tipo de acao.

>>> Ao editar: acrescentar a faixa nova NO FIM da lista, com a lei que a fixou.
"""
from datetime import date
from decimal import Decimal


# Faixas de vigencia do subsidio de Ministro do STF, em ordem cronologica.
# 'inicio' e o primeiro mes de competencia em que o valor vale.
TABELA_TETO_STF = [
    {
        "inicio": date(2004, 1, 1),
        "valor": Decimal("19115.19"),
        "fonte": "EC 41/2003, art. 8º",
        "observacao": (
            "Valor de transicao (maior remuneracao de Ministro do STF na data da "
            "EC 41/2003), aplicado ate a lei de fixacao do subsidio. Periodo hoje "
            "fora do quinquenio prescricional - conferir antes de usar."
        ),
    },
    {
        "inicio": date(2005, 1, 1),
        "valor": Decimal("21500.00"),
        "fonte": "Lei 11.143/2005, art. 1º",
        "observacao": "",
    },
    {
        "inicio": date(2006, 1, 1),
        "valor": Decimal("24500.00"),
        "fonte": "Lei 11.143/2005, art. 1º",
        "observacao": "",
    },
    {
        "inicio": date(2009, 9, 1),
        "valor": Decimal("25725.00"),
        "fonte": "Lei 12.041/2009 (reajuste de 5%)",
        "observacao": "",
    },
    {
        "inicio": date(2010, 2, 1),
        "valor": Decimal("26723.13"),
        "fonte": "Lei 12.041/2009 (reajuste de 3,88%)",
        "observacao": "",
    },
    {
        "inicio": date(2013, 1, 1),
        "valor": Decimal("28059.29"),
        "fonte": "Lei 12.771/2012, art. 1º",
        "observacao": "",
    },
    {
        "inicio": date(2014, 1, 1),
        "valor": Decimal("29462.25"),
        "fonte": "Lei 12.771/2012, art. 1º",
        "observacao": "",
    },
    {
        "inicio": date(2015, 1, 1),
        "valor": Decimal("33763.00"),
        "fonte": "Lei 13.091/2015, art. 1º",
        "observacao": (
            "A Lei 13.091/2015 fixou 33.763,00 a partir de 01/01/2015 e prevalece "
            "sobre os R$ 30.935,36 que a Lei 12.771/2012 previa para o mesmo mes."
        ),
    },
    {
        "inicio": date(2019, 1, 1),
        "valor": Decimal("39293.32"),
        "fonte": "Lei 13.752/2018, art. 1º",
        "observacao": (
            "A lei e de 26/11/2018 e os efeitos financeiros foram implementados a "
            "partir de 01/01/2019. Ha peticoes que sustentam efeitos desde "
            "01/11/2018 - se o caso alcancar nov/dez-2018, conferir a folha do "
            "orgao pagador antes de fechar o calculo."
        ),
    },
    {
        "inicio": date(2023, 4, 1),
        "valor": Decimal("41650.92"),
        "fonte": "Lei 14.520/2023, art. 1º (1ª parcela)",
        "observacao": "",
    },
    {
        "inicio": date(2024, 2, 1),
        "valor": Decimal("44008.52"),
        "fonte": "Lei 14.520/2023, art. 1º (2ª parcela)",
        "observacao": "",
    },
    {
        "inicio": date(2025, 2, 1),
        "valor": Decimal("46366.19"),
        "fonte": "Lei 14.520/2023, art. 1º (3ª parcela)",
        "observacao": "Valor vigente. Conferir se houve lei posterior de reajuste.",
    },
]


class TetoNaoCadastrado(Exception):
    """Competencia anterior a primeira faixa cadastrada."""


def teto_vigente(competencia):
    """Retorna a faixa do teto vigente na competencia (date ou 'MM/AAAA').

    Devolve um dict com 'valor' (Decimal), 'fonte', 'observacao' e 'inicio'.
    """
    comp = _normalizar(competencia)
    faixa = None
    for item in TABELA_TETO_STF:
        if item["inicio"] <= comp:
            faixa = item
        else:
            break
    if faixa is None:
        raise TetoNaoCadastrado(
            "Competencia %s e anterior a primeira faixa cadastrada (%s)."
            % (comp.strftime("%m/%Y"), TABELA_TETO_STF[0]["inicio"].strftime("%m/%Y"))
        )
    return dict(faixa)


def valor_teto(competencia):
    """Atalho: so o valor (Decimal) do teto na competencia."""
    return teto_vigente(competencia)["valor"]


def _normalizar(competencia):
    """Aceita date/datetime ou string 'MM/AAAA' e devolve o 1o dia do mes."""
    if isinstance(competencia, str):
        texto = competencia.strip().replace("-", "/")
        partes = texto.split("/")
        if len(partes) != 2:
            raise ValueError("Competencia deve ser 'MM/AAAA', recebido: %r" % competencia)
        mes, ano = int(partes[0]), int(partes[1])
        if ano < 100:
            raise ValueError("Informe o ano com 4 digitos: %r" % competencia)
        return date(ano, mes, 1)
    return date(competencia.year, competencia.month, 1)
