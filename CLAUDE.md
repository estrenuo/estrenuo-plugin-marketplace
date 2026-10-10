# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Wat dit is

Een Claude Code / Cowork **plugin marketplace**: een verzameling losse plugins onder één repo, geregistreerd via `.claude-plugin/marketplace.json`. Elke plugin leeft in een eigen subdirectory in de repo-root (zoals `myrag-wiki/`) en wordt onafhankelijk versioneerd.

Claude Code detecteert plugin-updates via **git refs (tags/commits)**, niet via `plugin.json#version`. Versies in `plugin.json` zijn auteur-metadata; de tag (`<plugin>/v<x.y.z>`) op de bump-commit is wat de update-flow ziet.

## Per-plugin versioning en releasen

Elke plugin heeft een eigen versielijn (semver in `<plugin>/.claude-plugin/plugin.json`) en eigen tag-prefix. Releasen gaat via een PR. `main` is beschermd (directe pushes geweigerd, ook voor admins; verplichte check `version-bump`):

```bash
git switch -c release/<plugin>-<x.y.z> origin/main
scripts/bump-plugin.sh <plugin> <patch|minor|major>          # weigert op main
scripts/bump-plugin.sh <plugin> <bump> --allow-dirty         # bundelen met gestagede changes
git push -u origin release/<plugin>-<x.y.z>
gh pr create --base main && gh pr merge --merge --delete-branch
```

Het script doet pre-flight checks (plugin geregistreerd in `marketplace.json`, niet op `main`, schone working tree, geldig semver, tag bestaat nog niet lokaal of op origin, `python3` aanwezig), muteert `plugin.json` en maakt een commit. Het tagt niet: de workflow `tag-release` zet `<plugin>/v<x.y.z>` na de merge op `main`. De workflow `release-gate` draait `scripts/check-version-bump.py`: gewijzigde plugin zonder versie-bump, bezette tag, of een `SKILL.md`-description met punthaken of langer dan 1024 tekens laat de PR falen. Na de merge: Cowork-marketplace handmatig re-syncen in claude.ai.

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

- **myrag-wiki** — Skills + agents voor het onderhouden van een Obsidian-based LLM wiki (ingest, query, lint, explore, start). Vereist de **estrenuo/qmd fork** (niet upstream qmd); MCP-server staat in `myrag-wiki/.mcp.json` als `qmd-feat`. De skills roepen `mcp__plugin_myrag-wiki_qmd-feat__*` tools aan (plugin-scoped prefix). Plugin levert ook `templates/CLAUDE.md` dat user-vaults kopiëren als hun eigen vault-schema — dat template is **niet** dezelfde CLAUDE.md als deze.
- **erwin-docs** — Documentatie-skill voor erwin Data Modeler 12.5. Eén skill (`skills/erwin-docs/`) met zes referentiebestanden in `references/`. Geen MCP-servers of scripts; vereist alleen web search + web fetch in de sessie, want de skill zoekt live in de erwin 12.5-bookshelf.

## Bekende conventies

- **Geen repo-wide tags** (`v1.0.0` zonder plugin-prefix). Per-plugin tags houden versielijnen onafhankelijk zodra er meer dan één plugin bestaat.
- **Eén plugin per PR**, met expliciete MAJOR/MINOR/PATCH-rationale in de PR-beschrijving zodat de tag na merge eenduidig vastligt.
- `docs/` is `.gitignore`d — lokaal werk, niet in de repo.
