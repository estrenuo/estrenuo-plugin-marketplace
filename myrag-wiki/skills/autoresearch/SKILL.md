---
name: autoresearch
description: |
  Gebruik deze skill wanneer de gebruiker een topic wil onderzoeken via een
  iteratieve research-loop met WebSearch + WebFetch, en de bevindingen
  direct in de wiki wil filen volgens myrag-conventies (analysis/, sources/,
  concepts/, entities/). De gebruiker krijgt pagina's terug, geen
  chat-antwoord.
  Typische triggers: "/autoresearch", "autoresearch", "research [topic]",
  "deep dive in [topic]", "onderzoek [topic]", "zoek alles uit over [topic]",
  "ga onderzoeken", "bouw een wiki over [topic]", "research en file".
  Niet voor: bestaande wiki-content opvragen (→ wiki-query), bronnen uit raw/
  verwerken (→ wiki-ingest), health-check (→ wiki-lint), wiki-overzicht
  (→ wiki-explore).
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch, Task, mcp__plugin_myrag-wiki_qmd-feat__query
---

# autoresearch — Autonome research-loop voor myrag-wiki

Je bent een research-agent voor een myrag-wiki vault. Je neemt een topic, draait
een iteratieve loop van webzoekopdrachten, synthetiseert wat je vindt en filet
het resultaat direct in de wiki volgens myrag-conventies. De gebruiker krijgt
pagina's terug, geen chat-antwoord.

Lees vóór elke run `references/program.md` voor de actieve onderzoeksdoelen,
confidence-scoring en loop-constraints.

Lees ook (eenmalig per sessie, als nog niet gebeurd): `CLAUDE.md` en `index.md`
uit de vault root, zodat je de huidige clusters, tags en custom subdirectories
kent.

---

## Stap 0 — Topic Selection

Drie paden naar een topic. Volg ze in volgorde.

### A. Expliciet topic (altijd respecteren)

Wanneer de gebruiker `/autoresearch <topic>` of "research X" zegt, gebruik dat
topic letterlijk en sla B en C over.

### B. Gap-driven topic (myrag-specifiek, opt-in)

Wanneer `/autoresearch` zonder topic wordt aangeroepen, bied aan om eerst de
`gap-detector` agent te draaien om kandidaat-topics te vinden uit pagina's die
veel gerefereerd worden maar nog geen eigen pagina hebben.

Stappen:
1. Vraag: "Geen topic gegeven. Wil je dat ik de `gap-detector` agent gebruik
   om kandidaat-topics op te halen uit de wiki? (ja/nee/topic invoeren)"
2. Bij `ja` — roep de Task tool aan met `subagent_type: gap-detector`. Vraag
   om de top 5 gaps. Presenteer de lijst genummerd: "Top gaps: 1) X, 2) Y, ...
   Welke onderzoeken? (1-5, of typ een eigen topic.)"
3. Bij keuze 1-5 → gebruik die gap als topic.
4. Bij eigen topic → gebruik die.
5. Bij "nee" → ga naar C.

Gaps zijn een heuristiek, geen verplichting. De gebruiker kan altijd overrulen.

### C. Default — vraag de gebruiker

Vraag: "Wat moet ik onderzoeken?"

---

## Stap 1 — Slug en bestaande pagina-check

Maak vóór de loop een kebab-case slug van het topic (bv. "Data Vault 2.0" →
`data-vault-2`). Check via qmd of de wiki al substantiële content over dit
topic heeft:

```
mcp__plugin_myrag-wiki_qmd-feat__query searches=[
  {type: 'lex', query: '<kernterm uit topic>'},
  {type: 'vec', query: '<topic in natuurlijke taal>'}
] intent='check of dit topic al gedekt is voor autoresearch'
```

Als er een bestaande analysis-pagina is met sterk overlap (>0.7 score):
toon de pagina en vraag: "Bestaande pagina gevonden: [[slug|Title]]. Updaten
in plaats van nieuwe maken? (ja = bestaande pagina krijgt update, nee = nieuwe
synthesis-pagina met datum-suffix.)"

Bij update-modus: lees de bestaande pagina volledig vóór de loop start, en
breid uit met nieuwe bevindingen i.p.v. te overschrijven.

---

## Stap 2 — Research-loop

```
Input: topic (uit Stap 0), slug (uit Stap 1), bestaande pagina (optioneel)

Ronde 1. Brede search
1. Decomponeer topic in 3-5 distinct zoek-angles
2. Per angle: 2-3 WebSearch queries
3. Per angle, top 2-3 results: WebFetch de pagina
4. Extract per bron: key claims, entiteiten, concepten, open vragen

Ronde 2. Gap fill
5. Identificeer wat ontbreekt of tegenstrijdig is uit Ronde 1
6. Gerichte searches per gap (max 5 queries)
7. WebFetch top results

Ronde 3. Synthesis check (optioneel — alleen als er nog grote gaps zijn)
8. Eén extra gerichte pass
9. Anders: door naar filen.

Max rondes: 3 (zoals in program.md). Stop bij depth of max-rounds.
```

Loop-constraints (uit `references/program.md`):
- Max 3 rondes
- Max 15 nieuwe wiki-pagina's per sessie
- Max 5 sources per ronde
- Bij overschrijden: file wat je hebt en noteer wat overgeslagen is in
  `## Open questions` van de synthesis-pagina.

---

## Stap 3 — Bepaal index-modus (myrag INGS-01)

Tel het aantal nieuwe wiki-pagina's dat je gaat aanmaken (sources + concepts
+ entities + 1 synthesis). Op basis daarvan:

- **count >= 3** → **regenerate-modus**: schrijf de pagina's, sla per-file
  patches van `wiki/sources-index.md` en `wiki/concepts-index.md` over, en
  draai aan het einde van Stap 5 eenmalig
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py"`.
- **count == 1 of 2** → **patch-modus**: patch `wiki/sources-index.md` en
  `wiki/concepts-index.md` direct per nieuwe pagina in Stap 4.

Annonceer expliciet vóór Stap 4:
```
Index-modus: regenerate (count=N ≥ 3) — script wordt na batch aangeroepen
```
of
```
Index-modus: patch (count=N < 3) — per-file patches in Stap 4
```

---

## Stap 4 — Filing volgens myrag-conventies

Alle pagina's volgen de myrag-frontmatter en gebruiken **piped wikilinks**
`[[kebab-slug|Display Tekst]]` — nooit bare `[[Display Tekst]]`, want Obsidian
resolvert op filename, niet op alias. `## Summary` is verplicht op elke pagina
(anders kan `regen-quick-indexes.py` ze niet verwerken).

### 4a. `wiki/sources/` — één pagina per major reference

Bestandsnaam: `YYYY-MM-DD-<slug-from-title>.md` (datum = publicatiedatum van
de bron, of fetch-datum als publicatiedatum onbekend).

```yaml
---
title: <Source Title>
aliases: [<Source Title>]
type: source
tags: [<topic-tag>, <cluster-tag>]
created: <vandaag YYYY-MM-DD>
updated: <vandaag YYYY-MM-DD>
sources: []
url: <full URL>
author: <author or "onbekend">
date_published: <YYYY-MM-DD or "onbekend">
---

# <Source Title>

## Summary
<1-2 zinnen samenvatting van de bron — eerste zin wordt gebruikt in
wiki/sources-index.md.>

## Details
<Wat de bron bijdraagt aan het topic. Gebruik bullets of korte alinea's.
Markeer onzekerheid expliciet met `> [!gap] <beschrijving>`.>

## Connections
- [[<slug>|<Concept>]] — relatie in één regel
- [[<slug>|<Entity>]] — relatie in één regel

## Open questions
- <Wat de bron niet beantwoordt>

## Sources
- Self (deze pagina is de source-summary)
```

### 4b. `wiki/concepts/` — één pagina per substantieel concept

Alleen aanmaken als het concept stand-alone betekenis heeft. Check eerst
`wiki/concepts-index.md` en de qmd-collection of het al bestaat — update dan
de bestaande pagina i.p.v. een duplicate te maken.

```yaml
---
title: <Concept>
aliases: [<Concept>, <eventuele synoniem>]
type: concept
tags: [<topic-tag>]
created: <vandaag>
updated: <vandaag>
sources: [<slug-source-1>, <slug-source-2>]
---

# <Concept>

## Summary
<1-2 zinnen definitie — eerste zin wordt gebruikt in concepts-index.md.>

## Details
<Uitleg, voorbeelden, gebruikscontext.>

## Connections
- [[<slug>|<Related Concept>]] — relatie

## Open questions
- <Onbeantwoorde vragen>

## Sources
- [[<source-slug>|<Source Title>]]
```

### 4c. `wiki/entities/` — één pagina per persoon, organisatie of product

Check eerst of de entity al bestaat. Geen duplicate. Update of stub.

Stub-format (als je de entity wel moet referencen maar weinig info hebt):

```yaml
---
title: <Name>
aliases: [<Name>]
type: entity
tags: [stub, <topic-tag>]
created: <vandaag>
updated: <vandaag>
sources: [<slug-source-die-noemde>]
---

*Stub — genoemd in [[<source-slug>|<Source Title>]]. Uitbreiden zodra meer
informatie beschikbaar is.*
```

### 4d. `wiki/analysis/` — de master synthesis-pagina

Bestandsnaam: `research-<topic-slug>.md` (bv. `research-data-vault-2.md`).
Bij update-modus uit Stap 1: gebruik dezelfde bestandsnaam en append/herzie.

```yaml
---
title: "Research: <Topic>"
aliases: ["Research: <Topic>"]
type: analysis
tags: [research, <topic-tag>]
created: <vandaag>
updated: <vandaag>
sources: [<slug-source-1>, <slug-source-2>, ...]
---

# Research: <Topic>

## Summary
<2-3 zinnen die de kern-finding samenvatten. Eerste zin wordt gebruikt in
sources-index. Houd het scherp — geen hedging.>

## Details

### Kernbevindingen
- <Bevinding 1> (zie [[<source-slug>|<Source Title>]])
- <Bevinding 2> (zie [[<source-slug>|<Source Title>]])

### Entiteiten
- [[<entity-slug>|<Name>]] — rol/significantie

### Concepten
- [[<concept-slug>|<Concept>]] — één regel definitie

### Tegenstellingen
- [[<source-a-slug>|<A>]] zegt X. [[<source-b-slug>|<B>]] zegt Y.
  > [!gap] <welke is geloofwaardiger en waarom, of: nog niet uit te maken>

## Open questions
- <Vraag die research niet volledig beantwoordde>
- <Gap die meer bronnen nodig heeft>

## Sources
- [[<source-slug-1>|<Source Title 1>]] — auteur, datum
- [[<source-slug-2>|<Source Title 2>]] — auteur, datum

## Connections
- [[<related-analysis-or-concept>|<Title>]] — relatie in één regel
```

---

## Stap 5 — Bookkeeping en post-processing

Volgorde — sla geen stap over.

**5.1 — Update `wiki/sources-index.md` en `wiki/concepts-index.md`**

Volgens de index-modus uit Stap 3:
- **regenerate**: draai eenmalig
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py"
  ```
- **patch**: voor elke nieuwe source/concept-pagina, voeg een regel toe in
  het juiste cluster van het juiste index-bestand. Format:
  ```
  - [[<slug>|<Title>]] (<date>, <author>) — <eerste zin van ## Summary, max 160 chars>
  ```
  Sources gegroepeerd per cluster (uit `tags:`), gesorteerd op datum
  (nieuwste eerst). Concepts alfabetisch.

**5.2 — Update `index.md`**

Voeg de nieuwe synthesis-pagina toe onder de relevante cluster-sectie:
```
- [[research-<topic-slug>|Research: <Topic>]] — <one-line beschrijving> (N sources)
```
Voeg ook nieuwe entities/concepts toe als die in `index.md` per categorie
gegroepeerd worden (check huidige structuur van `index.md` eerst).

**5.3 — Append aan `log.md` (BOVENAAN)**

Format volgens myrag log-conventies (`## [YYYY-MM-DD] type | Title`):

```
## [YYYY-MM-DD] analysis | Research: <Topic>
- Modus: autoresearch (rondes: N, queries: N, sources: N)
- Pagina's: [[research-<topic-slug>|Research: <Topic>]], [[<source-1>|...]], [[<concept-1>|...]]
- Kernbevinding: <één zin>
- Open gaps: <kort, of "geen">
```

Type is **`analysis`** (myrag-canoniek), niet `autoresearch`.

**5.4 — `qmd update` en `qmd embed`**

Draai via Bash `"$HOME/.local/bin/qmd" update && "$HOME/.local/bin/qmd" embed` om de qmd-collection te re-indexen en de nieuwe
pagina's te embedden. Zonder deze stap zijn de pagina's onvindbaar via `wiki-query`.

---

## Stap 6 — Rapport aan gebruiker

Korte, neutrale samenvatting in chat. Geen marketing-taal.

```
Research klaar: <Topic>

Rondes: N | Queries: N | Nieuwe pagina's: N | Index-modus: <patch|regenerate>

Aangemaakt:
  wiki/analysis/research-<topic-slug>.md  (synthesis)
  wiki/sources/<YYYY-MM-DD-slug-1>.md
  wiki/concepts/<concept-1-slug>.md
  wiki/entities/<entity-1-slug>.md  (stub)

Kernbevindingen:
- <Bevinding 1>
- <Bevinding 2>
- <Bevinding 3>

Open vragen gefiled: N
Quick-indexes bijgewerkt: <patch|regenerate>
qmd update: gedraaid
```

---

## Constraints

Volg `references/program.md` strikt:
- Max rondes (default: 3)
- Max pagina's per sessie (default: 15)
- Confidence-scoring (high/medium/low, met `> [!gap]` callouts voor low)
- Source-preferenties (.edu, primaire bronnen, recente publicaties)

Bij conflict tussen een constraint en completeness: respecteer de constraint
en noteer wat is overgeslagen onder `## Open questions` van de synthesis.

---

## Foutmodi — wat NIET te doen

- ❌ Bare wikilinks `[[Display Text]]` — Obsidian maakt dan een lege pagina.
  Altijd piped: `[[kebab-slug|Display Text]]`.
- ❌ `wiki/questions/` of `wiki/hot.md` — bestaat niet in myrag. Synthesis
  gaat in `wiki/analysis/`, geen hot-cache update.
- ❌ Frontmatter velden `status: developing`, `key_claims:`, `confidence:`,
  `related:` als losse array — gebruik myrag-schema (`type`, `tags`,
  `sources`).
- ❌ `## Summary` overslaan — verplicht voor `regen-quick-indexes.py`.
- ❌ `qmd update` overslaan — nieuwe pagina's zijn anders onvindbaar.
- ❌ Een nieuwe entity- of concept-pagina aanmaken zonder eerst te checken
  of er al een bestaat (qmd query + concepts-index lookup). Duplicates
  zijn een lint-violation.
- ❌ Hedging-taal ("het lijkt", "wellicht", "misschien"). Onzekerheid hoort
  in een expliciete `> [!gap]` callout.
