#!/usr/bin/env bash
# DEMO 2 — the constitution is code. Every write goes propose→commit through
# 8 validator gates; closed vocabularies are JSON-Schema enums at the tool
# boundary. Watch real violations get rejected with actionable messages,
# then the corrected note commit.
set -euo pipefail

Usage() { echo "Usage: demo2-gates.sh [-r|--repo DIR]"; }

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
while [[ $# -gt 0 ]]; do case "$1" in
  -r|--repo) REPO="$2"; shift 2 ;;
  -h|--help) Usage; exit 0 ;;
  *) Usage; exit 1 ;;
esac; done

V="$(mktemp -d /tmp/kb-demo2.XXXX)"
trap 'rm -rf "$V"' EXIT
python3 "$REPO/plugin/scripts/bootstrap_vault.py" -v "$V" >/dev/null
KB() { python3 "$REPO/plugin/scripts/kbcall.py" -v "$V" "$@"; }

echo "== 1. seed one legitimate note (genesis anchor)"
KB -t propose_note -a '{"title":"Gates as Code","entityClass":"Concept",
  "overview":"Rules enforced by validators, not prose.","tags":["status/anchor"],
  "confidence":0.95,"provenanceSource":"_meta/constitution.md",
  "provenanceAuthor":"team","isolatedJustification":"genesis anchor"}' | head -1
FIRST=$(python3 - "$V" <<'EOF'
import sqlite3, sys
db = sqlite3.connect(sys.argv[1] + "/.teamkb.db")
print(db.execute("SELECT id FROM staged ORDER BY id LIMIT 1").fetchone()[0])
EOF
)
KB -t commit_note -a "{\"proposalId\":\"$FIRST\"}" | head -1

echo
echo "== 2. VIOLATION: duplicate permalink (gate C2)"
KB -t propose_note -a '{"title":"Gates as Code","entityClass":"Concept",
  "overview":"dup","tags":["status/draft"],"confidence":0.9,
  "provenanceSource":"_meta/x.md","provenanceAuthor":"t",
  "isolatedJustification":"demo"}' | head -3

echo
echo "== 3. VIOLATION: near-duplicate title (gate I4, trigram similarity)"
KB -t propose_note -a '{"title":"Gates as Codes","entityClass":"Concept",
  "overview":"near dup","tags":["status/draft"],"confidence":0.9,
  "provenanceSource":"_meta/x.md","provenanceAuthor":"t",
  "isolatedJustification":"demo"}' | head -3

echo
echo "== 4. VIOLATION: placeholder provenance (gate PROV)"
KB -t propose_note -a '{"title":"Provenance Demo Note","entityClass":"Concept",
  "overview":"prov","tags":["status/draft"],"confidence":0.9,
  "provenanceSource":"TBD","provenanceAuthor":"unknown",
  "isolatedJustification":"demo"}' | head -3

echo
echo "== 5. VIOLATION: unregistered tag (gate TAG — registry is closed)"
KB -t propose_note -a '{"title":"Tag Demo Note","entityClass":"Concept",
  "overview":"tag","tags":["domain/not-registered"],"confidence":0.9,
  "provenanceSource":"_meta/x.md","provenanceAuthor":"t",
  "isolatedJustification":"demo"}' | head -3

echo
echo "== 6. CLOSED VOCABULARY: illegal entity class rejected at the boundary —"
echo "     schema enum for MCP clients, re-checked server-side for any caller"
KB -t propose_note -a '{"title":"Enum Demo","entityClass":"BlogPost",
  "overview":"x","tags":["status/draft"],"confidence":0.9,
  "provenanceSource":"_meta/x.md","provenanceAuthor":"t"}' 2>&1 | head -3 || true

echo
echo "== 7. corrected note: register the tag, then propose+commit cleanly"
KB -t register_tag -a '{"tag":"domain/demo","description":"justification demo tag"}' | head -1
OUT=$(KB -t propose_note -a '{"title":"Tag Demo Note","entityClass":"Concept",
  "overview":"tag demo, now with a registered tag.","tags":["domain/demo"],
  "confidence":0.9,"provenanceSource":"_meta/x.md","provenanceAuthor":"t",
  "isolatedJustification":"demo"}')
echo "$OUT" | head -1
PID2=$(echo "$OUT" | awk '/^STAGED/{print $2}')
KB -t commit_note -a "{\"proposalId\":\"$PID2\"}" | head -1
