#!/usr/bin/env bash
# DEMO 3 — four independent retrieval modalities against the live repo vault,
# plus the verdict honesty contract: a query with no real answer says so
# (with the top score as evidence) instead of returning plausible noise.
set -euo pipefail

Usage() { echo "Usage: demo3-retrieval.sh [-r|--repo DIR] [-v|--vault DIR]"; }

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
VAULT="$REPO/vault"
while [[ $# -gt 0 ]]; do case "$1" in
  -r|--repo)  REPO="$2"; shift 2 ;;
  -v|--vault) VAULT="$2"; shift 2 ;;
  -h|--help)  Usage; exit 0 ;;
  *) Usage; exit 1 ;;
esac; done

KB() { python3 "$REPO/plugin/scripts/kbcall.py" -v "$VAULT" "$@"; }

echo "== 1. FTS/BM25 — exact + paraphrase"
KB -t search_notes -a '{"query":"bi-temporal"}' | head -3
KB -t search_notes -a '{"query":"post-mortem"}' | head -3

echo
echo "== 2. semantic — conceptual query (needs the embedding endpoint for the query vector)"
KB -t semantic_search -a '{"query":"how does the system stop two notes about the same thing"}' | head -3

echo
echo "== 3. tag — exact namespaced + class-plane prefix"
KB -t search_by_tag -a '{"tag":"domain/curation"}' | head -3
KB -t search_by_tag -a '{"tag":"kb/Concept","prefix":true}' | head -4

echo
echo "== 4. graph — 1-hop backlinks with inverse verbs, from an anchor"
KB -t read_note -a '{"permalink":"knowledge/concept/gates-as-code"}' | grep -A6 "Backlinks" | head -7

echo
echo "== 5. HONESTY: queries with no true answer → verdict: absent, top score shown"
KB -t search_notes -a '{"query":"kubernetes ingress controller"}' | head -2
KB -t semantic_search -a '{"query":"recipe for sourdough bread"}' | head -2
