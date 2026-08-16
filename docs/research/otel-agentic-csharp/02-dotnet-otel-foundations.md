# OpenTelemetry .NET Foundations in C# — Instrumenting an Agentic AI System

**Audience:** engineers adding traces, metrics, and logs to a .NET agentic system (orchestrator, tool calls, LLM invocations).
**State of the world as of 2026-08-15:** OpenTelemetry .NET stable train is **1.17.0** (core SDK, OTLP exporter, Extensions.Hosting released 2026-07-16; AspNetCore/Http/Runtime instrumentation 2026-07-17).

## 1. The core insight: .NET's built-ins ARE the OTel API

Unlike other languages, .NET did not bolt OTel onto the runtime — the OTel tracing/metrics APIs were folded into the BCL (`System.Diagnostics` / `System.Diagnostics.Metrics`). You instrument with framework types; the OpenTelemetry SDK only *collects and exports*.

| OTel concept | .NET type | Package |
|---|---|---|
| Tracer | `ActivitySource` | System.Diagnostics.DiagnosticSource (in-box) |
| Span | `Activity` | in-box |
| Meter | `System.Diagnostics.Metrics.Meter` | in-box |
| Counter/Histogram/Gauge | `Counter<T>`, `Histogram<T>`, `ObservableGauge<T>`, `UpDownCounter<T>` | in-box |
| LogRecord | `ILogger` / `LoggerMessage` | Microsoft.Extensions.Logging |
| TracerProvider/MeterProvider | SDK-side providers | `OpenTelemetry` NuGet |

Consequence: **libraries need zero OTel dependencies.** Your agent-core library takes only in-box types; the host app decides what to listen to and where to ship it. An `ActivitySource` with no listener is a near-zero-cost no-op — `StartActivity` returns `null`.

## 2. Packages to reference (versions current 2026-08-15)

```xml
<!-- host/app project only -->
<PackageReference Include="OpenTelemetry" Version="1.17.0" />
<PackageReference Include="OpenTelemetry.Extensions.Hosting" Version="1.17.0" />
<PackageReference Include="OpenTelemetry.Exporter.OpenTelemetryProtocol" Version="1.17.0" />
<PackageReference Include="OpenTelemetry.Instrumentation.AspNetCore" Version="1.17.0" />
<PackageReference Include="OpenTelemetry.Instrumentation.Http" Version="1.17.0" />
<PackageReference Include="OpenTelemetry.Instrumentation.Runtime" Version="1.17.0" />
```

Targets: .NET 8+, .NET Standard 2.0, .NET Framework 4.6.2+. The 1.17 train adds .NET 10 targets. Instrumentation.AspNetCore/Http implement HTTP semantic conventions v1.23.

## 3. Tracing primitives — ActivitySource/Activity

```csharp
// Static, one per component. Name it like a namespace — it is your "tracer name".
internal static class AgentTelemetry
{
    public static readonly ActivitySource Source = new("MyCompany.Agent", "1.0.0");
    public static readonly Meter Meter = new("MyCompany.Agent", "1.0.0");
    public static readonly Counter<long> ToolCalls =
        Meter.CreateCounter<long>("agent.tool.calls", description: "Tool invocations");
    public static readonly Histogram<double> LlmLatency =
        Meter.CreateHistogram<double>("agent.llm.duration", unit: "s");
}

// In the agent loop:
using var act = AgentTelemetry.Source.StartActivity("agent.tool_call");
act?.SetTag("agent.tool.name", toolName);           // note the null-conditional — no listener => null
act?.SetTag("gen_ai.request.model", model);          // GenAI semantic conventions
try
{
    var result = await InvokeToolAsync(toolName, args, ct);
    act?.SetTag("agent.tool.result.size", result.Length);
}
catch (Exception ex)
{
    act?.SetStatus(ActivityStatusCode.Error, ex.Message);
    act?.AddException(ex);                            // AddException available on modern Activity
    throw;
}
```

Key behaviors:
- `StartActivity` automatically parents to `Activity.Current` (AsyncLocal), so nested tool calls form a tree across `await` boundaries with no plumbing. Context propagation across HTTP is W3C `traceparent` handled by the Http/AspNetCore instrumentation.
- `ActivityKind.Client` for LLM/tool HTTP calls you wrap yourself; `Internal` (default) for orchestration steps.
- Add events for cheap point-in-time markers: `act?.AddEvent(new ActivityEvent("retry", tags: ...))`.
- For agentic systems, prefer the GenAI semantic conventions attribute names (`gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`) so backends can aggregate them.

## 4. Metrics primitives — Meter/Instruments

```csharp
AgentTelemetry.ToolCalls.Add(1,
    new KeyValuePair<string, object?>("agent.tool.name", toolName),
    new KeyValuePair<string, object?>("outcome", ok ? "success" : "error"));

AgentTelemetry.LlmLatency.Record(sw.Elapsed.TotalSeconds,
    new KeyValuePair<string, object?>("gen_ai.request.model", model));

// Observable gauge for queue depth / active agents:
AgentTelemetry.Meter.CreateObservableGauge("agent.active_sessions", () => _sessions.Count);
```

The SDK aggregates in-process; the OTLP metric exporter pushes periodically (default 60 s, tune via `PeriodicExportingMetricReaderOptions` or `OTEL_METRIC_EXPORT_INTERVAL`).

## 5. Logging — ILogger maps to OTel LogRecords

Use `ILogger` exactly as usual; the OTel logging provider turns structured template values into LogRecord attributes and stamps TraceId/SpanId from `Activity.Current`, correlating logs to spans automatically.

```csharp
_logger.LogInformation("Tool {ToolName} finished in {ElapsedMs} ms", toolName, sw.ElapsedMilliseconds);
```

## 6. Host wiring — WithTracing / WithMetrics / WithLogging

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddOpenTelemetry()
    .ConfigureResource(r => r
        .AddService(serviceName: "agent-orchestrator",
                    serviceVersion: "1.0.0",
                    serviceInstanceId: Environment.MachineName)
        .AddAttributes(new Dictionary<string, object>
        {
            ["deployment.environment.name"] = builder.Environment.EnvironmentName
        }))
    .WithTracing(t => t
        .AddSource("MyCompany.Agent")            // subscribe to your ActivitySource(s)
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddOtlpExporter())                       // defaults: grpc, localhost:4317
    .WithMetrics(m => m
        .AddMeter("MyCompany.Agent")
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddRuntimeInstrumentation()
        .AddOtlpExporter())
    .WithLogging(l => l
        .AddOtlpExporter());                      // WithLogging is stable on OpenTelemetryBuilder

var app = builder.Build();
```

`AddOpenTelemetry()` registers an `IHostedService` that manages provider lifecycle (flush on shutdown). `WithLogging` on the builder replaces the older `builder.Logging.AddOpenTelemetry(...)` pattern; both work, prefer the unified builder.

## 7. OTLP exporter configuration — grpc vs http/protobuf

```csharp
.AddOtlpExporter(o =>
{
    o.Endpoint = new Uri("http://localhost:4317");            // grpc: base endpoint, no path
    o.Protocol = OtlpExportProtocol.Grpc;                      // default
    // -- or --
    // o.Endpoint = new Uri("http://localhost:4318/v1/traces"); // http/protobuf: signal path REQUIRED in code
    // o.Protocol = OtlpExportProtocol.HttpProtobuf;
    o.Headers = "x-otlp-api-key=...";                          // comma-separated k=v
})
```

Rules that bite people:
- **grpc** → port 4317, endpoint is the root. **http/protobuf** → port 4318; when set via *code*, you must append `/v1/traces`, `/v1/metrics`, `/v1/logs`; when set via *env var* `OTEL_EXPORTER_OTLP_ENDPOINT`, the SDK appends signal paths itself.
- Traces/logs use a `BatchExportProcessor` by default; metrics use periodic exporting. gzip compression and mTLS (on .NET 8+) are supported options on the 1.17 exporter.

## 8. Env-var configuration (OTEL_*)

The SDK honors the standard spec env vars — prefer these over code for anything environment-dependent:

```bash
OTEL_SERVICE_NAME=agent-orchestrator
OTEL_RESOURCE_ATTRIBUTES=deployment.environment.name=dev,team=agents
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc          # or http/protobuf
OTEL_EXPORTER_OTLP_HEADERS=x-otlp-api-key=secret
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.25
OTEL_METRIC_EXPORT_INTERVAL=15000         # ms
OTEL_BSP_SCHEDULE_DELAY=5000              # batch span processor flush delay, ms
```

Per-signal overrides exist (`OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`, etc.). Env vars are read at provider build time; code-set values win where both are present on the exporter options.

## 9. Sampling (head sampling)

Sampling decides at `StartActivity` time whether a span is recorded/exported. Built-in samplers:

```csharp
.WithTracing(t => t
    .SetSampler(new ParentBasedSampler(new TraceIdRatioBasedSampler(0.25)))
    // AlwaysOnSampler / AlwaysOffSampler for the poles
    ...)
```

- `ParentBasedSampler` — respects the incoming parent's sampled flag; the delegate sampler (here 25% ratio) applies only to root spans. This is the default composition you want in a distributed agent system so a trace is all-in or all-out.
- Custom head sampling: derive from `Sampler`, override `ShouldSample(in SamplingParameters)` and return `SamplingResult` — e.g., always sample activities tagged as LLM errors, ratio-sample chatter.
- Unsampled activities still exist (for context propagation) but `IsAllDataRequested == false`; guard expensive tag computation with `if (act is { IsAllDataRequested: true })`.

## 10. Custom processors

Processors sit between activity end and the exporter — use for enrichment, scrubbing (prompts often contain user data), or filtering:

```csharp
public sealed class PromptScrubProcessor : BaseProcessor<Activity>
{
    public override void OnEnd(Activity activity)
    {
        if (activity.GetTagItem("gen_ai.prompt") is string)
            activity.SetTag("gen_ai.prompt", "[REDACTED]");
    }
}

.WithTracing(t => t
    .AddProcessor(new PromptScrubProcessor())   // order matters: before the exporter's batch processor
    .AddOtlpExporter())
```

`BaseProcessor<LogRecord>` does the same for logs (e.g., drop records below a level per-category, redact PII). For tail-style decisions in-process, filter in `OnEnd` by setting `activity.ActivityTraceFlags &= ~ActivityTraceFlags.Recorded` — but real tail sampling belongs in an OTel Collector.

## 11. Minimal checklist for an agentic system

1. One `ActivitySource` + one `Meter` per logical component; names registered via `AddSource`/`AddMeter`.
2. Span per agent step / tool call / LLM call; GenAI semconv attributes; token counts as span tags **and** counters.
3. `ParentBased(TraceIdRatioBased)` in prod, `AlwaysOn` in dev.
4. OTLP → local Aspire dashboard in dev (see Doc B), Collector in prod.
5. Scrub prompts/completions in a processor before export.

## Sources

- https://www.nuget.org/packages/OpenTelemetry — accessed 2026-08-15 — core SDK latest stable 1.17.0 (2026-07-16), TFMs (.NET 8 / netstandard2.0 / .NET Fx 4.6.2).
- https://www.nuget.org/packages/OpenTelemetry.Exporter.OpenTelemetryProtocol — accessed 2026-08-15 — OTLP exporter 1.17.0 (2026-07-16); grpc + http/protobuf, gzip, mTLS (.NET 8+), batch processor for logs/traces, 60 s periodic metrics default.
- https://www.nuget.org/packages/OpenTelemetry.Extensions.Hosting — accessed 2026-08-15 — 1.17.0 (2026-07-16); AddOpenTelemetry/ConfigureResource/WithTracing/WithMetrics extension surface, IHostedService lifecycle.
- https://www.nuget.org/packages/OpenTelemetry.Instrumentation.AspNetCore — accessed 2026-08-15 — 1.17.0 (2026-07-17); HTTP semconv v1.23.
- https://www.nuget.org/packages/OpenTelemetry.Instrumentation.Http — accessed 2026-08-15 — 1.17.0 (2026-07-17); HttpClient/HttpWebRequest instrumentation, semconv v1.23.
- https://www.nuget.org/packages/OpenTelemetry.Instrumentation.Runtime — accessed 2026-08-15 — 1.17.0 (2026-07-17); GC/JIT/threading metrics, `AddRuntimeInstrumentation()`.
- https://github.com/open-telemetry/opentelemetry-dotnet/releases and https://opentelemetry.io/docs/languages/dotnet/ — accessed 2026-08-15 — release train confirmation, .NET 10 support in recent releases, ActivitySource/Meter-as-OTel-API mapping.

*Unverified-in-detail note: exact default values quoted for `OTEL_BSP_SCHEDULE_DELAY` and env-var precedence follow the OTel specification; confirm against spec docs if load-bearing.*
