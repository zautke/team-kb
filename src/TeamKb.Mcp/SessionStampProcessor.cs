using System.Diagnostics;
using OpenTelemetry;
using TeamKb.Core;

namespace TeamKb.Mcp;

// D1: every span carries session identity so per-step root traces group into
// one session in every UI (Aspire attribute filter, App Insights
// operation.name, Grafana variable). Values come from env — the MCP host is
// launched per agent session, so process env is the session scope.
public sealed class SessionStampProcessor : BaseProcessor<Activity>
{
    private readonly string? _sessionId = Environment.GetEnvironmentVariable("TEAMKB_SESSION_ID");
    private readonly string? _sessionName = Environment.GetEnvironmentVariable("TEAMKB_SESSION_NAME");

    public override void OnStart(Activity activity)
    {
        if (_sessionId is not null)
        {
            activity.SetTag(Telemetry.SessionId, _sessionId);
            activity.SetTag(Telemetry.ConversationId, _sessionId);
        }
        if (_sessionName is not null)
        {
            activity.SetTag(Telemetry.SessionName, _sessionName);
            // Root spans get the session name as DisplayName suffix source for
            // App Insights operation grouping (operation.name maps from the
            // root span name there).
            if (activity.Parent is null && activity.ParentId is null)
                activity.SetTag("operation.name", _sessionName);
        }
    }
}
