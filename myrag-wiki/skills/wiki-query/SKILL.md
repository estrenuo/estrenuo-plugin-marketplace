---
name: wiki-query
description: |
  Gebruik deze skill wanneer de gebruiker een kennisvraag stelt over
  wiki-inhoud: wat iets is, hoe iets werkt, of welke bronnen er zijn
  over een onderwerp.

  Voorbeelden van triggerzinnen:
  - "Wat is Data Vault 2.0?"
  - "Vertel me over bitemporal data"
  - "Hoe werkt X?"
  - "Zijn er bronnen over Indiase keuken?"
  - "Wat zegt de wiki over persona-ontwikkeling?"

  NIET voor navigatievragen — die gaan naar wiki-explore:
  - "Geef me een overzicht" (→ wiki-explore/overview)
  - "Welke pagina's zijn orphans?" (→ wiki-explore/graph)
  - "Wat ontbreekt er in de wiki?" (→ wiki-explore/gaps)
  - "Hoeveel pagina's heeft de wiki?" (→ wiki-explore)

  Grijze zone: als de vraag een eigennaam of concept bevat waarover
  inhoud verwacht kan worden → wiki-query. Als de vraag over de wiki
  als systeem gaat → wiki-explore.
allowed-tools: Read Write Edit Task mcp__plugin_myrag-wiki_qmd-feat__query mcp__plugin_myrag-wiki_qmd-feat__update mcp__plugin_myrag-wiki_qmd-feat__get mcp__qmd-feat__query mcp__qmd-feat__update mcp__qmd-feat__get
---

# Wiki Query — 5-staps checklist

Voer alle stappen in volgorde uit. Sla geen stap over.

---

**Stap 1: Bevraag qmd (primaire retrieval)**

Roep de qmd `query`-tool aan — `mcp__plugin_myrag-wiki_qmd-feat__query` (of `mcp__qmd-feat__query` als qmd via project-MCP i.p.v. de plugin geladen is) — met minimaal twee sub-queries:

```
searches=[
  {type: 'lex', query: '<kernterm(en) uit de vraag>'},
  {type: 'vec', query: '<volledige vraag in natuurlijke taal>'}
]
intent='<korte beschrijving van wat de gebruiker zoekt>'
```

Gebruik altijd minimaal één `lex` en één `vec` sub-query. Voeg optioneel een `hyde`-sub-query toe voor abstracte of brede vragen.

Bij sparse resultaten (minder dan 3 hits boven `minScore: 0.5`): lees als aanvulling:
- `wiki/concepts-index.md` — voor conceptuele vragen
- `wiki/sources-index.md` — voor bronspecifieke of vergelijkende vragen
- `index.md` — voor navigatie op clusterniveau

Kies de meest relevante 3-5 pagina's uit de gecombineerde resultaten.

**Waarom:** qmd combineert BM25-keyword, vector-semantiek en LLM-reranking — dat geeft betere resultaten dan quick-indexes alleen. Quick-indexes zijn een fallback voor wanneer qmd te weinig teruggeeft.

---

**Stap 2: Lees de geselecteerde pagina's volledig**

Lees elke geselecteerde pagina in zijn geheel via Read of qmd `get`. Sla geen pagina's over omdat de titel al duidelijk lijkt.

**Waarom:** Snippets uit qmd zijn korte uittreksels — de volledige context zit in de pagina. Zonder volledig lezen mis je nuance, tegenstellingen of verbanden.

---

**Stap 3: Synthetiseer een antwoord met wikilink-citaten**

Geef een samengesteld antwoord op basis van de gelezen pagina's. Elke verwijzing naar een wiki-pagina gebruikt piped wikilink-syntax: `[[kebab-slug|Display Tekst]]`. Gebruik nooit `[[Display Tekst]]` zonder slug — Obsidian maakt dan een lege pagina aan.

**Waarom:** Piped syntax is de enige betrouwbare wikilink-vorm in Obsidian; bare alias-links lijken te werken in de editor maar falen bij klikken en creëren orphan-pagina's.

---

**Stap 4: Bied archivering aan (verplichte gate)**

Vraag na het antwoord altijd:

> "Wil je dit antwoord archiveren als nieuwe pagina in `wiki/analysis/`?"

Dit is een harde gate — sla hem nooit over, ook niet bij een "evident" antwoord. Behandel "misschien later", "weet ik niet" of geen reactie als "nee".

**Waarom:** Waardevolle antwoorden die alleen in de chatgeschiedenis leven, gaan verloren. De gate zorgt dat de gebruiker actief kiest.

---

**Stap 5: Archiveer het antwoord (alleen bij "ja")**

**Snelpad — delegeer naar `analysis-filer` agent:** roep de Task tool aan met
`subagent_type: analysis-filer` en plak de volledige Q&A-tekst (vraag + antwoord
inclusief alle wikilinks) **letterlijk** in de invocation prompt. De agent heeft
geen toegang tot deze conversatie-context, dus de Q&A-tekst moet expliciet in de
prompt staan. De agent doet substappen 5.1 t/m 5.5 in één keer en presenteert
een draft ter goedkeuring vóór schrijven.

Alleen als de gebruiker de delegatie afwijst of als de agent niet beschikbaar is,
voer je de vijf substappen hieronder handmatig uit.

Voer alle vijf substappen in volgorde uit. Sla geen enkele over.

**5.1 — Schrijf de analysis-pagina**

Maak `wiki/analysis/[kebab-slug].md` aan met Write. Verplichte structuur:

```markdown
---
title: [Vraag of synthesetitel]
aliases: ["[Vraag of synthesetitel]"]
type: analysis
tags: [relevante tags]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [source-slug-1, source-slug-2]
---

# [Vraag of titel]

## Summary
[1-2 zinnen die de kern van het antwoord samenvatten — VERPLICHT voor quick-index compatibiliteit]

## [Hoofdinhoud — vrije sectienamen]

## Connections
- [[kebab-slug|Gerelateerde Pagina]] — [één zin relatie]

## Sources
- [[source-slug|Brontitel]]
```

De `## Summary`-sectie is verplicht. Zonder Summary kan `scripts/regen-quick-indexes.py` de pagina niet verwerken.

**Waarom:** Gestandaardiseerde frontmatter en secties zorgen dat de pagina vindbaar is via qmd, correct wordt weergegeven in de quick-indexes, en consistent is met de rest van de wiki.

**5.2 — Update index.md**

Voeg de nieuwe pagina toe aan `index.md` onder de juiste categorie als:
`- [[kebab-slug|Vraag of titel]] — één zin beschrijving`

**Waarom:** index.md is de inhoudscatalogus van de wiki. Elke nieuwe pagina moet erin staan om orphan te voorkomen.

**5.3 — Voeg een log-entry toe**

Voeg aan het einde van `log.md` toe:
`## [YYYY-MM-DD] analysis | [Vraag of titel]`
`Antwoord gearchiveerd als wiki/analysis/[slug].md na gebruikersvraag.`

**Waarom:** log.md is append-only chronologisch record. Iedere wijziging aan de wiki hoort erin.

**5.4 — Voeg een one-liner toe aan de juiste quick-index**

Beslisregel:
- Synthese die uitleg geeft over een named concept (bijv. een diepgaande beschrijving van Data Vault 2.0) → `wiki/concepts-index.md`
- Synthese die bronnen vergelijkt of een procedurele Q&A beantwoordt (bijv. een PRD-werkwijze) → `wiki/sources-index.md`
- Bij twijfel: `wiki/sources-index.md`

Formaat one-liner:
`- [[kebab-slug|Title]] (YYYY-MM-DD) — eerste zin van ## Summary (≤160 tekens)`

**Waarom:** Quick-indexes geven per-rij context zodat de query-workflow later de juiste 3-5 pagina's kan selecteren zonder tientallen pagina's te openen.

**5.5 — Roep de qmd `update`-tool aan**

Roep `mcp__plugin_myrag-wiki_qmd-feat__update` aan (of `mcp__qmd-feat__update` bij project-MCP) zodat de nieuwe pagina direct doorzoekbaar is.

**Waarom:** qmd indexeert niet automatisch — zonder expliciete update-aanroep is de nieuwe pagina onzichtbaar voor toekomstige zoekopdrachten.
