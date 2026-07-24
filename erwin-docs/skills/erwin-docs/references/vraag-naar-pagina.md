# Van vraag naar zoekterm

Het lastigste aan de erwin-documentatie is niet dat ze slecht is, maar dat je de erwin-term moet kennen om iets te vinden. Deze tabel overbrugt dat. Alle vermelde paginanamen zijn geverifieerd in 12.5, tenzij anders vermeld.

Zoekpatroon: `bookshelf erwin 12.5 "<term uit kolom 2>"`.

## Vraagvorm naar term

| Wat de gebruiker vraagt | erwin-term om op te zoeken | Waar het staat |
|---|---|---|
| "Model opslaan als XML" | Save a Model in XML Format (XML Export) | HTML help |
| "Model naar een ander tool" | Import from External Format / Export to External Format, Metadata Integration Wizard, MIMB | HTML help |
| "Veel objecten tegelijk bewerken" | Bulk Editor, Bulk Editor Wizard | HTML help |
| "Metadata uit Excel of CSV importeren" | Bulk Editor CSV import (alleen updates), Metadata Integration Wizard | HTML help + support KB |
| "Fysiek model afleiden uit logisch" | Derive New Model, Design Layers, Type Selection, Option Set | HTML help |
| "Eigen properties toevoegen" | User-Defined Properties, User Defined Properties editor | HTML help |
| "Twee modellen vergelijken" | Complete Compare | HTML help |
| "Eigen rapport of interfacebestand" | Generating TLX Reports, Create a Custom TLX Report | **alleen PDF** |
| "DDL-generatie aanpassen" | Forward Engineering Templates, Template Editor, .fet | PDF (Editing FE Templates) |
| "Wat doet macro X" | de macronaam zelf, plus "erwin macro" | PDF (Template Language and Macro Reference) |
| "Welke property heet Y op object Z" | de objecttypenaam, plus "erwin metamodel reference" | **alleen HTML** (MM Ref) |
| "Erwin aansturen vanuit code" | API Reference, SCAPI, ISCApplication, persistence unit, session | PDF |
| "Hoe is dit intern opgeslagen" | erwin Spy | PDF (API Reference) |
| "Gedeelde repository" | Mart, Workgroup Edition | PDF + HTML |
| "Naamgevingsregels afdwingen" | Naming Standards, Model Naming Options, glossary | HTML help |

## Wat waar staat, in één regel

- **HTML-onderwerppagina's** (`.../12.5/Content/User Guides/erwin Help/<Topic>.html`) dekken vrijwel alles wat je in de UI doet. Kort, actueel, per onderwerp. Eerste keus.
- **Metamodel Reference** bestaat alleen als HTML (`.../References/MM Ref/main.htm`) en is de enige volledige lijst van objecttypes en properties.
- **TLX-rapporten, forward engineering-templates, de API en het volledige metamodel-overzicht** staan alleen in de PDF's. Zoek daar niet naar een HTML-pagina, die is er niet.

## Termen die de gebruiker anders noemt dan erwin

| Wat mensen zeggen | Wat erwin het noemt |
|---|---|
| tabel (in een logisch/fysiek model) | Entity, ook aan de fysieke kant |
| kolom | Attribute |
| datatype-definitie, herbruikbaar type | Domain |
| deelmodel, selectie van objecten | Subject Area |
| opgeslagen diagramweergave | Stored Display |
| eigen veld, extra attribuut op een object | UDP (User-Defined Property) |
| repository, centrale opslag | Mart |
| model afleiden, doorvertalen | Derive, Design Layer |
| sjabloon voor DDL | Forward Engineering Template (.fet) |

Zit de term van de gebruiker hier niet bij en levert zoeken niets op, zeg dat dan en vraag hoe het onderdeel in de UI heet. Doorraden op een term die erwin niet gebruikt levert alleen ruis op.
