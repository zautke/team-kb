#!/usr/bin/env bash
# Package a battery run's evidence into docs/test-battery/run-<date>/.
# Usage: collect_evidence.sh [-v|--vault <dir>] [-d|--date <YYYY-MM-DD>]
#                           [-r|--run-id <id>] [-o|--out <dir>]

set -euo pipefail

Usage() {
  cat <<'USAGE'
Usage: collect_evidence.sh [options]
  -v, --vault   <dir>         vault to collect from (default: $TEAMKB_VAULT or ~/vault/kb-test)
  -d, --date    <YYYY-MM-DD>  run date label (default: today)
  -r, --run-id  <id>          filter events to one run_id (default: all)
  -o, --out     <dir>         output dir (default: docs/test-battery/run-<date>)
  -h, --help                  this message
Collects: event stream, per-document metrics rollup, raw trace, vault tree,
a sample rendered note, and index counts.
USAGE
  exit 1
}

VAULT="${TEAMKB_VAULT:-$HOME/vault/kb-test}"
DATE="$(date +%F)"
RUN_ID=""
OUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -v|--vault)  VAULT="$2"; shift 2 ;;
    -d|--date)   DATE="$2"; shift 2 ;;
    -r|--run-id) RUN_ID="$2"; shift 2 ;;
    -o|--out)    OUT="$2"; shift 2 ;;
    -h|--help)   Usage ;;
    *) echo "unknown argument: $1" >&2; Usage ;;
  esac
done

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VAULT="${VAULT/#\~/$HOME}"
OUT="${OUT:-$REPO/docs/test-battery/run-$DATE}"
mkdir -p "$OUT"

[[ -f "$VAULT/.teamkb-events.jsonl" ]] || { echo "no event log in $VAULT" >&2; exit 1; }

cp "$VAULT/.teamkb-events.jsonl" "$OUT/events.jsonl"
[[ -f "$VAULT/.teamkb-trace.jsonl" ]] && cp "$VAULT/.teamkb-trace.jsonl" "$OUT/trace.jsonl"

ROLLUP_ARGS=(-e "$OUT/events.jsonl" -o "$OUT/metrics.jsonl" --summary
             --aggregate "$OUT/phase-stats.json")
[[ -n "$RUN_ID" ]] && ROLLUP_ARGS+=(-r "$RUN_ID")
python3 "$REPO/plugin/scripts/metrics_rollup.py" "${ROLLUP_ARGS[@]}" \
  2> "$OUT/metrics-summary.txt" || true
cat "$OUT/metrics-summary.txt"

find "$VAULT" -type f -name '*.md' | sed "s|$VAULT/||" | sort > "$OUT/vault-tree.txt"

SAMPLE="$(find "$VAULT/knowledge" -name '*.md' | head -1)"
[[ -n "$SAMPLE" ]] && cp "$SAMPLE" "$OUT/sample-note.md"

TEAMKB_VAULT="$VAULT" python3 "$REPO/plugin/scripts/kbcall.py" -t reindex -a '{}' \
  > "$OUT/index-counts.json" || true

echo "evidence → $OUT"
ls -la "$OUT"
