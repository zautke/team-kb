---
title: "Verdict Honesty Contract"
type: entity
kb_version: "1.0.0"
entity_class: Concept
permalink: knowledge/concept/verdict-honesty-contract
created: 2026-08-13T15:50
modified: 2026-08-13T15:50
status: active
confidence: 0.9
tags:
  - kb/concept
  - kb/status/active
  - domain/agent-memory
  - domain/curation
isolated_justification: "genesis anchor"
provenance:
  - source: "_meta/memory-model.md"
    author: "agent:curator"
    captured_at: "2026-08-13T15:50:51Z"
    confidence: 1.0
---

## Overview
Every retrieval surface returns an explicit verdict (ok | absent). absent asserts the knowledge does not exist, and the agent contract is to report the gap and stop — no synonym retries.

## Observations
- [fact] Semantic search implements absent via a calibrated similarity floor stored in db meta; top score is always reported. (provenance: _meta/memory-model.md)
