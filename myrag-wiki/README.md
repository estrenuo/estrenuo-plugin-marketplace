# myrag-wiki plugin

Skills + agents voor het onderhouden van een Obsidian-based LLM wiki (zie `templates/CLAUDE.md` voor het vault-schema en de Vault bootstrap-sectie hieronder voor setup).

## Bevat

**Skills** (auto-activerend op natural-language triggers):

- `wiki-start` — wiki-sessie starten ("wiki start", "open wiki"), oriëntatie op de wiki
- `wiki-ingest` — bronnen verwerken vanuit `raw/`
- `wiki-query` — kennisvragen beantwoorden via qmd + indexes
- `wiki-lint` — health check (broken links, orphans, stubs)
- `wiki-explore` — overview / graph / gaps verkennen
- `autoresearch` — iteratieve web-research-loop (WebSearch + WebFetch) die direct in `wiki/analysis/` filet volgens myrag-conventies

**Agents** (gespecialiseerd, oproepbaar via Task tool):

- `analysis-filer`, `contradiction-detector`, `cross-reference-sweeper`,
  `gap-detector`, `open-questions-triage`, `pdf-ingest-agent`,
  `source-cluster-tagger`, `stub-filler`

## Installeren

### Via GitHub

```text
/plugin marketplace add estrenuo/estrenuo-plugin-marketplace
/plugin install myrag-wiki@estrenuo-plugin-marketplace
```

### In Claude Cowork

Voeg de marketplace toe aan team-`settings.json` zodat alle teamleden hem automatisch zien:

```json
{
  "extraKnownMarketplaces": {
    "estrenuo-plugin-marketplace": {
      "type": "github",
      "repo": "estrenuo/estrenuo-plugin-marketplace"
    }
  },
  "enabledPlugins": {
    "myrag-wiki@estrenuo-plugin-marketplace": true
  }
}
```

> **Migratie:** de marketplace heette eerder `claude-plugin-marketplace`. Bestaande
> installs moeten opnieuw toevoegen onder `estrenuo-plugin-marketplace`. Zie de
> [marketplace-README](../README.md#migratie-hernoemd-van-claude-plugin-marketplace-juni-2026).

## Vault bootstrap

De skills + agents lezen bij elke startup `CLAUDE.md` en `index.md` uit de vault root.
Voor een nieuwe vault: kopieer het meegeleverde template en pas het aan voor je domein.

```bash
cd /pad/naar/jouw-vault
cp "${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md" ./CLAUDE.md
touch index.md log.md
mkdir -p raw wiki/{entities,concepts,sources,analysis}
```

Open daarna `CLAUDE.md` en vul de `Customization notes`-sectie in met je domein,
tags en eventuele custom subdirectories (zoals `recipes/` of `projects/`).

Het template bevat alleen de structurele afspraken — geen vault-specifieke
content. Workflows (ingest, query, lint, explore) leven in de plugin-skills,
niet in `CLAUDE.md`.

## Vereisten

- Obsidian-vault met `CLAUDE.md`, `index.md`, `log.md`, `raw/`, `wiki/` (zie Vault bootstrap hierboven)
- qmd CLI geïnstalleerd (upstream, <https://github.com/tobi/qmd>). De skills zoeken via de MCP-server en herindexeren via Bash met `qmd update && qmd embed`; een fork is niet meer nodig.
- De MCP-server staat in `.mcp.json` geregistreerd als `qmd-feat` (historische naam) en start automatisch wanneer de plugin enabled is. Het commando is `${HOME}/.local/bin/qmd`, een absoluut pad in plaats van een PATH-lookup: Claude Code start ook vanuit de Desktop-app, waar `~/.local/bin` niet altijd in PATH zit. Zorg dus dat de qmd-binary daar staat of daarheen symlinkt. De skills roepen de CLI om dezelfde reden aan via `"$HOME/.local/bin/qmd"`.
- Python 3 voor `${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py`
  (script wordt vanuit de vault root aangeroepen; vindt `wiki/` via cwd of via een vault-pad als argv[1])

## Configuratie

De `wiki-explore` skill (graph-modus) heeft het pad naar de `wiki/`-directory binnen je vault nodig.
Zet de environment variable `MYRAG_WIKI_DIR` in je shell profile (`~/.zshrc` of `~/.bashrc`):

```bash
export MYRAG_WIKI_DIR="/pad/naar/jouw-vault/wiki"
```

Voorbeelden voor veelvoorkomende setups:

```bash
# Lokale vault
export MYRAG_WIKI_DIR="$HOME/Documents/Obsidian/my-vault/wiki"

# iCloud-gesyncte Obsidian vault (macOS)
export MYRAG_WIKI_DIR="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault/wiki"
```

Herlaad daarna je shell (`source ~/.zshrc`) of start een nieuwe terminal.

Zonder deze variable falen de graph-commando's met een duidelijke foutmelding
die naar deze sectie verwijst.
