---
name: pop-conferencia-documental
description: Confere a documentacao recebida do cliente antes da producao juridica - pertinencia, legibilidade, completude, conferencia cruzada e classificacao COMPLETA/PENDENTE/IMPEDITIVA. Use ao iniciar caso novo, ao receber documentos ou complementacao, e antes de qualquer peca.
trigger: /conferir-docs
---

# Skill: Conferencia Documental do Cliente

> Fonte: `G:\Meu Drive\ALVES CARNEIRO\RCC E POP\POP - novo CONFERÊNCIA DE DOCUMENTAÇÃO DO CLIENTE.docx`
> (POP 01 — Controladoria Juridica, responsavel: Livia). Versao longa no mesmo
> diretorio e em `LIVIA - AUXILIAR JURIDICO/POP'S/`.

## Quando usar

- Caso novo entrando;
- Recebimento de documentos ou de complementacao documental;
- Antes de liberar qualquer producao juridica (peca, requerimento, relatorio).

Status de entrada no ADVBOX: **EM CONFERENCIA DOCUMENTAL**.

## Passo a passo

### 1. Identificar cliente e demanda
- [ ] Confirmar nome completo do cliente
- [ ] Verificar a demanda no ADVBOX (`/lawsuits`, leitura)
- [ ] Identificar quais documentos sao necessarios para ESTA demanda
- [ ] Consultar o checklist da demanda

**Nao iniciar sem saber o que esta sendo conferido.**

### 2. Abrir TODOS os documentos
Nunca conferir pelo nome do arquivo. Para cada documento:
- [ ] pertence ao cliente correto
- [ ] corresponde ao documento solicitado
- [ ] esta legivel
- [ ] esta completo (todas as paginas)
- [ ] tem frente e verso, quando necessario

### 3. Conferir os dados principais

| Bloco | Conferir |
|---|---|
| **Pessoais** | nome, CPF, RG, data de nascimento, endereco |
| **Demanda militar** | instituidor, Forca, posto/graduacao, data do obito, titulo de pensao, cota-parte, contracheques, requerimentos e decisoes administrativas |
| **Medicos** | nome do paciente, diagnostico, CID, data, medico/CRM, laudos, exames e pericias |

### 4. Conferencia cruzada
Comparar a mesma informacao entre documentos diferentes:
- Nome: RG × CPF × certidao
- Data do obito: certidao × titulo de pensao
- Posto/graduacao: documento militar × titulo de pensao × contracheque
- Valores / cota-parte: titulo × contracheques

**Regra:** havendo divergencia, **NAO escolher** qual informacao parece certa.
Registrar e sinalizar.

### 5. Classificar cada item
`recebido e conferido` · `nao recebido` · `incompleto` · `ilegivel` ·
`divergente` · `nao aplicavel`

## Classificacao final (obrigatoria)

| Classificacao | Quando | Proximo status |
|---|---|---|
| 🟢 **COMPLETA** | tudo recebido e conferido | **LIBERADA PARA PRODUCAO** |
| 🟡 **PENDENTE** | falta documento, ou ha incompleto / ilegivel / divergente | **PENDENCIA DOCUMENTAL** — solicitar complementacao (ver `/solicitar-docs`); ao chegar, voltar para EM CONFERENCIA DOCUMENTAL |
| 🔴 **IMPEDITIVA** | falta documento essencial para continuar | **PENDENCIA IMPEDITIVA** — producao juridica bloqueada |

## Registro no ADVBOX

Escrever no ADVBOX **exige autorizacao explicita da Dra. Fabiana** (ver CLAUDE.md).
Esta skill **monta o texto do registro** e entrega para lancamento humano:

```
CONFERENCIA DOCUMENTAL
Cliente:
Demanda:
Classificacao: Completa / Pendente / Impeditiva
Documentos conferidos:
  [relacionar]
Pendencias:
  [relacionar]
Divergencias:
  [relacionar]
Providencia seguinte:
  [informar]
```

## Checklist antes de mudar o status

☐ Conferi o cliente correto? ☐ Sei qual e a demanda? ☐ Consultei o checklist?
☐ Abri todos os arquivos? ☐ Li os documentos? ☐ Conferi nomes e datas?
☐ Conferi as informacoes militares, quando aplicavel? ☐ Fiz conferencia cruzada?
☐ Identifiquei documentos faltantes? ☐ Registrei divergencias?
☐ Atualizei o ADVBOX? ☐ Defini corretamente o proximo status?

## Erros que nao podem acontecer

❌ Presumir informacao · ❌ Conferir pelo nome do arquivo · ❌ Dar por completa sem
abrir tudo · ❌ Ignorar divergencia · ❌ Usar documento de outro cliente ·
❌ Preencher de memoria · ❌ Passar de pendencia para producao sem nova conferencia ·
❌ Perguntar a Dra. Fabiana antes de verificar POP, documentos e ADVBOX.

## Como encaminhar duvida

Antes de perguntar: conferir o POP, o documento, o ADVBOX e os demais documentos.
Persistindo a duvida, enviar neste formato:

```
Cliente:
Duvida:
Documento conferido:
Informacao encontrada:
O que ja verifiquei:
Ponto que precisa de validacao:
```

## Regra de ouro

**SE NAO ABRIU, NAO CONFERIU.
SE NAO ENCONTROU, NAO PRESUMA.
SE HOUVER DIVERGENCIA, NAO ESCOLHA — SINALIZE.
SE O CLIENTE ENVIAR NOVO DOCUMENTO, CONFIRA NOVAMENTE.**

## Limitacao desta maquina

Nao ha OCR instalado. PDF digitalizado sem camada de texto **nao** e lido por
extrator — usar a tool Read com o parametro `pages` (leitura visual). Ver a memoria
`drive-pastas-escritorio`.
