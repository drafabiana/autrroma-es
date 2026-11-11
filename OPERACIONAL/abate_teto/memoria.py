# -*- coding: utf-8 -*-
"""
Memoria de calculo do abate-teto: o texto que instrui a peca.

Gera dois artefatos a partir do resultado de calculadora.calcular_periodo():

  1. memoria_texto()   - memoria discursiva, com o detalhamento mes a mes e os
     fundamentos de cada exclusao. E o texto-fonte que vai para o timbrado do
     escritorio (OPERACIONAL/agente_operacional/escritorio_format.py) e, dali,
     para a peca ou para o anexo de calculo.
  2. exportar_csv()    - planilha mes a mes, para juntar aos autos e para a
     conferencia da Dra. Fabiana.

Nenhum dos dois protocola nada: saem marcados PRONTO PARA REVISAO DA DRA.
FABIANA, como toda peca deste repositorio.
"""
import csv
from datetime import date

from calculadora import fmt, _d
from rubricas import COMPUTAVEL, NAO_COMPUTAVEL, ABATE_TETO, ABATE_TETO_RETROATIVO

MESES_EXTENSO = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
    "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def memoria_texto(periodo, cliente="", processo="", detalhar_parcelas=True):
    """Monta a memoria de calculo completa em texto puro."""
    linhas = periodo["linhas"]
    ativas = [linha for linha in linhas if not linha["prescrita"]]
    saida = []
    escrever = saida.append

    escrever("MEMORIA DE CALCULO - ABATE-TETO (ART. 37, XI, DA CF/88)")
    escrever("")
    if cliente:
        escrever("Cliente: %s" % cliente)
    if processo:
        escrever("Processo: %s" % processo)
    if linhas:
        escrever("Periodo apurado: %s a %s" % (linhas[0]["competencia"], linhas[-1]["competencia"]))
    if periodo["data_ajuizamento"]:
        escrever("Data de ajuizamento considerada: %s" % _data_br(periodo["data_ajuizamento"]))
        escrever("Corte prescricional (5 anos - Decreto 20.910/1932, art. 1o): %s"
                 % periodo["corte_prescricional"].strftime("%m/%Y"))
    escrever("")

    escrever("CRITERIO DE APURACAO")
    escrever("")
    escrever(_parag(
        "O teto remuneratorio do art. 37, XI, da CF/88 corresponde ao subsidio "
        "mensal, em especie, de Ministro do Supremo Tribunal Federal, e incide "
        "sobre o valor BRUTO da remuneracao, antes dos descontos de imposto de "
        "renda e de contribuicao previdenciaria (Resolucao CNJ 14/2006, art. 1o, "
        "paragrafo unico)."))
    escrever("")
    escrever(_parag(
        "Nao integram a base de calculo as parcelas de carater indenizatorio "
        "previstas em lei (CF/88, art. 37, par. 11, incluido pela EC 47/2005), "
        "nem as verbas referentes a direitos sociais e as demais hipoteses do "
        "art. 4o da Resolucao CNJ 14/2006."))
    escrever("")
    escrever(_parag(
        "Qual criterio rege o caso depende da natureza de cada vinculo e, "
        "havendo pensao, da data do obito do instituidor. Tres temas de "
        "repercussao geral do Supremo Tribunal Federal governam a materia:"))
    escrever("")
    escrever(_parag(
        "TEMAS 377 e 384 (RE 612.975 e RE 602.043, julgados em 27/04/2020): "
        "\"Nos casos autorizados constitucionalmente de acumulacao de cargos, "
        "empregos e funcoes, a incidencia do artigo 37, inciso XI, da "
        "Constituicao Federal, pressupoe a consideracao de cada um dos vinculos "
        "formalizados, afastada a observancia do teto remuneratorio quanto ao "
        "somatorio dos ganhos do agente publico.\" Alcanca os vinculos PROPRIOS "
        "do agente - cargo, emprego, funcao e os proventos da propria "
        "aposentadoria. Teto POR VINCULO."))
    escrever("")
    escrever(_parag(
        "TEMA 359 (RE 602.584, julgado em 06/08/2020): \"Ocorrida a morte do "
        "instituidor da pensao em momento posterior ao da Emenda Constitucional "
        "no 19/1998, o teto constitucional previsto no inciso XI do artigo 37 da "
        "Constituicao Federal incide sobre o somatorio de remuneracao ou provento "
        "e pensao percebida por servidor.\" Alcanca a PENSAO somada a "
        "remuneracao ou provento proprio. Teto sobre a SOMA."))
    escrever("")
    escrever(_parag(
        "O proprio acordao do RE 602.584 distingue as duas situacoes ao "
        "registrar que, ali, \"o conflito de interesses diz respeito a institutos "
        "distintos, a saber: remuneracao e pensao; proventos e pensao\"."))
    escrever("")
    escrever(_parag(
        "MARCO TEMPORAL ADOTADO NESTA APURACAO: %s - %s. A tese do Tema 359 "
        "menciona a EC 19/1998 (4/06/1998); ha, porem, fundamento para tomar "
        "como marco a EC 20/1998 (15/12/1998), que acrescentou o art. 40, "
        "par. 11, da Constituicao - dispositivo que manda aplicar o limite do "
        "art. 37, XI, a soma total dos proventos de inatividade. Foi ali, nas "
        "palavras do voto do Ministro Celso de Mello no proprio RE 602.584, que "
        "\"o provento de pensao passou a constar expressamente do limite "
        "estabelecido no art. 37, inciso XI, da Constituicao Federal\"."
        % (periodo["marco_rotulo"], periodo["marco_fundamento"])))
    escrever("")
    if periodo["zona_cinzenta"]:
        escrever(_parag(
            "ATENCAO - O OBITO CAI ENTRE AS DUAS EMENDAS (%s). As duas leituras "
            "dao resultados opostos: por %s a glosa devida no periodo e de %s; "
            "por %s, de %s. A escolha da tese decide o pedido."
            % ("; ".join(periodo["zona_cinzenta"]),
               periodo["marco_rotulo"], fmt(periodo["total_glosa_criterio_aplicavel"]),
               periodo["marco_alternativo_rotulo"],
               fmt(periodo["total_glosa_criterio_alternativo"]))))
        escrever("")
    escrever(_parag(
        "A apuracao abaixo aplica a cada competencia o agrupamento que esses "
        "temas determinam (coluna DEVIDA) e o confronta com o que o orgao "
        "pagador efetivamente descontou (coluna LANCADA). A diferenca e o que se "
        "pede. As colunas POR VINCULO e PELA SOMA aparecem apenas como "
        "referencia dos dois extremos."))
    escrever("")

    if detalhar_parcelas and ativas:
        escrever(_regua())
        escrever("COMPOSICAO DA BASE DE CALCULO")
        escrever("")
        escrever(_parag(
            "Tomando por referencia a competencia %s, as parcelas se classificam "
            "assim:" % ativas[0]["competencia"]))
        escrever("")
        for vinculo in ativas[0]["vinculos"]:
            escrever("  %s" % vinculo["nome"])
            if vinculo["orgao"] or vinculo["matricula"]:
                escrever("  (%s)" % " - ".join(x for x in (vinculo["orgao"], vinculo["matricula"]) if x))
            for parcela in vinculo["parcelas"]:
                if parcela.natureza == COMPUTAVEL:
                    marca = "[ENTRA]"
                elif parcela.natureza == NAO_COMPUTAVEL:
                    marca = "[FORA] "
                elif parcela.natureza in (ABATE_TETO, ABATE_TETO_RETROATIVO):
                    marca = "[GLOSA]"
                else:
                    continue
                escrever("    %s %-32s %14s   %s" % (
                    marca, parcela.descricao[:32], fmt(parcela.valor), parcela.fundamento))
            escrever("    %s %-32s %14s" % (
                " " * 7, "BASE COMPUTAVEL", fmt(vinculo["base_computavel"])))
            escrever("")

    if ativas:
        escrever(_regua())
        escrever("CRITERIO APLICADO (referencia: competencia %s)" % ativas[-1]["competencia"])
        escrever("")
        for grupo in ativas[-1]["grupos"]:
            escrever("  %s" % grupo["nome"])
            escrever("    %s%s" % (
                grupo["tema"], "   << CONTROVERTIDO" if grupo["controvertido"] else ""))
            escrever("    %s" % grupo["fundamento"])
            escrever("    base %s   glosa devida %s" % (fmt(grupo["base"]), fmt(grupo["glosa"])))
            escrever("")

    escrever(_regua())
    escrever("APURACAO MES A MES")
    escrever("")
    escrever("%-9s %13s %13s %13s %13s %13s  %s" % (
        "Compet.", "Base somada", "Teto do mes", "Devida", "Lancada", "Diferenca",
        "Conferencia"))
    escrever("-" * 96)
    for linha in linhas:
        sufixo = "  (PRESCRITA)" if linha["prescrita"] else ""
        escrever("%-9s %13s %13s %13s %13s %13s  %s%s" % (
            linha["competencia"],
            fmt(linha["base_somada"]),
            fmt(linha["teto"]),
            fmt(linha["glosa_criterio_aplicavel"]),
            fmt(linha["glosa_aplicada"]),
            fmt(linha["conferencia"]["diferenca"]),
            linha["conferencia"]["veredito"],
            sufixo))
    escrever("-" * 96)
    escrever("%-9s %13s %13s %13s %13s" % (
        "TOTAIS", "", "",
        fmt(periodo["total_glosa_criterio_aplicavel"]),
        fmt(periodo["total_glosa_aplicada"])))
    escrever("")
    escrever(_parag(
        "Referencia dos extremos: pelo criterio POR VINCULO puro (Temas 377 e "
        "384 aplicados a todos os vinculos) a glosa do periodo seria de %s; pelo "
        "criterio da SOMA de tudo, de %s."
        % (fmt(periodo["total_glosa_criterio_vinculo"]),
           fmt(periodo["total_glosa_criterio_soma"]))))
    escrever("")

    com_glosa = periodo["meses_com_glosa"]
    divergentes = periodo["meses_com_divergencia"]
    escrever(_regua())
    escrever("CONFERENCIA DA GLOSA LANCADA PELO ORGAO PAGADOR")
    escrever("")
    if not com_glosa:
        escrever(_parag(
            "Nenhuma competencia do periodo apurado teve abate-teto lancado na "
            "folha de pagamento."))
        escrever("")
    else:
        escrever(_parag(
            "A glosa incidiu em %d das %d competencias apuradas, nos seguintes "
            "meses:" % (len(com_glosa), periodo["competencias_apuradas"])))
        escrever("")
        for linha in com_glosa:
            retro = ("   + atrasados %s" % fmt(linha["glosa_retroativa"])) \
                if linha["glosa_retroativa"] else ""
            escrever("  %-9s lancada %13s   devida %13s   %s%s" % (
                linha["competencia"], fmt(linha["glosa_aplicada"]),
                fmt(linha["glosa_criterio_aplicavel"]),
                linha["conferencia"]["veredito"], retro))
        escrever("")

    if divergentes:
        escrever(_parag(
            "Ha DIVERGENCIA em %d competencia(s) entre o que foi descontado e o "
            "que os temas do STF autorizam:" % len(divergentes)))
        escrever("")
        for linha in divergentes:
            escrever("  %-9s %-12s  diferenca %s" % (
                linha["competencia"], linha["conferencia"]["veredito"],
                fmt(linha["conferencia"]["diferenca"])))
        escrever("")
    elif com_glosa:
        escrever(_parag(
            "Nao ha divergencia na glosa do mes: em todas as competencias o "
            "valor descontado corresponde ao que o criterio aplicavel autoriza."))
        escrever("")

    if periodo["total_natalina"]:
        escrever(_regua())
        escrever("GRATIFICACAO NATALINA (13o SALARIO)")
        escrever("")
        escrever(_parag(
            "Foram identificados %s pagos a titulo de gratificacao natalina no "
            "periodo. Esse valor NAO foi somado a base mensal: o 13o salario e "
            "verba referente a direito social do art. 7o c/c art. 39, par. 3o, "
            "da CF/88, excluida da base mensal pelo art. 4o, II, da Resolucao "
            "CNJ 14/2006, e seu confronto com o teto e feito em separado. "
            "Soma-lo ao mes do pagamento faria surgir uma glosa em competencia "
            "que nao tem excesso algum."
            % fmt(periodo["total_natalina"])))
        escrever("")
        escrever(_parag(
            "ATENCAO: esta calculadora NAO faz o confronto do 13o com o teto - "
            "a regra varia conforme o orgao pagador. Conferir com a folha do "
            "CPEx/SIAPE se houve glosa sobre a gratificacao natalina e, havendo, "
            "apura-la a parte."))
        escrever("")

    if periodo["total_glosa_aplicada"] or periodo["total_glosa_retroativa"]:
        escrever(_regua())
        escrever("CONFRONTO COM O QUE FOI EFETIVAMENTE DESCONTADO")
        escrever("")
        escrever("  Glosa lancada nos contracheques (mes corrente) ... %s"
                 % fmt(periodo["total_glosa_aplicada"]))
        if periodo["total_glosa_retroativa"]:
            escrever("  Glosa de meses anteriores cobrada no periodo .... %s"
                     % fmt(periodo["total_glosa_retroativa"]))
        escrever("  TOTAL RETIDO DO CLIENTE ......................... %s"
                 % fmt(periodo["total_retido"]))
        escrever("  Glosa devida pelo criterio por vinculo .......... %s"
                 % fmt(periodo["total_glosa_criterio_vinculo"]))
        escrever("  VALOR A RESTITUIR (sem correcao) ................ %s"
                 % fmt(periodo["total_a_restituir"]))
        escrever("")
        if periodo["total_glosa_retroativa"]:
            escrever(_parag(
                "ATENCAO: ha glosa de meses anteriores cobrada de uma vez no "
                "periodo (%s). Conferir junto ao orgao pagador a quais "
                "competencias ela se refere antes de fechar o pedido - se "
                "alguma dessas competencias ja aparece acima com glosa propria, "
                "o mesmo mes estaria sendo pedido duas vezes."
                % fmt(periodo["total_glosa_retroativa"])))
            escrever("")

    escrever(_regua())
    escrever("RESULTADO")
    escrever("")
    escrever(_parag(
        "Apuradas %d competencias%s, a glosa devida pelo criterio por vinculo "
        "e de %s, contra %s exigidos pelo criterio da soma. A diferenca, de %s, "
        "e o valor glosado a maior no periodo, a ser acrescido de correcao "
        "monetaria e juros na forma do Manual de Calculos da Justica Federal."
        % (periodo["competencias_apuradas"],
           (" (%d competencias alcancadas pela prescricao quinquenal)"
            % periodo["competencias_prescritas"]) if periodo["competencias_prescritas"] else "",
           fmt(periodo["total_glosa_criterio_vinculo"]),
           fmt(periodo["total_glosa_criterio_soma"]),
           fmt(periodo["total_diferenca_entre_criterios"]))))
    escrever("")
    escrever(_parag(
        "Os valores acima sao NOMINAIS. A correcao monetaria e os juros nao "
        "estao aplicados nesta memoria e devem ser calculados a parte, pelo "
        "Manual de Calculos da Justica Federal vigente."))
    escrever("")

    pendencias = periodo["pendencias"]
    fontes_teto = sorted({l["teto_fonte"] for l in linhas})
    observacoes = sorted({l["teto_observacao"] for l in linhas if l["teto_observacao"]})

    escrever(_regua())
    escrever("PONTOS DE CONFERENCIA")
    escrever("")
    escrever("  Fonte do teto no periodo: %s" % "; ".join(fontes_teto))
    for observacao in observacoes:
        escrever("  Observacao: %s" % observacao)
    if pendencias:
        escrever("")
        escrever("  Rubricas que exigem decisao da Dra. Fabiana antes de fechar o calculo:")
        vistas = set()
        for parcela in pendencias:
            if parcela.descricao in vistas:
                continue
            vistas.add(parcela.descricao)
            escrever("    - %-34s (%s) %s" % (
                parcela.descricao[:34], parcela.natureza, parcela.fundamento))
    else:
        escrever("  Nenhuma rubrica ficou pendente de classificacao.")
    escrever("")
    escrever(_regua())
    escrever("PRONTO PARA REVISAO DA DRA. FABIANA")
    escrever("")
    escrever(_parag(
        "Calculo gerado por automacao do escritorio a partir dos contracheques "
        "juntados. Conferir os brutos contra os documentos originais antes de "
        "usar em peca. Nenhum valor aqui foi protocolado."))

    return "\n".join(saida)


def projecao_quinquenal(glosa_mensal, meses=60):
    """Projeta a glosa mensal sobre o quinquenio (60 competencias).

    Serve a triagem do atendimento: quanto o cliente perde se a glosa se
    mantiver. E ESTIMATIVA - assume glosa constante e valor nominal, sem
    correcao. O numero de peca sai da apuracao mes a mes, nao daqui.
    """
    return _d(glosa_mensal) * meses


def parecer_cliente(periodo, cliente="", processo="", data_parecer=None,
                    glosa_mensal_atual=None):
    """Parecer de calculo em texto, no formato que o motor do timbrado entende.

    Diferente da memoria de calculo: a memoria e tecnica, mes a mes, para
    instruir os autos. O parecer e para o CLIENTE - explica em portugues claro
    o que esta sendo descontado, por que e indevido e quanto vale.

    O texto sai pronto para gerar_peca_escritorio(), que o converte no DOCX
    timbrado com os topicos em tabela azul.
    """
    data_parecer = data_parecer or date.today()
    linhas = [l for l in periodo["linhas"] if not l["prescrita"]]
    saida = []
    escrever = saida.append

    escrever("PARECER DE CÁLCULO - ABATE-TETO")
    escrever("")
    if cliente:
        escrever("Interessado: %s" % cliente)
        escrever("")
    if processo:
        escrever("Processo: %s" % processo)
        escrever("")
    if linhas:
        escrever("Competências examinadas: %s a %s (%d %s)"
                 % (linhas[0]["competencia"], linhas[-1]["competencia"],
                    len(linhas), "mês" if len(linhas) == 1 else "meses"))
        escrever("")

    escrever("I - DO QUE FOI EXAMINADO")
    escrever("")
    escrever(_parag(
        "Foram examinados os contracheques apresentados, competência a "
        "competência, para verificar se o desconto lançado sob o título de "
        "abate-teto corresponde ao que a Constituição autoriza."))
    escrever("")

    if linhas:
        ultima = linhas[-1]
        escrever("II - DO QUE O SENHOR RECEBE E DO LIMITE APLICÁVEL")
        escrever("")
        escrever(_parag(
            "Na competência %s, o limite constitucional - que corresponde ao "
            "salário de Ministro do Supremo Tribunal Federal - era de %s (%s)."
            % (ultima["competencia"], fmt(ultima["teto"]), ultima["teto_fonte"])))
        escrever("")
        for vinculo in ultima["vinculos"]:
            escrever(_parag(
                "%s: valor bruto de %s, dos quais %s entram na conta do limite "
                "(as parcelas de caráter indenizatório e o 13º salário não entram, "
                "por força do art. 37, parágrafo 11, da Constituição)."
                % (vinculo["nome"], fmt(vinculo["total_bruto"]),
                   fmt(vinculo["base_computavel"]))))
            escrever("")
        escrever(_parag(
            "Somados, os valores alcançam %s." % fmt(ultima["base_somada"])))
        escrever("")

    escrever("III - DO CRITÉRIO ADOTADO PELO ÓRGÃO PAGADOR")
    escrever("")
    escrever(_parag(
        "O órgão pagador soma tudo o que o senhor recebe e aplica o limite "
        "sobre esse total. Por esse critério, a glosa no período examinado "
        "chega a %s." % fmt(periodo["total_glosa_criterio_soma"])))
    escrever("")

    escrever("IV - DO CRITÉRIO FIXADO PELO SUPREMO TRIBUNAL FEDERAL")
    escrever("")
    escrever(_parag(
        "O Supremo Tribunal Federal decidiu, em repercussão geral, que nas "
        "situações em que a própria Constituição autoriza acumular cargos, "
        "empregos e funções, o limite é conferido em relação a cada vínculo "
        "separadamente, e não sobre a soma (RE 612.975 e RE 602.043 - Temas 377 "
        "e 384)."))
    escrever("")
    escrever(_parag(
        "Julgando caso diverso, o mesmo Tribunal decidiu que, ocorrida a morte "
        "do instituidor da pensão depois da Emenda Constitucional nº 19/1998, o "
        "teto incide sobre a soma de provento ou remuneração com a pensão "
        "(RE 602.584 - Tema 359). São hipóteses distintas, e o enquadramento "
        "depende da natureza de cada vínculo e da data do óbito."))
    escrever("")
    if linhas:
        for grupo in linhas[-1]["grupos"]:
            escrever(_parag(
                "%s: apurado sob o %s. %s. Base de %s, com glosa devida de %s."
                % (grupo["nome"], grupo["tema"], grupo["fundamento"],
                   fmt(grupo["base"]), fmt(grupo["glosa"]))))
            escrever("")
    escrever(_parag(
        "Nesta apuração adotou-se como marco temporal a %s (%s)."
        % (periodo["marco_rotulo"], periodo["marco_fundamento"])))
    escrever("")
    if periodo["zona_cinzenta"]:
        escrever(_parag(
            "O óbito do instituidor ocorreu entre a Emenda Constitucional "
            "nº 19/1998 e a de nº 20/1998, faixa em que as duas leituras "
            "levam a resultados opostos: por uma, a glosa devida no período "
            "seria de %s; pela outra, de %s. A tese a sustentar é decisão "
            "a ser tomada à vista do conjunto do caso."
            % (fmt(periodo["total_glosa_criterio_aplicavel"]),
               fmt(periodo["total_glosa_criterio_alternativo"]))))
        escrever("")
    escrever(_parag(
        "Aplicado o critério que esses temas determinam, a glosa devida no "
        "período é de %s." % fmt(periodo["total_glosa_criterio_aplicavel"])))
    escrever("")

    escrever("V - DO VALOR APURADO")
    escrever("")
    escrever(_parag(
        "Confrontado o que o órgão pagador descontou como glosa do mês (%s) com "
        "o que os temas acima autorizam (%s), o valor descontado a maior no "
        "período examinado é de %s."
        % (fmt(periodo["total_glosa_aplicada"]),
           fmt(periodo["total_glosa_criterio_aplicavel"]),
           fmt(max(periodo["total_glosa_aplicada"] - periodo["total_glosa_criterio_aplicavel"],
                   _d(0))))))
    escrever("")
    if periodo["meses_com_divergencia"]:
        escrever(_parag(
            "A divergência aparece nas seguintes competências: %s."
            % "; ".join("%s (%s)" % (l["competencia"], l["conferencia"]["veredito"].lower())
                        for l in periodo["meses_com_divergencia"])))
        escrever("")
    if periodo["total_glosa_retroativa"]:
        escrever(_parag(
            "Além disso, foram cobrados %s a título de atrasados de competências "
            "anteriores. Esse valor depende de levantamento dos meses a que se "
            "refere e não está apurado neste parecer."
            % fmt(periodo["total_glosa_retroativa"])))
        escrever("")
    if periodo["total_retido"]:
        escrever(_parag(
            "Confrontado o que foi efetivamente retido nos contracheques (%s) "
            "com o que seria devido, o valor a restituir é de %s."
            % (fmt(periodo["total_retido"]), fmt(periodo["total_a_restituir"]))))
        escrever("")

    mensal = glosa_mensal_atual
    if mensal is None and linhas:
        mensal = linhas[-1]["diferenca_entre_criterios"]
    if mensal and _d(mensal) > 0:
        escrever(_parag(
            "Mantido o desconto atual de %s por mês, a perda alcança %s ao ano "
            "e %s no período de cinco anos que a lei permite reaver. Trata-se "
            "de projeção: o valor definitivo depende da apuração competência a "
            "competência e da atualização monetária."
            % (fmt(mensal), fmt(_d(mensal) * 12), fmt(projecao_quinquenal(mensal)))))
        escrever("")

    escrever("VI - DAS RESSALVAS")
    escrever("")
    escrever(_parag(
        "Os valores acima são nominais: a correção monetária e os juros são "
        "apurados à parte, pelo Manual de Cálculos da Justiça Federal. A "
        "pretensão alcança os cinco anos anteriores ao ajuizamento, por se "
        "tratar de desconto que se renova a cada mês (Decreto 20.910/1932)."))
    escrever("")
    escrever(_parag(
        "A tese depende de a acumulação ser lícita no caso concreto, o que se "
        "verifica no título de pensão e na legislação vigente na data do óbito "
        "do instituidor. Este parecer não substitui a análise da documentação "
        "completa."))
    escrever("")
    if periodo["pendencias"]:
        vistas = []
        for parcela in periodo["pendencias"]:
            if parcela.descricao not in vistas:
                vistas.append(parcela.descricao)
        escrever(_parag(
            "Ficaram pendentes de confirmação as seguintes rubricas do "
            "contracheque, que podem alterar o valor apurado: %s."
            % "; ".join(vistas)))
        escrever("")

    escrever("Rio de Janeiro, %s." % _data_br(data_parecer))
    escrever("")
    escrever("FABIANA SILVA ALVES CARNEIRO")
    escrever("")
    escrever("OAB/RJ 188.762")

    return "\n".join(saida)


def exportar_csv(periodo, caminho):
    """Grava a apuracao mes a mes em CSV (separador ';', padrao do Excel BR)."""
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow([
            "competencia", "teto", "base_somada", "glosa_devida_criterio_aplicavel",
            "glosa_lancada_na_folha", "conferencia", "diferenca_conferencia",
            "glosa_criterio_soma", "glosa_criterio_vinculo", "glosa_retroativa",
            "a_restituir", "prescrita", "tema_aplicado", "marco_temporal",
            "glosa_pelo_outro_marco", "fonte_do_teto",
        ])
        for linha in periodo["linhas"]:
            escritor.writerow([
                linha["competencia"],
                _num(linha["teto"]),
                _num(linha["base_somada"]),
                _num(linha["glosa_criterio_aplicavel"]),
                _num(linha["glosa_aplicada"]),
                linha["conferencia"]["veredito"],
                _num(linha["conferencia"]["diferenca"]),
                _num(linha["glosa_criterio_soma"]),
                _num(linha["glosa_criterio_vinculo"]),
                _num(linha["glosa_retroativa"]),
                _num(linha["a_restituir"]),
                "sim" if linha["prescrita"] else "nao",
                " | ".join(sorted({g["tema"] for g in linha["grupos"]})),
                linha["marco_rotulo"],
                _num(linha["glosa_criterio_alternativo"]),
                linha["teto_fonte"],
            ])
    return caminho


def exportar_csv_parcelas(periodo, caminho):
    """Grava o detalhamento rubrica a rubrica, para conferencia."""
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow([
            "competencia", "vinculo", "codigo", "descricao", "valor",
            "natureza", "conferir", "fundamento",
        ])
        for linha in periodo["linhas"]:
            for vinculo in linha["vinculos"]:
                for parcela in vinculo["parcelas"]:
                    escritor.writerow([
                        linha["competencia"], vinculo["nome"], parcela.codigo,
                        parcela.descricao, _num(parcela.valor), parcela.natureza,
                        "sim" if parcela.conferir else "nao", parcela.fundamento,
                    ])
    return caminho


def _num(valor):
    """Numero no padrao brasileiro, sem simbolo de moeda (para planilha)."""
    return ("%.2f" % valor).replace(".", ",")


def _data_br(dia):
    if isinstance(dia, date):
        return "%d de %s de %d" % (dia.day, MESES_EXTENSO[dia.month], dia.year)
    return str(dia)


def _regua():
    return "=" * 84


def _parag(texto, largura=84):
    """Quebra um paragrafo na largura da memoria."""
    palavras = texto.split()
    linhas, atual = [], ""
    for palavra in palavras:
        if len(atual) + len(palavra) + 1 > largura:
            linhas.append(atual)
            atual = palavra
        else:
            atual = (atual + " " + palavra).strip()
    if atual:
        linhas.append(atual)
    return "\n".join(linhas)
