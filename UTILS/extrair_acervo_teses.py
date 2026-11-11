"""
Extrai o texto do acervo de pecas e material de tese das DUAS areas ativas do
escritorio (Militar e Previdenciario), para alimentar BASE_CONHECIMENTO/.

Escopo (ver CLAUDE.md e docs/MAPA_DRIVE.md secao 2):
  - Militar         -> area propria da Dra. Fabiana
  - Previdenciario  -> area da Dra. Kenia (captamos e encaminhamos)
As areas encerradas (Trabalhista, TOI, Familia, Civel, Imobiliario, Empresarial)
sao ignoradas de proposito.

Saida: BASE_CONHECIMENTO/_extraido/<tema>/<arquivo>.txt  +  _manifesto.csv

Uso:  python UTILS/extrair_acervo_teses.py [--limite N] [--workers N]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

DRIVE = Path(r"G:\Meu Drive")
REPO = Path(__file__).resolve().parent.parent
SAIDA = REPO / "BASE_CONHECIMENTO" / "_extraido"

MAX_PAGINAS_PDF = 20
MIN_CARACTERES = 400  # abaixo disso e digitalizacao sem camada de texto

# --- Pastas tematicas: o proprio nome da pasta ja classifica a tese -----------

TEMAS_MILITAR = {
    "ABATE TETO": "militar-abate-teto",
    "CASOS DE ACUMULAÇÃO": "militar-acumulacao",
    "CTSM": "militar-ctsm",
    "AVERBAÇÃO CTM": "militar-averbacao-ctm",
    "APOSENTADORIA ESPECIAL": "militar-aposentadoria-especial",
    "FUNDO DE SAUDE - FORÇAS ARMADAS": "militar-fusex",
    "FUNDO SAUDE PM": "militar-fundo-saude-pm",
    "MILITAR - TEA - AUTISMO": "militar-tea",
    "IR - ACÕES E CÁLCULOS": "militar-isencao-ir",
    "PARECERES MD": "militar-pareceres-md",
    "PM": "militar-pmerj",
    "GLAUCIA PDC": "militar-pdc",
    "PROVA DE VIDA - EBOOK": "militar-prova-de-vida",
}

# Acoes de familia INSTRUMENTAIS a demanda militar. Nao sao acervo de "Familia"
# (area encerrada): as Forcas Armadas exigem a sentenca dessas duas acoes para
# habilitar a pensao militar, entao elas sao conduzidas aqui. Ficam espalhadas nas
# pastas de cliente, nao em pasta tematica - por isso a deteccao e por nome.
PADRAO_INSTRUMENTAL = (
    # \b antes de "curador" para nao casar com "proCURADOR"
    (re.compile(r"interdi|curatel|\bcurador", re.IGNORECASE), "militar-interdicao-curatela"),
    (re.compile(r"uni[aã]o\s*est[aá]vel", re.IGNORECASE), "militar-uniao-estavel"),
)

TEMAS_PREVIDENCIARIO = {
    "BASE DE CONHECIMENTO - BPC": "prev-bpc-loas",
    "ISENÇÃO IR": "prev-isencao-ir",
    "TEA": "prev-tea",
    "MECANICOS AERONAVES": "prev-mecanicos-aeronaves",  # -> enviar para a Dra. Kenia
    "AULA PISO PROFESSORES": "prev-piso-professores",
    "PISO NACION~L - TARSIS": "prev-piso-professores",
    "FERIAS PROFESSOR": "prev-ferias-professor",
    "PESQUISA APOSENTADORIA INVALIDEZ": "prev-aposentadoria-invalidez",
    "RPPS - AMANDA": "prev-rpps",
    "FGTS": "prev-fgts",
    "MAPAS MENTAIS": "prev-mapas-mentais",
}

RAIZ_MILITAR = DRIVE / "CLIENTES MILITARES" / "CLIENTES MILITARES"
RAIZ_PREV = DRIVE / "CLIENTES PREVIDENCIARIOS"
RAIZ_LIVIA = DRIVE / "LIVIA - AUXILIAR JURIDICO"

# Espelhos de backup e lixo - nunca varrer (ver memoria drive-pastas-escritorio)
EXCLUIR_TRECHO = (
    "- copia",
    "nova pasta",
    "outros computadores",
    "sony_32gr",
    "unidade de usb",
    "_files",
    "backup de ",
)

# Nomes que indicam peca autoral do escritorio
PADRAO_PECA = re.compile(
    r"inicial|peticao|petição|contestacao|contestação|replica|réplica|recurso|"
    r"apelacao|apelação|agravo|embargos|mandado|impetra|memorial|manifesta|"
    r"requerimento|defesa|razoes|razões|contrarraz|parecer|alegac|alegaç|"
    r"emenda|habilita|cumprimento|execucao|execução|tutela|liminar|"
    # acoes instrumentais a demanda militar
    r"interdi|curatel|curador|uniao estavel|união estável|idoneidade",
    re.IGNORECASE,
)


def sem_acento(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def slug(s: str, limite: int = 90) -> str:
    s = sem_acento(s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:limite] or "sem-nome"


def destino_unico(pasta: Path, base: str, origem: Path) -> Path:
    """Evita que dois arquivos de mesmo nome em pastas diferentes se sobrescrevam."""
    alvo = pasta / f"{base}.txt"
    if not alvo.exists():
        return alvo
    # Ja existe: se for o MESMO arquivo de origem, reescreve; senao, sufixa.
    try:
        if alvo.read_text(encoding="utf-8").startswith(f"# ORIGEM: {origem}"):
            return alvo
    except OSError:
        pass
    marca = hashlib.sha1(str(origem).encode("utf-8")).hexdigest()[:6]
    return pasta / f"{base}-{marca}.txt"


def excluido(caminho: Path) -> bool:
    if caminho.name.startswith("~$"):  # temporario aberto do Word
        return True
    alvo = sem_acento(str(caminho)).lower()
    return any(t in alvo for t in EXCLUIR_TRECHO)


def tema_de(caminho: Path) -> str | None:
    """Classifica pelo nome da pasta tematica; senao, pela area da raiz."""
    partes = caminho.parts
    for pasta, tema in {**TEMAS_MILITAR, **TEMAS_PREVIDENCIARIO}.items():
        if pasta in partes:
            return tema
    # Acao instrumental (interdicao/curatela, uniao estavel) dentro do acervo militar
    if "CLIENTES MILITARES" in partes:
        alvo = f"{caminho.parent.name} {caminho.stem}"
        for padrao, tema in PADRAO_INSTRUMENTAL:
            if padrao.search(alvo):
                return tema
    texto = sem_acento(str(caminho)).upper()
    if "CLIENTES MILITARES" in texto or "/MILITAR/" in texto.replace("\\", "/"):
        return "militar-pecas"
    if "PREVIDENCIARI" in texto:
        return "prev-pecas"
    return None


def coletar() -> list[tuple[Path, str]]:
    """Devolve [(arquivo, tema)] do que interessa extrair."""
    achados: dict[Path, str] = {}

    # 1. Pastas tematicas inteiras (PDF de jurisprudencia, parecer, portaria)
    for raiz, temas in ((RAIZ_MILITAR, TEMAS_MILITAR), (RAIZ_PREV, TEMAS_PREVIDENCIARIO)):
        for pasta, tema in temas.items():
            base = raiz / pasta
            if not base.is_dir():
                continue
            for f in base.rglob("*"):
                if f.is_file() and f.suffix.lower() in (".pdf", ".docx", ".doc") and not excluido(f):
                    achados[f] = tema

    # 2. Pecas autorais nas pastas de cliente das duas areas
    for raiz in (RAIZ_MILITAR, RAIZ_PREV, RAIZ_LIVIA / "MILITAR", RAIZ_LIVIA / "PREVIDENCIÁRIO"):
        if not raiz.is_dir():
            continue
        for f in raiz.rglob("*"):
            if not f.is_file() or excluido(f):
                continue
            if f.suffix.lower() not in (".docx", ".doc"):
                continue
            if not PADRAO_PECA.search(f.stem):
                continue
            achados.setdefault(f, tema_de(f) or "militar-pecas")

    # 3. Acoes instrumentais (interdicao/curatela, uniao estavel) no acervo militar.
    #    Aqui tambem entram PDF, porque a sentenca e a certidao - que sao o que a
    #    Forca exige - quase sempre chegam digitalizadas.
    if RAIZ_MILITAR.is_dir():
        for f in RAIZ_MILITAR.rglob("*"):
            if not f.is_file() or excluido(f):
                continue
            if f.suffix.lower() not in (".pdf", ".docx", ".doc"):
                continue
            alvo = f"{f.parent.name} {f.stem}"
            for padrao, tema in PADRAO_INSTRUMENTAL:
                if padrao.search(alvo):
                    achados[f] = tema
                    break

    return sorted(achados.items(), key=lambda kv: str(kv[0]))


# --- Extratores ---------------------------------------------------------------


def texto_docx(f: Path) -> str:
    import docx

    d = docx.Document(str(f))
    partes = [p.text for p in d.paragraphs]
    for t in d.tables:
        for linha in t.rows:
            partes.append(" | ".join(c.text.strip() for c in linha.cells))
    return "\n".join(partes)


def texto_pdf(f: Path) -> str:
    import pdfplumber

    partes = []
    with pdfplumber.open(str(f)) as pdf:
        for pagina in pdf.pages[:MAX_PAGINAS_PDF]:
            partes.append(pagina.extract_text() or "")
    return "\n".join(partes)


def extrair(item: tuple[Path, str]) -> dict:
    f, tema = item
    reg = {
        "arquivo": str(f),
        "tema": tema,
        "extraido": "",
        "caracteres": 0,
        "status": "",
    }
    try:
        if f.suffix.lower() == ".docx":
            txt = texto_docx(f)
        elif f.suffix.lower() == ".pdf":
            txt = texto_pdf(f)
        else:  # .doc -> segunda passada, com Word COM
            reg["status"] = "adiado-doc"
            return reg
    except Exception as e:  # arquivo corrompido, protegido, etc.
        reg["status"] = f"erro: {type(e).__name__}"
        return reg

    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    reg["caracteres"] = len(txt)
    if len(txt) < MIN_CARACTERES:
        reg["status"] = "sem-texto (digitalizado?)"
        return reg

    pasta = SAIDA / tema
    pasta.mkdir(parents=True, exist_ok=True)
    destino = destino_unico(pasta, slug(f.stem), f)
    cabecalho = f"# ORIGEM: {f}\n# TEMA: {tema}\n\n"
    destino.write_text(cabecalho + txt, encoding="utf-8")
    reg["extraido"] = str(destino.relative_to(REPO))
    reg["status"] = "ok"
    return reg


def extrair_docs_antigos(pendentes: list[tuple[Path, str]]) -> list[dict]:
    """.doc e .rtf so abrem via Word COM, e COM nao e thread-safe: serial."""
    if not pendentes:
        return []
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    registros = []
    try:
        for f, tema in pendentes:
            reg = {"arquivo": str(f), "tema": tema, "extraido": "", "caracteres": 0, "status": ""}
            doc = None
            try:
                doc = word.Documents.Open(
                    str(f), ReadOnly=True, AddToRecentFiles=False, Visible=False
                )
                txt = doc.Content.Text
            except Exception as e:
                reg["status"] = f"erro: {type(e).__name__}"
                registros.append(reg)
                continue
            finally:
                if doc is not None:
                    try:
                        doc.Close(False)
                    except Exception:
                        pass

            txt = re.sub(r"\r", "\n", txt)
            txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
            reg["caracteres"] = len(txt)
            if len(txt) < MIN_CARACTERES:
                reg["status"] = "sem-texto"
            else:
                pasta = SAIDA / tema
                pasta.mkdir(parents=True, exist_ok=True)
                destino = destino_unico(pasta, slug(f.stem), f)
                destino.write_text(f"# ORIGEM: {f}\n# TEMA: {tema}\n\n" + txt, encoding="utf-8")
                reg["extraido"] = str(destino.relative_to(REPO))
                reg["status"] = "ok"
            registros.append(reg)
    finally:
        try:
            word.Quit()
        except Exception:
            pass
        pythoncom.CoUninitialize()
    return registros


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=0, help="extrair so os N primeiros")
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()

    if not DRIVE.is_dir():
        print(f"ERRO: {DRIVE} nao esta montado.", file=sys.stderr)
        return 1

    t0 = time.time()
    print("Coletando arquivos em escopo (Militar + Previdenciario)...", flush=True)
    itens = coletar()
    if args.limite:
        itens = itens[: args.limite]
    print(f"{len(itens)} arquivos candidatos.", flush=True)

    SAIDA.mkdir(parents=True, exist_ok=True)
    registros: list[dict] = []
    adiados: list[tuple[Path, str]] = []

    # O gargalo e o download sob demanda do Drive, nao a CPU -> vale paralelizar.
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futuros = {pool.submit(extrair, it): it for it in itens}
        for i, fut in enumerate(as_completed(futuros), 1):
            reg = fut.result()
            if reg["status"] == "adiado-doc":
                adiados.append(futuros[fut])
            else:
                registros.append(reg)
            if i % 200 == 0:
                print(f"  {i}/{len(itens)}  ({time.time() - t0:.0f}s)", flush=True)

    if adiados:
        print(f"Abrindo {len(adiados)} arquivos .doc antigos via Word COM...", flush=True)
        registros.extend(extrair_docs_antigos(adiados))

    manifesto = SAIDA / "_manifesto.csv"
    with manifesto.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["arquivo", "tema", "extraido", "caracteres", "status"])
        w.writeheader()
        w.writerows(sorted(registros, key=lambda r: (r["tema"], r["arquivo"])))

    ok = [r for r in registros if r["status"] == "ok"]
    por_tema: dict[str, int] = {}
    for r in ok:
        por_tema[r["tema"]] = por_tema.get(r["tema"], 0) + 1

    print(f"\nExtraidos {len(ok)} de {len(registros)} em {time.time() - t0:.0f}s")
    for tema, n in sorted(por_tema.items(), key=lambda kv: -kv[1]):
        print(f"  {n:4d}  {tema}")
    falhas = len(registros) - len(ok)
    if falhas:
        print(f"\n{falhas} sem texto ou com erro - ver {manifesto}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
