# Modus C - Metamodel en XML

Hoe erwin zijn eigen modellen beschrijft en opslaat. Dit is de laag waar macro's en API-code hun namen vandaan halen. Een fout hier plant zich voort in alles wat de gebruiker daarna schrijft.

## Antwoordformaat

De naam exact zoals gedocumenteerd, met juiste casing en underscores, plus het objecttype waar hij op zit. Daarna pas de uitleg. De gebruiker kopieert de naam, dus die staat bovenaan en klopt letterlijk. Bij XML-werk: werkende fragmenten of parseercode met correct gedeclareerde namespaces.

## Twee metamodelbronnen, twee doelen

**Metamodel Overview** (PDF) geeft de grote structuur in IDEF1X-diagrammen. Voor "hoe hangt het samen".

**Metamodel Reference** (`References/MM Ref/main.htm`, alleen HTML, geen PDF) is de volledige naslag van alle object- en propertyklassen. Voor "hoe heet het precies". Alleen via `web_search` bereikbaar.

Verwar ze niet. De Overview bevat lang niet alle properties. Heb je een propertynaam nodig en alleen de Overview geraadpleegd, dan heb je hem niet geverifieerd.

## Kernbegrippen

**M0 en M1.** M1 is de metadatalaag met de definities van objecttypes, M0 de datalaag met de objecten in een model. Sommige macro's en API-aanroepen werken alleen op één van beide.

**Ownership.** Objecten bezitten andere objecten. Model bezit Entity, Entity bezit Attribute.

**Reference properties.** Verwijzingen tussen objecten, herkenbaar aan `_Ref`. Bijvoorbeeld `Referenced_Entities_Ref`, `Parent_Relationships_Ref`, `Child_Entity_Ref`, `Physical_Columns_Order_Ref`. Sommige scalair, andere vectoren. Een deel wordt door erwin zelf onderhouden en mag je niet direct wijzigen, de docs waarschuwen daar per geval voor.

**Twee views.** Via SCAPI is een vectorreferentie een property op het object, via ODBC wordt dezelfde relatie een associatieve tabel. Vermeld welke view je beschrijft.

## Naamgevingsregels

- Casegevoelig, altijd. Underscores tussen woorden.
- Logisch en fysiek delen één class name: `Attribute`, `Default`, `Domain`, `Entity`, `Key_Group`, `Relationship`, `Validation_Rule`.
- UDP's hebben een driedelige naam `<objecttype>.<modelzijde>.<naam>`, bijvoorbeeld `Entity.Logical.Color` naast `Entity.Physical.Color`. Dat zijn twee losse property types. Zonder het driedelige pad is de verwijzing dubbelzinnig.

## De XSD's

Vaak bijgevoegd in projectkennis (`/mnt/project/`) of uploads. Controleer dat eerst met `view` of `ls`.

| Bestand | Rol |
|---|---|
| `ERwinSchema.xsd` | Rootschema, definieert `erwin` en importeert de rest. Begin hier. |
| `EMX.xsd` | Objectstructuur: welke objecten bestaan en wat ze bezitten. |
| `EMXProps.xsd` | Alle propertylijsten, ruim 300 `*PropsList` types. Miljoenen tekens, nooit integraal inlezen. |
| `EM2.xsd` | De EM2-laag, `Model_Proxy_Object`, gebruikersopties en UI-instellingen. |
| `UDP.xsd` | User-defined property-definities. |

Root:

```xml
<erwin FileVersion="..." Format="erwin">
  <UDP:UDP_Definition_Groups/>   <!-- optioneel -->
  <EMX:Model/>                    <!-- verplicht, precies één -->
  <EM2:Model_Proxy_Object/>       <!-- optioneel -->
</erwin>
```

`Format` is `erwin` of `erwin_Repository`. Namespaces: root `http://www.erwin.com/dm`, `EMX` `/dm/data`, `EM2` `/dm/EM2data`, `UDP` `/dm/metadata`. `EMXProps.xsd` deelt de namespace van `EMX.xsd` en wordt via `xs:include` opgenomen, niet `xs:import`.

**Het vaste patroon**: elk object heeft `<Object>Props` met de eigenschappen en nul of meer `<Kindtype>_Groups` met de kinderen. Ken je dat, dan navigeer je elk object zonder de hele XSD te lezen.

Veelvoorkomende simple types: `SCVT_BOOLEAN`, `SCVT_GUID` (`{8-4-4-4-12}`), `SCVT_OBJID` (GUID plus `+` plus acht hextekens), `SCVT_POINT`.

## Werken met de grote bestanden

```bash
grep -A2 'complexType name="EntityPropsList"' EMXProps.xsd | head -40
grep -n 'name="Physical_Name"' EMX.xsd | head
sed -n '/<xs:element name="Entity">/,/^  <\/xs:element>/p' EMX.xsd | grep '_Groups"'
xmllint --noout --schema ERwinSchema.xsd model.xml   # alle vijf XSD's naast elkaar
```

Bij een echt modelbestand: eerst grootte checken, dan streamen of gericht met XPath zoeken. Nooit een export van tientallen megabytes integraal in context trekken.

Bij tegenspraak tussen de XML Schema-documentatiepagina en de XSD wint de XSD, want die hoort bij de geïnstalleerde versie.
