# -*- coding: utf-8 -*-
"""
=============================================================================
  CALCULADORA DE ABATE-TETO - ALVES CARNEIRO ADVOCACIA E CONSULTORIA JURIDICA
=============================================================================

  Apura MES A MES a glosa do art. 37, XI, da CF/88 (abate-teto), aplicando a
  cada competencia o criterio que os temas do STF determinam, e CONFERE o que o
  orgao pagador efetivamente descontou:

    Temas 377 e 384 (RE 612.975 e RE 602.043) - vinculos PROPRIOS (cargo,
      emprego, funcao, proventos da propria aposentadoria): teto POR VINCULO.
    Tema 359 (RE 602.584) - PENSAO somada a remuneracao/provento proprio,
      quando o obito do instituidor e posterior a EC 19/1998: teto sobre a SOMA.

  Por isso cada vinculo precisa declarar "natureza" (proprio|pensao) e, sendo
  pensao, "obito_instituidor". Sem isso o enquadramento sai errado.

  O teto e o subsidio mensal de Ministro do STF e incide sobre o valor BRUTO
  (Res. CNJ 14/2006, art. 1o, par. unico). Ver config/teto_constitucional.py.

  Uso:

    # 1. CASO COMPLETO - varios vinculos e regimes (Forca Armada + regime
    #    proprio), mes a mes. E o caminho principal.
    python OPERACIONAL/calcular_abate_teto.py modelo-caso caso.json
    python OPERACIONAL/calcular_abate_teto.py caso caso.json --parecer

    # 2. Um vinculo so, direto da pasta de contracheques do CPEx
    python OPERACIONAL/calcular_abate_teto.py contracheques ^
        "G:\\Meu Drive\\CLIENTES MILITARES\\FULANO\\CONTRACHEQUES" ^
        --vinculo "Pensao militar - Exercito"

    # 3. A partir de um CSV de rubricas (qualquer orgao pagador)
    python OPERACIONAL/calcular_abate_teto.py csv rubricas.csv ^
        --cliente "Fulano de Tal" --ajuizamento 01/10/2026

    # 4. Triagem de um mes so, na reuniao
    python OPERACIONAL/calcular_abate_teto.py rapido 02/2026 ^
        --vinculo "Pensao militar=25426,80" --vinculo "Aposentadoria=21978,07"

  Saidas (pasta do comando --saida, padrao: ao lado da entrada):
    memoria-de-calculo.txt    memoria discursiva, texto-fonte da peca
    apuracao-mensal.csv       planilha mes a mes, com a conferencia
    parcelas.csv              detalhamento rubrica a rubrica
    --parecer                 parecer no timbrado, na pasta do cliente no Drive

  A IA NUNCA PROTOCOLA. Tudo sai marcado PRONTO PARA REVISAO DA DRA. FABIANA.
=============================================================================
"""
import argparse
import glob
import io
import json
import os
import re
import sys
import unicodedata
from collections import OrderedDict
from datetime import date, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "abate_teto"))

from calculadora import (  # noqa: E402
    Parcela, Vinculo, Competencia, calcular_periodo, validar_bruto, fmt, _d,
    PROPRIO, PENSAO, GLOSA_CORRETA, SEM_GLOSA, MARCO_EC19, MARCO_EC20,
)
from rubricas import COMPUTAVEL, NAO_COMPUTAVEL, ABATE_TETO  # noqa: E402
from leitor_contracheque import (  # noqa: E402
    ler_contracheque_cpex, carregar_csv, modelo_csv,
)
from memoria import (  # noqa: E402
    memoria_texto, parecer_cliente, exportar_csv, exportar_csv_parcelas,
    projecao_quinquenal,
)

# Pasta autorizada para as pecas da automacao - ver
# .claude/rules/pecas-automacao-drive.md. Nenhum outro ponto do Drive e tocado.
PASTA_PECAS = os.environ.get("DRIVE_PECAS_AUTOMACAO", r"G:\Meu Drive\PEÇAS AUTOMAÇÃO")


def _competencia_de(rotulo):
    mes, ano = rotulo.split("/")
    return int(mes), int(ano)


def _natureza(texto):
    """'pensao' -> PENSAO; qualquer outra coisa (ou vazio) -> PROPRIO.

    ATENCAO: o default NAO e o lado seguro. Declarar como PROPRIO uma pensao
    que na verdade e pensao afasta o Tema 359, reduz a glosa tida por devida e
    INFLA o pedido - o erro caro. Por isso quem monta o caso e avisado sempre
    que a natureza nao vem declarada (ver _avisar_natureza).
    """
    chave = _sem_acento(str(texto or "")).strip().upper()
    return PENSAO if chave.startswith("PENSA") else PROPRIO


def _avisar_natureza(vinculos):
    """Avisa quando falta declarar natureza ou data de obito.

    So importa quando ha mais de um vinculo: e o agrupamento que muda de tema.
    """
    if len(vinculos) < 2:
        return
    for vinculo in vinculos:
        if not vinculo.get("natureza"):
            print('  [conferir] vinculo "%s" sem "natureza": tratado como vinculo '
                  "PROPRIO (Temas 377/384). Se for pensao, declare - o Tema 359 "
                  "pode mandar somar." % vinculo.get("nome", "?"))
        elif _natureza(vinculo.get("natureza")) == PENSAO \
                and not vinculo.get("obito_instituidor"):
            print('  [conferir] pensao "%s" sem "obito_instituidor": tratada como '
                  "obito posterior a EC 19/1998 (leitura conservadora do Tema 359)."
                  % vinculo.get("nome", "?"))


def _montar(registros):
    """Agrupa registros {competencia, vinculo, codigo, descricao, valor, coluna}
    em objetos Competencia."""
    mapa = OrderedDict()
    for registro in registros:
        chave = registro["competencia"].strip()
        mes, ano = _competencia_de(chave)
        competencia = mapa.setdefault(chave, Competencia(mes, ano, []))
        nome_vinculo = (registro.get("vinculo") or "Vinculo unico").strip()
        vinculo = next((v for v in competencia.vinculos if v.nome == nome_vinculo), None)
        if vinculo is None:
            vinculo = Vinculo(
                nome=nome_vinculo,
                orgao=registro.get("orgao", "") or "",
                matricula=registro.get("matricula", "") or "",
                natureza=_natureza(registro.get("natureza")),
                obito_instituidor=_data(registro.get("obito_instituidor")),
                fundamento_acumulacao=registro.get("fundamento_acumulacao", "") or "",
            )
            competencia.vinculos.append(vinculo)
        coluna = (registro.get("coluna") or "").strip().lower() or None
        vinculo.parcelas.append(Parcela(
            descricao=registro["descricao"],
            valor=registro["valor"],
            codigo=(registro.get("codigo") or "").strip(),
            coluna=coluna,
            # natureza/fundamento so vem preenchidos quando quem chamou ja sabe
            # o que a parcela e (comando 'rapido'); do contrario, classifica.
            natureza=(registro.get("natureza_parcela") or "").strip(),
            fundamento=(registro.get("fundamento") or "").strip(),
        ))
    return list(mapa.values())


def _gravar(periodo, destino, cliente, processo):
    os.makedirs(destino, exist_ok=True)
    caminho_memoria = os.path.join(destino, "memoria-de-calculo.txt")
    with open(caminho_memoria, "w", encoding="utf-8") as arquivo:
        arquivo.write(memoria_texto(periodo, cliente=cliente, processo=processo))
    exportar_csv(periodo, os.path.join(destino, "apuracao-mensal.csv"))
    exportar_csv_parcelas(periodo, os.path.join(destino, "parcelas.csv"))
    return caminho_memoria


def _gravar_parecer_no_drive(periodo, cliente, processo):
    """Gera o parecer no timbrado e o salva na pasta do cliente no Drive.

    Dois arquivos, conforme .claude/rules/pecas-automacao-drive.md:
      {CLIENTE} - Calculo Abate-Teto - DD-MM-AAAA.docx
      _fontes/{CLIENTE} - Calculo Abate-Teto - DD-MM-AAAA.txt
    O texto-fonte e o que permite regerar o DOCX depois sem refazer o calculo.
    """
    if not cliente.strip():
        print("  [parecer] informe --cliente para gravar na pasta do Drive.")
        return None

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agente_operacional"))
    try:
        from escritorio_format import gerar_peca_escritorio
    except ImportError as erro:
        print("  [parecer] motor do timbrado indisponivel (%s)." % erro)
        return None

    texto = parecer_cliente(periodo, cliente=cliente, processo=processo)
    destino = _pasta_do_cliente(cliente)

    nome_txt = _nome_arquivo(cliente, "Calculo Abate-Teto", ".txt")
    _gravar_sem_sobrescrever(
        os.path.join(destino, "_fontes", nome_txt),
        lambda caminho: open(caminho, "w", encoding="utf-8").write(texto))

    nome_docx = _nome_arquivo(cliente, "Calculo Abate-Teto", ".docx")
    caminho_docx = _gravar_sem_sobrescrever(
        os.path.join(destino, nome_docx),
        lambda caminho: gerar_peca_escritorio(texto, caminho))
    return caminho_docx


def _sem_acento(texto):
    forma = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in forma if not unicodedata.combining(c))


def _pasta_do_cliente(cliente):
    """Subpasta do cliente em PECAS AUTOMACAO, criada na primeira peca.

    Regra do escritorio: a pasta PECAS AUTOMACAO ja existe e nunca e recriada;
    dentro dela, uma subpasta por cliente, com o nome em MAIUSCULO.
    """
    if not os.path.isdir(PASTA_PECAS):
        raise RuntimeError(
            "Pasta de pecas nao encontrada: %s. Confira se o Google Drive esta "
            "montado, ou aponte outra em DRIVE_PECAS_AUTOMACAO." % PASTA_PECAS)
    destino = os.path.join(PASTA_PECAS, cliente.strip().upper())
    os.makedirs(os.path.join(destino, "_fontes"), exist_ok=True)
    return destino


def _nome_arquivo(cliente, peca, extensao, quando=None):
    """{Nome do Cliente} - {Peca} - {DD-MM-AAAA}.{ext}, sem acento nem barra."""
    quando = quando or date.today()
    base = "%s - %s - %s" % (
        _sem_acento(cliente.strip().upper()), peca, quando.strftime("%d-%m-%Y"))
    return re.sub(r"[\\/:*?\"<>|]", "-", base) + extensao


def _gravar_sem_sobrescrever(caminho, escrever):
    """Grava chamando escrever(caminho). Nunca sobrescreve arquivo existente.

    Peca com o mesmo nome pode ja ter sido revisada ou protocolada - a regra do
    escritorio manda avisar e aguardar decisao, nunca substituir.
    """
    if os.path.exists(caminho):
        print("  [ja existe] %s" % caminho)
        print("              NAO foi sobrescrito. Renomeie ou remova o anterior.")
        return None
    escrever(caminho)
    return caminho


def _resumo(periodo):
    print()
    print("=" * 96)
    print("  APURACAO MES A MES")
    print("=" * 96)
    print("  %-8s %13s %13s %13s %13s %13s  %s" % (
        "Compet.", "Base somada", "Teto do mes", "Devida", "Lancada", "Diferenca", "Conferencia"))
    print("  " + "-" * 94)
    for linha in periodo["linhas"]:
        conferencia = linha["conferencia"]
        marca = "  (prescrita)" if linha["prescrita"] else ""
        print("  %-8s %13s %13s %13s %13s %13s  %s%s" % (
            linha["competencia"],
            fmt(linha["base_somada"]),
            fmt(linha["teto"]),
            fmt(linha["glosa_criterio_aplicavel"]),
            fmt(linha["glosa_aplicada"]),
            fmt(conferencia["diferenca"]),
            conferencia["veredito"],
            marca))
    print("  " + "-" * 94)
    print("  Competencias apuradas ............... %d" % periodo["competencias_apuradas"])
    if periodo["competencias_prescritas"]:
        print("  Competencias prescritas ............. %d" % periodo["competencias_prescritas"])
    print("  Glosa devida (criterio aplicavel) ... %s" % fmt(periodo["total_glosa_criterio_aplicavel"]))
    print("  Glosa pelo criterio da soma ......... %s" % fmt(periodo["total_glosa_criterio_soma"]))
    print("  Glosa pelo criterio por vinculo ..... %s" % fmt(periodo["total_glosa_criterio_vinculo"]))
    print("  DIFERENCA entre os dois criterios ... %s" % fmt(periodo["total_diferenca_entre_criterios"]))
    _conferencia(periodo)
    if periodo["total_natalina"]:
        print("  13o salario no periodo (fora da base) %s" % fmt(periodo["total_natalina"]))
    if periodo["total_retido"]:
        print("  Efetivamente retido nos contracheques %s" % fmt(periodo["total_retido"]))
        print("  A RESTITUIR (nominal, sem correcao) . %s" % fmt(periodo["total_a_restituir"]))
    pendentes = {p.descricao for p in periodo["pendencias"]}
    if pendentes:
        print()
        print("  ATENCAO - rubricas a classificar com a Dra. Fabiana:")
        for descricao in sorted(pendentes):
            print("    - %s" % descricao)
    print("=" * 78)
    _triagem(periodo)


def _conferencia(periodo):
    """Em quais meses a glosa incidiu e se o orgao pagador acertou.

    E a auditoria que a acao precisa: mes a mes, a glosa lancada contra a que
    os Temas 377, 384 e 359 autorizam.
    """
    com_glosa = periodo["meses_com_glosa"]
    divergentes = periodo["meses_com_divergencia"]

    print()
    print("=" * 96)
    print("  CONFERENCIA DA GLOSA LANCADA PELO ORGAO PAGADOR")
    print("=" * 96)

    if not com_glosa:
        print("  Nenhuma competencia do periodo teve abate-teto lancado na folha.")
    else:
        print("  A glosa incidiu em %d das %d competencias apuradas:"
              % (len(com_glosa), periodo["competencias_apuradas"]))
        for linha in com_glosa:
            retro = ("  + atrasados %s" % fmt(linha["glosa_retroativa"])) \
                if linha["glosa_retroativa"] else ""
            print("    %-8s lancada %13s   devida %13s   %s%s" % (
                linha["competencia"], fmt(linha["glosa_aplicada"]),
                fmt(linha["glosa_criterio_aplicavel"]),
                linha["conferencia"]["veredito"], retro))

    print()
    if not divergentes:
        print("  SEM DIVERGENCIA no mes: o que foi descontado como glosa do mes")
        print("  confere com o criterio aplicavel em todas as competencias.")
    else:
        print("  DIVERGENCIA em %d competencia(s):" % len(divergentes))
        for linha in divergentes:
            print("    %-8s %-12s  lancada %13s  devida %13s  diferenca %13s" % (
                linha["competencia"], linha["conferencia"]["veredito"],
                fmt(linha["glosa_aplicada"]),
                fmt(linha["glosa_criterio_aplicavel"]),
                fmt(linha["conferencia"]["diferenca"])))

    print()
    print("  Glosa do mes lancada no periodo ..... %s" % fmt(periodo["total_glosa_aplicada"]))
    print("  Glosa do mes devida ................. %s" % fmt(periodo["total_glosa_criterio_aplicavel"]))
    if periodo["total_glosa_retroativa"]:
        print("  Atrasados cobrados no periodo ....... %s  << A CONFERIR"
              % fmt(periodo["total_glosa_retroativa"]))
        print("      Refere-se a competencias anteriores, que este calculo nao")
        print("      alcanca. Levantar a quais meses se refere antes de pedir:")
        print("      se aqueles meses tinham excesso, a cobranca era devida.")
    print("  Total retido do cliente ............. %s" % fmt(periodo["total_retido"]))
    print("  A RESTITUIR (nominal, a conferir) ... %s" % fmt(periodo["total_a_restituir"]))

    _temas(periodo)
    print("=" * 96)


def _temas(periodo):
    """Mostra sob qual tema do STF cada grupo de vinculos foi apurado."""
    ativas = [linha for linha in periodo["linhas"] if not linha["prescrita"]]
    if not ativas:
        return
    print()
    print("  CRITERIO APLICADO (referencia: competencia %s)" % ativas[-1]["competencia"])
    print("  Marco temporal do Tema 359: %s - %s"
          % (periodo["marco_rotulo"], periodo["marco_fundamento"]))
    for grupo in ativas[-1]["grupos"]:
        marca = "  << CONTROVERTIDO" if grupo["controvertido"] else ""
        print("    %-46s base %13s  glosa %13s" % (
            grupo["nome"][:46], fmt(grupo["base"]), fmt(grupo["glosa"])))
        print("      %s%s" % (grupo["tema"], marca))
        print("      %s" % grupo["fundamento"])
    _marcos_divergentes(periodo)


def _marcos_divergentes(periodo):
    """Mostra o resultado pela outra leitura do marco temporal, quando muda.

    Obito entre a EC 19 (4/06/1998) e a EC 20 (15/12/1998) e a faixa em que as
    duas leituras dao respostas opostas. A Dra. Fabiana precisa ver as duas
    antes de escolher a tese - e de dimensionar o risco.
    """
    aplicavel = periodo["total_glosa_criterio_aplicavel"]
    alternativo = periodo["total_glosa_criterio_alternativo"]
    if aplicavel == alternativo and not periodo["zona_cinzenta"]:
        return
    print()
    print("  >> AS DUAS LEITURAS DO MARCO TEMPORAL DIVERGEM NESTE CASO")
    if periodo["zona_cinzenta"]:
        print("     Obito entre a EC 19 (4/06/1998) e a EC 20 (15/12/1998): %s"
              % "; ".join(periodo["zona_cinzenta"]))
    print("     Glosa devida por %-28s %s" % (periodo["marco_rotulo"] + ":", fmt(aplicavel)))
    print("     Glosa devida por %-28s %s"
          % (periodo["marco_alternativo_rotulo"] + ":", fmt(alternativo)))
    print("     Diferenca entre as duas teses ....... %s" % fmt(abs(aplicavel - alternativo)))
    print("     Decisao da Dra. Fabiana: --marco ec19 (literal do Tema 359) ou")
    print("     --marco ec20 (art. 40, par. 11, da CF - tese do escritorio).")


def _triagem(periodo):
    """Leitura comercial do resultado, para o atendimento.

    Diz se ha tese, quanto vale por mes e quanto vale o quinquenio. A projecao
    e ESTIMATIVA: assume a glosa do ultimo mes constante, em valor nominal.
    """
    ativas = [linha for linha in periodo["linhas"] if not linha["prescrita"]]
    if not ativas:
        return
    ultima = ativas[-1]
    # O que se reave por mes e o que foi lancado a mais do que os temas
    # autorizam - nao a diferenca teorica entre os criterios.
    mensal = _d(ultima["glosa_aplicada"] - ultima["glosa_criterio_aplicavel"])
    if mensal < 0:
        mensal = _d(0)
    devida = ultima["glosa_criterio_aplicavel"]
    controvertido = any(g["controvertido"] for g in ultima["grupos"])

    print()
    print("=" * 78)
    print("  TRIAGEM DO ATENDIMENTO")
    print("=" * 78)

    if mensal > 0 and devida == 0:
        print("  TESE VIAVEL - a glosa e integralmente indevida pelo criterio aplicavel.")
    elif mensal > 0:
        print("  TESE PARCIAL - parte da glosa e devida (%s/mes) e parte nao." % fmt(devida))
    elif devida > 0:
        print("  GLOSA DEVIDA - o orgao pagador aplicou o criterio que os temas mandam.")
    elif ultima["glosa_criterio_soma"] > 0:
        print("  SEM TESE PELA SOMA - o excesso existe no vinculo isolado.")
    else:
        print("  SEM GLOSA na ultima competencia examinada.")

    if controvertido:
        print("  ATENCAO: ha grupo de vinculos em situacao CONTROVERTIDA - o")
        print("  enquadramento nos temas depende de decisao da Dra. Fabiana.")

    print("  Ultima competencia examinada ........ %s" % ultima["competencia"])
    print("  Glosa indevida no mes ............... %s" % fmt(mensal))
    if mensal > 0:
        print("  Projecao em 12 meses ................ %s" % fmt(mensal * 12))
        print("  Projecao no quinquenio (60 meses) ... %s" % fmt(projecao_quinquenal(mensal)))
        print("  (projecao nominal, glosa constante - o valor de peca e a apuracao acima)")
    if periodo["total_retido"]:
        print("  Ja retido nos contracheques lidos ... %s" % fmt(periodo["total_retido"]))
    print("=" * 78)


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------
def comando_contracheques(args):
    padroes = [args.pasta] if os.path.isfile(args.pasta) else [
        os.path.join(args.pasta, "*.pdf"), os.path.join(args.pasta, "*", "*.pdf"),
    ]
    arquivos = sorted({c for padrao in padroes for c in glob.glob(padrao)})
    if not arquivos:
        print("Nenhum PDF encontrado em %s" % args.pasta)
        return 1

    registros = []
    nome_cliente = args.cliente
    # A mesma competencia costuma aparecer em dois arquivos ("fevereiro 2026" e
    # "fevereiro de 2026"). Sem esta guarda, as rubricas somam em dobro e a base
    # do mes dobra - inventando uma glosa que nao existe.
    ja_lidas = {}
    print("Lendo %d contracheque(s)..." % len(arquivos))
    for caminho in arquivos:
        try:
            lido = ler_contracheque_cpex(caminho)
        except Exception as erro:
            print("  [ignorado] %-38s %s" % (os.path.basename(caminho)[:38], erro))
            continue
        if not lido["competencia"]:
            print("  [ignorado] %-38s sem competencia legivel" % os.path.basename(caminho)[:38])
            continue
        if lido["competencia"] in ja_lidas:
            print("  [duplicado] %-37s %s ja lida em %s" % (
                os.path.basename(caminho)[:37], lido["competencia"],
                ja_lidas[lido["competencia"]]))
            continue
        ja_lidas[lido["competencia"]] = os.path.basename(caminho)
        nome_cliente = nome_cliente or lido.get("nome", "")

        vinculo_conferencia = Vinculo(nome=args.vinculo, parcelas=[
            Parcela(p["descricao"], p["valor"], p["codigo"], p["coluna"])
            for p in lido["parcelas"]
        ])
        if lido.get("total_receitas"):
            ok, mensagem = validar_bruto(vinculo_conferencia, lido["total_receitas"])
            if not ok:
                print("  [conferir] %-38s %s" % (os.path.basename(caminho)[:38], mensagem))

        for parcela in lido["parcelas"]:
            registros.append({
                "competencia": lido["competencia"],
                "vinculo": args.vinculo,
                "orgao": "CPEx / Exercito Brasileiro",
                "matricula": lido.get("matricula", ""),
                "codigo": parcela["codigo"],
                "descricao": parcela["descricao"],
                "valor": parcela["valor"],
                "coluna": parcela["coluna"],
            })
        print("  [ok] %-38s %s  %d rubricas" % (
            os.path.basename(caminho)[:38], lido["competencia"], len(lido["parcelas"])))

    if not registros:
        print("Nada a calcular.")
        return 1

    destino = args.saida or os.path.join(
        args.pasta if os.path.isdir(args.pasta) else os.path.dirname(args.pasta),
        "CALCULO ABATE-TETO")
    return _finalizar(registros, args, destino, nome_cliente)


MODELO_CASO = {
    "cliente": "NOME DO CLIENTE",
    "processo": "",
    "ajuizamento": "01/10/2026",
    "marco_temporal": "ec19",
    "vinculos": [
        {
            "nome": "Pensao militar (Forca Armada)",
            "natureza": "pensao",
            "obito_instituidor": "22/03/2016",
            "orgao": "CPEx / Exercito Brasileiro",
            "fundamento_acumulacao": "art. 29, b, da Lei 3.765/60 (redacao original)",
            "contracheques": "G:\\Meu Drive\\CLIENTES MILITARES\\FULANO\\CONTRACHEQUES EXERCITO"
        },
        {
            "nome": "Aposentadoria (regime proprio)",
            "natureza": "proprio",
            "orgao": "RPPS",
            "meses": {
                "01/2026": "20816,47",
                "02/2026": {"bruto": "21978,07", "fora": "0,00", "glosa": "0,00"}
            }
        }
    ]
}


def comando_modelo_caso(args):
    with open(args.arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(MODELO_CASO, arquivo, ensure_ascii=False, indent=2)
    print("Arquivo de caso modelo gravado em: %s" % args.arquivo)
    print()
    print("Preencha um bloco por vinculo. Cada vinculo aceita UMA destas fontes:")
    print('  "contracheques": pasta com os PDFs do CPEx (leitura automatica)')
    print('  "csv":           arquivo de rubricas (ver comando "modelo")')
    print('  "meses":         mapa competencia -> bruto, ou {bruto, fora, glosa}')
    print()
    print("E declare sempre, em cada vinculo:")
    print('  "natureza":          "pensao" ou "proprio"  <- decide o tema do STF')
    print('  "obito_instituidor": "DD/MM/AAAA", quando for pensao (Tema 359)')
    print()
    print("Depois rode:  python OPERACIONAL/calcular_abate_teto.py caso \"%s\"" % args.arquivo)
    return 0


def comando_caso(args):
    """Apura um caso completo: varios vinculos, varios regimes, mes a mes."""
    with open(args.arquivo, "r", encoding="utf-8-sig") as arquivo:
        caso = json.load(arquivo)

    vinculos = caso.get("vinculos") or []
    if not vinculos:
        print("O arquivo de caso nao tem vinculos.")
        return 1

    print("Caso: %s" % (caso.get("cliente") or "(sem nome)"))
    print("Vinculos: %d" % len(vinculos))
    _avisar_natureza(vinculos)
    print()

    registros = []
    for vinculo in vinculos:
        nome = vinculo.get("nome") or "Vinculo sem nome"
        comum = {
            "vinculo": nome,
            "orgao": vinculo.get("orgao", ""),
            "natureza": vinculo.get("natureza", ""),
            "obito_instituidor": vinculo.get("obito_instituidor", ""),
            "fundamento_acumulacao": vinculo.get("fundamento_acumulacao", ""),
        }
        fontes = [chave for chave in ("contracheques", "csv", "meses") if vinculo.get(chave)]
        if len(fontes) != 1:
            print('  [erro] vinculo "%s": informe exatamente uma fonte '
                  "(contracheques, csv ou meses). Encontrei %d." % (nome, len(fontes)))
            return 1

        try:
            if vinculo.get("contracheques"):
                novos = _ler_pasta_cpex(vinculo["contracheques"], comum)
            elif vinculo.get("csv"):
                novos = _ler_csv_vinculo(vinculo["csv"], comum)
            else:
                novos = _ler_meses(vinculo["meses"], comum)
        except (RuntimeError, OSError, ValueError) as erro:
            print('  [erro] vinculo "%s": %s' % (nome, erro))
            return 1

        print("  %-44s %d competencia(s)" % (nome[:44], len({r["competencia"] for r in novos})))
        registros.extend(novos)

    args.cliente = args.cliente or caso.get("cliente", "")
    args.processo = args.processo or caso.get("processo", "")
    args.ajuizamento = args.ajuizamento or caso.get("ajuizamento", "")
    args.marco = args.marco or caso.get("marco_temporal", "")

    destino = args.saida or os.path.join(
        os.path.dirname(os.path.abspath(args.arquivo)), "CALCULO ABATE-TETO")
    return _finalizar(registros, args, destino, args.cliente)


def _ler_pasta_cpex(pasta, comum):
    """Le todos os contracheques do CPEx de uma pasta, sem duplicar competencia."""
    if not os.path.isdir(pasta):
        raise RuntimeError(
            'pasta de contracheques nao encontrada: "%s". Confira o caminho no '
            "arquivo do caso - acentos contam (CONTRACHEQUES EXERCITO x "
            "CONTRACHEQUES EXERCITO com acento)." % pasta)
    arquivos = sorted({c for padrao in (os.path.join(pasta, "*.pdf"),
                                        os.path.join(pasta, "*", "*.pdf"))
                       for c in glob.glob(padrao)})
    if not arquivos:
        raise RuntimeError('nenhum PDF em "%s".' % pasta)
    registros = []
    ja_lidas = {}
    for caminho in arquivos:
        try:
            lido = ler_contracheque_cpex(caminho)
        except Exception as erro:
            print("    [ignorado] %-34s %s" % (os.path.basename(caminho)[:34], erro))
            continue
        if not lido["competencia"]:
            print("    [ignorado] %-34s sem competencia legivel" % os.path.basename(caminho)[:34])
            continue
        if lido["competencia"] in ja_lidas:
            print("    [duplicado] %-33s %s ja lida em %s" % (
                os.path.basename(caminho)[:33], lido["competencia"],
                ja_lidas[lido["competencia"]]))
            continue
        ja_lidas[lido["competencia"]] = os.path.basename(caminho)

        conferencia = Vinculo(nome=comum["vinculo"], parcelas=[
            Parcela(p["descricao"], p["valor"], p["codigo"], p["coluna"])
            for p in lido["parcelas"]])
        if lido.get("total_receitas"):
            ok, mensagem = validar_bruto(conferencia, lido["total_receitas"])
            if not ok:
                print("    [conferir] %-33s %s" % (os.path.basename(caminho)[:33], mensagem))

        for parcela in lido["parcelas"]:
            registro = dict(comum)
            registro.update({
                "competencia": lido["competencia"],
                "matricula": lido.get("matricula", ""),
                "codigo": parcela["codigo"],
                "descricao": parcela["descricao"],
                "valor": parcela["valor"],
                "coluna": parcela["coluna"],
            })
            registros.append(registro)
    return registros


def _ler_csv_vinculo(caminho, comum):
    """Le um CSV de rubricas, forcando o vinculo e a natureza do bloco."""
    registros = []
    for linha in carregar_csv(caminho):
        registro = dict(comum)
        registro.update({
            "competencia": linha["competencia"],
            "codigo": linha.get("codigo", ""),
            "descricao": linha["descricao"],
            "valor": linha["valor"],
            "coluna": linha.get("coluna", ""),
        })
        registros.append(registro)
    return registros


def _ler_meses(meses, comum):
    """Le o mapa competencia -> bruto (ou {bruto, fora, glosa}).

    E a entrada manual: serve para o regime proprio, cujo contracheque (SIAPE e
    congeneres) esta fora do que o leitor automatico entende.
    """
    registros = []
    for competencia, dado in meses.items():
        if not isinstance(dado, dict):
            dado = {"bruto": dado}
        bruto = dado.get("bruto", "0")
        fora = dado.get("fora", "") or ""
        glosa = dado.get("glosa", "") or ""

        registro = dict(comum)
        registro.update({
            "competencia": competencia, "codigo": "",
            "descricao": "Base bruta informada", "valor": bruto, "coluna": "receita",
            "natureza_parcela": COMPUTAVEL,
        })
        registros.append(registro)

        if _d(fora or 0) > 0:
            fora_reg = dict(comum)
            fora_reg.update({
                "competencia": competencia, "codigo": "",
                "descricao": "Parcelas fora da base informadas", "valor": fora,
                "coluna": "receita", "natureza_parcela": NAO_COMPUTAVEL,
            })
            registros.append(fora_reg)

        if _d(glosa or 0) > 0:
            glosa_reg = dict(comum)
            glosa_reg.update({
                "competencia": competencia, "codigo": "",
                "descricao": "Abate-teto ja descontado", "valor": glosa,
                "coluna": "desconto", "natureza_parcela": ABATE_TETO,
            })
            registros.append(glosa_reg)
    return registros


def comando_csv(args):
    registros = carregar_csv(args.arquivo)
    destino = args.saida or os.path.join(os.path.dirname(os.path.abspath(args.arquivo)),
                                         "CALCULO ABATE-TETO")
    return _finalizar(registros, args, destino, args.cliente)


def comando_rapido(args):
    """Conferencia de um mes: base bruta ja somada por vinculo."""
    registros = []
    for item in args.vinculo:
        if "=" not in item:
            print("Use --vinculo \"Nome do vinculo=VALOR BRUTO\". Recebido: %s" % item)
            return 1
        nome, valor = item.split("=", 1)
        registros.append({
            "competencia": args.competencia,
            "vinculo": nome.strip(),
            "codigo": "",
            "descricao": "Base computavel informada",
            "valor": valor.strip(),
            "coluna": "receita",
            "natureza_parcela": "COMPUTAVEL",
            "fundamento": "Base bruta computavel informada na linha de comando",
        })
    if args.glosa:
        registros.append({
            "competencia": args.competencia,
            "vinculo": registros[0]["vinculo"],
            "codigo": "",
            "descricao": "Abate-teto ja descontado",
            "valor": args.glosa,
            "coluna": "desconto",
            "natureza_parcela": "ABATE_TETO",
            "fundamento": "Glosa informada na linha de comando",
        })
    periodo = calcular_periodo(_montar(registros), _data(args.ajuizamento),
                                _marco(getattr(args, 'marco', '')))
    _resumo(periodo)
    if args.saida:
        caminho = _gravar(periodo, args.saida, args.cliente or "", args.processo or "")
        print("\nMemoria gravada em: %s" % caminho)
    if args.parecer:
        print()
        print("Gerando parecer no timbrado...")
        docx = _gravar_parecer_no_drive(periodo, args.cliente or "", args.processo or "")
        if docx:
            print("Parecer (timbrado) ...... %s" % docx)
    return 0


def comando_modelo(args):
    caminho = modelo_csv(args.arquivo)
    print("CSV modelo gravado em: %s" % caminho)
    print("Preencha uma linha por rubrica e rode:")
    print("  python OPERACIONAL/calcular_abate_teto.py csv \"%s\"" % caminho)
    return 0


def _finalizar(registros, args, destino, cliente):
    periodo = calcular_periodo(_montar(registros), _data(args.ajuizamento),
                                _marco(getattr(args, 'marco', '')))
    _resumo(periodo)
    caminho = _gravar(periodo, destino, cliente or "", args.processo or "")
    print()
    print("Memoria de calculo ...... %s" % caminho)
    print("Apuracao mensal (CSV) ... %s" % os.path.join(destino, "apuracao-mensal.csv"))
    print("Parcelas (CSV) .......... %s" % os.path.join(destino, "parcelas.csv"))
    if getattr(args, "parecer", False):
        print()
        print("Gerando parecer no timbrado...")
        docx = _gravar_parecer_no_drive(periodo, cliente or "", args.processo or "")
        if docx:
            print("Parecer (timbrado) ...... %s" % docx)
    print()
    print("PRONTO PARA REVISAO DA DRA. FABIANA - nada foi protocolado.")
    return 0


def _marco(texto):
    """'ec20' -> MARCO_EC20; qualquer outra coisa -> MARCO_EC19 (literal da tese).

    O default e a leitura LITERAL do Tema 359 (EC 19), que produz a glosa maior
    e o pedido menor - o lado seguro. A tese do escritorio (EC 20, art. 40,
    par. 11) se pede explicitamente com --marco ec20.
    """
    chave = _sem_acento(str(texto or "")).strip().upper().replace(" ", "").replace("/", "")
    return MARCO_EC20 if chave in ("EC20", "20", "EC201998") else MARCO_EC19


def _data(texto):
    if not texto:
        return None
    return datetime.strptime(texto.strip(), "%d/%m/%Y").date()


def main():
    principal = argparse.ArgumentParser(
        description="Calculadora de abate-teto (art. 37, XI, da CF/88).")
    comandos = principal.add_subparsers(dest="comando")

    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("--cliente", default="", help="nome do cliente para a memoria")
    comum.add_argument("--processo", default="", help="numero do processo, se houver")
    comum.add_argument("--ajuizamento", default="", metavar="DD/MM/AAAA",
                       help="data da propositura, para o corte prescricional de 5 anos")
    comum.add_argument("--saida", default="", help="pasta de destino dos arquivos gerados")
    comum.add_argument("--marco", default="", choices=["", "ec19", "ec20"],
                       help="marco temporal do Tema 359: ec19 (literal da tese, "
                            "padrao) ou ec20 (art. 40, par. 11 - tese do escritorio)")
    comum.add_argument("--parecer", action="store_true",
                       help="gera o parecer no timbrado e salva na pasta do cliente "
                            "em PECAS AUTOMACAO (exige --cliente)")

    p1 = comandos.add_parser("contracheques", parents=[comum],
                             help="le os contracheques do CPEx de uma pasta")
    p1.add_argument("pasta")
    p1.add_argument("--vinculo", default="Vinculo unico",
                    help="nome do vinculo a que os contracheques se referem")
    p1.set_defaults(funcao=comando_contracheques)

    p2 = comandos.add_parser("csv", parents=[comum], help="calcula a partir de um CSV de rubricas")
    p2.add_argument("arquivo")
    p2.set_defaults(funcao=comando_csv)

    p3 = comandos.add_parser("rapido", parents=[comum],
                             help="confere um mes so, com as bases ja somadas")
    p3.add_argument("competencia", help="MM/AAAA")
    p3.add_argument("--vinculo", action="append", required=True, metavar="NOME=VALOR",
                    help="repita para cada vinculo: --vinculo \"Pensao militar=25426,80\"")
    p3.add_argument("--glosa", default="", help="abate-teto ja descontado no mes")
    p3.set_defaults(funcao=comando_rapido)

    p4 = comandos.add_parser("modelo", help="grava um CSV modelo para preencher")
    p4.add_argument("arquivo")
    p4.set_defaults(funcao=comando_modelo)

    p5 = comandos.add_parser("caso", parents=[comum],
                             help="apura o caso completo: varios vinculos e regimes")
    p5.add_argument("arquivo", help="arquivo .json do caso (ver 'modelo-caso')")
    p5.set_defaults(funcao=comando_caso)

    p6 = comandos.add_parser("modelo-caso",
                             help="grava um arquivo de caso modelo para preencher")
    p6.add_argument("arquivo")
    p6.set_defaults(funcao=comando_modelo_caso)

    args = principal.parse_args()
    if not getattr(args, "funcao", None):
        principal.print_help()
        return 1
    return args.funcao(args)


if __name__ == "__main__":
    sys.exit(main())
