# M0 Verification (run on the build host or the target machine — the authoring Mac has no .NET SDK and no disk headroom)

Requires .NET 10 SDK (net10.0 / C# 14; verified against SDK 10.0.302, packages 10.0.10,
ModelContextProtocol 2.1.0 native-net10.0, xunit.v3 3.2.2 — research-verified 2026-08-11).
Note: .NET 10 CLI writes non-command chatter to stderr — harmless for MCP stdio (protocol uses stdout).

```bash
cd src
dotnet build            # expect: 0 errors
dotnet test             # expect: all GateTests pass — each replays a real master-kb defect
```

GateTests coverage → post-mortem countermeasures:

| Test | Countermeasure |
|---|---|
| MissingProvenance / PlaceholderProvenance / HypothesisWithHighConfidence | #1 gates in code |
| DanglingRelationTarget_Rejected | #2 write-time link resolution (C4) |
| Backlinks_AreComputed | #3 computed inverses (C5) |
| Path_IsDerivedFromClass | #4 closed folder set (C1) |
| ExactPermalinkCollision / NearDuplicateTitle | #5 dedup merge-or-distinguish (C2/I4) |
| UnlinkedUnjustified_Rejected | #6→I1 connectivity |
| EdgeSignatureViolation / UnregisteredTag / ScopePredicate | #7 closed vocabularies (C3/C6/C7) |
| EpisodeCapture_AppendOnly / Search_FindsCommitted | episodic tier + honesty verdicts |

## MCP conformance

```bash
export TEAMKB_VAULT=$PWD/../vault-dev
dotnet run --project TeamKb.Mcp   # stdio server
# then from an MCP client/inspector: tools/list must show propose_note, commit_note,
# capture_episode, search_notes, read_note, register_tag — with EntityClass/Verb/ObsKind
# enums visible in the input schemas.
```

## Verification results (build host, dotnet 10.0.302, 2026-08-11)

- `dotnet build TeamKb.sln` — 0 errors (NU1903 warning: transitive SQLitePCLRaw.lib.e_sqlite3 2.1.11
  high-sev advisory GHSA-2m69-gcr7-jv3q — bump SQLitePCLRaw.bundle_e_sqlite3 explicitly in M1).
- `dotnet test TeamKb.sln` — **18/18 pass**. Three defects found+fixed during bring-up:
  1. Windows file lock in teardown → `SqliteConnection.ClearPool` in VaultStore.Dispose.
  2. C7 scope regex end-anchored → missed `conflict-files-obsidian-git.md`; now unanchored.
  3. FTS5 hyphen syntax (`no such column: topic`) → Search now token-quotes queries.
- MCP stdio: host logging rerouted to stderr (was polluting the protocol channel).

## RESOLVED — MCP handshake (was: "server silent")

Root cause: **test-harness stdin-EOF race, not a server bug.** Piping the JSON-RPC lines and
closing stdin immediately shut the host down before responses flushed. Holding stdin open
(`& { Get-Content smoke.jsonl; Start-Sleep 5 } | dotnet TeamKb.Mcp.dll`) yields correct
behavior (verified on build host 2026-08-11):
- initialize → `{"protocolVersion":"2025-06-18", "serverInfo":{"name":"TeamKb.Mcp"}, tools:{listChanged:true}}`
- tools/list → all 6 tools: capture_episode, propose_note, read_note, register_tag,
  search_notes, commit_note.
Real MCP clients hold stdin open for the session — no code change needed. M0 fully verified.

## Status / residual risk

- Authored source-only on the authoring Mac (no dotnet SDK there): **not yet compiled**. Package versions were
  research-verified 2026-08-11 (ModelContextProtocol 2.1.0, Microsoft.Data.Sqlite 8.x); expect at
  most minor API-shape fixes on first build.
- `WithToolsFromAssembly()` + static tool classes with DI-injected VaultStore parameter follows the
  SDK 2.x sample pattern; verify parameter binding on first run.

---

# M0.5 Verification — Python plugin stack + E2E battery (2026-08-12, authoring Mac, python3 stdlib only)

The C# stack above is frozen reference; the live path is `plugin/mcp/teamkb_server.py`
(zero-dependency port + battery surface). Full evidence: `docs/test-battery/run-2026-08-12/`.

## Unit suite (ported GateTests + serializer parity + battery surface + protocol)

```bash
cd plugin/mcp && python3 -m unittest test_teamkb_server -v
# Ran 31 tests ... OK          (05-unittest.log)
```

## MCP handshake smoke (stdin held open — see M0.1 lesson)

initialize → serverInfo teamkb/1.0.0, protocolVersion 2025-06-18; tools/list → 14 tools
with enum arrays in inputSchema (C1/C6 tier-1 enforcement visible at the API);
tools/call search_notes on empty vault → `verdict: absent`; `server/discover` → clean -32601.

## E2E battery (vault ~/vault/kb-test; hosted nomic-embed-text-v2-moe)

- Ingested through full gated pipeline: 3 genesis anchors + 13 documents
  (7 research + 6 whitepapers) + 13 DCF episodes + battery episode.
  Final index: 30 notes, 23 edges, 291 chunks, 13 doc embeddings, 14 tags.
- Iteration 1 → 5 whitepaper embed timeouts → sub-batching fix + resume path →
  iteration 2 all committed. Anchors idempotently C2-rejected on rerun.
- θ_semantic calibrated 0.45 → 0.30 (true-match floor 0.30, true-absent ceiling 0.163).
- **Deterministic gate PASS**: 13/13 docs retrieved by all 4 modalities
  (FTS, semantic, tag, graph); zero false absents; both expected-absent probes honest.
  GA mean alignment score 0.99 (scorecard.md).
- Back-pass verified: add_relations wrote markdown + edge; inverse backlink computed.
- Sample rendered note: 07-sample-note.md (full frontmatter, kb/* tag plane,
  wikilink relations, typed observations).

---

# M0.6 Verification — instrumented pipeline (2026-08-13)

Telemetry layer added: every pipeline phase emits structured events; the battery's
own numbers are now derived from that stream rather than narrated.
Evidence: `docs/test-battery/run-2026-08-13/` (scorecard, events, per-document
metrics, corpus phase stats, trace).

```bash
cd plugin/mcp && python3 -m unittest test_teamkb_server   # Ran 39 tests ... OK
```

Single clean run, fresh vault, no reruns:

- 13 documents + 3 anchors, **12 instrumented phases per document**, 669 events
- 0 gate failures across 32 validator passes; 0 embed retries across 72 batches
- Deterministic gate **PASS** (13/13 docs × 4 modalities, 0 false absents)
- GA modality battery **10/10** (was 9/10 before the θ fix below)
- Index: 29 notes, 22 edges, 291 chunks, 13 doc embeddings, 0 missing files
- Phase latency (p50/p95): embedding 33.2 s / 91.1 s dominates; every gate,
  chunk, commit, link and report phase is sub-millisecond

**Defect found by the telemetry itself**: a fresh vault seeded semantic θ at the
pre-calibration 0.45, so a true conceptual match returned `absent` (SEM-1 scored
0.0). The 0.30 calibration had only ever been written into the first vault's meta
table. Seed corrected; SEM-1 now passes. Prior runs' PASS verdicts were correct on
their own gate but concealed this, because scores existed only as prose.
