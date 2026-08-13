# 05 — Tool reference

Fifteen tools, exposed by one stdio MCP server named `teamkb`. Server wiring,
JSON config for each host, and the environment variables are in
[07-mcp-server-config.md](07-mcp-server-config.md).

In Claude Code they appear as
`mcp__plugin_team-kb_teamkb__<tool>`; in Copilot as `teamkb/<tool>`; from a shell
as `python3 plugin/scripts/kbcall.py -t <tool> -a '<json>'`.

Class, verb and observation-kind arguments are **enums in the tool schema** — an
off-vocabulary value cannot be sent, which is how the constitution's closed
vocabularies are enforced rather than merely stated.

## Write path (curator only)

### `propose_note`
Stage a note; runs all eight gates. Path is never an argument — it is computed
from `entityClass`.

| arg | type | notes |
|-----|------|-------|
| `title` | string | permalink = normalised title |
| `entityClass` | enum | Person, Org, Project, Codebase, Technology, Artifact, Concept, Event, Decision, Agent |
| `overview` | string | 1–3 sentences |
| `relations` | array | `{verb, target, since, mode?}`; verb is an enum, `since` is `YYYY-MM-DD` |
| `observations` | array | `{kind, text, provenance?}`; kind is an enum |
| `provenanceSource` | string | real origin; TBD/TODO/unknown rejected |
| `provenanceAuthor` | string | e.g. `agent:curator`, `user` |
| `confidence` | number | default 1.0; must be < 0.7 if any hypothesis observation |
| `tags` | array | must be registered first |
| `isolatedJustification` | string | required if `relations` is empty |

→ `STAGED prop-… → <permalink>. Call commit_note to finalize.`
or `REJECTED:\n[GATE] message` (one line per violation).

### `commit_note`
`{proposalId}` → re-validates every gate against current state, writes the
markdown, indexes FTS, edges and tags.
→ `COMMITTED <permalink>` · on conflict: `ERROR: Commit blocked: C2: …`

### `add_relations`
`{permalink, relations[]}` → gated (C3, C4) append to an existing note; updates
markdown *and* edge index. The back-pass tool.
→ `ADDED n relation(s) to <permalink>` · `REJECTED:\n[C3|C4] …`

### `register_tag`
`{tag, description?}` → registers a namespaced tag and appends its registry row.
→ `REGISTERED <tag>` · `REJECTED: namespace 'x/' is not in the closed namespace set.`
· `REJECTED: namespace 'kb/' is server-computed and reserved.`
· `REJECTED: too similar to registered tag '<tag>'. Reuse it or pick a distinct name.`

### `capture_episode`
`{title, body, provenanceSource, provenanceAuthor}` → append-only `Event` note in
`episodes/`, bypassing staging. Used for DCFs, session snapshots, batch reports.
→ `CAPTURED episodes/<date>-<slug>`
· `ERROR: Episodes are append-only; identical title today already captured.`

## Ingestion

### `submit_document`
`{path}` → registers a source document. Content-hash deduplicated; path must be
inside the approved corpus roots if `TEAMKB_CORPUS_ROOTS` is set.
→ `{"submission_id","source_path","status"}`
· `DUPLICATE: submission sub-… (status committed) already covers this content.`
· `REJECTED: … does not exist or is out of scope.`

### `ingest_chunks`
`{submissionId}` → deterministic heading-aware chunking plus embedding of every
chunk and a mean-pooled document vector. The slow step.
→ `{"submission_id","chunks","dim","headings"}`
· `FAILED: embedding endpoint failed after 3 attempts: … — submission marked failed; rerun after endpoint recovery.`

### `link_submission`
`{submissionId, permalink}` → binds the document vector to the committed note, so
semantic search returns permalinks.
→ `LINKED sub-… → <permalink>`

## Retrieval

### `search_notes`
`{query, limit?}` → FTS5/BM25 over title, overview, observations. Lower score is
better. Query tokens are quoted for you.
→ `verdict: ok\n<bm25>  <permalink>  <title>` · `verdict: absent — no notes match. …`

### `semantic_search`
`{query}` **or** `{target}`, plus `limit?` → cosine over document embeddings.
Higher is better. `target` (permalink or submission id) gives neighbours.
Honest absent below θ, with the top score reported.
→ `verdict: ok\n<score>  <permalink>` · `verdict: absent — no semantic neighbors above θ=0.3 (top score 0.163). …`

### `search_by_tag`
`{tag, prefix?}` → exact tag, or prefix match (`kb/concept` enumerates a class).
→ `verdict: ok\n<permalink>  <title>` · `verdict: absent — no notes tagged '<tag>'.`

### `read_note`
`{permalink}` → full markdown plus `## Backlinks (computed)` with inverse verbs.
→ markdown · `verdict: absent — no note '<permalink>'.`

### `suggest_tags`
`{text, limit?}` → registered tags ranked by embedding similarity. Suggestions
only; registration still goes through `register_tag`.
→ `<score>  <tag>` lines

## Operations

### `reindex`
`{rebuild?}` → consistency report: counts, missing files, pending embeddings,
vault path. With `rebuild: true`, re-derives notes, edges, tags and FTS from the
vault's markdown alone — for a freshly cloned vault, not routine curation.
→ `{"vault","notes","edges","chunks","doc_embeddings","tags","missing_files","embed_pending"}`
plus `"rebuilt": {"files_parsed","parse_failures","duration_ms"}` when rebuilding.

### `log_event`
`{phase, doc?, summary?, kind?, ok?, metrics?}` → records a runbook phase that is
your judgment rather than a tool call (CA-1 strategy, CA-6 metadata, CA-11
report, GA-4 scoring), so the run's metrics cover the whole pipeline.
→ `LOGGED <phase> (<doc>)`

## Who holds what

| | GA (kb-agent) | CA (kb-curator) |
|---|---|---|
| submit_document | ✓ | |
| search_notes, semantic_search, search_by_tag, read_note | ✓ | ✓ |
| ingest_chunks, suggest_tags | | ✓ |
| propose_note, commit_note, add_relations, register_tag, link_submission | | ✓ |
| capture_episode, reindex, log_event | ✓ | ✓ |

The GA has no write path, by tool shape rather than by instruction. Neither role
has filesystem write access to the vault. This is deliberate: a loop is
constrained by the tools it holds, not by what its prompt asks of it.
