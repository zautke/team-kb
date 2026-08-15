#!/usr/bin/env bash
# DEMO 5 — the system reports on itself: corpus health + per-phase pipeline
# metrics from structured telemetry, and the evidence dashboard is REGENERATED
# live from committed event streams (derived, not hand-made).
set -euo pipefail

Usage() { echo "Usage: demo5-observability.sh [-r|--repo DIR]"; }

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
while [[ $# -gt 0 ]]; do case "$1" in
  -r|--repo) REPO="$2"; shift 2 ;;
  -h|--help) Usage; exit 0 ;;
  *) Usage; exit 1 ;;
esac; done

echo "== 1. corpus health of the live vault (kb_report)"
python3 "$REPO/plugin/scripts/kb_report.py" -v "$REPO/vault"

echo
echo "== 2. + run stats from the ONNX battery's committed event stream"
python3 "$REPO/plugin/scripts/kb_report.py" -v "$REPO/vault" \
  -e "$REPO/docs/test-battery/run-2026-08-14-onnx/events.jsonl" | sed -n '/run stats/,$p'

echo
echo "== 3. regenerate the HTML dashboard from telemetry (proves it is derived)"
python3 "$REPO/plugin/scripts/make_dashboard.py" \
  -r "$REPO/docs/test-battery/run-2026-08-13" \
  -r "$REPO/docs/test-battery/run-2026-08-14-onnx" \
  -v "$REPO/vault" \
  -o "$REPO/docs/justification/dashboard/kb-dashboard.html"
echo "open docs/justification/dashboard/kb-dashboard.html"
