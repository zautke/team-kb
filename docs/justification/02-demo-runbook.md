# Demo runbook — justification meeting

Five live demos, each ≤2 minutes, each a self-contained script under
`docs/justification/demos/`. Every demo has a pre-captured transcript in
`demos/transcripts/` as fallback if a live run misbehaves.

## Pre-flight (run the morning of)

```bash
cd <repo-root>
git status                                    # clean
python3 -m unittest discover -s plugin/mcp -q # 55 tests OK
ls ~/vault/.models/bge-micro-v2-onnx/         # model_quantized.onnx + tokenizer.json
~/vault/.models/onnx-venv/bin/python -c "import onnxruntime"   # deps present
```

If the ONNX model/venv is missing: `plugin/scripts/fetch_onnx_model.sh` and
`python3 -m venv ~/vault/.models/onnx-venv && …/bin/pip install onnxruntime tokenizers`.

---

## Demo 1 — zero to knowledge base (`demo1-zero-to-kb.sh`)

**Skeptical question answered:** "How much infrastructure does this thing need?"

None. Empty directory → bootstrapped vault → 16 documents chunked, embedded
(locally, ONNX, no network), gate-checked, graph-inserted, and verified across
all four retrieval modalities. Expected finale:

```
DETERMINISTIC GATE: PASS
real  0m42s        # whole driver; server-side pipeline itself is ~6 s
  ... 29 notes total
```

Talking point: the "16 documents" are the project's own research corpus — the
system is documented in itself.

## Demo 2 — gates are code (`demo2-gates.sh`)

**Skeptical question answered:** "What stops this from rotting like every wiki?"

Live rejections with exact, actionable messages: C2 duplicate permalink, I4
near-duplicate title (trigram), PROV placeholder provenance, TAG unregistered
tag, C1 illegal entity class (closed enum, re-checked server-side for any
caller). Then the corrected propose→commit succeeds. Expected excerpts:

```
[C2] Permalink 'knowledge/concept/gates-as-code' already exists. Merge or supersede — never suffix.
[I4] Title too similar to existing 'Gates as Code' (...). Merge, supersede, or assert distinct_from.
[PROV] Placeholder provenance source 'TBD' rejected.
[TAG] Tag 'domain/not-registered' is not in the registry (...). Register it in the same commit.
[C1] Unknown entity class 'BlogPost'. Closed set: Person, Org, ...
COMMITTED knowledge/concept/tag-demo-note
```

## Demo 3 — retrieval + honesty (`demo3-retrieval.sh`)

**Skeptical question answered:** "Is retrieval real, and does it hallucinate?"

Four independent modalities against the live repo vault (FTS/BM25, semantic,
tag, graph backlinks with inverse verbs), then two junk queries returning
`verdict: absent` with the top score shown. Requires network for the semantic
query vector (repo vault is in the hosted-model vector space); if offline,
skip step 2 and reference demo 1, whose semantic channel is fully local.

## Demo 4 — the index is disposable (`demo4-rederive.sh`)

**Skeptical question answered:** "What do we actually own / what if the DB corrupts?"

rsync the markdown only (no database), `reindex(rebuild=true)` — 29 notes,
22 edges rebuilt in ~22 ms — then the same query on original and clone with
**identical BM25 scores**. Markdown is canonical; everything else is derived.

## Demo 5 — self-reporting (`demo5-observability.sh`)

**Skeptical question answered:** "How do you know any of this without babysitting it?"

`kb_report` prints corpus health (counts, class distribution, index parity,
orphans, θ, model) plus per-phase p50/p95 from the committed battery event
stream. Then the HTML dashboard is regenerated live from that telemetry —
proving the leave-behind artifact is derived, not hand-authored.

---

## Suggested order & timing (~12 min demos + walkthrough discussion)

1. Demo 1 (the opener — whole lifecycle, one command)
2. Demo 2 (the differentiator — why this isn't a wiki)
3. Demo 3 (retrieval quality + honesty contract)
4. Demo 4 (risk: durability/ownership)
5. Demo 5 (risk: operability) → hand over dashboard + walkthrough doc
