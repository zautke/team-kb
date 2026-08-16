# Instrumenting C# Agentic Frameworks with OpenTelemetry (as of 2026-08-15)

Operational guide for wiring distributed tracing/metrics through the Microsoft agentic stack: Microsoft Agent Framework (MAF), Semantic Kernel (SK), Microsoft.Extensions.AI (M.E.AI), and the official MCP C# SDK. All claims cited in Sources.

## 0. TL;DR architecture

One trace, four layers. Instrumentation lives at each layer; W3C Trace Context glues them:

```
invoke_agent <name>            (MAF, ActivitySource: your sourceName or Experimental.Microsoft.Agents.AI)
 ├─ chat <model>               (M.E.AI OpenTelemetryChatClient, gen_ai semconv)
 ├─ execute_tool <fn>          (MAF/M.E.AI function invocation)
 │    └─ MCP tools/call        (ModelContextProtocol SDK, ActivitySource: Experimental.ModelContextProtocol)
 │         └─ server-side span (parent extracted from _meta traceparent per SEP-414)
```

Everything is gen_ai semconv-shaped (`gen_ai.operation.name`, `gen_ai.usage.input_tokens`, …). MAF docs explicitly state it emits traces/logs/metrics per the OpenTelemetry GenAI Semantic Conventions; note those conventions are still marked experimental upstream, hence `Experimental.*` source names.

## 1. Microsoft Agent Framework (MAF)

Packages (NuGet, current as of 2026-08-15):

- `Microsoft.Agents.AI` — **1.17.0** (stable line, updated 2026-08-04)
- `Microsoft.Agents.AI.OpenAI`, `Microsoft.Agents.AI.Declarative`, `Microsoft.Agents.AI.Workflows.Declarative` — companion packages
- `Microsoft.Agents.AI.Harness` — `HarnessAgent` (auto-instrumented agent wrapper, announced at Build 2026)

### Enabling telemetry

Two attach points — chat client and agent. Both are decorator-style, opt-in:

```csharp
const string SourceName = "MyApplication";

// 1. Instrument the chat client (M.E.AI layer)
IChatClient instrumentedChatClient = rawClient
    .AsIChatClient(deploymentName)
    .AsBuilder()
    .UseOpenTelemetry(sourceName: SourceName, configure: cfg => cfg.EnableSensitiveData = true)
    .Build();

// 2. Instrument the agent (MAF layer)
AIAgent agent = new ChatClientAgent(
        instrumentedChatClient,
        name: "OpenTelemetryDemoAgent",
        instructions: "You are a helpful assistant.",
        tools: [AIFunctionFactory.Create(GetWeatherAsync)])
    .WithOpenTelemetry(sourceName: SourceName, configure: cfg => cfg.EnableSensitiveData = true);
```

Then a standard OTel SDK pipeline listening on that source:

```csharp
using var tracerProvider = Sdk.CreateTracerProviderBuilder()
    .SetResourceBuilder(ResourceBuilder.CreateDefault().AddService("AgentOpenTelemetry"))
    .AddSource(SourceName)                       // MUST match sourceName above
    .AddOtlpExporter(o => o.Endpoint = new Uri("http://localhost:4317"))
    .Build();
```

Key facts:

- **Default ActivitySource name** when you omit `sourceName`: `Experimental.Microsoft.Agents.AI`. `AddSource` must match it exactly.
- **Duplication warning (official):** instrumenting both chat client and agent duplicates prompt/response content in both span layers when sensitive data is on. Pick one layer if that matters.
- **Sensitive data switch:** `cfg.EnableSensitiveData = true` (C#). Captures prompts, responses, function-call args, results. Docs: dev/test only.
- **HarnessAgent** (`Microsoft.Agents.AI.Harness`): both layers instrumented by default. `HarnessAgentOptions.OpenTelemetrySourceName` (default `Experimental.Microsoft.Agents.AI`), `DisableOpenTelemetry = true` to opt out. Environment switch `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` records prompts/responses/tool args — this is the semconv-standard env var, the newer surface superseding per-builder flags for Harness scenarios.

```csharp
AIAgent agent = chatClient.AsHarnessAgent(new HarnessAgentOptions
{
    OpenTelemetrySourceName = SourceName,   // AddSource must match
});
```

### What it emits

Spans (gen_ai semconv operation names):

| Span | When | Notable attributes |
|---|---|---|
| `invoke_agent <agent_name>` | top-level per agent run | `gen_ai.operation.name`, `gen_ai.system`, `gen_ai.agent.id/name`, `gen_ai.request.instructions`, `gen_ai.usage.input_tokens/output_tokens`, `gen_ai.response.id` |
| `chat <model_name>` | each LLM call | `gen_ai.request.model`, token usage, `gen_ai.response.finish_reasons`; prompt/response only if sensitive enabled |
| `execute_tool <function_name>` | each tool call | args/result only if sensitive enabled |

Metrics (histograms): `gen_ai.client.operation.duration` (s), `gen_ai.client.token.usage` (tokens), `agent_framework.function.invocation.duration` (s).

Logs ride the normal `Microsoft.Extensions.Logging` → `AddOpenTelemetry()` provider path.

### MCP trace propagation from MAF

Documented for Python today: with an active span, MAF injects `traceparent`/`tracestate` into `params._meta` on `tools/call` for **client-opened** MCP transports (stdio/streamable-HTTP/websocket); it can NOT propagate through hosted/provider-managed MCP connectors (Foundry/OpenAI/Anthropic hosted tools) because the provider runtime issues the `tools/call`. In .NET the equivalent propagation is done by the MCP C# SDK itself (section 4), so the same client-opened-vs-hosted caveat applies: hosted connectors break the trace at the provider boundary.

## 2. Semantic Kernel (still relevant for legacy code)

SK agents are in maintenance orbit (MAF is the successor; `Microsoft.SemanticKernel.Agents.OpenAI` sits at 1.78.0-preview), but the kernel's model-diagnostics layer is unchanged and still works:

- ActivitySources: per-connector `Microsoft.SemanticKernel.Connectors.*` (e.g. `.Connectors.OpenAI`) plus `Microsoft.SemanticKernel*` wildcard subscription pattern; subscribe with `AddSource("Microsoft.SemanticKernel*")`.
- **Non-sensitive switch:** `AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnostics", true)` — model name, operation name, token usage.
- **Sensitive switch:** `AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive", true)` — adds prompt + completion content as span events.
- Env-var equivalents: `SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS[_SENSITIVE]=true`.

```csharp
AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive", true);
using var tp = Sdk.CreateTracerProviderBuilder()
    .AddSource("Microsoft.SemanticKernel*")
    .AddOtlpExporter()
    .Build();
```

Migration note: new code should take the MAF/M.E.AI path (`UseOpenTelemetry`) instead of AppContext switches; SK increasingly delegates to M.E.AI `IChatClient` under the hood, where the M.E.AI instrumentation applies.

## 3. Microsoft.Extensions.AI (`IChatClient`) telemetry

Package line: `Microsoft.Extensions.AI` / `Microsoft.Extensions.AI.OpenAI` — **10.8.0** current stable (the 9.x-preview era is over; 10.x GA line since late 2025).

`UseOpenTelemetry()` inserts `OpenTelemetryChatClient` into the pipeline:

```csharp
IChatClient client = new OpenAI.Chat.ChatClient(model, apiKey)
    .AsIChatClient()
    .AsBuilder()
    .UseFunctionInvocation()     // order matters: put OTel outside function invocation
    .UseOpenTelemetry(sourceName: SourceName, configure: c => c.EnableSensitiveData = true)
    .Build();
```

Captures, per gen_ai semconv: `chat`-operation spans (`gen_ai.request.model`, provider, temperature/max_tokens request attrs, `gen_ai.response.*`, token usage), the two client metrics (`gen_ai.client.operation.duration`, `gen_ai.client.token.usage`), and — only with `EnableSensitiveData` — message content, tool args, tool results. This is the exact same instrumentation MAF reuses at its chat-client layer, which is why the MAF docs warn about layer duplication. There is a matching `UseOpenTelemetry()` on `EmbeddingGeneratorBuilder` for embeddings.

## 4. MCP C# SDK (`ModelContextProtocol`)

Package: `ModelContextProtocol` — stable **1.4.0**; **2.0.0-preview.1** (2026-06-26, targets MCP spec 2026-07-28 with fallback to 2025-11-25).

Yes — the official SDK is natively instrumented:

- **ActivitySource + Meter:** both named `Experimental.ModelContextProtocol`. Add `AddSource("Experimental.ModelContextProtocol")` / `AddMeter("Experimental.ModelContextProtocol")` — no other switch needed; instrumentation is built into the transport/request layer.
- **Context propagation:** the SDK propagates `traceparent`/`tracestate` on **all JSON-RPC messages** via `System.Diagnostics.DistributedContextPropagator` (so it honors whatever propagator your process configured — W3C default). Incoming requests get Activity creation with parent context extracted, so server-side spans parent correctly onto the caller's trace.
- **Spec grounding:** SEP-414 (spec 2026-07-28 line) reserves `_meta` keys `traceparent`, `tracestate`, `baggage`; values MUST be W3C Trace Context / W3C Baggage format. `_meta` (not HTTP headers) is the carrier because stdio has no headers and streamable-HTTP multiplexes many tool calls in one long-lived request — each `tools/call` gets its own parentage.

Practical pattern, both sides:

```csharp
// Client process (agent host)
using var tp = Sdk.CreateTracerProviderBuilder()
    .AddSource(SourceName)                              // MAF/M.E.AI spans
    .AddSource("Experimental.ModelContextProtocol")     // MCP client spans
    .AddOtlpExporter()
    .Build();

// Server process (MCP server) — same AddSource("Experimental.ModelContextProtocol");
// incoming tools/call spans parent onto the agent's execute_tool span automatically
// as long as both processes export to the same backend.
```

Version guidance: full SEP-414 `_meta` propagation is the 2.0 line; 1.4.0-era builds already carried the experimental ActivitySource, but pin `2.0.0-preview.1`+ for cross-process parentage guaranteed per spec. Verified via `System.Diagnostics.ActivityListener` if you want a unit-level check that spans actually fire.

## 5. Correlation patterns

- **Session/conversation id:** no stable `gen_ai.conversation.id` auto-attribute yet in the .NET stack — attach it yourself. Wrap each user turn in an app-level root span and tag it:

```csharp
using var activity = myActivitySource.StartActivity("agent_session_turn", ActivityKind.Client);
activity?.SetTag("gen_ai.conversation.id", threadId);   // semconv attribute name
activity?.SetTag("session.id", sessionId);
// run agent inside this scope — invoke_agent parents onto it, everything below inherits the trace
```

- **Multi-agent handoffs, in-process:** free — `Activity.Current` flows across async continuations; each agent's `invoke_agent` span nests in the same trace. Distinguish agents via `gen_ai.agent.id`/`gen_ai.agent.name` (emitted automatically).
- **Handoffs across processes/MCP:** carried by `_meta` traceparent (section 4). Across plain HTTP between agent services, standard `HttpClient` + ASP.NET Core OTel instrumentation carries it via headers.
- **Hosted-connector gap:** provider-managed MCP tools break trace continuity (section 1). If end-to-end tracing is a requirement, use client-opened MCP transports.
- **Baggage for cross-cutting ids:** SEP-414 also reserves `baggage` in `_meta`; put `conversation.id` in OTel Baggage and promote it to span attributes in a processor on the server side if you need the id on remote spans.
- **Dashboard:** Aspire Dashboard (`mcr.microsoft.com/dotnet/aspire-dashboard`, OTLP on 4317, UI on 18888) is the recommended local viewer; Azure Monitor exporters for production.

## 6. Gotchas checklist

1. `AddSource` string mismatch = silent zero spans. Defaults: `Experimental.Microsoft.Agents.AI` (MAF), `Experimental.ModelContextProtocol` (MCP).
2. Don't double-instrument chat client + agent + Harness unless duplicate content spans are intended.
3. Sensitive-data capture (any of the three switch families) is dev/test only — prompts land in your telemetry backend.
4. `Experimental.` prefixes signal the gen_ai semconv is not yet stable; source names/attributes may shift — pin package versions and re-check on upgrade.
5. Metrics need `AddMeter`/meter-provider wiring separately from traces.

## Sources (all accessed 2026-08-15)

- https://learn.microsoft.com/en-us/agent-framework/agents/observability — MAF `UseOpenTelemetry`/`WithOpenTelemetry`, default source `Experimental.Microsoft.Agents.AI`, span names (`invoke_agent`/`chat`/`execute_tool`), metric names, `EnableSensitiveData`, duplication warning, HarnessAgent options + `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`, MCP `_meta` propagation scope and hosted-connector limitation, Aspire guidance, gen_ai semconv compliance statement. (doc dated 2026-07-30, updated 2026-08-10)
- https://www.nuget.org/packages/Microsoft.Agents.AI/ — Microsoft.Agents.AI 1.17.0, updated 2026-08-04.
- https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce/ — Agent Harness announcement; MAF built-in OTel positioning.
- https://github.com/modelcontextprotocol/csharp-sdk/releases/tag/v2.0.0-preview.1 — ActivitySource/Meter `Experimental.ModelContextProtocol`, `DistributedContextPropagator` traceparent/tracestate on all JSON-RPC messages, parent extraction on incoming requests, 1.4.0 stable baseline, spec 2026-07-28 target.
- https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/ — SEP-414: `traceparent`/`tracestate`/`baggage` reserved in `_meta`, W3C formats, cross-SDK span-tree correlation.
- https://modelcontextprotocol.io/specification/draft/basic — `_meta` field specification.
- https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/observability/telemetry-with-app-insights — SK AppContext switches `...EnableOTelDiagnostics` / `...EnableOTelDiagnosticsSensitive` + env-var equivalents, `Microsoft.SemanticKernel*` source subscription.
- https://www.nuget.org/packages/Microsoft.Extensions.AI.OpenAI — 10.8.0 current, `UseOpenTelemetry(sourceName, c => c.EnableSensitiveData = true)` usage.
- https://www.nuget.org/packages/Microsoft.SemanticKernel.Agents.OpenAI — SK agents 1.78.0-preview (legacy line).
- https://opentelemetry.io/blog/2025/ai-agent-observability/ and https://opentelemetry.io/blog/2026/genai-observability/ — gen_ai semconv status and agent span taxonomy.

Unverified/inference flags: exact request-attribute list of `OpenTelemetryChatClient` (temperature/max_tokens) is from semconv + package docs pattern, not re-read from 10.8.0 source; `gen_ai.conversation.id` non-emission in .NET is inferred from MAF docs' attribute lists (only agent/session attributes shown) — verify against your backend before relying on it.
