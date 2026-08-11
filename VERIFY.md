# M0 Verification (run on adagio or the target machine — largo has no .NET SDK and no disk headroom)

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

## Verification results (adagio, dotnet 10.0.302, 2026-08-11)

- `dotnet build TeamKb.sln` — 0 errors (NU1903 warning: transitive SQLitePCLRaw.lib.e_sqlite3 2.1.11
  high-sev advisory GHSA-2m69-gcr7-jv3q — bump SQLitePCLRaw.bundle_e_sqlite3 explicitly in M1).
- `dotnet test TeamKb.sln` — **18/18 pass**. Three defects found+fixed during bring-up:
  1. Windows file lock in teardown → `SqliteConnection.ClearPool` in VaultStore.Dispose.
  2. C7 scope regex end-anchored → missed `conflict-files-obsidian-git.md`; now unanchored.
  3. FTS5 hyphen syntax (`no such column: topic`) → Search now token-quotes queries.
- MCP stdio: host logging rerouted to stderr (was polluting the protocol channel).

## OPEN ISSUE — MCP handshake smoke fails (unresolved)

Feeding initialize + initialized + tools/list JSON-RPC lines (verified-clean, file-based) into
`dotnet TeamKb.Mcp.dll` yields **zero stdout lines**; stderr shows transport reading then clean
shutdown at EOF. Expected: initialize response. Suspects: (a) response requires the client to keep
stdin open until reply flushed and the pipeline races EOF, (b) SDK 2.1.0 tool-discovery/DI issue
with static tools + injected VaultStore, (c) protocolVersion negotiation silently dropping.
Next debug steps: stderr at Debug level; test with `npx @modelcontextprotocol/inspector`; try the
SDK QuickstartWeatherServer sample as a known-good on the same box; check `WithToolsFromAssembly`
found the 6 tools (log at startup).

## Status / residual risk

- Authored source-only on largo (no dotnet SDK there): **not yet compiled**. Package versions were
  research-verified 2026-08-11 (ModelContextProtocol 2.1.0, Microsoft.Data.Sqlite 8.x); expect at
  most minor API-shape fixes on first build.
- `WithToolsFromAssembly()` + static tool classes with DI-injected VaultStore parameter follows the
  SDK 2.x sample pattern; verify parameter binding on first run.
