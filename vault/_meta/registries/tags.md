# Tag Registry

Closed namespaces: `domain/` `project/` `status/` `source/` `machine/`.
Registry-before-choice: a tag must have a row here (and be registered via
`register_tag`) before any note may use it. The `kb/*` plane is server-computed
and reserved — never register or hand-write `kb/*` tags.

| tag | description | registered |
|-----|-------------|------------|
| status/anchor | protected anchor note; automated edits forbidden | seed |
| status/verified | content verified against its provenance | seed |
| status/draft | unverified draft | seed |
| source/session | captured from an agent session | seed |
| source/web | captured from a web source | seed |
| source/paper | captured from a paper | seed |
| source/code | captured from source code | seed |
| domain/knowledge-graphs | knowledge graph construction, schemas, integrity | 2026-08-13 |
| domain/agent-memory | agentic memory systems, self-learning loops, consolidation | 2026-08-13 |
| domain/curation | knowledge curation practice, gates, dedup, provenance | 2026-08-13 |
| domain/dotnet | .NET / C# implementation stack | 2026-08-13 |
| domain/obsidian | Obsidian as a vault UI: properties, tags, bases | 2026-08-13 |
| domain/code-cartography | code indexing, symbol maps, codebase intelligence | 2026-08-13 |
| project/team-kb | the team-kb knowledge system rebuild | 2026-08-13 |
