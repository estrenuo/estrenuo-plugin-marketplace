#!/usr/bin/env bash
# Regression test for wiki-lint LINT-01 Stap A (stub-detectie).
#
# SKILL.md verwees ooit naar "Grep op tags: [stub]" — een te letterlijke lezing
# die een stub met meerdere tags (bv. `tags: [wiki, concept, stub]`) zou missen.
# references/stub-detection.md gebruikt in werkelijkheid `tags:.*stub\|stub.*tags:`,
# dat wel multi-tag matcht. Deze test borgt dat het gedocumenteerde patroon
# multi-tag stubs blijft vinden, zodat deze klasse van bug niet terugkomt.
set -euo pipefail

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/wiki"

cat > "$tmp/wiki/multi-tag-stub.md" <<'EOF'
---
title: Multi-tag stub
tags: [wiki, concept, stub]
---

Stub content.
EOF

cat > "$tmp/wiki/single-tag-stub.md" <<'EOF'
---
title: Single-tag stub
tags: [stub]
---

Stub content.
EOF

cat > "$tmp/wiki/not-a-stub.md" <<'EOF'
---
title: Not a stub
tags: [wiki, concept]
---

Gewone pagina die het woord stub noemt in de lopende tekst, niet in tags.
EOF

fail=0

# Het patroon uit references/stub-detection.md Stap A.
found="$(grep -rl "tags:.*stub\|stub.*tags:" "$tmp/wiki" --include="*.md" | sort)"
expected="$(printf '%s\n%s\n' "$tmp/wiki/multi-tag-stub.md" "$tmp/wiki/single-tag-stub.md" | sort)"

if [ "$found" != "$expected" ]; then
  echo "FAIL: gedocumenteerd Stap A-patroon matcht niet exact de verwachte stub-set"
  echo "--- expected ---"
  echo "$expected"
  echo "--- found ---"
  echo "$found"
  fail=1
fi

# Guard tegen de te letterlijke lezing die in SKILL.md is gecorrigeerd: een
# kale grep op de losse string "tags: [stub]" mag niet als gelijkwaardig
# gelden, want die mist de multi-tag stub stilzwijgend.
literal_found="$(grep -rl "tags: \[stub\]" "$tmp/wiki" --include="*.md" | sort || true)"
if echo "$literal_found" | grep -q "multi-tag-stub.md"; then
  echo "FAIL: letterlijke 'tags: [stub]' matchte onverwacht de multi-tag stub — fixture ongeldig"
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "PASS: Stap A-patroon matcht multi-tag stubs correct"
fi

exit "$fail"
