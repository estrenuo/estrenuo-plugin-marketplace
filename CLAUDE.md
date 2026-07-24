# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Wat dit is

Een Claude Code / Cowork **plugin marketplace**: een verzameling losse plugins onder één repo, geregistreerd via `.claude-plugin/marketplace.json`. Elke plugin leeft in een eigen subdirectory in de repo-root (zoals `myrag-wiki/`) en wordt onafhankelijk versioneerd.

Claude Code detecteert plugin-updates via **git refs (tags/commits)**, niet via `plugin.json#version`. Versies in `plugin.json` zijn auteur-metadata; de tag (`<plugin>/v<x.y.z>`) op de bump-commit is wat de update-flow ziet.

## Per-plugin versioning en releasen

Elke plugin heeft een eigen versielijn (semver in `<plugin>/.claude-plugin/plugin.json`) en eigen tag-prefix. Releasen gaat via `scripts/bump-plugin.sh`:

```bash
scripts/bump-plugin.sh <plugin> <patch|minor|major>          # vanaf schone main
scripts/bump-plugin.sh <plugin> <bump> --allow-dirty         # bundelen met andere staged changes
git push origin main --follow-tags
```

Het script doet pre-flight checks (plugin geregistreerd in `marketplace.json`, op `main`, schone working tree, geldig semver, tag bestaat nog niet, `python3` aanwezig), muteert `plugin.json` (Python-based JSON edit, behoudt UTF-8 / accenten), maakt commit + annotated tag `<plugin>/v<x.y.z>`. Het pusht **niet** automatisch.

Wat MAJOR vs. MINOR vs. PATCH betekent voor een Claude Code plugin (verwijderde of hernoemde skill = MAJOR, gewijzigde trigger-conditie die bestaande prompts breekt = MAJOR, MCP-prefix rename = MAJOR, nieuwe skill = MINOR) staat uitgewerkt in `CONTRIBUTING.md`. Pre-1.0 (`0.x.y`) mag breaking changes via MINOR.

## Repo-layout

```
.claude-plugin/marketplace.json   # registreert plugins via relatief source-pad
<plugin-name>/
├── .claude-plugin/plugin.json    # naam, versie, beschrijving (auteur-metadata)
├── .mcp.json                     # optioneel; MCP-servers die de plugin meebrengt
├── README.md                     # installatie, configuratie, vereisten
├── skills/<skill-name>/SKILL.md  # auto-activerende skills
├── agents/<agent>.md             # subagents (Task tool)
├── scripts/                      # plugin-eigen scripts (aangeroepen via ${CLAUDE_PLUGIN_ROOT})
└── templates/                    # bestanden die naar user-vaults gekopieerd worden
scripts/bump-plugin.sh            # repo-wide release-tooling
docs/                             # lokaal werk, in .gitignore — niet committen
```

## Een nieuwe plugin toevoegen

1. Maak `<plugin-name>/.claude-plugin/plugin.json` met `name`, `version` (start op `0.1.0`), `description`.
2. Voeg een entry toe aan `.claude-plugin/marketplace.json#plugins` met `name`, `source: "./<plugin-name>"`, `description`. **Naam in `marketplace.json` moet matchen met `plugin.json#name`** — anders faalt `bump-plugin.sh` op de "plugin not registered" check.
3. Voeg skills/agents/MCP-config toe naar behoefte.
4. Eerste release: `scripts/bump-plugin.sh <plugin> patch` (van `0.1.0` → `0.1.1`) of edit de versie handmatig en tag.

## Plugins in deze marketplace

- **myrag-wiki** — Skills + agents voor het onderhouden van een Obsidian-based LLM wiki (ingest, query, lint, explore, start). Vereist de **estrenuo/qmd fork** (niet upstream qmd); MCP-server staat in `myrag-wiki/.mcp.json` als `qmd-feat`. De skills roepen `mcp__qmd-feat__*` tools aan. Plugin levert ook `templates/CLAUDE.md` dat user-vaults kopiëren als hun eigen vault-schema — dat template is **niet** dezelfde CLAUDE.md als deze.
- **erwin-docs** — Documentatie-skill voor erwin Data Modeler 12.5. Eén skill (`skills/erwin-docs/`) met zes referentiebestanden in `references/`. Geen MCP-servers of scripts; vereist alleen web search + web fetch in de sessie, want de skill zoekt live in de erwin 12.5-bookshelf.

## Bekende conventies

- **Geen repo-wide tags** (`v1.0.0` zonder plugin-prefix). Per-plugin tags houden versielijnen onafhankelijk zodra er meer dan één plugin bestaat.
- **Eén plugin per PR**, met expliciete MAJOR/MINOR/PATCH-rationale in de PR-beschrijving zodat de tag na merge eenduidig vastligt.
- `docs/` is `.gitignore`d — lokaal werk, niet in de repo.
