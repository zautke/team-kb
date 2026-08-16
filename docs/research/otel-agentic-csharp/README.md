# OTel for agentic AI in C# — research corpus

Pre-collected, source-cited knowledge base for the follow-up implementation
team: OpenTelemetry instrumentation of C#/.NET agentic systems, from zero to
Azure-deployed enterprise production with stakeholder-visible live telemetry.

All research verified current as of **2026-08-15** via web search, official
docs, NuGet/registry checks, and GitHub source reads. Every document ends
with a Sources section (URL + accessed date + what it supports). Conflicting
or unverified claims are flagged inline, not averaged away.

| Doc | Covers |
|---|---|
| [01-genai-semconv.md](01-genai-semconv.md) | gen_ai.* span/metric/event conventions, agent spans, stability status, gaps |
| [02-dotnet-otel-foundations.md](02-dotnet-otel-foundations.md) | ActivitySource/Meter/ILogger → OTel SDK, OTLP config, sampling, processors |
| [03-agent-framework-instrumentation.md](03-agent-framework-instrumentation.md) | MAF / Semantic Kernel / M.E.AI / MCP C# SDK telemetry surfaces + correlation |
| [04-azure-monitor-appinsights.md](04-azure-monitor-appinsights.md) | Azure Monitor distro, table mapping, KQL recipes, dashboards, alerting |
| [05-aspire-local-loop.md](05-aspire-local-loop.md) | Aspire dashboard as the local OTLP dev loop |
| [06-collector-and-purview.md](06-collector-and-purview.md) | OTel Collector pipeline on Azure; Purview DSPM for AI governance boundary |
| [07-production-hardening.md](07-production-hardening.md) | Redaction, cost/cardinality, tail sampling, RBAC, SLOs, wallboard rules |
| [08-zero-to-azure-roadmap.md](08-zero-to-azure-roadmap.md) | Phased implementation path + decisions D0–D4 (LOCKED 2026-08-16; start here) |
| [09-local-deployment.md](09-local-deployment.md) | Runbook for the portable Docker local loop (`deploy/otel/` — Phases 1–2 executable) |
| [implementation-log/](implementation-log/) | Dated evidence per implementation phase |

Consumption: implementation team reads 08 first for the path and decisions,
then the per-phase doc as each phase starts. Decisions D0–D4 are explicitly
reserved for the project owner.
