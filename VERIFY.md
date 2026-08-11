# M0 Verification (run on the target machine — largo has no .NET SDK and no disk headroom)

Requires .NET 8 SDK.

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

## Status / residual risk

- Authored source-only on largo (no dotnet SDK there): **not yet compiled**. Package versions were
  research-verified 2026-08-11 (ModelContextProtocol 2.1.0, Microsoft.Data.Sqlite 8.x); expect at
  most minor API-shape fixes on first build.
- `WithToolsFromAssembly()` + static tool classes with DI-injected VaultStore parameter follows the
  SDK 2.x sample pattern; verify parameter binding on first run.
