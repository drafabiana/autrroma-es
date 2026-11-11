# Onde salvar as pecas produzidas pela automacao

Toda peca produzida pelas automacoes deste repositorio e salva no Google Drive do
escritorio, dentro de:

```
G:\Meu Drive\PEÇAS AUTOMAÇÃO\
  {NOME DO CLIENTE EM MAIUSCULO}\
    {Nome do Cliente} - {Peca} - {DD-MM-YYYY}.docx
    _fontes\
      {Nome do Cliente} - {Peca} - {DD-MM-YYYY}.txt
```

## Regras

1. **A pasta `PEÇAS AUTOMAÇÃO` ja existe.** Nunca recriar, renomear nem mover.
2. **Uma subpasta por cliente**, com o nome do cliente em MAIUSCULO, igual ao padrao
   de pastas de cliente ja adotado pelo escritorio (ver [padroes-documentos.md](padroes-documentos.md)).
   Criar a subpasta na primeira peca daquele cliente; nas seguintes, reaproveitar.
3. **Se ja existir arquivo com o mesmo nome, NAO sobrescrever.** Avisar a Dra. Fabiana
   e aguardar decisao — uma peca pode ja ter sido revisada ou protocolada.
4. **Salvar tambem o texto-fonte** em `_fontes/`, com o mesmo nome e extensao `.txt`.
   E dele que o DOCX e regerado por `OPERACIONAL/agente_operacional/escritorio_format.py`;
   sem ele, qualquer ajuste posterior obriga a refazer a peca do zero. O prefixo `_`
   mantem a subpasta fora do caminho de quem so quer a peca.
5. **A peca vai no timbrado**, sempre, via `gerar_peca_escritorio()`. Nunca em folha branca.
6. **Isto nao autoriza mexer no resto do Drive.** A autorizacao permanente vale so para
   `PEÇAS AUTOMAÇÃO` e suas subpastas. Criar pasta ou arquivo em qualquer outro ponto do
   Drive continua dependendo de autorizacao explicita — ver [fluxo-operacional.md](fluxo-operacional.md).
7. **Salvar ali nao e protocolar.** Vale integralmente a regra de ouro do `CLAUDE.md`:
   a peca fica marcada "PRONTA PARA REVISAO DA DRA. FABIANA" e nenhuma automacao a
   envia para o processo.

## Convencao de nomes de peca

Usar o mesmo padrao das demais pecas do escritorio: nome do cliente, tipo da peca e
data, separados por ` - `. Sem acento e sem barra no nome do arquivo (o Drive
sincroniza melhor assim). Exemplos:

- `FULANO DE TAL - Requerimento Isencao IR - 03-09-2026.docx`
- `FULANO DE TAL - Peticao Inicial Isencao IR - 15-10-2026.docx`
