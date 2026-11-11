# Padroes de Documentos - Alves Carneiro Advocacia e Consultoria Jurídica

> **Origem deste padrao:** medido na peca REAL do escritorio
> emenda a inicial de reconhecimento de uniao estavel post mortem (Drive do escritorio, pasta da auxiliar juridica)
> (militar/familia - reconhecimento de uniao estavel post mortem, no timbrado
> Alves Carneiro), confirmada pela Dra. Fabiana em 03/09/2026.
>
> **Substitui** o padrao anterior (Ebrima 12pt, espacamento simples, titulos de
> secao em negrito sem tabela), que vinha das iniciais uma peticao inicial do escritorio e
> outra inicial. O Ebrima **nao e mais usado em nenhuma peca**.

## Formatacao Obrigatoria

| Item | Valor |
|---|---|
| Pagina | A4 (21 x 29,7 cm) |
| Margem superior | 2,5 cm |
| Margem inferior | 2,5 cm (o rodape do timbrado ocupa a faixa inferior) |
| Margem esquerda | 3,0 cm |
| Margem direita | 3,0 cm |
| Distancia do cabecalho / rodape | 0,5 cm |
| Fonte | **Segoe UI** |
| Corpo | 11 pt |
| Citacoes / transcricoes | 11 pt, **em italico** |
| Cor do texto | preto |
| Alinhamento padrao | justificado |
| Espacamento entre linhas | **"Pelo menos" 15 pt** (`w:lineRule="atLeast"`, nao "simples") |
| Espaco antes / depois do paragrafo | 0 (nenhum) |
| Recuo de 1a linha do corpo | 2,5 cm |
| Recuo esquerdo das citacoes | 4,0 cm (sem recuo de 1a linha) |

> O "espacamento de paragrafo 2,5" e o **recuo de primeira linha de 2,5 cm** - nao
> e espaco vertical entre paragrafos, que e zero.

## Topicos: tabela azul claro

Cada titulo de secao e uma **tabela de uma celula (1x1)**, e nao um paragrafo:

| Item | Valor |
|---|---|
| Estilo da tabela | `Table Grid` (com bordas) |
| Preenchimento da celula | **`DBE5F1`** (azul claro) |
| Largura | 15,0 cm (21 cm de A4 menos as duas margens de 3 cm) |
| Texto | Segoe UI 11 pt, **negrito + italico** |
| Alinhamento do texto | justificado, sem recuo |

Vale tanto para topicos numerados (`I – DA JUSTICA GRATUITA`, `2.1 – DO BENEFICIO`)
quanto para os que aparecem sem numeracao (`EMENTA`). O motor
(`OPERACIONAL/agente_operacional/escritorio_format.py`) reconhece os dois casos.

> Na peca-modelo o titulo esta so em negrito. O **italico foi acrescentado por
> decisao da Dra. Fabiana em 03/09/2026** - as pecas novas ficam com negrito +
> italico, divergindo de proposito das ja protocoladas.

## Estrutura da Peca (ordem e formatacao de cada bloco)

| Bloco | Formatacao |
|---|---|
| Enderecamento (`EXCELENTISSIMO SENHOR DOUTOR JUIZ...`) | maiusculo, negrito, justificado, sem recuo |
| Qualificacao da parte | justificado, nome da parte em maiusculo e negrito |
| Nome da acao / da peca | centralizado, negrito, maiusculo |
| Parte contraria (`em face do ...`) | justificado, nome do reu em maiusculo e negrito |
| Titulos de secao / topicos | **tabela azul 1x1** - ver secao acima |
| Corpo | justificado, recuo de 1a linha 2,5 cm |
| Citacoes de lei / jurisprudencia | justificado, italico, recuo esquerdo 4 cm |
| Pedidos (`a)`, `b)`, `c)`) | justificado, negrito, sem recuo |
| Valor da causa | justificado, negrito |
| Fecho (`Nestes Termos,` / `Pede e Espera Deferimento.`) | centralizado |
| Local e data (`Rio de Janeiro, 3 de setembro de 2026.`) | centralizado |
| Assinatura | centralizada, negrito: nome em MAIUSCULAS, `OAB/RJ 188.762` na linha seguinte |

Quando houver advogada em parceria, a assinatura dela vem logo abaixo, no mesmo
formato (nome em maiusculas + linha da OAB).

> **Pendente de confirmacao:** o recuo esquerdo de 4 cm das citacoes vem do padrao
> Ebrima anterior e nao foi remedido na peca-modelo. Confirmar com a Dra. Fabiana
> na proxima peca com transcricao longa de jurisprudencia.

## Convencao de Nomes de Arquivos
- Ficha: `{Nome do Cliente} - Ficha Cliente - {Data}`
- Contrato: `{Nome do Cliente} - Contrato de Honorarios`
- Procuracao: `{Nome do Cliente} - Procuracao`
- Declaracao: `{Nome do Cliente} - Declaracao de Hipossuficiencia`
- Pecas: ver [pecas-automacao-drive.md](pecas-automacao-drive.md)

## Estrutura de Pastas (Cliente)
```
{NOME DO CLIENTE (MAIUSCULO)}/
  ATOS INTERNOS/
  DOCUMENTOS DO CLIENTE/
  PASTA DO CLIENTE/
```

## Assinatura
- Local: Rio de Janeiro/RJ
- Escritorio: Alves Carneiro Advocacia e Consultoria Jurídica
- Dra. Fabiana Silva Alves Carneiro - OAB/RJ 188.762 (todas as areas -
  Previdenciario e Militar)

## Timbrado
- Toda peca e gerada sobre o timbrado do escritorio em `config/timbrado_modelo.docx`.
- Nunca gerar peca em folha branca.
- O timbrado tem tres elementos, todos ja embutidos no arquivo:
  1. Cabecalho: logo "ALVES CARNEIRO - Advocacia & Consultoria Jurídica";
  2. Marca d'agua: monograma "A" em cinza claro, ao centro de cada pagina;
  3. Rodape: telefones (21) 3042-6441 e (21) 99485-7337, site, e-mail e endereco
     (Av. Nelson Cardoso 309, Sl. 610, Tanque, Rio de Janeiro/RJ, CEP 22730-000).
- O motor (`OPERACIONAL/agente_operacional/escritorio_format.py`) limpa o corpo e
  insere a peca, preservando cabecalho, marca d'agua, rodape e margens.
- **Nao versionado** (`.gitignore`): em maquina nova, copiar o arquivo manualmente
  ou reextrair de uma peca real (ver `config/timbrado_modelo.LEIA-ME.txt`).

## Cuidado com o Google Docs
Converter a peca para Documentos Google **quebra este padrao**: a fonte Segoe UI nao
existe no Google Docs e e substituida automaticamente. O `.docx` aberto no Word e a
versao fiel. Usar o Docs so para revisar ou comentar, nunca para protocolar.

## Nao usar como referencia
Os arquivos abaixo estao no Drive mas sao material de terceiros (curso/parceria) e
**nao** definem o padrao do escritorio:
- `modelo 1/2/3 ...` (requerimentos e inicial de revisao de CTC) - timbrado de
  Amanda Medeiros Kravchychyn, Arial 10/12pt;
- kit numerado `1. Inicial`, `2. Contestacao`, `3. Manifestacao`, `4. Embargos`,
  `5. Apelacao`, `6. Procuracao`... (nov/2024) - kit de terceiro;
- material `MATERIAL PARA ISENÇÃO DE IR` (IBIJUS) - curso de terceiro;
- pecas em timbrado "Damasceno Santos Advocacia e Consultoria" (parceria com a
  Dra. Priscila Damasceno, OAB/RJ 138.616), fonte Book Antiqua - usar apenas nos
  casos conduzidos em parceria, nunca como padrao geral.

O conteudo desses arquivos serve de referencia de tese; a formatacao, nao.
