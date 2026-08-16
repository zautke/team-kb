# Production Hardening for Agentic-AI Telemetry

**Audience:** teams taking an agent-telemetry pipeline from demo to production on Azure. **Currency:** verified 2026-08-15. Pairs with Doc A's pipeline; section numbers assume that architecture (SDK → sidecar/agent collector → gateway collector → App Insights + ADX + Grafana).

## 1. PII and prompt-content redaction — defense in depth

**Layer 0 — SDK-side (preferred kill switch).** OTel GenAI semantic conventions do **not** capture prompt/completion content by default; capture is opt-in via `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` (`true` legacy; `span_only` / `event_only` / `span_and_event` under `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`). Production rule: leave it **unset** (off). What is never emitted never needs redacting, never hits a subpoena, never leaks via an exporter misconfig.

**Layer 1 — collector-side (backstop, not primary).**
- `redaction` processor with `allow_all_keys: false` and an explicit `allowed_keys` allowlist — this is structurally superior to blocklisting because unknown attributes (a new instrumentation library, a developer's debug attribute) are dropped by default. Add `blocked_values` regexes (SSN, PAN, email) to mask values inside allowed keys; remember `allowed_values` exact-matches override `blocked_values`.
- `transform` (OTTL) for what redaction can't express: `truncate_all(attributes, N)`, `delete_key` on `gen_ai.prompt`/`gen_ai.completion`, `SHA256(...)` hashing of user identifiers when you need joinability without identity.
- Run redaction at BOTH tiers if sidecars exist: sidecar redaction limits blast radius of a compromised/verbose app; gateway redaction is the org-wide guarantee.

**Regulatory framing.** Prompts are user-generated content: presume GDPR personal data (and possibly special-category), HIPAA PHI in healthcare, and EU AI Act logging-vs-privacy tension. The defensible posture: content capture off at SDK (data minimization, GDPR Art. 5(1)(c)); collector allowlist as documented technical measure (Art. 32); compliance-grade content capture delegated to Purview's governed audit store (Doc A §6) where retention, eDiscovery, and access review exist. Write this split into your DPIA.

## 2. Cost and cardinality control

- **Attribute allowlist = cardinality control.** The same `redaction.allowed_keys` doubles as your cardinality budget. Never allow raw `user.id`, full URLs, UUIDs, or timestamps into **metric** attributes; keep those on spans only.
- **Never put unbounded values in metric dimensions.** `session.id` on a metric = one time series per session = cardinality explosion in both App Insights custom metrics and any Prometheus-compatible store. Aggregate metrics over `model`, `operation`, `agent.name`, `environment` only (each ≤ ~50 values). Use the transform processor to `delete_key` high-cardinality datapoint attributes in the metrics pipeline.
- **Sampling economics, head vs tail.** Head sampling (probabilistic, at SDK or first collector) is cheap — decision at trace start, no buffering — but blind: it discards the 1-in-1000 failed agent run you needed. Tail sampling buffers complete traces and decides on real characteristics (error, latency, token spend), at the price of gateway memory (`decision_wait` × span rate) and trace-affinity routing. For long multi-step agent sessions, head sampling is actively dangerous (it decides before the interesting part happens); use tail sampling at the gateway, optionally with a coarse head-sample (e.g., 50%) in front only under extreme volume — accepting it uniformly thins everything including errors.
- **App Insights ingestion levers**, in order of preference per Microsoft's own guidance: (1) reduce at source — the collector filtering/sampling above; sampling is the primary volume-tuning mechanism; (2) **workspace-based** resource so you can use commitment tiers and table-level retention/Basic Logs; (3) **commitment tiers** at sustained ≥100 GB/day (up to ~30% off pay-as-you-go); (4) **ingestion sampling** at the service edge if collector sampling isn't enough; (5) **daily cap** (App Insights and workspace — the lower wins) strictly as a last-resort circuit breaker: hitting it blackouts telemetry until midnight UTC.
- Route bulk/audit-grade data to **ADX or blob** (cents/GB) and keep App Insights for the curated, sampled, alert-driving subset. This is the single biggest cost lever in the whole design.

## 3. Tail sampling for multi-step agent sessions

```yaml
processors:
  tail_sampling:
    decision_wait: 120s          # agent sessions run long; cover p99 trace duration
    num_traces: 200000
    policies:
      - name: errors-always
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: slow-steps
        type: latency
        latency: { threshold_ms: 15000 }
      - name: big-token-spend
        type: numeric_attribute
        numeric_attribute: { key: gen_ai.usage.output_tokens, min_value: 8000 }
      - name: flagged-sessions
        type: string_attribute
        string_attribute: { key: session.flagged, values: ["true"] }
      - name: baseline
        type: probabilistic
        probabilistic: { sampling_percentage: 5 }
```

- Policies are OR-composed: a trace kept by ANY policy is kept whole. Order error/latency checks before probabilistic. `latency` measures earliest-start → latest-end across the trace; `status_code` keys on OK/ERROR/UNSET; `numeric_attribute`/`string_attribute` give you token-spend and flag policies. `and`/`composite` policy types exist for rate-budgeted combinations.
- **Session-coherent, all-or-nothing:** tail sampling is inherently all-or-nothing **per trace ID**. Decide your unit: (a) one trace per agent *session* (steps as spans/child spans) — sampling coherence free, but `decision_wait` must exceed session length; or (b) trace per step with shared `session.id` attribute — then achieve session coherence by routing on `session.id` (loadbalancing exporter `routing_key: attribute`) and sampling via a deterministic hash of `session.id` (OTTL condition), so every trace of a session gets the same verdict. Never let half a session survive sampling — partial agent sessions are worse than none for debugging and for token-spend accounting.
- Capacity: memory ≈ spans/sec × decision_wait × bytes/span. Size `num_traces`, watch `otelcol_processor_tail_sampling_*` self-metrics, and alert on `sampling_trace_dropped_too_early`.

## 4. RBAC on telemetry and dashboards

- **Workspace RBAC:** workspace-based App Insights inherits Azure RBAC on the Log Analytics workspace. Use built-ins: `Monitoring Reader` (read-only), `Monitoring Contributor`, `Log Analytics Reader/Contributor`. For mixed-sensitivity workspaces use **resource-context access** or **table-level RBAC** so, e.g., only the AI-platform team reads the `dependencies`/custom GenAI tables.
- **Workbooks:** are ARM resources — sharing is Azure RBAC (`Workbook Reader`/`Workbook Contributor`) on their resource group; a workbook viewer still needs read on the underlying workspace, so scope both deliberately.
- **Grafana:** Azure Managed Grafana maps Entra ID to `Grafana Admin` / `Grafana Editor` / `Grafana Viewer` roles; datasource reads use the Grafana instance's managed identity — meaning a Grafana Viewer can see anything the identity can query. Restrict per-audience with separate folders + folder permissions, and for hard isolation, separate Grafana instances (stakeholder vs engineering) whose identities have different workspace scopes.
- Executives get `Grafana Viewer` on a locked stakeholder folder. Nobody edits the live board in place.

## 5. SLOs and alerting for agent quality

Define per agent × environment; evaluate over 5–15 min windows in Log Analytics scheduled query alerts or Grafana alerting:

| SLI | Definition | Starter SLO / alert |
|---|---|---|
| Session error rate | failed sessions ÷ sessions (root span status) | ≥ 99% success; page < 97% over 15 min |
| Step latency p95 | per `gen_ai.operation.name` span duration | budget per step class (e.g. LLM call p95 < 20 s); warn on 2× baseline |
| Token spend | sum `gen_ai.usage.{input,output}_tokens` × price | daily budget; warn 80%, page 100%; alert on per-session outliers (runaway loops) |
| Tool-failure rate | failed tool spans ÷ tool spans, per tool | < 2%; page on any tool > 10% (upstream outage signature) |
| Quality proxies (hallucination is not directly measurable in telemetry) | retry/regeneration rate, guardrail-block rate, user thumbs-down rate, LLM-judge score sampled offline from archived (ADX) sessions, groundedness-check failures | trend + week-over-week regression alerts, not paging |
| Pipeline health | collector self-metrics: queue size, send failures, tail-sampling drops, App Insights ingestion latency | page — a dead pipeline silently zeroes every other SLI |

Alert on **absence** too (`count() == 0` for 10 min = pipeline or agent down). Route: page on error-rate/pipeline/budget-100%; ticket the rest.

## 6. Top-stakeholder LIVE dashboard — do / don't

**Do**
- 5–7 tiles max: sessions today, success %, p95 session latency, token spend vs budget, top failing tool, trend sparklines. One screen, no scrolling.
- Pre-aggregate: dashboard queries hit summarized/materialized data (KQL materialized views / summary tables), never raw span scans — keeps load fast and cost flat.
- Annotate sampling: label spend/volume tiles "extrapolated from N% sample" if computed from sampled data — or better, drive counts from unsampled metrics, keep sampling for traces only.
- Read-only viewer role (§4); auto-refresh 1–5 min; show data-freshness timestamp; state the SLO target on each SLI tile so green/red is self-explanatory.
- Dry-run a failure day: verify the dashboard degrades honestly (shows red, not blank) when the pipeline or agent breaks.

**Don't**
- No raw prompts/completions or user identifiers — a stakeholder screen is a shoulder-surfing exfil channel; content lives in Purview's governed store, not on a wallboard.
- No live-editable panels, no drill-through into raw logs from the exec view, no per-user leaderboards (works councils/GDPR), no vanity metrics without targets, no un-thresholded "AI quality" gauges you can't defend, and never wire the board to a daily-capped workspace tier that blanks at month-end — stakeholders remember the blank, not the cap.

## Sources

- https://pypi.org/project/opentelemetry-util-genai/ and https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation-genai/util.html — accessed 2026-08-15 — content capture off by default; `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` values (`true`/`span_only`/`event_only`/`span_and_event`); `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`.
- https://opentelemetry.io/blog/2024/otel-generative-ai/ — accessed 2026-08-15 — GenAI semconv design: opt-in content, token-usage attributes.
- https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/redactionprocessor/README.md — accessed 2026-08-15 — allowlist model, `blocked_values` masking, precedence rules.
- https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/tailsamplingprocessor/README.md and .../testdata/tail_sampling_config.yaml — accessed 2026-08-15 — policy types (status_code, latency, numeric/string_attribute, probabilistic, and/composite), decision_wait/num_traces, latency measured earliest-start→latest-end, per-trace all-or-nothing decisions.
- https://grafana.com/docs/tempo/latest/set-up-for-tracing/instrument-send/set-up-collector/tail-sampling/policies-strategies/ — accessed 2026-08-15 — policy ordering (errors/latency before probabilistic) and trace-affinity load-balancing requirement.
- https://learn.microsoft.com/en-us/azure/well-architected/service-guides/application-insights/cost-optimization — accessed 2026-08-15 — sampling as primary volume control; daily cap as last resort; workspace-based prerequisites.
- https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs — accessed 2026-08-15 — commitment tiers (~100 GB/day threshold, up to ~30% saving), workspace vs App Insights cap interaction, table-level retention/Basic Logs.
- https://oneuptime.com/blog/post/2026-02-09-otel-tail-sampling-intelligent/view and https://oneuptime.com/blog/post/2026-01-25-tail-based-sampling-opentelemetry/view — accessed 2026-08-15 — head-vs-tail economics, buffering memory cost.
- https://learn.microsoft.com/en-us/azure/azure-monitor/logs/manage-access (referenced via cost/architecture guides above) — accessed 2026-08-15 — workspace access modes, table-level RBAC, Monitoring/Log Analytics built-in roles. *(Role model additionally cross-checked against the Well-Architected App Insights service guide.)*
- https://learn.microsoft.com/en-us/purview/dspm-for-ai — accessed 2026-08-15 — Purview as the governed store for prompt/response content (supports §1/§6 content-split argument).
