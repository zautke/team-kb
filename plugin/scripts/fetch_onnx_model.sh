#!/usr/bin/env bash
# Fetch a local ONNX embedding model for TEAMKB_EMBED_BACKEND=onnx.
# The MCP server never downloads anything itself; this script is the only
# sanctioned path for putting model weights on disk.
set -euo pipefail

Usage() {
  cat <<'EOF'
Usage: fetch_onnx_model.sh [-m|--model NAME] [-d|--dest DIR] [-q|--quant Q]

  -m, --model   bge-micro-v2 (default) | nomic-v1.5
  -d, --dest    destination directory (default: ~/vault/.models/<model>-onnx)
  -q, --quant   quantized (default) | fp32
  -h, --help    this text

Downloads model ONNX + tokenizer.json from HuggingFace. Preflights free disk
(>= 1 GiB required). Point TEAMKB_ONNX_MODEL_DIR at the destination directory.
EOF
}

MODEL="bge-micro-v2"
DEST=""
QUANT="quantized"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--model) MODEL="$2"; shift 2 ;;
    -d|--dest)  DEST="$2";  shift 2 ;;
    -q|--quant) QUANT="$2"; shift 2 ;;
    -h|--help)  Usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; Usage; exit 1 ;;
  esac
done

case "$MODEL" in
  bge-micro-v2) REPO="TaylorAI/bge-micro-v2" ;;
  nomic-v1.5)   REPO="nomic-ai/nomic-embed-text-v1.5" ;;
  *) echo "unknown model: $MODEL (bge-micro-v2 | nomic-v1.5)" >&2; exit 1 ;;
esac

case "$QUANT" in
  quantized) ONNX_FILE="onnx/model_quantized.onnx"; LOCAL_ONNX="model_quantized.onnx" ;;
  fp32)      ONNX_FILE="onnx/model.onnx";           LOCAL_ONNX="model.onnx" ;;
  *) echo "unknown quant: $QUANT (quantized | fp32)" >&2; exit 1 ;;
esac

DEST="${DEST:-$HOME/vault/.models/${MODEL}-onnx}"

avail_kb=$(df -k "$HOME" | awk 'NR==2 {print $4}')
if (( avail_kb < 1048576 )); then
  echo "ABORT: <1 GiB free on \$HOME ($((avail_kb/1024)) MiB) — no download." >&2
  exit 1
fi

mkdir -p "$DEST"
BASE="https://huggingface.co/${REPO}/resolve/main"
for pair in "${ONNX_FILE}:${LOCAL_ONNX}" "tokenizer.json:tokenizer.json"; do
  remote="${pair%%:*}"; local_name="${pair##*:}"
  out="$DEST/$local_name"
  if [[ -s "$out" ]]; then
    echo "exists: $out ($(du -h "$out" | cut -f1)) — skipping"
    continue
  fi
  echo "fetching $BASE/$remote"
  curl -fSL --retry 2 -o "$out.part" "$BASE/$remote"
  mv "$out.part" "$out"
  echo "wrote $out ($(du -h "$out" | cut -f1))"
done

echo
echo "done. use:"
echo "  export TEAMKB_EMBED_BACKEND=onnx"
echo "  export TEAMKB_ONNX_MODEL_DIR=$DEST"
[[ "$MODEL" == "nomic-v1.5" ]] && echo "  export TEAMKB_EMBED_MODEL=nomic-embed-text-v1.5-onnx"
exit 0
