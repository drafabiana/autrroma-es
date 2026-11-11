# Onboarding — Alves Carneiro Advocacia e Consultoria Jurídica

Checklist de configuracao. Faca **na ordem**. Marque cada item ao concluir.
Todo o preenchimento acontece em `config/.env` (copie de `config/.env.example`),
em `config/equipe.py` e em `config/regras_financeiras.py`.

---

## 0. O que ja se sabe

- **Nome / marca:** Alves Carneiro Advocacia e Consultoria Jurídica.
- **Advogado responsavel:** Dra. Fabiana Silva Alves Carneiro — OAB/RJ 188.762.
- **E-mail:** dra.fabiana@alvescarneiroadvocaciaeconsultoriajuridica.com. Telefone: (21) 99485-7337.
- **Areas:** Previdenciario (BPC/LOAS, aposentadorias, beneficios por
  incapacidade, pensao por morte, revisoes) e Militar (PAD/Conselhos de
  Disciplina e Justificacao, reforma, promocao, pensao militar, Mandado de
  Seguranca).
- **Abrangencia geografica:** Rio de Janeiro/RJ.
- **Sistema juridico:** NAO CONFIRMADO. Nao ha nenhuma informacao de que o
  escritorio use ADVBOX ou qualquer outro software de gestao — confirmar com a
  Dra. Fabiana antes de configurar `INTEGRACOES/advbox_integration.py`.
- **CRM/atendimento/cobranca:** NAO CONFIRMADO. Nenhuma ferramenta informada.
- **Briefing de onboarding:** AINDA NAO PREENCHIDO pela Dra. Fabiana (formulario
  enviado 16-18/08/2026, sem resposta ate a criacao deste repositorio). Dados
  abaixo vieram da conversa de contratacao por WhatsApp — ver
  `docs/_WHITE_LABEL_SPEC.md` secao 8.
- **Agentes juridicos de IA:** ja existem em `agentes_claude/`, mas ainda sao
  bases genericas (playbook padrao da area), SEM material real da Dra. Fabiana:
  - `carneiro-previdenciario.md` — Previdenciario.
  - `carneiro-militar.md` — Militar.
  Ver `GUIA_INSTALACAO_CLAUDE_AI.md` para instalar como Projects/Skills no
  Claude.ai.
- **Socia de negocio:** Dra. Kenia Helena de Araujo (Silva e Araujo Sociedade
  de Advogados, Patos de Minas/MG) — contrato individualizado, dados dos dois
  escritorios NAO devem se misturar.
- **Timbrado:** AINDA NAO RECEBIDO.

## 1. Credenciais de API (config/.env)

Nenhuma credencial foi recebida ate a criacao deste repositorio. Confirmar com o
Dra. Fabiana, uma a uma:

- [ ] **ANTHROPIC_API_KEY** — chave da API Claude (console.anthropic.com).
- [x] **ADVBOX_API_TOKEN** — recebido e configurado em 03/09/2026. Conexao
      validada (`python INTEGRACOES/advbox_integration.py`).
- [ ] **ASAAS_API_TOKEN** — SE usar Asaas para cobranca (a confirmar).
- [ ] **ZAPSIGN_API_TOKEN** — SE for usar assinatura digital via ZapSign.
- [ ] **ATENDE_DIREITO_TOKEN** — SE for usar CRM/WhatsApp Atende Direito.
- [ ] **Google Cloud** — coloque o JSON de credenciais em `config/credentials.json`
      (Service Account ou OAuth) e, se OAuth, gere o `token.json` no 1o uso.

## 2. Identidade do escritorio (config/.env)

Ja vem com os defaults do Alves Carneiro Advocacia e Consultoria Jurídica. Confira/ajuste:
- [x] ESCRITORIO_NOME / NOME_ESCRITORIO = Alves Carneiro Advocacia e Consultoria Jurídica
- [ ] ESCRITORIO_CNPJ — nao recebido.
- [x] ESCRITORIO_ADVOGADO = Dra. Fabiana Silva Alves Carneiro
- [x] ESCRITORIO_OAB = OAB/RJ 188.762
- [x] ESCRITORIO_CIDADE / CIDADE_FORO = Rio de Janeiro/RJ
- [ ] ESCRITORIO_ENDERECO — endereco fisico do escritorio, nao recebido.
- [x] ESCRITORIO_TELEFONE = (21) 99485-7337, ESCRITORIO_EMAIL =
      dra.fabiana@alvescarneiroadvocaciaeconsultoriajuridica.com
- [ ] ADVOGADO_RESPONSAVEL_EMAIL — confirmar se e o mesmo e-mail institucional
      acima ou um pessoal diferente, para signatario padrao (ZapSign/ADVBOX).

## 3. Usuarios ADVBOX (config/.env + config/equipe.py)

Preenchidos em 03/09/2026 a partir de GET /settings:
- [x] **ADVBOX_USER_RESPONSAVEL** = 240863 (Dra. Fabiana Silva Alves Carneiro).
- [x] ADVBOX_USER_OPERACIONAL = 240863 — **decisao pendente da Dra. Fabiana**:
      manter na conta dela ou passar para LIVIA PAULA (295602).
- [x] ADVBOX_USER_FINANCEIRO = 240863.
- [x] ADVBOX_USER_FROM = 240863.
- [x] ADVBOX_USER_AGENTE = 240863 — nao ha conta-agente separada no ADVBOX; se a
      Dra. Fabiana quiser isolar o CARNEIRO.IA, criar um usuario proprio e trocar.
- [x] ADVBOX_TASK_TYPE_ACOMPANHAMENTO = 8016440 (CONFERIR/REVISAR PETICAO).
- [ ] ADVBOX_TIPO_PROCESSO_PADRAO — deixado VAZIO de proposito (previdenciario e
      militar convivem; um default erraria a area). Preencher so se houver um
      tipo dominante.
- [ ] (Opcional) ADVBOX_USERS_MAP = "ID:NOME,ID:NOME" para exibir nomes nos
      relatorios.

## 4. Google Drive / Docs (config/.env)

Crie no Drive do escritorio e cole os IDs:
- [ ] GOOGLE_TEMPLATE_ID — Google Doc da Ficha-molde.
- [ ] GOOGLE_PASTA_RECLAMANTE — pasta raiz onde nascem as pastas de cliente.
- [ ] GOOGLE_SHEETS_CONTRATOS_ID (+ GOOGLE_PLANILHA_CONTRATOS / GOOGLE_ABA_CONTRATOS)
      — planilha de numeracao de contratos.
- [ ] Modelos e pastas dos documentos do intake (preencher os pares com e sem
      _ID iguais): GOOGLE_TEMPLATE_CONTRATO(_ID) / GOOGLE_PASTA_CONTRATO(_ID),
      GOOGLE_TEMPLATE_PROCURACAO(_ID) / GOOGLE_PASTA_PROCURACAO(_ID),
      GOOGLE_TEMPLATE_DECLARACAO(_ID) / GOOGLE_PASTA_DECLARACAO(_ID).
- [ ] Financeiro: DRIVE_PASTA_FECHAMENTO_ID, DRIVE_PASTA_FINANCEIRO_ID,
      DRIVE_PLANILHA_HISTORICO_ID, DRIVE_PLANILHA_RESULTADO_ID.
- [ ] DRIVE_PASTA_CLIENTES_ID — usada pelo handler de sincronizacao de assinados.

## 5. Regras financeiras (config/regras_financeiras.py)

Vem VAZIO de proposito (sem comissao nenhuma calculada). O escritorio tem um
unico advogado responsavel — nao ha indicacao ate agora de estrutura de
comissionamento com terceiros. Cadastrar apenas se/quando isso for definido:
- [ ] **COMISSOES** — para cada comissionado: rotulo, sufixos na descricao do
      Asaas, percentual, advbox_customers_id, exclusoes e (se for o caso)
      lista_fechada.
- [ ] **ADVBOX_FINANCEIRO** — banco/centro de custo/categoria para lancar
      comissoes.
- [ ] **EXCLUIR_FATURAMENTO** — clientes que nao contam como receita (se houver).
- [ ] **PERCENTUAL_PROVISAO_LUCRO** — se o escritorio usa provisao/reserva
      (default 0).

## 6. Listas de cobranca (FINANCEIRO/)

- [ ] `clientes_nao_cobrar.txt` — um cliente por linha (quem NUNCA recebe
      cobranca).
- [ ] `clientes_negociar.txt` — clientes em negociacao/acordo.

## 7. Padrao de pecas / timbrado

- [x] `config/timbrado_modelo.docx` — OK. Extraido da peca real
      uma peticao inicial do escritorio (Drive do escritorio): logo no cabecalho, marca
      d'agua "A" e rodape de contato. Ver `config/timbrado_modelo.LEIA-ME.txt`.
- [x] Margens confirmadas nas pecas reais: 2,5cm topo / 2,5cm base / 3,0cm
      esquerda / 3,0cm direita, cabecalho e rodape a 0,5cm. O motor ja aplica.
- [x] Padrao de formatacao CONFIRMADO em 03/09/2026: Segoe UI 11pt, entrelinhas
      "Pelo menos" 15pt, topicos em tabela azul DBE5F1. (antes: Ebrima 12pt, recuo de
      1a linha 2,5cm) ou prefere outro — ver `.claude/rules/padroes-documentos.md`.
- [ ] **Previdenciario e Militar:** pedir 1-2 pecas ja protocoladas em cada
      area para calibrar `agentes_claude/carneiro-previdenciario.md` e
      `carneiro-militar.md` puxando o estilo real da Dra. Fabiana (hoje sao
      bases genericas).

## 8. Agente Operacional (CARNEIRO.IA)

- [ ] AGENTE_OP_TOKEN — defina um token forte (autentica o webhook).
- [ ] AGENTE_OP_PORT — porta do servidor (default 8787).
- [ ] (Opcional) AGENTE_OP_USER_PHONES — JSON {"<id_advbox>":"<telefone>"} para
      notificacao WhatsApp ao concluir tarefa.
- [ ] Suba o servico: `OPERACIONAL/agente_operacional/iniciar_servicos.bat`
      (Windows) ou `.sh` (macOS/Linux). Testar com `verificar_servicos` e parar
      com `parar_servicos`.
- [ ] Configure o gatilho/n8n (`n8n_workflow.json`) apontando para a URL do
      webhook e usando o AGENTE_OP_TOKEN.
- [ ] Para rodar 24/7, avaliar deploy em VPS (`docs/DEPLOY_VPS.md`, systemd) —
      decidir com o escritorio se sera VPS propria ou compartilhada.

## 9. Agendamentos

- [ ] SYNC de assinados 3x/dia: `SYNC/sync_assinados.bat` (Windows) / `.sh`
      (macOS/Linux). Agendar via Task Scheduler (Windows) ou cron/launchd
      (macOS/Linux).
- [ ] (Opcional) Cobranca semanal: agendar `FINANCEIRO/cobranca_semanal.py` do
      mesmo jeito.

---

### Verificacao final

- [x] `python OPERACIONAL/main.py tarefas` lista tarefas do ADVBOX sem erro
      (validado em 03/09/2026; `processos` e `prazos` idem).
- [ ] `python FINANCEIRO/fechamento_mensal.py MM/YYYY --sem-lancar` roda o
      fechamento (modo seguro) — depende das regras financeiras (secao 5).
- [ ] Um intake de teste gera os 4 documentos no timbrado real (apos o timbrado
      ser recebido) e envia para assinatura/ADVBOX conforme definido.
- [ ] Testar os 2 agentes juridicos em `agentes_claude/` — ver
      `GUIA_INSTALACAO_CLAUDE_AI.md` para instalar como Projects no Claude.ai.
