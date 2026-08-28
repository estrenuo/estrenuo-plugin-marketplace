# wiki-lint: Goedkeuringsmodi (LINT-02, LINT-03)

Referentie voor Stap 2b van wiki-lint. Beschrijft de keuzegate (A/B/niets),
de per-stub ja/nee-loop (Modus A, LINT-02), de bulk-loop (Modus B, LINT-03),
de vulprocedure, en de randgevallen.

---

## Keuzegate-instructie

Toon dit blok na de stub-presentatielijst (alleen als er ≥1 vulbare stub is):

```
Op basis van de lijst hierboven zijn er N vulbare stubs gevonden.

Hoe wil je verder?
A) Individuele goedkeuring — ik vraag per stub of je hem wil laten vullen (ja/nee)
B) Bulk-goedkeuring — alle N stubs worden direct gevuld zonder verdere bevestiging

Typ 'A', 'B', of 'niets' om dit over te slaan.
```

Antwoord-interpretatie:

| Antwoord              | Actie                                                                                                    |
|-----------------------|----------------------------------------------------------------------------------------------------------|
| 'A' (of 'a')          | Ga naar Modus A                                                                                          |
| 'B' (of 'b')          | Ga naar Modus B                                                                                          |
| 'niets' of lege input | Sla vulling over; ga naar Stap 3                                                                         |
| Onduidelijk           | Herhaal de keuzevraag eenmalig met "Onbekende keuze. Typ 'A', 'B', of 'niets'." Bij opnieuw onduidelijk → behandel als 'niets' |

---

## Modus A: Individuele goedkeuring (LINT-02)

Per-stub loop. Herhaal het volgende voor elke stub in de vulbare-stub-lijst, één voor één:

1. Presenteer de stub:
   ```
   Stub N/[totaal]: [[slug|Titel]]
   Bronnen: [[bron-1|Titel 1]], [[bron-2|Titel 2]], [[bron-3|Titel 3]]
   Wil je deze stub laten vullen? (ja/nee/stop)
   ```
2. Wacht op antwoord.
3. Interpreteer:

   | Antwoord                        | Actie                                               |
   |---------------------------------|-----------------------------------------------------|
   | 'ja' / 'j' / 'yes' / 'y'       | Voeg stub toe aan te-vullen-lijst; ga naar volgende |
   | 'nee' / 'n' / 'no' / 'skip'    | Sla over; ga naar volgende stub                     |
   | 'stop' / 'klaar' / 'genoeg'     | Stop de loop; verwerk wat al goedgekeurd is         |
   | Onduidelijk                     | Herhaal de vraag voor dezelfde stub                 |

4. Na de laatste stub (of 'stop'): voer de vulprocedure uit voor alle goedgekeurde stubs.

---

## Modus B: Bulk-goedkeuring (LINT-03)

Geen verdere interactie per stub. Zet alle vulbare stubs direct op de te-vullen-lijst.
Voer de vulprocedure hieronder uit voor elke stub in de lijst, zonder tussenvragen.

---

## Vulprocedure (beide modi)

Voer voor elke stub op de te-vullen-lijst de volgende stappen uit in exacte volgorde:

1. **Lees de top-3 bronpagina's** (de paden genoteerd in Stap D van de stub-detectie).
2. **Genereer prose**: schrijf een `## Summary` (2-4 zinnen) en een `## Details` (substantieel,
   op basis van de bronnen). Gebruik uitsluitend piped wikilinks: `[[slug|Display Text]]` —
   nooit bare `[[Display Text]]` conform de wikilink-verplichting in CLAUDE.md.
3. **Telcheck**: tel de woorden in `## Details`. Als het aantal < 100 woorden:
   - Schrijf de stub NIET. Laat `tags: [stub]` onaangepast.
   - Noteer: "Stub [titel] onvoldoende gevuld — handmatig controleren."
   - Ga door naar de volgende stub.
4. **Pas frontmatter aan** (alleen na geslaagde telcheck):
   - Verwijder `stub` uit de tags-lijst (laat overige tags intact).
     Voorbeeld: `tags: [stub, ai, privacy]` → `tags: [ai, privacy, technologie]`
     (voeg relevante inhoudstags toe die je afleidt uit de bronpagina's,
     maar gooi bestaande niet-stub tags niet weg).
   - Update `updated:` naar vandaag (YYYY-MM-DD).
   - Vul `sources:` aan met de slugs van de gebruikte bronpagina's.
5. **Patch quick-index**: voeg/update de one-liner voor deze pagina in `wiki/sources-index.md`
   of `wiki/concepts-index.md` (afhankelijk van het type: source vs. concept).
   Format: `- [[slug|Titel]] (datum, auteur) — eerste zin van ## Summary (≤160 tekens)`.
6. Voeg de stub toe aan de gevuld-lijst voor de log-entry.
7. **Herbouw qmd-index**: roep `mcp__plugin_myrag-wiki_qmd-feat__update` aan ná de laatste stub in de loop
   (niet na elke individuele stub), maar alleen als ≥1 stub daadwerkelijk gevuld is.

Na alle stubs: schrijf één samenvattende entry aan `log.md`:
```
## [YYYY-MM-DD] lint | Stub-vulling: N gevuld, M overgeslagen (LINT-02/03)
```
Vermeld per overgeslagen stub de reden (gebruiker koos 'nee' / telcheck mislukt / bronpagina onleesbaar).

---

## Randgevallen

| Situatie                            | Behandeling                                                                         |
|-------------------------------------|-------------------------------------------------------------------------------------|
| Lege vulbare-stubs-lijst            | Keuzegate NIET tonen; ga direct naar Stap 3 (zie SKILL.md Stap 2b)                |
| Onduidelijk keuzegate-antwoord      | Herhaal eenmalig; bij opnieuw onduidelijk → 'niets' als default                   |
| Modus A: 'stop' halverwege          | Vul wat al goedgekeurd is; rapporteer welke stubs overgeslagen zijn                |
| Telcheck mislukt (< 100 woorden)    | Stub ongewijzigd laten; rapporteer als 'niet gevuld' in log-entry                  |
| Bronpagina onleesbaar               | Log als 'failed'; ga door naar volgende stub                                       |
| Meer dan 10 stubs (Phase 7 limiet)  | Alleen de gepresenteerde top-10 worden aangeboden voor vulling                     |
| Wikilink zonder piped syntax        | VERBODEN in gegenereerde content — altijd `[[slug|Display Text]]`                  |
| ≥1 stub gevuld maar Stap 4 = niets  | qmd update is al uitgevoerd in vulprocedure stap 7; Stap 5 hoeft niet opnieuw     |
