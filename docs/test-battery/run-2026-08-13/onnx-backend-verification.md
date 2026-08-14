# Local ONNX embedding backend — verification (2026-08-13)

Backend: `TEAMKB_EMBED_BACKEND=onnx`, model `TaylorAI/bge-micro-v2` int8
(`model_quantized.onnx` 17 MB + `tokenizer.json`, fetched by
`plugin/scripts/fetch_onnx_model.sh`), runtime onnxruntime 1.28.0 +
tokenizers 0.23.1 (CPU, macOS arm64, Python 3.13).

## Unit suite

`python3 -m unittest` — **53/53 OK** (2 skips without onnxruntime installed;
0 skips inside the venv that has it). New coverage: backend dispatch,
missing-deps/missing-dir clean errors, vector-space guard on all three
semantic tools, mask-weighted mean-pool + L2 math vs a hand-computed fixture.

## Live smoke (real model)

```
dim 384  norm 1.0  3 texts in 82.7 ms
sim("The cat sat on the mat.", "A feline rested on the rug.")      = 0.701
sim("The cat sat on the mat.", "Quarterly revenue grew 12 percent.") = 0.404
```

## End-to-end (fresh scratch vault)

submit `docs/whitepapers/02-memory-model.md` → `ingest_chunks`: 38 chunks,
dim 384, embedded in **767 ms total (~20 ms/chunk)** → meta stamped
`embed_dim=384`, `embed_model=bge-micro-v2-onnx`.

## θ calibration (bge-micro-v2)

| queries | top scores |
|---|---|
| 4 true-match ("memory decay and consolidation", "stratified memory tiers", …) | 0.704 – 0.783 |
| 5 junk ("french pastry recipes", "nba playoff schedule", …) | 0.638 – 0.680 |

True floor 0.704 vs junk ceiling 0.680 — **θ seeded 0.69** (server seeds per
model family; nomic stays 0.30). Margin is narrow: that is bge-micro's quality
ceiling, the price of its speed. Verified after calibration:

```
match  → verdict: ok      0.783
junk   → verdict: absent  — no semantic neighbors above θ=0.69 (top score 0.646)
```

## Vector-space guard

Reopening the bge-stamped vault with the default http model:

```
CRITICAL vault embeddings were built with 'bge-micro-v2-onnx' but the server is
configured for 'nomic-embed-text-v2-moe:latest' — semantic tools disabled. …
REJECTED: … (returned by semantic_search / suggest_tags / ingest_chunks)
```

## HTTP path regression

Repo `vault/` (nomic-stamped, hosted endpoint): no mismatch, `semantic_search`
"gate enforcement for knowledge writes" → `verdict: ok`, 0.410 top hit —
behavior unchanged; `embed.batch` events now carry `backend:"http"`.
