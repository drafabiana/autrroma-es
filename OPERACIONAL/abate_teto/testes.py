# -*- coding: utf-8 -*-
"""
Testes da calculadora de abate-teto.

Rodar:  python OPERACIONAL/abate_teto/testes.py

Sem dependencia de framework - o repositorio nao usa pytest. Cada teste e uma
funcao testar_*; o roteador no fim executa todas e conta as falhas.

Os casos vem dos contracheques REAIS do escritorio (CPEx / SIAPE) e das duas
armadilhas que ja apareceram na pratica: usar o liquido como base e somar o
13o ao mes.
"""
import io
import os
import sys
from datetime import date
from decimal import Decimal

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config"))

from calculadora import (  # noqa: E402
    Parcela, Vinculo, Competencia, calcular_competencia, calcular_periodo,
    agrupar_para_teto, validar_bruto, fmt, _d,
    PROPRIO, PENSAO, EC_19, EC_20, MARCO_EC19, MARCO_EC20,
    GLOSA_CORRETA, GLOSA_INDEVIDA, GLOSA_A_MAIOR, GLOSA_A_MENOR,
    GLOSA_NAO_LANCADA, SEM_GLOSA,
)
from rubricas import (  # noqa: E402
    classificar, e_gratificacao_natalina, COMPUTAVEL, NAO_COMPUTAVEL, DESCONTO,
    ABATE_TETO, ABATE_TETO_RETROATIVO,
)
from teto_constitucional import teto_vigente, TetoNaoCadastrado  # noqa: E402


def _pensao_exercito_fev2025():
    """Contracheque real: cliente do acervo, CPEx, fev/2025.
    Bruto impresso na folha: 23.284,80 | descontos: 11.223,73 | liquido: 12.061,07
    """
    return Vinculo(
        nome="Pensao militar (Exercito)", orgao="CPEx", matricula="98 2762508",
        parcelas=[
            Parcela("SOLDO (MAJ)", "11.088,00", "C01", "receita"),
            Parcela("ADIC TP SV", "4.435,20", "C03", "receita"),
            Parcela("ADIC HAB", "4.989,60", "C06", "receita"),
            Parcela("ADIC MIL", "2.772,00", "C08", "receita"),
            Parcela("FUSEX", "698,54", "Z01", "desconto"),
            Parcela("P MIL", "2.444,90", "Z02", "desconto"),
            Parcela("IR", "4.450,77", "Z10", "desconto"),
            Parcela("P MIL EXT", "698,54", "ZKA", "desconto"),
            Parcela("BB EMPREST", "2.930,98", "ZXR", "desconto"),
        ])


def _aposentadoria_ufrj_mar2025():
    """Contracheque real: SIAPE/UFRJ, mar/2025. Bruto impresso: 20.816,47."""
    return Vinculo(
        nome="Aposentadoria (UFRJ)", orgao="UFRJ/SIAPE", matricula="011244623",
        parcelas=[
            Parcela("PROVENTO BASICO", "9.462,03", coluna="receita"),
            Parcela("ANUENIO-ART.244,LEI 8112/90 AP", "473,10", coluna="receita"),
            Parcela("RT - RETRIB. POR TITULACAO AP", "10.881,34", coluna="receita"),
            Parcela("MENSALIDADE SINDICAL - ADUFRJ", "166,53", coluna="desconto"),
            Parcela("CONT P.SEGURIDADE SOCIAL AP", "1.972,50", coluna="desconto"),
            Parcela("IMPOSTO DE RENDA APO/PENSIONIS", "4.181,81", coluna="desconto"),
        ])


# ---------------------------------------------------------------------------
def testar_tabela_do_teto():
    assert teto_vigente("01/2016")["valor"] == Decimal("33763.00")
    assert teto_vigente("12/2018")["valor"] == Decimal("33763.00")
    assert teto_vigente("01/2019")["valor"] == Decimal("39293.32")
    assert teto_vigente("03/2023")["valor"] == Decimal("39293.32")
    assert teto_vigente("04/2023")["valor"] == Decimal("41650.92")
    assert teto_vigente("01/2024")["valor"] == Decimal("41650.92")
    assert teto_vigente("02/2024")["valor"] == Decimal("44008.52")
    assert teto_vigente("01/2025")["valor"] == Decimal("44008.52")
    assert teto_vigente("02/2025")["valor"] == Decimal("46366.19")
    assert teto_vigente(date(2026, 9, 1))["valor"] == Decimal("46366.19")
    try:
        teto_vigente("01/1999")
    except TetoNaoCadastrado:
        pass
    else:
        raise AssertionError("competencia anterior a tabela deveria falhar")


def testar_base_bruta_bate_com_a_folha():
    """O bruto apurado tem de bater com o total impresso no contracheque."""
    ok, _ = validar_bruto(_pensao_exercito_fev2025(), "23.284,80")
    assert ok
    ok, _ = validar_bruto(_aposentadoria_ufrj_mar2025(), "20.816,47")
    assert ok


def testar_liquido_nao_passa_por_bruto():
    """A armadilha classica: usar o TOTAL do espelho, que e o liquido."""
    ok, mensagem = validar_bruto(_pensao_exercito_fev2025(), "12.061,07")
    assert not ok
    assert "LIQUIDO" in mensagem


def testar_glosa_por_vinculo_e_por_soma():
    """Fev/2025: nenhum vinculo estoura sozinho e a soma tambem nao."""
    resultado = calcular_competencia(Competencia(
        2, 2025, [_pensao_exercito_fev2025(), _aposentadoria_ufrj_mar2025()]))
    assert resultado["teto"] == Decimal("46366.19")
    assert resultado["base_somada"] == Decimal("44101.27")
    assert resultado["glosa_criterio_soma"] == Decimal("0.00")
    assert resultado["glosa_criterio_vinculo"] == Decimal("0.00")


def testar_glosa_so_existe_pela_soma():
    """Dois vinculos abaixo do teto que, somados, o ultrapassam.

    E o coracao da tese: a glosa e inteiramente fruto do criterio da soma.
    """
    a = Vinculo(nome="Pensao do pai", parcelas=[Parcela("SOLDO", "30.000,00", coluna="receita")])
    b = Vinculo(nome="Pensao do conjuge", parcelas=[Parcela("SOLDO", "25.000,00", coluna="receita")])
    resultado = calcular_competencia(Competencia(6, 2026, [a, b]))
    # teto 46.366,19; soma 55.000,00
    assert resultado["glosa_criterio_soma"] == Decimal("8633.81")
    assert resultado["glosa_criterio_vinculo"] == Decimal("0.00")
    assert resultado["diferenca_entre_criterios"] == Decimal("8633.81")


def testar_glosa_legitima_em_vinculo_unico():
    """Vinculo unico acima do teto: a glosa e devida pelos dois criterios."""
    v = Vinculo(nome="Provento unico", parcelas=[Parcela("SUBSIDIO", "50.000,00", coluna="receita")])
    resultado = calcular_competencia(Competencia(6, 2026, [v]))
    assert resultado["glosa_criterio_soma"] == Decimal("3633.81")
    assert resultado["glosa_criterio_vinculo"] == Decimal("3633.81")
    assert resultado["diferenca_entre_criterios"] == Decimal("0.00")


def testar_indenizatorias_ficam_fora_da_base():
    v = Vinculo(nome="Militar da ativa", parcelas=[
        Parcela("SOLDO", "46.000,00", coluna="receita"),
        Parcela("AUXILIO-ALIMENTACAO", "1.000,00", coluna="receita"),
        Parcela("AUXILIO-FARDAMENTO", "500,00", coluna="receita"),
        Parcela("AJUDA DE CUSTO", "2.000,00", coluna="receita"),
    ])
    resultado = calcular_competencia(Competencia(6, 2026, [v]))
    assert resultado["vinculos"][0]["total_bruto"] == Decimal("49500.00")
    assert resultado["vinculos"][0]["base_computavel"] == Decimal("46000.00")
    # 46.000,00 < 46.366,19: sem as indenizatorias nao ha glosa nenhuma.
    assert resultado["glosa_criterio_soma"] == Decimal("0.00")


def testar_decimo_terceiro_fora_da_base_mensal():
    """Regressao: 'ADIC NATAL' somado ao mes criava glosa onde nao havia.

    Novembro do CPEx traz soldo + 13o. Somados, estouram o teto; so o mes, nao.
    """
    v = Vinculo(nome="Pensao militar", parcelas=[
        Parcela("SOLDO", "11.088,00", "C01", "receita"),
        Parcela("ADIC TP SV", "4.435,20", "C03", "receita"),
        Parcela("ADIC HAB", "4.989,60", "C06", "receita"),
        Parcela("ADIC MIL", "2.772,00", "C08", "receita"),
        Parcela("ADIC NATAL", "23.284,80", "C60", "receita"),
    ])
    resultado = calcular_competencia(Competencia(11, 2024, [v]))
    assert resultado["vinculos"][0]["base_computavel"] == Decimal("23284.80")
    assert resultado["glosa_criterio_soma"] == Decimal("0.00")
    assert resultado["natalina"] == Decimal("23284.80")
    assert e_gratificacao_natalina("ADIC NATAL-1 PAR")
    assert e_gratificacao_natalina("GRATIFICACAO NATALINA")
    assert not e_gratificacao_natalina("AUXILIO-NATALIDADE")


def testar_rubricas_de_abate_teto_do_cpex():
    """I40 = glosa do mes; I39 = atrasados. Codigos vistos nas folhas de 2026."""
    assert classificar("DA A.37 XI CF/88", "I40", "desconto")["natureza"] == ABATE_TETO
    assert classificar("DA I40 AT", "I39", "desconto")["natureza"] == ABATE_TETO_RETROATIVO
    # Tambem pela descricao, sem o codigo (outros orgaos pagadores).
    assert classificar("ABATE TETO CONSTITUCIONAL")["natureza"] == ABATE_TETO
    assert classificar("DESCONTO TETO ART 37 XI ATRASADOS")["natureza"] == ABATE_TETO_RETROATIVO


def testar_coluna_do_contracheque_prevalece():
    """Se a folha diz que e receita, nenhuma heuristica de nome a transforma
    em desconto."""
    assert classificar("RESTITUICAO FUSEX", coluna="receita")["natureza"] != DESCONTO
    assert classificar("SOLDO", coluna="desconto")["natureza"] == DESCONTO


def testar_rubrica_desconhecida_entra_na_base_e_sai_marcada():
    resultado = classificar("RUBRICA QUE NINGUEM CADASTROU", coluna="receita")
    assert resultado["natureza"] == COMPUTAVEL
    assert resultado["conferir"] is True


def testar_confronto_com_a_glosa_aplicada():
    """Glosa lancada na folha x glosa devida pelo criterio por vinculo."""
    a = Vinculo(nome="Pensao 1", parcelas=[
        Parcela("SOLDO", "30.000,00", coluna="receita"),
        Parcela("DA A.37 XI CF/88", "8.633,81", "I40", "desconto"),
    ])
    b = Vinculo(nome="Pensao 2", parcelas=[Parcela("SOLDO", "25.000,00", coluna="receita")])
    resultado = calcular_competencia(Competencia(6, 2026, [a, b]))
    assert resultado["glosa_aplicada"] == Decimal("8633.81")
    assert resultado["glosa_criterio_vinculo"] == Decimal("0.00")
    assert resultado["a_restituir"] == Decimal("8633.81")


def testar_retroativo_nao_entra_no_confronto_mensal():
    v = Vinculo(nome="Pensao", parcelas=[
        Parcela("SOLDO", "25.000,00", coluna="receita"),
        Parcela("DA A.37 XI CF/88", "1.000,00", "I40", "desconto"),
        Parcela("DA I40 AT", "12.000,00", "I39", "desconto"),
    ])
    resultado = calcular_competencia(Competencia(6, 2026, [v]))
    assert resultado["glosa_aplicada"] == Decimal("1000.00")
    assert resultado["glosa_retroativa"] == Decimal("12000.00")
    # A base do mes nao e afetada pelo atrasado.
    assert resultado["base_somada"] == Decimal("25000.00")
    assert resultado["a_restituir"] == Decimal("13000.00")


def testar_prescricao_quinquenal():
    def mes(m, a, valor):
        return Competencia(m, a, [Vinculo(nome="Unico", parcelas=[
            Parcela("SUBSIDIO", valor, coluna="receita")])])

    periodo = calcular_periodo(
        [mes(1, 2019, "50.000,00"), mes(1, 2024, "50.000,00"), mes(1, 2026, "50.000,00")],
        data_ajuizamento=date(2026, 10, 1))
    assert periodo["corte_prescricional"] == date(2021, 10, 1)
    assert periodo["competencias_prescritas"] == 1
    assert periodo["competencias_apuradas"] == 2
    # 01/2019 (prescrita) fica fora do total.
    assert periodo["linhas"][0]["prescrita"] is True
    assert periodo["linhas"][1]["prescrita"] is False


def _so_base(nome, valor, natureza=PROPRIO, obito=None, glosa=None):
    parcelas = [Parcela("SOLDO", valor, coluna="receita")]
    if glosa:
        parcelas.append(Parcela("DA A.37 XI CF/88", glosa, "I40", "desconto"))
    return Vinculo(nome=nome, natureza=natureza, obito_instituidor=obito, parcelas=parcelas)


def testar_temas_377_384_dois_cargos_proprios():
    """Cargos proprios acumulaveis: teto em cada vinculo, nunca na soma."""
    competencia = Competencia(2, 2026, [
        _so_base("Cargo A", "30.000,00"), _so_base("Cargo B", "25.000,00")])
    grupos = agrupar_para_teto(competencia.vinculos)
    assert len(grupos) == 2
    assert all("377" in g["tema"] for g in grupos)
    resultado = calcular_competencia(competencia)
    assert resultado["glosa_criterio_aplicavel"] == Decimal("0.00")
    assert resultado["glosa_criterio_soma"] == Decimal("8633.81")


def testar_tema_359_pensao_pos_ec19_soma_com_provento():
    """Obito apos 04/06/1998: pensao soma com o provento proprio."""
    competencia = Competencia(2, 2026, [
        _so_base("Pensao militar", "25.426,80", PENSAO, date(2016, 3, 22)),
        _so_base("Aposentadoria RPPS", "21.978,07")])
    grupos = agrupar_para_teto(competencia.vinculos)
    assert len(grupos) == 1
    assert "359" in grupos[0]["tema"]
    resultado = calcular_competencia(competencia)
    # 47.404,87 - 46.366,19
    assert resultado["glosa_criterio_aplicavel"] == Decimal("1038.68")
    assert resultado["glosa_criterio_vinculo"] == Decimal("0.00")


def testar_tema_359_pensao_pre_ec19_nao_soma():
    """Obito ate 04/06/1998: fora do Tema 359, volta a ser por vinculo."""
    competencia = Competencia(2, 2026, [
        _so_base("Pensao militar", "25.426,80", PENSAO, date(1995, 5, 10)),
        _so_base("Aposentadoria RPPS", "21.978,07")])
    grupos = agrupar_para_teto(competencia.vinculos)
    assert len(grupos) == 2
    resultado = calcular_competencia(competencia)
    assert resultado["glosa_criterio_aplicavel"] == Decimal("0.00")


def testar_ec19_e_o_marco_exato():
    """04/06/1998 e o dia da EC 19: 'posterior' comeca em 05/06/1998."""
    def glosa(dia):
        return calcular_competencia(Competencia(2, 2026, [
            _so_base("Pensao", "25.426,80", PENSAO, dia),
            _so_base("Provento", "21.978,07")]))["glosa_criterio_aplicavel"]
    assert glosa(date(1998, 6, 4)) == Decimal("0.00")     # no dia: nao e posterior
    assert glosa(date(1998, 6, 5)) == Decimal("1038.68")  # no dia seguinte: e


def _pensao_mais_provento(obito, marco=None):
    competencia = Competencia(2, 2026, [
        _so_base("Pensao militar", "25.426,80", PENSAO, obito),
        _so_base("Aposentadoria propria", "21.978,07")])
    if marco is None:
        return calcular_competencia(competencia)
    return calcular_competencia(competencia, marco)


def testar_marco_ec20_e_a_tese_do_escritorio():
    """Obito entre as duas emendas: a leitura muda o resultado por inteiro.

    Pela letra do Tema 359 (EC 19, 4/06/1998) ja soma. Pelo art. 40, par. 11,
    acrescentado pela EC 20 (15/12/1998), ainda nao - e o que o escritorio
    sustenta, na linha do voto do Min. Celso de Mello no proprio RE 602.584.
    """
    entre_as_emendas = date(1998, 8, 20)
    assert _pensao_mais_provento(entre_as_emendas, MARCO_EC19)["glosa_criterio_aplicavel"] \
        == Decimal("1038.68")
    assert _pensao_mais_provento(entre_as_emendas, MARCO_EC20)["glosa_criterio_aplicavel"] \
        == Decimal("0.00")


def testar_marco_padrao_e_o_literal_da_tese():
    """Sem escolher, vale a EC 19 - glosa maior, pedido menor, lado seguro."""
    resultado = _pensao_mais_provento(date(1998, 8, 20))
    assert resultado["marco"] == MARCO_EC19
    assert resultado["glosa_criterio_aplicavel"] == Decimal("1038.68")


def testar_zona_cinzenta_e_sinalizada():
    """So o obito ENTRE as duas emendas cai na faixa de divergencia."""
    assert _pensao_mais_provento(date(1998, 8, 20))["zona_cinzenta"] == ["Pensao militar"]
    assert _pensao_mais_provento(date(1998, 12, 15))["zona_cinzenta"] == ["Pensao militar"]
    assert _pensao_mais_provento(date(1998, 6, 4))["zona_cinzenta"] == []
    assert _pensao_mais_provento(date(1998, 12, 16))["zona_cinzenta"] == []
    assert _pensao_mais_provento(date(2016, 3, 22))["zona_cinzenta"] == []


def testar_leitura_alternativa_vem_sempre_junto():
    """A outra leitura e calculada mesmo quando nao foi a escolhida."""
    resultado = _pensao_mais_provento(date(1998, 8, 20), MARCO_EC20)
    assert resultado["glosa_criterio_aplicavel"] == Decimal("0.00")
    assert resultado["glosa_criterio_alternativo"] == Decimal("1038.68")
    assert resultado["marco_alternativo_rotulo"].startswith("EC 19")


def testar_marco_nao_altera_caso_fora_da_faixa():
    """Obito claramente antes ou depois: as duas leituras coincidem."""
    for obito in (date(1995, 5, 10), date(2016, 3, 22)):
        um = _pensao_mais_provento(obito, MARCO_EC19)["glosa_criterio_aplicavel"]
        outro = _pensao_mais_provento(obito, MARCO_EC20)["glosa_criterio_aplicavel"]
        assert um == outro


def testar_duas_pensoes_sai_marcado_controvertido():
    """Tema 359 fala em provento E pensao, nao pensao com pensao."""
    competencia = Competencia(2, 2026, [
        _so_base("Pensao do pai", "30.000,00", PENSAO, date(1968, 8, 13)),
        _so_base("Pensao do conjuge", "25.000,00", PENSAO, date(2016, 3, 22))])
    grupos = agrupar_para_teto(competencia.vinculos)
    assert len(grupos) == 2
    assert any(g["controvertido"] for g in grupos)
    resultado = calcular_competencia(competencia)
    assert resultado["glosa_criterio_aplicavel"] == Decimal("0.00")


def testar_pensao_sem_data_do_obito_e_conservadora():
    """Sem a data, assume obito pos-EC19: glosa MAIOR, pedido MENOR."""
    competencia = Competencia(2, 2026, [
        _so_base("Pensao militar", "25.426,80", PENSAO),
        _so_base("Aposentadoria", "21.978,07")])
    grupos = agrupar_para_teto(competencia.vinculos)
    assert len(grupos) == 1
    assert grupos[0]["controvertido"] is True
    assert calcular_competencia(competencia)["glosa_criterio_aplicavel"] == Decimal("1038.68")


def testar_conferencia_da_glosa_lancada():
    """A auditoria do mes: lancada x devida pelo criterio aplicavel."""
    def veredito(vinculos):
        return calcular_competencia(Competencia(2, 2026, vinculos))["conferencia"]["veredito"]

    # Forca acertou: Tema 359 manda somar e ela glosou o excedente exato.
    assert veredito([
        _so_base("Pensao", "25.426,80", PENSAO, date(2016, 3, 22), glosa="1.038,68"),
        _so_base("Provento", "21.978,07")]) == GLOSA_CORRETA

    # Forca glosou onde o Tema 359 nao alcanca (obito pre-EC19).
    assert veredito([
        _so_base("Pensao", "25.426,80", PENSAO, date(1995, 5, 10), glosa="1.038,68"),
        _so_base("Provento", "21.978,07")]) == GLOSA_INDEVIDA

    # Forca glosou mais do que o excedente.
    assert veredito([
        _so_base("Pensao", "25.426,80", PENSAO, date(2016, 3, 22), glosa="3.000,00"),
        _so_base("Provento", "21.978,07")]) == GLOSA_A_MAIOR

    # Forca glosou menos do que o excedente.
    assert veredito([
        _so_base("Pensao", "25.426,80", PENSAO, date(2016, 3, 22), glosa="500,00"),
        _so_base("Provento", "21.978,07")]) == GLOSA_A_MENOR

    # Havia excesso e nada foi descontado.
    assert veredito([
        _so_base("Pensao", "25.426,80", PENSAO, date(2016, 3, 22)),
        _so_base("Provento", "21.978,07")]) == GLOSA_NAO_LANCADA

    # Nao havia excesso e nada foi descontado.
    assert veredito([_so_base("Provento", "21.978,07")]) == SEM_GLOSA


def testar_meses_com_glosa_e_com_divergencia():
    """O periodo diz em quais meses a glosa incidiu e onde houve divergencia."""
    def mes(m, glosa):
        return Competencia(m, 2026, [
            _so_base("Pensao", "25.426,80", PENSAO, date(2016, 3, 22), glosa=glosa),
            _so_base("Provento", "21.978,07")])

    periodo = calcular_periodo([mes(4, None), mes(5, "1.038,68"), mes(6, "3.000,00")])
    assert [l["competencia"] for l in periodo["meses_com_glosa"]] == ["05/2026", "06/2026"]
    divergentes = {l["competencia"]: l["conferencia"]["veredito"]
                   for l in periodo["meses_com_divergencia"]}
    assert divergentes == {"04/2026": GLOSA_NAO_LANCADA, "06/2026": GLOSA_A_MAIOR}


def testar_formatacao_brasileira():
    assert fmt(Decimal("1234.56")) == "R$ 1.234,56"
    assert fmt(Decimal("0")) == "R$ 0,00"
    assert fmt(Decimal("1000000")) == "R$ 1.000.000,00"
    assert _d("1.234,56") == Decimal("1234.56")
    assert _d("46366.19") == Decimal("46366.19")
    assert _d("R$ 23.284,80") == Decimal("23284.80")


def main():
    testes = [v for k, v in sorted(globals().items()) if k.startswith("testar_")]
    falhas = 0
    for teste in testes:
        try:
            teste()
            print("  ok    %s" % teste.__name__)
        except Exception as erro:
            falhas += 1
            print("  FALHA %s -> %s: %s" % (teste.__name__, type(erro).__name__, erro))
    print()
    print("%d teste(s), %d falha(s)." % (len(testes), falhas))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
