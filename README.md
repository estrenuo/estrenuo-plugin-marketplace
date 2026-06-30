# estrenuo-plugin-marketplace

Een verzameling Claude Code / Cowork plugins van Estrenuo.

## Plugins in deze marketplace

- **[myrag-wiki](myrag-wiki/)** — Skills + agents voor het onderhouden van een Obsidian-based LLM wiki: ingest, query, lint, explore en start workflows bovenop de qmd MCP-server.

## Installeren

Voeg de marketplace toe en installeer een plugin:

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

Zie de README van elke plugin voor specifieke vereisten en configuratie.

## Bijdragen

Zie [CONTRIBUTING.md](CONTRIBUTING.md) voor de versioning- en tag-conventie
(per-plugin semver, tag-format `<plugin>/v<x.y.z>`).
