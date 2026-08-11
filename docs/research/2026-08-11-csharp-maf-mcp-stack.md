---
title: "R3 — C# MAF agents-as-MCP-tools (agent: research-maf)"
type: research
status: active
created: 2026-08-11
provenance:
  - source: "session:2026-08-11-teamkb-rebuild-research"
    author: "agent:research-maf"
tags: [research, rebuild, dossier-2026-08, dotnet, maf, mcp]
---

## 1. MAF status / version / abstractions

**GA'd 1.0 on 2026-04-03**; current stable **1.17.0** (2026-08-04, `dotnet-1.17.0` tag). Cadence ≈ weekly minor.

Stable (1.17.0): `Microsoft.Agents.AI`, `.Abstractions`, `.OpenAI`, `.Workflows`, `.Workflows.Declarative`, `.Workflows.Generators`, `.Workflows.Declarative.Mcp`.
Preview (1.17.0-preview.260804.1): `.Hosting`, `.Hosting.A2A[.AspNetCore]`, `.Hosting.AGUI.AspNetCore`, `.Foundry[.Hosting]`, `.Anthropic`, `.AzureAI.Persistent`, `.DevUI`. `.Declarative` is `1.17.0-rc1`; `.AzureAI` lags at `1.0.0-rc5`.

**TFMs** (from 1.17.0 nuspec): `net8.0`, `net9.0`, `net10.0`, `netstandard2.0`, `net472`. .NET 8+ recommended.

Abstractions: `AIAgent` (base) → `ChatClientAgent` (wraps any `IChatClient`; `ChatClientAgentOptions { ChatOptions, ChatHistoryProvider, AIContextProviders }`). Construction via `chatClient.AsAIAgent(...)` / `aiProjectClient.AsAIAgent(...)`. Run: `RunAsync` / `RunStreamingAsync`, sessions via `CreateSessionAsync()` → `AgentSession`.
Orchestrations: `SequentialOrchestration`, concurrent, group-chat, **handoff** (`HandoffBuilder`) all present. Graph workflows via `Microsoft.Agents.AI.Workflows` (`InProcessExecution.RunStreamingAsync`, executors, `SuperStepCompletedEvent`). DI/hosting: `builder.AddAIAgent("name", "instructions")`, `builder.AddSequentialWorkflow(...).AddAsAIAgent()`.

## 2. Agent → MCP tool (official pattern)

Two lines, first-party, documented on Learn and shipped as sample `dotnet/samples/02-agents/Agents/Agent_Step07_AsMcpTool`:

```csharp
McpServerTool tool = McpServerTool.Create(agent.AsAIFunction());
builder.Services.AddMcpServer().WithStdioServerTransport().WithTools([tool]);
```
`AsAIFunction()` (in `AgentExtensions.cs`) wraps `agent.RunAsync(query)` behind a single `query:string` param; agent `Name`/`Description` become MCP tool name/description. Optional `AgentSession` overload pins a session. Azure Functions variant: `samples/04-hosting/DurableAgents/AzureFunctions/07_AgentAsMcpTool` (Streamable HTTP at `/runtime/webhooks/mcp`).

**MCP C# SDK: `ModelContextProtocol` 2.1.0 (2026-08-05)**, Apache-2.0, 23M downloads. Packages: `.Core` (low-level), `ModelContextProtocol` (hosting/DI), `.AspNetCore` (Streamable HTTP), `.Extensions.Apps` (UI, experimental), `.Extensions.Tasks` (long-running, `IMcpTaskStore`). TFMs net8/9/10 + netstandard2.0.
API: `[McpServerToolType]` class + `[McpServerTool]` methods + `WithToolsFromAssembly()`, or imperative `WithTools([...])`. HTTP: `AddMcpServer().WithHttpTransport()` + `app.MapMcp()`.
**2.0 breaking changes (Aug 2026):** stateless HTTP is default (no `Mcp-Session-Id`); server-initiated elicitation/sampling replaced by **MRTR** — tools return `InputRequiredResult` with opaque `requestState`; `InputRequest.ForElicitation/ForSampling/ForRootsList`; legacy `ElicitAsync`/`SampleAsync` throw in stateless mode. Migration diagnostics `MCP9004`/`MCP9006`. Tasks extension not wire-compatible with 1.3.x/1.4.x. v2↔v1 handshake fallback preserved.

## 3. MAF consuming MCP tools (client)

Uses the same official SDK:
```csharp
await using var mcpClient = await McpClientFactory.CreateAsync(
    new StdioClientTransport(new(){ Name="MCPServer", Command="npx", Arguments=[...] }));
var mcpTools = await mcpClient.ListToolsAsync();
AIAgent agent = client.AsAIAgent(model, instructions: "...", tools: [.. mcpTools.Cast<AITool>()]);
```
MCP tools surface as `AIFunction`/`AITool` — no adapter needed. HTTP: `SseClientTransport`/streamable-HTTP transport. Sample: `dotnet/samples/02-agents/ModelContextProtocol/Agent_MCP_Server`.

## 4. Memory / state

- **Sessions**: `AgentSession` + `SerializeSessionAsync` / `DeserializeSessionAsync` (JsonElement → your store).
- **Workflow checkpointing**: `CheckpointManager.CreateInMemory()`, `run.Checkpoints`, `OnCheckpointRestoredAsync` + `context.ReadStateAsync<T>(key)`.
- **Memory = `AIContextProvider`** plugged into `ChatClientAgentOptions.AIContextProviders`. Released: `ChatHistoryMemoryProvider(vectorStore, collectionName, vectorDimensions, session => new State(storageScope, searchScope))` over `Microsoft.Extensions.VectorData` `VectorStore`. Preview: Mem0 (`Microsoft.Agents.AI.Mem0 1.0.0-preview.251028.1` — stale), Neo4j, Redis, Purview (`Microsoft.Agents.AI.Purview 1.17.0-rc1`). ⚠️ Unverified: could not confirm published NuGet IDs for the Redis/Neo4j providers — docs list them as Preview but NuGet search found no first-party package.
- History: `ChatHistoryProvider` (e.g. `InMemoryChatHistoryProvider`).

## 5. Exemplar repos (stars as of 2026-08-11)

| Repo | ★ | Pattern |
|---|---|---|
| microsoft/agent-framework | 12,729 | Canonical — `Agent_Step07_AsMcpTool`, `ModelContextProtocol/Agent_MCP_Server`, DevUI, A2A/AG-UI |
| modelcontextprotocol/csharp-sdk | 4,465 | SDK + stdio/HTTP server & client samples |
| microsoft/mcp | 3,555 | Official MS C# MCP servers (prod-grade auth/telemetry) |
| microsoft/kernel-memory | 2,174 | .NET RAG/ingestion pipeline, embeddings + vector DBs (⚠️ last push 2026-06, research project) |
| dotnet/ai-samples | 879 | `Microsoft.Extensions.AI` / VectorData / embedding + hybrid-search samples |
| Azure-Samples/azure-ai-travel-agents | 475 | Enterprise multi-agent-over-MCP on ACA, MAF |
| rwjdk/MicrosoftAgentFrameworkSamples | 310 | Broadest C#-only MAF sample set; pairs with AgentFrameworkToolkit (90★) |
| microsoft/mcp-dotnet-samples | 195 | C# MCP servers/clients, container + remote transports |
| clawdotnet/SharpClawCode | 79 | .NET 10 MAF coding-agent harness — sessions, tool permissions, MCP, plugins |

## 6. Embeddings against remote endpoints (no local weights)

`Microsoft.Extensions.AI` **10.8.3**; `Microsoft.Extensions.AI.OpenAI` **10.8.3**; `Microsoft.Extensions.VectorData.Abstractions` **10.8.2**.

Interface: `IEmbeddingGenerator<string, Embedding<float>>`. Two remote paths, both zero local download:

```csharp
// A. Any OpenAI-compatible endpoint (Ollama /v1, LM Studio, vLLM, tunnel)
var oa = new OpenAIClient(new ApiKeyCredential("ignored"),
    new OpenAIClientOptions { Endpoint = new Uri("https://ollama2.braisenly.com/v1") });
IEmbeddingGenerator<string, Embedding<float>> emb =
    oa.GetEmbeddingClient("embeddinggemma:cloud").AsIEmbeddingGenerator();

// B. Native Ollama API — OllamaSharp 5.4.30 implements IChatClient + IEmbeddingGenerator
var oll = new OllamaApiClient(new Uri("https://ollama2.braisenly.com"), "nomic-embed-text");
```
Feed either into `InMemoryVectorStoreOptions.EmbeddingGenerator` or a persistent store (`Microsoft.SemanticKernel.Connectors.SqliteVec 1.74.0-preview` for sqlite-vec; InMemory connector same version). Both stores speak `Microsoft.Extensions.VectorData`, so swapping is config-only.

## Sources

MAF 1.0 GA: https://techcommunity.microsoft.com/blog/azuredevcommunityblog/the-future-of-agentic-ai-inside-microsoft-agent-framework-1-0/4510698 · releases: https://github.com/microsoft/agent-framework/releases · NuGet MAF profile: https://www.nuget.org/profiles/MicrosoftAgentFramework · Learn (MCP tools + agent-as-MCP-server, updated 2026-08-10): https://learn.microsoft.com/en-us/agent-framework/agents/tools/local-mcp-tools · Learn workflow checkpoints: https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints · Learn ChatHistoryMemoryProvider: https://learn.microsoft.com/en-us/agent-framework/integrations/chat-history-memory-provider · ModelContextProtocol 2.1.0: https://www.nuget.org/packages/ModelContextProtocol · MCP C# SDK 2.0 migration: https://benjamin-abt.com/blog/2026/08/03/mcp-csharp-sdk-2/ · OllamaSharp: https://github.com/awaescher/OllamaSharp . All verified 2026-08-11.
