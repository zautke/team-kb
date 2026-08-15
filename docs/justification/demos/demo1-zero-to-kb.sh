#!/usr/bin/env bash
# DEMO 1 — zero to knowledge base: cold start → full corpus ingested, curated,
# gate-checked and retrieval-verified. Entirely on this laptop, no network.
set -euo pipefail

Usage() { echo "Usage: demo1-zero-to-kb.sh [-r|--repo DIR] [-p|--python BIN]"; }

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
PY="${HOME}/vault/.models/onnx-venv/bin/python"
while [[ $# -gt 0 ]]; do case "$1" in
  -r|--repo)   REPO="$2"; shift 2 ;;
  -p|--python) PY="$2"; shift 2 ;;
  -h|--help)   Usage; exit 0 ;;
  *) Usage; exit 1 ;;
esac; done

V="$(mktemp -d /tmp/kb-demo1.XXXX)"
trap 'rm -rf "$V"' EXIT

echo "== 1. bootstrap an empty vault ($V)"
python3 "$REPO/plugin/scripts/bootstrap_vault.py" -v "$V" >/dev/null
find "$V" -maxdepth 1 -type d | sed "s|$V|  vault|"

echo
echo "== 2. run the FULL battery: 16 documents through the complete pipeline"
echo "   (chunk → embed locally via ONNX → 8 gates → graph → retrieval × 4 modalities)"
export TEAMKB_EMBED_BACKEND=onnx
export TEAMKB_ONNX_MODEL_DIR="$HOME/vault/.models/bge-micro-v2-onnx"
time "$PY" "$REPO/plugin/scripts/battery_run.py" -v "$V" -p all 2>&1 \
  | grep -E "DETERMINISTIC|FTS=|PROBE|verdict: absent" | tail -18

echo
echo "== 3. the vault is real markdown, openable in Obsidian right now"
ls "$V/knowledge/artifact" | head -4
echo "  ... $(find "$V" -name '*.md' -not -path '*_meta*' | wc -l | tr -d ' ') notes total"
