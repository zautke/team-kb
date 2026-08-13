---
title: "C# MAF MCP Architecture Whitepaper"
type: entity
kb_version: "1.0.0"
entity_class: Artifact
permalink: knowledge/artifact/c-maf-mcp-architecture-whitepaper
created: 2026-08-13T16:03
modified: 2026-08-13T16:03
status: active
confidence: 0.9
tags:
  - kb/artifact
  - kb/status/active
  - domain/dotnet
provenance:
  - source: "docs/whitepapers/05-csharp-maf-mcp-architecture.md"
    author: "agent:curator"
    captured_at: "2026-08-13T16:03:29Z"
    confidence: 1.0
---

## Overview
Whitepaper 05: why .NET carries the knowledge substrate — the layering of Core/Mcp/Tests, cross-platform bring-up findings, and the verified 18/18 gate-suite state of the original implementation.

## Relations
- DERIVES_FROM :: [[knowledge/artifact/c-maf-agents-as-mcp-tools-stack-research]] {since: 2026-08-11}
- DERIVES_FROM :: [[knowledge/artifact/master-kb-formal-post-mortem-model]] {since: 2026-08-11}

## Observations
- [fact] Cross-machine bring-up surfaced a distinct bug class: Windows file locking, AppleDouble pollution, shell-quoting corruption.
