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

## Migratie: hernoemd van `claude-plugin-marketplace` (juni 2026)

Deze marketplace heette eerst `claude-plugin-marketplace`. De naam is gewijzigd
omdat "claude" gereserveerd is voor Anthropic. **Dit is een breaking change voor
bestaande installs**: de `name` in `marketplace.json` is veranderd, dus de oude
marketplace- en plugin-referenties werken niet meer.

GitHub redirect de oude repo-URL automatisch, maar de marketplace-naam waaronder
plugins geïnstalleerd zijn niet. Wie de plugin had onder de oude naam:

```text
/plugin marketplace remove claude-plugin-marketplace
/plugin marketplace add estrenuo/estrenuo-plugin-marketplace
/plugin install myrag-wiki@estrenuo-plugin-marketplace
```

In Claude Cowork: vervang in team-`settings.json` de key `claude-plugin-marketplace`
door `estrenuo-plugin-marketplace` en de plugin-key `myrag-wiki@claude-plugin-marketplace`
door `myrag-wiki@estrenuo-plugin-marketplace`.

## Bijdragen

Zie [CONTRIBUTING.md](CONTRIBUTING.md) voor de versioning- en tag-conventie
(per-plugin semver, tag-format `<plugin>/v<x.y.z>`).
