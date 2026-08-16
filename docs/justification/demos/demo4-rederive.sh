#!/usr/bin/env bash
# DEMO 4 — markdown is canonical, the index is disposable. Clone ONLY the
# markdown, rebuild the index from it, and show identical BM25 ranking.
# Answers: "what happens when the database corrupts / what do we actually own?"
set -euo pipefail

Usage() { echo "Usage: demo4-rederive.sh [-r|--repo DIR] [-v|--vault DIR]"; }

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
VAULT="$REPO/vault"
while [[ $# -gt 0 ]]; do case "$1" in
  -r|--repo)  REPO="$2"; shift 2 ;;
  -v|--vault) VAULT="$2"; shift 2 ;;
  -h|--help)  Usage; exit 0 ;;
  *) Usage; exit 1 ;;
esac; done

C="$(mktemp -d /tmp/kb-demo4.XXXX)"
trap 'rm -rf "$C"' EXIT
# local ONNX so the rebuild's re-embed needs no network (FTS steps unaffected)
export TEAMKB_EMBED_BACKEND=onnx
export TEAMKB_ONNX_MODEL_DIR="$HOME/vault/.models/bge-micro-v2-onnx"
KBC() { python3 "$REPO/plugin/scripts/kbcall.py" -v "$C" "$@"; }
KBO() { python3 "$REPO/plugin/scripts/kbcall.py" -v "$VAULT" "$@"; }

echo "== 0. ensure the original vault is indexed (fresh git clones ship no db —"
echo "     the index is rebuilt from markdown, which is the whole point)"
KBO -t reindex -a '{"rebuild":true}' | head -1   # idempotent; existing embeddings kept

echo
echo "== 1. clone markdown ONLY (no database, no index)"
rsync -a --include='*/' --include='*.md' --include='*.base' --exclude='*' "$VAULT/" "$C/"
echo "  cloned $(find "$C" -name '*.md' | wc -l | tr -d ' ') md files; db present? $(test -f "$C/.teamkb.db" && echo yes || echo no)"

echo
echo "== 2. rebuild the entire index from markdown"
KBC -t reindex -a '{"rebuild":true}' | head -2

echo
echo "== 3. identical BM25 ranking: original vault vs rebuilt clone"
Q='{"query":"consolidation"}'
echo "--- original:"; KBO -t search_notes -a "$Q" | head -4
echo "--- rebuilt clone:"; KBC -t search_notes -a "$Q" | head -4

echo
echo "== 4. semantic channel ALSO survives the clone — re-embedded from note"
echo "     text during rebuild (local ONNX, no network)"
KBC -t semantic_search -a '{"query":"how episodes consolidate into knowledge"}' | head -4
