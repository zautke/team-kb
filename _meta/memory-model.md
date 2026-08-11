---
title: "team-kb Memory Model v1.0.0"
type: meta
kb_version: "1.0.0"
status: active
created: 2026-08-11
---

# Memory Model — five tiers (P1 "Stratified Memory Organism")

Folders encode memory strata; tier = retrieval scope = decay policy.

```
team-kb-vault/
├── _meta/          # constitution, ontology, registries, versions — anchor-protected
├── inbox/          # WORKING: untriaged capture; excluded from default retrieval
├── episodes/       # EPISODIC: immutable session/event/incident records, append-only
├── knowledge/      # SEMANTIC: entity notes, per-class subfolders (path computed)
├── playbooks/      # PROCEDURAL-hot: ACE delta-bullet playbooks + per-domain cheatsheets
├── procedures/     # PROCEDURAL-cold: verified parameterized workflows (Voyager-gated)
└── hubs/           # HIERARCHICAL: auto-regenerated community/index notes (curator-owned)
```

| Tier | Write path | Retrieval | Decay |
|---|---|---|---|
| Working (inbox/ + session journal) | any agent, ungated | excluded by default | session end → episode or discard |
| Episodic (episodes/) | auto-capture, append-only | temporal + provenance queries | FadeMem differential decay; never deleted |
| Semantic (knowledge/) | curator-gated staged commit | RRF hybrid (FTS+vector) + PPR link-walk | per-class half-life + MemRL utility |
| Procedural (playbooks/, procedures/) | ACE deltas / verification gate | loaded-first (cheatsheet), then on-demand | usage-based (uses/wins/losses/last_used) |
| Hierarchical (hubs/) | curator-regenerated only | entry points, progressive disclosure | rebuilt, not decayed |

## Flows

- **Capture** (Reflexion): notable/failed runs auto-emit one typed episode.
- **Curate** (ACE): consolidator merges episodes as append-only delta bullets into domain playbooks —
  never whole-note rewrites (anti context-collapse).
- **Promote** (AWM + Voyager gate): pattern recurring ≥3× AND passing a real check → named procedure
  note with `verified: true`. Curator refuses unverified promotion.
- **Consolidate + decay** (nightly, sleep-time): episodic→semantic promotion, utility updates from
  retrieval outcomes, decayed notes archived (status change, never deleted). `_meta/` + anchors exempt.
- **Retrieve**: playbook (hot) → procedures → PPR walk from query-matched notes into cases/insights.
  Every retrieval logs hit/miss; misses replay as curation repair (SAGE loop).

## Frontmatter utility fields (MemRL)

`uses`, `wins`, `losses`, `last_used` — maintained by the server on retrieval feedback, drive decay
and hub ranking.
