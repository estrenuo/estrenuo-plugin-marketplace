#!/usr/bin/env python3
"""Regenerate wiki/sources-index.md and wiki/concepts-index.md from frontmatter + ## Summary.

Run from the wiki vault root (where wiki/ lives):
    python3 "$CLAUDE_PLUGIN_ROOT/scripts/regen-quick-indexes.py"

Or pass an explicit vault path as the first argument:
    python3 regen-quick-indexes.py /path/to/vault

Check for drift without writing (exit 1 when a regen would change a file):
    python3 regen-quick-indexes.py --check

Reads:
- wiki/concepts/*.md
- wiki/sources/*.md, wiki/recipes/*.md, wiki/travel/*.md
- wiki/analysis/*.md

Writes (overwrites, but only when the content changed):
- wiki/sources-index.md   — sources grouped by thematic cluster (tag-priority match),
                            plus an "Analyses" section for wiki/analysis/
- wiki/concepts-index.md  — concepts alphabetical + alias-to-canonical map

This script is the only writer of both files. Never patch them by hand: the next
run overwrites hand edits. `created:` is kept from the existing file; `updated:`
changes only when the body changed, so an unchanged wiki gives no file write.

Cluster mapping is defined in CLUSTERS below. First match wins. To add a new cluster
or expand an existing one, edit the keyword set. Re-run after changes.

The format per row is: `- [[slug|Title]] (date, author) — first sentence of ## Summary`
truncated to ~160 chars.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path


def _resolve_repo_root(arg: str | None) -> Path:
    """Resolve vault root from the argument, else cwd. wiki/ must exist beneath it."""
    candidate = Path(arg).resolve() if arg else Path.cwd().resolve()
    if not (candidate / "wiki").is_dir():
        sys.stderr.write(
            f"error: no wiki/ directory found under {candidate}.\n"
            "Run from the vault root, or pass the vault path as the first arg.\n"
        )
        sys.exit(1)
    return candidate


# Set in main(); module-level so the regen functions keep their simple shape.
REPO_ROOT: Path = Path.cwd()
WIKI: Path = REPO_ROOT / "wiki"

# Cluster mapping for sources. Priority order — first match wins.
# Keys = display name in the index. Values = set of tag keywords (lowercase).
CLUSTERS: list[tuple[str, set[str]]] = [
    ("Claude Use Cases (Anthropic-template-bibliotheek)", {"claude-use-case"}),
    ("Data Vault — kern, patronen, virtualisatie", {
        "data-vault", "data-vault-2", "hub", "satellite", "link", "driving-key",
        "hash-key", "virtualisatie", "automatisering",
        "data-warehouse-automatisering", "dwa", "willibald", "hook",
    }),
    ("Bitemporal & Temporal Modeling", {
        "bitemporal", "temporal", "temporeel", "tijd", "scd", "causal-leakers",
        "timestamps",
    }),
    ("Data Architectuur — Mesh, Lakehouse, Medallion", {
        "data-mesh", "lakehouse", "medallion", "fabric", "delta-architectuur",
        "data-lake", "modern-data-architecture", "data-warehouse", "dwh",
        "saas", "reverse-etl", "product-architectuur", "aif", "inmon",
    }),
    ("Data Modellering — concepten & methoden", {
        "data-modeling", "data-modellering", "fco-im", "elm", "anchor-modeling",
        "graph-normal-form", "gnf", "normalisatie", "6nf", "graph",
        "conceptueel", "logisch", "fysiek", "rdm", "erm",
        "gather-requirements", "information-product-canvas", "data-requirements",
        "requirements", "intake", "events", "states", "source-of-truth",
        "filosofie", "boek-aanbeveling", "abstract-model",
    }),
    ("Data Governance, Quality & Contracts", {
        "data-quality", "data-kwaliteit", "data-contracts", "data-governance",
        "shift-left", "metadata", "metamodel", "metrics", "pii",
        "master-data-management", "bronkwaliteit", "fix-at-source",
        "bron-verbetering", "completeness", "consistency",
    }),
    ("AI Tools & Prompt Engineering", {
        "ai-tools", "prompt-engineering", "claude", "chatgpt", "claude-skills",
        "ai-personas", "claude-use-cases", "ai-fluency", "ai-agents",
        "anthropic", "rag", "llm", "embedding-models", "machine-learning",
    }),
    ("Knowledge Management & Wiki", {
        "wiki", "kennisbeheer", "documentatie", "obsidian", "alfred",
        "alfred-workflow", "structuur", "adr", "storytelling",
    }),
    ("Software Engineering & Tooling", {
        "git", "code-review", "software-engineering", "agile",
        "sql", "dbt", "snowflake", "azure", "databricks", "iceberg",
        "streamlit", "pythonista", "google-analytics", "wordpress",
        "data-engineering", "functioneel-programmeren", "idempotent", "psa",
        "computer-use", "automation", "tooling",
    }),
    ("Recepten & Koken", {
        "recept", "koken", "indiaas", "indonesisch", "turks", "cooking",
    }),
    ("Reizen", {
        "reizen", "reis", "camper", "italie", "spanje", "bosnie", "eifel",
        "travel",
    }),
    ("Zakelijk & Financieel", {
        "accountant", "accounting", "fusie", "financieel", "finance", "dga",
        "holding", "jaarrekening", "payroll", "zzp", "esforzado", "estrenuo",
    }),
    ("Persoonlijk & Levensplanning", {
        "overlijden", "pensioen", "erfenis", "erfeniscontact", "digitale-erfenis",
        "fitness", "gezondheid", "health", "persoonlijke-ontwikkeling", "personal",
        "noodplan", "apple", "ios",
    }),
    ("Enterprise Architecture & Strategie", {
        "enterprise-architectuur", "archimate", "sparx-ea", "strategie",
        "strategy", "it-strategie", "it-strategy", "business-strategie",
        "taxonomie", "ontologie", "data-team",
    }),
    ("Cloud & Distributed Systems", {
        "cloud", "open-world-assumption", "monaden", "distributed-systems",
    }),
    ("Carrière & Arbeidsmarkt", {
        "carrière", "arbeidsmarkt", "cv", "sollicitatie", "positionering",
    }),
    ("Boeken & Naslag", {
        "boek", "boeken",
    }),
    ("Werk & Opdrachtdossiers", {
        "werk", "technologie", "onderzoek",
    }),
]

SUMMARY_MAX_CHARS = 160


def parse_frontmatter(text: str) -> str:
    m = re.match(r"---\n(.*?)\n---", text, re.DOTALL)
    return m.group(1) if m else ""


def get_field(fm: str, key: str) -> str:
    m = re.search(rf"^{re.escape(key)}\s*:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip() if m else ""


def parse_list(s: str) -> list[str]:
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    return [x.strip().strip('"').strip("'") for x in s.split(",") if x.strip()]


def first_summary_sentence(text: str, max_chars: int = SUMMARY_MAX_CHARS) -> str:
    """Return the first sentence of the ## Summary section, truncated."""
    body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
    m = re.search(r"^##\s+Summary\s*\n+(.+?)(?=\n##|\Z)", body, re.MULTILINE | re.DOTALL)
    chunk = m.group(1) if m else body
    chunk = chunk.strip()
    if not chunk:
        return ""
    para = chunk.split("\n\n")[0].strip()
    para = re.sub(r"\s+", " ", para)
    # Strip wikilink piping so the index stays readable
    para = re.sub(r"\[\[([^\|\]]+)\|([^\]]+)\]\]", r"\2", para)
    para = re.sub(r"\[\[([^\]]+)\]\]", r"\1", para)
    sentences = re.split(r"(?<=[\.\!\?])\s+", para)
    out = sentences[0] if sentences else para
    if len(out) > max_chars:
        out = out[:max_chars].rsplit(" ", 1)[0] + "…"
    return out


def _clean_date(v: str) -> str:
    v = v.strip().strip('"').strip("'")
    return "" if v.lower() in ("", "onbekend", "unknown", "null", "none") else v


def page_info(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    return {
        "slug": path.stem,
        "title": get_field(fm, "title").strip('"').strip("'"),
        "tags": parse_list(get_field(fm, "tags")),
        "author": get_field(fm, "author"),
        # `date` first; autoresearch writes `date_published` instead.
        "date": _clean_date(get_field(fm, "date") or get_field(fm, "date_published")),
        "created": _clean_date(get_field(fm, "created")),
        "summary": first_summary_sentence(text),
    }


# Fallback-keywords (2026-09-04): worden pas geraadpleegd als geen enkel cluster
# hierboven matcht. Reden: `claude-code` en `agentic-os` stonden nergens en zulke
# pagina's vielen via het catch-all `technologie` in "Werk & Opdrachtdossiers".
# Bewust NIET in de primaire sets, want AI Tools staat vóór Knowledge Management
# en Software Engineering; daar toevoegen verplaatste 10 pagina's die daar terecht
# stonden (Obsidian/memory-pagina's, website-builds). Het fallback-pad raakt alleen
# pagina's die anders in Werk of Overig zouden landen. Cluster-namen moeten
# letterlijk overeenkomen met een naam in CLUSTERS.
FALLBACK_CLUSTERS: list[tuple[str, set[str]]] = [
    ("AI Tools & Prompt Engineering", {"claude-code", "agentic-os", "claude-mem", "memory-systems"}),
    ("Software Engineering & Tooling", {"docker", "self-hosting", "synology", "nas"}),
]

_CATCH_ALL = {"technologie", "onderzoek"}


def cluster_for(tags: list[str]) -> str:
    tag_set = {t.lower() for t in tags}
    for name, keywords in CLUSTERS:
        if tag_set & keywords & (keywords - _CATCH_ALL if name == CLUSTERS[-1][0] else keywords):
            return name
    for name, keywords in FALLBACK_CLUSTERS:
        if tag_set & keywords:
            return name
    for name, keywords in CLUSTERS:
        if tag_set & keywords:
            return name
    return "Overig"


CREATED = "@@CREATED@@"
UPDATED = "@@UPDATED@@"


def build_sources_index() -> tuple[str, int, dict[str, int], int]:
    sources = []
    for subdir in ("sources", "recipes", "travel"):
        d = WIKI / subdir
        if not d.exists():
            continue
        for p in sorted(d.glob("*.md")):
            info = page_info(p)
            info["subdir"] = subdir
            info["cluster"] = cluster_for(info["tags"])
            sources.append(info)

    by_cluster: dict[str, list[dict]] = {}
    for s in sources:
        by_cluster.setdefault(s["cluster"], []).append(s)
    for k in by_cluster:
        by_cluster[k].sort(key=lambda x: (x["date"] or "0000", x["title"]), reverse=True)

    cluster_order = [name for name, _ in CLUSTERS] + ["Overig"]

    analyses = []
    d = WIKI / "analysis"
    if d.exists():
        analyses = [page_info(p) for p in sorted(d.glob("*.md"))]
    analyses.sort(key=lambda x: (x["date"] or x["created"] or "0000", x["title"]), reverse=True)

    lines = [
        "---",
        "title: Sources Index — Quick Reference",
        "type: meta",
        f"created: {CREATED}",
        f"updated: {UPDATED}",
        "---",
        "",
        "# Sources Index — Quick Reference",
        "",
        "One-liner per bron, gegroepeerd per thematisch cluster (auto-afgeleid uit `tags:` in de frontmatter), binnen cluster gesorteerd op datum (nieuwst eerst). Analysepagina's uit `wiki/analysis/` staan onderaan in een eigen sectie.",
        "",
        "**Doel:** zonder elke source-pagina te openen kunnen scannen wat erin staat. Bij query-workflow eerst hier zoeken, dan de geselecteerde 3–5 pagina's volledig lezen.",
        "",
        "**Onderhoud:** gegenereerd door `${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py` (myrag-wiki plugin). Niet met de hand bewerken: de volgende run overschrijft handwerk. Wijzig de frontmatter of `## Summary` van de pagina en draai het script.",
        "",
        "**Cluster-mapping:** gebaseerd op tag-prioriteit (eerste match wint). Een bron kan in werkelijkheid meerdere clusters raken; de single-cluster-toewijzing is een navigatie-hulp, geen waarheidsclaim.",
        "",
        "---",
        "",
    ]
    for cluster in cluster_order:
        if cluster not in by_cluster:
            continue
        items = by_cluster[cluster]
        lines.append(f"## {cluster} ({len(items)})")
        lines.append("")
        for s in items:
            bits = []
            if s["date"]:
                bits.append(s["date"])
            if s["author"]:
                bits.append(s["author"][:60])
            meta = f" ({', '.join(bits)})" if bits else ""
            summary = s["summary"] or "*(geen samenvatting)*"
            lines.append(f"- [[{s['slug']}|{s['title']}]]{meta} — {summary}")
        lines.append("")

    if analyses:
        lines.append(f"## Analyses ({len(analyses)})")
        lines.append("")
        for a in analyses:
            when = a["date"] or a["created"]
            meta = f" ({when})" if when else ""
            summary = a["summary"] or "*(geen samenvatting)*"
            lines.append(f"- [[{a['slug']}|{a['title']}]]{meta} — {summary}")
        lines.append("")

    counts = {c: len(by_cluster[c]) for c in cluster_order if c in by_cluster}
    return "\n".join(lines), len(sources), counts, len(analyses)


def build_concepts_index() -> tuple[str, int, int]:
    concepts = []
    for p in sorted((WIKI / "concepts").glob("*.md")):
        concepts.append(page_info(p))
    concepts.sort(key=lambda x: x["title"].lower())

    lines = [
        "---",
        "title: Concepts Index — Quick Reference",
        "type: meta",
        f"created: {CREATED}",
        f"updated: {UPDATED}",
        "---",
        "",
        "# Concepts Index — Quick Reference",
        "",
        "One-liner per concept-pagina, alfabetisch op titel. Aan het einde een aliases-mapping om correcte piped wikilinks te schrijven.",
        "",
        "**Doel:** snel zien welke concepten bestaan voor cross-referentie en wikilink-resolutie.",
        "",
        "**Onderhoud:** gegenereerd door `${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py` (myrag-wiki plugin). Niet met de hand bewerken: de volgende run overschrijft handwerk.",
        "",
        "---",
        "",
        f"## Concepts ({len(concepts)})",
        "",
    ]
    for c in concepts:
        summary = c["summary"] or "*(geen samenvatting)*"
        lines.append(f"- [[{c['slug']}|{c['title']}]] — {summary}")

    lines.extend([
        "",
        "---",
        "",
        "## Alias → canonical filename",
        "",
        "Helpt bij correcte piped wikilinks (`[[kebab-filename|Display Text]]`). Alleen aliases die afwijken van de filename.",
        "",
    ])

    alias_pairs: list[tuple[str, str]] = []
    for c in concepts:
        p = WIKI / "concepts" / f"{c['slug']}.md"
        fm = parse_frontmatter(p.read_text(encoding="utf-8"))
        for a in parse_list(get_field(fm, "aliases")):
            normalized = (
                a.lower()
                .replace(" ", "-")
                .replace("&", "and")
                .replace("(", "")
                .replace(")", "")
            )
            if normalized != c["slug"]:
                alias_pairs.append((a, c["slug"]))
    alias_pairs.sort(key=lambda x: x[0].lower())
    for alias, slug in alias_pairs:
        lines.append(f"- **{alias}** → `[[{slug}|{alias}]]`")

    return "\n".join(lines), len(concepts), len(alias_pairs)


_DATE_LINE = re.compile(r"^(created|updated):.*$", re.MULTILINE)


def _strip_dates(text: str) -> str:
    """Body for comparison: the created/updated lines do not count as content."""
    return _DATE_LINE.sub(r"\1:", text, count=2)


def write_index(path: Path, template: str, check: bool) -> bool:
    """Write `template` to `path` when the content changed. Returns True on change.

    `created:` is kept from the existing file. `updated:` becomes today only when
    the content changed; otherwise the file is not touched at all.
    """
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    old_fm = parse_frontmatter(old)
    created = get_field(old_fm, "created") or _today()
    probe = template.replace(CREATED, created).replace(UPDATED, "")
    if old and _strip_dates(probe) == _strip_dates(old):
        return False
    new = template.replace(CREATED, created).replace(UPDATED, _today())
    if check:
        diff = list(difflib.unified_diff(
            old.splitlines(), new.splitlines(),
            fromfile=f"{path.name} (huidig)", tofile=f"{path.name} (na regen)",
            lineterm="", n=0,
        ))
        body = [l for l in diff if l[:1] in "+-" and not l.startswith(("+++", "---"))
                and not re.match(r"^[+-](created|updated):", l)]
        print(f"DRIFT {path.name}: {len(body)} regels verschillen")
        for l in body[:20]:
            print(f"  {l[:200]}")
        if len(body) > 20:
            print(f"  … en nog {len(body) - 20}")
        return True
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(new, encoding="utf-8")
    tmp.replace(path)
    return True


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate wiki/sources-index.md and wiki/concepts-index.md.")
    parser.add_argument("vault", nargs="?", help="vault root (default: current directory)")
    parser.add_argument("--check", action="store_true",
                        help="write nothing; exit 1 when a regen would change a file")
    args = parser.parse_args(argv)

    global REPO_ROOT, WIKI
    REPO_ROOT = _resolve_repo_root(args.vault)
    WIKI = REPO_ROOT / "wiki"

    src_text, src_count, cluster_counts, analysis_count = build_sources_index()
    cpt_text, cpt_count, alias_count = build_concepts_index()

    src_changed = write_index(WIKI / "sources-index.md", src_text, args.check)
    cpt_changed = write_index(WIKI / "concepts-index.md", cpt_text, args.check)

    if args.check:
        if not (src_changed or cpt_changed):
            print("OK: sources-index.md en concepts-index.md zijn actueel.")
        return 1 if (src_changed or cpt_changed) else 0

    state = lambda c: "bijgewerkt" if c else "ongewijzigd"
    print(f"sources-index.md ({state(src_changed)}): {src_count} entries across "
          f"{len(cluster_counts)} clusters, {analysis_count} analyses")
    for cluster, n in cluster_counts.items():
        print(f"  {n:3d}  {cluster}")

    print(f"\nconcepts-index.md ({state(cpt_changed)}): {cpt_count} concepts, "
          f"{alias_count} alias mappings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
