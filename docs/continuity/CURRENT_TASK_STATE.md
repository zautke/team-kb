# CURRENT TASK STATE — team-kb

**As of:** 2026-08-13 · **Repo:** <repo-root> (origin: github:/zautke/team-kb) · **Phase:** M0.6 — operational, populated, documented

## State

**The KB is live and in use.** Repo `vault/` holds real content (81db1c6): 13 curated
documents (7 research + 6 whitepapers) + 3 genesis anchors + DCF episodes — 29 notes,
22 edges, 291 chunks, 13 doc embeddings. All four retrieval modalities verified in place.

- **Server**: `plugin/mcp/teamkb_server.py`, 15 tools, 8 gates, zero dependencies. Tests 45/45.
- **Registered** at project scope (895eba8): `.mcp.json` with `${CLAUDE_PROJECT_DIR:-.}` paths
  and env overrides; `claude mcp list` → `teamkb: ✔ Connected`. Approval recorded in
  `~/.claude.json` (backup `~/.claude.json.bak-*`).
  **Not yet live in a session started before registration — restart to get `mcp__teamkb__*` tools.**
- **Index is re-derivable** (6a021dd): `parse_markdown` inverts the serializer, `reindex(rebuild=true)`
  rebuilds notes/edges/tags/FTS from markdown alone. Proven on a markdown-only clone: 29 notes,
  22 edges, 6.5ms, identical BM25 scores.
- **Telemetry always on**: per-phase events → `<vault>/.teamkb-events.jsonl`; rollup + aggregate
  via `metrics_rollup.py`; packaging via `collect_evidence.sh`.
- **Manual**: `docs/agent-manual/` — 00 zero-to-running, 01 quickstart, 02 populate, 03 gates,
  04 retrieval, 05 tools, 06 troubleshooting, 07 MCP config. Every example run live before writing.
- C# stack still frozen reference in `src/`.

## Resume point

Nothing in flight. Highest-value next items (see TASKS):

1. **Restart a session** to exercise the registered server through native MCP tools rather than `kbcall.py`.
2. **Semantic coverage on clone** — open question below; needs a decision before the team relies on it.
3. M1 retrieval work (RRF fusion) once the corpus is larger.

## Open question for the user (raised 2026-08-13, undecided)

Document embeddings derive from *source corpus files*, not from vault notes. A cloned vault
therefore rebuilds FTS/tags/graph perfectly but has an **empty semantic channel** until documents
are re-ingested. Two fixes, user's call: (a) commit the embeddings, or (b) make `rebuild` re-embed
from note text. Neither is implemented.

## Key constraints

- Embeddings hosted only (`TEAMKB_EMBED_URL`); no local model weights on this machine.
  Default still points at the personal tunnel — **the one non-portable value for the other team.**
- GA never holds propose/commit; CA never holds fs-write. Write path is gates-only.
- θ semantic = 0.30 seeded (calibrated); per-vault override in db `meta`.
