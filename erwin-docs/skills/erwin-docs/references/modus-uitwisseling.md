# Modus B - Import, export en engineering

Alles wat een model erin of eruit krijgt. Dit is een aparte modus omdat de antwoorden hier verspreid staan over de User Guide, de Implementation Guide en de support-KB, en omdat gebruikers hier de meeste onjuiste aannames hebben.

## Antwoordformaat

Benoem eerst welk mechanisme van toepassing is, want er zijn er vier en ze lijken op elkaar. Dan de stappen. Als het gevraagde niet rechtstreeks kan, zeg dat in de eerste zin en geef daarna de omweg. Niet naar een route toe redeneren.

## De vier mechanismen, uit elkaar gehouden

| Mechanisme | Doet | Doet niet |
|---|---|---|
| **Save As XML** | Model wegschrijven in erwin's eigen XML | Vertalen naar een ander formaat |
| **Import/Export from External Format** (MIMB) | Vertalen van en naar circa 100 andere metadataproducten | Wat niet in de bridgelijst van jouw installatie zit |
| **Reverse Engineer** | Model bouwen uit een database of een DDL-script | Uit CSV, Excel of andere bronformaten |
| **Bulk Editor CSV** | Bestaande objecten bijwerken | Objecten aanmaken |

Vragen als "hoe krijg ik mijn metadata uit Excel in erwin" botsen op de onderste twee rijen tegelijk. Het eerlijke antwoord is: niet rechtstreeks. Omwegen, op volgorde van voorspelbaarheid: CSV naar DDL en dan Reverse Engineer from Script, of een API-script dat objecten aanmaakt, of kijken of er een bruikbare MIMB-bridge in de installatie zit. Beide eerste routes zijn via de API te automatiseren.

## XML-export, drie varianten met echt verschil

- **XML Standard Files**: expandeert macro's en namen niet, geschikt om terug te importeren in erwin DM.
- **XML Standard with Min Info Files**: alleen het minimum om het model te heropenen, afgeleide en read-only properties worden niet opgeslagen.
- **XML Repository Format Files**: expandeert namen, macro's en fysieke namen, exporteert afgeleide properties, en **kan niet meer met erwin DM geopend worden**.

De valkuil: fysieke namen worden vaak door een macro gegenereerd. In Standard XML staat dan de macro-aanroep in het bestand in plaats van de naam. Externe afnemers hebben meestal Repository Format nodig, maar leveren daarmee de terugweg in.

## Derive New Model

Actions, Design Layers, Derive New Model. De wizard heeft vijf panelen: Source Model, Target Model, Type Selection, Object Selection, Naming Standards. Wat er meekomt wordt bepaald door de Option Set op de Type Selection-pagina, die objecten én properties selecteert. De Advanced Default Option Set neemt alles mee voor het gekozen niveau, de Standard Default Option Set minder. Is het doel een fysiek model, dan is het logische filter niet beschikbaar.

Bron- en doelmodel worden automatisch gekoppeld en zijn later te synchroniseren via Sync with Model Source.

**Niet geverifieerd**: of UDP-definities en -waarden onder "properties" in de Option Set vallen. De documentatie zegt het niet expliciet. Adviseer een test met een minimaal model in plaats van te gokken.
