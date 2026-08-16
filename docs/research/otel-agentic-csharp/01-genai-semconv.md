# OpenTelemetry GenAI Semantic Conventions — Field Guide for C#/.NET Agentic Teams

**Current as of 2026-08-15.** Verified against live repo files on that date.

## 1. Where the spec lives now — critical

The GenAI conventions **moved out of `open-telemetry/semantic-conventions`** into a dedicated repo: **`open-telemetry/semantic-conventions-genai`**. Core-repo release **v1.42.0 (2026-06-12)** deprecated all `gen_ai.*` definitions under `model/gen-ai/`, `model/openai/`, `model/mcp/` in the core repo; the old doc pages are now redirect stubs.

- Core repo latest release: **v1.44.0 (2026-08-04)** — contains NO maintained gen_ai content.
- GenAI repo: **no tagged release yet** (zero tags as of 2026-08-15); pin by commit SHA. Schema URL marked "TODO". Docs generated via Weaver from `model/` YAML; depends on core semconv v1.44.0.
- Docs layout: `docs/gen-ai/{gen-ai-spans.md, gen-ai-agent-spans.md, gen-ai-metrics.md, gen-ai-events.md, gen-ai-exceptions.md, mcp.md, anthropic.md, openai.md, aws-bedrock.md, azure-ai-inference.md}`.

**Stability: every GenAI-specific attribute, span, metric, and event is `Development` (experimental). Nothing gen_ai.* is Stable.** Only borrowed core attributes (`error.type`, `server.address`, `server.port`) are Stable. Expect breaking renames; version-pin your attribute constants in one shared C# class.

## 2. Span conventions (`docs/gen-ai/gen-ai-spans.md`)

Span types: inference, embeddings, execute tool, retrieval, fetch response, memory (create/search/update/upsert/delete memory + memory store ops are newer additions).

| Span type | Name | Kind |
|---|---|---|
| Inference | `{gen_ai.operation.name} {gen_ai.request.model}` (e.g. `chat gpt-4o`) | `CLIENT` (MAY be `INTERNAL` if in-process model) |
| Embeddings | `{gen_ai.operation.name} {gen_ai.request.model}` | `CLIENT` |
| Execute tool | `execute_tool {gen_ai.tool.name}` | `INTERNAL` |
| Retrieval | `{gen_ai.operation.name} {gen_ai.data_source.id}` | `CLIENT` |
| Fetch response | `{gen_ai.operation.name}` (no response id — cardinality) | `CLIENT` |
| Memory ops | `{gen_ai.operation.name}` | `CLIENT`/`INTERNAL` |

### Core attributes (inference span)

| Attribute | Level | Stability |
|---|---|---|
| `gen_ai.operation.name` | Required | Development |
| `gen_ai.provider.name` | Required | Development |
| `error.type` | Cond. Required (on error) | **Stable** |
| `gen_ai.request.model` | Cond. Required (if available) | Development |
| `gen_ai.conversation.id` | Cond. Required (if readily available) | Development |
| `gen_ai.output.type`, `gen_ai.request.choice.count` (!=1), `gen_ai.request.seed`, `gen_ai.request.stream`, `gen_ai.request.top_k`, `server.port` | Cond. Required | Dev (server.* Stable) |
| `gen_ai.response.model`, `gen_ai.response.id`, `gen_ai.response.finish_reasons`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.request.temperature`, `.top_p`, `.max_tokens`, `.frequency_penalty`, `.presence_penalty`, `server.address` | Recommended | Dev |
| `gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.system_instructions`, `gen_ai.tool.definitions` | **Opt-In** | Dev |

- `gen_ai.operation.name` well-known values: `chat`, `generate_content`, `text_completion`, `embeddings`, `execute_tool`, `create_agent`, `invoke_agent`, `invoke_workflow`, `plan`, `retrieval`, `fetch_response`, `create_memory`, `create_memory_store`, `delete_memory`, `delete_memory_store`, `search_memory`, `update_memory`, `upsert_memory`.
- `gen_ai.provider.name` well-known values: `anthropic`, `openai`, `aws.bedrock`, `azure.ai.inference`, `azure.ai.openai`, `gcp.gemini`, `gcp.vertex_ai`, `gcp.gen_ai`, `cohere`, `deepseek`, `groq`, `ibm.watsonx.ai`, `mistral_ai`, `moonshot_ai`, `perplexity`, `x_ai`.
- Set at **span creation** (sampling-relevant): `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`, `server.address`, `server.port` (agents: also `gen_ai.agent.name`).
- Note the rename history your dashboards may still carry: `gen_ai.system` → `gen_ai.provider.name`; prompt/completion events → `gen_ai.input.messages`/`gen_ai.output.messages` attributes.

### Execute tool span (verbatim from spec, 2026-08-15)

Kind `INTERNAL`, name `execute_tool {gen_ai.tool.name}`. Instrument app-code tool calls manually if no auto-instrumentation covers them; MCP tool calls may instead be traced by MCP conventions (`docs/gen-ai/mcp.md`).

| Attribute | Level |
|---|---|
| `gen_ai.operation.name` (= `execute_tool`) | Required |
| `gen_ai.tool.name` | Required |
| `error.type` | Cond. Required (on error) |
| `gen_ai.agent.name` | Cond. Required (when applicable) |
| `gen_ai.tool.call.id` | Recommended (if available) |
| `gen_ai.tool.description`, `gen_ai.tool.type` (`function`/`extension`/`datastore`) | Recommended |
| `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result` | **Opt-In** (sensitive; must follow repo JSON schemas; structured form preferred, JSON string allowed on spans) |

## 3. Agent spans (`docs/gen-ai/gen-ai-agent-spans.md`) — all Development

| Span | Kind | Name | Notes |
|---|---|---|---|
| `create_agent` | CLIENT | `create_agent {gen_ai.agent.name}` | Remote agent services. Required: `gen_ai.operation.name`, `gen_ai.provider.name`. Cond: `gen_ai.agent.id/.name/.version/.description` |
| `invoke_agent` (client) | CLIENT | `invoke_agent {gen_ai.agent.name}` | Remote agents (OpenAI Assistants, Bedrock Agents). Same required set; plus token usage / request params Recommended |
| `invoke_agent` (internal) | INTERNAL | `invoke_agent {gen_ai.agent.name}` | In-process frameworks (LangChain, CrewAI, SK, Agent Framework). `gen_ai.provider.name` NOT required |
| `invoke_workflow` | INTERNAL | `invoke_workflow {gen_ai.workflow.name}` | Multi-agent orchestration (LangGraph, Crews, ADK Runners). `gen_ai.workflow.name` must be low-cardinality |
| `plan` | INTERNAL | `plan {gen_ai.agent.name}` | Decision phase; the LLM call generating the plan SHOULD be a child of the plan span |

**Multi-step trace shape:** `invoke_workflow` → nested `invoke_agent` (internal) → children: `plan` spans (each parenting its inference span), inference (`chat`) spans, and sibling `execute_tool` spans. Cross-invocation correlation via `gen_ai.conversation.id`.

## 4. Metrics (`docs/gen-ai/gen-ai-metrics.md`) — all Histograms, all Development

| Metric | Unit | Key attrs (Required) |
|---|---|---|
| `gen_ai.client.token.usage` | `{token}` | `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.token.type` (`input`/`output`). Buckets 1…67108864 (powers of 4) |
| `gen_ai.client.operation.duration` | `s` | `gen_ai.operation.name`; `error.type` cond. Buckets 0.01…81.92 (×2) |
| `gen_ai.client.operation.time_to_first_chunk` | `s` | streaming only |
| `gen_ai.client.operation.time_per_output_chunk` | `s` | streaming only |
| `gen_ai.server.request.duration` / `gen_ai.server.time_to_first_token` / `gen_ai.server.time_per_output_token` | `s` | model-server side (self-hosted) |
| `gen_ai.invoke_workflow.duration` | `s` | buckets 1…7200; `gen_ai.workflow.name` cond |
| `gen_ai.invoke_agent.duration` | `s` | buckets 0.1…409.6; `gen_ai.agent.name` cond |
| `gen_ai.invoke_agent.inference_calls` | `{inference_call}` | per-invocation count histogram, buckets 1…128 |
| `gen_ai.invoke_agent.tool_calls` | `{tool_call}` | buckets 1…128 |
| `gen_ai.execute_tool.duration` | `s` | `gen_ai.tool.name` Required |

.NET: register explicit bucket boundaries via `MeterProviderBuilder.AddView` — SDK defaults are wrong for token counts and durations at these scales.

## 5. Events vs attributes; content capture

Direction reversed from the 2024-era design: per-message log events (`gen_ai.user.message` etc.) are gone. Content now rides as **Opt-In structured attributes** (`gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.system_instructions`) on spans and/or on one consolidated event:

- Events defined (`gen-ai-events.md`, Development): **`gen_ai.client.inference.operation.details`** (full request/response detail, for when span attributes are insufficient or spans are sampled out) and **`gen_ai.evaluation.result`**.
- On events, content MUST be structured; on spans, structured preferred, JSON string allowed. Message bodies follow JSON schemas in `model/gen-ai/*.json` (role + parts array: text/tool_call/tool_call_response; per-choice `finish_reason`).
- Opt-in mechanics: instrumentations SHOULD NOT capture by default; gate on explicit opt-in — spec cites `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` as the example env var. .NET equivalents: `Microsoft.Extensions.AI` `OpenTelemetryChatClient.EnableSensitiveData = true`; Microsoft Agent Framework `UseOpenTelemetry(...)` wrapper honors the same switch. Keep OFF in production unless you have a data-handling story.

## 6. .NET specifics

- `Microsoft.Extensions.AI` (`UseOpenTelemetry()` on `IChatClient`) and Microsoft Agent Framework (`AsBuilder().UseOpenTelemetry(sourceName)`) emit gen_ai spans/metrics, tracking these conventions at some lag — verify emitted attribute names against the pinned spec commit; frameworks in the wild emit **multiple generations** of the schema simultaneously (`gen_ai.system` vs `gen_ai.provider.name` is the common skew).
- Semantic Kernel telemetry also emits gen_ai spans; docs/sample coverage is an open ask (microsoft/semantic-kernel#13237).

## 7. Known gaps / things to track

- **No release/tag, no schema_url** in `semantic-conventions-genai` → no formal versioned target to declare conformance against. Pin a commit SHA.
- Everything Development → renames still land (recent: memory-operation spans, `fetch_response`, stream-cursor resume, tool.definitions).
- Agentic gaps: no convention yet for handoffs/delegation between agents, guardrail/eval spans (only `gen_ai.evaluation.result` event), reasoning/thinking token accounting, or cross-process agent-to-agent (A2A) propagation. Umbrella discussion: [issue #35 — Semantic Conventions for GenAI Agentic Systems](https://github.com/open-telemetry/semantic-conventions-genai/issues/35); repo has ~135 open issues — watch labels on that repo, not the core repo.
- MCP conventions (`docs/gen-ai/mcp.md`) live in the same repo; MCP client instrumentation may own tool-call spans instead of `execute_tool` — pick one to avoid double-spanning.

## Sources (all accessed 2026-08-15)

- https://github.com/open-telemetry/semantic-conventions-genai — repo existence, structure, Weaver, schema TODO, ~135 open issues, no tags (verified via `gh api .../tags` — empty).
- https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/gen-ai-spans.md — span names/kinds, attribute tables, operation/provider enums, opt-in content attributes, execute_tool section (lines 1059+ read verbatim).
- https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/gen-ai-agent-spans.md — agent/workflow/plan spans, trace shape.
- https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/gen-ai-metrics.md — all 12 metrics, units, buckets.
- https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/gen-ai-events.md — two events, structured-content rules.
- https://github.com/open-telemetry/semantic-conventions/releases + `gh api .../releases` — core v1.44.0 (2026-08-04); v1.42.0 (2026-06-12) gen_ai deprecation/migration note.
- https://github.com/open-telemetry/semantic-conventions-genai/issues/35 — agentic-systems umbrella issue.
- https://john-hodge.com/blog/opentelemetry-genai-semantic-conventions/ and https://zylos.ai/research/2026-02-28-opentelemetry-ai-agent-observability/ — ecosystem schema-skew observations (secondary).
- https://learn.microsoft.com/en-us/azure/app-service/tutorial-ai-agent-monitoring-dotnet, https://jesseliberty.com/2026/07/31/opentelemetry-in-microsoft-agent-framework-apps/, https://github.com/microsoft/semantic-kernel/issues/13237 — .NET/Agent Framework instrumentation + `EnableSensitiveData` / `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`.
