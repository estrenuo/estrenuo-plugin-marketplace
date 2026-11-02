---
name: wiki-ingest
description: |
  Gebruik deze skill wanneer de gebruiker nieuwe of bijgewerkte bronnen in de wiki
  wil verwerken. Dit omvat:
  - bestandsingest uit `raw/` zoals `*.md`, `*.pdf`
  - import van documenten in de wiki-structuur
  - bijwerken van bestaande wiki-entiteiten/concepten op basis van nieuwe bronnen
  - het bijwerken van `index.md`, `wiki/ingest-state.md`, `log.md`, en quick-indexes

  Niet voor:
  - vragen over wiki-inhoud of betekenis van pagina's (→ wiki-query)
  - lint- of kwaliteitscontroles zonder ingestactie (→ wiki-lint)
  - algemene wiki-overzichten of grafiekanalyses (→ wiki-explore)

  Typische triggers: "ingest", "verwerk bronnen", "nieuwe bestanden verwerken",
  "voeg dit toe aan de wiki", "ingest" plus een bestandsnaam, "verwerk nieuwe bronnen",
  "scan de raw-map", "verwerk dit artikel", of informele varianten daarvan.
allowed-tools: Read, Write, Edit, Bash, Task, WebFetch, mcp__plugin_context7_context7__query-docs, mcp__plugin_context7_context7__resolve-library-id
---

# wiki-ingest

Je bent de wiki-onderhouder. Codificeer de 10-staps ingest-workflow als rigide checklist. Sla geen stap over, ook niet als de bron al bekend lijkt.

---

## Stap 0 — Session state lezen (context-log)

Lees `wiki/context-log.md` aan het begin van elke ingest-operatie.

- Als het bestand een sessie-ID bevat die overeenkomt met de huidige sessie: sla bestanden over die al als "Verwerkt" staan. Meld dit aan de gebruiker.
- Als het bestand een ander sessie-ID bevat of leeg is: ga normaal verder.

Dit voorkomt dubbele verwerking wanneer de ingest-skill meerdere keren in dezelfde sessie wordt aangeroepen.

---

## Stap 1 — Detectie (auto-modus)

Detecteer welke bestanden verwerkt moeten worden voordat je begint.

**Scan raw/:**
```bash
find raw/ -maxdepth 1 -type f \( -name "*.md" -o -name "*.pdf" \) | sort
```
Sla `raw/assets/` altijd over — dit zijn afbeeldingen, geen bronnen (INGS-06).

**Vergelijk met wiki/ingest-state.md.** Lees het bestand en classificeer elk gevonden bestand.
Zie `references/detection-logic.md` voor de exacte regels:
- De Morgan-regel (mtime ÉN hash — niet alleen mtime)
- Alle 4 detectiemodi: New / Modified / Unchanged / Deleted
- Bash-commando's voor mtime en hash
- Multi-page check bij Modified

**Toon classificatie vóór je begint:**
```
New (N): [namen]
Modified (N): [namen]
Unchanged (N): [namen]
Deleted/orphan (N): [namen]
```

Verwerk alleen New en Modified. Vraag bij Deleted altijd bevestiging vóór actie.

**Bereken de batch-count (INGS-01):**

`count = aantal New + aantal Modified` — dit is het aantal bronnen dat in deze run verwerkt wordt. Multi-page raws (één raw die meerdere wiki-pagina's voedt) tellen als 1 bron, ongeacht hoeveel wiki-pagina's geüpdatet worden. De count staat in het rapport; hij bepaalt niets anders.

Force-ingest (`ingest <bestandsnaam>`) heeft altijd `count = 1`.

---

## Stap 2 — Quick-indexes: altijd regenereren (INGS-01)

`wiki/sources-index.md` en `wiki/concepts-index.md` hebben één eigenaar: het script `${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py`. Het overschrijft beide bestanden volledig op basis van frontmatter en `## Summary`.

- Bewerk de quick-indexes **nooit** met de hand. De volgende run overschrijft handwerk.
- Bij `count ≥ 1`: draai na de batch eenmalig `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py"` (Stap 9.5), vóór `qmd update`. Het script schrijft alleen als er iets veranderde en duurt minder dan een seconde.
- Bij `count = 0`: geen ingest, geen regen, geen qmd update. Alleen het Stap 5-rapport.

---

## Stap 3 — Force-ingest modus

Als de gebruiker `ingest <bestandsnaam>` geeft, overschrijft deze stap Stap 1.
Force-ingest springt direct naar verwerking van het opgegeven bestand zonder
de detectiepad van Stap 1.

Gebruik dit voor geforceerde herverwerking ongeacht mtime/hash-status.

- Als het bestand niet bestaat in `raw/`: geef een foutmelding en stop — geen verdere stappen.
- Als het bestand meerdere wikilinks heeft in ingest-state.md: voer de multi-page dialoog uit vóór Stap 4 (zie Multi-page geval in Stap 4).
- Genereer altijd een volledig rapport via Stap 5, ook bij force-ingest van één bestand.
- `count = 1` altijd.

**PDF-bronnen — delegeer naar `pdf-ingest-agent`:** als het te verwerken bestand
een `.pdf` is (geldt voor zowel auto-modus als force-ingest), roep de Task tool
aan met `subagent_type: pdf-ingest-agent` en geef het PDF-pad als input. De
agent doet chunked reading (max 20 pagina's per call) en voert de volledige
ingest-workflow uit, behalve de quick-indexes. Sla Stap 4 voor dit specifieke
bestand over en neem het resultaat van de agent op in het Stap 5-rapport. De
regen in Stap 9.5 draait na de hele batch, ook voor de PDF.

---

## Stap 4 — Batch-loop ingest-uitvoering (INGS-03)

**Fout-afhandeling per bestand:**
Als een bestand niet verwerkt kan worden (onleesbaar bestand, write-fout, onverwachte conditie), vang de fout op en ga door met het volgende bestand in de batch. Breek de batch nooit af vanwege één bestand. Noteer per mislukt bestand: de bestandsnaam en een korte foutmelding. Deze notities verwerkt Stap 5 naar de per-bestand tabel in het rapport.

Waarom: fout-abort veroorzaakt onvolledige batches en vereist handmatig herstart. Per-file continuering is robuuster en minder belastend voor de gebruiker.

Itereer over de werkverzameling (alle New + Modified bestanden uit Stap 1) en voer voor **elk** bestand de **ingest-stappen 1-9** (uit `references/ingest-steps.md`) sequentieel uit. De gebruiker hoeft het commando niet per bestand te herhalen — de hele batch verwerkt in één run.

De stappen 1-9 worden per bestand uitgevoerd. Stap 9.5 (regen quick-indexes) en Stap 10 (qmd update) zijn post-batch stappen — ze draaien eenmalig na afronding van alle bestanden.

Volledige stappen met why-zinnen en format-specs in `references/ingest-steps.md`.

**Samenvatting:**
1. Lees het bronbestand volledig (skip raw/assets/)
2. Bespreek 2-5 kernpunten — **wacht op bevestiging gebruiker vóór schrijven**
3. Schrijf/update wiki/sources/YYYY-MM-DD-slug.md
4. Update wiki/entities/*.md (nieuwe info, tegenstrijdigheden → ## Open questions)
5. Update wiki/concepts/*.md (idem) — **Stap 5a: canonical-doc-check verplicht** voor feitelijk-klinkende technische claims uit derivative bronnen over Claude Code, MCP, Task-tool of memory. Eén check per claim vóór schrijven; bij tegenspraak landt de claim onder `## Open questions` in plaats van als feit. Details in `references/ingest-steps.md`.
6. Update index.md (entry toevoegen of verversen)
7. (vervallen) Quick-indexes nooit met de hand bewerken — zie Stap 9.5
8. Append aan log.md (type: ingest of update)
9. Update wiki/ingest-state.md (mtime, hash, wikilink met `\|`-escape, datum)
9.5. (Post-batch, altijd bij count ≥ 1) Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py"`
10. Draai via Bash `"$HOME/.local/bin/qmd" update && "$HOME/.local/bin/qmd" embed` — altijd als laatste stap, post-batch

**Multi-page geval:** Als Modified bestand meerdere wikilinks heeft in de Source page cel, voer dan de multi-page dialoog uit vóór stap 2. Details in `references/ingest-steps.md`.

---

## Stap 5 — Afsluitend rapport

Na verwerking van alle bestanden: genereer het rapport met 7 verplichte elementen.
Zie `references/report-format.md` voor het volledige template.

Minimaal vereist (INGS-07):
- **Tellingen:** N nieuw | N bijgewerkt | N ongewijzigd | N verwijderd | N mislukt
- **Per-bestand uitkomsten:** één tabelrij per bestand (ook ongewijzigde) met uitkomst en eventuele foutmelding
- **Quick-indexes:** geregenereerd (bijgewerkt / ongewijzigd) of n.v.t. bij count = 0
- **Pages touched:** welke pagina's aangemaakt of bijgewerkt
- **Contradictions found:** tegenstrijdigheden (of: Geen)
- **Stubs created:** nieuwe stubs (of: Geen)
- **Meest interessante bevinding:** nooit weglaten
- **Suggesties voor vervolgvragen:** aanbevolen maar niet verplicht

---

## Stap 5b — Session state schrijven (context-log)

Schrijf `wiki/context-log.md` na elke ingest-operatie:

| Veld | Waarde |
|---|---|
| Datum | huidige datum (YYYY-MM-DD) |
| Sessie-ID | sessie-identifier |
| Verwerkt | lijst van verwerkte bestandsnamen |
| Overgeslagen | lijst van overgeslagen bestanden (ongewijzigd of al verwerkt) |
| Open | eventuele openstaande items (mislukte bestanden, vragen) |

Bij een nieuwe sessie (ander sessie-ID): overschrijf de tabel volledig.

---

## Stap 6 — Optioneel: cluster-tags opschonen (post-batch)

Na een grote batch (count ≥ 5) of wanneer het Stap 5-rapport meldt dat nieuwe
sources in cluster "Overig" zijn beland: stel de gebruiker voor om de
`source-cluster-tagger` agent te draaien.

- Roep de Task tool aan met `subagent_type: source-cluster-tagger`
- De agent her-evalueert "Overig"-sources en wijst betere clustertags toe in
  de frontmatter van de bronpagina's
- Draai daarna zelf opnieuw
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py"`, zodat de
  nieuwe tags in `sources-index.md` landen
- Doe dit vóór `qmd update` als de gebruiker akkoord gaat; anders sla over

---

## Kwaliteitsregels

- Maak geen tweede bronpagina voor een al-getrackte raw — edit de bestaande rij
- Stap 2 (bespreek met gebruiker) nooit overslaan
- `stat -f` is macOS BSD-syntax — deze skill werkt alleen op macOS
- ingest-state.md tabel: gebruik `\|` als pipe-escape in wikilinks binnen tabelcellen
- Bewerk `wiki/sources-index.md` en `wiki/concepts-index.md` nooit met de hand; alleen `regen-quick-indexes.py` schrijft ze
