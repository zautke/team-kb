# Justification-meeting package

Materials for the technical justification of team-kb to a principal-engineer
audience. Everything here is evidence-backed and re-runnable.

| File | Role |
|---|---|
| [01-walkthrough.md](01-walkthrough.md) | The document to read/hand over: problem, architecture, evidence table, cost model, deferrals |
| [02-demo-runbook.md](02-demo-runbook.md) | Five live demos with pre-flight, expected output, timing, fallbacks |
| [03-observability-tasks.md](03-observability-tasks.md) | Remaining observability gaps as sized task specs (none block operation) |
| `demos/*.sh` | The demo scripts (self-contained, scratch vaults, idempotent) |
| `demos/transcripts/` | Captured live runs of every demo (fallback material) |
| `dashboard/kb-dashboard.html` | Single-file evidence dashboard generated from committed telemetry — open locally, no network |

Regenerate the dashboard: `demos/demo5-observability.sh`.
