#!/usr/bin/env bash
# otel-stack.sh — lifecycle driver for the team-kb OTel local loop.
# See docs/research/otel-agentic-csharp/09-local-deployment.md for the runbook.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION=""
PROFILE=""
CONFIG=""

Usage() {
  cat <<'EOF'
Usage: otel-stack.sh -a <action> [-p <profile>] [-c <collector-config>]

Actions:
  -a, --action    up | down | status | logs | validate | smoke
  -p, --profile   optional compose profile: cosmos  (starts the Cosmos emulator)
  -c, --config    collector config path relative to this dir
                  (default collector/config.yaml; Azure: collector/config-azure.yaml)
  -h, --help      this help

Examples:
  ./otel-stack.sh -a up                          # aspire + collector + bridge (file sink)
  ./otel-stack.sh -a up -p cosmos                # + Cosmos emulator
  ./otel-stack.sh -a up -c collector/config-azure.yaml   # + Azure Monitor pipeline
  ./otel-stack.sh -a smoke                       # send one test span, verify end to end
  ./otel-stack.sh -a status                      # health of every service
  ./otel-stack.sh -a down
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -a|--action)  ACTION="$2"; shift 2 ;;
    -p|--profile) PROFILE="$2"; shift 2 ;;
    -c|--config)  CONFIG="$2"; shift 2 ;;
    -h|--help)    Usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; Usage; exit 1 ;;
  esac
done

[[ -z "$ACTION" ]] && { Usage; exit 1; }

cd "$SCRIPT_DIR"
[[ -f .env ]] || { echo "No .env — run: cp .env.example .env  (then edit)" >&2; exit 1; }
# shellcheck disable=SC1091
set -a; source .env; set +a

COMPOSE=(docker compose)
[[ -n "$PROFILE" ]] && COMPOSE+=(--profile "$PROFILE")

apply_config() {
  # Collector mounts ./collector; compose always reads config.yaml, so an
  # alternate config is copied over the active one (originals stay in git).
  if [[ -n "$CONFIG" && "$CONFIG" != "collector/config.yaml" ]]; then
    [[ -f "$CONFIG" ]] || { echo "Config not found: $CONFIG" >&2; exit 1; }
    cp "$CONFIG" collector/config.active.yaml
    echo "NOTE: using $CONFIG (copied to collector/config.active.yaml)"
    export COLLECTOR_CONFIG=/etc/otelcol/config.active.yaml
  else
    export COLLECTOR_CONFIG=/etc/otelcol/config.yaml
  fi
}

case "$ACTION" in
  up)
    apply_config
    if [[ "$COLLECTOR_CONFIG" == *config-azure* || "$CONFIG" == *azure* ]]; then
      [[ -z "${AZURE_MONITOR_CONNECTION_STRING:-}" ]] && {
        echo "AZURE_MONITOR_CONNECTION_STRING is empty in .env — required for the Azure config." >&2; exit 1; }
    fi
    "${COMPOSE[@]}" up -d --build
    echo
    echo "Aspire dashboard:  http://localhost:${ASPIRE_UI_PORT}"
    echo "OTLP ingest:       grpc://localhost:${OTLP_GRPC_PORT}  http://localhost:${OTLP_HTTP_PORT}"
    echo "Bridge health:     http://localhost:${BRIDGE_PORT}/healthz"
    echo
    echo "Point an app at it with:"
    echo "  export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:${OTLP_GRPC_PORT}"
    echo "  export TEAMKB_SESSION_ID=\$(uuidgen)"
    echo "  export TEAMKB_SESSION_NAME=my-session"
    ;;
  down)
    "${COMPOSE[@]}" down
    ;;
  status)
    "${COMPOSE[@]}" ps
    echo
    printf 'collector health: '
    curl -sf "http://localhost:${COLLECTOR_HEALTH_PORT:-14313}/" >/dev/null && echo OK || echo FAIL
    printf 'bridge health:    '
    curl -sf "http://localhost:${BRIDGE_PORT}/healthz" || echo FAIL
    echo
    ;;
  logs)
    "${COMPOSE[@]}" logs -f --tail 100
    ;;
  validate)
    apply_config
    docker run --rm -v "$SCRIPT_DIR/collector:/etc/otelcol:ro" \
      "${OTEL_COLLECTOR_IMAGE}" validate --config "${COLLECTOR_CONFIG}"
    echo "collector config valid: ${COLLECTOR_CONFIG}"
    ;;
  smoke)
    # One synthetic span via OTLP/HTTP JSON. Verifies: collector ingest ->
    # bridge sink (and Aspire display; check the UI for trace "smoke-step").
    NOW=$(($(date +%s) * 1000000000))
    TRACE_ID=$(hexdump -n16 -e '16/1 "%02x"' /dev/urandom)
    SPAN_ID=$(hexdump -n8 -e '8/1 "%02x"' /dev/urandom)
    curl -sf -X POST "http://localhost:${OTLP_HTTP_PORT}/v1/traces" \
      -H 'Content-Type: application/json' \
      -d @- <<EOF
{"resourceSpans":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"smoke"}}]},
"scopeSpans":[{"scope":{"name":"smoke"},"spans":[{
  "traceId":"${TRACE_ID}","spanId":"${SPAN_ID}","name":"smoke-step","kind":1,
  "startTimeUnixNano":"${NOW}","endTimeUnixNano":"$((NOW + 250000000))",
  "attributes":[
    {"key":"session.id","value":{"stringValue":"smoke-session"}},
    {"key":"session.name","value":{"stringValue":"smoke"}}]}]}]}]}
EOF
    echo "sent trace ${TRACE_ID}"
    sleep 4
    if [[ -f data/spans.jsonl ]] && grep -q "${TRACE_ID}" data/spans.jsonl; then
      echo "SMOKE PASS: span reached the bridge file sink (data/spans.jsonl)"
    else
      echo "bridge file sink miss — if using Cosmos, query container '${COSMOS_CONTAINER}' for traceId ${TRACE_ID}"
    fi
    echo "Aspire check: http://localhost:${ASPIRE_UI_PORT} -> Traces -> 'smoke-step'"
    ;;
  *)
    echo "Unknown action: $ACTION" >&2; Usage; exit 1 ;;
esac
