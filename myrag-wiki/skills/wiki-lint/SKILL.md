---
name: wiki-lint
description: |
  Gebruik deze skill wanneer de gebruiker vraagt om een lint-pass of health check
  van de wiki. Triggerwoorden: "lint", "health check", "wiki controleren",
  "check de wiki", "zijn er kapotte links?", "wiki health", "wiki doorlichten",
  "orphan pages", "broken links controleren", of andere zinnen die expliciet
  verwijzen naar controle van wiki-structuur, links of kwaliteit.
allowed-tools: Read Grep Bash Edit Write Task mcp__plugin_myrag-wiki_qmd-feat__query mcp__qmd-feat__query
---

# wiki-lint

## Hoofdworkflow

1. Scan de wiki met algoritmische en beoordelingschecks.
2. Identificeer vulbare stubs.
3. Rapporteer bevindingen gesorteerd op prioriteit.
4. Vraag welke items de gebruiker nu wil fixen.
5. Voer geselecteerde fixes uit en werk qmd-index bij als er wijzigingen zijn.

## Stap 1: Scan wiki/ — 10 check-categorieën

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

**Check 8: Quick-index drift — via tool**

Doel: zien of `wiki/sources-index.md` en `wiki/concepts-index.md` nog
overeenkomen met de pagina's. Alleen `regen-quick-indexes.py` schrijft die
bestanden; drift betekent dat iemand ze met de hand heeft bewerkt, of dat
na een wijziging de regen niet is gedraaid.

- Draai vanuit de vault-root:
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py" --check`
- Exit 0: actueel. Exit 1: drift; de uitvoer toont de verschillende regels.
  Schrijft niets.
- Neem drift op onder Middel. De fix is altijd de regen zelf, nooit een
  handmatige correctie in de index.

**Check 9: Registerformaat — via tool**

Doel: kapotte rijen in `wiki/ingest-state.md` vinden vóór ze de detectie breken
(bijvoorbeeld een `|` zonder backslash in een wikilink, waardoor een rij zes
cellen krijgt).

- Draai vanuit de vault-root: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/register.py" ingest-state check --plain`
- Exit 0: schoon. Exit 1: de uitvoer noemt per rij het probleem. Schrijft niets.
- Neem problemen op onder Hoog. De fix is `ingest-state check --fix`
  (herstelt escape en volgorde), nooit een handmatige edit.

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

**Check 10: Bronverificatie** — kandidaten via tool, oordeel via `source-verifier` agent

Doel: de enige check die een claim naast de bron legt in plaats van naast andere
wikipagina's. Checks 1–9 meten consistentie; een fout die vanaf het begin in een hub
staat, komt daar nooit uit, en elke volgende sessie vertrouwt hem. Deze check vangt dat.

- Draai vanuit de vault-root:
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/verify_candidates.py" --limit 5 --plain`
  (JSON zonder `--plain`). Schrijft niets. Het kiest concept- en entity-hubs die nooit
  geverifieerd zijn of na hun `verified:`-datum zijn gewijzigd, meeste inkomende links
  eerst, en geeft per hub de bijbehorende `raw/`-bestanden.
- Roep per geselecteerde hub de Task tool aan met `subagent_type: source-verifier`,
  met het hubpad en de `raw_files`-lijst als input. Hooguit 5 hubs per run: dit is een
  steekproef die over de runs heen de wiki doorloopt, geen volledige audit.
- Neem over in het rapport: per hub het eindoordeel, en elke `afwijkend`-claim met citaat.
- Neem ook over: het aantal hubs met `unresolved_sources` en de lijst
  `untraceable_source_pages` (bronpagina's zonder rij in `wiki/ingest-state.md`). Die
  zijn principieel niet te verifiëren.
- In een onbemande run: alleen rapporteren, geen `verified:` zetten.

---

## Stap 2: Identificeer vulbare stubs (LINT-01)

Zodat de gebruiker een gerichte lijst krijgt van stubs die de wiki al kan vullen,
vóór het algemene rapport gepresenteerd wordt.

Volg de procedure in `references/stub-detection.md`:

- **Stap A**: Vind alle stub-bestanden via Grep op de tag `stub` binnen de
  `tags:`-lijst (zie `references/stub-detection.md` Stap A voor het exacte
  patroon — niet beperkt tot single-tag `tags: [stub]`)
- **Stap B**: Bepaal het onderwerp per stub (uit `title:` frontmatter)
- **Stap C**: Bevraag de wiki per stub via `mcp__plugin_myrag-wiki_qmd-feat__query` (drempel: ≥2 resultaten, score ≥0.5, niet-stubs)
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
per-stub interactie binnen de skill. De agent schrijft geen registers: hij sluit af met
een **Registerblok** (de exacte `register.py`-aanroepen). Voer dat blok ongewijzigd uit
via Bash, vanuit de vault root, controleer de uitvoer, en draai daarna
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py"`.

Na afloop van Stap 2b: ga naar Stap 3.

---

## Stap 3: Rapporteer bevindingen

Zodat de gebruiker een volledig overzicht heeft en zelf kan prioriteren welke problemen
urgent zijn en welke later aangepakt worden.

Presenteer bevindingen als geprioriteerde lijst:

- **Kritiek** (broken links, bare-alias die Obsidian kapotmaakt): direct actie nodig
- **Hoog** (orphans, contradictions, kapotte register-rijen, `afwijkend` uit check 10): problemen die de wiki-integriteit raken; een afwijking van de bron is een fout waarop andere pagina's leunen
- **Middel** (missing cross-refs, stale claims, quick-index drift, `niet gevonden` uit check 10, onherleidbare bronpagina's): kwaliteitsproblemen
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
| Quick-index drift | ja / nee |
| Kapotte register-rijen | X |
| Hubs geverifieerd deze run (verifieerbaar / niet) | X / X |
| Afwijkende claims t.o.v. bron | X |
| Hubs nog nooit of verouderd geverifieerd | X |
| Bronpagina's zonder ingest-state-rij | X |

---

## Stap 4: Vraag welke items nu te fixen

Zodat de gebruiker controle houdt over welke fixes nu plaatsvinden en welke
bewaard worden voor een volgende sessie.

Vraag de gebruiker:
"Welke items wil je nu fixen? Geef nummers op (bijv. '1, 3, 5'), 'alles', of 'niets'."

Wacht op antwoord. Voer alleen de geselecteerde fixes uit.
Documenteer elke fix: welke pagina is aangepast, wat is gewijzigd.

Fixes uit check 10:
- `afwijkend`: corrigeer de claim naar wat de bron zegt, of zet hem onder `## Open questions`
  met het broncitaat als de gebruiker twijfelt. Werk `updated:` bij.
- Eindoordeel verifieerbaar: zet `verified: <vandaag>` in de frontmatter, direct na
  `updated:`. Zet `verified:` nooit op een pagina die je in dezelfde fix hebt
  gecorrigeerd; die wordt bij de volgende run opnieuw gecontroleerd.
- `niet gevonden`: geen automatische fix. Laat de gebruiker kiezen: bron toevoegen aan
  `sources:`, claim verwijderen, of naar `## Open questions`.

Na het uitvoeren van fixes:
- Draai `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/regen-quick-indexes.py"` (schrijft alleen als er iets veranderde; bewerk de quick-indexes nooit met de hand) en daarna `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/register.py" index stats`
- Log via `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/register.py" log --type lint --title "<samenvatting>" --body "<per fix één regel>"` (schrijf nooit zelf in `log.md`)
- Registreer nieuwe concept-, entity- of analysepagina's via `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/register.py" index add --page … --section … --summary …` (schrijf nooit zelf in `index.md`)

---

## Stap 5: Herbouw qmd-index na fixes

Na het uitvoeren van fixes: draai via Bash `"$HOME/.local/bin/qmd" update && "$HOME/.local/bin/qmd" embed` om de qmd-index te herbouwen.
Dit zorgt dat gefixte pagina's direct doorzoekbaar zijn in toekomstige query-sessies.

**Stap 5 wordt ALLEEN uitgevoerd als er daadwerkelijk fixes zijn gedaan** (stap 4 ≠ "niets").
