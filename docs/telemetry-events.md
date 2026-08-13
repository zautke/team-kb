# Telemetry — event stream and per-document metrics

Every run of the teamkb MCP server appends structured events to
`$TEAMKB_VAULT/.teamkb-events.jsonl` (override with `TEAMKB_EVENTS`). Always on;
one JSON object per line; append-only; flushed per event so a crashed run keeps
everything up to the crash.

## Envelope (every line)

| field | meaning |
|-------|---------|
| `ts` | ISO-8601 UTC timestamp |
| `run_id` | `TEAMKB_RUN_ID` if set, else `run-<YYYYMMDD-HHMMSS>` at server start |
| `seq` | monotonic per server process |
| `kind` | event type (below) |
| `phase` | runbook step id (below) |
| `doc` | correlation key: submission id (`sub-…`), permalink, or source filename |
| `ok` | false on gate failure, embed failure, tool error, or REJECTED/FAILED result |
| `duration_ms` | wall time, when the event measures something |

Phase-specific metrics are merged in at the top level (no nesting to unwrap).

## Event kinds

| kind | emitted when | key metrics |
|------|--------------|-------------|
| `run.start` / `run.end` | server process boundaries | vault, embed_url, embed_model, semantic_theta, pid, events |
| `tool.start` | before a tools/call executes | tool, arguments |
| `tool.end` | after it returns | tool, duration_ms, plus extracted metrics: verdict, n_hits, top_score, scores, hits, accepted, violations, n_violations, permalink, proposal_id, n_backlinks, n_relations_added, duplicate, and any JSON fields the tool returned (chunks, notes, edges, …) |
| `gate.eval` | every validator pass (propose and commit) | gates_evaluated, gates_passed, gates_failed, n_violations, violations[{gate,message}], entity_class, confidence, n_relations, n_observations, n_tags |
| `chunk.done` | after deterministic chunking | n_chunks, doc_chars, chunk_chars_min/max/mean, cap, overlap, headings, source_path |
| `embed.batch` | each HTTP batch, including failed attempts | batch, size, attempt, chars, error |
| `embed.done` | after all batches for one call | n_texts, n_batches, dim, chars, model, prefix |
| `submission.failed` | embedding gave up; submission marked failed | error, n_chunks |
| `agent.step` (or custom via `kind`) | agent judgment phases via the `log_event` tool | summary + arbitrary caller metrics |

## Phase ids

Ingestion: `GA-1.submit` · `CA-1.strategy` · `CA-2.chunk` · `CA-3.embed` ·
`CA-4.neighbors` · `CA-5.tag_similarity` (+`.embed_query`, `.embed_registry`) ·
`CA-5.register_tag` · `CA-6.metadata` · `CA-7.propose` · `CA-7.commit` ·
`CA-7.link` · `CA-7.backpass` · `CA-8.verify` · `CA-9.reindex` · `CA-10.dcf` ·
`CA-11.report`.

Retrieval: `GA-3.retrieve.fts` · `GA-3.retrieve.semantic` (+`.embed_query`) ·
`GA-3.retrieve.tag` · `GA-3.retrieve.graph` · `GA-4.score`.

Steps that are agent judgment rather than tool calls (CA-1, CA-6, CA-11, GA-4)
are logged by the agents themselves with the `log_event` tool — the agent
definitions require it, so the stream covers the whole runbook, not just the
tool calls.

## Per-document rollup

```bash
python3 plugin/scripts/metrics_rollup.py \
    -e ~/vault/kb-test/.teamkb-events.jsonl \
    -o metrics.jsonl --summary            # optionally -r <run_id>
```

One line per document, aliasing each submission id to the permalink it became
(via `link_submission`), so pre-commit and post-commit phases roll into one
record:

```json
{"doc": "knowledge/artifact/…", "run_id": "…", "submission_ids": ["sub-…"],
 "source_path": "…", "permalink": "…", "entity_class": "Artifact",
 "phases": {"CA-2.chunk": {"calls": 1, "ms": 3.1, "ok": true,
                           "metrics": {"n_chunks": 8, "doc_chars": 15234}}, …},
 "phases_completed": ["GA-1.submit", "CA-1.strategy", …],
 "gate_history": [{"stage": "CA-7.propose", "passed": [...], "failed": [], …}],
 "n_gate_failures": 0, "retrieval": {"fts": [...], "semantic": [...]},
 "errors": [], "total_ms": 41234.5, "events": 37, "status": "committed"}
```

`--summary` prints a per-document status/phase/gate/timing table to stderr.
`-a/--aggregate <file>` additionally writes corpus-level phase statistics —
per-phase p50/p95/max/total latency, per-phase failure counts, gate-failure
tallies, and embed batch/retry counts:

```json
{"documents": 13, "committed": 13, "failed": 0,
 "phases": {"CA-3.embed": {"docs": 13, "p50_ms": 31652.8, "p95_ms": 93708.6,
                           "max_ms": 93708.6, "total_ms": 512340.1, "failures": 0}, …},
 "gate_failures": {}, "embed_batches": 58, "embed_retries": 0, "embed_p95_ms": 18494.8}
```

## Packaging a run

```bash
plugin/scripts/collect_evidence.sh -v ~/vault/kb-test -r <run-id>
# → docs/test-battery/run-<date>/{events,metrics,trace}.jsonl,
#   metrics-summary.txt, vault-tree.txt, sample-note.md, index-counts.json
```

## Raw trace (optional)

`TEAMKB_TRACE=1` additionally writes `.teamkb-trace.jsonl` — full request and
response bodies per tools/call. Use it when you need exact payloads; use the
event stream for metrics.
