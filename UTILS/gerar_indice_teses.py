"""
Gera BASE_CONHECIMENTO/INDICE.md a partir das fichas existentes e do que esta
extraido em _extraido/ mas ainda nao virou ficha.

Uso:  python UTILS/gerar_indice_teses.py
"""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "BASE_CONHECIMENTO"
AREAS = ("MILITAR", "PREVIDENCIARIO", "PROCESSUAL")

# tema em _extraido -> area da ficha
AREA_DO_TEMA = {"militar": "MILITAR", "prev": "PREVIDENCIARIO"}


def frontmatter(p: Path) -> dict:
    txt = p.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---\n", txt, re.S)
    if not m:
        return {}
    dados: dict[str, str] = {}
    # Aceita chave no topo e chave indentada (ex.: `tipo:` dentro de `origem:`).
    for linha in m.group(1).splitlines():
        mm = re.match(r"^\s*(\w+):\s*(.*)$", linha)
        if mm and mm.group(2).strip():
            dados.setdefault(mm.group(1), mm.group(2).strip().strip('"'))
    return dados


def temas_extraidos() -> dict[str, int]:
    d = BASE / "_extraido"
    if not d.is_dir():
        return {}
    return {
        sub.name: len(list(sub.glob("*.txt")))
        for sub in sorted(d.iterdir())
        if sub.is_dir()
    }


def temas_ja_fichados() -> set[str]:
    """Temas citados no campo `extraido:` de alguma ficha."""
    usados: set[str] = set()
    for area in AREAS:
        for f in (BASE / area).glob("*.md"):
            ref = frontmatter(f).get("extraido", "")
            for t in re.findall(r"_extraido/([a-z0-9-]+)", ref):
                usados.add(t)
    return usados


def sem_texto() -> list[tuple[str, str]]:
    man = BASE / "_extraido" / "_manifesto.csv"
    if not man.is_file():
        return []
    fora = []
    with man.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["status"] != "ok":
                fora.append((Path(r["arquivo"]).name, r["status"]))
    return fora


def main() -> int:
    L: list[str] = []
    L.append("# Indice da Base de Conhecimento")
    L.append("")
    L.append("> Arquivo **gerado** por `UTILS/gerar_indice_teses.py` - nao editar a mao.")
    L.append("> O que se edita e a ficha de cada tese.")
    L.append("")
    L.append(f"Ultima geracao: {datetime.now():%d/%m/%Y %H:%M}")
    L.append("")
    L.append("**Escopo:** so **Militar** (area propria) e **Previdenciario** (da Dra. Kenia).")
    L.append("Areas encerradas nao entram - ver CLAUDE.md.")
    L.append("")
    L.append("**Status:** `RASCUNHO` = ficha escrita, ainda nao conferida pela Dra. Fabiana.")
    L.append("`CONFERIDA` = validada - **so esta vale como fundamentacao em peca**.")
    L.append("")

    total = 0
    for area in AREAS:
        fichas = sorted((BASE / area).glob("*.md"))
        L.append(f"## {area.title()}")
        L.append("")
        if not fichas:
            L.append("_(nenhuma ficha ainda)_")
            L.append("")
            continue
        L.append("| Ficha | Assunto | Origem | Status |")
        L.append("|---|---|---|---|")
        for f in fichas:
            fm = frontmatter(f)
            titulo = fm.get("titulo", f.stem)
            status = fm.get("status", "?")
            tipo = fm.get("tipo", "-")
            L.append(
                f"| [{f.stem}]({area}/{f.name}) | {titulo} | {tipo} | `{status}` |"
            )
            total += 1
        L.append("")

    # Material extraido que ainda nao virou ficha
    extraidos = temas_extraidos()
    fichados = temas_ja_fichados()
    pendentes = {t: n for t, n in extraidos.items() if t not in fichados}

    L.append("## Material extraido pendente de ficha")
    L.append("")
    if not pendentes:
        L.append("_(nada pendente)_")
    else:
        L.append("Texto ja extraido em `_extraido/`, aguardando destilacao em ficha")
        L.append("(ver a skill `/ficha-tese`). Ordenado por volume.")
        L.append("")
        L.append("| Tema | Arquivos | Area | Caminho |")
        L.append("|---|---|---|---|")
        for t, n in sorted(pendentes.items(), key=lambda kv: -kv[1]):
            area = AREA_DO_TEMA.get(t.split("-")[0], "?")
            L.append(f"| {t} | {n} | {area} | `_extraido/{t}/` |")
    L.append("")

    # Pendentes de leitura visual
    falhas = sem_texto()
    L.append("## Pendentes de leitura visual")
    L.append("")
    L.append("Arquivos do acervo que o extrator nao conseguiu ler - PDF digitalizado sem")
    L.append("camada de texto, arquivo corrompido ou protegido. Esta maquina **nao tem OCR**;")
    L.append("para ler, usar a tool Read com o parametro `pages`.")
    L.append("")
    if not falhas:
        L.append("_(nenhum)_")
    else:
        L.append(f"**Total: {len(falhas)}.** Lista completa em `_extraido/_manifesto.csv`.")
        L.append("")
        L.append("| Arquivo | Motivo |")
        L.append("|---|---|")
        for nome, motivo in falhas[:25]:
            L.append(f"| {nome} | {motivo} |")
        if len(falhas) > 25:
            L.append(f"| _... e mais {len(falhas) - 25}_ | ver o manifesto |")
    L.append("")

    (BASE / "INDICE.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"INDICE.md gerado: {total} fichas, {len(pendentes)} temas pendentes, "
          f"{len(falhas)} arquivos sem texto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
