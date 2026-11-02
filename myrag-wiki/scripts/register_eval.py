#!/usr/bin/env python3
"""Regression eval for register.py.

Builds a synthetic vault in a temp dir and checks every guarantee the skills
and the Registerblok rely on. Run after each change to register.py:

    python3 scripts/register_eval.py      # exit 1 on a failure
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "register.py"

INDEX = """---
title: Wiki Index
type: index
updated: 2026-01-01
last_change: lange tekst die nooit mag veranderen | met pipe en [[link|Link]]
---

# Wiki Index

## Concepts

**AI**
- [[prompting|Prompting]], [[agents|Agents]] (komma-lijst)

**Data**
- [[hub|Hub]] — business keys (2 sources)

## Entities

- [[jan|Jan]] — persoon

**Auteurs**
- [[piet|Piet]] — auteur

## Analysis
- [[oud|Oud]] — oude analyse

---

## Stats
- **Total wiki pages**: 1
- oude notitie
"""

STATE = """---
title: Ingest State
type: meta
updated: 2026-01-01 (vrije tekst)
---

# Ingest State

## Multi-page references

| Raw | Primary (`sources/`) | Derivatives | Notes |
|---|---|---|---|
| `bestaand.md` | [[s-a]] | [[hub]] (concept) | Notitie die moet blijven. |

---

## State table

| File | mtime | hash | Source page | Ingested |
|---|---|---|---|---|
| `Alpha.md` | {alpha_m} | {alpha_h} | [[s-a\\|Bron A]] | 2026-01-01 |
| `kapot.md` | 2026-01-01T00:00:00 | 0123456789ab | [[s-k|Kapot]] | 2026-01-01 |
| `weg.md` | 2026-01-01T00:00:00 | 0123456789ab | [[s-w\\|Weg]] | 2026-01-01 |
"""

LOG = """# Log

## [2026-01-01] ingest | Eerste

Body.
"""


def page(root: Path, rel: str, title: str, typ: str, sources: str = "[]", tags: str = "[]") -> None:
    p = root / "wiki" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\ntitle: {title}\ntype: {typ}\ntags: {tags}\nsources: {sources}\n---\n\n## Summary\nTekst.\n",
                 encoding="utf-8")


def make_vault(root: Path) -> None:
    (root / "raw" / "assets").mkdir(parents=True)
    for name, body in [("Alpha.md", "alpha"), ("kapot.md", "kapot"), ("Nieuw.md", "nieuw"),
                       ("beta.pdf", "pdf"), ("plaatje.png", "x")]:
        (root / "raw" / name).write_text(body, encoding="utf-8")
    (root / "raw" / "assets" / "a.md").write_text("asset", encoding="utf-8")
    page(root, "sources/s-a.md", "Bron A", "source")
    page(root, "sources/s-n.md", "Bron Nieuw", "source")
    page(root, "sources/s-k.md", "Kapot", "source")
    page(root, "concepts/hub.md", "Hub", "concept", "[s-a, s-n]")
    page(root, "concepts/nieuw-concept.md", "Nieuw Concept", "concept", "[s-n]", "[stub, x]")
    page(root, "entities/klaas.md", "Klaas", "entity")
    page(root, "analysis/nieuwe-analyse.md", "Nieuwe Analyse", "analysis", "[s-a]")
    page(root, "concepts/pipe.md", "Slecht | titel", "concept")
    alpha = root / "raw" / "Alpha.md"
    import datetime as dt
    m = dt.datetime.fromtimestamp(alpha.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%S")
    h = hashlib.sha256(alpha.read_bytes()).hexdigest()[:12]
    (root / "wiki" / "ingest-state.md").write_text(STATE.format(alpha_m=m, alpha_h=h), encoding="utf-8")
    (root / "index.md").write_text(INDEX, encoding="utf-8")
    (root / "log.md").write_text(LOG, encoding="utf-8")


ENV: dict[str, str] = {}   # set in main(): isolated XDG_CACHE_HOME for the lock dir


def run(root: Path, *args: str) -> tuple[int, dict]:
    r = subprocess.run([sys.executable, "-I", str(SCRIPT), "--vault", str(root), *args],
                       capture_output=True, text=True, env=ENV)
    try:
        return r.returncode, json.loads(r.stdout)
    except json.JSONDecodeError:
        return r.returncode, {"raw": r.stdout + r.stderr}


def main() -> int:
    results: list[tuple[str, bool]] = []

    def check(name: str, ok: bool) -> None:
        results.append((name, bool(ok)))

    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cache:
        ENV.update(os.environ, XDG_CACHE_HOME=cache)
        root = Path(tmp)
        make_vault(root)
        log = root / "log.md"
        idx = root / "index.md"
        state = root / "wiki" / "ingest-state.md"

        # ---------------- log ----------------
        before = log.read_text(encoding="utf-8")
        code, out = run(root, "log", "--type", "ingest", "--title", "Bron | met pipe",
                        "--body", "Regel [[s-n|Bron Nieuw]].", "--date", "2026-11-02")
        after = log.read_text(encoding="utf-8")
        check("log: appended", code == 0 and out.get("status") == "appended")
        check("log: oude inhoud is exact het begin (append-only)", after.startswith(before))
        check("log: kop + lege regel + body onderaan",
              after.endswith("\n## [2026-11-02] ingest | Bron | met pipe\n\nRegel [[s-n|Bron Nieuw]].\n"))
        check("log: één lege regel tussen entries", "Body.\n\n## [2026-11-02]" in after)
        code, out = run(root, "log", "--type", "ingest", "--title", "Bron | met pipe",
                        "--body", "Regel [[s-n|Bron Nieuw]].", "--date", "2026-11-02")
        check("log: herhaling = duplicate, geen write",
              out.get("status") == "duplicate" and log.read_text(encoding="utf-8") == after)
        code, out = run(root, "log", "--type", "setup", "--title", "x")
        check("log: onbekend type -> exit 1", code == 1)
        code, out = run(root, "log", "--type", "lint", "--title", "a\nb")
        check("log: titel met newline -> exit 1", code == 1)
        code, out = run(root, "log", "--type", "lint", "--title", "x", "--date", "2-11-2026")
        check("log: ongeldige datum -> exit 1", code == 1)
        code, out = run(root, "log", "--type", "fix", "--title", "Zonder body", "--dry-run")
        check("log: dry-run schrijft niets", out.get("status") == "dry-run"
              and log.read_text(encoding="utf-8") == after)

        # Parallel writers: the lock serialises them; nothing is lost.
        n_before = log.read_text(encoding="utf-8").count("\n## [")
        procs = [subprocess.Popen([sys.executable, "-I", str(SCRIPT), "--vault", str(root), "log",
                                   "--type", "ingest", "--title", f"Parallel {i}", "--date", "2026-11-02"],
                                  stdout=subprocess.DEVNULL, env=ENV) for i in range(8)]
        codes = [p.wait() for p in procs]
        txt = log.read_text(encoding="utf-8")
        check("log: 8 parallelle aanroepen, 8 entries, oude inhoud intact",
              all(c == 0 for c in codes) and txt.count("\n## [") == n_before + 8 and txt.startswith(after))

        # Lock: per-user dir with mode 0700; a symlink at the lock path is refused, not followed.
        import stat as _stat
        lock_dir = Path(cache) / "myrag"
        check("lock: map ~/.cache/myrag met mode 0700",
              lock_dir.is_dir() and _stat.S_IMODE(lock_dir.stat().st_mode) == 0o700)
        locks = list(lock_dir.glob("register-*.lock"))
        check("lock: bestand met mode 0600", len(locks) == 1
              and _stat.S_IMODE(locks[0].stat().st_mode) == 0o600)
        victim = Path(cache) / "victim.txt"
        victim.write_text("niet afkappen", encoding="utf-8")
        locks[0].unlink()
        locks[0].symlink_to(victim)
        log_before = log.read_text(encoding="utf-8")
        code, out = run(root, "log", "--type", "fix", "--title", "Via symlink")
        check("lock: symlink op lockpad -> exit 3, doel en log ongemoeid",
              code == 3 and victim.read_text(encoding="utf-8") == "niet afkappen"
              and log.read_text(encoding="utf-8") == log_before)
        locks[0].unlink()

        # ---------------- ingest-state check ----------------
        code, out = run(root, "ingest-state", "check")
        check("check: kapotte rij gevonden (exit 1)", code == 1 and any(
            p["file"] == "kapot.md" for p in out.get("problems", [])))
        code, out = run(root, "ingest-state", "set", "--raw", "raw/kapot.md")
        check("set op kapotte rij weigert", code == 1 and "check --fix" in out.get("error", ""))
        code, out = run(root, "ingest-state", "check", "--fix")
        txt = state.read_text(encoding="utf-8")
        check("check --fix herstelt de escape", code == 0 and "| [[s-k\\|Kapot]] |" in txt)
        check("check --fix laat frontmatter staan", "updated: 2026-01-01 (vrije tekst)" in txt)

        # ---------------- ingest-state status ----------------
        code, out = run(root, "ingest-state", "status", "--list-unchanged")
        check("status: New (alleen .md/.pdf, geen assets)", sorted(out.get("new", [])) == ["Nieuw.md", "beta.pdf"])
        check("status: Unchanged via mtime", "Alpha.md" in out.get("unchanged", []))
        check("status: Deleted", out.get("deleted") == ["weg.md"])
        alpha = root / "raw" / "Alpha.md"
        os.utime(alpha, (1_600_000_000, 1_600_000_000))
        code, out = run(root, "ingest-state", "status", "--list-unchanged")
        check("status: alleen mtime anders = Unchanged (De Morgan)", "Alpha.md" in out.get("unchanged", []))
        alpha.write_text("alpha gewijzigd", encoding="utf-8")
        os.utime(alpha, (1_600_000_000, 1_600_000_000))
        code, out = run(root, "ingest-state", "status")
        check("status: mtime én hash anders = Modified", "Alpha.md" in out.get("modified", []))

        # ---------------- ingest-state set ----------------
        code, out = run(root, "ingest-state", "set", "--raw", "raw/Nieuw.md",
                        "--page", "wiki/concepts/hub.md", "--page", "wiki/sources/s-n.md", "--date", "2026-11-02")
        txt = state.read_text(encoding="utf-8")
        check("set: nieuwe rij", code == 0 and out.get("status") == "added")
        check("set: sources-pagina eerst, escape, datum",
              "| [[s-n\\|Bron Nieuw]], [[hub\\|Hub]] | 2026-11-02 |" in txt)
        rows = [l.split("|")[1].strip().strip("`") for l in txt.split("## State table")[1].splitlines()
                if l.startswith("| `")]
        check("set: alfabetisch ingevoegd", rows == sorted(rows, key=str.lower))
        check("set: frontmatter updated: kale datum", "\nupdated: 2026-11-02\n" in txt)
        check("set: multi-page rij toegevoegd, Notes leeg",
              "| `Nieuw.md` | [[s-n\\|Bron Nieuw]] | [[hub\\|Hub]] (concept) |  |" in txt)
        check("set: bestaande Notes blijven", "Notitie die moet blijven." in txt)
        code, out = run(root, "ingest-state", "set", "--raw", "raw/Alpha.md", "--date", "2026-11-03")
        txt2 = state.read_text(encoding="utf-8")
        h = hashlib.sha256(alpha.read_bytes()).hexdigest()[:12]
        check("set zonder --page ververst mtime/hash/datum", f"| {h} | [[s-a\\|Bron A]] | 2026-11-03 |" in txt2)
        code, out = run(root, "ingest-state", "set", "--raw", "raw/Alpha.md", "--page", "wiki/concepts/hub.md",
                        "--date", "2026-11-03")
        txt3 = state.read_text(encoding="utf-8")
        check("set: extra pagina achter komma", "[[s-a\\|Bron A]], [[hub\\|Hub]] | 2026-11-03 |" in txt3)
        check("set: bestaande multi-page rij uitgebreid, Notes intact",
              "| `bestaand.md` |" in txt3 and txt3.count("`Alpha.md`") == 2)
        code, _ = run(root, "ingest-state", "set", "--raw", "raw/Alpha.md", "--page", "wiki/concepts/hub.md",
                      "--date", "2026-11-03")
        check("set: herhaling verandert niets", state.read_text(encoding="utf-8") == txt3)
        code, out = run(root, "ingest-state", "set", "--raw", "raw/bestaatniet.md", "--page", "wiki/sources/s-a.md")
        check("set: raw ontbreekt -> exit 2", code == 2)
        code, out = run(root, "ingest-state", "set", "--raw", "raw/assets/a.md", "--page", "wiki/sources/s-a.md")
        check("set: raw/assets geweigerd", code == 1)
        code, out = run(root, "ingest-state", "set", "--raw", "raw/plaatje.png", "--page", "wiki/sources/s-a.md")
        check("set: alleen .md/.pdf", code == 1)
        code, out = run(root, "ingest-state", "set", "--raw", "raw/beta.pdf")
        check("set: nieuwe rij zonder --page geweigerd", code == 1)
        code, out = run(root, "ingest-state", "set", "--raw", "raw/beta.pdf", "--page", "wiki/concepts/pipe.md")
        check("set: titel met | geweigerd", code == 1)
        code, out = run(root, "ingest-state", "check")
        check("check na alle sets: schoon", code == 0 and out.get("status") == "ok")

        # ---------------- index ----------------
        fm_before = idx.read_text(encoding="utf-8").split("\n---\n", 1)[0]
        code, out = run(root, "index", "sections")
        check("index sections", [s["heading"] for s in out.get("sections", [])] ==
              ["Concepts", "Entities", "Analysis", "Stats"])
        code, out = run(root, "index", "add", "--page", "wiki/analysis/nieuwe-analyse.md",
                        "--section", "Analysis", "--summary", "Een analyse")
        txt = idx.read_text(encoding="utf-8")
        check("index add: regel met (N sources) aan einde van sectie",
              out.get("status") == "added" and
              "- [[oud|Oud]] — oude analyse\n- [[nieuwe-analyse|Nieuwe Analyse]] — Een analyse (1 sources)\n" in txt)
        check("index add: frontmatter alleen updated: anders",
              txt.split("\n---\n", 1)[0] == fm_before.replace("updated: 2026-01-01", f"updated: {__import__('datetime').date.today()}"))
        code, out = run(root, "index", "add", "--page", "wiki/concepts/nieuw-concept.md", "--section", "Concepts",
                        "--summary", "x")
        check("index add: sectie met alleen groepen vraagt --group (exit 2)", code == 2 and "AI" in out.get("candidates", []))
        code, out = run(root, "index", "add", "--page", "wiki/concepts/nieuw-concept.md", "--section", "Concepts",
                        "--group", "Data", "--summary", "Nieuw")
        txt = idx.read_text(encoding="utf-8")
        check("index add: in groep, na laatste regel van de groep",
              "- [[hub|Hub]] — business keys (2 sources)\n- [[nieuw-concept|Nieuw Concept]] — Nieuw (1 sources)\n\n## Entities" in txt)
        code, out = run(root, "index", "add", "--page", "wiki/entities/klaas.md", "--section", "Entities",
                        "--summary", "persoon")
        txt = idx.read_text(encoding="utf-8")
        check("index add: zonder groep naar het ongegroepeerde deel, niet in de laatste groep",
              "- [[jan|Jan]] — persoon\n- [[klaas|Klaas]] — persoon\n\n**Auteurs**" in txt)
        code, out = run(root, "index", "add", "--page", "wiki/entities/klaas.md", "--section", "Entities",
                        "--summary", "persoon")
        check("index add: herhaling = unchanged", out.get("status") == "unchanged")
        code, out = run(root, "index", "add", "--page", "wiki/entities/klaas.md", "--section", "Entities",
                        "--summary", "andere zin")
        check("index add: eigen regel ververst", out.get("status") == "refreshed"
              and "- [[klaas|Klaas]] — andere zin" in idx.read_text(encoding="utf-8"))
        before = idx.read_text(encoding="utf-8")
        code, out = run(root, "index", "add", "--page", "wiki/concepts/hub.md", "--section", "Concepts",
                        "--group", "AI", "--summary", "business keys")
        check("index add: bestaande eigen regel in andere groep blijft waar hij staat",
              out.get("status") == "unchanged" and idx.read_text(encoding="utf-8") == before)
        code, out = run(root, "index", "add", "--page", "wiki/sources/s-a.md", "--section", "Concepts",
                        "--group", "AI", "--summary", "x")
        check("index add: bronpagina overgeslagen", out.get("status") == "skipped")
        page(root, "concepts/prompting.md", "Prompting", "concept")
        code, out = run(root, "index", "add", "--page", "wiki/concepts/prompting.md", "--section", "Concepts",
                        "--group", "AI", "--summary", "x")
        check("index add: slug in komma-lijst -> already_listed, lijst intact",
              out.get("status") == "already_listed"
              and "- [[prompting|Prompting]], [[agents|Agents]] (komma-lijst)" in idx.read_text(encoding="utf-8"))
        code, out = run(root, "index", "add", "--page", "wiki/concepts/hub.md", "--section", "Bestaatniet",
                        "--summary", "x")
        check("index add: sectie onbekend maar slug al eigen regel -> geen fout", code == 0)
        code, out = run(root, "index", "add", "--page", "wiki/entities/geen.md", "--section", "Entities",
                        "--summary", "x")
        check("index add: pagina ontbreekt -> exit 2", code == 2)
        code, out = run(root, "index", "stats")
        txt = idx.read_text(encoding="utf-8")
        check("index stats: blok vervangen, oude notitie weg",
              "oude notitie" not in txt and "- **Raw sources tracked**: 4" in txt and "- **Open stubs**: 1" in txt)
        check("index stats: last_change onaangeroerd",
              "last_change: lange tekst die nooit mag veranderen | met pipe en [[link|Link]]" in txt)

        # ---------------- ingest-state: raw-namen met '|' en in NFD ----------------
        # Eigen vault, zodat de New/Deleted-verwachtingen hierboven niet verschuiven.
        with tempfile.TemporaryDirectory() as tmp2:
            root = Path(tmp2)
            make_vault(root)
            state = root / "wiki" / "ingest-state.md"
            nfd = "Café | menu.md"                       # zo levert macOS hem aan
            nfc = "Café | menu.md"
            for name in ("Oud | pijp.md", "Nieuw | pijp.md", nfd):
                (root / "raw" / name).write_text(name, encoding="utf-8")
            # Rij zoals versie 0.12.0 hem schreef: kale '|' in de File-cel.
            txt = state.read_text(encoding="utf-8").replace(
                "| `weg.md` |",
                "| `Oud | pijp.md` | 2026-01-01T00:00:00 | 0123456789ab | [[s-a\\|Bron A]] | 2026-01-01 |\n| `weg.md` |")
            state.write_text(txt, encoding="utf-8")

            code, out = run(root, "ingest-state", "status", "--list-unchanged")
            check("pipe: oude rij met kale '|' is geen New of Deleted",
                  "Oud | pijp.md" not in out.get("new", []) and out.get("deleted") == ["weg.md"])
            code, out = run(root, "ingest-state", "check")
            check("pipe: check meldt kale '|' in bestandsnaam", code == 1 and any(
                "bestandsnaam" in p["problem"] for p in out.get("problems", [])))
            code, out = run(root, "ingest-state", "check", "--fix")
            txt = state.read_text(encoding="utf-8")
            check("pipe: check --fix escapet de File-cel (en herstelt kapot.md)",
                  code == 0 and "| `Oud \\| pijp.md` | 2026-01-01T00:00:00 |" in txt
                  and "| [[s-k\\|Kapot]] |" in txt)

            code, out = run(root, "ingest-state", "set", "--raw", "raw/Nieuw | pijp.md",
                            "--page", "wiki/sources/s-n.md")
            check("pipe: set schrijft '\\|' in de File-cel",
                  code == 0 and "| `Nieuw \\| pijp.md` |" in state.read_text(encoding="utf-8"))
            code, out = run(root, "ingest-state", "set", "--raw", "raw/Nieuw | pijp.md",
                            "--page", "wiki/sources/s-n.md")
            check("pipe: tweede set vindt de rij terug", out.get("status") == "updated"
                  and state.read_text(encoding="utf-8").count("Nieuw \\| pijp.md") == 1)

            code, out = run(root, "ingest-state", "set", "--raw", f"raw/{nfc}", "--page", "wiki/sources/s-a.md")
            txt = state.read_text(encoding="utf-8")
            check("nfd: set met NFC-naam vindt het NFD-bestand en schrijft NFC",
                  code == 0 and "| `Café \\| menu.md` |" in txt and "Café" not in txt)
            code, out = run(root, "ingest-state", "set", "--raw", f"raw/{nfd}", "--page", "wiki/sources/s-a.md")
            check("nfd: set met NFD-naam werkt dezelfde rij bij", out.get("status") == "updated")
            code, out = run(root, "ingest-state", "status", "--list-unchanged")
            check("pipe + nfd: niets onterecht New, alleen weg.md Deleted",
                  sorted(out.get("new", [])) == ["Nieuw.md", "beta.pdf"] and out.get("deleted") == ["weg.md"]
                  and {nfc, "Nieuw | pijp.md"} <= set(out.get("unchanged", []))
                  and "Oud | pijp.md" in out.get("modified", []))   # rij heeft een verzonnen mtime/hash
            code, out = run(root, "ingest-state", "check")
            check("pipe + nfd: check schoon", code == 0 and out.get("status") == "ok")

    failed = [n for n, ok in results if not ok]
    for name, ok in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    print(f"\n{len(results) - len(failed)}/{len(results)} geslaagd")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
