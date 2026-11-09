#!/usr/bin/env python3
"""Tekstversies van de PDF's in raw/ voor de qmd-collectie `raw-pdf`.

Schrijft per PDF in raw/ (alleen het hoogste niveau, net als de ingest-detectie)
een markdownbestand met de pdftotext-uitvoer naar een map BUITEN de vault
(standaard ~/.cache/myrag/raw-pdf-text), zodat Obsidian, iCloud en raw/ er niets
van merken. Idempotent: een PDF wordt alleen opnieuw omgezet als hij nieuwer is
dan zijn tekstversie. Tekstversies van PDF's die niet meer in raw/ staan,
worden verwijderd. Een PDF zonder tekstlaag (scan) levert een bestand met
alleen de kop en wordt gemeld.

Gebruik (vanuit de vault-root):
  python3 raw_pdf_text.py [vault] [--out DIR] [--plain]
Daarna: qmd update && qmd embed
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault", nargs="?", default=".")
    ap.add_argument("--out", default=str(Path.home() / ".cache" / "myrag" / "raw-pdf-text"))
    ap.add_argument("--plain", action="store_true")
    a = ap.parse_args()
    raw = Path(a.vault).resolve() / "raw"
    if not raw.is_dir():
        print(f"geen raw/ in {raw.parent}", file=sys.stderr)
        return 2
    exe = shutil.which("pdftotext") or "/opt/homebrew/bin/pdftotext"
    if not Path(exe).exists():
        print("pdftotext niet gevonden (brew install poppler)", file=sys.stderr)
        return 2
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(p for p in raw.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")
    wanted = {p.stem + ".md": p for p in pdfs}
    made, kept, empty, failed = [], 0, [], []
    for name, pdf in wanted.items():
        target = out / name
        if target.exists() and target.stat().st_mtime >= pdf.stat().st_mtime:
            kept += 1
            continue
        r = subprocess.run([exe, "-layout", str(pdf), "-"], capture_output=True, text=True)
        if r.returncode != 0:
            failed.append(pdf.name)
            continue
        body = r.stdout.strip()
        target.write_text(f"# {pdf.stem}\n\nBron: raw/{pdf.name}\n\n{body}\n", encoding="utf-8")
        made.append(pdf.name)
        if len(body.split()) < 20:
            empty.append(pdf.name)
    removed = [f.name for f in out.glob("*.md") if f.name not in wanted]
    for name in removed:
        (out / name).unlink()
    res = {"out": str(out), "pdfs": len(pdfs), "converted": len(made), "unchanged": kept,
           "removed": removed, "no_text_layer": empty, "failed": failed}
    if a.plain:
        for k, v in res.items():
            print(f"{k}: {v if not isinstance(v, list) else (len(v), v[:10])}")
    else:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
