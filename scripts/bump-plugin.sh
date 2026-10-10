#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage: bump-plugin.sh <plugin> <patch|minor|major> [--allow-dirty]
EOF
  exit 2
}

error_exit() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

# Parse args: 2 positionals + optional --allow-dirty (mag ook tussen positionals)
ALLOW_DIRTY=0
POSITIONAL=()
for arg in "$@"; do
  case "$arg" in
    --allow-dirty) ALLOW_DIRTY=1 ;;
    -*) usage ;;
    *) POSITIONAL+=("$arg") ;;
  esac
done

if [[ ${#POSITIONAL[@]} -ne 2 ]]; then
  usage
fi

PLUGIN="${POSITIONAL[0]}"
BUMP_TYPE="${POSITIONAL[1]}"

case "$BUMP_TYPE" in
  patch|minor|major) ;;
  *) error_exit "bump type must be patch, minor, or major (got: ${BUMP_TYPE})" ;;
esac

# Check 9: python3 beschikbaar (vóór eerste python-aanroep!)
command -v python3 >/dev/null 2>&1 \
  || error_exit "python3 is required for JSON edit but not found on PATH"

# Check 3: plugin.json bestaat
PLUGIN_JSON="${PLUGIN}/.claude-plugin/plugin.json"
[[ -f "$PLUGIN_JSON" ]] || error_exit "plugin not found: ${PLUGIN_JSON}"

# Check 4: plugin staat in marketplace.json
MARKETPLACE_JSON=".claude-plugin/marketplace.json"
[[ -f "$MARKETPLACE_JSON" ]] || error_exit "marketplace manifest not found: ${MARKETPLACE_JSON}"

if ! python3 - "$MARKETPLACE_JSON" "$PLUGIN" <<'PY'
import json, sys
path, name = sys.argv[1], sys.argv[2]
with open(path) as f:
    data = json.load(f)
names = [p.get("name") for p in data.get("plugins", [])]
sys.exit(0 if name in names else 1)
PY
then
  error_exit "plugin ${PLUGIN} not registered in ${MARKETPLACE_JSON}"
fi

# Read current version (uit plugin.json)
CURRENT=$(python3 -c "
import json, sys
with open(sys.argv[1]) as f: print(json.load(f).get('version', ''))
" "$PLUGIN_JSON")

# Check 5: geldig semver X.Y.Z
if ! [[ "$CURRENT" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  error_exit "current version is not valid semver: ${CURRENT}"
fi

# Compute nieuwe versie
IFS=. read -r MAJ MIN PAT <<< "$CURRENT"
case "$BUMP_TYPE" in
  patch) NEW="$MAJ.$MIN.$((PAT + 1))" ;;
  minor) NEW="$MAJ.$((MIN + 1)).0" ;;
  major) NEW="$((MAJ + 1)).0.0" ;;
esac

# Check 6: working tree clean
if [[ "$ALLOW_DIRTY" -eq 0 ]]; then
  if [[ -n "$(git status --porcelain)" ]]; then
    error_exit "working tree not clean — commit/stash or pass --allow-dirty"
  fi
fi

# Check 7: NIET op main — main is beschermd, releases gaan via PR + merge
CURRENT_BRANCH=$(git branch --show-current)
if [[ -z "$CURRENT_BRANCH" || "$CURRENT_BRANCH" == "main" ]]; then
  error_exit "on main (or detached) — bump on a feature branch: git switch -c release/${PLUGIN}-<versie>"
fi

# Check 8: tag bestaat nog niet (lokaal of op origin)
TAG="${PLUGIN}/v${NEW}"
if git rev-parse --verify --quiet "refs/tags/${TAG}" >/dev/null \
   || git ls-remote --exit-code --tags origin "refs/tags/${TAG}" >/dev/null 2>&1; then
  error_exit "tag ${TAG} already exists"
fi

# Mutate plugin.json (canonical re-format, behoudt accenten)
python3 - "$PLUGIN_JSON" "$CURRENT" "$NEW" <<'PY'
import json, sys
path, expected, new_version = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as f:
    data = json.load(f)
got = data.get("version")
if got != expected:
    raise SystemExit(f"version mismatch: expected {expected}, got {got}")
data["version"] = new_version
with open(path, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
PY

# Git operations
git add "$PLUGIN_JSON"
if ! git commit -m "${PLUGIN}: bump to ${NEW}"; then
  error_exit "commit failed — plugin.json edit is staged but not committed; fix and re-run"
fi
COMMIT_SHA=$(git rev-parse --short HEAD)

# Geen tag hier: de tag-release-workflow zet ${TAG} na de merge op main.
cat <<EOF
✓ Bumped ${PLUGIN}: ${CURRENT} → ${NEW}
✓ Committed: ${COMMIT_SHA} op ${CURRENT_BRANCH}

Volgende stappen:
  git push -u origin ${CURRENT_BRANCH}
  gh pr create --base main --title "${PLUGIN}: ${NEW}" --body "<MAJOR|MINOR|PATCH>: <waarom>"
  gh pr merge --merge --delete-branch   # na groene release-gate
Daarna: tag ${TAG} wordt automatisch gezet; Cowork-marketplace handmatig re-syncen.
EOF
