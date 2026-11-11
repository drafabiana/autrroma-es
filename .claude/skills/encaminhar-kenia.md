---
name: encaminhar-kenia
description: Encaminha caso previdenciario (INSS/RPPS civil) para a Dra. Kenia Helena de Araujo, que conduz essa area. Monta o dossie de encaminhamento, a mensagem e o controle. Use sempre que o caso for previdenciario comum e nao previdenciario militar.
trigger: /encaminhar-kenia
---

# Skill: Encaminhamento de Caso Previdenciario para a Dra. Kenia

## Por que existe

O escritorio atua em **duas** areas (ver CLAUDE.md):

| Area | Quem conduz |
|---|---|
| **Militar / Previdenciario Militar** | Dra. Fabiana — area propria |
| **Previdenciario comum (INSS / RPPS civil)** | **Dra. Kenia Helena de Araujo** |

O Alves Carneiro **capta, atende e encaminha**. A conducao do caso previdenciario
comum e dela.

**Dra. Kenia Helena de Araujo** — Silva e Araujo Sociedade de Advogados,
Patos de Minas/MG. **Contrato individualizado: nao misturar dados dos dois
escritorios** (financeiro, ADVBOX, pastas de cliente, relatorios).

## Como saber se o caso e da Kenia

| Fica aqui (Dra. Fabiana) | Vai para a Dra. Kenia |
|---|---|
| Pensao militar (habilitacao, revisao, cota-parte, acumulacao) | Aposentadoria por tempo de contribuicao / idade / especial no **RGPS** |
| Auxilio funeral militar | BPC/LOAS |
| Reforma, promocao, preterição | Beneficio por incapacidade (auxilio-doenca, aposentadoria por invalidez) |
| PAD, Conselho de Disciplina / Justificacao | Pensao por morte **civil** |
| Abate-teto, CTSM, averbacao de tempo militar | Revisao de RMI, buraco negro, indices |
| FUSEX / fundo de saude militar | Salario-maternidade, auxilio-acidente |
| **Isencao de IR por doenca grave** — militares, pensionistas **e aposentados** (inclusive INSS e RPPS) | RPPS civil (municipio, estado, União) — exceto a isencao de IR, que fica aqui |
| TCU em ato de pensao militar | Averbacao de tempo rural, CTC civil |
| — | **Piso do magisterio** e demais teses de professor (ferias, aposentadoria de professor) |
| — | Aposentadoria especial (ruido, PPP) — inclusive mecanicos de aeronaves |

> **Piso do magisterio e previdenciario**, nao administrativo: incide sobre o
> vencimento-base, que e base da contribuicao e dos proventos; com paridade alcanca
> aposentado e pensionista, e o Instituto de Previdencia vai ao polo passivo junto com
> o ente federativo. Ver
> [BASE_CONHECIMENTO/PREVIDENCIARIO/piso-nacional-do-magisterio.md](../../BASE_CONHECIMENTO/PREVIDENCIARIO/piso-nacional-do-magisterio.md).

**Caso hibrido** (ex.: militar que tambem tem vinculo RGPS, CTSM para averbar no
INSS): a parte militar fica aqui, a parte previdenciaria comum vai para a Kenia —
alinhar antes de prometer qualquer coisa ao cliente.

## Teses ja mapeadas para enviar a ela

`G:\Meu Drive\CLIENTES PREVIDENCIARIOS\MECANICOS AERONAVES\` — **aposentadoria
especial de mecanicos de aeronaves**: procedimento de obtencao de PPP junto a
**Varig, Vasp, Transbrasil e Avianca** (material do SNA). E material a destilar em
ficha e encaminhar. Ver `/ficha-tese`.

Outras pastas tematicas previdenciarias no Drive (ver `docs/MAPA_DRIVE.md` 2.2):
`BASE DE CONHECIMENTO - BPC`, `TEA` (checklists BPC/FGTS/IPVA), `AULA PISO
PROFESSORES`, `FERIAS PROFESSOR`, `PESQUISA APOSENTADORIA INVALIDEZ`, `RPPS - AMANDA`,
`FGTS`, `ISENÇÃO IR`, `KENIA` e `kit - KENIA`.

## Passo a passo

### 1. Confirmar que e caso dela
Usar a tabela acima. Na duvida, perguntar a Dra. Fabiana **antes** de falar com o
cliente.

### 2. Conferir a documentacao
Rodar `/conferir-docs` antes de encaminhar. **Nao se manda caso incompleto** — a
Kenia perde tempo e o cliente e cobrado duas vezes pelos mesmos documentos.
Classificacao minima para encaminhar: 🟢 COMPLETA ou 🟡 PENDENTE com a pendencia
relacionada de forma explicita.

### 3. Montar o dossie de encaminhamento

```
ENCAMINHAMENTO — ALVES CARNEIRO → DRA. KENIA HELENA DE ARAUJO
Data: [DD/MM/AAAA]

CLIENTE
  Nome completo:
  CPF:
  Data de nascimento:
  Telefone / WhatsApp:
  E-mail:
  Endereco completo:

DEMANDA
  Beneficio pretendido:
  Regime: RGPS / RPPS ([ente])
  NB / protocolo administrativo (se houver):
  DER / data do requerimento:
  Situacao atual:
  Ha indeferimento? Motivo:
  Ha prazo em curso? Qual e ate quando:

DOCUMENTACAO ANEXA
  [relacionar, com a classificacao de /conferir-docs]

PENDENCIAS
  [o que falta e de quem e a responsabilidade de obter]

ANALISE PRELIMINAR DO ALVES CARNEIRO
  [o que foi apurado na consulta — sem firmar tese pela Kenia]

CONTRATACAO
  Contrato assinado? Com qual escritorio?
  Honorarios combinados:
  Valor pago ate aqui:

PONTO DE CONTATO AQUI
  [nome do responsavel no Alves Carneiro]
```

### 4. Mensagem ao cliente

```
Olá, Sr.(a) [NOME]. Tudo bem?

Aqui é a [REMETENTE], do Alves Carneiro Advocacia e Consultoria Jurídica.

Após a análise do seu caso, identificamos que sua demanda é de Direito
Previdenciário [comum/INSS/RPPS], área conduzida pela Dra. Kenia Helena de Araujo,
do escritório Silva e Araujo Sociedade de Advogados, com quem trabalhamos em
parceria.

Isso significa que seu caso será acompanhado por uma advogada especialista
exatamente nesse tipo de demanda, o que garante a melhor condução técnica para a
sua situação.

Já encaminhamos toda a documentação que você nos enviou, de forma que não será
necessário refazer o envio.

A Dra. Kenia entrará em contato para dar seguimento. Qualquer dúvida sobre essa
transição, pode falar comigo por aqui.

Obrigada!
[REMETENTE]
Alves Carneiro Advocacia e Consultoria Jurídica
```

### 5. Registrar
- Arquivar o dossie na pasta do cliente;
- Registrar o encaminhamento no ADVBOX (**escrita no ADVBOX exige autorizacao
  explicita** — a skill monta o texto, o lancamento e humano);
- Manter o controle de honorarios separado: **contrato individualizado**.

## O que NAO fazer

❌ Firmar tese ou estrategia pela Dra. Kenia · ❌ Prometer prazo ou resultado no
caso dela · ❌ Gerar peca previdenciaria comum aqui · ❌ Misturar o financeiro dos
dois escritorios · ❌ Lancar o caso dela no ADVBOX do Alves Carneiro como processo
proprio · ❌ Mandar caso sem conferencia documental · ❌ Encaminhar sem avisar o
cliente.

> A IA **nao encaminha** nada sozinha. Monta o dossie e as mensagens, marcados
> **PRONTO PARA REVISAO DA DRA. FABIANA**.
