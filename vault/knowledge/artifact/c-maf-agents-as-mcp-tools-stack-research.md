---
title: "C# MAF Agents-as-MCP-Tools Stack Research"
type: entity
kb_version: "1.0.0"
entity_class: Artifact
permalink: knowledge/artifact/c-maf-agents-as-mcp-tools-stack-research
created: 2026-08-13T15:52
modified: 2026-08-13T15:52
status: active
confidence: 0.9
tags:
  - kb/artifact
  - kb/status/active
  - domain/dotnet
provenance:
  - source: "docs/research/2026-08-11-csharp-maf-mcp-stack.md"
    author: "agent:curator"
    captured_at: "2026-08-13T15:52:45Z"
    confidence: 1.0
---

## Overview
R3 research dossier: Microsoft Agent Framework 1.17.0, agents exposed as MCP tools, ModelContextProtocol 2.1.0, remote embedding generators, and exemplar repositories grounding the original C# implementation.

## Relations
- MENTIONS :: [[knowledge/concept/gates-as-code]] {since: 2026-08-11}

## Observations
- [fact] IEmbeddingGenerator abstracts the embedding endpoint behind a base URI — LM Studio locally or a tunnel remotely.
