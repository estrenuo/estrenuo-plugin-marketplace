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

## Stap 4: Geen review-queue (opgeheven — nooit opnieuw aanmaken)

`wiki/review-queue.md` is op 2026-08-07 opgeheven; datum-getriggerde acties leven sindsdien in OmniFocus, niet in de wiki. Lees dit bestand niet en maak het niet opnieuw aan, ook niet als een oudere instructie of pagina ernaar verwijst. Ontstaat er tijdens de sessie een actie met een datum, dan hoort die in OmniFocus (skill `plan-to-omnifocus`), en hoort in de wiki alleen de kennis achter die actie te staan.

**Waarom:** De queue dupliceerde een functie die OmniFocus al vervult en kon niets afdwingen: een markdown-bestand verschijnt niet op je dag, dus items met een verstreken datum rolden sessie na sessie door. CLAUDE.md §Session start protocol §4 legt deze opheffing expliciet vast.

## Stap 5: Rapporteer de wiki-status

Rapporteer exact in dit formaat:

> Wiki heeft [N] pagina's verdeeld over [N] categorieën.
> Laatste activiteit: [datum] — [wat].

Vraag daarna: "Wat wil je doen?"

**Waarom:** Een gestandaardiseerde rapportage maakt het eenvoudig om de wikistatus snel te beoordelen. Afwijken van het formaat maakt vergelijking tussen sessies lastiger en verbergt ontbrekende informatie.

## Stap 6: Wacht op gebruikersinput

Wacht op de reactie van de gebruiker voordat je een vervolgactie start. Start geen workflow op basis van aannames over wat de gebruiker wil.

**Waarom:** De sessiestart is oriëntatie, geen actie. De gebruiker beslist wat er vervolgens gebeurt. Door te wachten, voorkom je dat Claude zonder input een workflow start die niet aangevraagd is.

</process>

<success_criteria>
- [ ] Stap 1: CLAUDE.md volledig gelezen
- [ ] Stap 2: index.md gelezen, pagina- en categorietellingen beschikbaar
- [ ] Stap 3: Laatste 5 log-entries gelezen en genoteerd
- [ ] Stap 4: Geen review-queue gelezen of aangemaakt; eventuele datum-acties naar OmniFocus gerouteerd
- [ ] Stap 5: Status gerapporteerd in exact het voorgeschreven formaat, gevolgd door "Wat wil je doen?"
- [ ] Stap 6: Geen vervolgactie gestart zonder gebruikersinput
- [ ] Invarianten: ≤ 300 regels, allowed-tools: [Read], description bevat trigger-varianten en verplichtheidsuitleg
</success_criteria>
