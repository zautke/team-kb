# 04 — Retrieval playbook

Four modalities. Each answers a different shape of question, and each can say
`absent`. Picking the wrong one produces a false negative that looks exactly like
missing knowledge.

## Which modality for which question

| The question is… | Use | Because |
|------------------|-----|---------|
| "Where is the note that says *X*?" (you know the wording) | `search_notes` | FTS/BM25 over title, overview, observations — exact terms, porter-stemmed |
| "What do we know *about* this idea?" (you know the meaning, not the words) | `semantic_search` | cosine over document embeddings; survives paraphrase |
| "What is filed under this facet?" | `search_by_tag` | exact tag, or prefix (`kb/concept` for a whole class) |
| "What connects to this note?" | `read_note` | markdown plus computed backlinks with inverse verb names |

Run more than one when the answer matters. They fail differently: FTS misses
paraphrase, semantic misses rare proper nouns, tags miss anything the curator did
not file that way, graph only sees what someone linked.

## FTS — `search_notes`

```bash
python3 plugin/scripts/kbcall.py -t search_notes -a '{"query":"duplicate slugs orphans census","limit":3}'
```

```
verdict: ok
-10.05  knowledge/artifact/master-kb-formal-post-mortem-model  master-kb Formal Post-Mortem Model
```

BM25: **lower is better**, negatives normal. Query text is tokenised and quoted
for you, so hyphens, colons and dots are safe to include. Stemming means
"curating" finds "curation" — but "bitemporal" will *not* find "bi-temporal",
because the hyphen splits the source into two tokens. When a term might be
written either way, try both or fall back to semantic.

## Semantic — `semantic_search`

```bash
python3 plugin/scripts/kbcall.py -t semantic_search -a '{"query":"how does the knowledge base stay healthy over time","limit":3}'
```

```
verdict: ok
0.319  knowledge/artifact/the-stratified-memory-organism-whitepaper
0.310  knowledge/artifact/survey-of-agentic-self-learning-loops
0.301  knowledge/artifact/curation-tactics-whitepaper
```

Cosine similarity: **higher is better**, 0 to 1. Two modes:

- `{"query": "<text>"}` — search by meaning.
- `{"target": "<permalink or submission id>"}` — neighbours of an existing
  document. This is what the curator uses at CA-4.

**The threshold is real and it is honest.** Below θ (0.30 by default, stored per
vault in the database's `meta` table) the tool returns `absent` *and reports the
top score it saw*:

```
verdict: absent — no semantic neighbors above θ=0.3 (top score 0.163). The knowledge likely does not exist yet.
```

That top score is diagnostic. 0.16 means genuinely unrelated. 0.28 means
something is close but under the line — worth reading the note manually, and
worth asking whether θ is calibrated for this corpus. Note that θ mattering this
much is not theoretical: a vault seeded at 0.45 silently returned `absent` for a
true conceptual match until the threshold was corrected to the calibrated 0.30.

Note also that semantic search covers documents that were *ingested through the
pipeline* (they have embeddings). A note written directly with `propose_note`
has no document vector, so it is findable by FTS, tag and graph but not by
semantic search.

## Tag — `search_by_tag`

```bash
python3 plugin/scripts/kbcall.py -t search_by_tag -a '{"tag":"domain/agent-memory"}'
python3 plugin/scripts/kbcall.py -t search_by_tag -a '{"tag":"kb/concept","prefix":true}'
```

```
verdict: ok
knowledge/concept/gates-as-code  Gates as Code
knowledge/concept/stratified-memory-organism  Stratified Memory Organism
knowledge/concept/verdict-honesty-contract  Verdict Honesty Contract
```

Prefix mode is how you enumerate a class (`kb/concept`, `kb/artifact`) or a
status (`kb/status/`). The `kb/*` plane is written by the server for every note,
so it is always complete — unlike topical tags, which are only as complete as
curation.

## Graph — `read_note`

```bash
python3 plugin/scripts/kbcall.py -t read_note -a '{"permalink":"knowledge/concept/gates-as-code"}'
```

Returns the full markdown, then:

```
## Backlinks (computed)
- MENTIONED_BY ← [[knowledge/artifact/master-kb-empirical-failure-audit]] (stored as MENTIONS)
- DESCRIBED_BY ← [[knowledge/artifact/curation-tactics-whitepaper]] (stored as DESCRIBES)
```

`stored as` shows the direction someone actually authored; the arrow shows the
inverse computed for you. Following backlinks from a hub concept is usually the
fastest way to find everything on a topic once you have one good note.

## The verdict contract

`verdict: absent` means **the knowledge does not exist**. The required response
is to report the gap and stop.

What not to do: rephrase and retry until something comes back. Every retry
lowers the bar until you find a weak match and present it as an answer. The
system tells you the truth precisely so you do not have to guess, and a run that
never returns `absent` is not a thorough run — it is one that has stopped being
able to say "we don't know".

Legitimate follow-ups after an `absent`:

- try a **different modality** once (FTS missed a paraphrase; semantic will not)
- check the **top score** on a semantic absent — near-θ means look manually
- confirm you are pointed at the **right vault** (`reindex` reports its path)
- then report the gap, and if the knowledge should exist, ingest the source

## Scoring what you got back

When you are evaluating retrieval quality rather than just using it, score each
result 0–1 against the query intent, and log it so it is evidence rather than
prose:

```bash
python3 plugin/scripts/kbcall.py -t log_event -a '{
  "phase":"GA-4.score","doc":"knowledge/artifact/…","kind":"ga.score",
  "metrics":{"modality":"semantic","query":"…","expected":"ok","observed":"ok",
             "score":1.0,"justification":"top hit is the whitepaper the query paraphrases"}}'
```

Weigh the metadata the tools hand you: verdict, rank or score, the note's own
`confidence`, whether tags match the facet you asked about, and whether
provenance points at a source you trust. A high-ranking note with confidence 0.5
and a `hypothesis` observation is a lead, not an answer.
