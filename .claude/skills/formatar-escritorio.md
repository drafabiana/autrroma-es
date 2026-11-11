---
name: formatar-escritorio
description: Aplica formatacao fiel do escritorio (Segoe UI 11pt, recuo 2,5cm, entrelinhas min. 15pt, topicos em tabela azul, timbrado do escritorio) em texto bruto ou arquivo .docx existente. Sem chamar IA.
trigger: /formatar-escritorio
---

# Skill: Formatar Escritorio - aplica so a formatacao (sem IA)

## Quando usar

Quando ja existe um texto de peca redigido (manualmente ou por outra ferramenta) e
voce so quer aplicar a FORMATACAO oficial do escritorio + timbrado:

- Peca redigida em texto pela equipe e precisa do polish final
- Migrar peca de outra fonte para o padrao do escritorio
- Reformatar uma peca antiga
- Aplicar correcao de formatacao sem mexer no conteudo

Para gerar peca NOVA com IA, use `/peca-escritorio`.

## O que essa skill faz

1. Le texto bruto (.txt ou .docx convertido) com marcacao simples:
   - Linhas em branco separam paragrafos
   - Numeracao I., I.I., a), b) detecta titulos/subtitulos
   - Linha comecando com aspa (") vira citacao
   - `**texto**` -> negrito inline
   - `_texto_` -> italico inline
   - Marcadores markdown `#`, `##`, `###` sao limpos automaticamente
2. Renderiza no timbrado do escritorio com formatacao FIEL:
   - Margens 2.5 / 2.5 / 3 / 3 cm
   - Segoe UI 11pt (corpo)
   - Citacoes em 11pt, recuo esquerdo 4cm
   - Recuo 1a linha 2,5cm
   - Entrelinhas "Pelo menos" 15pt, sem espaco entre paragrafos
   - Topicos de secao viram tabela 1x1 de fundo azul claro (DBE5F1), texto negrito + italico
   - Nome da peca centralizado bold
   - Titulos de secao com travessao longo "–" (nao hifen)

## Como invocar

```python
import sys
sys.path.insert(0, 'OPERACIONAL/agente_operacional')
from peca_escritorio_engine import formatar_no_timbrado

# Le seu texto bruto (de onde quiser)
texto = open('minha_peca_bruta.txt', encoding='utf-8').read()

# Aplica formatacao + salva
out = formatar_no_timbrado(texto, 'CLIENTE - Peticao Inicial.docx')
print(f'Peca formatada: {out}')
```

Ou diretamente o formatador puro:

```python
import sys
sys.path.insert(0, 'OPERACIONAL/agente_operacional')
import escritorio_format as PF

PF.gerar_peca(texto, 'output.docx')
```

## Especificacoes aplicadas

| Item | Valor |
|---|---|
| Pagina | A4 (21 x 29.7 cm) |
| Margens | top 2.5 / bottom 2.5 / left 3 / right 3 cm |
| Fonte | Segoe UI |
| Corpo | 11 pt |
| Citacoes (jurisprudencia/sumula) | 11 pt |
| Espacamento linha | "Pelo menos" 15 pt |
| Recuo 1a linha (corpo + pedidos) | 2,5 cm |
| Recuo esquerdo citacoes | 4 cm |
| space_before / space_after | 0 |
| Alinhamento padrao | Justificado |

## Estrutura detectada automaticamente

- "EXCELENTISSIMO..." -> enderecamento (justify, bold, sem recuo)
- "RECLAMATORIA TRABALHISTA" / "CONTESTACAO" / "REPLICA" -> nome da peca (CENTER, bold)
- "I - ...", "II - ...", "EMENTA" -> topico: tabela 1x1 azul DBE5F1, bold + italico
- "a) ...", "b) ..." em meio de paragrafo -> subtitulo (justify, bold)
- "a) ...", "b) ..." na secao V/PEDIDOS -> pedido (justify, recuo 2,5cm)
- Linha comecando com aspa -> citacao (11pt italico, recuo esquerdo 4cm)

## Boas praticas relacionadas

- Obrigatorio gerar no timbrado do escritorio
- Recuo 1a linha 2,5cm
- Assinatura padrao: Dra. Fabiana Silva Alves Carneiro — OAB/RJ 188.762 — Rio de Janeiro/RJ
