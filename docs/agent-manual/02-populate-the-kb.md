# 02 — Populating the KB

The main job: turning a folder of markdown documents into connected, provenance-
backed, retrievable knowledge. This is the curator pipeline, end to end, with the
real outputs it produced on the 2026-08-13 run of thirteen documents.

## Before you ingest anything: order matters

Relation targets must already exist when you commit (gate C4 — there is no
auto-stub). So plan the batch in dependency order:

1. **Anchors first.** Two or three `Concept` notes the corpus keeps referring to.
   In an empty vault these have nothing to link to yet, so they carry
   `isolatedJustification: "genesis anchor"` — the one legitimate use of that
   escape hatch.
2. **Sources next.** Documents other documents cite.
3. **Derivatives last.** Papers whose `sources:` frontmatter points at documents
   from step 2, so `DerivesFrom` targets already resolve.

Anything you discover out of order is not lost — commit the note without that
relation and add it later with `add_relations` (see the back-pass at the end).

## Register your tags first

Tags are registry-before-choice: `propose_note` rejects unregistered ones. Give
each a description — it feeds the embedding used by `suggest_tags` later.

```bash
python3 plugin/scripts/kbcall.py -t register_tag -a '{
  "tag":"domain/knowledge-graphs",
  "description":"knowledge graph construction, schemas, integrity"}'
```

```
REGISTERED domain/knowledge-graphs
```

Namespaces are closed: `domain/ project/ status/ source/ machine/`. `kb/*` is
reserved for the server. Near-duplicates of existing tags are refused, so reuse
beats coining a synonym.

## The per-document pipeline

Each document runs the same eleven steps. Steps that are tool calls are shown
with their real output; steps that are your judgment are logged with `log_event`
so the run's metrics cover the whole pipeline and not just tool traffic.

### CA-1 — record the strategy

```bash
python3 plugin/scripts/kbcall.py -t log_event -a '{
  "phase":"CA-1.strategy","doc":"sub-20260813143001215",
  "metrics":{"strategy":"default","reason":"single-note artifact curation"}}'
```

Only `default` exists today (one note per document, heading-aware chunk
embeddings). Recording it now means that when other strategies land, old runs
remain interpretable.

### GA-1 — submit the document

```bash
python3 plugin/scripts/kbcall.py -t submit_document -a '{
  "path":"/Volumes/MACDEV/team-kb/docs/research/2026-08-11-self-evolving-kg-systems.md"}'
```

```json
{"submission_id": "sub-20260813143001215", "source_path": "…", "status": "staged"}
```

Submissions are content-hash deduplicated. `DUPLICATE: submission sub-… (status
committed) already covers this content` means the work is already done — do not
resubmit. A `DUPLICATE` whose status is `failed` or `curating` is resumable:
carry on with that submission id.

### CA-2/CA-3 — chunk and embed

```bash
python3 plugin/scripts/kbcall.py -t ingest_chunks -a '{"submissionId":"sub-20260813143001215"}'
```

```json
{"submission_id": "sub-20260813143001215", "chunks": 8, "dim": 768,
 "headings": ["(preamble)", "Ranked 10", …]}
```

Chunking is deterministic and server-side — heading-aware, ~512-token cap, with
overlap only *within* a section. You do not choose chunk boundaries; that keeps
runs reproducible.

This is the slow step: embedding is roughly 33 s at the median and 91 s at p95
per document, and it is ~99.9% of total pipeline wall time. If it returns
`FAILED: …`, the submission is marked `failed` — record it, move to the next
document, and rerun after the endpoint recovers. Do not retry in a loop.

### CA-4 — find neighbours

```bash
python3 plugin/scripts/kbcall.py -t semantic_search -a '{"target":"sub-20260813143001215","limit":5}'
```

On the first document of an empty vault:

```
verdict: absent — no semantic neighbors above θ=0.3 (top score 0.000). The knowledge likely does not exist yet.
```

That is correct and expected — there is nothing to be near. By the sixth
document the same call returns real neighbours at 0.88–0.93, and those are your
best candidates for relations. Cosine similarity suggests; you decide whether a
real relation exists.

### CA-5 — tag similarity

```bash
python3 plugin/scripts/kbcall.py -t suggest_tags -a '{"text":"<your overview draft>","limit":4}'
```

```
0.522  project/team-kb
0.467  domain/agent-memory
0.428  domain/knowledge-graphs
```

Suggestions only. Reuse a good existing tag rather than registering a near-miss.
Register genuinely new facets before proposing, or the TAG gate stops you.

### CA-6 — decide the metadata

This is the judgment core. Per-field discipline lives in the `curate-*` skills;
the short version:

- **Class** — one of ten. An ingested source document is almost always
  `Artifact`; pull out a `Concept` only when other notes will point at it.
- **Overview** — one to three sentences, written for a reader who will see it in
  a search result with no other context.
- **Observations** — three to eight one-line typed claims. `fact` means
  verifiable in the source as stated. `hypothesis` forces confidence below 0.7
  (gate HYP). Write them with the words someone would search for; the FTS index
  covers observation text.
- **Relations** — real connections only, forward direction only. Most common on
  ingestion: `DerivesFrom` (document → its sources), `Describes` (document →
  concept it explains), `Supersedes` (v2 → v1), `Mentions` (weakest — use when
  nothing stronger is true).
- **Provenance** — the actual origin, precise enough to re-find: a repo-relative
  path, a URL, or `session:<date>-<topic>`. Placeholders are rejected.
- **Confidence** — tracks source quality, not your enthusiasm.

Log the decision so the run explains itself:

```bash
python3 plugin/scripts/kbcall.py -t log_event -a '{
  "phase":"CA-6.metadata","doc":"sub-20260813143001215",
  "metrics":{"entity_class":"Artifact","n_tags":2,"n_relations":1,"confidence":0.9}}'
```

### CA-7 — propose, fix, commit, link

```bash
python3 plugin/scripts/kbcall.py -t propose_note -a '{ … }'
# STAGED prop-20260813143128279646 → knowledge/artifact/survey-of-self-evolving-knowledge-graph-systems. Call commit_note to finalize.

python3 plugin/scripts/kbcall.py -t commit_note -a '{"proposalId":"prop-20260813143128279646"}'
# COMMITTED knowledge/artifact/survey-of-self-evolving-knowledge-graph-systems
```

Rejected? Read the gate lines, fix the curation, propose again —
[03-gates-playbook.md](03-gates-playbook.md) has the fix for each.

Then bind the submission to the note it became, so semantic search returns
permalinks instead of submission ids:

```bash
python3 plugin/scripts/kbcall.py -t link_submission -a '{
  "submissionId":"sub-20260813143001215",
  "permalink":"knowledge/artifact/survey-of-self-evolving-knowledge-graph-systems"}'
# LINKED sub-20260813143001215 → knowledge/artifact/survey-of-self-evolving-knowledge-graph-systems
```

### CA-8 — verify the links resolve

`read_note` the committed permalink. Relations already render as real Obsidian
wikilinks — `- DERIVES_FROM :: [[knowledge/artifact/…]] {since: 2026-08-11}` —
so the graph view and backlinks pane work with no extra step. **Do not add a
second copy of the links.** Verification here means: targets resolve, backlinks
appear on the other side.

### CA-9 — reindex

```bash
python3 plugin/scripts/kbcall.py -t reindex -a '{}'
```

Counts for the report, and a check that no indexed note has lost its file.

### CA-10 — the Document Creation Form

Every ingestion records a DCF as an immutable episode:

```bash
python3 plugin/scripts/kbcall.py -t capture_episode -a '{
  "title":"DCF sub-20260813143001215",
  "body":"submission: sub-…\nsource: docs/research/…\nstrategy: default\nclass: Artifact\ntags: …\nrelations: 1\ngates: all passed at commit\ncurated_at: 2026-08-13",
  "provenanceSource":"docs/research/2026-08-11-self-evolving-kg-systems.md",
  "provenanceAuthor":"agent:curator"}'
# CAPTURED episodes/dcf-sub-20260813143001215
```

It is an `Event`, so it lands in `episodes/` — the audit trail lives in the
episodic tier and does not pollute semantic retrieval of the knowledge tier.
Episodes are append-only: the same title twice in one day is refused.

### CA-11 — report

Log it, then say it:

```bash
python3 plugin/scripts/kbcall.py -t log_event -a '{
  "phase":"CA-11.report","doc":"knowledge/artifact/survey-of-self-evolving-knowledge-graph-systems",
  "metrics":{"submission_id":"sub-…","class":"Artifact","n_relations":1,"status":"committed"}}'
```

The report itself is one compact JSON block: submission id, permalink, class,
tags, relations added, neighbours, violations encountered and fixed, chunk count,
confidence, DCF permalink, status.

## After the batch: the relation back-pass

Relations you had to skip because the target had not landed yet:

```bash
python3 plugin/scripts/kbcall.py -t add_relations -a '{
  "permalink":"knowledge/artifact/the-formal-theory-of-the-team-kb-knowledge-graph",
  "relations":[{"verb":"Describes","target":"knowledge/concept/verdict-honesty-contract","since":"2026-08-11"}]}'
# ADDED 1 relation(s) to knowledge/artifact/the-formal-theory-of-the-team-kb-knowledge-graph
```

Gated exactly like a proposal (C3 signatures, C4 existence), and it updates both
the markdown and the edge index, so the new backlink appears immediately. Without
this pass, graph density becomes an accident of ingestion order.

## What a healthy run looks like

From the 2026-08-13 run, thirteen documents, single pass:

```
docs=16 committed=16 failed=0  embed_batches=72 retries=0
gate_failures: none
  CA-2.chunk       docs=13 p50=      0.4ms
  CA-3.embed       docs=13 p50=  33153.3ms  p95=91147.6ms
  CA-4.neighbors   docs=13 p50=      0.7ms
  CA-5.tag_similarity docs=13 p50=10941.5ms
  CA-7.propose     docs=16 p50=      0.9ms  fails=0
  CA-7.commit      docs=16 p50=      2.4ms  fails=0
```

Everything except embedding is sub-millisecond. If your run looks different —
gate failures, embed retries, documents stuck in `curating` — start at
[06-troubleshooting.md](06-troubleshooting.md).

Generate that table for your own run:

```bash
python3 plugin/scripts/metrics_rollup.py -e <vault>/.teamkb-events.jsonl \
    -o metrics.jsonl --aggregate phase-stats.json --summary
```
