# .NET Aspire Dashboard as the Local OTLP Dev Loop

**Audience:** engineers who want to *see* their OpenTelemetry data (from Doc A) within seconds of emitting it, with zero backend setup.
**State of the world as of 2026-08-15:** current Aspire release is **13.4.x** (13.4 shipped 2026-06-01; latest patch 13.4.6, 2026-06-20). The dashboard ships standalone as `mcr.microsoft.com/dotnet/aspire-dashboard`.

## 1. What it is

The Aspire dashboard is a self-contained web UI that ingests OTLP directly — no Collector, no database, no cloud account. Run it as a container, point any OTLP-emitting app at it, get traces + metrics + structured logs in the browser. It is the fastest local dev loop for validating instrumentation of an agentic system: emit a tool-call span, refresh, inspect the tree.

You do **not** need an Aspire project to use it. It is a generic OTLP sink.

## 2. Standalone container — the one command

```bash
docker run --rm -it -d \
  -p 18888:18888 \        # dashboard UI
  -p 4317:18889 \         # OTLP/gRPC   (container listens on 18889)
  -p 4318:18890 \         # OTLP/HTTP   (container listens on 18890)
  --name aspire-dashboard \
  mcr.microsoft.com/dotnet/aspire-dashboard:latest
```

(podman: same command, `podman run ...`.) Pin a version tag instead of `latest` for reproducible teams — tags track the Aspire release train (13.x current).

- UI: http://localhost:18888
- OTLP gRPC endpoint for your apps: `http://localhost:4317`
- OTLP HTTP/protobuf endpoint: `http://localhost:4318`

Note the port asymmetry: the container's internal OTLP ports are **18889/18890**; the standard host-side 4317/4318 mapping is a convention from the docs so apps can use default OTLP endpoints.

## 3. Browser auth token

By default the dashboard requires a login token. On startup it prints a link to the container logs:

```bash
docker logs aspire-dashboard
# ... Login to the dashboard at http://localhost:18888/login?t=<token>
```

Open that URL (or paste the token into the login page). New token each container start.

To skip auth for throwaway local use:

```bash
docker run ... -e ASPIRE_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS=true \
  mcr.microsoft.com/dotnet/aspire-dashboard:latest
```

This also leaves OTLP ingestion unauthenticated — anything that can reach the ports can read/write telemetry. Local-only; never expose on a shared network like that.

## 4. Wiring a non-Aspire app to the standalone dashboard

Nothing dashboard-specific: it is standard OTLP config (Doc A §7–8). Env vars:

```bash
OTEL_EXPORTER_OTLP_PROTOCOL=grpc                      # or http/protobuf
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317     # 4318 for http/protobuf
OTEL_SERVICE_NAME=agent-orchestrator
dotnet run
```

or in code:

```csharp
builder.Services.AddOpenTelemetry()
    .ConfigureResource(r => r.AddService("agent-orchestrator"))
    .WithTracing(t => t.AddSource("MyCompany.Agent")
                       .AddAspNetCoreInstrumentation()
                       .AddOtlpExporter())              // default grpc localhost:4317 — matches the container mapping
    .WithMetrics(m => m.AddMeter("MyCompany.Agent").AddOtlpExporter())
    .WithLogging(l => l.AddOtlpExporter());
```

Because the OTLP exporter's default is already `grpc` + `localhost:4317`, a bare `.AddOtlpExporter()` hits the standalone dashboard with zero config. `OTEL_SERVICE_NAME` controls how the app is labeled in the dashboard's resource dropdowns — set it, or everything shows as `unknown_service`.

Non-.NET emitters (Python agent sidecars, Node tools) work identically — the dashboard doesn't care what produced the OTLP.

## 5. ServiceDefaults pattern (inside Aspire projects)

When you *are* in an Aspire solution, the `dotnet new aspire` templates generate a **ServiceDefaults** project (`YourApp.ServiceDefaults`) referenced by every service. Its `Extensions.cs` exposes:

```csharp
public static TBuilder AddServiceDefaults<TBuilder>(this TBuilder builder)
    where TBuilder : IHostApplicationBuilder
{
    builder.ConfigureOpenTelemetry();   // WithTracing/WithMetrics + ASP.NET Core, HttpClient, runtime instr.
    builder.AddDefaultHealthChecks();
    builder.Services.AddServiceDiscovery();
    builder.Services.ConfigureHttpClientDefaults(http => http.AddStandardResilienceHandler()
                                                              .AddServiceDiscovery());
    return builder;
}
```

Each service calls `builder.AddServiceDefaults();` once. The OTLP exporter is enabled conditionally on `OTEL_EXPORTER_OTLP_ENDPOINT` being set — and the Aspire **AppHost** injects that env var (plus per-resource auth keys) into every orchestrated resource automatically, pointing at the AppHost-owned dashboard instance. That is the whole trick: in Aspire, telemetry wiring is ambient; standalone, you set the env vars yourself (§4).

To add your agent sources, edit ServiceDefaults once:

```csharp
.WithTracing(t => t.AddSource("MyCompany.Agent"))
.WithMetrics(m => m.AddMeter("MyCompany.Agent"))
```

Hybrid setup that works well: an Aspire AppHost for your services **plus** external tools/sidecars pointed at the same dashboard via env vars.

## 6. What the dashboard shows

- **Structured logs** — OTLP log records with attribute table, level/resource filtering, full-text search; trace-correlated (click through log → owning span) because the .NET logging provider stamps TraceId/SpanId.
- **Traces** — waterfall/tree view per trace, cross-service when multiple resources report; span attributes, events, exceptions, status. Your agent step → tool call → LLM call hierarchy renders as one tree.
- **Metrics** — instrument browser per meter, time-series graphs, dimension filtering (e.g., `agent.tool.calls` split by `agent.tool.name`). Recent versions render histograms with percentile views.
- **Live** — telemetry appears in near-real time as OTLP batches land (with Doc A defaults, spans within ~5 s, metrics on the export interval). In full Aspire mode you additionally get resource console logs and resource state; standalone mode shows only telemetry pages, since there is no orchestrator feeding resource info.

## 7. Limitations vs Azure Monitor / production backends

| Concern | Aspire dashboard | Azure Monitor (App Insights) / real backend |
|---|---|---|
| Persistence | **In-memory only** — gone on restart; ring-buffer limits evict oldest data | Durable storage, 30–90+ day retention |
| Scale | One process, single-node, capped telemetry counts | Ingestion pipelines, sampling at scale |
| Query | Filter/search UI only | Full query language (KQL), cross-signal joins |
| Alerting | None | Alerts, dashboards, SLOs, workbooks |
| Multi-user/RBAC | Token or anonymous, effectively single-user | AAD RBAC, audit |
| Cost | Free | Ingestion-billed |

The docs are explicit that it persists telemetry in memory and is a "development and short-term diagnostic tool." Correct mental model: **dashboard for the inner loop, OTel Collector → Azure Monitor (or other backend) for staging/prod.** Because everything is OTLP, promotion is a config change (endpoint/headers), not a code change — the same instrumentation from Doc A feeds both.

## 8. Version note

Aspire renumbered from 9.x to 13.x in late 2025 (aligning with the .NET train); current as of 2026-08-15 is **13.4.6** (2026-06-20 patch of the 13.4 release, 2026-06-01). 13.4 headline items: TypeScript apphost GA, typed resource commands, server-side CLI log/telemetry search, matured Kubernetes/AKS deploy. For the dashboard-as-OTLP-sink workflow nothing version-sensitive changed — image name, ports, and token flow are stable across 13.x.

## Sources

- https://aspire.dev/dashboard/standalone/ — accessed 2026-08-15 — docker run command, image `mcr.microsoft.com/dotnet/aspire-dashboard:latest`, ports 18888 (UI), 18889→4317 (OTLP/gRPC), 18890→4318 (OTLP/HTTP), login token in container logs, `ASPIRE_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS`, OTLP env-var wiring for external apps, in-memory persistence / short-term diagnostic tool limitation.
- https://learn.microsoft.com/dotnet/aspire/fundamentals/dashboard/standalone — accessed 2026-08-15 — same standalone guidance on Microsoft Learn (mirror of the above).
- https://github.com/microsoft/aspire/releases — accessed 2026-08-15 — latest release 13.4.6 (2026-06-20); 13.4.5 (2026-06-17), 13.4.4 (2026-06-15).
- https://devblogs.microsoft.com/aspire/whats-new-aspire-13-4/ — accessed 2026-08-15 — Aspire 13.4 release (2026-06-01) and headline features.
- https://anthonysimmon.com/dotnet-aspire-dashboard-best-tool-visualize-opentelemetry-local-dev/ — accessed 2026-08-15 — community walkthrough of dashboard as local OTLP visualizer for non-Aspire apps.
- https://www.nuget.org/packages/OpenTelemetry.Exporter.OpenTelemetryProtocol — accessed 2026-08-15 — exporter defaults (grpc, localhost:4317) that make bare `.AddOtlpExporter()` line up with the container mapping.

*Inference note: exact ServiceDefaults `Extensions.cs` contents shown are the well-known template shape (ConfigureOpenTelemetry + health checks + service discovery + resilience); verify against your generated template version — templates drift slightly between Aspire releases.*
