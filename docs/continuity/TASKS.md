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

- [ ] Phase 1: vault bootstrap (repo vault/ + ~/vault/kb-test, parameterized)
- [ ] Phase 2: plugin/ — teamkb_server.py (12 tools, 8 gates byte-parity §F) + unittest + agents + skills + hooks + commands
- [ ] Phase 3: .github Copilot agents/skills (verify .agent.md fields from official docs first)
- [ ] Phase 4: E2E battery ≥5 docs (Appendix A/B), iterate until deterministic gate green
- [ ] Phase 5: evidence → docs/test-battery/run-<date>/ + VERIFY.md + commits
- Deferred (M1+): ANN, RRF, md→Note parser/full rebuild, submission GC, Copilot full battery, 4-value verdict, decay/MemRL, C4 auto-stub, tag-registry migrations

## Blocked-until

(nothing — M0 fully verified, M1 unblocked)
