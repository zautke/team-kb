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

## Resume point

System is operational — team can ingest documents now:
- Prime: `/team-kb:kb-prime` · Ingest: submit via kb-agent → `/team-kb:kb-curator` · Battery: `plugin/scripts/battery.sh`
- Repo `vault/` is EMPTY of content (battery ran against `~/vault/kb-test`); first real ingestion into
  repo vault = rerun `battery_run.py -v vault -p ingest` or curate live via agents.

## Next (M1 candidates, in TASKS)

RRF fusion wrapper, md→Note parser + full reindex rebuild, ANN if corpus grows, Copilot full battery,
4-value verdict, decay/MemRL, C4 auto-stub, submission GC.
