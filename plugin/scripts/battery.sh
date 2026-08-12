#!/usr/bin/env bash
# Launch Claude Code with the team-kb plugin pointed at the BATTERY vault.
# Usage: plugin/scripts/battery.sh [-v|--vault <vault-dir>] [claude args...]

set -euo pipefail

Usage() {
  echo "Usage: $0 [-v|--vault <vault-dir>] [extra claude args...]"
  echo "  Defaults: vault=~/vault/kb-test, TEAMKB_TRACE=1"
  exit 1
}

VAULT="$HOME/vault/kb-test"
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -v|--vault) VAULT="$2"; shift 2 ;;
    -h|--help) Usage ;;
    *) EXTRA+=("$1"); shift ;;
  esac
done

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# .mcp.json interpolates TEAMKB_VAULT from the environment at server launch;
# exporting here overrides the repo-vault default for the battery run.
export TEAMKB_VAULT="$VAULT"
export TEAMKB_TRACE=1

echo "[battery] vault=$TEAMKB_VAULT trace=on plugin=$PLUGIN_DIR"
exec claude --plugin-dir "$PLUGIN_DIR" "${EXTRA[@]}"
