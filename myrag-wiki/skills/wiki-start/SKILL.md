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

  Verplicht, niet optioneel: het sessiestart-protocol heeft 6 geordende
  stappen en zonder deze skill worden stappen samengevat of
  overgeslagen. De skill dwingt de volledige volgorde af.

  Als deze skill en CLAUDE.md conflicteren, heeft CLAUDE.md voorrang.
  Volg de expliciete instructies in CLAUDE.md en pas deze skill alleen
  aan waar nodig om consistentie met CLAUDE.md te behouden.
allowed-tools:
  - Read
  - Bash
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

## Stap 2: Lees de stats en koppen van index.md (niet het hele bestand)

Draai vanuit de vault-root:

```bash
sed -n '/^## Stats/,/^## [^S]/p' index.md
grep '^## ' index.md
```

Neem het aantal pagina's uit de regel `**Total wiki pages**`, en tel de categoriekoppen uit de tweede uitvoer (zonder `## Stats` en `## Meta`). Noteer beide voor stap 5. Lees `index.md` niet met de Read-tool; dat doen de query- en explore-workflow wanneer ze het nodig hebben.

Ontbreekt `## Stats` of de regel `**Total wiki pages**`, tel dan met `grep -c '^- \[\[' index.md` en zeg in stap 5 dat het een schatting is.

**Waarom:** `## Stats` wordt geteld door `register.py index stats` en klopt met de schijf. Het volledige bestand (tientallen KB) hoort niet in de context die elke sessie geladen wordt: dat verbruikt tokens en verlaagt de naleving van de rest van de instructies.

## Stap 3: Lees de laatste 5 log-entries (niet het hele bestand)

```bash
grep -n '^## \[' log.md | tail -5
```

Noteer datum en titel van de meest recente entry voor stap 5. Heb je de body van een entry nodig, lees dan alleen dat stuk met de Read-tool (`offset` = het regelnummer uit de uitvoer, `limit` ≈ 10). Lees `log.md` nooit volledig: het is honderden KB groot en append-only.

**Waarom:** De recente log geeft context over wat er in vorige sessies is gedaan. Daarvoor zijn vijf koppen genoeg; het bestand integraal lezen kostte meer dan 100K tokens per sessiestart.

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
- [ ] Stap 2: Stats en koppen van index.md via sed/grep gelezen, niet het hele bestand
- [ ] Stap 3: Laatste 5 log-koppen via grep gelezen, log.md niet integraal geopend
- [ ] CLAUDE-reference.md niet gelezen bij sessiestart
- [ ] Stap 4: Geen review-queue gelezen of aangemaakt; eventuele datum-acties naar OmniFocus gerouteerd
- [ ] Stap 5: Status gerapporteerd in exact het voorgeschreven formaat, gevolgd door "Wat wil je doen?"
- [ ] Stap 6: Geen vervolgactie gestart zonder gebruikersinput
- [ ] Invarianten: ≤ 300 regels, allowed-tools: [Read, Bash] (Bash alleen voor de sed/grep in stap 2 en 3), description bevat trigger-varianten en verplichtheidsuitleg
</success_criteria>
