#!/usr/bin/env python3
"""Regression eval for regen-quick-indexes.py.

Builds a small synthetic vault in a temp dir and checks the guarantees the
skills rely on: one writer, no write without a change, `created:` kept,
`--check` exit codes, `date_published` fallback, the "Analyses" section.

    python3 scripts/regen_quick_indexes_eval.py      # exit 1 on a failure
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "regen-quick-indexes.py"

PAGES = {
    "sources/2026-01-01-dv-boek.md": (
        "title: DV Boek\ntype: source\ntags: [data-vault]\ndate: 2026-01-01\nauthor: Linstedt",
        "Een boek over hubs. Tweede zin."),
    "sources/2026-02-02-ar-bron.md": (
        "title: AR Bron\ntype: source\ntags: [claude]\ndate_published: 2026-02-02\nauthor: onbekend",
        "Bron uit autoresearch."),
    "sources/2026-03-03-leeg.md": (
        'title: Lege Datum\ntype: source\ntags: [zzz]\ndate: ""',
        "Valt in Overig."),
    "concepts/hub.md": (
        "title: Hub\naliases: [Hub, Business Hub]\ntype: concept\ntags: [data-vault]",
        "Een hub bevat business keys."),
    "analysis/research-x.md": (
        "title: \"Research: X\"\ntype: analysis\ntags: [research]\ncreated: 2026-04-04",
        "X werkt zo. Meer tekst."),
}


def make_vault(root: Path) -> None:
    for rel, (fm, summary) in PAGES.items():
        p = root / "wiki" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"---\n{fm}\n---\n\n# T\n\n## Summary\n{summary}\n", encoding="utf-8")


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(SCRIPT), str(root), *args],
                          capture_output=True, text=True)


def main() -> int:
    results: list[tuple[str, bool]] = []

    def check(name: str, ok: bool) -> None:
        results.append((name, ok))

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_vault(root)
        src = root / "wiki" / "sources-index.md"
        cpt = root / "wiki" / "concepts-index.md"

        r = run(root, "--check")
        check("check op lege vault meldt drift (exit 1)", r.returncode == 1)
        check("check schrijft niets", not src.exists() and not cpt.exists())

        r = run(root)
        check("eerste run slaagt", r.returncode == 0)
        text = src.read_text(encoding="utf-8")
        check("bron met date + author", "[[2026-01-01-dv-boek|DV Boek]] (2026-01-01, Linstedt) — Een boek over hubs." in text)
        check("date_published als terugval, 'onbekend' als auteur blijft", "(2026-02-02, onbekend)" in text)
        check("lege datum geeft geen (\"\")", '("")' not in text and "[[2026-03-03-leeg|Lege Datum]] — Valt in Overig." in text)
        check("sectie Analyses met created-datum", "## Analyses (1)" in text
              and "[[research-x|Research: X]] (2026-04-04) — X werkt zo." in text)
        check("concept zonder datum/auteur", "- [[hub|Hub]] — Een hub bevat business keys." in cpt.read_text(encoding="utf-8"))
        check("alias-map", "**Business Hub** → `[[hub|Business Hub]]`" in cpt.read_text(encoding="utf-8"))

        # created: blijft; geen write zonder wijziging.
        src.write_text(re.sub(r"^created: .*$", "created: 2020-01-01", text, count=1,
                              flags=re.MULTILINE), encoding="utf-8")
        cpt_before = cpt.read_text(encoding="utf-8")
        mtime_before = cpt.stat().st_mtime_ns
        r = run(root)
        check("tweede run zonder wijziging raakt concepts-index niet",
              cpt.stat().st_mtime_ns == mtime_before and cpt.read_text(encoding="utf-8") == cpt_before)
        check("created: blijft behouden", "created: 2020-01-01" in src.read_text(encoding="utf-8"))
        r = run(root, "--check")
        check("check na regen: exit 0", r.returncode == 0)

        # Handwerk wordt als drift gezien en door de regen overschreven.
        src.write_text(src.read_text(encoding="utf-8") + "\n- [[hand|Hand]] — handregel\n", encoding="utf-8")
        r = run(root, "--check")
        check("handregel = drift (exit 1)", r.returncode == 1 and "DRIFT sources-index.md" in r.stdout)
        run(root)
        check("regen verwijdert handregel", "handregel" not in src.read_text(encoding="utf-8"))
        check("created: blijft ook na echte wijziging", "created: 2020-01-01" in src.read_text(encoding="utf-8"))

        # Geen wiki/ -> exit 1.
        r = subprocess.run([sys.executable, "-I", str(SCRIPT), str(root / "nope")],
                           capture_output=True, text=True)
        check("geen wiki/ -> exit 1", r.returncode == 1)

    failed = [n for n, ok in results if not ok]
    for name, ok in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    print(f"\n{len(results) - len(failed)}/{len(results)} geslaagd")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
