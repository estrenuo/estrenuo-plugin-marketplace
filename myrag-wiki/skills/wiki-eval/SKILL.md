---
name: wiki-eval
description: |
  Gebruik deze skill wanneer de gebruiker wil meten of de wiki iets oplevert
  ten opzichte van zoeken in de bronnen zelf. Triggerwoorden: "wiki eval",
  "eval draaien", "levert de wiki iets op", "meet de wiki", "baseline wiki",
  "wiki vs raw", of een expliciete verwijzing naar eval/questions.md.
  Vergelijkt drie condities (alleen raw, alleen wiki, wiki plus raw) op de
  vaste vragenset en schrijft een resultaatbestand in eval/. Schrijft niets
  in wiki/ of in de registers.
allowed-tools: Read Grep Glob Bash Write Task mcp__plugin_myrag-wiki_qmd-feat__query mcp__qmd-feat__query
---

# wiki-eval

## Waarom deze skill bestaat

Wiki-onderhoud kost elke ingest en elke lint tokens en tijd. Of dat zich terugbetaalt, is
zonder meting een gevoel. Anthropic mat het op een eigen corpus (*The components of agent
memory*, 2026-11-06): alleen zoeken 53%, alleen wiki 48%, wiki plus zoeken 61%, met de
winst vrijwel uitsluitend op vragen die meerdere documenten combineren. Deze skill doet
dezelfde meting op deze vault.

## Input

- Vragenset: `eval/questions.md` in de vault-root. Elke vraag heeft een type (`single` of
  `multi`), bronnen in `raw/` en genummerde criteria, één punt per criterium.
- Wijzig de vragenset nooit tijdens een run. Twee runs zijn alleen vergelijkbaar met
  dezelfde set; meld bij de start het aantal vragen en criteria.

## Stap 1: Drie antwoordrondes, elk in een eigen subagent

Start drie Task-aanroepen (`subagent_type: general-purpose`), parallel. Geef elke agent
alleen de vragen (nooit de criteria of de bronnen-regels) en exact één van deze opdrachten:

- **Conditie A, alleen raw:** "Beantwoord elke vraag uitsluitend uit bestanden in `raw/`.
  Gebruik Grep, Glob en Read; pdftotext via Bash mag voor PDF's. Lees niets in `wiki/`,
  `index.md` of `log.md`, en gebruik qmd niet met de collectie `myrag`."
- **Conditie B, alleen wiki:** "Beantwoord elke vraag uitsluitend uit `wiki/`. Gebruik qmd
  `query` met `collections: [\"myrag\"]` en Read op `wiki/`. Lees niets in `raw/`."
- **Conditie C, wiki plus raw:** "Begin bij de wiki (qmd `myrag`, Read op `wiki/`) en ga naar
  `raw/` wanneer de wiki onvolledig is of je een claim wilt controleren."

Voor alle drie: "Antwoord per vraag in hooguit 150 woorden, met de bestanden die je
gebruikte. Gis niet: wat je niet vond, zeg je. Geef aan het eind per vraag het aantal
tool-aanroepen dat je deed."

Werk vanuit de vault-root. Sla de drie ruwe antwoorden op in
`eval/runs/<datum>/answers-A.md`, `answers-B.md`, `answers-C.md`.

## Stap 2: Blinde beoordeling in een aparte subagent

Hussel per vraag de drie antwoorden naar labels X, Y, Z en bewaar de sleutel in
`eval/runs/<datum>/key.json`. Start één Task (`subagent_type: general-purpose`) met per
vraag: de vraag, de criteria, de bronbestanden, en de drie antwoorden onder X, Y, Z.

Opdracht aan de grader: "Beoordeel per antwoord elk criterium met 1 (gedekt) of 0 (niet
gedekt of fout). Toets tegen de bronbestanden in `raw/`, niet tegen je eigen kennis en
niet tegen `wiki/`. Een antwoord dat iets beweert wat de bron tegenspreekt, krijgt 0 op dat
criterium, ook als de rest klopt. Geef per vraag een tabel: criterium, X, Y, Z, en één regel
toelichting bij elke 0."

De grader ziet nooit welke conditie welk label is.

## Stap 3: Resultaat

Pak de sleutel uit en schrijf `eval/results-<datum>.md` met:

1. Score per conditie als percentage gedekte criteria: totaal, `single`, `multi`.
2. Gemiddeld aantal tool-aanroepen per vraag per conditie (zoals gemeld door de agents).
3. Per vraag de drie scores naast elkaar.
4. De vragen waarop B of C slechter scoort dan A, met de toelichting van de grader: daar
   zit de wiki fout, onvolledig of misleidend, en dat zijn de eerste kandidaten voor lint
   check 10.

Rapporteer aan de gebruiker in vier regels: de drie totaalscores, het verschil C min A op
`multi`, het verschil C min A op `single`, en de vraag met het grootste verlies voor de wiki.

## Interpretatie (zeg dit eerlijk, ook als het tegenvalt)

- C min A op `multi` is het kerncijfer. Klein of negatief betekent dat het wiki-onderhoud
  zich op deze vault niet terugbetaalt boven gewoon zoeken in de bronnen.
- B lager dan A is te verwachten (Anthropic: 48 tegen 53). B lager dan A op `single` met
  veel nullen wegens tegenspraak is wél een signaal: dan bevat de wiki fouten.
- Een kleine vragenset is een kleine steekproef: bij veertien vragen is één vraag ruim 7
  procentpunt. Trek geen conclusie uit een verschil van één of twee vragen; breid eerst de
  set uit.

## Grenzen

- Schrijft alleen in `eval/`. Geen wijzigingen in `wiki/`, `raw/`, `index.md`, `log.md`.
- Geen `register.py log`-entry: een eval is een meting, geen wijziging van de wiki.
