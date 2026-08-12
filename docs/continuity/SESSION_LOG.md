# SESSION LOG — team-kb (newest first)

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
