# OTel Collector on Azure + Microsoft Purview for AI Governance — Implementation Guide

**Audience:** platform/agent engineers wiring agentic-AI telemetry on Azure. **Currency:** verified 2026-08-15. **Register:** instructional — follow steps in order; every normative claim is cited in Sources.

## 1. Collector distro and version

- Use **opentelemetry-collector-contrib**, not core. Current contrib release line at time of writing: **v0.158.0 (2026-08-04)**. Pin an explicit version tag in your image reference; never `latest`.
- Rationale: everything Azure-specific you need lives only in contrib — `azuremonitorexporter`, `azuredataexplorerexporter`, `redaction`, `transform`, `filter`, `tail_sampling`. Core ships only OTLP-family components.
- Better practice for production: build a **custom distro with `ocb` (OpenTelemetry Collector Builder)** containing exactly the components below. Smaller attack surface, smaller image, faster CVE triage.

## 2. Component set for AI telemetry

Declare these in the pipeline (order in `processors:` list is execution order):

```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:44317 }   # non-default port per org rule
      http: { endpoint: 0.0.0.0:44318 }

processors:
  memory_limiter: { check_interval: 1s, limit_percentage: 80, spike_limit_percentage: 20 }
  redaction:
    allow_all_keys: false
    allowed_keys: [gen_ai.system, gen_ai.request.model, gen_ai.usage.input_tokens,
                   gen_ai.usage.output_tokens, gen_ai.operation.name, session.id,
                   error.type, server.address]
    blocked_values: ["\\d{3}-\\d{2}-\\d{4}", "4[0-9]{12}(?:[0-9]{3})?"]  # SSN, PAN
  transform:
    trace_statements:
      - context: span
        statements:
          - truncate_all(attributes, 1024)
          - delete_key(attributes, "gen_ai.prompt") where attributes["gen_ai.prompt"] != nil
  filter:
    traces:
      span:
        - 'attributes["http.route"] == "/healthz"'
  attributes:
    actions:
      - key: deployment.environment.name
        value: prod
        action: upsert
  batch: {}

exporters:
  azuremonitor:
    connection_string: ${env:APPLICATIONINSIGHTS_CONNECTION_STRING}
```

Key semantics, verified against contrib READMEs:

- **redaction**: deletes attributes NOT in `allowed_keys` (allowlist model), then masks values matching `blocked_values` regexes; `allowed_keys` entries still get value-masked if they match `blocked_values` — but `allowed_values` (exact-value allowlist) takes precedence over `blocked_values`. Applies to spans, logs, metric datapoints.
- **transform** (OTTL): arbitrary mutation — truncation, key deletion, hashing. Use it to strip `gen_ai.prompt`/`gen_ai.completion` span attributes if any SDK leaks them.
- **filter**: drop whole spans/metrics/logs by OTTL condition (health checks, noisy tools).
- **tail_sampling**: see Doc B — placed on the gateway tier only.
- **azuremonitor exporter**: contrib-only; maps OTel spans to the Application Insights data model (requests/dependencies/traces/exceptions). Configure via `connection_string` or `APPLICATIONINSIGHTS_CONNECTION_STRING` env var; default auth is local (ikey from connection string); Entra ID (AAD) auth is documented in the exporter's AUTHENTICATION.md.

## 3. Deployment on Azure

### 3.1 Azure Container Apps (ACA)

Three viable shapes; pick one:

1. **Managed OpenTelemetry agent** on the ACA *environment* — Microsoft-operated, zero collector maintenance, OTLP endpoint env vars injected into apps. Least control: no custom processors (no redaction/tail-sampling). Fine for dev, insufficient for the governance pipeline in this doc.
2. **Sidecar collector container** in each Container App — ACA has no DaemonSet concept, so sidecar is the per-app agent pattern there. Mount config via ACA secret/volume; app exports OTLP to `localhost:44317`.
3. **Dedicated Container App as gateway** — one ACA app running contrib, min replicas ≥2, internal ingress, apps point OTLP at its FQDN. This is where redaction + tail sampling live.

Recommended: sidecar (light: batch + memory_limiter) → gateway (redaction, transform, tail_sampling, exporters). Config via env-substituted YAML (`${env:...}`) stored as ACA secret; scale gateway on CPU + concurrent-connection rules.

### 3.2 AKS

- **DaemonSet agent tier** (one collector per node, via the OpenTelemetry Operator or Helm chart, config in a ConfigMap) → **Deployment gateway tier** behind a ClusterIP Service. Two-tier agent→gateway is the standard production pattern: node-local capture + centralized policy point.
- Tail sampling constraint: all spans of a trace must hit the **same gateway replica**. Put a **loadbalancing exporter** (routing_key: traceID) in front of the tail-sampling tier, or run a single-replica sampling tier for low volume.
- Health: enable `health_check` extension (liveness/readiness probes) and `zpages` extension (`/debug/tracez`, `/debug/pipelinez`) for live pipeline inspection. Expose neither publicly.
- Scaling: HPA on CPU/memory; `memory_limiter` first in every processor chain so backpressure beats OOM.

## 4. Fan-out (one pipeline, three destinations)

```yaml
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, redaction, transform, filter, tail_sampling, batch]
      exporters: [azuremonitor, azuredataexplorer]
```

- **Azure Monitor / Application Insights** (`azuremonitor` exporter): live dashboards, alerts, workbooks, App Map.
- **Archive tier**: `azuredataexplorerexporter` (contrib, available since v0.62.0) writes traces/metrics/logs to ADX tables via managed/queued ingestion with Entra app auth — cheap long-retention analytical store for full-fidelity (pre-sampling tap, if desired, via a second pipeline) agent telemetry. `azureblob` exporter is the rawest/cheapest archival alternative.
- **Grafana**: do NOT export to Grafana; Grafana *queries* the stores — Azure Monitor datasource (App Insights/Log Analytics KQL) and Azure Data Explorer datasource. Azure Managed Grafana ships both with managed-identity auth.

## 5. Microsoft Purview for AI — what it is and is not

**What DSPM (Data Security Posture Management) for AI does today** (GA experience refreshed April–May 2026):

- Central console to discover and monitor AI usage: Microsoft 365 Copilot, Security Copilot, Copilot in Fabric, Copilot Studio agents, Microsoft Foundry apps, Entra-registered AI apps, and third-party consumer/enterprise AI (ChatGPT Enterprise, Claude Enterprise, Gemini, etc.).
- Captures **user prompts, AI responses, and interaction metadata** into the **Microsoft 365 unified audit log** via the Microsoft 365 audit pipeline (plus the Purview SDK/APIs and browser/network integrations for non-Microsoft apps), then layers DLP, sensitivity labels (EXTRACT usage rights gating what agents may read), Insider Risk analytics, oversharing risk assessments, eDiscovery, and Communication Compliance on top.
- Agent governance extends through Agent 365 registration and the AI Security Dashboard for end-to-end agent inventory and posture.

**What it is NOT — be precise here:**

- **Purview is not an OTLP sink.** It exposes no OTLP receiver endpoint and consumes no OpenTelemetry traces, metrics, or logs. Its ingestion paths are the M365 audit pipeline, the Purview APIs/SDK (for ISVs embedding governance signals), and connector/browser telemetry — not your collector. Verified: no OTLP/OpenTelemetry ingestion appears anywhere in the DSPM for AI configuration docs.
- It is a **governance/compliance plane** (who used which AI on which sensitive data; policy violations; audit trail; retention/eDiscovery), not an **observability plane** (latency, errors, token spend, traces). It answers auditors, not on-call engineers.

## 6. Wiring both — boundary and touchpoints

- **Two parallel planes, no pipe between them.** OTel collector → Azure Monitor/ADX/Grafana handles engineering observability. Purview observes AI interactions natively at the app layer (Copilot/Foundry/Entra-registered apps) via the audit pipeline. Do not attempt to forward OTel data into Purview or Purview audit into App Insights as a primary design.
- **Touchpoint 1 — correlation IDs:** stamp `session.id` / `gen_ai.conversation.id` and user AAD object ID (pseudonymized if policy requires) on spans so an incident found in Purview audit can be joined against traces in ADX/App Insights during investigation.
- **Touchpoint 2 — Foundry/Entra registration:** build custom agents on Microsoft Foundry or register them in Entra so Purview sees them without extra work; OTel instrumentation in the same agent code covers the observability side.
- **Touchpoint 3 — content stays out of OTel:** because Purview already captures prompts/responses for compliance, your OTel pipeline should carry *metadata only* (redaction allowlist above). One content store, governed; one metrics/trace store, clean. This split is your GDPR/DPIA story.
- **Touchpoint 4 — export for joint analysis:** unified audit log can be exported (Audit Search Graph API / Sentinel) into the same Log Analytics workspace family your App Insights uses, if analysts need one KQL surface — an analytics convenience, not a governance dependency.

## Sources

- https://github.com/open-telemetry/opentelemetry-collector-contrib/releases — accessed 2026-08-15 — contrib v0.158.0 (2026-08-04) current release.
- https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/redactionprocessor/README.md — accessed 2026-08-15 — allowlist semantics, blocked_values masking, precedence, spans/logs/metrics scope.
- https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/exporter/azuremonitorexporter (incl. README.md, AUTHENTICATION.md) — accessed 2026-08-15 — contrib-only availability, connection string / env var config, App Insights data-model mapping, auth modes.
- https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/exporter/azuredataexplorerexporter — accessed 2026-08-15 — ADX exporter config, since v0.62.0, ingestion types, Entra app auth.
- https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-configuration — accessed 2026-08-15 — APPLICATIONINSIGHTS_CONNECTION_STRING conventions.
- https://www.controltheory.com/resources/opentelemetry-collector-deployment-patterns-a-guide/ and https://www.elastic.co/observability-labs/blog/opentelemetry-collector-reference-architectures — accessed 2026-08-15 — sidecar-on-managed-platforms vs DaemonSet+gateway two-tier pattern.
- https://oneuptime.com/blog/post/2026-02-06-configure-opentelemetry-azure-container-apps/view and https://oneuptime.com/blog/post/2026-02-06-opentelemetry-azure-kubernetes-service-aks/view — accessed 2026-08-15 — ACA managed OTel agent vs sidecar trade-off; AKS agent→gateway pattern.
- https://learn.microsoft.com/en-us/purview/dspm-for-ai — accessed 2026-08-15 — DSPM for AI scope: Copilots, agents, third-party AI apps; supported app list.
- https://learn.microsoft.com/en-us/purview/dspm-for-ai-considerations and https://learn.microsoft.com/en-us/purview/developer/configurepurview — accessed 2026-08-15 — ingestion via M365 audit pipeline and Purview APIs; per-solution policy enablement; no OTLP ingestion path documented.
- https://techcommunity.microsoft.com/blog/microsoft-security-blog/securing-ai-agents-end%E2%80%91to%E2%80%91end-connecting-purview-dspm-agent-365-and-the-ai-secur/4521155 — accessed 2026-08-15 — DSPM + Agent 365 + AI Security Dashboard agent governance; 2026 GA rollout.
- https://learn.microsoft.com/en-us/fabric/data-science/data-agent-purview-governance — accessed 2026-08-15 — prompts/responses captured to unified audit log via M365 audit pipeline.
