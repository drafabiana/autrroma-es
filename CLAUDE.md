# Alves Carneiro Advocacia e Consultoria Jurídica - Central de Automacoes

> Escritorio: **Alves Carneiro Advocacia e Consultoria Jurídica** | Advogado responsavel:
> **Dra. Fabiana Silva Alves Carneiro (OAB/RJ 188.762)**
> Sede/foro: **Rio de Janeiro/RJ**.
> Contato: dra.fabiana@alvescarneiroadvocaciaeconsultoriajuridica.com | (21) 99485-7337.

## Areas — SO DUAS (confirmado em 24/09/2026)

| Area | Quem conduz | Escopo |
|---|---|---|
| **Militar** | **Dra. Fabiana** — area propria | PAD/Conselho de Disciplina/Justificacao, reforma, promocao, pensao militar, abate-teto, acumulacao, CTSM/averbacao, FUSEX/fundo de saude, TEA, isencao de IRPF, MS contra ato de autoridade militar |
| **Previdenciario** | **Dra. Kenia Helena de Araujo** (Silva e Araujo Sociedade de Advogados, Patos de Minas/MG) | BPC/LOAS, aposentadorias, incapacidade, pensao por morte, revisoes, RPPS, aposentadoria especial (inclusive mecanicos de aeronaves), **piso do magisterio** e demais teses de professor |

> **Piso do magisterio e tese previdenciaria** (confirmado em 24/09/2026), nao
> administrativa: o piso incide sobre o **vencimento-base**, que e a base da
> contribuicao e dos proventos — com paridade, alcanca aposentado e pensionista, e o
> Instituto de Previdencia entra no polo passivo. Ver
> [BASE_CONHECIMENTO/PREVIDENCIARIO/piso-nacional-do-magisterio.md](BASE_CONHECIMENTO/PREVIDENCIARIO/piso-nacional-do-magisterio.md).

**Previdenciario nao e conduzido aqui.** O escritorio **capta, atende e encaminha
para a Dra. Kenia**; ela conduz o caso. **Excecao: isencao de IR por doenca grave**
e conduzida aqui para militares, pensionistas **e aposentados** (inclusive INSS e
RPPS) — confirmado em 03/11/2026; nao encaminhar para a Kenia. Contrato individualizado — nao misturar
dados dos dois escritorios. As teses de **mecanicos de aeronaves** (PPP de Varig,
Vasp, Transbrasil e Avianca) sao material a enviar para ela.

**Areas ENCERRADAS — nao se atende mais:** Trabalhista, TOI/Energia (Light),
Familia e Sucessoes, Civel, Imobiliario/Locacao, Empresarial. O acervo delas segue
no Drive so como historico de processos antigos. **Nao gerar peca, nao captar, nao
criar agente, playbook ou skill para nenhuma delas.** Detalhe em
[docs/MAPA_DRIVE.md](docs/MAPA_DRIVE.md), secao 2.

### Excecao: acoes de familia INSTRUMENTAIS a demanda militar

Duas acoes de familia **continuam sendo feitas aqui** e contam como **MILITAR**, porque
as **Forcas Armadas exigem a sentenca** para habilitar a pensao militar:

| Acao | Para que a Forca exige |
|---|---|
| **Interdicao e curatela** | habilitar beneficiario incapaz; sem o termo de curatela definitivo nao ha habilitacao, pagamento de cota-parte nem prova de vida |
| **Reconhecimento (e dissolucao) de uniao estavel** | habilitar a companheira como beneficiaria — declaracao particular e escritura nao substituem o titulo judicial |

Sao **etapa do proprio caso militar**, nao area de familia. O acervo ja vive em
`CLIENTES MILITARES`, e as fichas ficam em `BASE_CONHECIMENTO/MILITAR/`
([interdicao-curatela](BASE_CONHECIMENTO/MILITAR/interdicao-curatela-instrumental.md) ·
[uniao-estavel post mortem](BASE_CONHECIMENTO/MILITAR/uniao-estavel-post-mortem-instrumental.md)).
Qualquer outra demanda de familia (divorcio, alimentos, inventario, guarda) **continua
encerrada**.

## Regra de ouro

**A IA NUNCA protocola.** Toda peca, peticao ou documento gerado pelas automacoes
deste repositorio e SEMPRE para revisao humana da Dra. Fabiana antes de
qualquer protocolo. Nenhum fluxo aqui envia peca direto para o processo. Os 5
agentes juridicos em `agentes_claude/` terminam toda peca marcada **"PRONTA PARA
REVISAO DA DRA. FABIANA"**.

## Estrutura

```
ALVES_CARNEIRO_ADVOGADOS/
├── agentes_claude/       # 2 agentes juridicos prontos (Claude.ai Projects/Skills)
│   ├── carneiro-previdenciario.md   # Previdenciario - base generica, pendente calibracao
│   ├── carneiro-militar.md          # Militar - base generica, pendente calibracao
│   ├── GUIA_INSTALACAO_CLAUDE_AI.md  # Passo a passo p/ instalar como Projects/Skills
│   └── prompt-criar-skill-timbrado.md # Prompt p/ empacotar skill de timbrado
│
├── .claude/agents/       # Mesmos 5 agentes juridicos + pipeline operacional, no
│                         # formato de subagente do Claude Code (auto-carregados)
│
├── INTEGRACOES/          # Modulos compartilhados (todos os squads usam)
│   ├── google_integration.py     # Google Drive/Docs/Sheets
│   ├── advbox_integration.py     # API ADVBOX - EM USO (token configurado)
│   ├── asaas_integration.py      # API Asaas (cobrancas/recebimentos) - se o escritorio usar
│   ├── zapsign_integration.py    # Assinatura digital
│   ├── atendedireito_integration.py # CRM WhatsApp
│   ├── infinitum_integration.py  # API publica do Infinitum - EM USO (token configurado)
│   └── legalmail_integration.py  # Integracao GENERICA/opcional (peticionamento
│       eletronico via LegalMail) - so usar apos confirmar com o escritorio
│
├── INTAKE/              # Squad Comercial - Intake e contratacao
│   ├── main.py                # Orquestrador intake
│   ├── llm_processor.py       # Analise juridica do caso (IA)
│   ├── pdf_extractor.py       # Extracao texto + OCR
│   ├── zapsign_integration.py # Assinatura digital
│   └── atendedireito_integration.py # CRM WhatsApp
│
├── FINANCEIRO/          # Squad Financeiro - Fechamento e conciliacao
│   ├── fechamento_mensal.py   # COMANDO UNICO - fechamento completo
│   ├── processar_extrato.py   # Extrato Asaas + comissoes
│   ├── conciliar_financeiro.py # Conciliacao Asaas x ADVBOX
│   ├── conciliar_c6_advbox.py # Conciliacao banco x ADVBOX
│   ├── cobranca_semanal.py    # Cobranca via WhatsApp/Atende Direito
│   └── preencher_resultado.py # Planilha resultado anual
│
├── OPERACIONAL/          # Squad Operacional - Processos, tarefas, pecas
│   ├── main.py                # Comandos operacionais (tarefas/processos/prazos)
│   ├── peticao_processor.py   # Geracao de peticao inicial (IA)
│   ├── gerar_peticao.py       # Baixar docs / subir peticao formatada
│   ├── protocolo_entrega.py   # Protocolo de entrega/recebimento
│   ├── calcular_abate_teto.py # Calculadora de abate-teto (art. 37, XI, CF)
│   ├── abate_teto/            # Motor do calculo + leitor de contracheque + testes
│   └── agente_operacional/    # Agente CARNEIRO.IA (webhook FastAPI)
│
├── SYNC/                # Sincronizacao de docs assinados (ZapSign -> Drive)
├── DOCS_MODELOS/        # Timbrado + pecas-modelo REAIS do escritorio (vazio - AGUARDANDO)
├── CADASTROS/           # Fichas e dados de clientes
├── BASE_CONHECIMENTO/   # Banco de teses: acervo proprio + cursos, so Militar e Previdenciario
│   ├── INDICE.md        # catalogo (GERADO - nao editar a mao)
│   ├── _MODELO_FICHA.md # template de ficha
│   ├── PREVIDENCIARIO/  # fichas por area
│   ├── MILITAR/
│   ├── PROCESSUAL/
│   └── _extraido/       # texto bruto dos originais (nao versionado)
├── UTILS/               # Scripts utilitarios
│   ├── indexar_cursos.py        # indexa G:\Meu Drive\CURSOS -> BASE_CONHECIMENTO
│   ├── extrair_acervo_teses.py  # extrai o acervo proprio (Militar + Previdenciario)
│   └── gerar_indice_teses.py    # regera BASE_CONHECIMENTO/INDICE.md
│
├── config/              # Configuracoes centralizadas
│   ├── .env             # (criado a partir de .env.example - NAO versionar)
│   ├── .env.example     # Template de variaveis
│   ├── equipe.py         # IDs de usuario ADVBOX por papel
│   ├── regras_financeiras.py # Comissoes/exececoes (configuravel)
│   ├── timbrado_modelo.docx  # Timbrado oficial - OK (extraido de peca real)
│   └── credentials.json # (credenciais Google - NAO versionar)
│
├── docs/                # Documentacao (ONBOARDING, DEPLOY_VPS)
├── .claude/             # Agents, Rules, Skills, Commands
├── CLAUDE.md             # Este arquivo
└── requirements.txt
```

## Squad Comercial (INTAKE)
Comando: `python INTAKE/main.py "TRANSCRICAO.pdf" "DOC_PESSOAL.pdf" "CADASTRO.txt"`

Fluxo:
1. IA analisa transcricao (analise tecnica + questionario) - previdenciario,
   ou militar
2. OCR extrai dados do documento pessoal (CNH/RG)
3. Cria pasta do cliente (3 subpastas padrao)
4. Gera Ficha do Cliente (documento guia)
5. Gera Contrato (numero sequencial automatico)
6. Gera Procuracao
7. Gera Declaracao de Hipossuficiencia (se aplicavel)
8. Envia para assinatura digital (ZapSign, se configurado)
9. Envia mensagem ao cliente via WhatsApp (Atende Direito, se configurado)
10. Cadastra cliente + processo no ADVBOX (funcao pronta; ainda NAO chamada
    automaticamente pelo INTAKE - ver "ADVBOX API" abaixo)
11. Sync docs assinados -> pasta do cliente

## Squad Financeiro (FINANCEIRO)
Comando unico: `python FINANCEIRO/fechamento_mensal.py MM/YYYY`
Sem lancar comissoes: `python FINANCEIRO/fechamento_mensal.py 03/2026 --sem-lancar`

Regras (configuraveis em `config/regras_financeiras.py`):
- Fonte da verdade: ADVBOX (por vencimento, nao competencia).
- Comissoes, exececoes e provisoes: cadastrar no onboarding (vem VAZIO - o
  escritorio tem hoje um unico advogado responsavel, sem estrutura de
  comissionamento definida).
- Distribuicao de lucros NAO e despesa operacional.

## Squad Operacional (OPERACIONAL)
Comandos:
- Tarefas pendentes: `python OPERACIONAL/main.py tarefas`
- Processos ativos: `python OPERACIONAL/main.py processos`
- Prazos em aberto: `python OPERACIONAL/main.py prazos` (vencidos primeiro;
  aceita `--dias N` e `--sem-prazo`)
- Relatorio diario de prazos: `python OPERACIONAL/prazos_diario.py`
  (`--sem-enviar` para so gerar; `--canal email|whatsapp|ambos`)
- Criar tarefa: `python OPERACIONAL/main.py criar-tarefa <lawsuit_id> ACOMPANHAMENTO <responsavel> -m "mensagem" -p 2026-04-08 --urgente`
- Abate-teto: `python OPERACIONAL/calcular_abate_teto.py contracheques "<pasta>" --vinculo "Pensao militar" --ajuizamento DD/MM/AAAA`

### Relatorio diario de prazos (9h)
Tarefa do Windows **"AlvesCarneiro - Prazos Diarios"** chama
`OPERACIONAL/prazos_diario.bat` todo dia as 09:00: consulta o ADVBOX, monta a
lista de prazos em aberto e envia por WhatsApp e/ou e-mail. Cada execucao salva
copia em `OPERACIONAL/relatorios_prazos/` (nao versionado) e registra log em
`_log-execucao.txt`. Canal e destinatarios no `config/.env` (`PRAZOS_ENVIO`,
`PRAZOS_WHATSAPP_PARA`, `PRAZOS_EMAIL_PARA`, bloco `SMTP_*`). Sem credencial
configurada o relatorio e gerado e salvo, e o script avisa que nao enviou -
nunca falha calado.

A coleta vive em `OPERACIONAL/prazos.py`, compartilhada com o comando `prazos`.
**Prazo em aberto inclui o VENCIDO:** a versao anterior consultava so de hoje
ate +14 dias e escondia prazo vencido e nao concluido (em 16/10/2026 mostrava
2 de 8). Nao reintroduzir janela que comece em "hoje".

Cada `GET /posts` do ADVBOX leva ~60s. Com filtro de prazo o `totalCount` vem
MAIOR que o conjunto filtrado (8 registros com `totalCount=9`), entao a
paginacao de `listar_tarefas()` para em pagina curta - sem isso cada relatorio
gastava uma segunda chamada inutil de 60s.

**Desde 05/11/2026 o ADVBOX recusa (422) intervalo de prazo maior que 1 ano.** A
coleta busca os vencidos de ate 3 anos em **fatias de 364 dias** (3-4 chamadas de
~60s); o relatorio falhou de 05 a 10/11 ate isso ser corrigido.

Regras:
- Tarefas ADVBOX usam endpoint /posts (nao /tasks)
- Campo `from` e o usuario responsavel (config/equipe.py / .env)
- Campo de mensagem e "comments" (nao "notes")
- Nunca criar tarefa sem autorizacao explicita
- Pecas geradas sao SEMPRE PARA REVISAO da Dra. Fabiana antes de protocolar
  - ver "Regra de ouro" acima.

### Monitor diario de acordaos do TCU (17:30)
Tarefa do Windows **"AlvesCarneiro - Acordaos TCU"** chama `OPERACIONAL/monitor_tcu.bat`
as 17:30: le os acordaos novos na API de Dados Abertos do TCU, baixa o inteiro teor
(RTF), filtra pelos temas de `config/termos_tcu.py` (controle de legalidade, habilitacao
inicial, cumulacao de 2 aposentadorias + pensao militar, militar + professor/medico,
fator redutor/abate-teto, decadencia/boa-fe, isencao de IR) e pelos **clientes citados**
(snapshot do ADVBOX do espelhamento + `config/tcu_clientes_extra.txt`), resume cada um
com o Claude e envia por e-mail (`TCU_EMAIL_PARA`, senao `PRAZOS_EMAIL_PARA`).
Cliente citado vem primeiro; registro rotineiro sem tese vai para "Rotina".

So os itens que a Dra. Fabiana **marcar** viram ficha: pedido "ficha os itens 3 e 7 do
relatorio do TCU de 03/11" = `python OPERACIONAL/monitor_tcu.py fichar 2026-11-03 3 7`
(ficha-rascunho em `BASE_CONHECIMENTO/MILITAR/`, **sem nome de cliente**, e o INDICE e
regerado). Teste de conexao: `python OPERACIONAL/monitor_tcu.py testar`.

Rede: o TCU **nao responde por IPv6** nesta maquina (o script forca IPv4), e o servidor
de documentos (`contas.tcu.gov.br`) **derruba a conexao apos ~50 downloads seguidos**
(a API de listagem nao). Por isso a leitura e espalhada: tarefa **"AlvesCarneiro -
Acordaos TCU (coleta)"** as 9h/11h/13h/15h com `--sem-enviar` (ate 45 por rodada, 4s
de pausa, para apos 3 falhas seguidas) e a das 17:30 faz a ultima rodada e envia. O
que nao baixou fica na **fila**. Acordao de interesse lido sem IA (chave vazia ou falha)
espera em `sem_ia` e e resumido na primeira rodada com IA. Volume tipico: 300-400
acordaos/semana. Saidas em `OPERACIONAL/relatorios_tcu/` (nao versionado - cita cliente;
acordao de relacao traz nome e CPF completo de cada interessado).

Formatos: o formato do arquivo se decide pelo **conteudo** - o e-TCU entrega `.docx`
com nome `.rtf`; acordao do Plenario com relatorio e voto (servidor `sagas`) tem RTF
que nao responde e e lido pelo **PDF**. Acordao cujo texto falha vai para o **fim da
fila** e sai dela apos 6 tentativas, listado no relatorio com o link: de 05 a 11/11/2026
os mesmos 3 da frente falhavam em toda rodada e a fila ficou travada.

## Espelhamento ADVBOX -> Infinitum (ate 30/11/2026)
O escritorio esta migrando para o Infinitum (org `067c892a-a938-450c-9966-22fd296b1263`;
migracao inicial feita em 31/10/2026). Ate o fim de novembro os dois sistemas convivem,
e o espelhamento e **semiautomatico**:
1. Tarefa do Windows **"AlvesCarneiro - Espelhamento Infinitum"** (07:30) roda
   `SYNC/advbox_infinitum.bat`: so LE o ADVBOX e acumula as mudancas em
   `SYNC/espelhamento/pendencias.json` (nao versionado).
2. Quando a Dra. Fabiana pede **"aplica o espelhamento"**: rodar
   `python SYNC/advbox_infinitum.py pendencias`, aplicar cada item no Infinitum pelo
   conector MCP (ou por `INTEGRACOES/infinitum_integration.py`) e marcar com `python SYNC/advbox_infinitum.py marcar <n...>` (`--nota`
   para o que for ignorado).

### Mapa completo do ADVBOX
`python SYNC/mapear_advbox.py` extrai TUDO o que a API entrega - clientes (com o
cadastro detalhado), processos, financeiro, tarefas, movimentacoes e os dados de
referencia de `/settings` - e grava em `SYNC/mapa_advbox/` (nao versionado: tem
dado pessoal): `mapa.json`, `MAPA.md` (relatorio legivel) e os CSV `clientes`,
`processos`, `transacoes` e `tarefas` (separador `;`, UTF-8 com BOM, abrem no Excel).
Serve de inventario da migracao e de copia do que existe hoje. **Somente leitura.**

- `--completo` acrescenta andamento (`/movements`) e historico de tarefas
  (`/history`) de cada processo: +2 chamadas por processo, ~15 min a mais.
- `--so-relatorio` regera CSV e MAPA.md do cache, sem rede.
- `--limpar-cache` recomeca do zero.

Demora por desenho: o ADVBOX limita GET a 30/min (pausa de 2,1s entre chamadas) e
cada `GET /posts` leva ~60s. Detalhar ~309 clientes custa ~11 min. Cada etapa grava
cache em `mapa_advbox/cache/` e a reexecucao so busca o que falta - pode interromper.

> A diferenca entre `/customers` e os clientes citados nos processos esta medida no
> proprio MAPA.md (secao "De onde vieram os clientes"): a listagem e incompleta, e
> quem migrar confiando so nela perde registros.

### API publica do Infinitum (INTEGRADA - 04/11/2026)
Modulo `INTEGRACOES/infinitum_integration.py`. Docs: https://docs.infinitum.app.br/guide
- Base: `https://public.infinitum.app.br/api/v1/public` | Auth: cabecalho `X-Public-Token`
  (`config/.env` -> `INFINITUM_API_TOKEN`, `INFINITUM_ORG_ID`)
- Paginacao `?page=&limit=`; resposta `{data, total, page, limit}`
- Teste de conexao: `python INTEGRACOES/infinitum_integration.py`
- IDs fixos (POPs Processos/CRM Comercial/Controladoria, databases Clientes/Processos/
  Publicacoes) estao como constantes no topo do modulo.
- Registros de database guardam valores ora pelo UUID do campo, ora pela chave
  (`cpf`, `field_15`): ler sempre por `valores_legiveis()`.
- **Escrita so com pedido explicito**, como no ADVBOX. `completar_registro()` so
  preenche campo vazio. O modulo nao tem funcao de apagar, de proposito.

### Triagem cliente x parte contraria (antes de subir para o Infinitum)
`python SYNC/triagem_clientes.py` gera `SYNC/mapa_advbox/triagem_clientes.csv`:
cada um dos 310 registros de "cliente" do ADVBOX com sugestao CLIENTE / PARTE
CONTRARIA / DUVIDOSO, o motivo e uma coluna DECISAO para a Dra. Fabiana marcar.

**Por que a triagem e obrigatoria:** o `customers[]` do processo **nao tem campo
de papel** - cliente e parte contraria sao o mesmo tipo de registro no ADVBOX.
UNIAO FEDERAL, INSS (4 grafias), ESTADO DO RIO, LIGHT (2 cadastros), MINISTERIO
PUBLICO FEDERAL e 15 empresas com CNPJ estao no mesmo balaio dos clientes reais.

**E por que nada sobe em lote:** o conector do Infinitum **nao tem rota para
apagar registro de cadastro nem card** - so apaga campo de POP, campo de cadastro,
automacao, tarefa e evento de agenda. Registro criado por engano sai so a mao, na
interface. Subida sempre em lote pequeno, depois da marcacao, preenchendo apenas
campo vazio (ver as regras do espelhamento acima).

> A heuristica casa por palavra inteira de proposito: sem isso "FABIANA" casa com
> "FAB" e "CAMILA" com "AMIL". Ainda erra em nome reduzido a iniciais (ex.: "C S A",
> provavelmente menor de idade, cai como sufixo societario) - por isso ha DECISAO.

### Subida ADVBOX -> Infinitum de 04/11/2026 (o que foi e o que NAO foi)
Rastro completo em `SYNC/mapa_advbox/subida_infinitum_2026-11-04.json`.

- **67 cadastros existentes enriquecidos** (de 183): 46 data de nascimento, 24
  documento, 1 e-mail - **so campo vazio**, nada sobrescrito.
- **4 clientes novos criados** (nomes no JSON de rastro, fora do git).
- **NAO subiu**: 58 parte contraria + 60 duvidosos (59 deles sao so um nome, sem CPF
  nem contato), aguardando a coluna DECISAO de `triagem_clientes.csv`.

Tres armadilhas que apareceram na execucao e nao devem ser reaprendidas:
1. **Data**: o ADVBOX devolve nascimento em `DD/MM/AAAA`; o campo `date` do Infinitum
   guarda `AAAA-MM-DD`. Converter sempre, senao grava data malformada.
2. **Concorrencia**: disparar ~11 updates em paralelo faz o Infinitum devolver
   `404 page not found` espurio (4 de 11 falharam). Em lotes de 4 passou 100%.
3. **Papel da parte**: a triagem automatica erra. Quatro pessoas fisicas com CPF
   foram classificadas CLIENTE e eram parte contraria - o que resolveu foi o campo
   `notes` do processo, que traz `Titulo: <cliente> x <parte contraria>`. **Usar
   `notes` do processo para definir o papel** antes de criar cadastro.
   O ADVBOX tambem tem cliente duplicado (um cliente com dois IDs e o mesmo CPF) - conferir CPF contra o Infinitum antes de criar.

### Meta Ads (Facebook/Instagram) - campanhas (INTEGRADA - 11/11/2026)
Modulo `INTEGRACOES/meta_integration.py` (Marketing API). Token de **usuario de
sistema "AUTOMACOES"** (nao expira) em `config/.env` -> `META_ACCESS_TOKEN`, mais
`META_AD_ACCOUNT_ID`, `META_PAGE_ID`, `META_INSTAGRAM_ID`.
Teste: `python INTEGRACOES/meta_integration.py` (lista contas, paginas e Instagram visiveis).
- Leitura livre: campanhas, conjuntos, anuncios, `insights()` (gasto, CPC, CTR, leads, conversas).
- **Tudo o que e criado nasce PAUSADO**; ativar (gastar) so com pedido explicito. Sem funcao de apagar.
- `conferir_texto_oab()` barra promessa de resultado, preco/gratuidade, superlativo e apelo
  de captacao (Provimento OAB 205/2021) - `criar_anuncio()` recusa texto com alerta.
- Campanha so das areas ativas (Militar, isencao de IR, captacao previdenciaria p/ Dra. Kenia).

### Asaas - cobrancas e recebimentos (INTEGRADO - 11/11/2026)
Modulo `INTEGRACOES/asaas_integration.py`. Chave de producao em `config/.env` ->
`ASAAS_API_TOKEN` (conta FABIANA SILVA ALVES CARNEIRO SOCIEDADE INDIVIDUAL DE ADVOCACIA).
Teste: `python INTEGRACOES/asaas_integration.py` (conta, saldo e cobrancas vencidas/a vencer em 7 dias).
- Usado por `FINANCEIRO/cobranca_semanal.py`, `conciliar_financeiro.py` e `fechamento_mensal.py`.
- Leitura livre; **criar cobranca ou cliente no Asaas so com pedido explicito**.
- No Infinitum a conta Asaas **ainda nao esta conectada** (conectar exige liberar a ferramenta
  `infinitum_asaas_connect` ou fazer pela interface do Infinitum).

## Calculadoras no cadastro de clientes (Infinitum)
O cadastro **Clientes** (database `67b7b6a1-f36a-426e-81ba-76e445196893`, ligado ao
POP CRM Comercial pelo campo "Cliente") tem dois campos de atalho, criados em
03/11/2026, tipo `url`, com `defaultValue` apontando para as calculadoras:

| Campo (`field_id`) | Calculadora |
|---|---|
| `calculadora_restituicao_ir` | Restituicao por Molestia Grave (IR, retificadora + PER/DCOMP) |
| `calculadora_abate_teto` | Abate-teto (art. 37, XI - Temas 377, 384 e 359 do STF) |

Os links sao os artifacts publicados; ao republicar a calculadora a URL **nao muda**,
entao o atalho continua valendo. Os 183 clientes migrados do ADVBOX estao SEM esses
campos preenchidos (o default so vale na criacao do registro) - nao houve backfill.

Regras: so ADVBOX -> Infinitum; card sem "ID Advbox" nasceu no Infinitum e nao se toca;
nunca sobrescrever campo ja preenchido no Infinitum (Filiacao e Protocolo Forcas
Armadas sao da Dra. Fabiana - cliente novo entra com "Nao informada"/"Nao se aplica");
anotacoes do ADVBOX, inclusive senha gov, vao para Observacoes do cliente; chave do
cliente e "Migrado do Advbox (ID nnnn)" nas Observacoes. `cliente_novo` pode ser parte
contraria (o ADVBOX nao distingue) - conferir antes de criar. Processo que some do
ADVBOX **nao** autoriza apagar card. O Infinitum recusa e-mail repetido entre clientes
(conjuges): registrar o e-mail nas Observacoes.

## Abate-teto (art. 37, XI, da CF)
Acao de abate-teto exige calculo da glosa mes a mes. Metodologia, armadilhas e
precedentes do acervo em `.claude/rules/abate-teto.md`. Em resumo:
- O teto e o subsidio de Ministro do STF e incide sobre o BRUTO. Serie historica
  em `config/teto_constitucional.py` (unica fonte - nao hardcodar). Vigente:
  **R$ 46.366,19** desde 02/2025 (Lei 14.520/2023).
- **TRES temas do STF decidem, e quem decide qual e a natureza do vinculo:**
  Temas 377 e 384 (RE 612.975 e RE 602.043) - cargos/empregos/funcoes PROPRIOS:
  teto POR VINCULO. Tema 359 (RE 602.584) - PENSAO somada a provento proprio com
  obito do instituidor POSTERIOR ao marco temporal: teto SOBRE A SOMA.
  Invocar so o teto por vinculo nessa segunda hipotese e perder a acao.
- **Marco temporal do Tema 359 - duas leituras.** A tese diz EC 19/1998
  (4/06/1998); o escritorio sustenta em parte dos casos a EC 20/1998
  (15/12/1998), que acrescentou o art. 40, par. 11, da CF (voto do Min. Celso de
  Mello no proprio RE 602.584). Obito ENTRE as duas emendas = zona cinzenta, em
  que as leituras dao respostas opostas. A calculadora apura pelos DOIS marcos e
  mostra os dois numeros; o padrao e `ec19` (literal, pedido menor) e a tese do
  escritorio se pede com `--marco ec20`.
- Cada vinculo declara `natureza` (proprio|pensao) e, sendo pensao,
  `obito_instituidor`. A calculadora agrupa conforme o tema e CONFERE, mes a mes,
  se o orgao pagador glosou certo (CORRETA / INDEVIDA / A MAIOR / A MENOR /
  NAO LANCADA).
- Ficam fora da base: indenizatorias (CF art. 37, par. 11), direitos sociais e
  o 13o salario (confrontado com o teto em separado).
- Valores saem NOMINAIS: correcao e juros pelo Manual de Calculos da JF, a parte.
- **Dois regimes (Forca Armada + regime proprio):** usar o arquivo de caso -
  `modelo-caso caso.json` e depois `caso caso.json`. Cada vinculo entra por
  `contracheques` (PDF do CPEx), `csv` ou `meses` (entrada manual, para o
  contracheque do RPPS/SIAPE, que o leitor automatico nao entende).
- **Cliente novo:** `rapido` faz a triagem na reuniao (veredito + projecao do
  quinquenio, que e ESTIMATIVA); `caso ... --parecer` faz a apuracao real e
  salva o parecer no timbrado em `PEÇAS AUTOMAÇÃO/{CLIENTE}/`, sem sobrescrever.

## Skills dos procedimentos (.claude/skills/)

Os POPs reais do escritorio viraram skills. Catalogo completo em
[.claude/skills/README.md](.claude/skills/README.md).

| Skill | Procedimento |
|---|---|
| `/lead-consulta` | Atendimento ao lead + oferta da consulta estrategica (R$ 550) |
| `/agendar-diagnostico` | Reuniao de Diagnostico pelo link oficial |
| `/proposta-honorarios` | Proposta de honorarios Visual Law |
| `/envio-contratacao` | Procuracao + Manual do Cliente + declaracao antifraude + boleto |
| `/solicitar-docs` | Pedido de documento ao cliente (com contexto e prazo) |
| `/conferir-docs` | Conferencia documental → COMPLETA / PENDENTE / IMPEDITIVA |
| `/digitalizar` | Digitalizacao, OCR, indexacao no Drive e ADVBOX |
| `/relacionamento` | Carta de concessao, aposentadoria, avaliacao Google, aniversario, boas-vindas |
| `/encaminhar-kenia` | Encaminhamento de caso previdenciario comum para a Dra. Kenia |
| `/script-isencao-ir` | Script de vendas da campanha de isencao de IR por doenca grave |
| `/restituicao-ir` | Calculadora de restituicao de IR por molestia grave ([link](https://claude.ai/artifact/5hKDGSC7LPvBacfHHWyRdb)); cadastra o cliente novo nela |
| `/script-acordao-2225` | Script de vendas da campanha de reducao da pensao militar (Acordao 2.225/2019 TCU) |
| `/ficha-tese` | Destila tese do acervo em ficha da BASE_CONHECIMENTO |

Fonte canonica dos POPs: `G:\Meu Drive\ALVES CARNEIRO\RCC E POP\`. Existem duas
copias divergentes no Drive (`ALVES CARNEIRO\POPs\`, com o lado comercial/SDR, e
`LIVIA - AUXILIAR JURIDICO\POP'S\`, operacional) — nao trata-las como iguais.

## Banco de teses (BASE_CONHECIMENTO/)

Acervo de tese das duas areas ativas, alimentado por
`python UTILS/extrair_acervo_teses.py` (pecas e material do Drive) e
`python UTILS/indexar_cursos.py` (cursos). Fichas em `MILITAR/`, `PREVIDENCIARIO/`
e `PROCESSUAL/`, no formato de `_MODELO_FICHA.md`. Ver `/ficha-tese`.

Regra: **material de terceiro serve de tese, nunca de formatacao**; precedente so
entra em peca depois de verificado na fonte oficial.

## Jurisprudencias.ai (INTEGRADO - 11/11/2026)
Busca de jurisprudencia em 54 bases (STF, STJ, TRF1-6, todos os TJs, TRTs, TST, CARF -
~25,6 milhoes de decisoes). Modulo `INTEGRACOES/jurisprudencias_integration.py`; spec em
`https://jurisprudencias.ai/openapi.json`; token em `config/.env` ->
`JURISPRUDENCIAS_API_TOKEN` (Bearer, prefixo `jur_`).
- Teste (nao gasta cota): `python INTEGRACOES/jurisprudencias_integration.py`
- Busca: `... buscar trf2 "\"pensao militar\" teto soma" --ordem julgamento --julg-de 01/01/2022`
- Ementa integral: `... consultar trf2 5056603-33.2023.4.02.5101` (numero no formato
  que a propria busca devolve; "RE 602584" no STF deu 404)
- **Cota: 5 consultas por DIA**, renova a meia-noite de Brasilia (`/courts` nao conta).
  Toda resposta fica em cache em `INTEGRACOES/_cache_jurisprudencias/` (nao versionado):
  busca repetida no mesmo dia e ementa ja lida nao gastam cota. 429 nao e repetido.
  Gastar a cota com busca bem montada (frase exata entre aspas + termos), nao exploratoria.
- Sintaxe: `"frase exata"`, termos somados = E, `a b OR c` = (a e b) ou c, `-termo`
  exclui; parenteses sao ignorados.
- O resultado e **pista, nao fonte oficial**: cada item traz o `url` do tribunal, que
  deve ser aberto e conferido antes de o precedente entrar em peca.

## Agentes juridicos (agentes_claude/ e .claude/agents/)

Dois agentes especializados por area, mais os agentes de pipeline (analista-juridica,
gerador-documentos, compliance-reviewer, revisora-controladoria):

| Agente | Area | Status |
|---|---|---|
| `carneiro-previdenciario.md` | Previdenciario (BPC/LOAS, aposentadorias, incapacidade, pensao por morte) | Base generica - pendente calibracao |
| `carneiro-militar.md` | Militar (PAD/Conselhos, reforma, promocao, pensao militar, MS) | Base generica - pendente calibracao |

Todos seguem a mesma regra de ouro: nunca protocolam, sempre entregam peca
marcada "PRONTA PARA REVISAO DA DRA. FABIANA". Ver `agentes_claude/GUIA_INSTALACAO_CLAUDE_AI.md`
para instalar como Projects/Skills no Claude.ai, ou usar direto como subagentes
do Claude Code (ja copiados em `.claude/agents/`).

## Agente Operacional (CARNEIRO.IA)
Servidor webhook (FastAPI) que recebe disparos e executa categorias:
peca juridica, notificacao de cliente, envio para assinatura, sincronizar
assinados, consultar assinatura e movimentacao processual. Inicia via
`OPERACIONAL/agente_operacional/iniciar_servicos.bat` (Windows) ou `.sh`
(macOS/Linux).

## ADVBOX API (INTEGRADO - 03/09/2026)
Conta ativa do escritorio, com 179 clientes, 212 processos (115 ativos) e 158
transacoes. Token configurado em `config/.env` -> `ADVBOX_API_TOKEN`.
- Base: https://app.advbox.com.br/api/v1
- Auth: Bearer token + User-Agent obrigatorio
- Endpoint tarefas: /posts (GET e POST)
- Endpoint processos: /lawsuits
- Endpoint financeiro: /transactions
- Rate limit: GET 30/min | POST 500/dia
- Teste de conexao: `python INTEGRACOES/advbox_integration.py`

### IDs do escritorio (de GET /settings)
| Item | ID |
|---|---|
| Dra. Fabiana Silva Alves Carneiro | 240863 |
| Livia Paula (juridico@) | 295602 |
| Conta bancaria principal (Itau) | 202404 |
| Centro de custo GERAL | 61488 |
| Tarefa CONFERIR/REVISAR PETICAO (retorno do agente) | 8016440 |

Tipos de processo, fases, origens, categorias e tipos de tarefa NAO sao
hardcodados: resolva por nome com `buscar_id_por_nome()` / `buscar_tipo_tarefa()`
/ `buscar_categoria()`, que ignoram acentuacao.

### Limite de escrita
So ha ESCRITA no ADVBOX com autorizacao explicita da Dra. Fabiana. O INTAKE
importa `cadastrar_cliente`/`cadastrar_processo` mas nao os chama; nenhum fluxo
cria cliente, processo, tarefa ou transacao sozinho. `cadastrar_processo()` exige
o tipo do processo (`dados_processo['tipo']` ou `ADVBOX_TIPO_PROCESSO_PADRAO`) e
falha com mensagem clara se nao resolver - o escritorio tem grupos
PREVIDENCIARIO, PREVIDENCIARIO MILITAR e ADMINISTRATIVO EXERCITO/MARINHA/FAB/INSS,
e um default errado cadastraria o caso na area errada.

## Padroes de peca
- Toda peca produzida pela automacao e salva em `G:\Meu Drive\PEÇAS AUTOMAÇÃO\{NOME
  DO CLIENTE}\`, com o texto-fonte em `_fontes/`. Detalhe em
  `.claude/rules/pecas-automacao-drive.md`.
- Toda peca juridica e gerada no timbrado do escritorio (config/timbrado_modelo.docx
  - JA DISPONIVEL: logo no cabecalho, marca d'agua "A" e rodape de contato,
  extraidos de peca real; nao versionado, ver config/timbrado_modelo.LEIA-ME.txt).
- Assinatura padrao: Dra. Fabiana Silva Alves Carneiro - OAB/RJ 188.762 -
  Rio de Janeiro/RJ.
- Formatacao (medida na peca real "emenda de uniao estavel (peca-modelo)"): **Segoe UI 11pt**,
  justificado, entrelinhas "Pelo menos 15pt", sem espaco entre paragrafos, recuo de
  1a linha 2,5cm, citacoes em italico, margens 2,5/2,5/3,0/3,0cm. Os topicos sao
  **tabelas 1x1 de fundo azul claro (DBE5F1) com o titulo em negrito + italico**.
  Substitui o padrao Ebrima 12pt anterior. Detalhe bloco a bloco em
  `.claude/rules/padroes-documentos.md`.
- Previdenciario e Militar ainda usam o playbook padrao da area
  (`agentes_claude/carneiro-*.md`) ate a Dra. Fabiana enviar pecas reais
  protocoladas para calibracao.

## Base de conhecimento (material de curso)
Material de curso, apostila, livro e palestra fica em `G:\Meu Drive\CURSOS\`. O
original **nunca** entra no repositorio: `python UTILS/indexar_cursos.py` extrai o
texto para `BASE_CONHECIMENTO/_extraido/` (nao versionado) e cria uma ficha-rascunho
na area certa; a IA destila a ficha e a Dra. Fabiana a marca `CONFERIDA`.

Duas regras nao negociaveis: material de terceiro vale pela **tese, nunca pela
formatacao** (o padrao de peca e so o de `padroes-documentos.md`), e **jurisprudencia
de apostila so vai para peca depois de conferida na fonte oficial** - tese de curso
envelhece. Procedimento completo em `.claude/rules/base-conhecimento-cursos.md`.

## Relatorio processual mensal ao cliente
Pedido de "montar o relatorio processual" segue sempre
`.claude/rules/relatorio-processual.md`: corpo de e-mail (texto do POP do
escritorio, versao 1o relatorio x meses subsequentes) + relatorio anexo no
timbrado. Caso administrativo leva "Administrativo" no titulo. A IA nunca envia -
entrega os dois artefatos para revisao da Dra. Fabiana.

## Credenciais (config/.env)
Todas as credenciais ficam em config/.env (copiar de config/.env.example).
NUNCA versionar o .env. Nenhuma credencial foi recebida ate a criacao deste
repositorio - ver docs/ONBOARDING.md para o checklist completo.
