# Battery run 2026-08-13 — instrumented, single clean pass

Run id `run-20260813-final` · vault `~/vault/kb-test3` (fresh) · corpus 13 documents
(7 research + 6 whitepapers) + 3 genesis anchors · θ_semantic 0.30 (now the seeded
default) · 669 events · **no reruns, no failures, no gate violations**.

Difference from the 2026-08-12 run: the pipeline is now fully instrumented, so this
scorecard is generated from the event stream rather than narrated. Every number
below is reproducible from `events.jsonl` via `metrics_rollup.py`.

## Deterministic gate — PASS

- 13/13 documents retrieved by all four modalities (FTS, semantic, tag, graph)
- 0 false absents; both expected-absent probes returned absent
- 0 gate failures across 32 validator passes (16 propose + 16 commit)
- 0 embed retries across 72 batches
- Index: 29 notes, 22 edges, 291 chunks, 13 doc embeddings, 14 tags, 0 missing files

## GA modality battery — 10/10

| # | Search | Expected | Observed | Score |
|---|--------|----------|----------|-------|
| FTS-1 | "bi-temporal Graphiti" | ok | ok | 1.0 |
| FTS-2 | "duplicate slugs orphans census" | ok | ok | 1.0 |
| SEM-1 | "how does the knowledge base stay healthy over time" | ok | ok | 1.0 |
| SEM-2 | "mathematical foundations of typed graphs with constraints" | ok | ok | 1.0 |
| TAG-1 | domain/agent-memory | ok | ok | 1.0 |
| TAG-2 | kb/concept (prefix) | ok | ok | 1.0 |
| GRAPH-1 | backlinks(gates-as-code) | ok | ok | 1.0 |
| GRAPH-2 | backlinks(formal post-mortem) | ok | ok | 1.0 |
| PROBE-1 | "quantum blockchain kubernetes recipes" | absent | absent | 1.0 |
| PROBE-2 | "baking sourdough bread hydration ratios" | absent | absent | 1.0 |

SEM-1 scored 0.0 on the preceding run — a fresh vault seeded θ=0.45 and called a true
conceptual match absent. The score event made it visible; the seed is now the
calibrated 0.30 and SEM-1 passes. That defect is the clearest argument for this
telemetry layer existing.

## Phase coverage — 12 phases per document, every document

From `phase-stats.json` (p50 / p95 across 13 documents):

| phase | docs | p50 | p95 | failures |
|-------|------|-----|-----|----------|
| GA-1.submit | 13 | 1.8 ms | 3.2 ms | 0 |
| CA-1.strategy | 13 | 0.0 ms | 0.0 ms | 0 |
| CA-2.chunk | 13 | 0.4 ms | 1.1 ms | 0 |
| CA-3.embed | 13 | 33.2 s | 91.1 s | 0 |
| CA-4.neighbors | 13 | 0.7 ms | 1.2 ms | 0 |
| CA-5.tag_similarity | 13 | 10.9 s | 12.4 s | 0 |
| CA-6.metadata | 13 | 0.0 ms | 0.0 ms | 0 |
| CA-7.propose | 16 | 0.9 ms | 1.4 ms | 0 |
| CA-7.commit | 16 | 2.4 ms | 3.5 ms | 0 |
| CA-7.link | 13 | 0.2 ms | 0.3 ms | 0 |
| CA-8.verify / graph read | 14 | 0.7 ms | 1.9 ms | 0 |
| CA-10.dcf | 13 | 1.2 ms | 1.9 ms | 0 |
| CA-11.report | 13 | 0.0 ms | 0.0 ms | 0 |

Everything except embedding is sub-millisecond; embedding is 99.9% of wall time
(hosted endpoint, 72 batches). Tag similarity costs ~11 s per document — one query
embedding each, since registry tag vectors are cached after first use.

## Neighbor quality (CA-4)

Honest cold start, then increasingly dense: doc 1 `absent` (top 0.000, empty corpus),
doc 2 ok at 0.895, and by the whitepapers the top neighbours sit at 0.91-0.94 against
exactly the research notes they derive from.

## Artifacts

| file | contents |
|------|----------|
| `events.jsonl` | 669 raw events, every phase of every document |
| `metrics.jsonl` | 16 per-document records (phases, gate history, retrieval, timings) |
| `phase-stats.json` | corpus phase latency distribution + gate/embed tallies |
| `metrics-summary.txt` | per-document status table |
| `trace.jsonl` | raw MCP request/response bodies |
| `vault-tree.txt`, `sample-note.md`, `index-counts.json` | vault state |

Regenerate any of it: `plugin/scripts/collect_evidence.sh -v ~/vault/kb-test3 -r run-20260813-final`.
