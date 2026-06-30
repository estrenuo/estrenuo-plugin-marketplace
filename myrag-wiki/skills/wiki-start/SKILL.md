---
name: wiki-start
description: |
  Gebruik deze skill wanneer de gebruiker expliciet een wiki-sessie wil
  starten. Typische triggers: "wiki start", "start wiki session",
  "open wiki", "wiki sessie starten", "begin wiki-sessie", of een
  informele variant die de wiki expliciet noemt.

  Triggert NIET op het kale "start" of generieke sessie-openers
  ("begin sessie", "laten we beginnen", "sessie starten", "waar waren
  we") — die horen bij session-briefing, de eenduidige eigenaar van
  sessiestart. Vereis een expliciete verwijzing naar de wiki.

  Deze skill is verplicht — niet optioneel — omdat het session start
  protocol 6 geordende stappen heeft die elk een specifiek doel
  dienen. CLAUDE.md staat al in de context, maar die context alleen
  garandeert niet dat alle stappen worden uitgevoerd; zonder skill
  worden stappen samengevat, samengevoegd of overgeslagen. De skill
  dwingt de volledige volgorde af.

  Als deze skill en CLAUDE.md conflicteren, heeft CLAUDE.md voorrang.
  Volg de expliciete instructies in CLAUDE.md en pas deze skill alleen
  aan waar nodig om consistentie met CLAUDE.md te behouden.
allowed-tools:
  - Read
---

<objective>
Dit is het session start protocol uit CLAUDE.md. Alle 6 stappen zijn verplicht en moeten in volgorde worden uitgevoerd. Geen stap mag overgeslagen worden — ook niet als de gebruiker al gedeeltelijk georiënteerd lijkt of de wiki recentelijk open had.
</objective>

<process>

Volg deze zes stappen in precies deze volgorde. Als een stap niet kan
worden uitgevoerd omdat een verplicht bestand ontbreekt of niet
toegankelijk is, meld dat meteen aan de gebruiker en onderbreek de
sessiestart. Lees eerst, verzamel vervolgens de benodigde statusdata,
en eindig met een gestandaardiseerde rapportage.

## Stap 1: Lees CLAUDE.md

Lees `CLAUDE.md` volledig met de Read-tool.

Als `CLAUDE.md` niet gevonden kan worden, meld dat meteen aan de gebruiker
met de bestandsnaam en onderbreek de sessiestart.

**Waarom:** CLAUDE.md is de gezaghebbende bron voor alle wiki-workflows en schema-definities. Als deze skill en CLAUDE.md conflicteren, heeft CLAUDE.md voorrang. Zonder CLAUDE.md actief in context kunnen latere stappen afwijken van de actuele workflow-definitie.

## Stap 2: Lees index.md

Lees `index.md` volledig. Tel het aantal pagina-entries (regels die beginnen met `- [[`) en het aantal categoriekoppen (regels die beginnen met `##`). Noteer beide tellingen voor gebruik in stap 5.

**Waarom:** index.md is de gezaghebbende catalog van wiki-content. Bestandstelling via `find` telt ook stubs en artefacten — index.md geeft de werkelijke omvang. Zonder deze telling is de statusinformatie in stap 5 onnauwkeurig.

## Stap 3: Lees log.md

Lees `log.md`. Identificeer de laatste 5 entries (herkenbaar aan `## [YYYY-MM-DD] type | Titel`). Als log.md minder dan 5 entries heeft, lees alle aanwezige entries. Noteer datum en beschrijving van de meest recente entry voor gebruik in stap 5.

**Waarom:** De recente log geeft context over wat er in vorige sessies is gedaan — nodig om te beoordelen of er open werk is of als er follow-up vereist is vanuit de laatste activiteit.

## Stap 4: Lees wiki/review-queue.md (verplicht — nooit overslaan)

Lees `wiki/review-queue.md` volledig. Controleer elk open item (`- [ ]`) op de datum direct ná `- [ ] `. Als die datum ≤ vandaag is (YYYY-MM-DD lexicografisch vergelijkbaar), markeer het item als "klaar voor review" voor gebruik in stap 5. Sla deze stap nooit over, ook niet als de queue leeg lijkt.

**Waarom:** Tijdgevoelige review-items worden anders gemist. Dit is de primaire reden dat de sessiestart een skill heeft en geen vrije instructie: zonder afdwinging wordt stap 4 overgeslagen zodra de queue ogenschijnlijk leeg is. CLAUDE.md §Session start protocol §4 vermeldt dit als expliciete vereiste.

## Stap 5: Rapporteer de wiki-status

Rapporteer exact in dit formaat:

> Wiki heeft [N] pagina's verdeeld over [N] categorieën.
> Laatste activiteit: [datum] — [wat].
> [Review-items klaar: [lijst] OF Geen review-items vandaag.]

Vraag daarna: "Wat wil je doen?"

**Waarom:** Een gestandaardiseerde rapportage maakt het eenvoudig om de wikistatus snel te beoordelen. Afwijken van het formaat maakt vergelijking tussen sessies lastiger en verbergt ontbrekende informatie (bijv. als review-queue niet gecheckt werd).

## Stap 6: Wacht op gebruikersinput

Wacht op de reactie van de gebruiker voordat je een vervolgactie start. Start geen workflow op basis van aannames over wat de gebruiker wil.

**Waarom:** De sessiestart is oriëntatie, geen actie. De gebruiker beslist wat er vervolgens gebeurt. Door te wachten, voorkom je dat Claude zonder input een workflow start die niet aangevraagd is.

</process>

<success_criteria>
- [ ] Stap 1: CLAUDE.md volledig gelezen
- [ ] Stap 2: index.md gelezen, pagina- en categorietellingen beschikbaar
- [ ] Stap 3: Laatste 5 log-entries gelezen en genoteerd
- [ ] Stap 4: wiki/review-queue.md gelezen, datumcheck uitgevoerd — nooit overgeslagen
- [ ] Stap 5: Status gerapporteerd in exact het voorgeschreven formaat, gevolgd door "Wat wil je doen?"
- [ ] Stap 6: Geen vervolgactie gestart zonder gebruikersinput
- [ ] Invarianten: ≤ 300 regels, allowed-tools: [Read], description bevat trigger-varianten en verplichtheidsuitleg
</success_criteria>
