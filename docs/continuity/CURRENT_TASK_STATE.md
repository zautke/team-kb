# CURRENT TASK STATE — team-kb

**As of:** 2026-08-16 · **Repo:** /Volumes/MACDEV/team-kb (origin: github:/zautke/team-kb, head 588a18a) · **Phase:** M0.8 — operational, justified, gap-closed

## State

**KB live, fully local-capable, meeting-ready.** All open roadmap gaps closed 2026-08-14/15.

- **Server**: `plugin/mcp/teamkb_server.py`, 15 tools, 8 gates + server-side closed-vocab
  re-check (C1/C3/C6). Dual embed backends: `http` (no default URL — fails fast) and `onnx`
  (bge-micro-v2 17 MB local, ~20 ms/chunk; nomic-v1.5 documented alt). Vector-space guard;
  per-model θ seeds (nomic 0.30 / bge 0.69). Tests **63/63**.
- **Semantic survives clone** (ed4eb8b): `reindex(rebuild=true)` re-embeds doc vectors from
  note text; demo 4 proves md-only clone → FTS identical BM25 + semantic `ok` 0.702, no network.
- **ONNX battery** (a67b49a): deterministic PASS first run — 16/16 committed, 0 gate failures,
  GA 10/10, 72 batches 0 retries, 5.9 s server-side pipeline.
- **Justification package** `docs/justification/` (775af9f, 84ec71c): walkthrough (evidence-traced),
  5 executed demo scripts + transcripts, `kb_report` (+ --gates/--check-embed/--sessions),
  `theta_calibrate.py`, HTML dashboard regenerable from telemetry. **Observability T1–T6 all done.**
- **OTel-agentic-C# research corpus** `docs/research/otel-agentic-csharp/` (70eeb06, 588a18a):
  8 docs + README, all source-cited @2026-08-15. Doc 08 = phased roadmap; **decisions D0–D4
  reserved for the user** (content capture, trace unit, ACA/AKS, sampling policies, cost posture).
- Committed config is infrastructure-free (personal tunnel removed everywhere live).
- MCP server registered project-scope; `mcp__teamkb__*` tools now available in fresh sessions.

## Resume point

Nothing in flight. Next moves are user-directed:

1. **Justification meeting** — package ready (`docs/justification/README.md`); pre-flight in 02-runbook.
2. **OTel implementation team** — starts from research corpus doc 08 after user decides D0–D4.
3. M1 retrieval items (RRF etc.) remain deliberately deferred until corpus grows.

## Environment notes

- MACDEV volume dropped mid-session 2026-08-15; work continued from clone `~/dev/team-kb`
  (all pushed). MACDEV re-synced via git pull 2026-08-16 — **both copies at 588a18a; MACDEV
  canonical again**. `~/dev/team-kb` can be deleted or kept as spare.
- ONNX runtime venv + model live at `~/vault/.models/` (onnx-venv, bge-micro-v2-onnx) — needed
  for demos 1/4/5 and any onnx-backend run on this machine.
- Local embed env (not committed): `TEAMKB_EMBED_BACKEND=onnx`,
  `TEAMKB_ONNX_MODEL_DIR=~/vault/.models/bge-micro-v2-onnx`.
