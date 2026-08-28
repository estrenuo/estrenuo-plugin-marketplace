# wiki-lint: Stub-detectie (LINT-01)

Referentie voor Stap 2 van wiki-lint. Beschrijft hoe vulbare stubs gedetecteerd worden,
welke drempel gebruikt wordt, en hoe de resultaten aan de gebruiker gepresenteerd worden.

---

## Definitie: vulbare stub

Een stub is vulbaar als aan beide voorwaarden is voldaan:

1. **Stubs met tag**: het bestand heeft `tags: [stub]` in frontmatter (of `stub` als onderdeel van een tags-lijst)
2. **Wiki-kennis aanwezig**: qmd-query op het stub-onderwerp retourneert ≥2 resultaten
   met `score ≥ 0.5` die **niet zelf een stub zijn** (geen `tags: [stub]` in frontmatter)

Als één van beide condities niet geldt, is de stub **niet vulbaar** in deze run.

---

## Detectieprocedure

### Stap A — Vind alle stub-bestanden

```bash
grep -rl "stub" wiki/ --include="*.md" | sort
```

Verfijn: controleer voor elk gevonden bestand of `stub` daadwerkelijk in de `tags:`-regel staat
(niet elders in de tekst). Gebruik:

```bash
grep -l "tags:.*stub\|stub.*tags:" wiki/path/to/file.md
```

Of visueel: open de frontmatter van elk kandidaat-bestand en controleer `tags:`.

### Stap B — Bepaal het onderwerp per stub

Lees de stub-pagina. Het onderwerp staat in:
- `title:` frontmatter (primair)
- De eerste zin van de stub-tekst als de title generiek is

### Stap C — Bevraag de wiki per stub

Roep `mcp__plugin_myrag-wiki_qmd-feat__query` aan voor elke stub met:

```
searches: [{type: 'lex', query: '<title>'}, {type: 'vec', query: '<title>'}]
intent: 'bestaande wiki-kennis over <title>'
minScore: 0.5
```

Tel het aantal resultaten waarbij:
- score ≥ 0.5
- het resultaat zelf geen stub is (`tags: [stub]` afwezig)
- het resultaat niet de stub-pagina zelf is

Drempel: **≥2 gekwalificeerde resultaten** → stub is vulbaar.

### Stap D — Noteer bronnen per vulbare stub

Voor elke vulbare stub: bewaar (a) de **bestandsnamen** (paden) van de top-3 resultaten
(op score) als "bronnen die de stub kunnen vullen", én (b) het **totale aantal
gekwalificeerde resultaten** uit Stap C als `bron-count`.

Gebruik `bron-count` als rankingcriterium bij de presentatielijst: bij >10 vulbare
stubs worden de stubs met het hoogste `bron-count` als eerste gepresenteerd.

---

## Presentatietemplate

Presenteer de lijst ná het lint-rapport (na de 7 standaard-checks) als volgt:

```
## Vulbare stubs (LINT-01)

Op basis van beschikbare wiki-kennis kunnen de volgende stubs gevuld worden:

N. [[stub-bestandsnaam|Stub-titel]]
   Onderwerp: <title uit frontmatter>
   Bronnen: [[bron-1|Titel 1]], [[bron-2|Titel 2]], [[bron-3|Titel 3]]

[herhaal per vulbare stub]

Geen vulbare stubs gevonden → "Geen stubs gevonden die gevuld kunnen worden op basis van huidige wiki-kennis."
```

Sluit de lijst af en ga naar de procedure in `## Goedkeuringsmodus` hieronder.

---

## Goedkeuringsmodus

Na de presentatielijst delegeert de skill naar:

`approval-modes.md`

Dat bestand bevat de keuzegate (individueel A vs. bulk B), de per-stub ja/nee-loop (LINT-02),
de bulk-loop (LINT-03), de vulprocedure, en de randgevallen. Voer hier geen eigen
goedkeuringslogica uit — volg uitsluitend approval-modes.md.

---

## Randgevallen

| Situatie | Behandeling |
|----------|-------------|
| Geen stub-bestanden in wiki/ | Sla Stap B t/m D over; rapporteer "Geen stubs gevonden" |
| Stub heeft geen title in frontmatter | Gebruik bestandsnaam (zonder .md) als onderwerp |
| qmd retourneert 0 resultaten voor stub | Stub niet vulbaar; niet opnemen in lijst |
| Alle resultaten zijn zelf stubs | Stub niet vulbaar; niet opnemen in lijst |
| Meer dan 10 stubs gevonden | Verwerk alle stubs maar begrens de presentatielijst tot de top-10 (hoogste aantal bronnen) |
