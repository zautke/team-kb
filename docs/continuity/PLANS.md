# PLANS — team-kb (self-evolving agentic knowledge system)

## Goal

Replace basic-memory master-kb with custom tooling: markdown-canonical vault + C# MAF curator agents
as MCP tools + SQLite FTS5/vector index + Neo4j mirror. Defects made unrepresentable by tooling
(closed enums in tool schemas, computed paths/inverses, write-time link resolution, staged commits).
Approved plan: `docs/plan-2026-08-11-teardown-rebuild.md` (research appendix R1-R6).

## Locked decisions

Fresh system (not master-kb evolution); C# MAF end-to-end; target machine has LMStudio+ONNX (local
inference legal there, NOT on the authoring Mac); poach neo4j-graphrag; aggressive ontology reset (10 classes /
14 verbs / 12 obs kinds — `_meta/ontology.md`); P1 "Stratified Memory Organism" folder=tier layout;
net10.0 (build host compiles; dotnet 10.0.302).

## Pivot 2026-08-12 — C# stack punted in place; lightweight plugin path

C# MAF stack (src/) frozen untouched (no local dotnet; ssh-iteration too slow). Live path: dual-target
plugin (Claude Code `plugin/` + Copilot `.github/agents|skills`) with zero-dep Python stdio MCP server
porting the 8 gates byte-for-byte, PLUS chunk/embed/semantic/tag-search/reindex tools (12 total).
Embeddings via hosted Ollama (`nomic-embed-text-v2-moe`), env-swappable to ONNX in target env.
Approved plan: `~/.claude/plans/i-need-to-set-deep-lobster.md` (base + runbook Appendix A + gap
addendum Appendix B from 3-reviewer distillation). E2E battery vault: `~/vault/kb-test`.

## Status 2026-08-13

M0.6 done: server (15 tools, 8 gates, 45/45 tests), populated repo vault, telemetry,
re-derivable index, 8-doc agent manual, project-scope MCP registration. The KB is
operational and documented for a consuming team. M1 (RRF fusion, richer verdicts) is
unblocked but deliberately deferred until the corpus is larger than 13 documents.

## Phases

- [x] M0 Core: constitution, gates-as-code, staged propose/commit, FTS5, episodes, MCP server, gate suite (18/18 on the build host) — **except MCP handshake open issue**
- [ ] M0.1 Fix MCP stdio handshake (see CURRENT_TASK_STATE)
- [ ] M1 Retrieval: embeddings (IEmbeddingGenerator → LM Studio), sqlite-vec, RRF fusion, PPR tiebreak, verdict contract, plan_turn router; bump SQLitePCLRaw
- [ ] M2 Graph: Neo4j mirror (neo4j-graphrag patterns), link analytics, hubs
- [ ] M3 Self-learning: consolidation daemon, decay+utility, contradiction operators, retrieval-miss replay
- [ ] M4 Specialists: MAF agents-as-MCP-tools (curator, ontologist, consolidator, sweeper, resolver, librarian)
- [ ] M5 Code-Cartographer (jcodemunch mirror; spec in docs/research R4)
- [ ] Migration: master-kb v0.2 → v1.0 via shim tables (ontology.md) + migration report

## Non-goals

Compliance ontology (GLBA/17a-4/clearance) — dead with the old vault-kit. Building anything on the authoring Mac.
