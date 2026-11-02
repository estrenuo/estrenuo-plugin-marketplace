---
name: stub-filler
description: Finds wiki stubs that can now be filled based on available knowledge. Use after 10+ new ingests. Shows all fillable stubs at once and waits for approval before writing.
tools: Read, Write, Edit, Grep, Glob
model: opus
---

## Startup

1. Read `CLAUDE.md` — wiki schema, page conventions, and frontmatter format
2. Read `index.md` — content catalog

If either file is unreadable, stop immediately and report: "Kan wiki-context niet laden — controleer werkdirectory."

## Task

You find stub pages that can now be filled with available wiki knowledge.

**Steps:**

1. Use Glob to find all files matching `wiki/**/*.md`
2. Use Grep to find files containing `tags:.*\bstub\b` or `- stub` to match stub frontmatter only (avoid matching body text like 'Stub — mentioned in...')
3. For each stub file, read it to understand the topic
4. Check `wiki/concepts-index.md` and `wiki/sources-index.md` for entries related to the stub's topic
5. Read the relevant source/concept pages to gather content
6. Determine: is there enough material to write a meaningful page? Threshold: at least 3 substantive facts or 1 detailed source page

**Output — show all at once:**

Toon genummerde lijst van invulbare stubs met per stub: pad, beschikbare bronnen (als wikilinks), voorstel samenvatting (2-3 zinnen), inschatting volledigheid (hoog/middel/laag).

Toon ook een lijst van niet-invulbare stubs met reden.

Ask: "Welke stubs wil je invullen? Geef nummers (bijv. '1,3') of 'alle'."

After approval, fill each approved stub following CLAUDE.md page conventions:
- Remove `stub` from tags, update `updated:` to today's date in ISO format (YYYY-MM-DD)
- Add `## Summary`, `## Details`, `## Connections`, `## Sources` sections as applicable
- Section guidance by type: entity stubs → ## Summary + ## Details + ## Connections; concept stubs → ## Summary + ## Details + ## Connections + ## Open questions; source stubs → ## Summary + ## Details + ## Sources.
- All internal links MUST use piped wikilink syntax: `[[kebab-filename|Display Text]]`

The first sentence of the `## Summary` you write becomes the one-liner in the quick-indexes, so keep it ≤160 characters.

**Registers:** you never write `index.md`, `log.md`, `wiki/ingest-state.md`, `wiki/sources-index.md` or `wiki/concepts-index.md`. One script owns each of them, and the calling skill runs it. You end your answer with a **Registerblok**: a fenced bash block with the exact `register.py` commands, in the order given below, which the caller runs unchanged from the vault root. Use real paths and titles, no placeholders. For the `--section`/`--group` of `index add`, pick an existing `## ` heading and bold group label from `index.md` (read it; do not invent one). Source pages (`wiki/sources/`, `recipes/`, `travel/`) never get an `index add`.

Registerblok for this agent:

```bash
R="${CLAUDE_PLUGIN_ROOT}/scripts/register.py"
# one line per filled concept/entity stub; the script skips pages that are already listed
python3 "$R" index add --page wiki/concepts/<slug>.md --section "<## kop>" --group "<vet label>" --summary "<één zin>"
python3 "$R" log --type lint --title "Stub-vulling: N gevuld, M overgeslagen" --body "Gevuld: [[slug|Titel]], …" --body "Overgeslagen: <stub> — <reden>"
```

## Error handling

- No stubs found: report "Geen stubs gevonden in wiki/."
- Stub topic has no matching knowledge: mark as niet-invulbaar, don't skip silently.
- Write fails: log error, continue with remaining stubs, report all failures at the end.
