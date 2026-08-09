---
name: wiki-lint
description: |
  Gebruik deze skill wanneer de gebruiker vraagt om een lint-pass of health check
  van de wiki. Triggerwoorden: "lint", "health check", "wiki controleren",
  "check de wiki", "zijn er kapotte links?", "wiki health", "wiki doorlichten",
  "orphan pages", "broken links controleren", of andere zinnen die expliciet
  verwijzen naar controle van wiki-structuur, links of kwaliteit.
allowed-tools: Read Grep Bash Edit Write Task mcp__qmd-feat__query mcp__qmd-feat__update
---

# wiki-lint

## Hoofdworkflow

1. Scan de wiki met algoritmische en beoordelingschecks.
2. Identificeer vulbare stubs.
3. Rapporteer bevindingen gesorteerd op prioriteit.
4. Vraag welke items de gebruiker nu wil fixen.
5. Voer geselecteerde fixes uit en werk qmd-index bij als er wijzigingen zijn.

## Stap 1: Scan wiki/ — 7 check-categorieën

Zodat alle structuur- en linkproblemen in de wiki systematisch in kaart worden gebracht
vóór er fixes worden gedaan.

### Blok A — Algoritmische checks (Grep + Bash)

**Check 1+2: Bare-alias & broken wikilinks — via tool (NIET met de hand grep'en)**

Doel: links opsporen die er goed uitzien maar in Obsidian een nieuwe lege pagina
aanmaken (bare-alias), plus links waarvan het doelbestand nergens bestaat (broken).

- Draai vanuit de vault-root:
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wikilinks.py" lint`
  (voeg `--plain` toe voor leesbare output; JSON is default met velden
  `files_scanned`, `by_category`, `results[]`). Exit 1 bij findings, 0 als schoon.
- De tool scant alle wiki-pagina's, deelt findings in `broken-bare` /
  `broken-piped` / `bare-alias`, en geeft per finding een `suggested_fix`
  (de correcte piped link om te plakken).
- De tool handelt de false-positives **zélf** af (code spans, fenced blocks,
  `\|`-tabelescape, `[[index]]`, wiki-root-pagina's zoals `sources-index`) — de
  FP-uitzonderingen hieronder hoeven op deze twee checks niet handmatig toegepast.
- Voor de correcte piped link van willekeurige display-tekst:
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wikilinks.py" resolve "Display Text" --plain`.
- Neem `bare-alias` + `broken-*` findings over in het rapport onder Kritiek.

**Check 3: Orphan pages**

Doel: pagina's die niet bereikbaar zijn vanuit andere wiki-pagina's identificeren.

- Bouw set A: alle bestanden in `wiki/**/*.md`
- Bouw set B: alle wikilink-targets die ergens in `wiki/**/*.md` voorkomen
- Verschil (A minus B) = orphan-kandidaten
- Sluit de volgende beheerbestanden uit van orphan-check
  (navigatie-hubs of management-bestanden zonder verwachte inkomende wikilinks):
  `sources-index.md`, `concepts-index.md`, `ingest-state.md`

**False-positive-uitzonderingen (orphan-check)**

Checks 1+2 handelt de tool zelf af. Voor de orphan-check (Check 3) geldt nog:
zie `references/false-positives.md` voor de volledige lijst van
false-positive-uitzonderingen die vóór rapportage toegepast moeten worden.

---

### Blok B — Judgment-only checks (lezen + redeneren)

**Check 4: Contradictions** — delegeer naar `contradiction-detector` agent

Doel: feitelijke tegenstrijdigheden tussen pagina's opsporen die de wiki misleidend maken.

- Roep de Task tool aan met `subagent_type: contradiction-detector`
- Geef als scope een onderwerp uit recente activiteit (bijv. "recent gewijzigde pagina's"
  of een cluster zoals "Data Vault") — bepaal scope via `log.md` of `updated`-datum
- De agent rapporteert alleen, schrijft niet — neem bevindingen over in het lint-rapport
- Slaag check 4 over als de scope leeg is (geen overlappende onderwerpen recent geraakt)

**Check 5: Missing cross-references** — delegeer naar `cross-reference-sweeper` agent

Doel: impliciete verbanden expliciet maken zodat de wiki beter navigeerbaar wordt.

- Roep de Task tool aan met `subagent_type: cross-reference-sweeper`
- De agent rapporteert eerst geplande wijzigingen en voert ze daarna direct uit;
  daarom: voer Check 5 alleen uit in Stap 4 (fix-fase), niet in Stap 1 (scan-fase)
- Neem het aantal toegevoegde wikilinks over in de tellerstabel als "Missing cross-refs"

**Check 6: Stale claims**

Doel: pagina's markeren waarvan de inhoud verouderd kan zijn door recentere ingest.

- Lees de meest recente 10 entries van `log.md`
- Vergelijk vermelde updates met pagina's die dezelfde onderwerpen behandelen
- Markeer pagina's waarvan de inhoud verouderd kan zijn door recentere ingest

**Check 7: Data gaps** — delegeer naar `gap-detector` agent

Doel: belangrijke concepten zonder eigen pagina signaleren voordat ze tot verwarring leiden.

- Roep de Task tool aan met `subagent_type: gap-detector`
- De agent rapporteert alleen, schrijft niet — neem de top-gaps over in het lint-rapport
  onder "Data gaps"

---

## Stap 2: Identificeer vulbare stubs (LINT-01)

Zodat de gebruiker een gerichte lijst krijgt van stubs die de wiki al kan vullen,
vóór het algemene rapport gepresenteerd wordt.

Volg de procedure in `references/stub-detection.md`:

- **Stap A**: Vind alle stub-bestanden via Grep op `tags: [stub]`
- **Stap B**: Bepaal het onderwerp per stub (uit `title:` frontmatter)
- **Stap C**: Bevraag de wiki per stub via `mcp__qmd-feat__query` (drempel: ≥2 resultaten, score ≥0.5, niet-stubs)
- **Stap D**: Noteer de top-3 bronnen per vulbare stub

Presenteer de lijst aan de gebruiker met het template uit `references/stub-detection.md`.

**Deze stap vult geen stubs** — alleen identificeren en presenteren.
Ga daarna naar Stap 2b.

---

## Stap 2b: Kies goedkeuringsmodus en vul stubs (LINT-02, LINT-03)

Zodat de gebruiker controle houdt over welke stubs gevuld worden en op welke manier,
vóór enige schrijfactie plaatsvindt.

**Als de vulbare-stubs-lijst uit Stap 2 leeg is**: sla Stap 2b volledig over en ga
direct naar Stap 3.

**Als er ≥1 vulbare stub is**: volg de volledige procedure in:
`references/approval-modes.md`

Dat bestand bevat de keuzegate (A/B/niets), de per-stub ja/nee-loop (Modus A, LINT-02),
de bulk-loop (Modus B, LINT-03), de vulprocedure, en de randgevallen.

**Snelpad — delegeer naar `stub-filler` agent**: bij ≥10 vulbare stubs of als de
gebruiker "vul alle stubs" zegt, roep de Task tool aan met `subagent_type: stub-filler`
in plaats van de modus-loop hier ter plaatse uit te voeren. De agent toont alle vulbare
stubs in één overzicht en wacht op goedkeuring vóór schrijven — dat is efficiënter dan
per-stub interactie binnen de skill.

Na afloop van Stap 2b: ga naar Stap 3.

---

## Stap 3: Rapporteer bevindingen

Zodat de gebruiker een volledig overzicht heeft en zelf kan prioriteren welke problemen
urgent zijn en welke later aangepakt worden.

Presenteer bevindingen als geprioriteerde lijst:

- **Kritiek** (broken links, bare-alias die Obsidian kapotmaakt): direct actie nodig
- **Hoog** (orphans, contradictions): structuurproblemen die de wiki-integriteit raken
- **Middel** (missing cross-refs, stale claims): kwaliteitsproblemen
- **Laag** (data gaps): groei-suggesties

Per bevinding: pagina, probleem, aanbevolen actie.

Sluit af met tellerstabel:

| Type | Aantal |
|------|--------|
| Broken links | X |
| Bare-alias kandidaten | X |
| Orphan pages | X |
| Contradictions | X |
| Missing cross-refs | X |
| Stale claims | X |
| Data gaps | X |

---

## Stap 4: Vraag welke items nu te fixen

Zodat de gebruiker controle houdt over welke fixes nu plaatsvinden en welke
bewaard worden voor een volgende sessie.

Vraag de gebruiker:
"Welke items wil je nu fixen? Geef nummers op (bijv. '1, 3, 5'), 'alles', of 'niets'."

Wacht op antwoord. Voer alleen de geselecteerde fixes uit.
Documenteer elke fix: welke pagina is aangepast, wat is gewijzigd.

Na het uitvoeren van fixes:
- Voeg een entry toe aan `log.md` van type `lint` met een samenvatting van de fixes
- Werk `index.md` bij als nieuwe pagina's zijn aangemaakt of hernoemd

---

## Stap 5: Herbouw qmd-index na fixes

Na het uitvoeren van fixes: roep `mcp__qmd-feat__update` aan om de qmd-index te herbouwen.
Dit zorgt dat gefixte pagina's direct doorzoekbaar zijn in toekomstige query-sessies.

**Stap 5 wordt ALLEEN uitgevoerd als er daadwerkelijk fixes zijn gedaan** (stap 4 ≠ "niets").
