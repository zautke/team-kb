# PLANS — team-kb (self-evolving agentic knowledge system)

## Goal

Replace basic-memory master-kb with custom tooling: markdown-canonical vault + C# MAF curator agents
as MCP tools + SQLite FTS5/vector index + Neo4j mirror. Defects made unrepresentable by tooling
(closed enums in tool schemas, computed paths/inverses, write-time link resolution, staged commits).
Approved plan: `docs/plan-2026-08-11-teardown-rebuild.md` (research appendix R1-R6).

## Locked decisions

Fresh system (not master-kb evolution); C# MAF end-to-end; target machine has LMStudio+ONNX (local
inference legal there, NOT on largo); poach neo4j-graphrag; aggressive ontology reset (10 classes /
14 verbs / 12 obs kinds — `_meta/ontology.md`); P1 "Stratified Memory Organism" folder=tier layout;
net10.0 (adagio compiles; dotnet 10.0.302).

## Phases

- [x] M0 Core: constitution, gates-as-code, staged propose/commit, FTS5, episodes, MCP server, gate suite (18/18 on adagio) — **except MCP handshake open issue**
- [ ] M0.1 Fix MCP stdio handshake (see CURRENT_TASK_STATE)
- [ ] M1 Retrieval: embeddings (IEmbeddingGenerator → LM Studio), sqlite-vec, RRF fusion, PPR tiebreak, verdict contract, plan_turn router; bump SQLitePCLRaw
- [ ] M2 Graph: Neo4j mirror (neo4j-graphrag patterns), link analytics, hubs
- [ ] M3 Self-learning: consolidation daemon, decay+utility, contradiction operators, retrieval-miss replay
- [ ] M4 Specialists: MAF agents-as-MCP-tools (curator, ontologist, consolidator, sweeper, resolver, librarian)
- [ ] M5 Code-Cartographer (jcodemunch mirror; spec in docs/research R4)
- [ ] Migration: master-kb v0.2 → v1.0 via shim tables (ontology.md) + migration report

## Non-goals

Compliance ontology (GLBA/17a-4/clearance) — dead with the old vault-kit. Building anything on largo.
