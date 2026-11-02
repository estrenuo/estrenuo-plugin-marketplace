# Detectielogica — wiki-ingest

## Kernregel (INGS-02)

Een bestand is **Modified** alleen als én mtime én hash afwijken van de opgeslagen waarden.
Een bestand is **Unchanged** als minstens één van beide overeenkomt.

De Morgan-inverse:
- Modified: `mtime_differs AND hash_differs`
- Unchanged: `NOT(mtime_differs AND hash_differs)` = `NOT mtime_differs OR NOT hash_differs`

**Waarom:** iCloud reset mtime soms zonder de inhoud te wijzigen. Hash-check voorkomt vals-positieve modified-detectie. Alleen mtime checken is niet voldoende.

## Beslisboom (INGS-03)

```
Bestand gevonden in raw/ (niet raw/assets/)
│
├─ Geen rij in ingest-state.md?
│  → NEW: voer stappen 1-10 uit
│
├─ Rij bestaat, maar bestand ontbreekt in raw/?
│  → DELETED: flageer in rapport, vraag gebruiker bevestiging voor archivering
│  → Verwijder de pagina NIET zonder expliciete goedkeuring
│
├─ Rij bestaat, mtime verschilt ÉN hash verschilt?
│  → MODIFIED: re-ingest (zie Multi-page check hieronder)
│
└─ Rij bestaat, mtime overeenkomt OF hash overeenkomt?
   → UNCHANGED: overslaan, telt mee in de "skipped"-teller van het rapport
```

## Batch-count (INGS-01)

Na classificatie van alle bestanden bereken je:

`count = aantal New + aantal Modified`

Deze count staat in het rapport (zie SKILL.md Stap 2):
- `count == 0` → geen verwerking, geen regen, alleen rapport
- `count >= 1` → verwerken, en na de batch eenmalig `regen-quick-indexes.py` draaien

**Multi-page raw telt als 1.** Eén raw-bestand dat meerdere wiki-pagina's voedt is één bron voor deze telling, ongeacht hoeveel pagina's de multi-page-dialoog uiteindelijk update.

**Force-ingest** (`ingest <bestandsnaam>`) heeft altijd `count = 1`.

## Bash-commando's

```bash
# mtime ophalen (macOS BSD-syntax — werkt niet op Linux)
mtime=$(stat -f "%Sm" -t "%Y-%m-%dT%H:%M:%S" "raw/<bestand>")

# hash ophalen (eerste 12 chars van SHA-256)
hash=$(shasum -a 256 "raw/<bestand>" | cut -c1-12)

# Scan raw/ — alleen .md en .pdf, exclusief raw/assets/
find raw/ -maxdepth 1 -type f \( -name "*.md" -o -name "*.pdf" \) | sort
```

## Force-ingest modus

`ingest <bestandsnaam>` slaat de detectiefase volledig over en voert stappen 1-10 direct uit op het opgegeven bestand. Gebruik dit om een bestand opnieuw te verwerken ongeacht mtime/hash-status.

Na voltooiing: ververs de rij in ingest-state.md (mtime, hash, datum).

## Multi-page check (bij Modified)

Controleer of de Source page cel van de ingest-state.md rij meerdere wikilinks bevat (komma-gescheiden).

Zo ja:
1. Toon alle gelinkte pagina's
2. Vraag gebruiker: primaire bronpagina / derivative analysis-pagina / allebei
3. Voer stappen 2-9 alleen uit voor de bevestigde pagina's
4. Update Ingested-datum naar vandaag

Zo nee: voer gewoon stappen 1-10 uit.
