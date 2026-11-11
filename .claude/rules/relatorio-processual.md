# Relatorio Processual Mensal ao Cliente

> Origem: POPs REAIS do escritorio, em `G:\Meu Drive\ALVES CARNEIRO\RCC E POP\`
> (copia identica em `G:\Meu Drive\POPs\`):
> - `POP – MENSAGEM EMAIL – 1º RELATÓRIO PROCESSUAL.docx`
> - `POP – MENSAGEM EMAIL – RELATÓRIO PROCESSUAL – MESES SUBSEQUENTES.docx`
>
> Sempre que a Dra. Fabiana pedir "monta o relatorio processual do cliente X",
> entregar EXATAMENTE no padrao desta regra: **corpo de e-mail + relatorio anexo**.

## Regra de ouro

A IA **nunca envia** o e-mail nem anexa nada no processo. Entrega os dois artefatos
prontos, marcados **"PRONTO PARA REVISAO DA DRA. FABIANA"**. O disparo e humano.

## Variaveis de cada relatorio

| Variavel | Como preencher |
|---|---|
| `{NOME COMPLETO DO CLIENTE}` | como consta no ADVBOX / na ficha do cliente |
| `{TRATAMENTO}` | `Prezada Senhora` ou `Prezado Senhor`, conforme o cliente |
| `{MES}` | mes de referencia por extenso + ano (`marco de 2026`) |
| `{REMETENTE}` | quem assina o corpo do e-mail — **default: Livia Paula, Auxiliar Juridico**. Confirmar antes de gerar em lote; os POPs originais ainda trazem "Ana Clara" |
| `{TIPO}` | `RELATORIO PROCESSUAL` ou, em caso administrativo, `RELATORIO PROCESSUAL ADMINISTRATIVO` |

**Judicial x administrativo:** se o caso for processo administrativo (INSS, PAD,
Conselho, JMS, requerimento em orgao militar), acrescentar a palavra
**Administrativo** — "Relatorio Processual Administrativo". Vale no titulo do
anexo e no corpo do e-mail.

## 1. Corpo do e-mail

### 1.1 Primeiro relatorio do cliente

```
{TRATAMENTO} {NOME COMPLETO DO CLIENTE}

Meu nome e {REMETENTE}, sou {CARGO} no escritorio Alves Carneiro Advocacia &
Consultoria Juridica.

Como nosso objetivo e sempre manter uma relacao proxima e transparente com nossos
clientes, a partir de agora, {a senhora|o senhor} recebera mensalmente RELATORIO DE
PROCESSO com informacoes atualizadas do seu caso.

Segue em anexo o envio do relatorio de {MES}.

Caso tenha alguma duvida ou solicitacao, por favor, nao hesite em nos contatar.

Desejamos um otimo final de semana!

Um abraco.
Equipe Alves Carneiro Advocacia & Consultoria Juridica.
```

> O fecho "otimo final de semana" so se o envio for as sextas. Em outro dia da
> semana, usar "Desejamos um otimo mes!".

### 1.2 Meses subsequentes

```
{TRATAMENTO} {NOME COMPLETO DO CLIENTE}, meus cumprimentos!

Meu nome e {REMETENTE}, sou {CARGO} no escritorio Alves Carneiro Advocacia &
Consultoria Juridica.

Segue em anexo o envio do relatorio mensal do mes de {MES}, com informacoes
atualizadas sobre o seu processo.

Caso tenha alguma duvida ou solicitacao, por favor, nao hesite em nos contatar.

Desejamos um otimo mes!

Um abraco.
Equipe Alves Carneiro Advocacia & Consultoria Juridica.
```

### 1.3 Assunto do e-mail

`{TIPO} – {Mes}/{Ano} – {Nome do Cliente}`

## 2. O relatorio anexo

### Formatacao
Segue integralmente [padroes-documentos.md](padroes-documentos.md): timbrado do
escritorio (`config/timbrado_modelo.docx`), Segoe UI 11 pt, justificado,
entrelinhas "pelo menos 15 pt", recuo de 1a linha 2,5 cm, e **cada topico em
tabela 1x1 azul claro (DBE5F1), negrito + italico**. Gerado por
`gerar_peca_escritorio()` — nunca em folha branca.

### Estrutura

| Bloco | Conteudo |
|---|---|
| Titulo | `{TIPO}` centralizado, maiusculo, negrito, seguido de `Referencia: {Mes}/{Ano}` |
| Saudacao | `{TRATAMENTO} {NOME COMPLETO DO CLIENTE}` |
| **DADOS DO PROCESSO** (topico) | numero do processo/protocolo, orgao (vara/juizo ou orgao administrativo), partes, objeto do pedido, data de distribuicao/protocolo |
| **SITUACAO ATUAL** (topico) | em que fase o caso esta, em uma frase que o cliente entenda |
| **MOVIMENTACOES DO PERIODO** (topico) | o que aconteceu no mes, em ordem cronologica, com data de cada ato. Se nao houve movimentacao, dizer isso com todas as letras |
| **PROVIDENCIAS ADOTADAS** (topico) | o que o escritorio fez no periodo |
| **PROXIMOS PASSOS** (topico) | o que se espera para o proximo periodo |
| **PENDENCIAS COM O CLIENTE** (topico) | documento ou informacao que falta. Omitir o topico se nao houver |
| Fecho | "Permanecemos a disposicao para qualquer esclarecimento." |
| Local e data | `Rio de Janeiro, {data por extenso}.` centralizado |
| Assinatura | Dra. Fabiana Silva Alves Carneiro — OAB/RJ 188.762 |

### Linguagem
O relatorio e para o **cliente**, nao para o juizo. Escrever em portugues claro,
sem juridiques; quando um termo tecnico for inevitavel, explicar entre parenteses.
Nunca prometer resultado nem estimar prazo de sentenca como se fosse certo.

### Fonte dos dados
Movimentacoes vem do ADVBOX (`/lawsuits`, consulta somente leitura) e do
andamento processual. **Nunca inventar movimentacao, data ou numero de processo** —
se o dado nao existe, deixar o placeholder e avisar a Dra. Fabiana.

## 3. Onde salvar

`G:\Meu Drive\PEÇAS AUTOMAÇÃO\{NOME DO CLIENTE EM MAIUSCULO}\`, com o texto-fonte
em `_fontes\`, conforme [pecas-automacao-drive.md](pecas-automacao-drive.md).

Nome do arquivo:
`{NOME DO CLIENTE} - Relatorio Processual - {MM-YYYY}.docx`
(ou `... - Relatorio Processual Administrativo - {MM-YYYY}.docx`)

Nao sobrescrever arquivo existente — avisar e aguardar decisao.

## 4. Pos-envio (etapa humana)

Do POP, apos o envio ao cliente:
1. Colocar o relatorio enviado na **pasta do cliente**, na subpasta do mes.
2. **Marcar a tarefa correspondente no ADVBOX** como concluida.

Ambos exigem autorizacao explicita: mover arquivo para fora de `PEÇAS AUTOMAÇÃO`
e escrever no ADVBOX estao fora do que a automacao faz sozinha
(ver [fluxo-operacional.md](fluxo-operacional.md) e CLAUDE.md).

## 5. Checklist antes de entregar

- [ ] Tratamento correto (Senhor/Senhora) e nome completo conferido na ficha
- [ ] "Administrativo" incluido quando o caso for administrativo
- [ ] Mes de referencia correto em **todos** os pontos (corpo, assunto e anexo)
- [ ] Nome de quem assina o corpo do e-mail conferido
- [ ] Primeiro relatorio do cliente usa o texto 1.1; demais usam o 1.2
- [ ] Nenhuma movimentacao inventada; placeholders sinalizados
- [ ] Relatorio no timbrado, topicos em tabela azul
- [ ] Marcado "PRONTO PARA REVISAO DA DRA. FABIANA"
