#!/usr/bin/env bash
# MCP server launcher. TEAMKB_VAULT from the parent environment wins (battery
# runs export it); otherwise fall back to the repo default passed by .mcp.json
# as TEAMKB_DEFAULT_VAULT. Server itself stays strict (no fallback).
set -euo pipefail
export TEAMKB_VAULT="${TEAMKB_VAULT:-${TEAMKB_DEFAULT_VAULT:?no vault configured}}"
exec python3 "$(dirname "${BASH_SOURCE[0]}")/teamkb_server.py"
