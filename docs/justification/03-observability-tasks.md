# Observability gaps — tasked out (spec-only)

Each item below is **not required for operation** — the system ingests,
curates, retrieves and self-reports today (see `01-walkthrough.md` §7).
All six were implemented and verified on 2026-08-15 (one working session) —
the statuses below record what shipped and how each was verified.

## T1. Retrieval-quality regression probes — S — **DONE** (RetrievalRegressionProbes, 4 tests, deterministic fake vectors; runs in `python3 -m unittest`)

**Problem:** retrieval correctness is currently proven by batteries run on
demand; a code change could silently degrade a channel between runs.
**Mechanism:** a canned probe set (N queries per modality with expected
verdict + expected permalink, including expected-absent probes) as a unittest
class that runs against a fixture vault in CI (`python3 -m unittest`).
**Files:** `plugin/mcp/test_teamkb_server.py` (new class), probe fixtures
inline.

## T2. Gate-violation trend report — S — **DONE** (`kb_report.py --gates`)

**Problem:** gate rejections are in the event stream but not aggregated over
time; can't answer "which gates fire most, is curation quality improving?"
**Mechanism:** extend `kb_report.py` with `--gates`: group `gate.eval` events
across one or more events.jsonl files by gate × week, table + JSON.
**Files:** `plugin/scripts/kb_report.py`.

## T3. Embed-backend health snapshot in kb_report — S — **DONE** (`kb_report.py --check-embed`; verified ok on onnx, clean fail on unset http URL)

**Problem:** `kb_report` shows corpus state but not whether the embedding
backend is currently reachable/working.
**Mechanism:** `--check-embed` flag: one 3-text embed round-trip, report
backend, model, dim, latency, ok/fail. Uses the existing `embed_texts` choke
point — no new code paths.
**Files:** `plugin/scripts/kb_report.py`.

## T4. θ auto-recalibration report — M — **DONE** (`plugin/scripts/theta_calibrate.py`; live run on the onnx battery vault: margin 0.072, recommended θ 0.716)

**Problem:** θ is seeded per model family from one calibration session; a
grown corpus may shift score distributions (bge margin is already narrow).
**Mechanism:** sampler that embeds K held-out true-match and K junk queries,
plots the two distributions (text histogram + JSON), recommends θ at the
midpoint, writes nothing — recommendation only, per-vault override stays a
human decision.
**Files:** new `plugin/scripts/theta_calibrate.py` (reuses `embed_texts`).

## T5. Session analytics from log_event — M — **DONE** (`kb_report.py --sessions`)

**Problem:** agent usage of the KB (which tools, hit/miss rates, absent-verdict
frequency) is captured in events but never summarized; can't answer "is the
team actually getting value?"
**Mechanism:** `kb_report --sessions`: aggregate `tool.end` + `ga.score` +
search-verdict events by run_id/day — searches per modality, absent rate,
top queries. Pure event-stream consumer.
**Files:** `plugin/scripts/kb_report.py`.

## T6. events.jsonl rotation policy — S — **DONE** (server startup rotation, `TEAMKB_EVENTS_MAX_MB` default 64; rotation live-verified)

**Problem:** the event log grows unbounded on a long-lived vault (669 events
per full battery; steady-state agent use is far lower, but still monotonic).
**Mechanism:** server-side size check at startup: over N MB → rename to
`.teamkb-events.<date>.jsonl` and start fresh; document archival in the agent
manual. No daemon.
**Files:** `plugin/mcp/teamkb_server.py` (~15 lines), `docs/agent-manual/`.

## Explicitly rejected (for the record)

- **Metrics service / Grafana / OTLP export** — violates the zero-dependency,
  no-services property that is itself a selling point. The JSONL streams are
  already machine-readable; anyone who wants Grafana can point an importer at
  them without touching the server.
