#!/usr/bin/env python3
"""Regressie-eval voor verify_candidates.py: synthetische vault, vaste cases.
Draai na elke wijziging aan verify_candidates.py. Exit 1 bij een failure."""
import importlib.util
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("vc", HERE / "verify_candidates.py")
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)


def page(title, updated, sources, verified=None, tags="[concept]"):
    v = f"\nverified: {verified}" if verified else ""
    return f"---\ntitle: {title}\ntags: {tags}\nupdated: {updated}{v}\nsources: {sources}\n---\n\n# {title}\n"


def build(root: Path):
    for d in ("wiki/concepts", "wiki/entities", "wiki/sources", "raw/assets", "raw/books"):
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "raw/Bron A.md").write_text("a")
    (root / "raw/Bron, met komma.md").write_text("b")
    (root / "raw/books/Bron A.md").write_text("kopie")
    (root / "raw/assets/plaatje.md").write_text("geen bron")
    (root / "raw/Spec.pdf").write_text("pdf")
    c = root / "wiki/concepts"
    c.joinpath("hub-a.md").write_text(page("Hub A", "2026-11-01", '["Bron A.md", "Bron, met komma.md"]'))
    c.joinpath("hub-slug.md").write_text(page("Hub Slug", "2026-10-01", "[2026-01-01-spec]"))
    c.joinpath("hub-actueel.md").write_text(page("Hub Actueel", "2026-09-01", "[Spec.pdf]", verified="2026-09-02"))
    c.joinpath("hub-oud.md").write_text(page("Hub Oud", "2026-10-05", "[Spec.pdf]", verified="2026-09-02"))
    c.joinpath("hub-stub.md").write_text(page("Hub Stub", "2026-10-05", "[]", tags="[stub]"))
    c.joinpath("hub-weg.md").write_text(page("Hub Weg", "2026-10-05", "[Verdwenen.md, plaatje.md]"))
    s = root / "wiki/sources"
    s.joinpath("2026-01-01-spec.md").write_text(
        page("Spec", "2026-01-01", "[Spec.pdf]") + "\n[[hub-a|Hub A]] [[hub-a|A]] [[hub-slug|S]]\n")
    s.joinpath("2026-02-02-wees.md").write_text(page("Wees", "2026-02-02", "[]") + "\n[[hub-a|A]]\n")
    (root / "wiki/ingest-state.md").write_text(
        "| File | mtime | hash | Source page | Ingested |\n|---|---|---|---|---|\n"
        "| `Spec.pdf` | x | y | [[2026-01-01-spec\\|Spec]] | 2026-01-01 |\n")
    (root / "index.md").write_text("[[hub-a|Hub A]]\n")


def main():
    fails = 0
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        build(root)
        r = vc.scan(root, limit=50)
        sel = {Path(c["page"]).stem: c for c in r["selected"]}

        def check(name, ok):
            nonlocal fails
            print(("PASS " if ok else "FAIL ") + name)
            fails += 0 if ok else 1

        check("1 rawnaam lost op naar raw/-root, niet naar books-kopie",
              sel["hub-a"]["raw_files"][0] == "raw/Bron A.md")
        check("2 naam met komma tussen aanhalingstekens blijft heel",
              "raw/Bron, met komma.md" in sel["hub-a"]["raw_files"])
        check("3 bronpagina-slug lost op via ingest-state",
              sel["hub-slug"]["raw_files"] == ["raw/Spec.pdf"])
        check("4 actueel geverifieerd wordt overgeslagen",
              "hub-actueel" not in sel and r["hubs_verified_current"] == 1)
        check("5 gewijzigd na verificatie wordt opnieuw kandidaat", "hub-oud" in sel)
        check("6 stubs vallen buiten de selectie", "hub-stub" not in sel)
        check("7 onvindbare bron en asset worden gemeld als onopgelost",
              sorted(sel["hub-weg"]["unresolved_sources"]) == ["Verdwenen.md", "plaatje.md"])
        check("8 meeste inkomende links eerst (pagina telt één keer per bron)",
              r["selected"][0]["page"].endswith("hub-a.md") and sel["hub-a"]["inbound_links"] == 3)
        check("9 bronpagina zonder ingest-state-rij wordt gemeld",
              r["untraceable_source_pages"] == ["wiki/sources/2026-02-02-wees.md"])
        check("10 limit begrenst de selectie", len(vc.scan(root, limit=2)["selected"]) == 2)
    print(f"\n{10 - fails}/10 geslaagd")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
