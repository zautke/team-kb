# E2E battery — local ONNX backend (2026-08-14)

Full Appendix A/B battery (same driver, same curated manifest as the hosted
runs) against a fresh vault `~/vault/kb-test-onnx`, embedding entirely
on-machine: `TEAMKB_EMBED_BACKEND=onnx`, `TaylorAI/bge-micro-v2` int8 (17 MB,
384-d), onnxruntime 1.28.0 CPU. Zero network calls for embeddings.

## Result: DETERMINISTIC GATE PASS — first run, zero rework

| Check | Result |
|---|---|
| Documents committed | 16/16 (3 genesis anchors + 13 corpus docs), 12 pipeline phases per corpus doc, **0 gate failures** |
| Modality recall | 13/13 docs: FTS=Y SEM=Y TAG=Y GRAPH=Y |
| Expected-absent probes | FTS probe `absent` ✓; semantic probe `absent` ✓ (top 0.671 < θ=0.69) |
| GA scorecard | 10/10 searches scored **1.0** (fts×2, sem×2, tag×2, graph×2, probe×2) |
| Embed batches | 72, **0 retries**, all `backend:"onnx"` |
| Embed latency | p50 77.9 ms / p95 198.3 ms / max 235.4 ms per batch (≤8 texts) |
| Whole-battery wall time | **5.9 s** end to end |

## vs hosted baseline (run-2026-08-12, nomic v2-moe over HTTPS)

- Hosted first iteration hit batch timeouts (90 s ceiling, retries, resume
  path needed); ONNX run had zero retries and finished the entire
  ingest+retrieve battery in under 6 seconds.
- Semantic margin is thinner than nomic's (absent probe cleared θ by 0.019
  vs nomic's comfortable 0.13 gap) — bge-micro's quality ceiling. All 26
  semantic checks (13 docs × 2 + probes) still resolved correctly.

## Evidence files

- `events.jsonl` — 669 structured events (full per-phase telemetry, run
  `run-20260814-133416`)
- `trace.jsonl` — raw MCP request/response bodies
- `per-doc-metrics.jsonl` — 16 per-document rollup records
- `phase-stats.json` — corpus-level phase aggregates
