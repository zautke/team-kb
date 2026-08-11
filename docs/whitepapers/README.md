# team-kb Whitepapers

Long-form educational expansions of the 2026-08-11 research dossier (`docs/research/`),
written for human consumption. Each paper explains its theory and maps it to this
project's implementation (existing code or milestone M1-M5).

| # | Paper | Expands | Core content |
|---|-------|---------|--------------|
| 01 | [Formal Graph Theory](01-formal-graph-theory.md) | post-mortem v2 (formal), self-evolving KG survey | Typed property graph $G$, gates C1-C8 as predicates, guarded transitions, drift/entropy math, BM25 · RRF · PPR with worked examples |
| 02 | [Memory Model](02-memory-model.md) | memory-model, self-learning loops | Working/episodic/semantic/procedural tiers, consolidation, decay $e^{-\lambda\Delta t}$, forgetting-as-feature, verdict contract |
| 03 | [Curation Tactics](03-curation-tactics.md) | post-mortems v1+v2, constitution, maintenance | Anatomy of KB rot, prose-gates-vs-code-gates doctrine, gate catalog, write path, defect-replay testing |
| 04 | [Self-Learning Loops](04-self-learning-loops.md) | agentic self-learning loops survey | Consolidation daemon, retrieval-miss replay, decay maintenance, contradiction resolution, ontology evolution, convergence + safety rails |
| 05 | [C#/MAF/MCP Architecture](05-csharp-maf-mcp-architecture.md) | C# MAF/MCP stack research | Stack rationale + version table, layered architecture (substrate ⊥ index), MCP server anatomy, agents-as-tools, cross-platform case study |
| 06 | [Code Cartography](06-code-cartography.md) | jcodemunch functional spec | Symbol graphs, ranked context, blast radius, negative evidence, code-as-KG-nodes thesis, M5 sketch |

Reading order: 03 (why) → 01 (theory) → 02 (memory) → 04 (loops) → 05 (build) → 06 (M5).
