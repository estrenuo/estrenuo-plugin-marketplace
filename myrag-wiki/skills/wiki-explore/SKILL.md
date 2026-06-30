---
name: wiki-explore
description: |
  Gebruik deze skill wanneer de gebruiker wil verkennen welke content de wiki bevat
  of hoe de wiki gestructureerd is. Triggerwoorden: "overview", "graph", "gaps",
  "overzicht", "verbindingen", "wat ontbreekt", "show wiki structure", "wat staat er
  in de wiki", "welke pagina's zijn het meest verbonden", en informele varianten.

  Triggerwoorden voor recent-modus: "recent", "recentelijk", "laatste activiteit",
  "wat is er gedaan", "wat heb je gedaan", en informele varianten.

  Deze skill triggert NIET op kennisvragen over wiki-content ("wat is X?",
  "hoe werkt Y?") — gebruik daarvoor wiki-query. De skill triggert ook NIET op
  wiki-sessiestart-commando's ("wiki start", "open wiki") — gebruik daarvoor wiki-start.
  De skill triggert ook NIET op onderhoudsvragen ("lint", "health check") — gebruik
  daarvoor wiki-lint.
allowed-tools: Read Bash
---

# wiki-explore

**Afdwinging:** Gebruik nooit Write- of Edit-tools in deze workflow.
De explore-workflow is strikt read-only. Alle modus-stappen lezen bestaande bestanden;
geen enkel stap schrijft naar de wiki.

## Bepaal de modus

Lees de gebruikersinput en dispatch naar één van de vier secties hieronder.
Gebruik de tabel als disambiguator bij twijfel.

Als de input meerdere intenties bevat, volg deze prioriteit in plaats van te
proberen alles tegelijk te beantwoorden:
- recent > graph > gaps > overview

Als de intentie onduidelijk blijft, vraag om verduidelijking.

Gebruik de volgende regels om mixed-intentvragen te behandelen:
- Als een query zowel recente activiteit als structuurinformatie wil, kies dan
  `recent`.
- Als een query zowel linkanalyse als dekking vraagt, kies dan `graph` als de
  focus op relaties ligt, anders `gaps`.

| Gebruiker vraagt naar... | Modus |
|--------------------------|-------|
| Wat staat er in de wiki / overzicht van content | overview |
| Verbindingen tussen pagina's, hubs, orphans | graph |
| Wat ontbreekt, ondervertegenwoordigd, gaps | gaps |
| Recente activiteit, wat is er gedaan, laatste wijzigingen | recent |

**Ambigue grensgevallen:**
- "Wat mist er in de wiki over onderwerp X?" — noem een specifiek concept, entiteit of zoekterm.
  Dat is een wiki-query-vraag. Bijvoorbeeld: "Wat mist er in de wiki over climate
  change?" is query; "Wat mist er in de wiki qua documentatie over het hele
  onderwerp energie?" kan gaps zijn als het om de algemene dekking gaat.
- Als de vraag alleen gaat over hiaten in de algemene wiki-structuur of
  thema's zonder een expliciet genoemd onderwerp, gebruik `gaps`.
- "Show me orphan pages" → graph-modus (orphan-detectie), niet gaps.

---

## Modus A: overview

**Stap 1: Lees index.md**
Lees `index.md`. Waarom: index.md is de canonieke inhoudsopgave van de wiki —
zonder dit overzicht kun je niet rapporteren wat er in de wiki staat.

**Stap 2: Rapporteer samenvatting**
Geef een samenvatting met: aantal pagina's per categorie, meest actieve clusters,
recentste activiteit op basis van de pagina-beschrijvingen.
Waarom: de gebruiker wil een mentaal model van de wiki, geen ruwe dump —
een gestructureerde samenvatting is bruikbaarder dan een lijst van bestandsnamen.

---

## Modus B: graph

**Stap 1: Tel inbound links per pagina**
Voer de Bash-commando's uit uit
`references/graph-logic.md` (sectie Inbound-link-teller).
Waarom: Obsidian heeft geen CLI voor link-graafanalyse; grep over `wiki/**/*.md` is
de enige manier om inbound-link-tellingen te berekenen zonder externe tools.

**Stap 2: Detecteer orphan-pagina's**
Voer de Bash-commando's uit uit
`references/graph-logic.md` (sectie Orphan-detector).
Waarom: orphan-pagina's zijn onzichtbaar in normale navigatie en verraden
structuurproblemen of vergeten content.

**Stap 3: Bepaal top-5 hubs en alle orphans**
Selecteer uit de uitvoer van stap 1 de 5 meest gelinkte pagina's (hubs).
Verzamel uit stap 2 alle pagina's met 0 inbound links.
Waarom: hubs en orphans zijn de twee meest informatieve structuurindicatoren —
ze onthullen de ruggengraat en de blinde vlekken van de wiki.

**Stap 4: Rapporteer**
Beschrijf hubs en orphans met bestandspad, type (entity/concept/source/analysis)
en een korte beschrijving. Lees maximaal 5 orphan-pagina's kort in voor context als
het er minder dan 10 zijn.
Waarom: namen alleen zijn onvoldoende — type en samenvatting per pagina maken de
output bruikbaar voor vervolgacties.

---

## Modus C: gaps

**Stap 1: Lees concepts-index.md en sources-index.md**
Lees `wiki/concepts-index.md` en `wiki/sources-index.md`.
Waarom: de quick-indexes geven de breedste dekking van wat er WEL is —
ze zijn de juiste basislijn voor het identificeren van wat ontbreekt.

**Stap 2: Lees index.md**
Lees `index.md` voor het clusteroverzicht.
Waarom: index.md onthult welke thematische clusters relatief klein of afwezig zijn
vergeleken met hun verwachte belang in dit kennisdomein.

**Stap 3: Rapporteer ondervertegenwoordigde gebieden**
Noem concepten, thema's of brontypen die ontbreken of sterk ondervertegenwoordigd zijn.
Waarom: een kwalitatief oordeel over de gaten is waardevoller dan een mechanische check —
de gebruiker wil weten wat de wiki *mist*, niet alleen wat er *is*.

**Opmerking:** Gaps-modus rapporteert alleen — geen fixstappen, geen vragen.
Voor onderhoud met fixes: gebruik wiki-lint.

---

## Modus D: recent

**Stap 0: Detecteer optioneel typefilter**
Controleer of de gebruikersinput een activiteitstype bevat. Herkende tokens
(hoofdletterongevoelig):
- `ingest` of `ingests` → filter op type `ingest`
- `query` of `queries` of `vraag` of `vragen` → filter op type `query`
- `lint` of `lints` of `health` of `healthcheck` → filter op type `lint`
- `update` of `updates` of `wijziging` of `wijzigingen` → filter op type `update`
- `analysis` of `analyses` of `analyse` of `analyses` → filter op type `analysis`

Sla het gevonden type op als `typefilter` (of `geen` als niets herkend).
Waarom: de gebruiker kan zowel "recent lint" als "recente ingests" typen en wil
gefocuste output zonder door niet-relevante entries te hoeven scrollen.

**Stap 1: Lees log.md**
Lees `log.md` (volledig bestand).
Waarom: log.md is het append-only chronologisch register van alle wiki-activiteit —
het is de enige betrouwbare bron voor een accuraat overzicht van recente wijzigingen.

**Stap 2: Selecteer recente entries**
Selecteer de meest recente entries. Gebruik de volgende heuristiek:
- Standaard: alle entries van de laatste 7 kalenderdagen, of minimaal de laatste 10
  entries als er in 7 dagen minder dan 10 zijn.
- Als de gebruiker een specifiek getal noemde ("laatste 5 activiteiten") → gebruik dat getal.

Pas daarna het typefilter toe: als `typefilter` niet `geen` is, behoud alleen de
entries waarvan het type overeenkomt met `typefilter`. Pas de selectieheuristiek
opnieuw toe als na filtering minder dan 10 entries overblijven en er meer entries
in de log staan (ga verder terug).
Waarom: filter na selectie voorkomt een leeg overzicht bij actieve periodes
met gemengde types; terugkijken bij te weinig resultaten herstelt de minimumdrempel.

**Stap 3: Rapporteer in leesbaar formaat**
Groepeer de geselecteerde entries per kalenderdag, nieuwste dag eerst.
Sorteer binnen elke daggroep op activiteitstype in deze vaste volgorde:
ingest, query, lint, update, analysis.
Per entry: type (ingest/query/lint/update/analysis) en de one-line body.
Sluit af met een korte samenvatting: totaal entries getoond, periode gedekt,
en indien van toepassing: welk typefilter actief was.
Waarom: type-sortering binnen een dag maakt het overzicht scanbaar bij hoge
activiteitsdichtheid — ingest en query verschijnen altijd bovenaan als meest
frequente types, wat het patroon voorspelbaar maakt.

**Opmerking:** Recent-modus rapporteert alleen — geen fixstappen, geen vragen.
