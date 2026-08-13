# Tool cheatsheet (teamkb MCP server)

Tool names in Claude Code: `mcp__plugin_team-kb_teamkb__<tool>`.

| Tool | In | Out |
|------|----|----|
| submit_document | {path} | {"submission_id","source_path","status"} or DUPLICATE/REJECTED |
| ingest_chunks | {submissionId} | {"chunks",N,"dim",768,…} or FAILED (endpoint down → submission failed) |
| semantic_search | {query} XOR {target: permalink\|sub-id}, limit | `verdict: ok\n<score>  <permalink>` lines, or absent with top score |
| suggest_tags | {text, limit} | ranked `score  tag` lines (suggestions only) |
| search_notes | {query, limit} | `verdict: ok\n<bm25>  <permalink>  <title>` (lower bm25 = better) or absent |
| search_by_tag | {tag, prefix?} | `verdict: ok\n<permalink>  <title>` or absent |
| read_note | {permalink} | markdown + `## Backlinks (computed)` or absent |
| propose_note | title, entityClass, overview, relations[], observations[], provenanceSource, provenanceAuthor, confidence?, tags?, isolatedJustification? | `STAGED <id> → <permalink>` or `REJECTED:\n[GATE] msg` |
| commit_note | {proposalId} | `COMMITTED <permalink>` or ERROR "Commit blocked: …" |
| link_submission | {submissionId, permalink} | `LINKED sub → permalink` |
| add_relations | {permalink, relations[]} | `ADDED n relation(s)` or `REJECTED:\n[C3/C4] …` |
| register_tag | {tag, description?} | `REGISTERED` / `REJECTED` (namespace, kb/*, near-dup) |
| capture_episode | title, body, provenanceSource, provenanceAuthor | `CAPTURED episodes/…` (append-only; same title same day rejected) |
| log_event | {phase, doc?, summary?, kind?, ok?, metrics?} | `LOGGED <phase>` — records agent-judgment phases into the run event log |
| reindex | {rebuild?} | JSON counts + missing_files + embed_pending + vault path; rebuild=true re-derives notes/edges/tags/FTS from markdown (use after cloning a vault) |

Patterns:
- relations item: `{"verb":"Mentions","target":"knowledge/concept/x","since":"2026-08-12"}`
- observations item: `{"kind":"Fact","text":"…","provenance":"url:…"}`
- Dates: since = YYYY-MM-DD. Verbs/classes/kinds are enum-validated at the schema.
