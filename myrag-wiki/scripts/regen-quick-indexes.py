#!/usr/bin/env python3
"""Regenerate wiki/sources-index.md and wiki/concepts-index.md from frontmatter + ## Summary.

Run from the wiki vault root (where wiki/ lives):
    python3 "$CLAUDE_PLUGIN_ROOT/scripts/regen-quick-indexes.py"

Or pass an explicit vault path as argv[1]:
    python3 regen-quick-indexes.py /path/to/vault

Reads:
- wiki/concepts/*.md
- wiki/sources/*.md, wiki/recipes/*.md, wiki/travel/*.md

Writes (overwrites):
- wiki/sources-index.md   — sources grouped by thematic cluster (tag-priority match)
- wiki/concepts-index.md  — concepts alphabetical + alias-to-canonical map

Cluster mapping is defined in CLUSTERS below. First match wins. To add a new cluster
or expand an existing one, edit the keyword set. Re-run after changes.

The format per row is: `- [[slug|Title]] (date, author) — first sentence of ## Summary`
truncated to ~160 chars.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _resolve_repo_root() -> Path:
    """Resolve vault root from argv[1], else cwd. wiki/ must exist beneath it."""
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1]).resolve()
    else:
        candidate = Path.cwd().resolve()
    if not (candidate / "wiki").is_dir():
        sys.stderr.write(
            f"error: no wiki/ directory found under {candidate}.\n"
            "Run from the vault root, or pass the vault path as the first arg.\n"
        )
        sys.exit(1)
    return candidate


REPO_ROOT = _resolve_repo_root()
WIKI = REPO_ROOT / "wiki"

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


def page_info(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    return {
        "slug": path.stem,
        "title": get_field(fm, "title").strip('"').strip("'"),
        "tags": parse_list(get_field(fm, "tags")),
        "author": get_field(fm, "author"),
        "date": get_field(fm, "date"),
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


def regen_sources_index() -> tuple[int, dict[str, int]]:
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

    today = _today()
    lines = [
        "---",
        "title: Sources Index — Quick Reference",
        "type: meta",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        "# Sources Index — Quick Reference",
        "",
        "One-liner per bron, gegroepeerd per thematisch cluster (auto-afgeleid uit `tags:` in de frontmatter), binnen cluster gesorteerd op datum (nieuwst eerst).",
        "",
        "**Doel:** zonder elke source-pagina te openen kunnen scannen wat erin staat. Bij query-workflow eerst hier zoeken, dan de geselecteerde 3–5 pagina's volledig lezen.",
        "",
        "**Onderhoud:** auto-genereerbaar via `scripts/regen-quick-indexes.py`. Bij ingest van een nieuwe bron: regel handmatig invoegen in het juiste cluster, of het script herrunnen.",
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

    (WIKI / "sources-index.md").write_text("\n".join(lines), encoding="utf-8")
    counts = {c: len(by_cluster[c]) for c in cluster_order if c in by_cluster}
    return len(sources), counts


def regen_concepts_index() -> tuple[int, int]:
    concepts = []
    for p in sorted((WIKI / "concepts").glob("*.md")):
        concepts.append(page_info(p))
    concepts.sort(key=lambda x: x["title"].lower())

    today = _today()
    lines = [
        "---",
        "title: Concepts Index — Quick Reference",
        "type: meta",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        "# Concepts Index — Quick Reference",
        "",
        "One-liner per concept-pagina, alfabetisch op titel. Aan het einde een aliases-mapping om correcte piped wikilinks te schrijven.",
        "",
        "**Doel:** snel zien welke concepten bestaan voor cross-referentie en wikilink-resolutie.",
        "",
        "**Onderhoud:** auto-genereerbaar via `scripts/regen-quick-indexes.py`.",
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

    (WIKI / "concepts-index.md").write_text("\n".join(lines), encoding="utf-8")
    return len(concepts), len(alias_pairs)


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


def main() -> int:
    if not WIKI.exists():
        print(f"ERROR: {WIKI} not found. Run from repo root.", file=sys.stderr)
        return 1

    src_count, cluster_counts = regen_sources_index()
    print(f"sources-index.md: {src_count} entries across {len(cluster_counts)} clusters")
    for cluster, n in cluster_counts.items():
        print(f"  {n:3d}  {cluster}")

    cpt_count, alias_count = regen_concepts_index()
    print(f"\nconcepts-index.md: {cpt_count} concepts, {alias_count} alias mappings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
