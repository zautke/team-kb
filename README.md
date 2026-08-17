# team-kb

Self-evolving agentic knowledge system for a software team. Replaces the basic-memory-based
master-kb with custom tooling: markdown-canonical vault + C# (Microsoft Agent Framework) curator
agents exposed as MCP tools + SQLite/FTS5+vector index + Neo4j analytics mirror.

Built from a 6-report research dossier (`docs/research/`) and a formal post-mortem of the previous
KB. Core stance: **defects are made unrepresentable by tooling, not discouraged by prose** — closed
vocabularies live in MCP tool schemas, paths and inverse edges are computed by the server, links
resolve at write time, and every write is a staged propose→commit.

## Layout

```
_meta/           # constitution, ontology v1.0, memory model, maintenance procedures, registries, versions
docs/research/   # research dossier R1-R6 (2026-08-11)
src/             # .NET solution: TeamKb.Mcp (M0 server), TeamKb.Core, tests
```

## Documents

- [`_meta/constitution.md`](_meta/constitution.md) — formal model G=(V,E,τ,π,ω), constraints C1-C8, invariants I1-I4, write lifecycle
- [`_meta/ontology.md`](_meta/ontology.md) — 10 entity classes / 14 verbs / 12 observation kinds + v0.2 shims
- [`_meta/memory-model.md`](_meta/memory-model.md) — five memory tiers + self-learning flows
- [`_meta/maintenance.md`](_meta/maintenance.md) — 8 scheduled procedures + contradiction-operator table
- [`docs/research/README.md`](docs/research/README.md) — dossier index

## Phasing

M0 core store+gates → M1 hybrid retrieval → M2 Neo4j graph → M3 self-learning loops → M4 specialist
MAF agents → M5 code-graph integration. M0 is usable alone.


