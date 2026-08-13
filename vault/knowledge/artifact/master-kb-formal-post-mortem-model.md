---
title: "master-kb Formal Post-Mortem Model"
type: entity
kb_version: "1.0.0"
entity_class: Artifact
permalink: knowledge/artifact/master-kb-formal-post-mortem-model
created: 2026-08-13T15:54
modified: 2026-08-13T15:54
status: active
confidence: 0.9
tags:
  - kb/artifact
  - kb/status/active
  - domain/knowledge-graphs
  - domain/curation
provenance:
  - source: "docs/research/2026-08-11-kb-failure-postmortem-v2-formal.md"
    author: "agent:curator"
    captured_at: "2026-08-13T15:54:26Z"
    confidence: 1.0
---

## Overview
R6 research dossier: full legacy census (653 notes: 35.2% dangling wikilinks, 53.8% orphans, 31 duplicate slugs) grounded in KG literature, yielding the formal model G=(V,E,τ,π,ω) and constraints C1-C8 / I1-I4 that became the constitution.

## Relations
- SUPERSEDES :: [[knowledge/artifact/master-kb-empirical-failure-audit]] {since: 2026-08-11}
- MENTIONS :: [[knowledge/concept/gates-as-code]] {since: 2026-08-11}

## Observations
- [fact] Census: 189 distinct observation kinds with a singleton tail — vocabulary sprawl without closure.
- [fact] The graph was never a graph — a folder of documents with decorative links.
