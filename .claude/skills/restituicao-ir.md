---
name: restituicao-ir
description: Abre a calculadora de restituicao de IR por molestia grave e cadastra nela o cliente novo, a partir dos informes e declaracoes da pasta do Drive. Use quando a isencao ja foi reconhecida (INSS, Forca Armada ou RPPS) e falta calcular e pedir a devolucao dos anos anteriores.
trigger: /restituicao-ir
---

# Skill: Restituicao de IR por molestia grave

## A calculadora

**https://claude.ai/artifact/5hKDGSC7LPvBacfHHWyRdb** — privada, abre em qualquer aparelho
com a conta da Dra. Fabiana. Fonte em
[OPERACIONAL/restituicao_ir/calculadora.html](../../OPERACIONAL/restituicao_ir/calculadora.html);
depois de editar, republicar o mesmo arquivo no mesmo artifact (slug
`26058756-a9d6-4718-98fd-2f111674513a`), nunca criar outro.

Os clientes ficam no banco do artifact, colecao `clientes` (so dona e editores leem).
Dois modos:

| Modo | Quando | Campos por ano |
|---|---|---|
| **Calculo rapido** (`modo: "rapido"`) | so ha o recibo ou o extrato do e-CAC | `devidoOrig`, `irrf13`, `restante`, `darfPago` |
| **Completo** (sem `modo`) | ha a declaracao original inteira | `tribTotal`, `tribIsentar`, `parcela65`, `decimo`, `irrfInss`, `irrfOutros`, `irrf13`, `devidoOrig`, `darfPago`, `restRecebida`, `deducoes`, `nota` |

Documento: `{cliente, desde, modo?, atualizado, anos:[{ac, ...}]}`, `doc_id` = nome do
cliente em kebab-case (ex.: `fulano-de-tal`).

## Fluxo para cliente novo

1. **Achar a pasta** do cliente no Drive (`CLIENTES MILITARES\...` ou
   `LIVIA - AUXILIAR JURIDICO\...`) e listar laudo, ato de isencao, informes e declaracoes.
2. **Data de inicio**: do laudo oficial / portaria. Anos antes dela nao entram; anos com
   prazo vencido (5 anos do vencimento da declaracao) a calculadora separa sozinha.
3. **Extrair os valores** com `pdfplumber`; PDF digitalizado se renderiza com `pypdfium2`
   e se le com a tool Read (nao ha OCR nem pdftoppm na maquina).
4. **Escolher o modo**: declaracao inteira → completo; so imposto devido → rapido.
5. **Gravar o cliente** no banco do artifact (`db_write`, colecao `clientes`). Nao
   sobrescrever documento que ja existe sem ler antes.
6. **Conferir**: no completo, o recalculo do imposto da original tem de bater com a
   declaracao (a calculadora mostra ✓). Se nao bater, falta renda ou deducao.
7. **Entregar** o link e o resumo por ano, marcado PRONTO PARA REVISAO DA DRA. FABIANA.

## Armadilhas ja vistas

- **INSS com dois beneficios**: a partir de 2023 o informe e UM so, consolidado. Os dois
  PDFs do ano sao o mesmo informe — somar dobra o calculo (caso real do escritorio).
- **Parcela de 65 anos em dois beneficios**: o INSS aplica em cada um, mas vale uma vez
  por pessoa; o contador soma uma delas de volta aos tributaveis.
- **CRP retificado do CPEx**: o IR do 13o vem somado na linha 3.5 e o campo do 13o fica
  zerado. Esta certo (conferido ao centavo num caso real do escritorio).
- **A maior parte pode estar no DARF**, nao no IR retido: quem tem duas fontes paga no
  ajuste. Isso volta por PER/DCOMP (codigo 0211), um pedido por DARF.
- **Calculo sem informes**: se a renda que sobra fica abaixo da faixa isenta, o valor a
  recuperar e o imposto devido original + o IR do 13o. Basta o recibo de cada ano.
- **Previdencia complementar** (Brasilprev, fundacoes): pode ser isenta, mas o pedido e a
  entidade; resgate tem tratamento diferente de renda mensal.
- **Fonte pagadora que so refez o informe** sem corrigir DIRF/EFD-Reinf: a retificadora
  cai em malha. Confirmar com a fonte antes de transmitir.

## O que a IA nao faz

- Nao transmite retificadora nem PER/DCOMP, nao acessa o e-CAC: o pedido e humano.
- Nao aplica Selic: a Receita corrige sozinha; os valores da calculadora sao nominais.
- Nao decide sobre ano prescrito nem sobre tese de suspensao de prazo — e da Dra. Fabiana.
