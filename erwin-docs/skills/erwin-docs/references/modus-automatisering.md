# Modus D - Automatisering: macro's, templates, rapporten, API

## Antwoordformaat

Werkende code in een codeblok, met commentaar op de niet-vanzelfsprekende regels. Benoem welke context de code aanneemt, want vrijwel elke TLX-fout komt voort uit een verkeerde aanname over de contextstack. Verzin geen macronaam of parameterlijst.

## Eerst uitzoeken: welk macro-systeem

erwin heeft er twee en ze delen niets.

1. **Macro Toolbox-macro's**, `%`-stijl, ruim 190 stuks. Voor triggers, stored procedures, DDL-fragmenten en logisch-naar-fysiek naammapping. Gedocumenteerd in de Online Help onder Macros.
2. **TLX**, in de Template Editor. Voor forward engineering, alter scripts, metamodel-dumps en naamgeving in Model Explorer en Complete Compare. Gedocumenteerd in de Template Language and Macro Reference.

Vraagt iemand "hoe doe ik X met macro's", stel dan eerst vast welke van de twee. Antwoorden zonder dat te doen is half fout.

## TLX-syntax, de kern

- **Literals** tussen dubbele quotes. Escapes `\n`, `\t`, `\\`, `\"`.
- **Macro's** zijn tekst zonder quotes en zonder `@`. Parameters tussen haakjes, altijd strings.
- **Substitutiemacro's** leveren een string. **Iteratiemacro's** krijgen een blok tussen accolades.
- **Return codes** staan los van de opgeleverde string. Een macro kan slagen en leeg zijn.
- **Keywords** met `@`: `@if`, `@ifnot`, `@elseif`, `@else`. Niet casegevoelig.
- **Conditionele blokken** tussen rechte haken: inhoud komt er alleen uit als alle macro's erin slagen.
- **Propagerende blokken** tussen punthaken: slagen als hun inhoud niet leeg is, en geven dat door naar buiten.
- **Commentaar** C-stijl.

## De contextstack

Macro's werken op het huidige contextobject, op een LIFO-stack. Iteratiemacro's pushen automatisch.

- `PushOwner`, `PushReference`, `PushTopLevelObject`, `Repush` erop, `Pop` eraf.
- Het onderste object is het anchor object en kan niet gepopt worden. Een `Pop` te veel faalt, hij crasht niet.
- `...From` zoekt dieper in de stack naar een type. `...Through` volgt een reference property.
- Punt in de naam: werkt alleen binnen een specifieke iterator. Dubbele punt: alleen in bepaalde processen. DBMS-prefix met underscore: alleen bij die target server.

**Phantom objects**: bij alter script-generatie simuleert erwin objecten die niet in het model zitten. De meeste macro's behandelen ze als gewoon, een aantal faalt erop, per macro gedocumenteerd. Werkt code wel bij schema-generatie en niet bij een alter script, kijk hier eerst.

**Deprecation levels**: Active, Discouraged, Deprecated, Removed. Vermeld het als een macro niet Active is en noem de opvolger.

## Een eigen uitvoerbestand maken

TLX is een expansietaal en schrijft zelf geen bestanden weg. Het hostproces bepaalt waar de tekst heen gaat. In de macro-index staat wel `IncludeFile` om te lezen, maar geen algemene schrijfmacro. Dit is bewijs uit afwezigheid, geen expliciete uitspraak in de docs. Zeg dat er zo bij.

Routes, aflopend van "hiervoor bedoeld" naar "hiervoor misbruikt":

1. **TLX Reports.** Generating TLX Reports, Generate a Default TLX Report, Create a Custom TLX Report. Staat **alleen in de PDF's**, Implementation Guide en Navigator Edition User Guide rond p.124. Dit is het aangewezen mechanisme voor een eigen uitvoerformaat.
2. **Forward engineering-template.** Actions, Forward Engineer, Forward Engineering Templates. Templates per DBMS in `.fet`-bestanden. Te herschrijven zodat er geen DDL maar een eigen formaat uitkomt, maar je vecht tegen de bedoeling van het proces. Kopieer altijd het meegeleverde bestand voor je bewerkt. Diepgang in Editing Forward Engineering Templates.
3. **De API.** Volledige controle, schrijft zelf weg, plambaar.

Is het gevraagde bestand simpelweg tabelvormig, wijs dan op de Report Designer of de Bulk Editor-CSV-export. Geen macro's om te onderhouden.

## De API

COM-gebaseerd (SCAPI), geleverd via `EAL.dll`, ingang `ISCApplication`. Vier tiers: Application, Model Directory, Sessions, Model Data.

**Twee modi met verschillend gedrag.** Standalone draait buiten de erwin DM-omgeving en de PersistenceUnits-collectie is leeg bij aanvang, ook als erwin DM open modellen heeft. Als add-in of script draait de client binnen het erwin DM-proces en bevat de collectie alle open modellen. Dit is de fout die iedereen één keer maakt.

**Twee niveaus.** `SCD_SL_M0` voor modeldata, objecten aanmaken en verwijderen, propertywaarden zetten. `SCD_SL_M1` voor object- en propertydefinities, UDP's en user-defined object definitions.

**Kan wel**: modellen aanmaken, openen uit bestand of mart, opslaan, objecten en properties opsommen en filteren, transacties met nesting en rollback, objecten aanmaken en verwijderen, scalaire en niet-scalaire waarden zetten, metamodel benaderen, history tracking. Op `ISCPersistenceUnit` zitten bovendien `ReverseEngineer`, `ReverseEngineerScript`, `ForwardEngineer`, `CompleteCompare`, `ReportDesigner` en `ApplyDataVault`, dus wizard-niveau operaties zijn direct aanroepbaar.

**Kan niet, of alleen met pijn**:
- Properties met de TL-vlag worden door erwin onderhouden en zijn niet via de API te wijzigen. Read-only properties evenmin.
- Commit werkt alleen op het model in het geheugen. Persisteren vereist expliciet `ISCPersistenceUnit::Save()`.
- Zodra je binnen een transactie iets wijzigt, kun je geen nieuwe geneste transactie meer openen tot commit of rollback. Een rollback van de buitenste transactie draait ook al gecommitte geneste transacties terug.
- Heterogene niet-scalaire properties bestaan niet, leden hebben altijd hetzelfde datatype. Leden benoemen kan niet, je werkt met indexen.
- Geen UI. Alles wat een dialoogvenster nodig heeft gaat niet.
- Gelijktijdige toegang is jouw probleem tenzij je Workgroup Edition gebruikt.
- COM-gebonden en daarmee in de praktijk Windows-gebonden. Dat laatste staat er niet met zoveel woorden, dat is een afleiding uit de architectuur. Markeer het als zodanig.

**erwin Spy** toont per object de properties met datatype, waarde en vlaggen, inclusief TL en RO. Daarmee zie je vooraf wat via de API schrijfbaar is. De aanbevolen werkwijze bij twijfel: leeg model, minimaal model bouwen dat de feature bevat, met erwin Spy bekijken. Sneller en betrouwbaarder dan de documentatie doorspitten.

## Volgorde bij een codeverzoek

1. Bepaal het proces of mechanisme. Dat bepaalt wat beschikbaar is.
2. Bepaal het anchor- of contextobject. Zonder dat kun je geen `Property`-aanroep beoordelen.
3. Verifieer elke property- en macronaam. Propertynamen uit modus C, macronamen uit de TLX-referentie, API-namen uit de API Reference.
4. Schrijf de code en benoem je aannames.
