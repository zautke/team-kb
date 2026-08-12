# AGENTS.md — team-kb

Repo = a gated knowledge system: markdown-canonical Obsidian vault (`vault/`),
zero-dependency Python MCP server (`plugin/mcp/teamkb_server.py`), dual-target
agent plugin (Claude Code: `plugin/`; Copilot CLI: `.github/agents`,
`.github/skills`). The C# stack in `src/` is frozen reference — do not modify,
do not build here.

## Hard rules

1. **Never hand-edit vault markdown.** The MCP server (propose→commit) is the
   only write path; hand edits bypass every constitution gate.
2. **Never write under `vault/_meta/**`** or edit notes tagged `status/anchor`.
3. **Vocabulary is closed** (10 classes, 14 verbs, 12 observation kinds,
   5 tag namespaces). No tool can change it; never propose to.
4. **Verdict honesty**: `verdict: absent` from any search = the knowledge does
   not exist. Report the gap and stop — no synonym retries.
5. **No local model weights** on the authoring machine — embeddings run against
   the hosted endpoint (TEAMKB_EMBED_URL; default is the team's tunnel).

## Start here

- Prime a session: `/team-kb:kb-prime` (Claude Code) or read
  `plugin/skills/kb-prime/SKILL.md`.
- Search/submit: kb-agent. Ingest/curate: kb-curator.
- E2E battery: `plugin/scripts/battery.sh` (vault `~/vault/kb-test`), driver
  skill `plugin/skills/kb-battery/SKILL.md`.
- Server tests: `cd plugin/mcp && python3 -m unittest test_teamkb_server`.

## Layout

- `vault/` — the knowledge vault (Obsidian). Tier tree per `_meta/memory-model.md`.
- `plugin/` — Claude Code plugin (agents/, skills/, mcp/, hooks/, scripts/).
- `.github/agents/` — Copilot CLI custom agents (gpt-5.6-luna, xhigh effort).
- `.github/skills/` — portable copies of the curate-* skills.
- `_meta/` — constitution, ontology, memory model (ANCHORS — read-only).
- `docs/` — research, whitepapers, continuity, test-battery evidence.
- `src/` — frozen C# reference implementation (byte-parity source of truth).
