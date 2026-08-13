---
name: kb-battery
description: >
  Drive the live-fire E2E test battery: per-document GA submit → CA curate →
  GA retrieve-and-score loop against the battery vault. Use for "run the
  battery", "test ingestion end to end", "/team-kb:kb-battery <doc paths>".
argument-hint: <doc-path> [<doc-path> ...]
---

# kb-battery — E2E battery driver (you are the driver, in the main session)

Documents to run: $ARGUMENTS
(If empty: default corpus = docs/research/*.md then docs/whitepapers/*.md, ≥5 docs.)

Preconditions (verify, don't assume):
- Server pointed at the battery vault (launcher: `plugin/scripts/battery.sh`,
  sets TEAMKB_VAULT=~/vault/kb-test and TEAMKB_TRACE=1) — confirm via `reindex`
  (vault path is in the report).
- Genesis anchors: if the vault is empty, first commit 2-3 Concept anchor notes
  (from _meta/ontology.md, _meta/memory-model.md) with
  isolatedJustification "genesis anchor".

Per document (SEQUENTIAL — fresh CA fork each):
1. GA submit: call `submit_document(path)` yourself or via `/team-kb:kb-agent`.
   DUPLICATE = skip (already ingested).
2. CA curate: invoke `/team-kb:kb-curator` with the submission id + source path.
   Parse the fenced JSON report from its final message. status=failed → record,
   continue with next doc (NO infinite retry).
3. GA retrieval battery (8 searches, via `/team-kb:kb-agent` or directly):
   - FTS ×2: distinctive term; paraphrase
   - Semantic ×2: conceptual query; cross-doc analogy
   - Tag ×2: exact namespaced tag; `kb/<class>` prefix
   - Graph ×2: read_note backlinks on the doc; on a related anchor
   Score each 0-1 vs intent, one-line justification.

Full-corpus wrap-up:
4. One expected-absent probe (query for knowledge NOT in the corpus) — must
   return `verdict: absent`.
5. Relation back-pass: `add_relations` for any A→B edges where B landed after A.
6. `reindex` — counts into the record.
7. Deterministic pass gate: every doc retrieved by ≥1 search per modality
   (semantic waivers allowed on tiny corpus — document them); zero false
   absents; expected-absent probe correct. LLM scores are commentary
   (mean ≥ 0.7 secondary).
8. Evidence: copy from the vault → `docs/test-battery/run-<date>/`:
   - `.teamkb-events.jsonl` — structured per-phase events/metrics (always on;
     set `TEAMKB_RUN_ID` before the run so the run is filterable)
   - `.teamkb-trace.jsonl` — raw tool req/resp (TEAMKB_TRACE=1)
   - `metrics.jsonl` — per-document rollup:
     `python3 plugin/scripts/metrics_rollup.py -e <events> -o metrics.jsonl --summary`
   - scorecard.md + vault tree snapshot
9. `capture_episode` the battery run summary.
