using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using TeamKb.Core;
using TeamKb.Mcp;

// Config SSoT: vault root from env (TEAMKB_VAULT), no hardcoded paths.
var vaultRoot = Environment.GetEnvironmentVariable("TEAMKB_VAULT")
    ?? throw new InvalidOperationException("Set TEAMKB_VAULT to the vault root directory.");

var builder = Host.CreateApplicationBuilder(args);
// MCP stdio: stdout is the protocol channel — all logging must go to stderr.
builder.Logging.AddConsole(o => o.LogToStandardErrorThreshold = LogLevel.Trace);
builder.Services.AddSingleton(new VaultStore(vaultRoot));

// OTel Phase 0 (docs/research/otel-agentic-csharp/08): SDK lives in the host
// only. Exporter target comes from standard OTEL_EXPORTER_OTLP_ENDPOINT env
// (Aspire dashboard in dev, collector gateway in prod) — telemetry is a
// no-op when the env var is absent, so stdio MCP behavior is unchanged.
if (Environment.GetEnvironmentVariable("OTEL_EXPORTER_OTLP_ENDPOINT") is not null)
{
    builder.Services.AddOpenTelemetry()
        .ConfigureResource(r => r.AddService("teamkb-mcp"))
        .WithTracing(t => t
            .AddSource(Telemetry.SourceName)
            .AddSource("Experimental.ModelContextProtocol") // MCP C# SDK spans (SEP-414 traceparent via _meta)
            .AddProcessor(new SessionStampProcessor())
            .AddOtlpExporter())
        .WithMetrics(m => m
            .AddMeter(Telemetry.SourceName)
            .AddOtlpExporter());
}
builder.Services
    .AddMcpServer()
    .WithStdioServerTransport()
    .WithToolsFromAssembly();

await builder.Build().RunAsync();
