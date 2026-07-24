# Documentatiekaart erwin Data Modeler 12.5

Twee mirrors met identieke padstructuur: `bookshelf.quest.com` en `bookshelf.erwin.com`. Werkt de een niet, probeer de ander met hetzelfde pad.

Basis: `https://bookshelf.quest.com/bookshelf/public_html/12.5/Content/`

## HTML-onderwerppagina's, eerste keus

Pad: `.../12.5/Content/User Guides/erwin Help/<Topic_Name>.html`

Deze pagina's zijn kort, per onderwerp en actueel. Ze dekken vrijwel alles wat je in de UI doet. Bereikbaar via `web_search` op de exacte featurenaam. De paginanamen volgen de titel met underscores, bijvoorbeeld `Bulk_Editor.html`, `User-Defined_Properties.html`, `Save_a_Model_in_XML_Format_XML_Export.html`.

Zodra één zo'n pagina is opgehaald, zijn de links erop fetchbaar. Onderaan elke pagina staat een "More information"-blok dat naar verwante onderwerpen wijst. Dat is vaak sneller dan opnieuw zoeken.

Andere HTML-ingangen:

| Onderwerp | Pad onder `Content/` |
|---|---|
| Online Help startpunt | `User Guides/erwin Help/Online Help.html` |
| **Metamodel Reference** (enige volledige naslag, geen PDF) | `References/MM Ref/main.htm` |
| Metamodel Overview | `References/Metamodel Overview/Metamodel Overview Guide.html` |
| XML Schema | `References/API Reference/XML_Schema.html` |
| Data Modeling Overview | `References/Data Modeling Overview/Data Modeling Overview Guide.html` |
| Template Language and Macro Reference | `References/Template Language and Macro Reference/...Guide.html` |
| API Reference | `References/API Reference/API Reference Guide.html` |

## PDF-gidsen, voor wat niet in HTML staat

Index: `.../Content/PDF.htm`. Die pagina ophalen maakt alle PDF-links fetchbaar. Pad: `.../Content/PDFs/<naam>.pdf`.

**Dit staat alleen in de PDF's:**

| Onderwerp | Gids |
|---|---|
| TLX-rapporten (Generating TLX Reports, Create a Custom TLX Report) | `Implementation Guide.pdf` of `Navigator Edition User Guide.pdf`, rond p.124 |
| Volledige macro-naslag | `Template Language and Macro Reference.pdf` |
| Templates bewerken | `Editing Forward Engineering Templates.pdf` |
| API, interfaces, erwin Spy | `API Reference.pdf` |
| Metamodel-diagrammen | `Metamodel Overview.pdf` |
| Lijst MIMB-bridges | `Implementation Guide.pdf`, appendix |

Overige gidsen: `Data Modeling Overview.pdf`, `Create Custom Mart Reports.pdf`, `WorkgroupEdition Implementation Administration Guide.pdf`, `Scheduler.pdf`, `erwin DM Connect DI.pdf`, `erwin Data Modeler Git Support.pdf`, `erwin Data Modeler Installation Guide.pdf`, `Data Modeler Release Notes.pdf`, `erwin DM 12.5 Feature Tour.pdf`. Alles samen: `.../Content/PDFs/PDFs.zip`.

**Altijd `text_content_token_limit` meegeven**, 2000 tot 4500. De inhoudsopgave staat vooraan, dus een lage limiet geeft je eerst de TOC met paginanummers en dan weet je of doorlezen zin heeft.

## Aanvullende bronnen buiten de bookshelf

De erwin Support Knowledge Base (`support.quest.com/erwin-data-modeler/kb/...` en `support.erwin.com/hc/...`) bevat praktijkantwoorden die in de officiële docs ontbreken, bijvoorbeeld dat de Bulk Editor-CSV-import alleen bestaande objecten bijwerkt. Bruikbaar, maar het is geen productdocumentatie: markeer het als zodanig en controleer de datum.

## Als je het niet vindt

Zeg dat in één regel. Geef de meest waarschijnlijke gids plus URL en het advies om het zoekvak op de bookshelf zelf te gebruiken. Vul niet aan met een plausibel klinkend antwoord zonder het te markeren. Bij erwin is "waarschijnlijk heet het zo" vrijwel altijd fout.
