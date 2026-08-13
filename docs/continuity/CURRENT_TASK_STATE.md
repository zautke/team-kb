# CURRENT TASK STATE — team-kb

**As of:** 2026-08-12 (eve) · **Repo:** <repo-root> (origin: github:/zautke/team-kb) · **Phase:** M0.5 complete — plugin live, battery PASS

## State

- **All 5 plan phases done.** Vault bootstrapped (repo `vault/` + `~/vault/kb-test`), plugin built
  (`plugin/`: 14-tool zero-dep Python MCP server, kb-agent/kb-curator agents, kb-prime + 6 curate-* +
  kb-battery skills, PreCompact hook), Copilot side shipped (`.github/agents/*.agent.md` gpt-5.6-luna
  + xhigh, portable skills, AGENTS.md).
- **E2E battery PASS** (VERIFY.md M0.5 section; evidence `docs/test-battery/run-2026-08-12/`):
  13 docs + 3 anchors ingested through all 8 gates; 13/13 × 4 modalities deterministic recall;
  zero false absents; GA mean 0.99. Unit suite 31/31.
- Fixes landed during battery: embed sub-batching (8/req, 90s), submission resume, θ=0.30 calibration,
  Cloudflare User-Agent, run_server.sh vault-override resolution.
- C# stack still frozen reference in `src/`.

## Telemetry (added 2026-08-13)

Structured event stream `$TEAMKB_VAULT/.teamkb-events.jsonl` (always on) covers every
pipeline phase per document: tool.start/end w/ durations + extracted metrics, gate.eval
(all 8 gates each pass), chunk.done, embed.batch/done (incl. retries), submission.failed,
plus agent-judgment phases via the new `log_event` tool (CA-1 strategy, CA-6 metadata,
CA-11 report, GA-4 scoring — required by both agent definitions). Correlation keys:
run_id/seq/phase/doc, with filename→submission→permalink chaining and a scoped
pipeline-context slot for doc-less tools. `metrics_rollup.py` → per-document records
+ `--aggregate` corpus phase stats (p50/p95, gate tallies, embed retries).
`collect_evidence.sh` packages a run. Schema: `docs/telemetry-events.md`.

Caught by this layer immediately: fresh vaults seeded semantic θ=0.45 and returned
absent for a true conceptual match — seed is now the calibrated 0.30.

## Resume point

System is operational — team can ingest documents now:
- Prime: `/team-kb:kb-prime` · Ingest: submit via kb-agent → `/team-kb:kb-curator` · Battery: `plugin/scripts/battery.sh`
- Repo `vault/` is EMPTY of content (battery ran against `~/vault/kb-test`); first real ingestion into
  repo vault = rerun `battery_run.py -v vault -p ingest` or curate live via agents.

## Next (M1 candidates, in TASKS)

RRF fusion wrapper, md→Note parser + full reindex rebuild, ANN if corpus grows, Copilot full battery,
4-value verdict, decay/MemRL, C4 auto-stub, submission GC.
