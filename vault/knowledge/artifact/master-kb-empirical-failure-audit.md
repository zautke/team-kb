---
title: "master-kb Empirical Failure Audit"
type: entity
kb_version: "1.0.0"
entity_class: Artifact
permalink: knowledge/artifact/master-kb-empirical-failure-audit
created: 2026-08-13T15:53
modified: 2026-08-13T15:53
status: active
confidence: 0.9
tags:
  - kb/artifact
  - kb/status/active
  - domain/curation
provenance:
  - source: "docs/research/2026-08-11-kb-failure-postmortem-v1.md"
    author: "agent:curator"
    captured_at: "2026-08-13T15:53:44Z"
    confidence: 1.0
---

## Overview
R5 research dossier: sampled empirical audit of the legacy master-kb — missing frontmatter, three relation dialects, one-sided relations, orphaned protocols — the defect inventory the gate suite replays as tests.

## Relations
- MENTIONS :: [[knowledge/concept/gates-as-code]] {since: 2026-08-11}

## Observations
- [fact] Worst offender had 6 of 9 required fields missing and zero relations despite being a blocking protocol.
- [lesson] Every sampled relation was one-sided — no back-edge on the target; inverses must be computed, never authored.
