#!/usr/bin/env python3
"""Wikilink tooling for the MyRAG wiki — resolve + lint in one place.

Two agent-facing tools sharing one resolver, so `lint`'s fix suggestions and
`resolve`'s answers can never drift apart.

    resolve — given display text, return the exact piped wikilink to paste.
    lint    — scan wiki/ for bare-alias and truly-broken wikilinks.

Run from repo root:
    python3 scripts/wikilinks.py resolve "Data Vault 2.0"
    python3 scripts/wikilinks.py lint
    python3 scripts/wikilinks.py lint --plain          # human-readable
    python3 scripts/wikilinks.py resolve "X" --display "X" --plain

Both commands emit JSON by default (high-signal, machine-consumable) and accept
--plain for a readable view. Exit code is 0 on success, 2 when `resolve` finds
no page and 1 when `lint` finds broken links (so a caller can branch on it).

Resolution is by ON-DISK FILENAME, matching Obsidian: a link resolves to
<slug>.md, never to a frontmatter alias. The resolver maps display text ->
canonical slug via (1) exact stem, (2) kebab(stem), (3) title, (4) alias, then
falls back to fuzzy nearest-matches. See CLAUDE.md "Wikilinks — ALWAYS USE
PIPED SYNTAX" for the rules this enforces.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

def _resolve_repo_root() -> Path:
    """Locate the vault root (the dir containing wiki/).

    Works whether this file lives in <vault>/scripts/ (vault-local copy) or in a
    plugin's scripts/ dir (run from the vault root). Order:
      1. script's own parent.parent, if wiki/ lives there  → vault-local copy
      2. current working directory, if wiki/ lives there    → plugin copy
    """
    here = Path(__file__).resolve().parent.parent
    if (here / "wiki").is_dir():
        return here
    cwd = Path.cwd().resolve()
    if (cwd / "wiki").is_dir():
        return cwd
    sys.stderr.write(
        "error: no wiki/ directory found next to the script or under the "
        "current directory. Run from the vault root.\n"
    )
    sys.exit(1)


REPO_ROOT = _resolve_repo_root()
WIKI = REPO_ROOT / "wiki"

# Wiki subdirs that hold linkable pages. Root index.md is handled separately.
PAGE_DIRS = ("concepts", "sources", "entities", "analysis", "recipes", "travel")

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".pdf"}


# --------------------------------------------------------------------------- #
# Normalization — same shape as regen-quick-indexes.py's alias normalization.
# --------------------------------------------------------------------------- #

def norm(s: str) -> str:
    """Fold display text to a slug-comparison key (lossy, for matching only)."""
    s = s.strip().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[()\[\]{}]", "", s)
    s = re.sub(r"[\s_/]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


# --------------------------------------------------------------------------- #
# Frontmatter parsing (minimal — title + aliases only).
# --------------------------------------------------------------------------- #

def _frontmatter(text: str) -> str:
    m = re.match(r"---\n(.*?)\n---", text, re.DOTALL)
    return m.group(1) if m else ""


def _field(fm: str, key: str) -> str:
    m = re.search(rf"^{re.escape(key)}\s*:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip().strip('"').strip("'") if m else ""


def _list_field(fm: str, key: str) -> list[str]:
    m = re.search(rf"^{re.escape(key)}\s*:\s*(.+)$", fm, re.MULTILINE)
    if not m:
        return []
    s = m.group(1).strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    return [x.strip().strip('"').strip("'") for x in s.split(",") if x.strip()]


# --------------------------------------------------------------------------- #
# Page index — built once, reused by both commands.
# --------------------------------------------------------------------------- #

class WikiIndex:
    def __init__(self) -> None:
        self.stems: dict[str, str] = {}          # stem.lower() -> canonical stem
        self.by_key: dict[str, set[str]] = {}     # norm-key      -> {slugs}
        self.titles: dict[str, str] = {}          # slug          -> title
        self._build()

    def _add_key(self, key: str, slug: str) -> None:
        if key:
            self.by_key.setdefault(key, set()).add(slug)

    def _build(self) -> None:
        paths: list[Path] = []
        for d in PAGE_DIRS:
            paths.extend(sorted((WIKI / d).glob("*.md")))
        # Top-level wiki pages (sources-index, context-log, …) are
        # linkable too; Obsidian resolves them despite living outside PAGE_DIRS.
        paths.extend(sorted(WIKI.glob("*.md")))
        for p in paths:
            slug = p.stem
            self.stems[slug.lower()] = slug
            self._add_key(norm(slug), slug)
            try:
                fm = _frontmatter(p.read_text(encoding="utf-8"))
            except OSError:
                continue
            title = _field(fm, "title")
            self.titles[slug] = title or slug
            if title:
                self._add_key(norm(title), slug)
            for alias in _list_field(fm, "aliases"):
                self._add_key(norm(alias), slug)
        # Root-level index.md resolves globally in Obsidian.
        if (REPO_ROOT / "index.md").exists():
            self.stems["index"] = "index"

    def exists(self, stem: str) -> str | None:
        """Return the canonical on-disk stem for `stem` (case-insensitive), or None."""
        return self.stems.get(stem.lower())

    def resolve(self, text: str) -> dict:
        """Map display text to a canonical slug. Returns a structured verdict."""
        text = text.strip()
        # 1. Exact on-disk filename (case-insensitive) — bare form is already valid.
        exact = self.exists(text)
        if exact:
            return self._hit(text, exact, "filename", bare_ok=True)
        # 2. Normalized-key match against stem / title / alias.
        key = norm(text)
        slugs = sorted(self.by_key.get(key, ()))
        if len(slugs) == 1:
            return self._hit(text, slugs[0], "alias/title")
        if len(slugs) > 1:
            return {
                "query": text, "resolved": False, "reason": "ambiguous",
                "candidates": [self._piped(text, s) for s in slugs],
            }
        # 3. Fuzzy nearest-matches over stems + titles.
        pool = list(self.stems.values()) + list(self.titles.values())
        near = difflib.get_close_matches(text, pool, n=5, cutoff=0.6)
        suggestions = []
        seen: set[str] = set()
        for cand in near:
            slug = self.exists(cand) or next(
                (s for s, t in self.titles.items() if t == cand), None)
            if slug and slug not in seen:
                seen.add(slug)
                suggestions.append(self._piped(text, slug))
        return {
            "query": text, "resolved": False, "reason": "no-match",
            "suggestions": suggestions,
            "stub_hint": f"No page for '{text}'. Create a stub, then link "
                         f"[[{norm(text)}|{text}]].",
        }

    def _hit(self, text: str, slug: str, via: str, bare_ok: bool = False) -> dict:
        out = {
            "query": text, "resolved": True, "slug": slug,
            "via": via, **self._piped(text, slug),
        }
        if bare_ok:
            out["note"] = "Display text equals the filename; bare form also works."
        return out

    def _piped(self, display: str, slug: str) -> dict:
        return {
            "slug": slug,
            "piped": f"[[{slug}|{display}]]",
            "path": str((self._path_for(slug)).relative_to(REPO_ROOT))
            if self._path_for(slug) else None,
            "title": self.titles.get(slug, slug),
        }

    def _path_for(self, slug: str) -> Path | None:
        for d in PAGE_DIRS:
            p = WIKI / d / f"{slug}.md"
            if p.exists():
                return p
        p = WIKI / f"{slug}.md"
        if p.exists():
            return p
        if slug == "index" and (REPO_ROOT / "index.md").exists():
            return REPO_ROOT / "index.md"
        return None


# --------------------------------------------------------------------------- #
# Link extraction — strips code so documentation examples aren't flagged.
# --------------------------------------------------------------------------- #

# Matches [[target]] or [[target|display]] or ![[embed]]. Table cells escape the
# separator as \| — we normalize that to | before splitting.
LINK_RE = re.compile(r"(!?)\[\[([^\[\]]+?)\]\]")


def _strip_inline_code(line: str) -> str:
    return re.sub(r"`[^`]*`", "", line)


def iter_links(text: str):
    """Yield (line_no, is_embed, target, display, raw) for every real wikilink."""
    in_fence = False
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        clean = _strip_inline_code(line)
        for m in LINK_RE.finditer(clean):
            is_embed = m.group(1) == "!"
            inner = m.group(2).replace("\\|", "|")
            if "|" in inner:
                target, display = inner.split("|", 1)
            else:
                target, display = inner, None
            target = target.split("#", 1)[0].split("^", 1)[0].strip()
            yield i, is_embed, target, (display.strip() if display else None), m.group(0)


# --------------------------------------------------------------------------- #
# Commands.
# --------------------------------------------------------------------------- #

def cmd_resolve(args: argparse.Namespace) -> int:
    idx = WikiIndex()
    result = idx.resolve(args.text)
    if args.display and result.get("resolved"):
        result["piped"] = f"[[{result['slug']}|{args.display}]]"
    if args.plain:
        _print_resolve_plain(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("resolved") else 2


def _print_resolve_plain(r: dict) -> None:
    if r.get("resolved"):
        print(r["piped"])
        print(f"  → {r['path']}  (matched via {r['via']})")
        if r.get("note"):
            print(f"  note: {r['note']}")
    elif r.get("reason") == "ambiguous":
        print(f"AMBIGUOUS — '{r['query']}' matches multiple pages:")
        for c in r["candidates"]:
            print(f"  {c['piped']}  ({c['path']})")
    else:
        print(f"NO MATCH — '{r['query']}'")
        for s in r.get("suggestions", []):
            print(f"  did you mean: {s['piped']}  ({s['path']})")
        if r.get("stub_hint"):
            print(f"  {r['stub_hint']}")


def cmd_lint(args: argparse.Namespace) -> int:
    idx = WikiIndex()
    findings: list[dict] = []
    files = []
    for d in PAGE_DIRS:
        files.extend(sorted((WIKI / d).glob("*.md")))

    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = str(p.relative_to(REPO_ROOT))
        for line_no, is_embed, target, display, raw in iter_links(text):
            if not target:
                continue
            # Image / asset embeds are not page links.
            if is_embed and Path(target).suffix.lower() in IMAGE_EXT:
                continue
            target = target[:-3] if target.lower().endswith(".md") else target

            if display is not None:
                # Piped link: the target slug must exist on disk.
                if idx.exists(target):
                    continue
                res = idx.resolve(target)
                findings.append(_finding(
                    rel, line_no, raw, target, "broken-piped",
                    "Piped target file does not exist.", res, display))
            else:
                # Bare link: fine only if it IS an existing filename.
                if idx.exists(target):
                    continue
                res = idx.resolve(target)
                if res.get("resolved"):
                    findings.append(_finding(
                        rel, line_no, raw, target, "bare-alias",
                        "Bare alias-style link; Obsidian would create an empty "
                        "page. Use piped form.", res, target))
                else:
                    findings.append(_finding(
                        rel, line_no, raw, target, "broken-bare",
                        "Link resolves to no page.", res, target))

    order = {"broken-bare": 0, "broken-piped": 1, "bare-alias": 2}
    findings.sort(key=lambda f: (order.get(f["category"], 9), f["file"], f["line"]))

    if args.plain:
        _print_lint_plain(findings)
    else:
        print(json.dumps({
            "files_scanned": len(files),
            "findings": len(findings),
            "by_category": _counts(findings),
            "results": findings,
        }, ensure_ascii=False, indent=2))
    return 1 if findings else 0


def _finding(file, line, raw, target, category, msg, res, display) -> dict:
    fix = None
    if res.get("resolved"):
        fix = f"[[{res['slug']}|{display}]]"
    elif res.get("suggestions"):
        fix = res["suggestions"][0]["piped"]
    return {
        "file": file, "line": line, "link": raw, "target": target,
        "category": category, "message": msg, "suggested_fix": fix,
    }


def _counts(findings: list[dict]) -> dict:
    out: dict[str, int] = {}
    for f in findings:
        out[f["category"]] = out.get(f["category"], 0) + 1
    return out


def _print_lint_plain(findings: list[dict]) -> None:
    if not findings:
        print("No broken or bare-alias wikilinks found.")
        return
    print(f"{len(findings)} finding(s):\n")
    for f in findings:
        print(f"[{f['category']}] {f['file']}:{f['line']}")
        print(f"  {f['link']}")
        if f["suggested_fix"]:
            print(f"  fix → {f['suggested_fix']}")
        else:
            print(f"  {f['message']}")
        print()


def main() -> int:
    if not WIKI.exists():
        print(f"ERROR: {WIKI} not found. Run from repo root.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="Resolve and lint wiki wikilinks.")
    sub = parser.add_subparsers(dest="command", required=True)

    r = sub.add_parser("resolve", help="Resolve display text to a piped wikilink.")
    r.add_argument("text", help="Display text or slug to resolve.")
    r.add_argument("--display", help="Display text for the piped link (defaults to TEXT).")
    r.add_argument("--plain", action="store_true", help="Human-readable output.")
    r.set_defaults(func=cmd_resolve)

    l = sub.add_parser("lint", help="Scan wiki/ for broken and bare-alias links.")
    l.add_argument("--plain", action="store_true", help="Human-readable output.")
    l.set_defaults(func=cmd_lint)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
