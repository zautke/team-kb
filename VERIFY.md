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
