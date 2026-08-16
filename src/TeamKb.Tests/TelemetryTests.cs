using System.Diagnostics;
using TeamKb.Core;
using TeamKb.Mcp;
using Xunit;

namespace TeamKb.Tests;

public class TelemetryTests
{
    [Fact]
    public void SourceAndMeter_ShareComponentName()
    {
        Assert.Equal(Telemetry.SourceName, Telemetry.Source.Name);
        Assert.Equal(Telemetry.SourceName, Telemetry.Meter.Name);
    }

    [Fact]
    public void SessionStampProcessor_StampsSessionIdentityOnRootSpans()
    {
        Environment.SetEnvironmentVariable("TEAMKB_SESSION_ID", "s-123");
        Environment.SetEnvironmentVariable("TEAMKB_SESSION_NAME", "battery-run");
        try
        {
            var processor = new SessionStampProcessor();
            using var activity = new Activity("step").Start();
            processor.OnStart(activity);

            Assert.Equal("s-123", activity.GetTagItem(Telemetry.SessionId));
            Assert.Equal("s-123", activity.GetTagItem(Telemetry.ConversationId));
            Assert.Equal("battery-run", activity.GetTagItem(Telemetry.SessionName));
            Assert.Equal("battery-run", activity.GetTagItem("operation.name"));
        }
        finally
        {
            Environment.SetEnvironmentVariable("TEAMKB_SESSION_ID", null);
            Environment.SetEnvironmentVariable("TEAMKB_SESSION_NAME", null);
        }
    }

    [Fact]
    public void SessionStampProcessor_ChildSpans_GetIdentityButNotOperationName()
    {
        Environment.SetEnvironmentVariable("TEAMKB_SESSION_ID", "s-123");
        Environment.SetEnvironmentVariable("TEAMKB_SESSION_NAME", "battery-run");
        try
        {
            var processor = new SessionStampProcessor();
            using var root = new Activity("step").Start();
            using var child = new Activity("tool").Start(); // inherits root as parent
            processor.OnStart(child);

            Assert.Equal("s-123", child.GetTagItem(Telemetry.SessionId));
            Assert.Null(child.GetTagItem("operation.name"));
        }
        finally
        {
            Environment.SetEnvironmentVariable("TEAMKB_SESSION_ID", null);
            Environment.SetEnvironmentVariable("TEAMKB_SESSION_NAME", null);
        }
    }
}
