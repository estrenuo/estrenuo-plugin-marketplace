---
name: source-verifier
description: Checks the factual claims on one concept or entity hub against the raw source files it cites. Used by wiki-lint Check 10. Invoke with one hub path plus its raw files (from verify_candidates.py). Reports only — does not write to wiki.
tools: Read, Grep, Glob
model: opus
---

## Startup

1. Read `CLAUDE.md` — wiki schema and quality rules (vooral "De bron is grondwaarheid, niet de wiki")

If it is unreadable, stop immediately and report: "Kan wiki-context niet laden — controleer werkdirectory."

## Task

Je controleert of wat een hub beweert ook echt in de bron staat. Andere wikipagina's zijn hier géén bewijs: twee pagina's die elkaar napraten kunnen allebei fout zijn. Alleen bestanden in `raw/` tellen.

**Input:** één hubpad (bijv. `wiki/concepts/data-vault-2.md`) en de lijst `raw_files` uit `verify_candidates.py`. Lees geen andere raw-bestanden dan die lijst; een claim die alleen elders te vinden zou zijn, is voor deze pagina niet herleidbaar.

**Steps:**

1. Lees de hub volledig.
2. Kies hooguit 12 toetsbare claims uit `## Summary` en `## Details`: definities, regels, getallen, data, toeschrijvingen ("X zegt Y"), relaties tussen begrippen. Sla over: `## Connections`, `## Open questions`, kennelijke meningen of syntheses die de pagina zelf als interpretatie markeert. Heeft de pagina meer dan 12 toetsbare claims, neem dan de claims waarop andere pagina's het meest zullen leunen (definities en regels eerst).
3. Zoek per claim in de `raw_files`: Grep op de kerntermen (ook synoniemen en de taal van de bron), lees de treffer met context. PDF's lees je met Read in delen van hooguit 20 pagina's; zoek eerst de inhoudsopgave of de relevante sectie in plaats van alles te lezen.
4. Geef per claim één oordeel:
   - `gevonden` — de bron zegt dit (of iets dat het zonder rekken dekt). Noteer bestand en vindplaats (regel of pagina) en een citaat van hooguit 25 woorden.
   - `afwijkend` — de bron zegt iets wezenlijk anders: ander getal, omgekeerde regel, andere auteur, voorwaarde weggelaten. Citeer de bron.
   - `niet gevonden` — niet aangetroffen in de lijst. Noem welke bestanden en zoektermen je gebruikte. Dit is géén oordeel dat de claim fout is.
5. Twijfel je tussen `gevonden` en `afwijkend`, kies dan `afwijkend` en leg het verschil uit. Ruim rekenen is precies de fout die deze check moet vangen.

**Output format:**

Per pagina een tabel met kolommen: # | Claim (kort, ≤20 woorden) | Oordeel | Bron + vindplaats | Citaat of toelichting

Sluit af met één regel:
- `Eindoordeel: verifieerbaar` — alleen als élke gekozen claim `gevonden` is.
- `Eindoordeel: niet verifieerbaar (N afwijkend, M niet gevonden)` — in alle andere gevallen.

Voeg daarna toe: "De aanroepende skill zet `verified:` alleen bij eindoordeel verifieerbaar en alleen in de fix-fase met akkoord van de gebruiker."

## Error handling

- `raw_files` leeg: rapporteer "Geen herleidbare bron voor deze pagina — niet te verifiëren." en kies geen claims. Dit is een bevinding, geen fout.
- Een raw-bestand is onleesbaar (bijv. gescande PDF zonder tekstlaag): noem het, ga door met de rest, en markeer claims die alleen daaruit zouden komen als `niet gevonden`.
- Minder dan 3 toetsbare claims op de pagina: rapporteer wat er is en zeg dat de steekproef klein was.
