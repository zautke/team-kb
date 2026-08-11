---
title: "R4 — jcodemunch functional spec (agent: explore-jcodemunch)"
type: research
status: active
created: 2026-08-11
provenance:
  - source: "session:2026-08-11-teamkb-rebuild-research"
    author: "agent:claude-fable-5"
tags: [research, rebuild, dossier-2026-08]
---

# jcodemunch — functional spec (read-only recon, verified from source)

## Identity
`~/.local/bin/jcodemunch-mcp` → uv-tool shim → Python pkg `jcodemunch_mcp` **v1.108.155** at `~/.local/share/uv/tools/jcodemunch-mcp/lib/python3.14/site-packages/`. Siblings: `jdocmunch-mcp`, `gcm`, `munch-bench`. Source repo on disk: `/Volumes/MACDEV/jgravelle#jcodemunch-mcp` (older than installed; ARCHITECTURE.md/SPEC.md still accurate). Live MCP surface = `mcp__codemunch-adagio__*`, ~95 tools.

## Capability groups
**Indexing/lifecycle** — index_repo, index_folder, index_file, index_dependency, resolve_repo, list_repos, list_workspaces, invalidate_cache, register_edit, get_watch_status, embed_repo, import_scip, import_runtime_signal.
**Search** — search_symbols (kind/language/file_pattern/decorator filters), search_text (regex + context_lines), search_ast, search_columns (dbt/SQLMesh), find_similar_symbols, find_implementations, suggest_queries, suggest_corrections, winnow_symbols.
**Reading** — get_file_outline, get_symbol_source (exact byte-offset span + drift verify), get_context_bundle, get_ranked_context, get_file_content, get_repo_outline, get_file_tree, get_repo_map, summarize_repo, digest.
**Relationships** — find_references, check_references, find_importers, get_dependency_graph, get_dependency_cycles, get_call_hierarchy, get_class_hierarchy, get_blast_radius, get_impact_preview, get_related_symbols, check_edit_safe / check_rename_safe / check_delete_safe, get_endpoint_impact, get_signal_chains, get_cross_repo_map.
**Analytics** — get_hotspots, get_churn_rate, get_symbol_complexity, get_repo_health, health_radar, get_file_risk, get_coupling_metrics, get_architecture_metrics, get_layer_violations, find_dead_code / get_dead_code_v2, find_unused_paths, get_untested_symbols, get_decorator_census, get_extraction_candidates, plan_refactoring, get_pr_risk_profile, get_delivery_metrics, get_parity_map, get_tectonic_map, observatory, render_diagram (mermaid).
**Session** — plan_turn, announce_model / set_tool_tier, get_session_context, get_session_stats, get_session_snapshot, session_journal, turn_budget, assemble_task_context, decision_context, get_symbol_provenance, audit_agent_config, tune_weights, get_redaction_log.

## Verified internals
- **Parser**: tree-sitter. `parser/languages.py` = 2226 lines ext→lang map with disambiguation heuristics (`.m` MATLAB/ObjC, Ansible paths, OpenAPI basenames). Plus complexity.py, fqn.py, parse_cache.py, sql_preprocessor.py, hierarchy.py, imports.py.
- **Storage**: SQLite **WAL**, one `{repo_slug}.db` per repo under `~/.code-index/` (`CODE_INDEX_PATH` override). Tables: meta, symbols, files, imports, raw_cache, content_blob + branch_deltas/branch_meta, runtime_* (calls/edges/imports/columns/stack_events/redaction_log), scip_*. Sidecars: `.meta` (list without opening DB), `.checksum` SHA-256, `{slug}/` cached raw sources. Legacy `.json` indexes auto-migrate. LRU index cache w/ mtime invalidation, process locks, WAL checkpoint on shutdown. Symbols store byte offsets → exact retrieval by seek, no reparse.
- **Ranking**: BM25 over symbol fields + identity signals (exact / substring / word-overlap / signature / summary / docstring) + PageRank centrality bonus (log-scaled) as tiebreaker; bounded-heap top-k. `retrieval/signal_fusion.py` = **RRF**: `score(s) = Σ weight[c] / (k + rank(c,s))` across identity / similarity(semantic) / lexical channels; weights overridable, `tune_weights` persists.
- **Embeddings**: optional, float32 BLOBs in `symbol_embeddings` table inside the same .db (stdlib `array`, no numpy). Local ONNX all-MiniLM-L6-v2, 384-dim, ~23 MB, lazy download. ⚠️ that download breaks the largo no-local-models rule — mirror the *interface*, not the local encoder.
- **Honesty contract** (`retrieval/verdict.py`): states `ok` / `low_confidence` / `absent` / `degraded`, with scanned counts, coverage disclosure attached on absent/degraded, `did_you_mean`, versioned heuristic pin. Legacy `negative_evidence` emitted additively.
- **Session routing**: `plan_turn` scores symbols → confidence `high|medium|low`, escalates to `none` when index says the feature doesn't exist; `max_supplementary_reads = {high:2, medium:5, low:10}`; returns recommended_symbols/files, `session_overlap` from journal, insertion-point suggestion when low/none, budget advisor at >60% used.
- **Budget** (`tools/turn_budget.py`): turn boundary inferred from inter-call gap; `record_output()` emits `budget_warning` at >80% and on exhaustion; `should_compact()` drives auto-compaction.
- **Journal** (`tools/session_journal.py`): in-memory, thread-safe, per-dict cap 5000, LRU-by-last_ts eviction; tracks reads, queries (+result counts), edits, tool-call counts, negative-evidence log.
- **Model tiering** (`tier_resolver.py`): normalizes model id (strip provider prefix, `[1m]` bracket, `-YYYYMMDD`), matches exact → glob → longest substring → `*` → `full` fallback; narrows exposed tool list.
- **Hooks** (`cli/hooks.py`): PreToolUse steers off native Grep/Read; PostToolUse auto-reindexes after Edit/Write (plus a Copilot-CLI payload adapter); PreCompact writes a session snapshot; WorktreeCreate/Remove append to `~/.claude/jcodemunch-worktrees.jsonl` (present on this machine) driving `watch-claude` incremental reindex via `watchfiles`.
- **Other**: SCIP ingestion (`evidence/scip*.py`), runtime signal ingest + OTel + redaction (`runtime/`), org rollup store + license (`org/`), retrieval extras (confidence, freshness, entropy_prune, embed_drift, provenance, query_shape, regret).

## Top 10 to mirror in a knowledge-vault curator agent
1. **plan_turn analogue** — confidence (high/medium/low/none) + hard read budget before touching any note; `none` = report the gap, stop searching.
2. **Unified verdict contract** — ok / low_confidence / absent / degraded, with scan counts + coverage + did_you_mean. Kills re-query loops.
3. **Outline-first reading** — frontmatter + heading tree before body; body only by anchor.
4. **Exact-span retrieval + drift verification** — byte offsets into cached content; detect stale index vs edited note.
5. **Context bundle** — note + links/backlinks/related as one bounded, deduped payload instead of N reads.
6. **RRF signal fusion** — identity + lexical(BM25) + semantic channels with tunable weights; centrality (PageRank on link graph) as tiebreaker.
7. **Impact/safety checks** — backlinks, blast radius, check_rename_safe/check_delete_safe before moving or deleting a note.
8. **SQLite WAL single-file index + meta/checksum sidecars + incremental mtime→hash reindex** — cheap listing, safe concurrency with a watcher.
9. **Session journal + turn budget** — track reads/queries/edits, warn at 80%, auto-compact; feeds session_overlap dedupe.
10. **Edit hooks** — PostToolUse auto-reindex on write (`register_edit`) + PreCompact snapshot so context survives compaction.

Bonus mapping: hotspots/churn → stale & over-edited notes; find_dead_code / find_unused_paths → orphan notes; get_dependency_cycles → circular link loops; render_diagram → vault graph views.

Note: one Bash call failed mid-recon with `ENOSPC ... /private/tmp/claude-503/...` — tmp pressure on largo, retried smaller and completed. No indexing commands were run; all findings read from source.
