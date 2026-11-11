# Abate-teto (art. 37, XI, da CF/88) — como o escritório calcula

> Origem: ações REAIS do escritório em `G:\Meu Drive\CLIENTES MILITARES\`
> (pastas `ABATE TETO` e de um caso de duas pensoes militares) e o caso
> vivo de uma cliente (pensão militar do Exército + proventos
> da UFRJ), em na pasta da cliente no Drive.
>
> Ferramenta: `python OPERACIONAL/calcular_abate_teto.py`. Motor em
> `OPERACIONAL/abate_teto/`, tabela do teto em `config/teto_constitucional.py`.

## A pergunta que a calculadora responde

Quanto, exatamente, o órgão pagador glosou a mais do que podia — mês a mês, com
a fundamentação de cada exclusão. Esse número é o pedido da ação.

## As quatro regras que decidem o cálculo

### 1. O teto é o subsídio de Ministro do STF, e é BRUTO

O limite do art. 37, XI, incide sobre o valor **bruto**, antes de imposto de renda
e de contribuição previdenciária — Resolução CNJ 14/2006, art. 1º, parágrafo único.

> **Armadilha nº 1.** O campo `TOTAL` do espelho da ficha financeira do CPEx é o
> **líquido**, não o bruto. Numa ficha de 2016 de um instituidor (coronel), o
> `TOTAL` de R$ 17.072,29 é o líquido; o bruto é R$ 21.271,84. Usar o líquido
> subestima a glosa e invalida o cálculo. `validar_bruto()` existe só para pegar isso.

A série histórica do teto está em `config/teto_constitucional.py` — **nunca**
hardcodar o valor em outro lugar. Valor vigente: **R$ 46.366,19** desde 02/2025
(Lei 14.520/2023, 3ª parcela).

### 2. Fora da base: indenizatórias, direitos sociais, assistenciais

CF/88, art. 37, § 11 (EC 47/2005): não se computam as parcelas de caráter
indenizatório previstas em lei. Res. CNJ 14/2006, art. 4º detalha o rol — ajuda
de custo, diárias, auxílio-alimentação, fardamento, transporte, moradia,
pré-escolar, adicional de férias, adicional noturno, salário-família, abono de
permanência.

> **Armadilha nº 2 — o 13º.** O CPEx lança a gratificação natalina como
> `ADIC NATAL` e, na antecipação de junho, como `ADIC NATAL-1 PAR`. Somá-la à
> base do mês faz surgir glosa em competência que não tem excesso nenhum: em
> nov/2024 a base da pensao de uma cliente saltava de R$ 23.284,80 para
> R$ 46.569,60 e "estourava" o teto. O 13º fica **fora da base mensal** e é
> confrontado com o teto **em separado** — a calculadora o destaca e **não** faz
> esse confronto, porque a regra varia conforme o órgão pagador.

> **Regra de segurança.** Rubrica não cadastrada **entra** na base e sai marcada
> `conferir`. Errar incluindo gera glosa maior e pedido menor — defensável.
> Errar excluindo infla o pedido do cliente e derruba a credibilidade do cálculo.

### 3. TRÊS temas do STF — e é a natureza do vínculo que diz qual rege

> **A armadilha mais cara deste tipo de ação.** Invocar só o teto por vínculo
> quando o caso é pensão + provento próprio com óbito posterior ao marco é
> entregar a derrota: nessa hipótese o STF **mandou somar**.

| Temas | Julgado | Alcança | Teto incide |
|---|---|---|---|
| **377 e 384** (RE 612.975 e RE 602.043) | 27/04/2020 | acumulação de **cargos, empregos e funções** — vínculos **próprios** do agente, inclusive os proventos da própria aposentadoria | **por vínculo** |
| **359** (RE 602.584) | 06/08/2020 | **pensão** somada a remuneração ou provento próprio, com **óbito do instituidor posterior ao marco temporal** (EC 19 ou EC 20 — ver abaixo) | **sobre a soma** |

Teses literais:

> **Temas 377/384:** "Nos casos autorizados constitucionalmente de acumulação de
> cargos, empregos e funções, a incidência do artigo 37, inciso XI, da
> Constituição Federal, pressupõe a consideração de cada um dos vínculos
> formalizados, afastada a observância do teto remuneratório quanto ao somatório
> dos ganhos do agente público."

> **Tema 359:** "Ocorrida a morte do instituidor da pensão em momento posterior
> ao da Emenda Constitucional nº 19/1998, o teto constitucional previsto no
> inciso XI do artigo 37 da Constituição Federal incide sobre o somatório de
> remuneração ou provento e pensão percebida por servidor."

O próprio acórdão do RE 602.584 (inteiro teor em
`G:\Meu Drive\CLIENTES MILITARES\CLIENTES MILITARES\ABATE TETO\STF_RE_602584_c62a5.pdf`)
separa as duas situações: *"Já agora, o conflito de interesses diz respeito a
institutos distintos, a saber: remuneração e pensão; proventos e pensão."*

### O marco temporal do Tema 359: EC 19 ou EC 20?

A tese do Tema 359 diz **EC 19/1998** (4/06/1998). O escritório sustenta, em
parte dos casos, a **EC 20/1998** (15/12/1998) — e tem fundamento: foi a EC 20
que acrescentou o **art. 40, § 11**, da Constituição, mandando aplicar o limite
do art. 37, XI, *"à soma total dos proventos de inatividade"*. Nas palavras do
voto do **Min. Celso de Mello no próprio RE 602.584**:

> *"A cada uma das relações constituídas aplica-se, isoladamente, o teto
> constitucional. (...) com a edição da Emenda Constitucional nº 20/98, o
> provento de pensão passou a constar expressamente do limite estabelecido no
> art. 37, inciso XI, da Constituição Federal."*

O art. 40, § 11, já era citado numa inicial do acervo — é argumento de casa.

| Data do óbito do instituidor | Pela EC 19 | Pela EC 20 |
|---|---|---|
| até 04/06/1998 | separado | separado |
| **05/06/1998 a 15/12/1998** | **soma** | **separado** |
| a partir de 16/12/1998 | soma | soma |

A faixa do meio é a **zona cinzenta**. A calculadora apura **sempre pelos dois
marcos** e mostra os dois números quando divergem — nenhuma das duas leituras
fica escondida.

```bash
# padrão: EC 19, leitura literal da tese (glosa maior, pedido menor)
python OPERACIONAL/calcular_abate_teto.py caso caso.json

# tese do escritório
python OPERACIONAL/calcular_abate_teto.py caso caso.json --marco ec20
```

Ou no arquivo de caso: `"marco_temporal": "ec20"`.

> **Por que o padrão é a EC 19.** É a redação literal da tese e produz a glosa
> devida **maior** — logo, o pedido **menor**. Errar para esse lado é
> defensável; o contrário infla o pedido. A EC 20 se escolhe conscientemente,
> e o cálculo registra a escolha na memória e no parecer.

**Como a calculadora agrupa** (`agrupar_para_teto`):

| Configuração do cliente | Agrupamento | Tema |
|---|---|---|
| só vínculos próprios | cada um isolado | 377/384 |
| pensão após o marco + provento próprio | **somados num grupo só** | 359 |
| pensão até o marco + provento próprio | isolados | 359, *a contrario* |
| duas ou mais pensões, sem vínculo próprio | isolados, **marcado CONTROVERTIDO** | 359 não alcança pensão com pensão |
| pensão sem data de óbito informada | tratada como posterior ao marco (leitura conservadora) + **marcada para conferir** | 359 |

> **O dia do marco ainda é "anterior".** Com EC 19, "posterior" começa em
> 05/06/1998; com EC 20, em 16/12/1998. Há testes de regressão para os dois
> (`testar_ec19_e_o_marco_exato`, `testar_zona_cinzenta_e_sinalizada`).

> **Declarar a natureza é obrigação de quem monta o caso.** O default é
> `proprio`, que **não** é o lado seguro: tratar uma pensão como vínculo próprio
> afasta o Tema 359, reduz a glosa tida por devida e **infla o pedido**. O comando
> avisa sempre que a natureza ou a data do óbito não vêm declaradas.

A tese por vínculo só se sustenta se a **acumulação for lícita**. Fundamentos já
usados pelo escritório:

- **duas pensões militares:** art. 29, alínea *a*, da Lei 3.765/60 **em sua redação
  original** — preservada para quem contribuiu com a parcela específica de 1,5%,
  pela regra de transição do art. 31 da MP 2.215-10/2001 (caso do acervo: pensao
  do pai, general, + pensao do conjuge, coronel);
- **pensão militar + cargo civil:** art. 29, alínea *b*, da mesma lei (caso do acervo:
  pensao do Exercito + proventos de universidade federal);
- acumulação constitucionalmente autorizada do art. 37, XVI.

Precedentes do acervo: sentença da 10ª VF/RJ no proc. **0181443-60.2017.4.02.5151**
(favorável, depois reformada em 2ª instância, que manteve o reconhecimento da
licitude da cumulação) e TRF-2, **AP/RN 0029113-97.2018.4.02.5101**, que mandou
considerar o valor individual de cada matrícula.

### 4. Prescrição e correção

- **Prescrição:** quinquenal, Decreto 20.910/1932, art. 1º. O desconto é ato de
  **trato sucessivo** — a cada mês renasce a pretensão (STJ, MS 12.198/DF;
  MS 20.105/DF). A calculadora corta as competências anteriores a 5 anos da data
  de ajuizamento informada em `--ajuizamento`.
- **Correção monetária e juros:** a calculadora entrega valores **nominais**.
  A atualização é feita à parte, pelo Manual de Cálculos da Justiça Federal
  vigente. Não inventar índice.
- **Devolução dos atrasados pelo cliente:** quando o órgão pagador exige de volta
  o que pagou a maior, o acervo tem o argumento da irrepetibilidade das verbas
  alimentares recebidas de boa-fé (`ABATE TETO/ACORDÃO NÃO DEVOLUÇÃO DOS VALORES
  PRETERITOS.pdf`).

## A conferência: a Força está glosando certo?

Cada competência sai com um veredito, comparando o que a folha descontou com o
que o critério aplicável autoriza:

| Veredito | O que houve |
|---|---|
| `CORRETA` | a glosa lançada bate com a devida |
| `INDEVIDA` | descontou sem que houvesse excesso algum |
| `A MAIOR` | descontou mais do que o excedente |
| `A MENOR` | descontou menos do que o excedente |
| `NAO LANCADA` | havia excesso e nada foi descontado |
| `SEM GLOSA` | não havia excesso e nada foi descontado |

Tolerância de R$ 0,05 para arredondamento da folha. A saída lista **em quais
meses a glosa incidiu** e **em quais houve divergência**, e a coluna
`tema_aplicado` do `apuracao-mensal.csv` registra sob qual tema cada competência
foi apurada.

> `NAO LANCADA` **não** é boa notícia para o cliente: significa que a Força pode
> cobrar aquele mês depois, como atrasado. Avisar.

## Rubricas de abate-teto no CPEx

Desde 2026 o Exército lança a glosa com código próprio:

| Código | Descrição na folha | O que é |
|---|---|---|
| `I40` | `DA A.37 XI CF/88` | glosa do **mês corrente** |
| `I39` | `DA I40 AT` | **atrasados** da glosa de meses anteriores |

O retroativo fica **fora** do confronto mensal (senão o mês em que foi cobrado
apareceria com glosa absurda), mas entra no total retido do cliente. Antes de
pedir, conferir a quais competências ele se refere — para não pedir o mesmo mês
duas vezes.

> A leitura de `I39` como "atrasados do I40" é **inferência** a partir dos
> contracheques de 2026; a rubrica sai marcada `conferir`. Confirmar com o CPEx.

## Cliente novo: do atendimento à contratação

A calculadora serve a dois momentos diferentes. **Não confundir os dois números.**

### 1. Na reunião — triagem

Com um contracheque em mãos, uma competência basta para saber se há tese:

```bash
python OPERACIONAL/calcular_abate_teto.py rapido 02/2026 \
    --vinculo "Pensao militar=25426,80" --vinculo "Aposentadoria=21978,07" \
    --glosa 1038,68 --cliente "Fulano de Tal"
```

A saída inclui o bloco **TRIAGEM DO ATENDIMENTO**, com três leituras possíveis:

| Veredito | O que significa |
|---|---|
| **TESE VIÁVEL** | a glosa só existe porque o órgão somou os vínculos — é o Tema 377 |
| **SEM TESE PELA SOMA** | o excesso existe no vínculo isolado; conferir se entrou indenizatória na base |
| **SEM GLOSA** | nada a reaver naquela competência |

E a projeção: valor mensal, em 12 meses e no quinquênio (60 meses). **É estimativa** —
assume a glosa constante e valores nominais. Serve para dimensionar o caso na
conversa, nunca como valor da causa.

### 2. Depois — apuração mês a mês dos DOIS regimes

O militar costuma ter dois regimes: a **Força Armada** (pensão ou proventos
militares, contracheque do CPEx) e o **regime próprio** (cargo civil, SIAPE ou
RPPS estadual). O cálculo tem de juntar os dois na mesma competência — é a soma
por mês que decide o teto.

Isso se faz com um **arquivo de caso**:

```bash
python OPERACIONAL/calcular_abate_teto.py modelo-caso caso.json
python OPERACIONAL/calcular_abate_teto.py caso caso.json --parecer
```

```json
{
  "cliente": "Fulano de Tal",
  "ajuizamento": "01/10/2026",
  "vinculos": [
    { "nome": "Pensao militar (Exercito)",
      "natureza": "pensao",
      "obito_instituidor": "22/03/2016",
      "orgao": "CPEx / Exercito Brasileiro",
      "fundamento_acumulacao": "art. 29, b, da Lei 3.765/60 (redacao original)",
      "contracheques": "G:\\Meu Drive\\CLIENTES MILITARES\\FULANO\\CONTRACHEQUES EXÉRCITO" },
    { "nome": "Aposentadoria (regime proprio)",
      "natureza": "proprio",
      "orgao": "RPPS",
      "meses": { "01/2026": "20816,47",
                 "02/2026": { "bruto": "21978,07", "fora": "0,00", "glosa": "0,00" } } }
  ]
}
```

Cada vínculo aceita **uma** fonte:

| Fonte | Quando usar |
|---|---|
| `contracheques` | pasta com os PDFs do CPEx — leitura automática |
| `csv` | rubricas digitadas (qualquer órgão pagador) |
| `meses` | mapa competência → bruto, ou `{bruto, fora, glosa}` — é o **local de entrada manual** do regime próprio, cujo contracheque (SIAPE e congêneres) o leitor automático não entende |

O arquivo de caso fica na pasta do cliente e é reaproveitado: chegando o
contracheque do mês seguinte, acrescenta-se a competência e roda de novo.

### Um vínculo só

```bash
python OPERACIONAL/calcular_abate_teto.py contracheques "G:\Meu Drive\...\CONTRACHEQUES" \
    --vinculo "Pensao militar - Exercito" --cliente "Fulano de Tal" \
    --ajuizamento 01/10/2026 --parecer
```

`--parecer` gera o **parecer de cálculo no timbrado** e o salva na pasta do cliente
em `PEÇAS AUTOMAÇÃO`, com o texto-fonte em `_fontes\` — mesma regra das demais peças
([pecas-automacao-drive.md](pecas-automacao-drive.md)). Arquivo existente **não é
sobrescrito**: o comando avisa e para.

O parecer é escrito para o **cliente**, em português claro: o que ele recebe, qual o
limite, o que o órgão pagador faz, o que o STF decidiu, quanto vale e as ressalvas.
Não é petição — não tem "Nestes Termos" nem pedido.

### Demais formas de entrada

```bash
# Vários vínculos / qualquer órgão pagador: CSV
python OPERACIONAL/calcular_abate_teto.py modelo rubricas.csv
python OPERACIONAL/calcular_abate_teto.py csv rubricas.csv --cliente "Fulano de Tal"

# Testes
python OPERACIONAL/abate_teto/testes.py
```

Saídas: `memoria-de-calculo.txt` (técnica, para os autos), `apuracao-mensal.csv`,
`parcelas.csv` e, com `--parecer`, o DOCX no timbrado.

### Onde os dados do cliente ficam

A calculadora visual guarda os atendimentos no **navegador da máquina** onde é usada
(`localStorage`). Não vai para servidor nenhum e não acompanha outro aparelho. O
arquivo permanente do caso é o parecer no Drive, gerado pelo comando.

## O que a IA faz e o que não faz

**Faz:** ler contracheque do CPEx, classificar rubrica, apurar a glosa pelos dois
critérios, aplicar o corte prescricional, montar a memória de cálculo e apontar
as rubricas que precisam de decisão.

**Não faz:**
- aplicar correção monetária ou juros (Manual da JF, à parte);
- confrontar o 13º com o teto (regra varia por órgão pagador);
- decidir se a acumulação é lícita — isso é juízo da Dra. Fabiana e depende do
  título de pensão e da contribuição de 1,5%;
- ler ficha financeira anual digitalizada (sem camada de texto — ver
  [base-conhecimento-cursos.md](base-conhecimento-cursos.md), seção de OCR);
- protocolar. A memória sai marcada **PRONTO PARA REVISÃO DA DRA. FABIANA**.

## Onde salvar o resultado

A memória vira peça no timbrado pelo motor de sempre
(`gerar_peca_escritorio()`), e o arquivo vai para
`G:\Meu Drive\PEÇAS AUTOMAÇÃO\{NOME DO CLIENTE}\`, com o texto-fonte em
`_fontes\` — ver [pecas-automacao-drive.md](pecas-automacao-drive.md) e
[padroes-documentos.md](padroes-documentos.md).
