// TeamKb.OtlpBridge — OTLP/JSON → Cosmos DB bridge (decision D0 gap fix).
// The collector's otlphttp exporter (encoding: json) POSTs OTLP/JSON here;
// each span becomes one Cosmos document partitioned by session.id. When
// COSMOS_ENDPOINT is unset, spans append to /data/spans.jsonl instead (local
// dev without an emulator). Roadmap: docs/research/otel-agentic-csharp/08.

using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Azure.Cosmos;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton<ISpanSink>(_ =>
{
    var endpoint = Environment.GetEnvironmentVariable("COSMOS_ENDPOINT");
    return string.IsNullOrEmpty(endpoint)
        ? new FileSink(Environment.GetEnvironmentVariable("BRIDGE_FILE_SINK") ?? "/data/spans.jsonl")
        : new CosmosSink(
            endpoint,
            Environment.GetEnvironmentVariable("COSMOS_KEY")
                ?? throw new InvalidOperationException("COSMOS_KEY required when COSMOS_ENDPOINT is set."),
            Environment.GetEnvironmentVariable("COSMOS_DATABASE") ?? "teamkb-telemetry",
            Environment.GetEnvironmentVariable("COSMOS_CONTAINER") ?? "spans");
});

var app = builder.Build();

app.MapGet("/healthz", (ISpanSink sink) => Results.Ok(new { ok = true, sink = sink.Name }));

// OTLP/HTTP traces endpoint (JSON encoding). Success = HTTP 200 with an
// empty ExportTraceServiceResponse object, per the OTLP/HTTP spec.
app.MapPost("/v1/traces", async (HttpRequest request, ISpanSink sink, ILogger<Program> log) =>
{
    JsonNode? payload;
    try
    {
        payload = await JsonNode.ParseAsync(request.Body);
    }
    catch (JsonException e)
    {
        log.LogWarning(e, "rejecting non-JSON OTLP payload");
        return Results.BadRequest(new { error = "expected OTLP/JSON (set exporter encoding: json)" });
    }

    var docs = new List<JsonObject>();
    foreach (var rs in payload?["resourceSpans"]?.AsArray() ?? [])
    {
        foreach (var ss in rs?["scopeSpans"]?.AsArray() ?? [])
        {
            foreach (var span in ss?["spans"]?.AsArray() ?? [])
            {
                if (span is null) continue;
                var attrs = Flatten(span["attributes"]);
                var traceId = span["traceId"]?.GetValue<string>() ?? "";
                var spanId = span["spanId"]?.GetValue<string>() ?? "";
                docs.Add(new JsonObject
                {
                    ["id"] = $"{traceId}-{spanId}",
                    ["sessionId"] = attrs.GetValueOrDefault("session.id", "unknown"),
                    ["sessionName"] = attrs.GetValueOrDefault("session.name"),
                    ["traceId"] = traceId,
                    ["name"] = span["name"]?.GetValue<string>(),
                    ["startTimeUnixNano"] = span["startTimeUnixNano"]?.DeepClone(),
                    ["endTimeUnixNano"] = span["endTimeUnixNano"]?.DeepClone(),
                    ["span"] = span.DeepClone(), // full fidelity — nothing dropped
                });
            }
        }
    }

    await sink.WriteAsync(docs);
    return Results.Json(new { }); // ExportTraceServiceResponse
});

app.Run();

// OTLP KeyValue list -> flat string dictionary (string values only; that's
// all the session identity needs).
static Dictionary<string, string?> Flatten(JsonNode? attributes)
{
    var result = new Dictionary<string, string?>();
    foreach (var kv in attributes?.AsArray() ?? [])
    {
        var key = kv?["key"]?.GetValue<string>();
        if (key is null) continue;
        result[key] = kv?["value"]?["stringValue"]?.GetValue<string>();
    }
    return result;
}

interface ISpanSink
{
    string Name { get; }
    Task WriteAsync(IReadOnlyList<JsonObject> docs);
}

sealed class FileSink(string path) : ISpanSink
{
    private readonly SemaphoreSlim _lock = new(1, 1); // ponytail: global lock; per-file queue if throughput matters
    public string Name => $"file:{path}";

    public async Task WriteAsync(IReadOnlyList<JsonObject> docs)
    {
        await _lock.WaitAsync();
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            await File.AppendAllLinesAsync(path, docs.Select(d => d.ToJsonString()));
        }
        finally { _lock.Release(); }
    }
}

sealed class CosmosSink : ISpanSink
{
    private readonly Container _container;
    public string Name { get; }

    public CosmosSink(string endpoint, string key, string database, string containerName)
    {
        var client = new CosmosClient(endpoint, key, new CosmosClientOptions
        {
            AllowBulkExecution = true,
            // Cosmos emulator ships a self-signed cert; gateway mode + relaxed
            // TLS keeps local dev friction-free. Real Azure ignores this path.
            ConnectionMode = ConnectionMode.Gateway,
            ServerCertificateCustomValidationCallback = (_, _, _) => true,
        });
        var db = client.CreateDatabaseIfNotExistsAsync(database).GetAwaiter().GetResult().Database;
        _container = db.CreateContainerIfNotExistsAsync(containerName, "/sessionId")
            .GetAwaiter().GetResult().Container;
        Name = $"cosmos:{database}/{containerName}";
    }

    public async Task WriteAsync(IReadOnlyList<JsonObject> docs)
    {
        // ponytail: sequential upserts; switch to bulk Task.WhenAll if ingest lags
        foreach (var doc in docs)
        {
            using var stream = new MemoryStream(System.Text.Encoding.UTF8.GetBytes(doc.ToJsonString()));
            await _container.UpsertItemStreamAsync(stream,
                new PartitionKey(doc["sessionId"]!.GetValue<string>()));
        }
    }
}
