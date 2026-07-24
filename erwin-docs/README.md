# erwin-docs plugin

Documentatie-skill voor **erwin Data Modeler 12.5**. Beantwoordt vragen uit de
officiële bookshelf in plaats van uit modelgeheugen: erwin's class names,
property names, macronamen en menupaden zijn casegevoelig en precies het soort
detail dat een taalmodel plausibel verzint. De skill verifieert, of zegt
expliciet dat iets niet geverifieerd is, en sluit elk antwoord af met een
bronverwijzing.

## Bevat

**Skills** (auto-activerend op natural-language triggers):

- `erwin-docs` — triggert op vragen over erwin Data Modeler / erwin DM / ERwin
  en op losse termen als TLX, Template Editor, Bulk Editor, Complete Compare,
  Mart, UDP, metamodel, SCAPI, erwin Spy, EMX, `.erwin`-bestanden. Vier
  antwoordmodi: gebruik & features, import/export & engineering, metamodel &
  XML, en automatisering (TLX, macro's, API).

De skill brengt zes referentiebestanden mee (`references/`): een doc-map van
de 12.5-bookshelf, een vraag-naar-pagina-gids, en per modus een
antwoordformaat.

## Installeren

### Via GitHub

```text
/plugin marketplace add estrenuo/estrenuo-plugin-marketplace
/plugin install erwin-docs@estrenuo-plugin-marketplace
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
    "erwin-docs@estrenuo-plugin-marketplace": true
  }
}
```

## Vereisten

- **Web search + web fetch** moeten beschikbaar zijn in de sessie: de skill
  zoekt en leest live in de erwin 12.5-bookshelf en gebruikt geen lokale kopie
  van de documentatie.
- Geen MCP-servers of externe tools nodig.
