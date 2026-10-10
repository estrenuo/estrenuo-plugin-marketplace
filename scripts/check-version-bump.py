#!/usr/bin/env python3
"""Release-gate voor pull requests naar main.

Gebruik: scripts/check-version-bump.py <base-ref>

Voor elke plugin uit .claude-plugin/marketplace.json met gewijzigde bestanden
t.o.v. de merge-base met <base-ref>:
  1. plugin.json#version moet semver X.Y.Z zijn en hoger dan op de base;
  2. de tag <plugin>/v<versie> mag nog niet bestaan (lokaal of op origin);
  3. elke SKILL.md-description moet door de claude.ai-sync komen:
     geen punthaken en maximaal 1024 tekens.
Wijzigingen buiten plugin-mappen (CI, docs, scripts) vereisen geen bump.
Exit 0 = ok, 1 = gate faalt.
"""
import json
import re
import subprocess
import sys
from pathlib import Path


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def semver(v: str):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", v or "")
    return tuple(int(x) for x in m.groups()) if m else None


def version_at(ref: str, plugin: str):
    try:
        return json.loads(git("show", f"{ref}:{plugin}/.claude-plugin/plugin.json")).get("version")
    except subprocess.CalledProcessError:
        return None  # plugin bestaat nog niet op de base


def tag_exists(tag: str) -> bool:
    if git("tag", "--list", tag).strip():
        return True
    return bool(git("ls-remote", "--tags", "origin", f"refs/tags/{tag}").strip())


def skill_description(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ""
    front = text.split("\n---", 1)[0]
    m = re.search(r"^description:[ \t]*(.*)$", front, re.M)
    if not m:
        return ""
    first = m.group(1).strip()
    if first and first[0] not in "|>":
        return first.strip("'\"")
    lines = []
    for line in front[m.end():].split("\n")[1:]:
        if line and not line.startswith((" ", "\t")):
            break
        lines.append(line.strip())
    return "\n".join(lines).strip()


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    base = git("merge-base", sys.argv[1], "HEAD").strip()
    changed = [p for p in git("diff", "--name-only", base, "HEAD").splitlines() if p]
    plugins = [p["name"] for p in json.loads(Path(".claude-plugin/marketplace.json").read_text())["plugins"]]

    errors = []
    touched = [pl for pl in plugins if any(c.startswith(pl + "/") for c in changed)]
    if not touched:
        print("Geen plugin-bestanden gewijzigd; geen versie-bump vereist.")
        return 0

    for pl in touched:
        old, new = version_at(base, pl), version_at("HEAD", pl)
        if semver(new) is None:
            errors.append(f"{pl}: versie in plugin.json is geen geldige semver ({new!r}).")
            continue
        if old is not None and semver(old) is not None and semver(new) <= semver(old):
            errors.append(
                f"{pl}: bestanden gewijzigd maar versie niet verhoogd ({old} -> {new}). "
                f"Draai scripts/bump-plugin.sh {pl} <patch|minor|major> op deze branch."
            )
        elif tag_exists(f"{pl}/v{new}"):
            errors.append(f"{pl}: tag {pl}/v{new} bestaat al; kies een hogere versie.")
        else:
            print(f"{pl}: {old} -> {new} ok")

        for skill in sorted(Path(pl, "skills").glob("*/SKILL.md")):
            desc = skill_description(skill)
            if "<" in desc or ">" in desc:
                errors.append(f"{skill}: description bevat punthaken; claude.ai haalt die weg.")
            if len(desc) > 1024:
                errors.append(f"{skill}: description is {len(desc)} tekens; claude.ai kapt af op 1024.")

    for e in errors:
        print(f"::error::{e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
