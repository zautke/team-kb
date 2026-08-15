# SESSION LOG — team-kb (newest first)

## 2026-08-15 — justification-meeting package (775af9f)

Built docs/justification/: evidence-traced walkthrough for a skeptical principal
engineer, runbook + 5 self-contained demo scripts (all executed, transcripts
committed), kb_report (corpus health + run stats), regenerable single-file HTML
evidence dashboard (hosted 994.9s vs ONNX 5.9s comparison), 6 sized observability
task specs. Demo 2 exposed a real gap — closed-vocab enums were enforced only by
client-side tool schemas; server now re-checks C1/C3/C6 for any caller. Tests 55/55.
Earlier (2026-08-14): full battery vs ONNX backend — deterministic PASS first run
(a67b49a).

## 2026-08-13 (later) — vault populated, manual written, server registered

Closed the portability gap first: the constitution called markdown canonical but nothing
could re-derive the index, so a cloned vault answered `absent` to everything. Added
`parse_markdown` (exact serializer inverse) + `reindex(rebuild=true)` (6a021dd); proven on a
markdown-only copy — 29 notes, 22 edges, 6.5ms, identical BM25 scores to the original.

Populated repo `vault/` (81db1c6): 13 documents + 3 anchors, 16 commits, zero gate failures,
zero embed retries; all four modalities verified in place. Telemetry artifacts moved to
gitignore — run evidence belongs in docs/test-battery/, not the vault.

Wrote `docs/agent-manual/` (7c24e2d, 5fbb989, 111803d): eight documents from zero-to-running
through troubleshooting and MCP config. Every command executed live before being written, which
caught a real defect — the `kb/*` reserved-namespace message was unreachable behind the generic
namespace check, so agents got the less useful error.

Registered the server at project scope (895eba8) with portable `${CLAUDE_PROJECT_DIR:-.}` paths;
`claude mcp list` → Connected. Approval had to be recorded manually: the trust dialog only fires
at session start, so the user's stated approval was not captured by the mechanism.

## 2026-08-13 — telemetry layer: per-phase events + per-document metrics

Answered "can we capture all runbook output?" — previously no (only opt-in raw tool
trace: no timings, no doc correlation, no phase labels, metrics buried in result
strings, nothing for agent-judgment steps). Built the structured event stream
(gate/chunk/embed/tool/agent events with run_id/seq/phase/doc/duration_ms), the
`log_event` tool so agents log non-tool phases, the per-document rollup with
filename→submission→permalink chaining, corpus phase-stat aggregation, and
one-command evidence packaging. Tests 39/39. The layer immediately caught a real
defect: fresh vaults seeded θ=0.45 (pre-calibration) so a true conceptual match
returned absent — seed corrected to the calibrated 0.30.

## 2026-08-12 (evening) — plugin built, E2E battery PASS

Executed all 5 phases: vault bootstrap ×2; teamkb_server.py (zero-dep, 14 tools, 31/31 tests);
plugin agents/skills/hooks (validate clean); Copilot .agent.md (spec fetched from GitHub docs —
description required, model free string, mcp-servers inline). Battery vs ~/vault/kb-test:
iteration 1 exposed embed timeouts on whitepaper batches (fixed: sub-batch 8/90s + resume) and
θ miscalibration (0.45→0.30 on observed distribution). Final: 13/13 docs × 4 modalities PASS,
zero false absents, GA mean 0.99, back-pass + DCF episodes + battery episode captured.
Evidence committed docs/test-battery/run-2026-08-12/. System operational for team ingestion.

## 2026-08-12 (later) — docs scrub, plugin pivot, battery plan approved

Scrubbed all machine/network refs from docs for new-team handoff (commit 564a8ff). Then planning
cycle for "vault + ingestion + curator gate" goal: explore → design → user pivot (C# punted;
lightweight "copilot plugin" wanted) → conformance map vs _meta/docs (blocking items: enum schemas,
byte-parity serializer, FTS quoting, TEAMKB_VAULT SSoT, no fs-write for agents) → SOTA syntax research
(plugin.json/subagent/SKILL.md/Copilot .agent.md/MCP 2026-07-28 spec, all official-doc-verified;
`5.6-luna-xtrahigh` = OpenAI gpt-5.6-luna + xhigh effort, invalid in Claude frontmatter → dual-target)
→ E2E battery runbook (GA/CA per-doc, ~/vault/kb-test) → 3 disparate reviewers → Appendix B gap
addendum (server 6→12 tools, embeddings via hosted nomic w/ task prefixes, deterministic scoring,
CA-8 verification-only, DCF as episode). Plan approved; implementation starting.

## 2026-08-11 — genesis + net10 + the build host verification

Teardown of obsidian-vault-config compliance kit ordered; rebuild as team-kb. 6-agent research
fan-out (R1 self-evolving KG, R2 self-learning loops, R3 C# MAF/MCP, R4 jcodemunch, R5+R6 master-kb
post-mortems incl. formal model). Plan approved (`docs/plan-2026-08-11-teardown-rebuild.md`).
Executed: research filed (docs + kb `_governance/research/rebuild-2026-08/` 7 notes); constitution
v1.0.0; M0 scaffold; genesis commit 7b308d6. Then net10.0 retarget (research-verified versions) and
Build-host bring-up: build 0 errors, tests 18/18 after 3 real fixes (Windows sqlite pool lock, C7 regex
anchor, FTS5 hyphen quoting) + MCP logging→stderr. OPEN: MCP stdio handshake returns zero responses
to clean JSON-RPC (see VERIFY.md OPEN ISSUE + CURRENT_TASK_STATE resume steps). The authoring Mac hit ENOSPC
twice mid-session (boot vol ~200-500MB free) — all builds stay on the build host.

## 2026-08-12 — remote, whitepapers, Obsidian plane, M0 closed

Remote added + pushed (github:/zautke/team-kb) — team-kb is now the primary working dir;
obsidian-vault-config retired. Prior session also: 6 whitepapers (docs/whitepapers/, ~4.3k lines),
Obsidian integration (R7 research, typed-properties serializer, kb/* tag plane, kb.base dashboards),
and M0.1 resolved — "silent MCP server" was a harness stdin-EOF race, all 6 tools verified.
M0 done. Next: M1 (embeddings, RRF, verdict contract, plan_turn router). Also open: SQLitePCLRaw bump.
