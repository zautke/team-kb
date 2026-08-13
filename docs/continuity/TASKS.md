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
- [ ] First real ingestion into repo vault/ (battery ran vs ~/vault/kb-test)
- Deferred (M1+): ANN, RRF, md→Note parser/full rebuild, submission GC, Copilot full battery, 4-value verdict, decay/MemRL, C4 auto-stub, tag-registry migrations

## Blocked-until

(nothing — M0 fully verified, M1 unblocked)
