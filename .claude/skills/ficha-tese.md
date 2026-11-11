---
name: ficha-tese
description: Destila uma tese juridica do acervo do escritorio em ficha padronizada na BASE_CONHECIMENTO - teses aproveitaveis, dispositivos, jurisprudencia com coluna de verificacao, armadilhas e resultado. Use ao alimentar o banco de teses ou ao preparar material para a Dra. Kenia.
trigger: /ficha-tese
---

# Skill: Ficha de Tese (Banco de Teses)

> Alimenta `BASE_CONHECIMENTO/MILITAR/`, `BASE_CONHECIMENTO/PREVIDENCIARIO/` e
> `BASE_CONHECIMENTO/PROCESSUAL/`. Template: `BASE_CONHECIMENTO/_MODELO_FICHA.md`.
> Regras: `BASE_CONHECIMENTO/README.md` e `.claude/rules/base-conhecimento-cursos.md`.

## Escopo — so as duas areas ativas

| Area | Pasta da ficha | Destino |
|---|---|---|
| **Militar / Previdenciario Militar** | `BASE_CONHECIMENTO/MILITAR/` | uso proprio, calibra `agentes_claude/carneiro-militar.md` |
| **Previdenciario comum (INSS/RPPS)** | `BASE_CONHECIMENTO/PREVIDENCIARIO/` | material para a **Dra. Kenia** — ver `/encaminhar-kenia` |
| Processo civil, recursos, JEF, MS | `BASE_CONHECIMENTO/PROCESSUAL/` | transversal as duas |

**Nao fichar** tese de Trabalhista, TOI/energia, Familia, Civel, Imobiliario ou
Empresarial — areas encerradas (CLAUDE.md).

## De onde vem o material

1. **Acervo proprio** — pecas do escritorio, ja extraidas em
   `BASE_CONHECIMENTO/_extraido/<tema>/` por `python UTILS/extrair_acervo_teses.py`.
   Temas correspondem as pastas do Drive (ver `docs/MAPA_DRIVE.md` 2.1 e 2.2):
   `militar-abate-teto`, `militar-acumulacao`, `militar-ctsm`,
   `militar-averbacao-ctm`, `militar-aposentadoria-especial`, `militar-fusex`,
   `militar-tea`, `militar-isencao-ir`, `militar-pareceres-md`, `militar-pmerj`,
   `prev-bpc-loas`, `prev-mecanicos-aeronaves`, `prev-piso-professores`, etc.
2. **Curso / apostila / livro** — original em `G:\Meu Drive\CURSOS\`, indexado por
   `python UTILS/indexar_cursos.py`.

## Regra de ouro

**Material de terceiro serve de TESE, nunca de FORMATACAO.** Apostila e modelo de
professor entram pelo *argumento* — dispositivo, jurisprudencia, estrutura da tese,
armadilha processual. A formatacao da peca e uma so, de
`.claude/rules/padroes-documentos.md` (Segoe UI 11pt, timbrado proprio, topicos em
tabela azul DBE5F1).

Ver a lista "Nao usar como referencia" em `padroes-documentos.md`: kits de terceiro,
material IBIJUS, timbrado de outros escritorios.

## Estrutura da ficha

Copiar `_MODELO_FICHA.md` e preencher. Os campos que mais importam:

### Frontmatter
```yaml
titulo:   # como consta no original
area:     MILITAR | PREVIDENCIARIO | PROCESSUAL
origem:
  tipo:   peca-propria | curso | livro | apostila | palestra | parecer | modelo
  autor:
  data:   MM/YYYY do material
original: G:\Meu Drive\...           # caminho de volta
extraido: BASE_CONHECIMENTO/_extraido/<tema>/<arquivo>.txt
status:   RASCUNHO | CONFERIDA
```

### Corpo

**Do que trata** — duas ou tres linhas: qual problema juridico resolve e em que tipo
de caso do escritorio serve.

**Teses aproveitaveis** — uma entrada por tese, sempre nos quatro campos:
- **Quando cabe:** a situacao de fato que autoriza
- **Fundamento:** artigos, sumulas, temas repetitivos
- **Como se argumenta:** a linha de raciocinio em duas ou tres frases
- **Contra-argumento tipico da Uniao / do INSS / do TCU:** o que a outra parte responde

**Dispositivos citados** — tabela dispositivo × o que estabelece × onde usar.

**Jurisprudencia citada** — tabela tribunal/tema × ementa resumida × **Verificado?**

> ⚠️ A coluna **Verificado?** e obrigatoria. Material envelhece: **tese superada e o
> erro mais caro que se comete copiando apostila.** Nada entra em peca com `nao`
> nesta coluna. Conferir na fonte oficial (STF, STJ, TRF2, TCU).

**Armadilhas e prazos** — o que derruba o pedido: documento que falta, decadencia,
exigencia de previo requerimento administrativo, competencia.

**Resultado** (quando a ficha vem de peca propria com desfecho arquivado):
`procedente` · `improcedente` · `em andamento` · `tese vencida`.
Ficha de tese vencida **permanece** no banco, marcada — evita repetir o erro
(ver a memoria `tese-vencida-sumula-111`).

**Observacoes da Dra. Fabiana** — preenchido na conferencia: o que se aplica a
realidade do RJ / da JFRJ, o que ela faz diferente.

## Status

| Status | O que significa | Pode entrar em peca? |
|---|---|---|
| `RASCUNHO` | ficha criada, nao conferida | **nao** — so como pista a checar na fonte primaria |
| `CONFERIDA` | lida e validada pela Dra. Fabiana | sim, como fundamentacao |

## Fluxo

```
1. rodar UTILS/extrair_acervo_teses.py (acervo) ou UTILS/indexar_cursos.py (cursos)
2. ler o texto extraido do tema
3. escrever a ficha a partir de _MODELO_FICHA.md
4. verificar CADA precedente na fonte oficial -> coluna Verificado?
5. salvar em BASE_CONHECIMENTO/<AREA>/<slug-da-tese>.md com status RASCUNHO
6. regenerar o INDICE.md
7. Dra. Fabiana confere -> status CONFERIDA
```

`INDICE.md` e **gerado** — nao editar a mao.

## Quem consome a ficha

Os agentes `agentes_claude/carneiro-militar.md` e `carneiro-previdenciario.md`
consultam as fichas da area antes de montar a peca. Ficha `CONFERIDA` entra como
fundamentacao; `RASCUNHO` entra so como pista.

> Ficha nao e peca. Nada que sai daqui vai direto para o processo — vale a regra de
> ouro do CLAUDE.md.
