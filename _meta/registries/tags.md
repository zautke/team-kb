---
title: "team-kb Tag Registry"
type: meta
kb_version: "1.0.0"
status: active
created: 2026-08-11
---

# Tag Registry (C-3: registry-before-choice)

Only namespaced tags are legal; the namespace set is closed, the values are registered here.
`teamkb-mcp` rejects unregistered tags at the API.

| Namespace | Purpose | Seed values |
|---|---|---|
| `domain/` | knowledge domain | (registered on first curated use) |
| `project/` | project scope | (mirrors knowledge/project/ entries) |
| `status/` | lifecycle markers | `status/anchor`, `status/verified`, `status/draft` |
| `source/` | provenance shorthand | `source/session`, `source/web`, `source/paper`, `source/code` |
| `machine/` | machine relevance | (registered per host) |

Adding a value: curator appends a row here in the same staged commit that first uses it. Adding a
namespace: KGCL evolution proposal + human gate.
