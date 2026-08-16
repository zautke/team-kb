# Azure Monitor / Application Insights for .NET Agentic-AI Telemetry

**Status: current as of 2026-08-15.** Instructional reference for wiring a .NET agentic-AI app (agents, tools, LLM calls) into Azure Monitor via OpenTelemetry (OTel), querying it with Kusto Query Language (KQL), exposing stakeholder dashboards, and alerting on agent Service Level Objectives (SLOs).

---

## 1. Packages and setup

Current stable versions (NuGet, verified 2026-08-15):

| Package | Version | Released | Use when |
|---|---|---|---|
| `Azure.Monitor.OpenTelemetry.AspNetCore` (the "Distro") | **1.6.0** | 2026-07-27 | ASP.NET Core apps — one-line setup, batteries included |
| `Azure.Monitor.OpenTelemetry.Exporter` | **1.8.3** | 2026-07-24 | Console/worker/non-ASP.NET apps, or when you compose your own OTel pipeline and only want the exporter |

Distro targets .NET 8.0 and .NET Standard 2.0.

### Distro setup (`UseAzureMonitor`)

```csharp
// Program.cs
builder.Services.AddOpenTelemetry().UseAzureMonitor();
```

Connection string, in preference order:
1. Env var `APPLICATIONINSIGHTS_CONNECTION_STRING` (preferred — keep it in `.env`/app settings, single source of truth).
2. Code: `UseAzureMonitor(o => o.ConnectionString = "InstrumentationKey=…;IngestionEndpoint=…")`.

### Microsoft Entra ID (formerly Azure Active Directory, AAD) auth

```csharp
builder.Services.AddOpenTelemetry().UseAzureMonitor(o =>
{
    o.Credential = new DefaultAzureCredential(); // Azure.Identity
});
```
Pair with "Local Authentication disabled" on the App Insights resource so only token-authenticated ingestion is accepted. The identity needs the **Monitoring Metrics Publisher** role on the resource.

### What the distro auto-instruments

- **Traces:** incoming ASP.NET Core requests, outgoing `HttpClient`, `SqlClient`.
- **Metrics:** App Insights standard metrics; ASP.NET Core + HttpClient metrics (on .NET 8+, the built-in `Microsoft.AspNetCore.Hosting` / `System.Net.Http` meters).
- **Logs:** `Microsoft.Extensions.Logging` (`ILogger`) and Azure SDK logs — no separate logging config needed.
- **Live Metrics:** enabled by default (`o.EnableLiveMetrics = false` to disable).

### What you must add for agentic telemetry

Nothing agent-specific is auto-instrumented by the distro itself. Register your agent framework's `ActivitySource`/`Meter` explicitly:

```csharp
builder.Services.AddOpenTelemetry()
    .UseAzureMonitor()
    .WithTracing(t => t.AddSource("Microsoft.Agents.AI", "MyCompany.AgentApp"))
    .WithMetrics(m => m.AddMeter("Microsoft.Agents.AI", "MyCompany.AgentApp"));
```

Emit agent spans per the **OTel Generative AI (GenAI) semantic conventions**: span names like `invoke_agent <name>`, `chat <model>`, `execute_tool <tool>`; attributes `gen_ai.operation.name`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.agent.name`, `gen_ai.tool.name`. Microsoft Agent Framework, Semantic Kernel, and Foundry SDKs emit these for you; hand-rolled agents should mirror them — every Azure agent-monitoring surface (Agents view, Grafana dashboards, Foundry) keys off them.

---

## 2. OTel signal → Application Insights table mapping (KQL implications)

Azure Monitor exporter maps OTel to classic App Insights tables:

| OTel signal | App Insights table | Notes |
|---|---|---|
| Span, kind `Server`/`Consumer` | `requests` | your inbound API call that starts an agent run |
| Span, kind `Client`/`Producer`/`Internal` | `dependencies` | **agent/LLM/tool spans land here** (they're usually Internal or Client) |
| Span attributes | `customDimensions` (string-typed bag) | `gen_ai.*` lives here — always `toint()`/`todouble()`/`tostring()` on extraction |
| Span events / exceptions | `exceptions` (exception events), `traces` (other events) | |
| `ILogger` logs | `traces` | severity in `severityLevel`; correlated via `operation_Id` |
| OTel metrics | `customMetrics` | pre-aggregated; **never sampled** |
| Resource attributes | `cloud_RoleName` (from `service.name`/`service.namespace`), `cloud_RoleInstance` | |

Correlation model: OTel `TraceId` → `operation_Id`; `SpanId` → `id`; parent span → `operation_ParentId`. Everything in one agent run shares `operation_Id`.

---

## 3. KQL recipes for agent traces

**Trace waterfall for one run:**
```kusto
union requests, dependencies, traces, exceptions
| where operation_Id == "<trace-id>"
| project timestamp, itemType, name, id, operation_ParentId, duration,
          success, agent = tostring(customDimensions["gen_ai.agent.name"]),
          op = tostring(customDimensions["gen_ai.operation.name"])
| sort by timestamp asc
```

**Token usage per agent / model (last 24 h):**
```kusto
dependencies
| where timestamp > ago(24h)
| where isnotempty(customDimensions["gen_ai.usage.input_tokens"])
| extend agent = tostring(customDimensions["gen_ai.agent.name"]),
         model = tostring(customDimensions["gen_ai.request.model"]),
         inTok  = toint(customDimensions["gen_ai.usage.input_tokens"]),
         outTok = toint(customDimensions["gen_ai.usage.output_tokens"])
| summarize calls=count(), input=sum(inTok), output=sum(outTok),
            total=sum(inTok+outTok) by agent, model
| order by total desc
```

**Most expensive runs:**
```kusto
dependencies
| where tostring(customDimensions["gen_ai.operation.name"]) == "invoke_agent"
| extend tok = toint(customDimensions["gen_ai.usage.input_tokens"])
             + toint(customDimensions["gen_ai.usage.output_tokens"])
| top 20 by tok desc
| project timestamp, operation_Id, name, tok, duration
```

**Error rate and latency percentiles per agent/tool:**
```kusto
dependencies
| where timestamp > ago(7d)
| where tostring(customDimensions["gen_ai.operation.name"]) in ("invoke_agent", "execute_tool", "chat")
| extend actor = coalesce(tostring(customDimensions["gen_ai.tool.name"]),
                          tostring(customDimensions["gen_ai.agent.name"]))
| summarize n=count(), errors=countif(success == false),
            p50=percentile(duration,50), p95=percentile(duration,95), p99=percentile(duration,99)
    by actor, bin(timestamp, 1h)
| extend errorRate = todouble(errors)/n
```

**Sampling sanity check** (is telemetry being sampled, and how hard):
```kusto
union requests, dependencies, traces, exceptions
| where timestamp > ago(1d)
| summarize RetainedPercentage = 100/avg(itemCount) by bin(timestamp, 1h), itemType
```
Note `itemCount`: sampled rows carry the inverse sample rate — use `sum(itemCount)` instead of `count()` whenever counting sampled tables.

---

## 4. Live Metrics, sampling, cost controls

- **Live Metrics:** on by default in the distro; ~1-second-latency stream of request/dependency rate, failures, CPU/memory. Not billed as ingested data; requires the Azure Monitor sampler for full compatibility.
- **Sampling in the distro** — not enabled at 100% forever; the .NET distro defaults to **rate-limited sampling at 5 traces/second**. Configure:
  ```csharp
  builder.Services.AddOpenTelemetry().UseAzureMonitor(o =>
  {
      o.TracesPerSecond = 10.0;      // rate-limited (default mode)
      // OR fixed-rate:
      // o.SamplingRatio = 0.1F; o.TracesPerSecond = null;  // ~10%
  });
  ```
  The custom Application Insights sampler keeps traces whole (no broken waterfalls) and stays Live-Metrics-compatible. Metrics are never sampled — alert on `customMetrics`, not on counted rows. Trace-based log sampling can drop logs tied to unsampled traces.
- **Ingestion sampling** (portal: App Insights → Usage and estimated costs → Data Sampling) drops data at the ingestion endpoint. Microsoft explicitly recommends against it except when you can't touch the source or need immediate relief — it breaks traces randomly. Prefer source-side sampling.
- **Daily cap:** set on the backing Log Analytics workspace (Usage and estimated costs → Daily cap). Hard stop on ingestion for the day — last-resort guard, creates telemetry gaps when tripped.
- **Pricing tiers:** workspace-based App Insights bills via Log Analytics — Pay-As-You-Go per GB, Commitment Tiers (100 GB/day and up) for discounts; consider the cheaper Basic table plan for high-volume verbose logs you only query occasionally. Agent apps with verbose prompt/completion capture are exactly where token/content logging + no sampling produces bill shock: decide deliberately whether to record prompt content (`gen_ai` content-capture switches in your framework) — it's both a cost and a privacy decision.

---

## 5. Stakeholder-visible display

Three realistic options, in increasing effort:

**a) Built-in Agents view (App Insights → "Agents (Preview)")** — zero-effort, opinionated. Shows agent runs, tool calls, models, token/cost tiles; drill into gen-AI-error traces; "simple view" of end-to-end transactions renders agent → LLM → tool steps as a story. Works for any telemetry following GenAI semantic conventions (Foundry, Copilot Studio, third-party/custom). Sharing = Azure RBAC on the App Insights resource (Reader suffices). Still preview-labeled; no customization.

**b) Azure Workbooks** — portal-native, parameterized KQL canvases. Strengths: parameters (time range, agent name dropdowns fed by KQL), tabs, ARM-deployable (dashboard-as-code), pinnable to Azure Dashboards. Sharing model: workbooks are ARM resources — access via Azure RBAC (`Workbook Reader`/`Contributor`); viewers need portal access and Reader on the underlying App Insights/workspace. Best when your audience already lives in the Azure portal and you want no extra infrastructure.

**c) Azure Managed Grafana** — richer visualization, cross-source dashboards, its own sharing/snapshot model. The Azure Monitor data source authenticates via managed identity and queries the same App Insights tables with KQL. Azure ships **prebuilt Gen-AI dashboards**: *Agent Framework*, *Agent Framework workflow*, *Foundry*, and coding-agent dashboards (GitHub Copilot, Claude Code, etc.); the Agents view has an "Explore in Grafana" button that lands on them, and "Save as" forks them for customization. Costs a Managed Grafana instance (or use the free "Dashboards with Grafana" embedded experience in App Insights); viewers need Grafana Viewer role (Grafana's own RBAC layered on Entra ID) — friendlier for non-Azure-portal stakeholders.

Tradeoff summary: Agents view = fastest, least flexible. Workbooks = flexible, Azure-native RBAC, no new service. Grafana = best visuals + prebuilt agent dashboards + audience outside the portal, at the cost of one more service and a second RBAC surface.

---

## 6. Azure AI Foundry (Microsoft Foundry) tracing integration

Yes — it connects to Application Insights, and this is now the paved road:

- Foundry observability (tracing, monitoring, evaluations) went **GA around March 2026** (announced Ignite 2025); some pieces (dashboard views, several agent evaluators, the App Insights Agents view) remain preview.
- You **connect an Application Insights resource to your Foundry project**; agent/model traces are stored there using standard OTel GenAI semantic conventions. Same data is viewable in the Foundry portal Monitoring tab, App Insights (Agents view / transaction search), and Grafana — one store, several lenses. Foundry's Monitoring tab has "View in Azure Monitor" and the Agents view links back.
- Framework coverage: Microsoft Agent Framework, OpenAI Agents SDK, LangChain/LangGraph, Semantic Kernel — enable the framework's tracing hook and export via the Azure Monitor distro/exporter.
- **Continuous evaluation** samples live traffic, scores it (groundedness, task adherence, tool-call accuracy, safety) and writes results next to your traces in App Insights — queryable with the same KQL/operation_Id joins.

For a .NET agent app: use the distro (section 1), add your `ActivitySource`, and point at the same App Insights resource the Foundry project is connected to — you get Foundry portal views for free.

---

## 7. Alerting for agent SLOs

Building blocks: **metric alerts** (fast, cheap, on metrics incl. `customMetrics`), **log search alerts** (scheduled KQL, 1-min minimum frequency, anything expressible in KQL), **action groups** (email/SMS/webhook/Teams/PagerDuty/Logic App/Function targets, reused across alerts).

Patterns for agent SLOs:

- **Availability/error-rate SLO** — log search alert on the error-rate query from §3 (`errorRate > 0.05` over 15 min, per-`actor` dimension splitting so each agent/tool alerts independently).
- **Latency SLO** — log search alert: `dependencies | where … invoke_agent | summarize p95=percentile(duration,95) | where p95 > 30000`. (Percentiles need log alerts; metric alerts only do avg/min/max/count on platform metrics.)
- **Token-burn / cost guard** — log search alert on hourly `sum(input+output tokens)` exceeding budget; catches runaway agent loops before the daily cap does. Prefer a custom `Meter` counter (`gen_ai.client.token.usage`-style) + metric alert for lower latency and immunity to trace sampling.
- **Silence detection** — alert when agent-run count drops to zero over 30 min (`summarize count()` with `< 1` threshold) — dead pipelines look like "no errors."
- **Daily-cap warning** — Azure emits an event/alert when the workspace cap is reached; wire it to the same action group so telemetry gaps are known, not discovered.

Remember sampling (§4): count-based log alerts on sampled tables must use `sum(itemCount)`; SLO-critical signals belong in metrics, which are never sampled.

---

## Sources (all accessed 2026-08-15)

- https://www.nuget.org/packages/Azure.Monitor.OpenTelemetry.AspNetCore — distro latest stable 1.6.0 (2026-07-27), .NET 8 / netstandard2.0 targets.
- https://www.nuget.org/packages/Azure.Monitor.OpenTelemetry.Exporter — exporter latest stable 1.8.3 (2026-07-24).
- https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/monitor/Azure.Monitor.OpenTelemetry.AspNetCore/README.md — `UseAzureMonitor` setup, connection-string options, `Credential`/Entra auth, auto-instrumented traces/metrics/logs, `TracesPerSecond` default 5/s, `SamplingRatio`, `EnableLiveMetrics`.
- https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-sampling — custom sampler, fixed-rate vs rate-limited, Live Metrics compatibility, ingestion sampling (not recommended), daily cap as last resort, `itemCount` retained-percentage validation query, metrics never sampled, trace-based log sampling.
- https://learn.microsoft.com/en-us/azure/azure-monitor/app/agents-view — Agents (Preview) view, GenAI-semconv basis, token/cost tiles, simple end-to-end view, Explore-in-Grafana, prebuilt Agent Framework/Foundry/coding-agent Grafana dashboards, Foundry "View in Azure Monitor" link.
- https://learn.microsoft.com/en-us/azure/foundry/concepts/observability and https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/trace-agent-setup — Foundry tracing built on OTel GenAI semconv, stored in connected App Insights; continuous evaluation writes scores beside traces; framework support (Agent Framework, OpenAI Agents SDK, LangChain/LangGraph).
- https://jannikreinhard.com/microsoft-foundry-observability/ — Foundry observability GA timeline (Ignite 2025 announce, GA ~March 2026, preview remnants); corroborates single-store/multi-lens model.
- https://github.com/microsoft/azure-skills/blob/main/skills/microsoft-foundry/foundry-agent/trace/references/tracing-insights-api.md — gen_ai attributes stored in `customDimensions` on `dependencies`; `invoke_agent`/`execute_tool` operation names; token extraction via `toint(customDimensions["gen_ai.usage.output_tokens"])`; operation_Id joins reconstruct traces.
- https://learn.microsoft.com/en-us/azure/azure-monitor/app/live-stream — Live Metrics behavior, default-on for ASP.NET Core.
- https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable — signal→table mapping (span kinds → requests/dependencies, ILogger → traces, metrics → customMetrics), correlation IDs. (Standard doc; mapping also reflected in tracing-insights-api reference above.)
- https://learn.microsoft.com/en-us/azure/azure-monitor/logs/daily-cap and https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs — workspace daily cap and pricing tiers (PAYG per-GB, commitment tiers, Basic table plan). Standard docs; tier names stable, verify current GB thresholds before committing.
- https://learn.microsoft.com/en-us/azure/azure-monitor/visualize/workbooks-overview and https://learn.microsoft.com/en-us/azure/managed-grafana/overview — Workbooks as ARM resources with Azure RBAC sharing; Managed Grafana Azure Monitor data source + Grafana-level RBAC. Standard docs supporting §5 tradeoffs.
- https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-overview — alert types (metric, log search, activity), action groups. Supports §7 building blocks.

**Confidence notes:** package versions, distro API surface, sampling behavior, Agents view, and Foundry status verified directly against pages dated May–July 2026. The pricing-tier and workbook-RBAC specifics cite standard Learn pages not re-fetched today — mechanisms are stable but re-verify exact commitment-tier price points before budgeting.
