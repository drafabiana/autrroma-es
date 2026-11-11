# Base de Conhecimento - Alves Carneiro Advocacia e Consultoria Jurídica

Acervo de **tese juridica** do escritorio: o que foi destilado de cursos, livros,
apostilas, pareceres e material de estudo, num formato que a IA le rapido e a Dra.
Fabiana confere em um minuto.

## Regra de ouro desta pasta

**Material de curso serve de TESE, nunca de FORMATACAO.**

Apostila, modelo de peca de professor ou kit de curso entram aqui pelo *argumento*:
o dispositivo legal, a jurisprudencia, a estrutura da tese, a armadilha processual.
A formatacao da peca do escritorio e uma so e vem de
[`.claude/rules/padroes-documentos.md`](../.claude/rules/padroes-documentos.md) -
Segoe UI 11 pt, timbrado proprio, topicos em tabela azul. Nenhum material de terceiro
sobrepoe isso, por mais bonito que seja o modelo do professor.

Vale tambem a regra de ouro do `CLAUDE.md`: nada que sai daqui vai direto para o
processo. Tese de curso e ponto de partida para a peca, que segue para revisao da
Dra. Fabiana.

## Escopo — so as duas areas ativas

| Area | Pasta | Quem conduz |
|---|---|---|
| **Militar / Previdenciario Militar** | `MILITAR/` | Dra. Fabiana — area propria |
| **Previdenciario comum (INSS/RPPS)** | `PREVIDENCIARIO/` | **Dra. Kenia** — material a encaminhar |
| Processo civil, recursos, JEF, MS | `PROCESSUAL/` | transversal |

**Nao fichar** Trabalhista, TOI/energia, Familia, Civel, Imobiliario ou Empresarial —
areas encerradas (ver CLAUDE.md e `docs/MAPA_DRIVE.md`).

## Duas fontes de material

| Fonte | Script | O que traz |
|---|---|---|
| **Acervo proprio** — pecas, pareceres, acordaos e portarias das pastas tematicas do Drive | `python UTILS/extrair_acervo_teses.py` | o que o escritorio ja litigou; rende o campo "resultado" da ficha |
| **Cursos** — apostila, livro, palestra em `G:\Meu Drive\CURSOS\` | `python UTILS/indexar_cursos.py` | tese de terceiro, a verificar na fonte primaria |

Depois de extrair, destilar em ficha com a skill `/ficha-tese` e regenerar o indice
com `python UTILS/gerar_indice_teses.py`.

## Como esta organizado

```
BASE_CONHECIMENTO/
├── README.md              # este arquivo
├── INDICE.md              # catalogo de tudo que ja entrou
├── _MODELO_FICHA.md       # template para uma ficha nova
├── PREVIDENCIARIO/        # fichas de tese previdenciaria
├── MILITAR/               # fichas de tese militar
├── PROCESSUAL/            # fichas de processo civil, recursos, JEF, MS
└── _extraido/             # texto bruto dos originais (NAO versionado)
```

Os **arquivos originais** (PDF, DOCX, PPTX, video, audio) ficam no Google Drive, em
`G:\Meu Drive\CURSOS\`. Nunca sao copiados para o repositorio: sao material protegido
por direito autoral de terceiro, muitas vezes pesado, e o git nao e lugar para eles.
O que entra no repositorio e a **ficha** - o resumo autoral que o escritorio faz do
material, com o caminho de volta para o original.

## Como entra um material novo

1. Jogar o arquivo em `G:\Meu Drive\CURSOS\` (subpasta por curso, se quiser).
2. Rodar `python UTILS/indexar_cursos.py` - ele varre a pasta, extrai o texto que der
   para extrair em `_extraido/` e cria uma ficha-rascunho na area certa.
3. Pedir para a IA destilar: ela le o texto extraido e preenche a ficha (teses,
   dispositivos, jurisprudencia, armadilhas).
4. A Dra. Fabiana confere a ficha. So depois de conferida ela vale como base.

Detalhe do procedimento em
[`.claude/rules/base-conhecimento-cursos.md`](../.claude/rules/base-conhecimento-cursos.md).

## Como a ficha e usada

Os agentes juridicos (`agentes_claude/carneiro-previdenciario.md`,
`carneiro-militar.md`) consultam as fichas da sua area antes de montar a peca. A ficha
conferida entra como fundamentacao; a ficha ainda marcada `RASCUNHO` entra so como
pista a checar na fonte primaria.
