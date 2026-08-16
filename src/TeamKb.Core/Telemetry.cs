using System.Diagnostics;
using System.Diagnostics.Metrics;

namespace TeamKb.Core;

// gen_ai attribute names pinned to open-telemetry/semantic-conventions-genai
// commit a685613a207a580163353b8e48a7ad88967e7b42 (2026-08-15). The repo has
// no tagged release and everything is Development stability, so every
// attribute name lives in this one class — a semconv rename lands here only.
// Decisions D0-D4: docs/research/otel-agentic-csharp/08-zero-to-azure-roadmap.md
public static class Telemetry
{
    public const string SourceName = "TeamKb";

    // One ActivitySource + one Meter for the component (in-box types only —
    // the OTel SDK is referenced by the host, never by this library).
    public static readonly ActivitySource Source = new(SourceName);
    public static readonly Meter Meter = new(SourceName);

    // Session identity (D1: per-step root traces, grouped by session).
    public const string SessionId = "session.id";
    public const string SessionName = "session.name";
    public const string ConversationId = "gen_ai.conversation.id";

    // gen_ai semconv
    public const string OperationName = "gen_ai.operation.name";
    public const string ProviderName = "gen_ai.provider.name";
    public const string RequestModel = "gen_ai.request.model";
    public const string UsageInputTokens = "gen_ai.usage.input_tokens";
    public const string UsageOutputTokens = "gen_ai.usage.output_tokens";
    public const string ToolName = "gen_ai.tool.name";
    public const string ToolCallId = "gen_ai.tool.call.id";
    public const string ErrorType = "error.type";
}
