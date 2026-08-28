# Ingest-stappen — wiki-ingest

De 10 stappen worden altijd sequentieel uitgevoerd. Geen stap overslaan, ook niet als de bron al bekend lijkt.

## Stap 1: Lees het bronbestand

Lees het bestand in `raw/` volledig. Sla bestanden in `raw/assets/` altijd over — dat zijn afbeeldingen, geen bronnen. Zonder volledige lezing kun je de kernpunten niet correct samenvatten.

## Stap 2: Bespreek kernpunten met gebruiker

Formuleer 2-5 kernpunten en vraag of de framing klopt. Bij updates: focus op wat er veranderd is ten opzichte van de vorige ingest. Dit is geen optionele stap — de gebruiker moet de richting bevestigen vóór het schrijven.

## Stap 3: Schrijf of update de bronpagina

Schrijf een nieuwe pagina in `wiki/sources/YYYY-MM-DD-slug.md` (nieuw bestand) of update de bestaande pagina (bij re-ingest). Maak nooit een tweede bronpagina voor een al-getrackte raw — edit de bestaande en voeg de nieuwe wikilink toe aan de Source page cel.

## Stap 4: Update wiki/entities/

Voeg nieuwe informatie toe aan relevante entiteitenpagina's. Markeer tegenstrijdigheden expliciet onder `## Open questions`. Entiteitenpagina's zijn de canonieke bron voor feitelijke claims over mensen, plaatsen, organisaties en producten.

## Stap 5: Update wiki/concepts/

Zelfde als stap 4 maar voor conceptpagina's. Één feit heeft één eigenaar — als een concept al elders gedocumenteerd is, link daarnaar in plaats van te dupliceren.

### Stap 5a: Canonical-doc-check voor derivative bronnen (verplicht)

**Trigger — alle drie moeten gelden:**
1. De bron is **derivative** (niet de canonieke leverancier-doc). Concreet: blogposts, LinkedIn/X-posts, nieuwsbrieven, YouTube-transcripts, Reddit-threads, community-artikelen, of pagina's onder `analysis/`. Officiële Anthropic-docs (`docs.claude.com`, `docs.anthropic.com`, `modelcontextprotocol.io`, repo-READMEs van anthropics/) zijn **niet** derivative — sla 5a over.
2. De claim is **feitelijk-klinkend en technisch** (niet een mening/recensie). Voorbeeld feitelijk: "Claude Code's Task-tool spawnt subagents in een eigen context window van 200k tokens". Voorbeeld mening: "Claude Code voelt sneller dan Cursor".
3. De claim raakt **Claude Code, MCP, de Task-tool (subagents), of memory** (auto-memory, CLAUDE.md, claude-mem, sessiestate). Andere onderwerpen → 5a niet vereist.

**Actie — precies één canonical-doc-check per claim, vóór schrijven naar wiki/concepts/*.md:**

Kies één bron, in deze volgorde van voorkeur:
- **Claude Code / Task-tool / memory:** delegeer via Task tool met `subagent_type: claude-code-guide` met de specifieke claim. De agent verifieert tegen `docs.claude.com/en/docs/claude-code/*`.
- **MCP:** WebFetch op `https://modelcontextprotocol.io/` of de relevante spec-pagina (bijv. `/specification/...`). Als dat onhaalbaar is: `claude-code-guide` agent met het MCP-onderwerp.
- **Anthropic SDK / API-claims die binnenglippen:** `mcp__plugin_context7_context7__query-docs` met library-id voor anthropic-sdk, of `claude-code-guide`.

Eén check per claim is genoeg — niet meerdere bronnen vergelijken. Doel is detectie van flagrante onjuistheden, geen volledige peer review.

**Drie uitkomsten:**

- **Bevestigd** → schrijf de claim naar de conceptpagina als feit. Geen extra annotatie nodig.
- **Tegenspraak met canonical doc** → schrijf de claim **niet** als feit. Voeg in plaats daarvan een entry onder `## Open questions` op de conceptpagina:
  ```
  - Bron [[sources/<slug>|<titel>]] claimt "<exacte claim>" maar canonical doc (<URL of agent-citaat>) zegt "<wat de doc zegt>". Niet overgenomen als feit.
  ```
- **Niet vindbaar in canonical doc** (claim gaat over ongedocumenteerd intern gedrag of recente change) → schrijf de claim met expliciete attributie: `Volgens [[sources/<slug>|<titel>]]: <claim>.` Niet als ongekwalificeerd feit. Noteer kort onder `## Open questions` dat canonical doc geen uitspraak doet.

**Rapportage:** noteer per geverifieerde claim één regel in het Stap 5-rapport onder een nieuw kopje **Canonical-doc-checks**: `<concept> ← <bron-slug>: bevestigd | tegenspraak | niet-vindbaar`.

**Waarom:** derivative bronnen halen Claude Code/MCP-internals geregeld door elkaar (verouderde API's, hallucinaties over toolnamen, verkeerd geciteerde limieten). Eén check vóór de claim de wiki binnenkomt voorkomt dat foutieve feiten zich via concept-pagina's vermenigvuldigen. Entiteiten- en bronpagina's zijn niet onderworpen aan 5a — daar staat de claim al expliciet aan een bron toegeschreven.

**Voorbeelden van triggerende claims:**
- "MCP servers communiceren standaard via stdio" → check op modelcontextprotocol.io
- "De Task-tool heeft een eigen context window van 200k" → check via claude-code-guide
- "CLAUDE.md wordt automatisch geladen tot 5 niveaus diep" → check via claude-code-guide
- "claude-mem injecteert geheugen via een PreToolUse hook" → check via claude-code-guide of repo-README

**Voorbeelden van niet-triggerende claims:**
- "Claude Code voelt prettig in de terminal" — geen feitelijke claim
- "Postgres ondersteunt JSONB" — niet over Claude Code/MCP/Task/memory
- Claim afkomstig uit `docs.claude.com` zelf — niet derivative

## Stap 6: Update index.md

Voeg de nieuwe bronpagina toe of ververs de bestaande entry. Formaat per entry: `- [[slug|Titel]] — één-zin beschrijving (N bronnen)`. Zonder deze stap raakt index.md verouderd en verliest het zijn functie als inhoudscatalogus.

## Stap 7: Patch quick-indexes (alleen in patch-modus)

**Conditioneel uitvoeren op basis van de index-modus uit SKILL.md Stap 2.**

In **patch-modus** (`count < 3`):
Voeg een one-liner toe aan `wiki/sources-index.md` in het juiste thematische cluster (of ververs de bestaande one-liner). Als er een conceptpagina is gewijzigd, ververs dan ook de entry in `wiki/concepts-index.md`. Formaat: `- [[slug|Titel]] (datum, auteur) — eerste zin van ## Summary (≤160 chars)`.

In **regenerate-modus** (`count >= 3`):
Sla deze stap volledig over voor dit bestand. De quick-indexes worden in één keer geregenereerd door `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py"` na afloop van de batch (zie nieuwe Stap 9.5 hieronder).

## Stap 8: Append aan log.md

Voeg één entry toe onderaan `log.md`:
- `## [YYYY-MM-DD] ingest | Titel` voor nieuwe bestanden
- `## [YYYY-MM-DD] update | Titel` voor gewijzigde bestanden

Log.md is append-only — nooit bestaande entries wijzigen of verwijderen.

## Stap 9: Update wiki/ingest-state.md

Ververs de rij: mtime, hash, source-page link en ingested-datum. Gebruik `\|` als tabel-escape voor de wikilink-pipe (bijv. `[[slug\|Titel]]`). Maak geen nieuwe rij als de raw al getrackt is — edit de bestaande. Voeg bij meerdere bronpagina's de extra wikilink toe na een komma in de Source page cel.

## Stap 9.5: Quick-indexes regenereren (alleen in regenerate-modus, post-batch)

**Wanneer:** alleen als de batch in **regenerate-modus** draait (count ≥ 3 uit SKILL.md Stap 2). Niet uitvoeren in patch-modus.

**Wanneer in de stappen-volgorde:** ná de per-file batch-loop (Stappen 1-9 voor elk bestand voltooid) maar **vóór** Stap 10 (qmd update). Dit is een post-batch stap, niet een per-file stap.

**Waarom de volgorde?** `regen-quick-indexes.py` schrijft `wiki/sources-index.md` en `wiki/concepts-index.md` opnieuw. `qmd update` indexeert daarna die nieuwe bestanden. Andersom werkt niet — qmd zou dan de oude indexen indexeren.

**Commando (vanuit vault root, zodat het script `wiki/` vindt via cwd):**
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py"
```

Het script is idempotent: leest alle pagina's in `wiki/sources/`, `wiki/recipes/`, `wiki/travel/`, `wiki/concepts/`, en overschrijft de twee index-bestanden volledig op basis van actuele frontmatter en `## Summary`-secties.

**Bevestig kort de output** (regel-totalen per cluster) zodat de gebruiker ziet dat de regeneratie geslaagd is.

**Bij scriptfout:** stop vóór Stap 10. Rapporteer de foutmelding aan de gebruiker en vraag bevestiging voordat je doorgaat. Voer Stap 10 (qmd update) pas uit nadat de indexes succesvol zijn bijgewerkt — anders worden stale indexes geïndexeerd.

## Stap 10: Re-index qmd (post-batch)

Roep `mcp__plugin_myrag-wiki_qmd-feat__update` aan zodat alle nieuwe en gewijzigde pagina's direct doorzoekbaar zijn. Dit is altijd de laatste stap — ook als er maar één pagina is gewijzigd. Deze stap is altijd de laatste — in regenerate-modus draait Stap 9.5 vóór deze stap, in patch-modus is Stap 9.5 niet van toepassing.

---

## Multi-page dialoogstroom

Trigger: een Modified bestand waarvan de Source page cel in ingest-state.md meerdere wikilinks bevat (komma-gescheiden).

**Stap M1:** Toon alle gelinkte pagina's:
```
Dit bestand is gekoppeld aan meerdere wiki-pagina's:
- [[sources/2026-01-10-artikel|Artikel]] (primaire bronpagina)
- [[analysis/2026-02-15-analyse|Analyse]] (derivative pagina)
```

**Stap M2:** Vraag gebruiker:
```
Welke pagina('s) wil je updaten?
1. Alleen de primaire bronpagina
2. Alleen de analyse-pagina
3. Beide pagina's
```

**Stap M3:** Voer stappen 2-9 uit alleen voor de bevestigde keuze.
- Stap 1 (lees bestand) is al uitgevoerd.
- Stap 7 binnen deze stappen is nog steeds conditioneel op index-modus (patch vs regenerate).
- Stap 10 (qmd update) draait altijd, post-batch.

**Stap M4:** Update de Ingested-datum in de ingest-state.md rij naar vandaag, ongeacht welke subset is bijgewerkt.

**Telling voor batch-count (INGS-01):** ongeacht welke subset wordt geüpdatet (alleen primair / alleen analyse / beide), telt deze raw als **1 bron** in de batch-count die de index-modus bepaalt. De count van de raw is onafhankelijk van het aantal wiki-pagina's dat erdoor geraakt wordt.
