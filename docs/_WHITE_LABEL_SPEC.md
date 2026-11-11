# Identidade & Spec — Alves Carneiro Advocacia e Consultoria Jurídica

> Documento-guia interno. Toda peça de código/documentação deste repositório deve
> refletir SOMENTE a identidade do Alves Carneiro Advocacia e Consultoria Jurídica.
> Regra de ouro: **zero menção a qualquer outro escritório, pessoa ou cliente que
> não seja do Alves Carneiro Advocacia e Consultoria Jurídica.** Nenhuma credencial, token, ID de
> Drive/ADVBOX, timbrado ou regra de negócio de terceiros pode existir neste
> repositório.

## 1. Identidade do escritório

| Campo | Valor |
|-------|-------|
| Nome / marca | Alves Carneiro Advocacia e Consultoria Jurídica |
| Advogado responsável | Dra. Fabiana Silva Alves Carneiro |
| OAB (responsável) | OAB/RJ 188.762 |
| Cidade / Foro | Rio de Janeiro/RJ |
| Telefone | (21) 99485-7337 |
| E-mail | dra.fabiana@alvescarneiroadvocaciaeconsultoriajuridica.com |
| Áreas | Previdenciário (BPC/LOAS, aposentadorias, benefícios por incapacidade, pensão por morte) e Militar (PAD/Conselhos de Disciplina/Justificação, reforma, promoção, pensão militar, Mandado de Segurança) |
| Abrangência geográfica | Rio de Janeiro/RJ |
| Sistema jurídico em uso | **ADVBOX — confirmado e integrado em 03/09/2026.** Conta ativa: 179 clientes, 212 processos (115 ativos), 158 transações. Token em `config/.env`. Plano de contas, fases e tipos de processo já configurados pelo escritório (grupos Previdenciário, Previdenciário Militar, Administrativo Exército/Marinha/FAB/INSS). |
| CRM/atendimento | **Não confirmado.** Nenhuma ferramenta contratada foi informada. |
| Agente de IA | CARNEIRO.IA |
| Timbrado | **Disponível.** `config/timbrado_modelo.docx` — extraído da peça real uma peticao inicial do escritorio (Drive do escritório): logo no cabeçalho, marca d'água "A" e rodapé de contato. Não versionado (ver `config/timbrado_modelo.LEIA-ME.txt`). |
| Sócia de negócio | Dra. Kênia Helena de Araújo (Silva e Araújo Sociedade de Advogados, Patos de Minas/MG) — contrato individualizado, **não misturar dados dos dois escritórios neste repositório**. |
| Pacote contratado | Titanium (Casal da IA) |

## 2. Credenciais → status neste onboarding

Diferente de outros onboardings, **nenhuma credencial real foi recebida ainda**.
`config/.env.example` vem 100% vazio (exceto identidade textual — nome, OAB, e-mail
e telefone, que já são conhecidos):

```
ANTHROPIC_API_KEY=
ADVBOX_API_TOKEN=
ASAAS_API_TOKEN=
ZAPSIGN_API_TOKEN=
ATENDE_DIREITO_TOKEN=
GOOGLE_APPLICATION_CREDENTIALS=config/credentials.json
AGENTE_OP_TOKEN=
AGENTE_OP_PORT=8787
```

- IDs de pasta do Drive → vazios.
- IDs de usuário do ADVBOX → **preenchidos** (240863 = Dra. Fabiana; 295602 = Lívia Paula).

## 3. Equipe / usuários → config central

Nunca hardcodar pessoas; usar `config/equipe.py` (ou env) com placeholders:

```python
USUARIOS_ADVBOX = {
    "RESPONSAVEL": 240863, # ID ADVBOX da Dra. Fabiana Silva Alves Carneiro (via .env)
    "OPERACIONAL": None,   # ID de quem recebe tarefas operacionais
    "FINANCEIRO": None,
}
USUARIO_PADRAO_TAREFAS = "RESPONSAVEL"  # campo 'from' das tarefas /posts
```

## 4. Regras de negócio → configuráveis (vêm VAZIAS)

Cadastrar no onboarding, em `config/regras_financeiras.py`:
- Comissões (rótulo, sufixos, percentual, exclusões) — o escritório atua com um único
  advogado responsável; não há indicação de estrutura de comissionamento até o momento.
- Exceções de faturamento / clientes que não contam como receita.
- Provisão / reserva de lucro (default 0).
- Listas `clientes_nao_cobrar.txt` / `clientes_negociar.txt` (vazias).

## 5. Formatação de peças

- Motor de formatação: **Segoe UI 11pt**, justificado, entrelinhas "Pelo menos"
  15pt, sem espaço entre parágrafos, recuo de 1ª linha 2,5cm, citações em itálico
  com recuo esquerdo de 4cm, margens 2,5/2,5/3,0/3,0cm, e **tópicos em tabela 1x1
  de fundo azul claro (DBE5F1) com o título em negrito + itálico** — valores
  **medidos na peça real protocolada pela Dra. Fabiana**
  (`emenda de uniao estavel (peca-modelo)`), que substituiu
  o padrão Ebrima 12pt anterior. Detalhe bloco a bloco em
  `.claude/rules/padroes-documentos.md`.
- Timbrado: `config/timbrado_modelo.docx` — **disponível**.
- Assinatura padrão das peças: **Dra. Fabiana Silva Alves Carneiro — OAB/RJ
  188.762 — Rio de Janeiro/RJ**.
- Previdenciário e Militar usam bases genéricas — ver `agentes_claude/carneiro-previdenciario.md`
  e `agentes_claude/carneiro-militar.md` — pendentes de calibração com peças reais
  protocoladas pela Dra. Fabiana.

## 6. Estrutura de pastas (clientes)

Convenção: `{NOME DO CLIENTE}/ATOS INTERNOS/ DOCUMENTOS DO CLIENTE/ PASTA DO CLIENTE`.
IDs de Drive ficam em env (vazios).

## 7. Checklist de aceitação (passa só se TODOS = OK)

- [x] Nenhuma referência a outro escritório/pessoa/cliente que não seja do
      Alves Carneiro Advocacia e Consultoria Jurídica (verificado por varredura antes do commit
      inicial — este repositório partiu de um template de outro cliente e todos
      os resíduos de identidade foram removidos, incluindo dados pessoais como
      CPF/RG e endereços que pertenciam ao template original).
- [x] Nenhum token de terceiro no `.env.example` — todos os campos de credencial
      vêm vazios.
- [x] Assinatura e foro = Dra. Fabiana Silva Alves Carneiro / Rio de Janeiro-RJ.
- [x] OAB preenchida (OAB/RJ 188.762).
- [x] `requirements.txt` idêntico ao núcleo funcional (herdado do template, não alterado).
- [ ] Briefing do onboarding (forms.gle) ainda não preenchido pela Dra. Fabiana —
      CNPJ, RG, endereço completo (2 versões divergentes — ver nota abaixo),
      sistema jurídico em uso e timbrado seguem pendentes.

## 8. Dados já recebidos via WhatsApp (16/08/2026, pré-briefing)

Estes dados vieram da conversa de contratação, não do formulário de briefing formal
(ainda pendente). Usar como base, mas confirmar no briefing:

- Razão social: FABIANA SILVA ALVES CARNEIRO SOCIEDADE INDIVIDUAL DE ADVOCACIA
- CNPJ: 35.254.227/0001-48
- Endereço: Avenida Nelson Cardoso nº 309, salas 718 e 719, Tanque, Rio de Janeiro – RJ
  (a própria Dra. Fabiana avisou que na Receita Federal ainda consta sala 610 — confirmar
  qual endereço usar nos documentos)
