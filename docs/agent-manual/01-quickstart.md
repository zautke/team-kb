# 01 — Quickstart

Five minutes from cold start to your first correct query and first note.
**If the KB does not exist yet**, start at
[00-zero-to-running.md](00-zero-to-running.md) instead — this page assumes a
vault that is already bootstrapped and holding notes.

## 0. Know which vault you are pointed at

The server takes its vault from `TEAMKB_VAULT` and has no fallback. Confirm it
before anything else — every other symptom in this manual is downstream of being
in the wrong vault.

```bash
TEAMKB_VAULT=~/vault/kb-test python3 plugin/scripts/kbcall.py -t reindex -a '{}'
```

```json
{"vault": "/Users/derp/vault/kb-test", "notes": 29, "edges": 22, "chunks": 291,
 "doc_embeddings": 13, "tags": 14, "missing_files": [], "embed_pending": []}
```

`missing_files: []` means every indexed note still exists on disk.
`embed_pending: []` means no document is stuck waiting on the embedding endpoint.

In a Claude Code session the plugin starts this server for you and the tools
appear as `mcp__plugin_team-kb_teamkb__<tool>`; the `kbcall.py` form above is the
same server driven from a shell, which is what the examples in this manual use so
you can copy them verbatim.

## 1. Prime yourself

Run `/team-kb:kb-prime` (or read `plugin/skills/kb-prime/SKILL.md`). It loads the
constitution digest, the closed vocabulary, the verdict contract and the write
ritual. Do this before touching the KB in a new session — it is short, and it is
the difference between working with the gates and fighting them.

## 2. Ask the KB something

```bash
python3 plugin/scripts/kbcall.py -t search_notes -a '{"query":"bi-temporal Graphiti","limit":2}'
```

```
verdict: ok
-6.14  knowledge/artifact/survey-of-self-evolving-knowledge-graph-systems  Survey of Self-Evolving Knowledge Graph Systems
```

The number is BM25: **lower is better**, and negative values are normal.

## 3. Ask it something it does not know

```bash
python3 plugin/scripts/kbcall.py -t search_notes -a '{"query":"quantum blockchain kubernetes recipes"}'
```

```
verdict: absent — no notes match. The knowledge likely does not exist yet.
```

**This is a complete answer.** Report the gap. Do not rephrase and retry until
something matches — that manufactures a false positive out of an honest negative.

## 4. Read a note and see its computed backlinks

```bash
python3 plugin/scripts/kbcall.py -t read_note -a '{"permalink":"knowledge/concept/gates-as-code"}'
```

The markdown comes back, followed by:

```
## Backlinks (computed)
- MENTIONED_BY ← [[knowledge/artifact/master-kb-empirical-failure-audit]] (stored as MENTIONS)
- DESCRIBED_BY ← [[knowledge/artifact/curation-tactics-whitepaper]] (stored as DESCRIBES)
```

Nobody wrote those backlinks. The audit note declares `MENTIONS`, and the inverse
is derived on read. This is why you only ever author one direction.

## 5. Write your first note

Two steps, always. Propose runs the gates:

```bash
python3 plugin/scripts/kbcall.py -t propose_note -a '{
  "title": "Reciprocal Rank Fusion",
  "entityClass": "Concept",
  "overview": "Rank-based fusion that merges result lists from several retrieval channels by summing 1/(k+rank), conventionally with k=60.",
  "relations": [{"verb":"Mentions","target":"knowledge/concept/verdict-honesty-contract","since":"2026-08-13"}],
  "observations": [{"kind":"Fact","text":"RRF needs no score normalisation across channels because it consumes ranks, not scores."}],
  "provenanceSource": "docs/whitepapers/02-memory-model.md",
  "provenanceAuthor": "agent:curator",
  "confidence": 0.9,
  "tags": ["domain/retrieval"]
}'
```

If the curation is sound you get a proposal id:

```
STAGED prop-20260813144654999397 → knowledge/concept/reciprocal-rank-fusion. Call commit_note to finalize.
```

If it is not, you get the gates that stopped it — see
[03-gates-playbook.md](03-gates-playbook.md). (The example above will in fact be
rejected on a fresh vault, because `domain/retrieval` is not registered yet.
That is the intended first lesson: tags are registry-before-choice.)

Commit re-runs every gate against current state, then writes the file:

```bash
python3 plugin/scripts/kbcall.py -t commit_note -a '{"proposalId":"prop-20260813144654999397"}'
```

```
COMMITTED knowledge/concept/reciprocal-rank-fusion
```

**A staged proposal is not a note.** If you stop after `STAGED`, nothing was
written. Commit, or the work is lost.

## What to read next

Putting real documents in is a longer pipeline than a single note —
[02-populate-the-kb.md](02-populate-the-kb.md) walks it end to end.
