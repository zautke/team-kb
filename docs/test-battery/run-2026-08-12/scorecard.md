# GA Scorecard — E2E battery run 2026-08-12

Vault: `~/vault/kb-test` · Corpus: 13 docs (7 research + 6 whitepapers) + 3 genesis anchors · θ_semantic = 0.30 (calibrated this run from 0.45; true-match floor 0.30, true-absent ceiling 0.163)

## Modality battery (4 × 2) + probes — GA alignment scores

| # | Search | Result | Score | Justification |
|---|--------|--------|-------|---------------|
| FTS-1 | "bi-temporal Graphiti" | ok → self-evolving-KG survey #1 | 1.0 | Exactly the doc holding the Graphiti bi-temporal claim, rank 1 |
| FTS-2 | "duplicate slugs orphans census" | ok → formal post-mortem #1 | 1.0 | Paraphrase hit the census doc directly |
| SEM-1 | "how does the knowledge base stay healthy over time" | ok → memory-organism WP, self-learning survey, curation-tactics WP | 0.9 | All three top hits on-intent; curation-tactics arguably #1, ranked #3 |
| SEM-2 | "mathematical foundations of typed graphs with constraints" | ok → formal-theory WP #1 | 1.0 | Cross-doc analogy resolved to the right paper |
| TAG-1 | domain/agent-memory | ok → 5 notes | 1.0 | Complete and precise tag plane recall |
| TAG-2 | kb/concept prefix | ok → 3 anchors | 1.0 | Server-computed class plane complete |
| GRAPH-1 | backlinks(gates-as-code) | 6 backlinks, correct inverse verbs | 1.0 | MENTIONED_BY ×4 + DESCRIBED_BY ×2, all real |
| GRAPH-2 | backlinks(formal post-mortem) | 3 × SOURCE_OF | 1.0 | Whitepaper derivation edges all present |
| PROBE-1 | "quantum blockchain kubernetes recipes" (FTS) | **absent** | 1.0 | Correct honest verdict |
| PROBE-2 | "baking sourdough bread" (semantic) | **absent** (top 0.163) | 1.0 | θ holds under calibration; top score reported |

**Mean alignment score: 0.99** (gate requires ≥ 0.7 as secondary signal).

## Deterministic gate (primary)

- Per-doc recall, 13/13 docs: FTS=Y SEM=Y TAG=Y GRAPH=Y (all four modalities, every doc) → **PASS**
- Zero false absents; both expected-absent probes returned absent → **PASS**
- Semantic waivers needed: none (0 after θ calibration)

## Iterations

1. **Run 1**: 5 whitepapers FAILED at CA-3 (embed timeout, 30s, large batches). Per failure policy: marked failed, battery continued, no infinite retry.
2. **Fix**: embed sub-batching (8/request, 90s timeout) + submission resume path in driver. Unit suite re-run: 31/31.
3. **Run 2 (resume)**: all 5 whitepapers committed; anchors idempotently C2-rejected (gate working).
4. **Calibration**: SEM conceptual paraphrase at 0.319 < θ=0.45 (missed true match) → θ=0.30 in db meta; verified both directions.
5. **Back-pass**: `add_relations` added DESCRIBES edge post-commit; markdown + edge index + backlink all verified.
