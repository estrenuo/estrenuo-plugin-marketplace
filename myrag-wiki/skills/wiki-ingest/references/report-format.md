# Rapport-format — wiki-ingest

Na verwerking van alle bestanden rapporteer je altijd de zeven verplichte elementen (INGS-07). Geen enkel element mag ontbreken, ook niet als er niets bijzonders is.

## Template

```
## Ingest-rapport — [YYYY-MM-DD]

**Tellingen:** N nieuw | N bijgewerkt | N ongewijzigd | N verwijderd (orphan) | N mislukt
**Quick-indexes:** geregenereerd — [sources-index bijgewerkt|ongewijzigd, concepts-index bijgewerkt|ongewijzigd] | n.v.t. (count=0)

**Pages touched:**
- Nieuw: [[slug|Titel]], ...
- Bijgewerkt: [[slug|Titel]], ...
(Geen als er niets is aangemaakt of bijgewerkt)

**Contradictions found:** [N tegenstrijdigheden gemarkeerd in ## Open questions van ...]
(Geen als er geen zijn)

**Stubs created:** [N stubpagina's aangemaakt: [[slug|Titel]], ...]
(Geen als er geen zijn)

**Canonical-doc-checks:** [N checks uitgevoerd op claims over Claude Code/MCP/Task-tool/memory uit derivative bronnen]
- <concept> ← <bron-slug>: bevestigd | tegenspraak | niet-vindbaar
(Geen als er geen derivative claims op die onderwerpen waren)

**Per-bestand uitkomsten:**
| Bestand | Uitkomst | Opmerking |
|---------|----------|-----------|
| `bestandsnaam.md` | nieuw / bijgewerkt / ongewijzigd / mislukt | (foutmelding als mislukt, anders leeg) |
| `Orphan Bestand.md` | verwijderd (orphan) | Bevestiging gevraagd — pagina nog NIET verwijderd |

(Verplicht bij elke batch, ook bij 1 bestand. Bij mislukt: korte foutmelding in de Opmerking-kolom. Bij ongewijzigd: Opmerking leeg.)

**Meest interessante bevinding:**
[Één zin over de opvallendste ontdekking of de meest verrassende verbinding]

**Suggesties voor vervolgvragen:**
- ...
- ...
```

## Verplichte elementen

| Element | Wat te rapporteren | Mag "Geen" zijn? |
|---------|--------------------|-----------------|
| Tellingen | Alle vijf: nieuw / bijgewerkt / ongewijzigd / verwijderd / mislukt | Nee — altijd alle vijf |
| Per-bestand uitkomsten | Eén tabelrij per verwerkt of gedetecteerd bestand | Nee — altijd alle bestanden |
| Quick-indexes | geregenereerd (per bestand bijgewerkt/ongewijzigd) of n.v.t. | Nee — altijd vermelden |
| Pages touched | Elke gewijzigde of nieuwe wikipagina | Ja ("Geen") |
| Contradictions found | Tegenstrijdigheden in ## Open questions | Ja ("Geen") |
| Stubs created | Nieuwe stubpagina's aangemaakt | Ja ("Geen") |
| Meest interessante bevinding | Opvallendste ontdekking of verbinding | Nee — altijd vermelden |

## Richtlijnen

- Rapporteer altijd na verwerking, ook als alle bestanden ongewijzigd zijn (0 new, N unchanged is een geldig rapport)
- "Deleted" in de telling betekent: orphan gedetecteerd én de gebruiker gevraagd om bevestiging — de pagina is nog NIET verwijderd
- "verwijderd (orphan)" in de Per-bestand tabel betekent: gedetecteerd én bevestiging gevraagd — de raw zelf is niet aangeraakt
- Suggesties voor vervolgvragen zijn niet verplicht maar sterk aanbevolen; ze maken de waarde van de ingest zichtbaar
- Quick-indexes moet altijd vermeld worden, óók bij count=0 (dan: "n.v.t. — geen verwerking nodig")
- Neem de uitkomst van het script over: per index-bestand "bijgewerkt" of "ongewijzigd"

## Voorbeeld

```
## Ingest-rapport — 2026-05-06

**Tellingen:** 2 nieuw | 1 bijgewerkt | 4 ongewijzigd | 0 verwijderd | 0 mislukt
**Quick-indexes:** geregenereerd — sources-index bijgewerkt, concepts-index bijgewerkt

**Pages touched:**
- Nieuw: [[2026-05-06-data-vault-boek|Data Vault Boek]], [[data-vault-2|Data Vault 2.0]]
- Bijgewerkt: [[indiase-keuken|Indiase Keuken]]

**Contradictions found:** 1 tegenstrijdigheid gemarkeerd in ## Open questions van [[data-vault-2|Data Vault 2.0]] (auteursversie verschilt)

**Stubs created:** 1 stubpagina aangemaakt: [[dan-linstedt|Dan Linstedt]]

**Per-bestand uitkomsten:**
| Bestand | Uitkomst | Opmerking |
|---------|----------|-----------|
| `Data Vault Boek.md` | nieuw | |
| `Indiase Recepten Update.md` | bijgewerkt | |
| `Paneer Tikka.md` | nieuw | |
| `Bestaand Oud.md` | ongewijzigd | |
| `Bestaand Oud 2.md` | ongewijzigd | |
| `Bestaand Oud 3.md` | ongewijzigd | |
| `Bestaand Oud 4.md` | ongewijzigd | |

**Meest interessante bevinding:**
Het boek introduceert een vijfde normaalvorm specifiek voor Data Vault — niet vermeld in eerder ingested bronnen.

**Suggesties voor vervolgvragen:**
- Wat is het verschil tussen Data Vault 1.0 en 2.0 qua hub-definitie?
- Hoe verhoudt Data Vault zich tot Anchor Modeling?
```

## Voorbeeld 2 — één nieuwe bron

```
## Ingest-rapport — 2026-05-07

**Tellingen:** 1 nieuw | 0 bijgewerkt | 5 ongewijzigd | 0 verwijderd | 0 mislukt
**Quick-indexes:** geregenereerd — sources-index bijgewerkt (cluster "Recepten & Koken" +1), concepts-index ongewijzigd

**Pages touched:**
- Nieuw: [[2026-05-07-paneer-curry|Paneer Curry]]

**Contradictions found:** Geen

**Stubs created:** Geen

**Per-bestand uitkomsten:**
| Bestand | Uitkomst | Opmerking |
|---------|----------|-----------|
| `paneer-curry.md` | nieuw | |
| `Bestaand 1.md` | ongewijzigd | |
| `Bestaand 2.md` | ongewijzigd | |
| `Bestaand 3.md` | ongewijzigd | |
| `Bestaand 4.md` | ongewijzigd | |
| `Bestaand 5.md` | ongewijzigd | |

**Meest interessante bevinding:**
Eerste recept met paneer-bereiding via marineren — afwijkend van standaardpatroon in [[indiase-keuken|Indiase Keuken]].
```

## Voorbeeld 3 — batch met een mislukt bestand

```
## Ingest-rapport — 2026-05-08

**Tellingen:** 1 nieuw | 0 bijgewerkt | 3 ongewijzigd | 0 verwijderd | 1 mislukt
**Quick-indexes:** geregenereerd — sources-index bijgewerkt, concepts-index ongewijzigd

**Pages touched:**
- Nieuw: [[2026-05-08-nieuw-artikel|Nieuw Artikel]]

**Contradictions found:** Geen

**Stubs created:** Geen

**Per-bestand uitkomsten:**
| Bestand | Uitkomst | Opmerking |
|---------|----------|-----------|
| `Nieuw Artikel.md` | nieuw | |
| `Corrupt Bestand.pdf` | mislukt | Bestand niet leesbaar — mogelijk corrupt of te groot |
| `Bestaand 1.md` | ongewijzigd | |
| `Bestaand 2.md` | ongewijzigd | |
| `Bestaand 3.md` | ongewijzigd | |

**Meest interessante bevinding:**
Het nieuwe artikel introduceert een nog niet eerder besproken invalshoek op [[onderwerp|Onderwerp]].

**Suggesties voor vervolgvragen:**
- Wat is de relatie tussen dit artikel en [[verwant-concept|Verwant Concept]]?
```
