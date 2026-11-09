#!/usr/bin/env python3
"""Kandidaten voor lint check 10 (bronverificatie). Schrijft niets.

Kiest concept- en entity-hubs die verificatie nodig hebben: nooit
geverifieerd, of inhoudelijk gewijzigd na de laatste verificatie
(`updated` > `verified`). Volgorde: meeste inkomende links eerst (daar wordt
het meest op vertrouwd), dan meest recent gewijzigd. Per kandidaat lost het
de `sources:`-namen op naar bestanden in raw/, zodat de verifier de echte
bron leest en niet een andere wikipagina.

Meldt daarnaast bronpagina's (wiki/sources/) zonder rij in
wiki/ingest-state.md: die zijn niet naar een raw-bestand te herleiden.

Gebruik (vanuit de vault-root):
  python3 verify_candidates.py [vault] [--limit 5] [--plain]
Exit 0 altijd (rapporterend); 2 bij een ongeldige vault.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

HUB_DIRS = ("wiki/concepts", "wiki/entities")
LINK_RE = re.compile(r"\[\[([^\]|#]+)")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def fm_value(fm: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.*)$", fm, re.M)
    return m.group(1).strip().strip("'\"") if m else ""


def fm_list(fm: str, key: str) -> list[str]:
    raw = fm_value(fm, key)
    if not raw.startswith("["):
        return [raw] if raw else []
    inner = raw[1:raw.rfind("]")] if "]" in raw else raw[1:]
    # Splits op komma's buiten aanhalingstekens; namen kunnen komma's bevatten.
    out, cur, q = [], "", None
    for ch in inner:
        if q:
            if ch == q:
                q = None
            else:
                cur += ch
        elif ch in "\"'" and not cur.strip():
            q = ch
        elif ch == ",":
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return [nfc(x) for x in out if x]


def raw_lookup(vault: Path) -> dict[str, list[Path]]:
    """Naam en stam (zonder extensie) -> paden in raw/, assets uitgezonderd."""
    table: dict[str, list[Path]] = {}
    raw = vault / "raw"
    if not raw.is_dir():
        return table
    for p in raw.rglob("*"):
        if not p.is_file() or "assets" in p.relative_to(raw).parts:
            continue
        if p.suffix.lower() not in (".md", ".pdf", ".txt"):
            continue
        rel = p.relative_to(vault)
        for key in {nfc(p.name), nfc(p.stem)}:
            table.setdefault(key, []).append(rel)
    return table


STATE_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|(.*)$")


def state_map(state_text: str) -> dict[str, str]:
    """Wiki-slug -> raw-pad (relatief aan raw/) uit de hoofdtabel van ingest-state."""
    out: dict[str, str] = {}
    for ln in state_text.splitlines():
        m = STATE_ROW_RE.match(ln)
        if not m:
            continue
        for slug in LINK_RE.findall(m.group(2)):
            out.setdefault(nfc(slug.split("\\")[0].strip()), nfc(m.group(1)))
    return out


def resolve(name: str, table: dict[str, list[Path]], slugs: dict[str, str] | None = None) -> list[str]:
    hits = table.get(nfc(name)) or table.get(nfc(Path(name).stem)) or []
    if not hits and slugs and nfc(name) in slugs:
        # Hub verwijst naar een bronpagina-slug: volg die via ingest-state naar raw/.
        raw_name = slugs[nfc(name)]
        hits = table.get(nfc(Path(raw_name).name)) or []
    # Voorkeur voor raw/ root boven kopieën (raw/books/ is een qmd-scope-kopie).
    hits = sorted(set(hits), key=lambda p: (len(p.parts), str(p)))
    return [str(h) for h in hits[:1]]


def scan(vault: Path, limit: int) -> dict:
    texts: dict[Path, str] = {}
    for p in (vault / "wiki").rglob("*.md"):
        texts[p] = p.read_text(encoding="utf-8", errors="replace")
    index = vault / "index.md"
    if index.exists():
        texts[index] = index.read_text(encoding="utf-8", errors="replace")

    inbound: dict[str, int] = {}
    for p, t in texts.items():
        for target in set(m.strip().lower() for m in LINK_RE.findall(t)):
            if target != p.stem.lower():
                inbound[target] = inbound.get(target, 0) + 1

    table = raw_lookup(vault)
    state = vault / "wiki" / "ingest-state.md"
    state_text = state.read_text(encoding="utf-8", errors="replace") if state.exists() else ""
    slugs = state_map(state_text)
    candidates, skipped_current = [], 0
    for d in HUB_DIRS:
        for p in sorted((vault / d).glob("*.md")):
            fm = frontmatter(texts[p])
            if "stub" in fm_list(fm, "tags"):
                continue
            updated, verified = fm_value(fm, "updated"), fm_value(fm, "verified")
            if verified and verified >= updated:
                skipped_current += 1
                continue
            srcs = fm_list(fm, "sources")
            resolved, unresolved = [], []
            for s in srcs:
                r = resolve(s, table, slugs)
                (resolved.extend(r) if r else unresolved.append(s))
            resolved = list(dict.fromkeys(resolved))
            candidates.append({
                "page": str(p.relative_to(vault)),
                "inbound_links": inbound.get(p.stem.lower(), 0),
                "updated": updated,
                "verified": verified or None,
                "raw_files": resolved,
                "unresolved_sources": unresolved,
            })
    # Meeste inkomende links eerst; bij gelijke stand de meest recent gewijzigde.
    candidates.sort(key=lambda c: (c["inbound_links"], c["updated"] or ""), reverse=True)

    untraceable = [
        str(p.relative_to(vault))
        for p in sorted((vault / "wiki" / "sources").glob("*.md"))
        if f"[[{p.stem}" not in state_text
    ]
    return {
        "hubs_needing_verification": len(candidates),
        "hubs_verified_current": skipped_current,
        "selected": candidates[:limit],
        "untraceable_source_pages": untraceable,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault", nargs="?", default=".")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--plain", action="store_true")
    a = ap.parse_args()
    vault = Path(a.vault).resolve()
    if not (vault / "wiki").is_dir():
        print(f"geen vault: {vault}", file=sys.stderr)
        return 2
    r = scan(vault, a.limit)
    if not a.plain:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    print(f"Hubs die verificatie nodig hebben: {r['hubs_needing_verification']} "
          f"(actueel geverifieerd: {r['hubs_verified_current']})")
    for c in r["selected"]:
        print(f"\n- {c['page']}  (inbound {c['inbound_links']}, updated {c['updated']}, "
              f"verified {c['verified'] or 'nooit'})")
        for f in c["raw_files"]:
            print(f"    bron: {f}")
        for s in c["unresolved_sources"]:
            print(f"    NIET GEVONDEN in raw/: {s}")
    print(f"\nBronpagina's zonder rij in ingest-state ({len(r['untraceable_source_pages'])}):")
    for s in r["untraceable_source_pages"]:
        print(f"  {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
