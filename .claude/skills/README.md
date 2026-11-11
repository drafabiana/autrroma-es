# Skills do escritorio — Alves Carneiro

Skills do Claude Code para os procedimentos reais do escritorio. Invocar por
`/nome-da-skill`.

**Escopo:** so **Militar** (area propria) e **Previdenciario** (da Dra. Kenia —
captamos e encaminhamos). Ver CLAUDE.md. Nao ha, nem deve haver, skill para
Trabalhista, TOI, Familia, Civel, Imobiliario ou Empresarial — areas encerradas.

## Procedimentos do escritorio (POPs)

Destilados dos POPs reais em `G:\Meu Drive\ALVES CARNEIRO\RCC E POP\` (fonte
canonica), `ALVES CARNEIRO\POPs\` e `LIVIA - AUXILIAR JURIDICO\POP'S\`.

| Skill | O que faz | POP de origem |
|---|---|---|
| [`/lead-consulta`](pop-lead-consulta.md) | Atende o lead, apresenta o escritorio e oferece a consulta estrategica de R$ 550 | POP Mensagem lead oferecendo a consulta · pop consulta · Ligar para Lead Quente |
| [`/agendar-diagnostico`](pop-agendar-diagnostico.md) | Agenda a Reuniao de Diagnostico pelo link oficial | POP – Agendamento de Reuniao de Diagnostico |
| [`/proposta-honorarios`](pop-proposta-honorarios.md) | Monta a proposta de honorarios Visual Law | Modelo + Prompt de proposta de honorarios |
| [`/envio-contratacao`](pop-envio-contratacao.md) | Kit pos-contratacao: procuracao, manual, declaracao antifraude, boleto | POP – Envio de procuracao, manual do cliente e boleto |
| [`/solicitar-docs`](pop-solicitar-documentos.md) | Pede documento ao cliente com contexto, finalidade e prazo | POP – Solicitacao de documentos aos clientes |
| [`/conferir-docs`](pop-conferencia-documental.md) | Confere a documentacao e classifica COMPLETA/PENDENTE/IMPEDITIVA | POP 01 – Conferencia de documentacao do cliente |
| [`/digitalizar`](pop-digitalizacao.md) | Digitaliza, aplica OCR, nomeia, indexa no Drive e no ADVBOX | POP 01 – Digitalizacao |
| [`/relacionamento`](pop-relacionamento-cliente.md) | Carta de concessao, carta de aposentadoria, avaliacao no Google, aniversario, boas-vindas | POP Carta do Titulo de Pensao · Carta de Aposentadoria · avaliacao Google · Feliz Aniversario |
| [`/encaminhar-kenia`](encaminhar-kenia.md) | Encaminha caso previdenciario comum para a Dra. Kenia, com dossie | — (regra de negocio) |
| [`/script-isencao-ir`](script-isencao-ir.md) | Script da campanha de isencao de IR por doenca grave: abertura, qualificacao SPIN, oferta, follow-up, boas-vindas, objecoes | Livros de vendas do Drive + ficha da tese |
| [`/restituicao-ir`](restituicao-ir.md) | Abre a calculadora de restituicao de IR por molestia grave e cadastra nela o cliente novo (calculo rapido ou completo) | — (dois casos reais do escritorio) |
| [`/script-acordao-2225`](script-acordao-2225.md) | Script da campanha de reducao da pensao militar (Acordao 2.225/2019 TCU): idem, com casos do acervo para treino | Livros de vendas + palestra CDM Niteroi + Caderno SVP |

## Conhecimento e producao juridica

| Skill | O que faz |
|---|---|
| [`/ficha-tese`](ficha-tese.md) | Destila tese do acervo em ficha da BASE_CONHECIMENTO |
| [`/peca-escritorio`](peca-escritorio.md) | Produz peca no DNA de escrita e no timbrado do escritorio |
| [`/formatar-escritorio`](formatar-escritorio.md) | Aplica a formatacao do escritorio a um texto pronto |
| [`/validar`](validar-documentos.md) | Valida documento gerado contra o checklist de conformidade |
| [`/gerar-intake`](gerar-intake.md) | Roda o intake completo de cliente novo |
| [`/jurimetria`](jurimetria.md) | Analise jurimetrica |

## ADVBOX (consulta livre; escrita so com autorizacao)

`/advbox-listar-tarefas` · `/advbox-criar-tarefa` · `/advbox-criar-cliente` ·
`/advbox-criar-processo` · `/advbox-atualizar-processo` · `/advbox-movimentacoes` ·
`/advbox-publicacoes` · `/advbox-historico`

## Regras que valem para todas

1. **A IA nunca protocola e nunca envia.** Peca, e-mail, carta e mensagem saem
   marcados **PRONTO PARA REVISAO DA DRA. FABIANA**.
2. **Escrita no ADVBOX so com autorizacao explicita.** As skills montam o texto do
   lancamento; quem lanca e humano.
3. **Nunca criar pasta ou arquivo no Drive** fora de `PEÇAS AUTOMAÇÃO` sem
   autorizacao — `.claude/rules/fluxo-operacional.md`.
4. **Formatacao e uma so:** `.claude/rules/padroes-documentos.md`.
5. Conferir sempre **nome completo, tratamento e genero** na ficha do cliente — a
   base e majoritariamente de pensionistas mulheres.

## Relatorio processual mensal

Nao e skill — tem regra propria, mais detalhada:
[`.claude/rules/relatorio-processual.md`](../rules/relatorio-processual.md).

## Skills do Drive ainda nao portadas

`G:\Meu Drive\ALVES CARNEIRO\BANCO DE PROMPTS\` guarda 16 arquivos `.skill` (ZIPs com
`SKILL.md` dentro). **Em escopo, ainda nao portadas:**
`agenda-prazos-processuais` · `precatorio-rpv-acompanhamento` ·
`analise-contrato-geral` · `financeiro-juridico-controladoria` ·
`ata-reuniao-cliente` · `personas-cliente-juridico` ·
`auditoria-conversas-comerciais-juridicas` · `treinamento-robos-atendimento-juridico` ·
`followup-comercial-juridico` · `humanizador-de-texto`.

**Fora de escopo, nao portar:** `apelacao-civel`, `contestacao-civel-geral`,
`tutela-de-urgencia-civel` (Civel encerrado). `onboarding-cliente`,
`relatorio-mensal-cliente`, `qualificador-leads-juridicos` e
`roteiro-reuniao-diagnostico-juridico` ja estao cobertos pelas skills acima, que
usam os textos reais do escritorio em vez dos genericos.
