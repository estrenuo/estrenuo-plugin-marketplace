#!/usr/bin/env python3
"""The single writer of the wiki's shared registers: log.md, index.md, wiki/ingest-state.md.

Skills call this script; they never edit these files by hand. Agents do not call
it either: they end with a "Registerblok" (the exact commands below) and the
calling skill runs it. The quick-indexes have their own owner,
regen-quick-indexes.py.

Run from the vault root (or pass --vault PATH):

    register.py log --type ingest --title "Titel" --body "één regel" [--body …] [--date YYYY-MM-DD]

    register.py index sections
    register.py index add --page wiki/concepts/x.md --section "Entities" [--group "Label"] --summary "één zin"
    register.py index stats

    register.py ingest-state status [--raw raw/X.pdf]
    register.py ingest-state set --raw raw/X.pdf [--page wiki/sources/x.md]… [--date YYYY-MM-DD]
    register.py ingest-state check [--fix]

Common flags: --vault PATH, --plain (readable output; JSON is the default),
--dry-run (print a diff, write nothing).

Exit codes: 0 done or nothing to do · 1 invalid input or a check failed ·
2 file/section/page not found · 3 lock not acquired.

Guarantees:
- log.md: entries go at the bottom, the file is only ever appended to, the
  header is exactly `## [YYYY-MM-DD] type | Title`, and repeating the last
  entry is a no-op.
- ingest-state.md: one row per raw, mtime/hash computed here (local time
  `%Y-%m-%dT%H:%M:%S`, first 12 hex of SHA-256), wikilinks written as
  `[[slug\\|Title]]`, rows kept in case-insensitive order, only the table under
  `## State table` (and new rows in `## Multi-page references`) is touched.
- index.md: one line `- [[slug|Title]] — summary (N sources)` per call, placed
  in an existing section/group; existing text and the rest of the frontmatter
  stay byte-for-byte the same. Source-style pages (sources/, recipes/,
  travel/) are listed in wiki/sources-index.md, not in index.md.
- Every write holds a per-vault lock and replaces the file atomically (log.md
  is appended under the lock instead, so earlier bytes are never rewritten).
"""

from __future__ import annotations

import argparse
import bisect
import contextlib
import datetime as dt
import difflib
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

LOG_TYPES = ("ingest", "update", "query", "analysis", "lint", "fix")
SOURCE_DIRS = ("sources", "recipes", "travel")   # listed in sources-index, not index.md
RAW_EXT = (".md", ".pdf")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MTIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
HASH_RE = re.compile(r"^[0-9a-f]{12}$")
CELL_SPLIT = re.compile(r"(?<!\\)\|")
LINK_SLUG = re.compile(r"\[\[([^\]|\\#]+)")


class Fail(Exception):
    def __init__(self, code: int, message: str, **extra):
        super().__init__(message)
        self.code = code
        self.extra = extra


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #

def today() -> str:
    return dt.date.today().isoformat()


def check_date(value: str | None) -> str:
    value = value or today()
    if not DATE_RE.match(value):
        raise Fail(1, f"ongeldige datum {value!r}; gebruik YYYY-MM-DD")
    return value


def one_line(value: str, what: str) -> str:
    value = value.strip()
    if not value:
        raise Fail(1, f"{what} is leeg")
    if "\n" in value or "\r" in value:
        raise Fail(1, f"{what} moet één regel zijn")
    return value


def resolve_vault(arg: str | None) -> Path:
    root = Path(arg).expanduser().resolve() if arg else Path.cwd().resolve()
    if not (root / "wiki").is_dir():
        raise Fail(2, f"geen wiki/ onder {root}; draai vanuit de vault-root of geef --vault")
    return root


@contextlib.contextmanager
def vault_lock(vault: Path, timeout: float = 30.0):
    """One lock per vault, kept outside the vault so iCloud never syncs it."""
    key = hashlib.sha1(str(vault).encode("utf-8")).hexdigest()[:16]
    path = Path(tempfile.gettempdir()) / f"myrag-register-{key}.lock"
    with open(path, "w") as fh:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > deadline:
                    raise Fail(3, f"lock niet gekregen na {timeout:.0f}s ({path})")
                time.sleep(0.1)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def atomic_write(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter block incl. both --- lines, body). Text, not YAML."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[: end + 5], text[end + 5:]
        if text.endswith("\n---"):
            return text, ""
    return "", text


def fm_field(fm: str, key: str) -> str:
    m = re.search(rf"^{re.escape(key)}\s*:\s*(.*)$", fm, re.MULTILINE)
    return m.group(1).strip() if m else ""


def fm_list(fm: str, key: str) -> list[str]:
    raw = fm_field(fm, key)
    if raw.startswith("[") and raw.endswith("]"):
        return [x.strip().strip("'\"") for x in raw[1:-1].split(",") if x.strip()]
    if raw:
        return [raw.strip("'\"")]
    # YAML block list
    m = re.search(rf"^{re.escape(key)}\s*:\s*\n((?:\s*-\s.*\n?)+)", fm, re.MULTILINE)
    return [l.strip()[1:].strip().strip("'\"") for l in m.group(1).splitlines()] if m else []


def set_updated(text: str, date: str) -> str:
    """Set `updated:` in the frontmatter to a bare date; nothing else changes."""
    fm, body = split_frontmatter(text)
    if not fm:
        return text
    if re.search(r"^updated\s*:", fm, re.MULTILINE):
        fm = re.sub(r"^updated\s*:.*$", f"updated: {date}", fm, count=1, flags=re.MULTILINE)
    else:
        fm = fm[:-4] + f"updated: {date}\n---\n"
    return fm + body


class Page:
    def __init__(self, vault: Path, rel: str):
        rel = rel.strip()
        path = (vault / rel).resolve() if not Path(rel).is_absolute() else Path(rel).resolve()
        if not path.is_file():
            raise Fail(2, f"pagina niet gevonden: {rel}")
        try:
            self.rel = path.relative_to(vault / "wiki")
        except ValueError:
            raise Fail(1, f"pagina ligt niet onder wiki/: {rel}")
        if path.suffix != ".md":
            raise Fail(1, f"geen markdown-pagina: {rel}")
        fm, _ = split_frontmatter(read(path))
        self.slug = path.stem
        self.dir = self.rel.parts[0] if len(self.rel.parts) > 1 else ""
        self.title = fm_field(fm, "title").strip("'\"") or self.slug
        self.type = fm_field(fm, "type") or self.dir or "meta"
        self.sources = fm_list(fm, "sources")
        for bad in ("|", "[[", "]]"):
            if bad in self.title:
                raise Fail(1, f"titel van {rel} bevat {bad!r}; pas de frontmatter aan")


def diff_text(name: str, old: str, new: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True),
        fromfile=f"{name} (huidig)", tofile=f"{name} (nieuw)", n=1))


# --------------------------------------------------------------------------- #
# log
# --------------------------------------------------------------------------- #

def cmd_log(vault: Path, args) -> dict:
    if args.type not in LOG_TYPES:
        raise Fail(1, f"onbekend type {args.type!r}; kies uit {', '.join(LOG_TYPES)}")
    date = check_date(args.date)
    title = one_line(args.title, "titel")
    body = [one_line(b, "body-regel") for b in (args.body or [])]
    header = f"## [{date}] {args.type} | {title}"
    entry = header + "\n" + ("\n" + "\n".join(body) + "\n" if body else "")

    path = vault / "log.md"
    with vault_lock(vault):
        old = read(path)
        last = old.rfind("\n## [")
        last_entry = old[last + 1:] if last != -1 else (old if old.startswith("## [") else "")
        if last_entry and last_entry.rstrip() == entry.rstrip():
            return {"status": "duplicate", "file": "log.md", "header": header}
        sep = "" if not old or old.endswith("\n\n") else ("\n" if old.endswith("\n") else "\n\n")
        addition = sep + entry
        if args.dry_run:
            return {"status": "dry-run", "file": "log.md", "diff": diff_text("log.md", old, old + addition)}
        with open(path, "a", encoding="utf-8", newline="") as fh:   # append-only by construction
            fh.write(addition)
    return {"status": "appended", "file": "log.md", "header": header}


# --------------------------------------------------------------------------- #
# index.md
# --------------------------------------------------------------------------- #

GROUP_RE = re.compile(r"^\*\*(.+?)\*\*")


def index_structure(body_lines: list[str]) -> list[dict]:
    sections: list[dict] = []
    for i, line in enumerate(body_lines):
        if line.startswith("## "):
            sections.append({"heading": line[3:].strip(), "line": i, "groups": []})
        elif sections and (m := GROUP_RE.match(line)):
            sections[-1]["groups"].append({"label": m.group(1).strip(), "line": i})
    return sections


def _pick(items: list[dict], key: str, wanted: str, what: str) -> dict:
    w = wanted.strip().lower()
    exact = [x for x in items if x[key].lower() == w]
    if len(exact) == 1:
        return exact[0]
    pref = [x for x in items if x[key].lower().startswith(w)]
    if len(pref) == 1:
        return pref[0]
    raise Fail(2, f"{what} {wanted!r} niet eenduidig gevonden",
               candidates=[x[key] for x in (pref or items)])


def _block_end(lines: list[str], start: int, stop_at_groups: bool) -> int:
    """Index after the last non-blank line of the block that starts at `start`."""
    last = start
    for j in range(start + 1, len(lines)):
        l = lines[j]
        if l.startswith("## ") or l.strip() == "---" or (stop_at_groups and GROUP_RE.match(l)):
            break
        if l.strip():
            last = j
    return last + 1


def cmd_index(vault: Path, args) -> dict:
    path = vault / "index.md"
    if not path.exists():
        raise Fail(2, "index.md niet gevonden in de vault-root")

    if args.index_cmd == "sections":
        fm, body = split_frontmatter(read(path))
        return {"status": "ok", "sections": [
            {"heading": s["heading"], "groups": [g["label"] for g in s["groups"]]}
            for s in index_structure(body.split("\n"))]}

    with vault_lock(vault):
        old = read(path)
        fm, body = split_frontmatter(old)
        lines = body.split("\n")
        date = today()

        if args.index_cmd == "stats":
            new_body, info = _stats_block(vault, lines)
            result = {"status": "updated", "file": "index.md", **info}
        else:
            page = Page(vault, args.page)
            if page.dir in SOURCE_DIRS:
                return {"status": "skipped", "file": "index.md", "slug": page.slug,
                        "reason": "bronpagina's staan in wiki/sources-index.md (regen-quick-indexes.py), niet in index.md"}
            summary = one_line(args.summary, "samenvatting")
            n = len(page.sources)
            entry = f"- [[{page.slug}|{page.title}]] — {summary}" + (f" ({n} sources)" if n else "")
            linked = re.compile(r"\[\[" + re.escape(page.slug) + r"(\||\\\||\]\]|#)")
            # Own line = a single-entry line: the link is followed by " — " or nothing.
            # A comma list ("- [[a|A]], [[b|B]]") is never rewritten.
            own = re.compile(r"^- \[\[" + re.escape(page.slug) + r"(\|[^\]]*)?\]\]( — |$)")
            own_line = [i for i, l in enumerate(lines) if own.match(l)]
            if own_line:
                i = own_line[0]
                if lines[i] == entry:
                    return {"status": "unchanged", "file": "index.md", "slug": page.slug}
                lines[i] = entry
                result = {"status": "refreshed", "file": "index.md", "slug": page.slug, "line": entry}
            elif any(linked.search(l) for l in lines):
                return {"status": "already_listed", "file": "index.md", "slug": page.slug,
                        "reason": "de slug staat al in een lijst of in proza; niets toegevoegd"}
            else:
                sections = index_structure(lines)
                if not sections:
                    raise Fail(2, "index.md heeft geen ##-secties")
                sec = _pick(sections, "heading", args.section, "sectie")
                if args.group:
                    grp = _pick(sec["groups"], "label", args.group, "groep") if sec["groups"] else None
                    if grp is None:
                        raise Fail(2, f"sectie {sec['heading']!r} heeft geen groepen")
                    at = _block_end(lines, grp["line"], stop_at_groups=True)
                elif sec["groups"]:
                    # Ungrouped entries above the first group get the new line; if there are
                    # none, the caller must pick a group instead of us guessing one.
                    first = sec["groups"][0]["line"]
                    if not any(l.startswith("- [[") for l in lines[sec["line"] + 1:first]):
                        raise Fail(2, f"sectie {sec['heading']!r} bestaat uit groepen; geef --group",
                                   candidates=[g["label"] for g in sec["groups"]])
                    at = _block_end(lines, sec["line"], stop_at_groups=True)
                else:
                    at = _block_end(lines, sec["line"], stop_at_groups=False)
                lines.insert(at, entry)
                result = {"status": "added", "file": "index.md", "slug": page.slug,
                          "section": sec["heading"], "line": entry}
            new_body = "\n".join(lines)

        new = set_updated(fm + new_body, date)
        if args.dry_run:
            return {"status": "dry-run", "file": "index.md", "diff": diff_text("index.md", old, new)}
        if new != old:
            atomic_write(path, new)
        return result


def _stats_block(vault: Path, lines: list[str]) -> tuple[str, dict]:
    wiki = vault / "wiki"
    per_dir = {}
    stubs = 0
    for d in sorted(p for p in wiki.iterdir() if p.is_dir() and not p.name.startswith(".")):
        pages = list(d.rglob("*.md"))
        if pages:
            per_dir[d.name] = len(pages)
        for p in pages:
            fm, _ = split_frontmatter(read(p))
            if "stub" in [t.lower() for t in fm_list(fm, "tags")]:
                stubs += 1
    meta = len([p for p in wiki.glob("*.md")])
    total = sum(per_dir.values()) + meta
    tracked = len(_StateTable(vault).rows) if (wiki / "ingest-state.md").exists() else 0
    parts = " + ".join(f"{n} {name}" for name, n in per_dir.items()) + f" + {meta} meta"
    block = [
        "## Stats",
        "",
        "*Gegenereerd door `register.py index stats`; niet met de hand bewerken.*",
        "",
        f"- **Total wiki pages**: {total} ({parts})",
        f"- **Raw sources tracked**: {tracked} (rijen in [[ingest-state|ingest-state.md]])",
        f"- **Open stubs**: {stubs}",
        f"- **Last updated**: {today()}",
        "",
    ]
    start = next((i for i, l in enumerate(lines) if l.strip() == "## Stats"), None)
    if start is None:
        while lines and not lines[-1].strip():
            lines.pop()
        lines = lines + ["", *block]
    else:
        end = next((j for j in range(start + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
        lines = lines[:start] + block + lines[end:]
    return "\n".join(lines), {"total_pages": total, "tracked_raws": tracked, "stubs": stubs}


# --------------------------------------------------------------------------- #
# ingest-state.md
# --------------------------------------------------------------------------- #

def raw_mtime(path: Path) -> str:
    """Same value as `stat -f "%Sm" -t "%Y-%m-%dT%H:%M:%S"` (local time)."""
    return dt.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%S")


def raw_hash(path: Path) -> str:
    """Same value as `shasum -a 256 <file> | cut -c1-12`."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def raw_fingerprint(path: Path) -> tuple[str, str]:
    return raw_mtime(path), raw_hash(path)


class Row:
    def __init__(self, line: str):
        self.line = line
        cells = [c.strip() for c in CELL_SPLIT.split(line)[1:-1]]
        self.cells = cells
        self.ok = len(cells) == 5
        self.file = cells[0].strip("`") if cells else ""
        self.mtime = cells[1] if len(cells) > 1 else ""
        self.hash = cells[2] if len(cells) > 2 else ""
        self.source = cells[3] if self.ok else (" \\| ".join(cells[3:-1]) if len(cells) > 5 else "")
        self.ingested = cells[-1] if len(cells) >= 5 else ""

    def key(self) -> str:
        return self.file.lower()

    def slugs(self) -> list[str]:
        return [s.strip() for s in LINK_SLUG.findall(self.source)]

    def render(self) -> str:
        return f"| `{self.file}` | {self.mtime} | {self.hash} | {self.source} | {self.ingested} |"

    def problems(self) -> list[str]:
        out = []
        if len(self.cells) != 5:
            out.append(f"{len(self.cells)} cellen i.p.v. 5 (een '|' zonder backslash in een wikilink?)")
        if not MTIME_RE.match(self.mtime):
            out.append(f"mtime {self.mtime!r} ongeldig")
        if not HASH_RE.match(self.hash):
            out.append(f"hash {self.hash!r} ongeldig")
        if not DATE_RE.match(self.ingested):
            out.append(f"Ingested {self.ingested!r} ongeldig")
        return out


class _StateTable:
    def __init__(self, vault: Path):
        self.path = vault / "wiki" / "ingest-state.md"
        if not self.path.exists():
            raise Fail(2, "wiki/ingest-state.md niet gevonden")
        self.text = read(self.path)
        self.lines = self.text.split("\n")
        start = next((i for i, l in enumerate(self.lines) if l.startswith("## State table")), None)
        if start is None:
            raise Fail(1, "ingest-state.md heeft geen sectie '## State table'")
        head = next((i for i in range(start, len(self.lines)) if self.lines[i].startswith("| File")), None)
        if head is None:
            raise Fail(1, "geen tabelkop '| File | …' onder '## State table'")
        self.first = head + 2            # after header + separator
        self.end = self.first
        while self.end < len(self.lines) and self.lines[self.end].startswith("|"):
            self.end += 1
        self.rows = [Row(l) for l in self.lines[self.first:self.end]]

    def find(self, name: str) -> Row | None:
        return next((r for r in self.rows if r.file == name), None)

    def render(self) -> str:
        return "\n".join(self.lines[:self.first] + [r.line for r in self.rows] + self.lines[self.end:])


def _raw_name(vault: Path, arg: str) -> tuple[str, Path]:
    rel = arg.strip()
    if rel.startswith("raw/"):
        rel = rel[4:]
    path = vault / "raw" / rel
    if rel.startswith("assets/"):
        raise Fail(1, "raw/assets/ bevat afbeeldingen, geen bronnen")
    if path.suffix.lower() not in RAW_EXT:
        raise Fail(1, f"alleen {' en '.join(RAW_EXT)} worden getrackt: {arg}")
    if not path.is_file():
        raise Fail(2, f"raw-bestand niet gevonden: raw/{rel}")
    return rel, path


def _link(page: Page) -> str:
    return f"[[{page.slug}\\|{page.title}]]"


def _add_multi_page(lines: list[str], row: Row, pages_by_slug: dict[str, Page]) -> str:
    """Add (or extend) the row for `row.file` in the Multi-page references table."""
    sec = next((i for i, l in enumerate(lines) if l.startswith("## Multi-page references")), None)
    if sec is None:
        return "no-section"
    head = next((i for i in range(sec, len(lines))
                 if lines[i].startswith("| Raw") or lines[i].startswith("## State table")), None)
    if head is None or lines[head].startswith("## State table"):
        return "no-table"
    i = head + 2
    while i < len(lines) and lines[i].startswith("|"):
        cells = [c.strip() for c in CELL_SPLIT.split(lines[i])[1:-1]]
        if cells and cells[0].strip("`") == row.file:
            have = set(LINK_SLUG.findall(" ".join(cells[1:3])))
            extra = [s for s in row.slugs() if s not in have]
            if not extra or len(cells) < 4:
                return "listed"
            add = ", ".join(_deriv(s, pages_by_slug) for s in extra)
            cells[2] = f"{cells[2]}, {add}" if cells[2] else add
            lines[i] = "| " + " | ".join(cells) + " |"
            return "extended"
        i += 1
    slugs = row.slugs()
    primary = _cell_link(slugs[0], pages_by_slug)
    derivs = ", ".join(_deriv(s, pages_by_slug) for s in slugs[1:])
    lines.insert(i, f"| `{row.file}` | {primary} | {derivs} |  |")
    return "added"


def _cell_link(slug: str, pages: dict[str, Page]) -> str:
    p = pages.get(slug)
    return _link(p) if p else f"[[{slug}]]"


def _deriv(slug: str, pages: dict[str, Page]) -> str:
    p = pages.get(slug)
    return f"{_link(p)} ({p.type})" if p else f"[[{slug}]]"


def _pages_by_slug(vault: Path, slugs: list[str]) -> dict[str, Page]:
    out = {}
    wiki = vault / "wiki"
    for s in slugs:
        hit = next(iter(wiki.rglob(f"{s}.md")), None)
        if hit:
            with contextlib.suppress(Fail):
                out[s] = Page(vault, str(hit.relative_to(vault)))
    return out


def cmd_ingest_state(vault: Path, args) -> dict:
    if args.state_cmd == "status":
        return _status(vault, args)
    with vault_lock(vault):
        table = _StateTable(vault)
        old = table.text
        if args.state_cmd == "check":
            return _check(table, args)
        result = _set(vault, table, args)
        new = set_updated(table.render(), check_date(args.date))
        if args.dry_run:
            return {"status": "dry-run", "file": "wiki/ingest-state.md",
                    "diff": diff_text("ingest-state.md", old, new)}
        if new != old:
            atomic_write(table.path, new)
        return result


def _set(vault: Path, table: _StateTable, args) -> dict:
    name, path = _raw_name(vault, args.raw)
    date = check_date(args.date)
    pages = [Page(vault, p) for p in (args.page or [])]
    mtime, digest = raw_fingerprint(path)
    row = table.find(name)
    status = "updated"
    if row is None:
        if not pages:
            raise Fail(1, f"raw/{name} heeft nog geen rij; geef minstens één --page")
        pages.sort(key=lambda p: 0 if p.dir == "sources" else 1)
        row = Row(f"| `{name}` | {mtime} | {digest} | {', '.join(_link(p) for p in pages)} | {date} |")
        keys = [r.key() for r in table.rows]
        table.rows.insert(bisect.bisect_right(keys, row.key()), row)
        status = "added"
    else:
        if not row.ok:
            raise Fail(1, f"rij van raw/{name} is kapot; draai eerst `ingest-state check --fix`",
                       problems=row.problems())
        have = row.slugs()
        new_links = [_link(p) for p in pages if p.slug not in have]
        row.mtime, row.hash, row.ingested = mtime, digest, date
        if new_links:
            row.source = ", ".join([row.source] + new_links) if row.source and row.source != "-" else ", ".join(new_links)
        row.line = row.render()
    result = {"status": status, "file": "wiki/ingest-state.md", "raw": name,
              "mtime": mtime, "hash": digest, "source_page": row.source}
    if len(row.slugs()) > 1:
        lines = table.lines
        before = len(lines)
        state = _add_multi_page(lines, row, _pages_by_slug(vault, row.slugs()))
        shift = len(lines) - before
        table.first += shift
        table.end += shift
        result["multi_page"] = state
    return result


def _check(table: _StateTable, args) -> dict:
    problems = []
    seen = {}
    for idx, r in enumerate(table.rows):
        line_no = table.first + idx + 1
        for p in r.problems():
            problems.append({"line": line_no, "file": r.file, "problem": p})
        if r.file in seen:
            problems.append({"line": line_no, "file": r.file, "problem": f"dubbel (ook regel {seen[r.file]})"})
        seen.setdefault(r.file, line_no)
    keys = [r.key() for r in table.rows]
    unsorted = keys != sorted(keys)
    if unsorted:
        problems.append({"line": None, "file": None, "problem": "rijen niet alfabetisch (hoofdletterongevoelig)"})
    if not args.fix:
        return {"status": "ok" if not problems else "problems", "file": "wiki/ingest-state.md",
                "rows": len(table.rows), "problems": problems}
    fixed = 0
    for r in table.rows:
        if len(r.cells) > 5 and MTIME_RE.match(r.mtime) and HASH_RE.match(r.hash) and DATE_RE.match(r.ingested):
            r.source = "\\|".join(c.strip() for c in CELL_SPLIT.split(r.line)[1:-1][3:-1])
            r.cells = [r.file, r.mtime, r.hash, r.source, r.ingested]
            r.ok = True
            r.line = r.render()
            fixed += 1
    if unsorted:
        table.rows.sort(key=Row.key)
    new = table.render()
    if args.dry_run:
        return {"status": "dry-run", "file": "wiki/ingest-state.md", "diff": diff_text("ingest-state.md", table.text, new)}
    if new != table.text:
        atomic_write(table.path, new)
    left = [p for r in table.rows for p in r.problems()]
    return {"status": "fixed" if not left else "partly-fixed", "file": "wiki/ingest-state.md",
            "repaired_rows": fixed, "resorted": unsorted, "remaining_problems": left}


def _status(vault: Path, args) -> dict:
    table = _StateTable(vault)
    by_name = {r.file: r for r in table.rows}
    raw = vault / "raw"
    if args.raw:
        name, path = _raw_name(vault, args.raw)
        files = [name]
    else:
        files = sorted(p.name for p in raw.iterdir()
                       if p.is_file() and p.suffix.lower() in RAW_EXT and not p.name.startswith("."))
    out = {"new": [], "modified": [], "unchanged": [], "deleted": [], "broken_rows": [], "multi_page": {}}
    for name in files:
        row = by_name.get(name)
        path = raw / name
        if row is None:
            out["new"].append(name)
            continue
        if not row.ok:
            out["broken_rows"].append(name)
        mtime = raw_mtime(path)
        # De Morgan: Modified only when mtime AND hash differ. Equal mtime -> skip the hash.
        if mtime == row.mtime or raw_hash(path) == row.hash:
            out["unchanged"].append(name)
        else:
            out["modified"].append(name)
            if len(row.slugs()) > 1:
                out["multi_page"][name] = row.slugs()
    if not args.raw:
        present = set(files)
        out["deleted"] = sorted(r.file for r in table.rows if "/" not in r.file and r.file not in present)
    counts = {k: len(v) for k, v in out.items() if isinstance(v, list)}
    if not args.list_unchanged:
        out["unchanged"] = counts["unchanged"]
    return {"status": "ok", "counts": counts, **out}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    def flags(suppress: bool) -> argparse.ArgumentParser:
        # Subcommands repeat the flags with SUPPRESS defaults, so a flag given before
        # the subcommand (`register.py --vault X log …`) is not reset to None.
        d = {"default": argparse.SUPPRESS} if suppress else {}
        c = argparse.ArgumentParser(add_help=False)
        c.add_argument("--vault", help="vault-root (standaard: huidige map)", **d)
        c.add_argument("--plain", action="store_true", help="leesbare uitvoer i.p.v. JSON", **d)
        c.add_argument("--dry-run", action="store_true", help="toon de diff, schrijf niets", **d)
        return c

    common = flags(suppress=True)
    p = argparse.ArgumentParser(description="Enige schrijver van log.md, index.md en wiki/ingest-state.md.",
                                parents=[flags(suppress=False)])
    sub = p.add_subparsers(dest="command", required=True)

    lg = sub.add_parser("log", parents=[common], help="entry onderaan log.md toevoegen")
    lg.add_argument("--type", required=True, help=f"een van: {', '.join(LOG_TYPES)}")
    lg.add_argument("--title", required=True)
    lg.add_argument("--body", action="append", help="één body-regel (herhaalbaar)")
    lg.add_argument("--date")

    ix = sub.add_parser("index", parents=[common], help="index.md")
    ixs = ix.add_subparsers(dest="index_cmd", required=True)
    ixs.add_parser("sections", parents=[common], help="koppen en groepen tonen")
    add = ixs.add_parser("add", parents=[common], help="entry-regel toevoegen of verversen")
    add.add_argument("--page", required=True)
    add.add_argument("--section", required=True)
    add.add_argument("--group")
    add.add_argument("--summary", required=True)
    ixs.add_parser("stats", parents=[common], help="## Stats opnieuw tellen")

    st = sub.add_parser("ingest-state", parents=[common], help="wiki/ingest-state.md")
    sts = st.add_subparsers(dest="state_cmd", required=True)
    s1 = sts.add_parser("status", parents=[common], help="New/Modified/Unchanged/Deleted (leest alleen)")
    s1.add_argument("--raw")
    s1.add_argument("--list-unchanged", action="store_true", help="ook de namen van ongewijzigde raws")
    s2 = sts.add_parser("set", parents=[common], help="rij zetten of verversen")
    s2.add_argument("--raw", required=True)
    s2.add_argument("--page", action="append")
    s2.add_argument("--date")
    s3 = sts.add_parser("check", parents=[common], help="tabel controleren")
    s3.add_argument("--fix", action="store_true", help="escape en volgorde herstellen")
    return p


def print_plain(result: dict) -> None:
    if "diff" in result:
        print(result["diff"] or "(geen wijziging)")
        return
    for k, v in result.items():
        if isinstance(v, list):
            print(f"{k} ({len(v)}):")
            for item in v:
                print(f"  - {item if not isinstance(item, dict) else ', '.join(f'{a}={b}' for a, b in item.items())}")
        elif isinstance(v, dict):
            print(f"{k}:")
            for a, b in v.items():
                print(f"  {a}: {b}")
        else:
            print(f"{k}: {v}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        vault = resolve_vault(args.vault)
        handler = {"log": cmd_log, "index": cmd_index, "ingest-state": cmd_ingest_state}[args.command]
        result = handler(vault, args)
        code = 1 if result.get("status") in ("problems", "partly-fixed") else 0
    except Fail as e:
        result = {"status": "error", "error": str(e), **e.extra}
        code = e.code
    if args.plain:
        print_plain(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
