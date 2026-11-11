---
name: pop-digitalizacao
description: Digitalizacao, indexacao e arquivamento de documentos de cliente com scanner Brother, Google Drive e ADVBOX - padroes de PDF/OCR, nomenclatura, estrutura de pastas e conformidade LGPD. Use ao receber documento fisico ou organizar acervo do cliente.
trigger: /digitalizar
---

# Skill: Digitalizacao de Documentos

> Fonte: `G:\Meu Drive\ALVES CARNEIRO\RCC E POP\POP - Digitalização.docx`
> (POP no 01 — Operacional, revisao 18/05/2026). Video: `POP_01__Digitalização.mp4`.

## Objetivo

Garantir digitalizacao, organizacao, indexacao e arquivamento fisico e digital dos
documentos de clientes com qualidade, rastreabilidade e conformidade com a LGPD,
usando **scanner Brother, Google Drive e ADVBOX**, produzindo sempre **PDF
pesquisavel (OCR)** quando aplicavel.

## Material necessario

Scanner Brother e cabo/rede · Computador com Brother iPrint&Scan / ControlCenter ·
Acesso ao Google Drive do escritorio · Acesso ao ADVBOX · Checklist ·
Etiquetas e caneta para pastas fisicas · Limpador de scanner e panos sem fiapos ·
Software OCR (integrado, Adobe Acrobat ou ADVBOX).

## Padroes obrigatorios

| Item | Padrao |
|---|---|
| Formato | **PDF/A** preferencial; PDF padrao quando nao for possivel |
| Resolucao | **300 dpi**; 200 dpi so se o volume for muito alto e a qualidade se mantiver |
| Cor | escala de cinza para texto; colorido so quando necessario |
| Nome do arquivo | `[NomeCliente] [TipoDocumento]-[Sequencia].pdf` |
| Estrutura no Drive | `/Clientes/Militar/[NomeCliente]/[Processo]/Documentos Originais/` |
| Metadados ADVBOX | cliente, data do documento, tipo, processo, observacoes, tags |

## Conformidade LGPD

- Nao compartilhar documentos fora das plataformas autorizadas;
- Registrar consentimento quando necessario e anexar o termo ao processo;
- Manter confidencialidade — acessar apenas pastas autorizadas;
- Documento sensivel (medico, financeiro, dado de saude): **sinalizar ao responsavel**.

## Passo a passo

### 1. Preparacao
- Receber e conferir a lista de documentos;
- Verificar integridade (rasgos, grampos) e remover grampos/clipes;
- Ordenar conforme o checklist;
- Etiquetar o lote: `CPF_CNPJ-Nome-Data`.

### 2. Configurar o scanner Brother
- Ligar scanner e computador;
- Abrir Brother iPrint&Scan / ControlCenter;
- Selecionar perfil: **PDF, 300 dpi, OCR ativo**;
- Fazer teste de uma pagina.

### 3. Digitalizacao
- Alimentar o ADF respeitando a capacidade;
- Iniciar e acompanhar para evitar atolamento;
- Em caso de falha, corrigir e **rescanear o lote afetado**;
- Verificar legibilidade e orientacao do arquivo.

### 4. OCR e revisao
- Aplicar OCR e conferir se o PDF ficou **pesquisavel**;
- Corrigir paginas invertidas, tortas ou ilegiveis.

### 5. Nomear, indexar e arquivar
- Renomear no padrao acima;
- Salvar na estrutura do Drive;
- Indexar no ADVBOX com os metadados;
- Devolver/arquivar o fisico na pasta etiquetada.

### 6. Conferir
Antes de dar o lote por concluido, rodar `/conferir-docs`: digitalizar nao e
conferir.

## Erros que nao podem acontecer

❌ PDF sem OCR quando o documento tem texto · ❌ Pagina faltando, cortada ou
invertida · ❌ Arquivo salvo na pasta de outro cliente · ❌ Nome fora do padrao ·
❌ Documento sensivel em plataforma nao autorizada · ❌ Descartar o fisico sem
autorizacao.

## Nota importante sobre OCR nesta maquina

**A maquina onde as automacoes rodam nao tem OCR instalado** (sem tesseract,
pytesseract ou pdf2image). O OCR do fluxo acima e do **scanner Brother / Acrobat /
ADVBOX**, na digitalizacao — nao do repositorio.

Consequencia pratica: PDF digitalizado que chegar aqui **sem** camada de texto nao e
lido por extrator (`pdfplumber` devolve vazio). Para ler, usar a tool Read com o
parametro `pages` (leitura visual do PDF). Por isso a exigencia de OCR **na origem**
e o que mantem o acervo utilizavel pela automacao.

> Nunca criar pasta ou arquivo no Drive fora de `PEÇAS AUTOMAÇÃO` sem autorizacao
> explicita — ver `.claude/rules/fluxo-operacional.md`.
