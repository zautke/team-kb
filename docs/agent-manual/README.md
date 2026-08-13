# Agent Manual — how to use and populate the team-kb knowledge base

You are an agent working against a **gated knowledge vault**. This folder is the
operational manual: what to do, in what order, with real commands and real
outputs. Everything here has been executed against the live system — no
invented examples.

## Routing — start with what you're trying to do

| I want to… | Read |
|------------|------|
| Get oriented in 5 minutes and run my first query | [01-quickstart.md](01-quickstart.md) |
| Put documents into the KB (the main job) | [02-populate-the-kb.md](02-populate-the-kb.md) |
| Understand a `REJECTED` response and fix it | [03-gates-playbook.md](03-gates-playbook.md) |
| Find things, and know when to stop looking | [04-retrieval-playbook.md](04-retrieval-playbook.md) |
| Look up a tool's arguments and return shape | [05-tool-reference.md](05-tool-reference.md) |
| Fix something that broke | [06-troubleshooting.md](06-troubleshooting.md) |
| Wire the MCP server into a host, or change its vault/endpoint | [07-mcp-server-config.md](07-mcp-server-config.md) |

Related material outside this folder: `AGENTS.md` (repo rules),
`plugin/skills/` (per-step curation discipline), `docs/telemetry-events.md`
(event/metric schema), `_meta/` (the constitution itself — read-only).

## The mental model, in one page

**The vault is markdown; the database is a derived index.** Notes are real files
under `<vault>/knowledge/<class>/` and `<vault>/episodes/`. SQLite holds search,
edges, tags and embeddings, and can be re-derived from the markdown at any time.
Delete the database and nothing is lost; delete the markdown and everything is.

**There is exactly one write path: propose → commit.** You never write vault
files directly, and you have no tool that lets you. Every write is validated by
eight gates before it lands. A rejection is the system working correctly; it
means the *curation* is wrong, not the gate.

**Vocabulary is closed and enforced at the API.** Ten entity classes, fourteen
relation verbs, twelve observation kinds, five tag namespaces. These appear as
enums in the tool schemas, so an off-vocabulary value is not something you can
express. Do not propose extending them.

**Structure is computed, never authored.** The folder comes from the entity
class. The permalink comes from the title. Inverse relations (`MENTIONED_BY` for
your `MENTIONS`) are computed at read time. The `kb/*` tag plane is added by the
serializer. You supply meaning; the server supplies structure.

**Retrieval tells you the truth.** Every search returns `verdict: ok` or
`verdict: absent`. `absent` is a real answer: the knowledge does not exist.
Report the gap and stop — do not retry with synonyms until something matches.

**Two roles.** The *general agent* (GA) submits documents and retrieves
knowledge; it deliberately holds no write tools. The *curator agent* (CA) runs
the ingestion pipeline and is the only holder of propose/commit. If you are
retrieving, you are GA. If you are ingesting, you are CA.

## The shape of a note

```markdown
---
title: "Curation Tactics Whitepaper"
type: entity
kb_version: "1.0.0"
entity_class: Artifact
permalink: knowledge/artifact/curation-tactics-whitepaper
created: 2026-08-12T21:18
modified: 2026-08-12T21:18
status: active
confidence: 0.9
tags:
  - kb/artifact
  - kb/status/active
  - domain/curation
provenance:
  - source: "docs/whitepapers/03-curation-tactics.md"
    author: "agent:curator"
    captured_at: "2026-08-12T21:18:42Z"
    confidence: 1.0
---

## Overview
Whitepaper 03: how team-kb stays healthy where master-kb rotted — curator duties,
write-time resolution, near-duplicate discipline, tag registry, and the
maintenance rituals.

## Relations
- DERIVES_FROM :: [[knowledge/artifact/master-kb-empirical-failure-audit]] {since: 2026-08-11}
- DESCRIBES :: [[knowledge/concept/gates-as-code]] {since: 2026-08-11}

## Observations
- [fact] The curator owns propose/commit and enforces C2, C3, C4, I1, I4, PROV, HYP, TAG.
- [fact] The ontologist proposes vocabulary changes but never applies them.
```

You author: title, class, overview, relations, observations, provenance, tags,
confidence. Everything else in that file was generated.
