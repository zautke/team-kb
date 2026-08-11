# TASKS — team-kb

## Done (2026-08-11)

- [x] Research fan-out R1-R6 (docs/research/ + kb dossier notes)
- [x] Constitution v1.0.0 set (_meta/: constitution, ontology, memory-model, maintenance, tag registry, versions)
- [x] M0 source: TeamKb.Core / TeamKb.Mcp / TeamKb.Tests
- [x] net10.0 retarget (verified versions; xunit.v3)
- [x] adagio build pipeline (ssh adagio; C:\Users\me\dev\team-kb) — build 0 err, tests 18/18
- [x] Bring-up fixes: ClearPool teardown lock; C7 unanchored scope regex; FTS5 token quoting; MCP logs→stderr

## Open

- [x] M0.1 MCP handshake — RESOLVED 2026-08-11: harness stdin-EOF race, not a server bug; all 6 tools verified (VERIFY.md)
- [ ] Bump SQLitePCLRaw.bundle_e_sqlite3 (NU1903 GHSA-2m69-gcr7-jv3q)
- [ ] Decide GitHub remote + push
- [ ] M1 kickoff (see PLANS)
- [ ] Sync fixes back: adagio copy is scp-patched — re-tar from largo (COPYFILE_DISABLE=1) or git-clone once remote exists

## Blocked-until

(nothing — M0 fully verified, M1 unblocked)
