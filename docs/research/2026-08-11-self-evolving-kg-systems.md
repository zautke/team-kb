---
title: "R1 — Self-evolving KG construction (agent: research-kg)"
type: research
status: active
created: 2026-08-11
provenance:
  - source: "session:2026-08-11-teamkb-rebuild-research"
    author: "agent:claude-fable-5"
tags: [research, rebuild, dossier-2026-08]
---

RESEARCH REPORT — Self-evolving KG construction & agentic memory for SE teams. All sources checked 2026-08-11. Caveat: entries built from search-result snippets + abstract pages; mechanism claims marked (abs) are abstract-level, not full-text verified.

# Ranked 10

**1. Graphiti / Zep (temporal KG)** — arXiv:2501.13956 (Jan 2025) | github.com/getzep/graphiti | neo4j.com/blog/developer/graphiti-knowledge-graph-memory/
Bi-temporal edges: t_valid/t_invalid (world time) + t_created/t_expired (ingest time). Episode → LLM extract → hybrid (semantic+BM25+traversal) conflict detection → contradicting edge gets t_invalid stamp, never deleted. Auto-ontology with node dedup; custom entity/edge types as Pydantic models. Retrieval does zero LLM calls. LongMemEval 63.8% (GPT-4o) vs Mem0 49.0%. STEAL: the 4-timestamp schema + invalidate-don't-delete rule — maps directly onto markdown frontmatter fields plus Neo4j mirror. Production OSS, Apache-2.0, Python, Neo4j/FalkorDB. Strongest temporal modeling in the field.

**2. SAGE — Self-Evolving Agentic Graph-Memory Engine** — arXiv:2605.12061 (May 2026, NeurIPS 2026) | github.com/aFastHero/sage_self_evolving_graph_memory
Two coupled roles: memory *writer* incrementally constructs graph memory from interaction history; Graph-Foundation-Model memory *reader* feeds retrieval outcomes back as training signal to the writer (abs). Explicitly attacks the "GraphRAG treats graph as static retrieval middleware" failure. Gains on multi-hop QA, open-domain retrieval, long-term agent-memory benchmarks. STEAL: closed writer↔reader loop — every retrieval that failed to recover an evidence chain becomes a repair instruction for extraction. For a team KB: log which notes retrieval *should* have surfaced, replay as extraction feedback. Research-grade code only.

**3. TOKI — bitemporal operator algebra for contradiction resolution** — arXiv:2606.06240 (Jun 2026, HKUST)
Reframes contradiction resolution as WRITE-TIME CONCURRENCY CONTROL. Types the four production heuristics — last-writer-wins, evidence-weighted merge, await-confirmation, per-rule policy — as one family of bitemporal operators over a dual-row schema, each with a declared isolation precondition and a provenance annotation preserving the losing fact in an audit row. 43pp with proofs. STEAL: stop hand-waving "the agent updates the note." Pick an explicit resolution operator per fact class (decisions = await-confirmation; benchmarks = last-writer-wins; incident findings = evidence-weighted) and keep the superseded claim in an audit block. Spec, no production impl.

**4. Cognee (memify)** — cognee.ai/blog/guides/ai-coding-agent-persistent-codebase-memory | particula.tech/blog/agent-memory-frameworks-tested-mem0-zep-letta-cognee-2026 (2026)
Apache-2.0, Python, MCP-native. Pipeline: AST-level code parsing → cognify (entity/relation extraction) → hybrid graph+vector store → **memify** refinement: rated responses feed back into edge weights, prunes stale nodes, reweights by usage signals, adds derived facts. 14 retrieval modes. Claimed >1M pipelines/month, ~70 companies. STEAL: usage-signal edge reweighting is the cheapest self-evolution mechanism available — count retrievals-that-helped per link, decay the rest. Top OSS scorer on storage architecture + self-improvement in 2026 comparisons. Best off-the-shelf candidate for the Neo4j mirror layer.

**5. Google Open Knowledge Format (OKF) v0.1** — cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing | marktechpost.com/2026/06/16/... (pub. 2026-06-12)
Knowledge = directory of markdown + YAML frontmatter; only mandatory field is `type`. Concepts cross-link via plain markdown links → the directory IS the graph. Optional per-bundle `index.md` (progressive disclosure) and `log.md` (chronological change history). Full spec fits one page. STEAL: this is literally our architecture, standardized — adopt `type:` + link-as-edge + per-bundle `log.md` and the markdown KB becomes machine-portable, zero new surfaces, no vendor lock-in. Highest steal-to-effort ratio on this list.

**6. HAGE — RL-driven weighted graph evolution** — arXiv:2605.09942 (2026-05-11) | github.com/FredJiang0324/HAGE_MVPReview
Memory = four orthogonal relation views (Semantic, Temporal, Causal, Entity) over shared nodes; each edge carries a trainable relation feature vector. LLM classifier detects the query's relational intent; a QueryRouter MLP modulates matching edge dimensions; retrieval = query-conditioned sequential traversal. Edge features + router co-trained by policy-gradient RL on downstream reward (abs). STEAL: the four-view decomposition even without the RL — a team KB fact is rarely "related," it is caused-by, superseded-by, co-occurred-with, or about-same-entity. Typing edges that way makes traversal answerable. Research code.

**7. Codebase-Memory MCP** — arXiv:2603.27277 (Mar 2026) | github.com/DeusData/codebase-memory-mcp
Tree-sitter KG over 158 languages, two-pass: syntactic tree-sitter pass (defs/calls/imports) + hybrid LSP type-aware pass refining call edges via import graph and cross-file definition registry. Call-graph traversal, impact analysis, community discovery. Persisted in SQLite, kept fresh by a background watcher → sub-ms queries against the working tree. 31 repos: 83% answer quality, 10× fewer tokens, 2.1× fewer tool calls. Single static binary, zero deps. STEAL: incremental-watcher + community-detection combo; the code graph is the substrate the prose KB should link into. Production-grade OSS.

**8. TGMS + MemTX (agent-native temporal DB layer)** — TGMS arXiv:2607.10265 | MemTX arXiv:2607.23929 | also MemTxn arXiv:2607.27834 (Jul 2026)
TGMS: bi-temporal property graph exposing **13 verified temporal operators as agent tools** — typed, deterministic, bounded, cost-guarded; separates valid from transaction time so "as of T, what did we believe?" is answerable; LLM plans operator calls, system computes, and every numeric/entity/ordering/pattern claim is checked against a content-addressed execution trace. MemTX: writes staged in snapshot-isolated transactions, validate-and-commit admission, beliefs mature tentative → action-safe, irreversible tool calls gated on in-flight belief state, retraction triggers typed cascading repair of derived records. STEAL: trace-grounded answer checking, and never letting an agent's write be a commit.

**9. AutoSchemaKG** — arXiv:2505.23628 / ACL 2026 long (aclanthology.org/2026.acl-long.942/) | github.com/HKUST-KnowComp/AutoSchemaKG
No predefined schema: LLM simultaneously extracts triples AND induces the schema via conceptualization + clustering + semantic alignment. Built ATLAS from 50M+ docs → 900M+ nodes, 5.9B edges. Schema induction hits 92% semantic alignment with human-crafted schemas, zero manual intervention. Events are first-class citizens, capturing causality, temporality, procedural knowledge that entity-only graphs drop. STEAL: don't pre-declare the team ontology — induce it from existing notes, freeze the top-N concepts as the frontmatter `type:` vocabulary, re-induce quarterly. Schema evolution with a human gate. OSS, Python.

**10. FadeMem + Episodic→Semantic Consolidation** — FadeMem arXiv:2601.18642 (Jan 2026) | Episodic-to-Semantic Consolidation Without Identity Drift arXiv:2607.01988 (Jul 2026)
FadeMem: differential decay rates per memory, modulated by semantic relevance × access frequency × temporal pattern — biologically-inspired forgetting for cost control. The consolidation paper attaches an explicit forgetting curve so older un-rehearsed memories decay while episodic traces are promoted into semantic abstractions, with an identity-drift guard preventing consolidation from rewriting who/what the agent is. STEAL: the drift guard. Session logs (episodic) → distilled protocol notes (semantic) is the right pipeline, but consolidation must be forbidden from mutating anchor/protocol notes.

## Runners-up (evaluated, ranked out)
- HippoRAG 2 / LightRAG / MS GraphRAG — still the retrieval-mechanism reference (PPR seeds, dual-level retriever + incremental index patches, community summaries) but all treat the graph as static middleware. Survey: arXiv:2506.05690.
- **Mem0 — dropped its graph module entirely in v3** (commit a488e190, PR #4805, merged 2026-04-14). Do NOT build on Mem0ᵍ.
- Letta / MemGPT — OS-style RAM/disk paging; best for stateful runtimes, not KG construction.
- Structurally Aligned Subtask-Level Memory for SE Agents — arXiv:2602.21611 (+4.7pp mean Pass@1 SWE-bench Verified; memory keyed to functional decomposition, not task instance).
- Survey list: github.com/DEEP-PolyU/Awesome-GraphMemory.

# Synthesis — the converged proven core (10 lines)
1. Bi-temporal is settled. Valid-time vs transaction-time, 4 timestamps. Graphiti, TOKI, TGMS, MemTX land here independently.
2. Invalidate, never delete. Contradiction = stamp t_invalid + keep the loser in an audit row. Unanimous.
3. Contradiction handling is a WRITE-time concern, not a retrieval hack — declare the resolution operator and its isolation level per fact class.
4. Write ≠ commit. Staged, validated, provenance-carrying belief lifecycle before a fact becomes action-safe.
5. Schema is induced, not declared — LLM co-extracts triples and schema; humans gate the vocabulary.
6. Events/episodes are first-class nodes, not just entities — that's where causality and procedure live.
7. Retrieval feedback rewrites the graph. This is THE 2026 delta: edge weights from usage (Cognee), from RL reward (HAGE), from failed evidence chains (SAGE).
8. Decay is required and must be guarded — differential forgetting by relevance×frequency×recency, with anchor/protocol notes exempt from consolidation drift.
9. Typed multi-relational edges beat one "related" edge — semantic / temporal / causal / entity views over shared nodes.
10. Markdown + frontmatter + links is now a legitimate substrate (OKF v0.1); the graph DB is a mirror/index, not the source of truth — exactly the markdown+MCP+optional-Neo4j shape.

RECOMMENDED STEAL-STACK: OKF frontmatter conventions (`type:`, `log.md`) → Graphiti 4-timestamp bi-temporal fields → TOKI operator-per-fact-class resolution → Cognee-style usage reweighting → FadeMem decay with protocol-note exemption → Codebase-Memory MCP as the code-side substrate the prose links into.
