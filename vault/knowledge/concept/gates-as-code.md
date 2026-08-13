---
title: "Gates as Code"
type: entity
kb_version: "1.0.0"
entity_class: Concept
permalink: knowledge/concept/gates-as-code
created: 2026-08-13T15:50
modified: 2026-08-13T15:50
status: active
confidence: 0.9
tags:
  - kb/concept
  - kb/status/active
  - domain/curation
  - project/team-kb
isolated_justification: "genesis anchor"
provenance:
  - source: "_meta/constitution.md"
    author: "agent:curator"
    captured_at: "2026-08-13T15:50:51Z"
    confidence: 1.0
---

## Overview
The constitution's core principle: a rule not enforced by code does not exist. Closed vocabularies live in tool JSON schemas, paths and inverse edges are computed server-side, and every write passes validator gates C2/C3/C4/I1/I4/PROV/HYP/TAG.

## Observations
- [fact] C1/C6/C7 are structurally unrepresentable at the API (enums, computed paths, scope regex) rather than validated after the fact. (provenance: _meta/constitution.md)
- [lesson] master-kb died of prose gates — rules stated in documents that no tool enforced. (provenance: _meta/constitution.md)
