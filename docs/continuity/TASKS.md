# TASKS — team-kb

## Done (2026-08-11)

- [x] Research fan-out R1-R6 (docs/research/ + kb dossier notes)
- [x] Constitution v1.0.0 set (_meta/: constitution, ontology, memory-model, maintenance, tag registry, versions)
- [x] M0 source: TeamKb.Core / TeamKb.Mcp / TeamKb.Tests
- [x] net10.0 retarget (verified versions; xunit.v3)
- [x] the build host build pipeline (ssh <build-host>; C:\Users\me\dev\team-kb) — build 0 err, tests 18/18
- [x] Bring-up fixes: ClearPool teardown lock; C7 unanchored scope regex; FTS5 token quoting; MCP logs→stderr

## Open

- [x] M0.1 MCP handshake — RESOLVED 2026-08-11: harness stdin-EOF race, not a server bug; all 6 tools verified (VERIFY.md)
- [ ] Bump SQLitePCLRaw.bundle_e_sqlite3 (NU1903 GHSA-2m69-gcr7-jv3q)
- [x] GitHub remote added + pushed (github:/zautke/team-kb, 2026-08-12)
- [ ] M1 kickoff (see PLANS)
- [ ] Re-sync build host: replace scp-patched copy with git clone from origin

## Open (2026-08-12 — plugin pivot, approved plan)

- [x] Phase 1: vault bootstrap (repo vault/ + ~/vault/kb-test) — bfd2da8
- [x] Phase 2: plugin/ — teamkb_server.py (14 tools, 8 gates byte-parity) + 31 unittests + agents + skills + hooks
- [x] Phase 3: .github Copilot agents/skills (.agent.md spec verified from docs.github.com)
- [x] Phase 4: E2E battery — 13 docs, deterministic gate PASS after 2 iterations (embed sub-batching, resume, θ=0.30)
- [x] Phase 5: evidence docs/test-battery/run-2026-08-12/ + VERIFY.md M0.5 section
- [x] Telemetry: per-phase event stream, log_event tool, per-document rollup, aggregate stats, evidence packaging (2026-08-13)
- [x] First real ingestion into repo vault/ — 13 docs + 3 anchors, zero gate failures (81db1c6)
- [x] md→Note parser + reindex(rebuild=true); verified on markdown-only clone (6a021dd)
- [x] docs/agent-manual/ — 8 operational how-to docs, all examples live-verified (7c24e2d, 5fbb989, 111803d)
- [x] Register teamkb MCP server at project scope, portable paths (895eba8)
- [x] Restart a session to exercise native mcp__teamkb__* tools — RESOLVED 2026-08-16: tools appear in fresh sessions (deferred-tool listing confirms mcp__teamkb__* available)
- [x] Semantic channel on clone — DECIDED + shipped: rebuild re-embeds doc vectors from note text; demo4 proves semantic ok on md-only clone (ed4eb8b)
- [x] Repoint TEAMKB_EMBED_URL — default removed entirely; http backend fails fast without explicit URL; committed config infrastructure-free (ed4eb8b)
- [x] Local ONNX embedding backend (bge-micro-v2 default, nomic-v1.5 alt) + vector-space guard + per-model θ + fetch script + live verification (2026-08-13)
- [x] Justification-meeting package: docs/justification/ (walkthrough, 5 executed demos + transcripts, kb_report, HTML dashboard, 6 observability task specs) — 775af9f
- [x] Server-side closed-vocabulary re-check (C1/C3/C6) — gap found by demo 2: enums were client-schema-only (775af9f)
- Deferred (M1+): ANN, RRF, md→Note parser/full rebuild, submission GC, Copilot full battery, 4-value verdict, decay/MemRL, C4 auto-stub, tag-registry migrations; ~~observability T1–T6~~ ALL DONE 2026-08-15 (84ec71c)

## Blocked-until

(nothing — M0 fully verified, M1 unblocked)

## Open (2026-08-15 — OTel research fan-out)

- [x] docs/research/otel-agentic-csharp/ COMPLETE: 8 docs + README, all source-cited, dated 2026-08-15; roadmap 08 holds decisions D0-D4 for the user
- [x] MACDEV re-synced via git pull 2026-08-16 — canonical again at 588a18a; ~/dev/team-kb clone is a disposable spare
- [ ] Justification meeting: run pre-flight from docs/justification/02-demo-runbook.md the morning of
- [ ] OTel implementation kickoff: user decides D0–D4 (docs/research/otel-agentic-csharp/08), then direct the team
