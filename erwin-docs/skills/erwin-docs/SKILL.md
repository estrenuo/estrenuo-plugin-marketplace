---
name: erwin-docs
description: Beantwoord vragen over erwin Data Modeler 12.5 op basis van de officiële bookshelf, met geverifieerde namen en een bronverwijzing. Gebruik deze skill altijd bij vragen over erwin Data Modeler, erwin DM of ERwin. Trigger ook bij losse termen als TLX, Template Editor, forward engineering template, alter script, Bulk Editor, Derive New Model, design layer, Complete Compare, Mart, subject area, UDP, metamodel, M0/M1, SCAPI, erwin Spy, EMX, EMXProps, .erwin bestand, model XML, Key_Group, class name, MIMB, of bij vragen als "hoe schrijf ik een macro in erwin", "welke property heet X", "hoe exporteer ik mijn model", "hoe automatiseer ik erwin", "wat kan de erwin API". Gebruik de skill ook wanneer iemand erwin-macro's, erwin-XML of erwin-API-code laat schrijven of reviewen, want class- en propertynamen zijn casegevoelig en verzin je niet uit het hoofd. Niet voor algemene datamodelleertheorie zonder erwin-context.
---

# erwin Data Modeler documentatie raadplegen

Doel: vragen over erwin Data Modeler beantwoorden uit de officiële 12.5-documentatie, niet uit herinnering. erwin's class names, property names, macronamen en menupaden zijn casegevoelig, talrijk en historisch gegroeid. Ze zijn precies het soort detail dat een taalmodel plausibel verzint. Een `Property("PhysicalName")` in plaats van `Property("Physical_Name")` kost de gebruiker een uur debuggen. Daarom: verifiëren, of expliciet zeggen dat je het niet geverifieerd hebt.

## 1. Zoek eerst, classificeer daarna

De snelste en meest betrouwbare route naar een antwoord is bijna altijd dezelfde:

```
web_search: bookshelf erwin 12.5 "<exacte erwin-featurenaam>"
→ fetch de gevonden bookshelf-pagina
```

Zoek op de **erwin-term zelf**, niet op je omschrijving ervan. "erwin Bulk Editor wizard" werkt. "erwin bewerk meerdere objecten tegelijk" niet. Ken je de erwin-term niet, dan is dat het eigenlijke probleem: los dat eerst op via `references/vraag-naar-pagina.md`.

Deze route werkte in zes testvragen zes keer. Sla hem niet over ten gunste van de PDF-hub.

Lees pas daarna `references/doc-map.md` als je moet weten wáár iets staat, of `references/modus-*.md` voor het antwoordformaat.

## 2. Twee valkuilen bij het ophalen

**Versiedrift is de grootste foutbron.** Zoekresultaten mengen 9.8, 12.0, 12.1, 14.0, 15.0, 2020R2 en zelfs CA ERwin r7.3 door elkaar. De inhoud verschilt echt: de r7.3-pagina over UDP's bevat een uitzondering die in 12.5 geschrapt is. **Lees het versienummer uit het URL-pad voordat je een resultaat gebruikt.** Staat er iets anders dan 12.5, zeg dat er dan bij in je antwoord. Vaak is het 12.5-equivalent te vinden door in de URL het versienummer te vervangen en die pagina te zoeken.

**Gebruik URL's exact zoals ze in het resultaat stonden.** `web_fetch` weigert URL's die niet eerder in een zoek- of fetchresultaat voorkwamen, en de match is letterlijk. Een link met een spatie in het pad werkt niet als jij hem als `%20` intypt, en omgekeerd. Kopieer, typ niet over.

Bij PDF's altijd `text_content_token_limit` meegeven (2000 tot 4500) en `web_fetch_pdf_extract_text: true`. De gidsen zijn honderden pagina's. De inhoudsopgave staat vooraan, dus een lage limiet geeft je eerst de TOC met paginanummers.

## 3. Modus en antwoordformaat

Classificeer de vraag en noem de modus in één regel bovenaan, zodat de gebruiker kan corrigeren.

| Modus | Wanneer | Bestand |
|---|---|---|
| **A. Gebruik en features** | Wat de tool doet, hoe je hem bedient, modelleerconcepten in erwin-termen | `references/modus-gebruik.md` |
| **B. Import, export, engineering** | Reverse/forward engineering, XML, MIMB-bridges, Bulk Editor, derive, Mart | `references/modus-uitwisseling.md` |
| **C. Metamodel en XML** | Objecttypes, propertynamen, ownership, referenties, de XSD's, modelbestanden parsen | `references/modus-metamodel-xml.md` |
| **D. Automatisering** | TLX, macro's, templates, TLX-rapporten, de API | `references/modus-automatisering.md` |

Onderwerp voorspelt niet waar het antwoord staat. Een metamodelvraag kan in de User Guide beantwoord worden en een UI-vraag in de API Reference. Classificeer op **de uitkomst die de gebruiker nodig heeft**, en zoek breed.

In alle modi geldt:

- **Bronregel verplicht.** Sluit af met gids en URL. Eén regel.
- **Markeer wat niet geverifieerd is**, bij het betreffende stuk en niet als disclaimer aan het eind. Schrijf letterlijk "niet geverifieerd in de docs".
- **Onderscheid bewijs uit afwezigheid.** "Ik vond geen macro die dit doet" is zwakker dan "de docs zeggen dat dit niet kan". Zeg welke van de twee je hebt.

## 4. Verzin geen namen

Harde regel, dit is de bestaansreden van de skill.

Class names, property names, macronamen, API-methodenamen en menupaden komen uit de documentatie of ze komen er niet in. Kun je een naam niet verifiëren, schrijf dan `<nog te verifiëren>` met een comment erboven, in plaats van een plausibel ogende gok. Een lege plek is een taak, een verzonnen naam is een valstrik.

Twee vuistregels die van fouten redden:
- Class names zijn casegevoelig met underscores: `Physical_Name`, `Key_Group`, `Null_Option_Type`, `Referenced_Entities_Ref`.
- Een entiteit logisch en een tabel fysiek hebben dezelfde class name: `Entity`. Idem voor `Attribute`, `Domain`, `Default`, `Key_Group`, `Relationship`, `Validation_Rule`. De UI-naam verschilt, de class name niet.

## 5. Vraag door bij bekende dubbelzinnigheden

Sommige erwin-vragen hebben twee geldige lezingen die tot verschillende antwoorden leiden. Kies niet stilzwijgend, benoem de splitsing en beantwoord beide kort, of vraag.

De vier die in tests naar boven kwamen:

1. **"Macro's"** betekent Macro Toolbox-macro's (`%`-stijl, triggers en naamgeving) óf TLX in de Template Editor (forward engineering). Twee systemen, twee documenten, geen overlap.
2. **"Logisch en fysiek"** betekent de twee zijden van één logisch/fysiek model óf twee losse modellen gekoppeld via een design layer. Het antwoord verschilt volledig.
3. **"Exporteren"** betekent Save As XML, Import/Export from External Format via MIMB, een TLX-rapport, of de Report Designer. Vier mechanismen, vier resultaten.
4. **"Reverse engineeren"** kan in erwin alleen vanuit een database of een script. Elk ander bronformaat vereist een tussenstap. Zeg dat meteen in plaats van naar een route toe te redeneren.

## 6. Wanneer de vraag geen documentatievraag is

Een vraag als "hoe krijg ik mijn model in Data Vault-vorm" is een modelleervraag met een erwin-stap eraan vast. Zeg dat, doe de erwin-kant, laat de modelleerkant aan de gebruiker of een andere skill. Documentatie opdreunen bij een ontwerpprobleem is drukte, geen hulp.

## Referentiebestanden

- `references/vraag-naar-pagina.md` - van vraagvorm naar de exacte erwin-term en helppagina. Lees dit als je niet weet waarop je moet zoeken.
- `references/doc-map.md` - waar welk soort documentatie staat, en wat alleen als HTML of alleen als PDF bestaat.
- `references/modus-gebruik.md`, `modus-uitwisseling.md`, `modus-metamodel-xml.md`, `modus-automatisering.md`
