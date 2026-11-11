---
name: pop-proposta-honorarios
description: Monta a proposta de honorarios do escritorio no padrao Visual Law - capa, sobre o escritorio, problema, solucao por fase, diferenciais, tabela de honorarios, validade e aceite. Use apos a reuniao de diagnostico, antes do contrato.
trigger: /proposta-honorarios
---

# Skill: Proposta de Honorarios (Visual Law)

> Fontes: `ALVES CARNEIRO\POPs\Modelo de proposta de honorários.docx` e
> `Prompt para proposta de honorários.docx`.

## Quando usar

Depois da **Reuniao de Diagnostico** e da analise do caso, antes do Contrato de
Honorarios. A proposta e o documento que converte — vem antes da ZapSign.

## Dados fixos da advogada responsavel

```
FABIANA SILVA ALVES CARNEIRO
Sócia de FABIANA SILVA ALVES CARNEIRO SOCIEDADE INDIVIDUAL DE ADVOCACIA,
inscrita sob o nº 157372019 perante a OAB/RJ, inscrita no CNPJ nº 35.254.227/0001-48
```
OAB/RJ 188.762 · Rio de Janeiro/RJ · PIX (CNPJ): 35.254.227/0001-48

## Estrutura da proposta

### 1. 🧾 Capa
- Cliente
- Advogada responsavel (bloco acima, integral)
- **Objeto** — ex.: "Requerimento de Habilitacao Inicial a Pensao Militar e Auxilio Funeral"
- **Orgao** — ex.: "Ministerio da Defesa – Exercito Brasileiro / Comando da 1a Regiao
  Militar – SVP/1"

### 2. 💼 Sobre o escritorio
> FABIANA SILVA ALVES CARNEIRO e advogada especialista em Direito Previdenciario
> Militar, com atuacao estrategica em pensoes militares das Forcas Armadas. Possui
> experiencia consolidada na conducao de processos administrativos e judiciais com
> elevado indice de exito. Atua com foco em resultados, celeridade e seguranca
> juridica, sendo tambem palestrante e integrante de comissao especializada da OAB.

Especializacoes: Direito Previdenciario Militar · Direito Administrativo Militar ·
Planejamento Previdenciario Estrategico · Atuacao em pensoes e beneficios militares.

### 3. ⚠️ O problema / desafio
Dizer o que esta em risco **neste caso**, nao em tese. Padrao:
> A [demanda] exige rigor tecnico e correta conducao junto ao [orgao].
> Falhas no processo podem gerar: indeferimento do pedido · atrasos na concessao ·
> perda de valores retroativos.
> A atuacao especializada e essencial para garantir o deferimento e a protecao
> integral do direito.

### 4. ⚖️ Solucao juridica (por fase)

| Fase | Conteudo |
|---|---|
| 📂 **Administrativa** | analise documental completa · enquadramento juridico adequado · elaboracao e protocolo do requerimento · acompanhamento junto ao orgao · atendimento a exigencias administrativas |
| 📈 **Acompanhamento** | monitoramento continuo · atuacao estrategica em exigencias · suporte integral ao cliente |
| ⚖️ **Judicial (se necessaria)** | ajuizamento da acao · defesa do direito e dos valores retroativos |

### 5. ⭐ Diferenciais
Atendimento direto com a advogada responsavel · Especializacao exclusiva em Direito
Previdenciario Militar · Atuacao pratica junto ao Exercito Brasileiro · Comunicacao
clara e estrategica · Foco em deferimento administrativo celere.

### 6. 💰 Honorarios e forma de pagamento

Tabela — **exemplo real de pensao militar + auxilio funeral** (ajustar por caso):

| Modalidade | Descricao | Valor |
|---|---|---|
| Honorarios iniciais | Atuacao completa na fase administrativa (pensao militar e auxilio funeral) | R$ 2.000,00 |
| Exito — Pensao Militar | Percentual sobre valores retroativos ate implantacao do beneficio | 30% sobre os atrasados |
| Exito — Auxilio Funeral | Percentual sobre o valor recebido do beneficio | 30% sobre o valor recebido |

**Servico adicional — Isencao de Imposto de Renda:**

| Servico | Descricao | Honorarios |
|---|---|---|
| Fase administrativa | Elaboracao, protocolo e acompanhamento do pedido de isencao | 30% sobre os valores retroativos |
| Exito economico | Economia gerada com a suspensao do IR | 3 parcelas vincendas, calculadas sobre o ultimo valor mensal descontado de IR, a contar do 1o mes de suspensao |

**Condicoes de pagamento:**
- Valor inicial pago no ato da contratacao
- Honorarios de exito condicionados ao proveito economico
- Base de calculo: valores brutos recebidos/economizados
- Formas: PIX, transferencia ou boleto

### 7. 📅 Validade
`[05 dias uteis]`

### 📌 Consideracoes finais
> A correta conducao tecnica desde o inicio e determinante para o sucesso do
> requerimento. Esta proposta visa assegurar eficiencia, seguranca juridica e
> maximizacao dos direitos envolvidos.

### ✍️ Aceite
> Declaro estar de acordo com os termos apresentados.
> Basta responder a mensagem com: **"ACEITO A PROPOSTA"**
>
> Na sequencia, enviaremos a lista de documentos para inicio imediato do requerimento.

## Formatacao

Design **elegante corporativo minimalista** (Visual Law). Capa com foto da equipe/logo,
etapas com icones/cronograma visual, honorarios em tabela clara.

Os valores, prazos e dados do cliente sao **campos editaveis** — a proposta e
reutilizavel entre clientes. Nunca deixar valor de outro cliente no documento.

> A peca em si segue `.claude/rules/padroes-documentos.md` quando gerada em `.docx`
> pelo motor do escritorio (timbrado, Segoe UI 11pt). A versao Visual Law e material
> comercial, nao peca processual.

## Depois do aceite

1. Enviar a lista de documentos — `/solicitar-docs`
2. Contrato de Honorarios pela **ZapSign**
3. Kit de contratacao — `/envio-contratacao`

Contratos-matriz disponiveis em `G:\Meu Drive\ALVES CARNEIRO\CONTRATOS DE HONORÁRIOS\`:
parceria, reducao de pensao militar (Acordao 2.225), aposentadoria INSS, termo
aditivo, transferencia de cota, declaracao de prevencao a fraudes.

## O que NAO fazer

❌ Prometer resultado ou prazo de concessao · ❌ Estimar retroativos sem calculo ·
❌ Alterar percentual de exito sem autorizacao da Dra. Fabiana ·
❌ Enviar proposta sem validade · ❌ Reaproveitar proposta sem trocar TODOS os dados.

> A IA monta a proposta. **Quem envia e a Dra. Fabiana** — entrega marcada
> **PRONTA PARA REVISAO DA DRA. FABIANA**.
