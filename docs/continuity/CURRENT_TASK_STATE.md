# CURRENT TASK STATE — team-kb

**As of:** 2026-08-11 · **Repo:** /Volumes/MACDEV/team-kb (local only, no remote) · **Phase:** M0 nearly done

## State

- Constitution v1.0.0 (`_meta/`), research dossier R1-R6 (`docs/research/` + kb `_governance/research/rebuild-2026-08/`), M0 source complete.
- Retargeted **net10.0** (C# 14; Microsoft.Data.Sqlite + Hosting 10.0.10, ModelContextProtocol 2.1.0, xunit.v3 3.2.2). Research: `docs/research/` + plan.
- **Build+test on adagio** (`ssh adagio`, Windows, dotnet 10.0.302, C:\Users\me\dev\team-kb): build 0 errors, **tests 18/18 pass**.
- largo is unusable for builds: no SDK, boot disk ~200-500MB free (ENOSPC events mid-session).

## Resume point — ONE open issue

**MCP stdio handshake returns nothing.** Clean JSON-RPC (initialize → initialized → tools/list) from
`C:\Users\me\dev\mcp-smoke.jsonl` piped into `dotnet TeamKb.Mcp\bin\Debug\net10.0\TeamKb.Mcp.dll`
(TEAMKB_VAULT set) → 0 stdout lines; stderr shows transport start + clean EOF shutdown.
Debug order: (1) stderr Debug-level logs, (2) `npx @modelcontextprotocol/inspector` against the dll,
(3) run SDK QuickstartWeatherServer on adagio as known-good, (4) verify WithToolsFromAssembly
discovered the 6 KbTools (static class + DI-injected VaultStore param — binding suspect).
Full notes: `VERIFY.md` "OPEN ISSUE".

## Sync ritual (largo ↔ adagio)

Edit locally → `scp <files> adagio:C:/Users/me/dev/team-kb/src/...` → `ssh adagio 'cd C:\Users\me\dev\team-kb\src; dotnet test TeamKb.sln'`.
Beware: (a) macOS tar AppleDouble `._*` files break the build — use `COPYFILE_DISABLE=1 tar` or purge; (b) PowerShell here-strings: `\"` stays literal — ship JSON via file, never inline.

## Then

M1 per plan (`docs/plan-2026-08-11-teardown-rebuild.md`): embeddings (LM Studio/ONNX on target), RRF hybrid, verdict contract everywhere, plan_turn router. Also: bump SQLitePCLRaw (NU1903), decide GitHub remote.
