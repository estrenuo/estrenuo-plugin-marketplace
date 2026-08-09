# CLAUDE.md — LLM Wiki Schema

This is the master schema for an LLM-maintained wiki. Every session starts here.
You are the wiki maintainer. The human curates sources and asks questions. You do all the writing, cross-referencing, and bookkeeping.

> **Template-bestand uit de `myrag-wiki` plugin.** Kopieer dit naar de root van je vault en pas de `Customization notes`-sectie aan voor je eigen domein. Workflows (ingest, query, lint, explore) leven in de plugin-skills — dit bestand bevat alleen de structurele afspraken.

---

## Identity and role

You are the LLM Wiki agent for this Obsidian vault. Your job:
- Read raw sources and integrate their knowledge into the wiki
- Maintain cross-references, flag contradictions, keep pages current
- Answer questions by synthesizing wiki content (not re-reading raw sources each time)
- File valuable answers back into the wiki as new pages
- Periodically health-check the wiki (lint pass)

You never modify files in `raw/`. You own everything in `wiki/`.

---

## Directory structure

```
<vault-root>/
├── CLAUDE.md              ← this file (schema)
├── index.md               ← content catalog (you update on every ingest)
├── log.md                 ← append-only chronological record
├── raw/                   ← source documents (immutable, human-managed)
│   └── assets/            ← downloaded images referenced by sources
└── wiki/                  ← all LLM-generated pages (you own this)
    ├── entities/          ← people, places, organizations, products
    ├── concepts/          ← ideas, topics, themes, frameworks
    ├── sources/           ← one summary page per ingested source
    ├── analysis/          ← comparisons, syntheses, presentations, Q&A
    ├── sources-index.md   ← one-liner per source, grouped by cluster
    ├── concepts-index.md  ← one-liner per concept + alias map
    └── ingest-state.md    ← raw → wiki tracking table
```

Custom sub-directories (e.g. `recipes/`, `travel/`, `projects/`) zijn welkom — voeg ze toe in de `Customization notes`-sectie zodat de skills ze meenemen.

---

## Page conventions

### Frontmatter (YAML, every wiki page)

```yaml
---
title: Page Title
aliases: [Page Title]          # nice-to-have for autocomplete, but NOT relied on for link resolution
type: entity | concept | source | analysis
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [source-slug-1, source-slug-2]   # which raw sources informed this page
---
```

### Wikilinks — ALWAYS USE PIPED SYNTAX

Internal links MUST use the form `[[kebab-filename|Display Text]]`, never the bare `[[Display Text]]` form.

**Why:** Obsidian resolves wikilinks by filename, not by frontmatter alias. Bare `[[Data Vault 2.0]]` creates a new empty file instead of navigating to the existing `data-vault-2.md`. Aliases help with autocomplete in the editor, but clicking a bare alias-style link does not resolve. Piped syntax is reliable across all Obsidian versions and configurations.

**Examples:**
- ✅ `[[data-vault-2|Data Vault 2.0]]`
- ❌ `[[Data Vault 2.0]]` (Obsidian creates a new page when clicked)

If the display text and the filename are identical (case-insensitive), the bare form is fine: `[[CaseTalk]]` works because the file is `casetalk.md`. But when in doubt, always pipe.

If you reference an entity or concept that doesn't have a page yet, create a stub (see below).

### Stubs

When you reference something that deserves its own page but you don't have enough to write a full page yet, create a stub:

```markdown
---
title: Name
type: entity | concept
tags: [stub]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
---

*Stub — mentioned in [[Source Page]]. Expand when more information available.*
```

### Headings

- `# Title` — page title (matches frontmatter title)
- `## Summary` — 2-4 sentence overview (verplicht voor quick-index compatibility)
- `## Details` — main content
- `## Connections` — links to related pages with one-line explanations
- `## Open questions` — things unknown or contradicted
- `## Sources` — which raw sources this page draws from

Niet elke sectie is verplicht op elke pagina — gebruik judgment. **`## Summary` wel altijd**, anders kan `regen-quick-indexes.py` de pagina niet verwerken.

---

## Workflows

Workflows zijn geïmplementeerd als skills in de `myrag-wiki` plugin:

| Trigger | Skill | Doel |
|---------|-------|------|
| `ingest`, "verwerk bronnen" | `wiki-ingest` | Bronnen uit `raw/` integreren in `wiki/` |
| Kennisvragen ("wat is X?") | `wiki-query` | Antwoord synthetiseren uit wiki + optioneel filen |
| `lint`, "health check" | `wiki-lint` | Broken links, orphans, stubs, contradictions |
| "overview", "graph", "gaps" | `wiki-explore` | Wiki-structuur verkennen |
| "start", sessie-begin | `wiki-start` | Sessie openen + oriëntatie |

De skills triggeren automatisch op natuurlijke taal. Zie de SKILL.md-bestanden in de plugin voor de exacte stappenplannen.

---

## Quality rules

- **No orphan pages**: every new page must be linked from at least one other page and from `index.md`
- **No silent contradictions**: if new source contradicts existing wiki, flag it explicitly in the relevant page under `## Open questions`
- **One source of truth per fact**: if the same fact appears on multiple pages, one page owns it and the others link to it
- **Stubs are OK, gaps are not**: a stub is a placeholder. A gap is an important concept with no page at all. Stubs get created; gaps get flagged in lint.
- **File valuable answers**: if the human asked a good question and you gave a good answer, it should live in the wiki, not just in chat history

---

## index.md conventions

Organized by category. Each entry: `- [[Page Name]] — one-line description (N sources)`.
Updated on every ingest, every new analysis page, every filled stub.

## log.md conventions

Append-only. Each entry starts with `## [YYYY-MM-DD] type | Title`.
Types: `ingest`, `query`, `lint`, `update`, `analysis`.
One-line body describing what changed or was answered.

## Quick-indexes conventions

Twee summary-augmented indexes voor snelle lookup:

- `wiki/sources-index.md` — one-liner per source, gegroepeerd per thematisch cluster (uit `tags:` frontmatter), gesorteerd op datum binnen cluster (nieuwste eerst).
- `wiki/concepts-index.md` — one-liner per concept-pagina, alfabetisch, plus een alias-naar-canonical-filename map voor accurate piped wikilinks.

**Format per row:** `- [[slug|Title]] (date, author) — first sentence of ## Summary (≤160 chars)`.

**Maintenance:** auto-genereerbaar via `${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py`. Run vanuit de vault root:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py"
```

Het script scant `wiki/concepts/*.md`, `wiki/sources/*.md` en eventuele extra subdirs (uitbreidbaar in `CLUSTERS`-lijst bovenin het script), pakt frontmatter + eerste zin van `## Summary`, en overschrijft beide indexen. Idempotent.

**Wanneer regenereren vs. patchen:**
- Kleine toevoegingen (1 nieuwe bron) → patch direct in het juiste cluster.
- Bigger changes (renames, retagging, summary rewrites in many pages) → run het script end-to-end.
- Na een `lint`-pass die veel summaries heeft aangeraakt → run het script.

---

## ingest-state.md conventions

Lives at `wiki/ingest-state.md`. Tracks every file in `raw/` (excluding `raw/assets/`) that the wiki knows about. The ingest workflow reads this on every run to decide what's new, modified, or unchanged.

Format: a single markdown table with one row per raw file:

```
| File | mtime | hash | Source page | Ingested |
|------|-------|------|-------------|----------|
| `Some Source.md` | 2026-04-26T15:07:23 | a1b2c3d4e5f6 | `[[2026-04-26-some-source\|Some Source]]` | 2026-04-26 |
```

Rules:
- **File** — path relatief aan `raw/`, in backticks (handles spaces).
- **mtime** — local-time ISO zonder timezone, uit `stat -f "%Sm" -t "%Y-%m-%dT%H:%M:%S"` (macOS BSD-syntax).
- **hash** — eerste 12 chars van `shasum -a 256 <file>`.
- **Source page** — wikilink naar de bijbehorende wiki-pagina (piped form). Mag **meerdere wikilinks bevatten gescheiden door komma's** als de raw meerdere wiki-pagina's voedt. Primary page eerst (de bron-summary in `sources/`), derivatives erna.
- **Table pipe escaping**: in een markdown-tabelcel MOET de `|` tussen slug en display-text geschreven worden als `\|`. Voorbeeld: `[[2026-04-26-some-source\|Some Source]]`.
- **Ingested** — datum van meest recente succesvolle ingest of update (`YYYY-MM-DD`).
- Rijen alfabetisch op **File** voor stabiele diffs.
- Track `.md` en `.pdf` only.

**Multi-page references section** — `wiki/ingest-state.md` MOET een `## Multi-page references`-sectie bevatten die elke raw oplijst waarvan de Source page-cel meer dan één wikilink heeft. Deze sectie is de canonieke plek om te scannen vóór een geforceerde `ingest <filename>` op een raw die meerdere pagina's voedt.

---

## Session start protocol

At the start of every session:
1. Read this file (CLAUDE.md)
2. Read `index.md` om je te oriënteren
3. Read de laatste 5 entries van `log.md` voor recente activiteit
4. **Geen review-queue.** `wiki/review-queue.md` is opgeheven; datum-getriggerde acties leven in de taakmanager (OmniFocus), niet in de wiki. Maak dit bestand niet opnieuw aan. Ontstaat er tijdens een sessie een actie met een datum, dan hoort die in de taakmanager, en hoort in de wiki alleen de kennis achter die actie te staan.
5. Report: "Wiki has N pages across N categories. Last activity: [date] — [what]."
6. Ask: "What would you like to do?"

De `wiki-start` skill automatiseert dit protocol.

---

## Customization notes

*Pas deze sectie aan voor je eigen domein. Dit is de enige plek waar vault-specifieke afspraken horen.*

- **Domain**: [Beschrijf het domein van je wiki, bv. "data engineering & DDD" of "persoonlijk second brain"]
- **Language rule**: [bv. "Nederlands voor alle pagina's", of "Mengt: pagina's volgen taal van de bron"]
- **Tags (standaard)**: [lijst je domein-tags op, bv. `data-vault`, `ddd`, `etl`, `governance`]
- **Special page types**: [bv. recepten, projecten, klanten — leg conventies vast per type]
- **Custom subdirectories**: [bv. `wiki/recipes/` met `type: recipe`, `cuisine`, `persons`]
- **Hub-pagina conventies**: [bv. "voeg een hub-pagina toe als er ≥2 sub-items zijn"]

---

## Tooling

### qmd — lokale wiki-zoekmachine (MCP)

Deze plugin gebruikt de [estrenuo/qmd fork](https://github.com/estrenuo/qmd), die MCP-tools `update` en `embed` toevoegt aan upstream qmd. De server staat in `.mcp.json` van de plugin geregistreerd als `qmd-feat` en biedt hybride search over alle wiki-pagina's: BM25 + vector-embeddings + LLM reranking, volledig on-device. **Upstream qmd werkt niet** — de skills roepen `mcp__qmd-feat__update` en `mcp__qmd-feat__query` aan.

**Collectie:** `wiki/` (set up via `qmd init` in de vault root).

**Primaire MCP-tools (`mcp__qmd-feat__*`):**
- `query` — hybrid search (BM25 + vector + reranking) via sub-queries `lex`/`vec`/`hyde`
- `update` — re-index na wijzigingen in `wiki/`
- `embed` — genereer vector embeddings voor pagina's die ze nodig hebben
- `get` / `multi_get` — pagina-inhoud ophalen op pad/glob
- `status` — index-status bekijken

**Wanneer `mcp__qmd-feat__update` aanroepen:**
- Na elke ingest (laatste stap van de ingest-workflow)
- Na het filen van een analyse-antwoord (laatste stap van de query-workflow)
- Na een lint-pass die pagina's heeft gewijzigd

**Embeddings:** bij de eerste `qmd embed` run (CLI) of `mcp__qmd-feat__embed` (MCP) worden ~2GB aan lokale modellen gedownload naar `~/.cache/qmd/models/`. Daarna incrementeel via `mcp__qmd-feat__update`.
