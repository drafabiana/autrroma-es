# Base de Conhecimento - material de curso e estudo

Como entra, onde fica e ate onde vale o material de curso, apostila, livro e palestra
que a Dra. Fabiana acumula.

## Onde fica o que

| O que | Onde | Versionado? |
|---|---|---|
| Arquivo original (PDF, DOCX, PPTX, video, audio) | `G:\Meu Drive\CURSOS\` | nao - fica so no Drive |
| Texto extraido do original | `BASE_CONHECIMENTO/_extraido/` | nao (`.gitignore`) |
| Ficha destilada (o que o escritorio aproveita) | `BASE_CONHECIMENTO/<AREA>/` | **sim** |
| Catalogo geral | `BASE_CONHECIMENTO/INDICE.md` | sim |

O original **nunca** e copiado para o repositorio: e material protegido de terceiro e
o git nao e lugar para arquivo pesado. O que se versiona e a ficha - texto autoral do
escritorio, com o caminho de volta para o original no Drive.

## Regra de ouro: tese sim, formatacao nao

Material de terceiro entra pelo **argumento**, nunca pelo layout. A formatacao de peca
do escritorio e uma so - Segoe UI 11 pt, timbrado proprio, topicos em tabela azul
`DBE5F1` - e esta em [padroes-documentos.md](padroes-documentos.md). Modelo de peca de
professor, kit de curso e apostila com minuta pronta **nao** alteram esse padrao.

E a lista "Nao usar como referencia" de `padroes-documentos.md` continua valendo
integralmente: aquele material (kit numerado, modelos da Amanda Medeiros Kravchychyn,
`MATERIAL PARA ISENCAO DE IR` da IBIJUS) serve de tese e so.

## Procedimento

1. **Depositar** o arquivo em `G:\Meu Drive\CURSOS\`, de preferencia numa subpasta por
   curso (`CURSOS\IBIJUS - Isencao de IR\`). A subpasta vira a `origem` da ficha.
2. **Indexar:** `python UTILS/indexar_cursos.py`
   - varre a pasta, extrai o texto para `_extraido/`,
   - cria uma ficha-rascunho na area certa a partir de `_MODELO_FICHA.md`,
   - atualiza `INDICE.md`,
   - lista o que nao deu para extrair (PDF digitalizado, video, audio).
   Rodar com `--dry-run` primeiro mostra o que seria feito sem escrever nada.
3. **Destilar:** a IA le o texto em `_extraido/` e preenche a ficha - teses,
   dispositivos, jurisprudencia, armadilhas. Nada de resumo generico: a ficha tem que
   responder "quando cabe esta tese e com que fundamento".
4. **Conferir:** a Dra. Fabiana le a ficha e a marca `status: CONFERIDA`, com data.

## Jurisprudencia de apostila e sempre suspeita

Material de curso envelhece. Tema repetitivo muda, sumula e cancelada, entendimento
vira. Toda jurisprudencia copiada de curso entra na ficha com `Verificado? nao` e **so
vai para peca depois de conferida na fonte oficial** (STJ, STF, TRF2, DJe). Copiar
precedente superado de apostila e o erro mais caro que se comete com este acervo.

O mesmo vale para dispositivo legal: conferir a redacao vigente, sobretudo em
previdenciario pos-EC 103/2019.

## O que a IA faz e o que nao faz

**Faz:** indexar, extrair, destilar, preencher ficha, apontar conflito entre o que diz
a apostila e o que o escritorio ja praticava.

**Nao faz:**
- marcar ficha como `CONFERIDA` - isso e ato da Dra. Fabiana;
- usar ficha `RASCUNHO` como fundamentacao de peca (serve de pista, a checar na fonte);
- criar ou mexer em pasta do Drive fora de `CURSOS` e `PEÇAS AUTOMAÇÃO`
  (ver [fluxo-operacional.md](fluxo-operacional.md));
- copiar original de curso para dentro do repositorio.

## Limitacao da maquina: sem OCR

Nao ha OCR instalado (sem tesseract/pytesseract/pdf2image), e `pdftotext` nao existe.
PDF digitalizado sem camada de texto e slide em imagem caem na secao "Pendentes de
leitura visual" do `INDICE.md` e precisam ser lidos pela IA com a tool Read e o
parametro `pages`. Video e audio de aula ficam registrados no indice, sem transcricao.
