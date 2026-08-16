# 07 — MCP server configuration

The KB is exposed as one stdio MCP server named `teamkb`
(`plugin/mcp/teamkb_server.py`). It is pure Python standard library — no pip
install, no virtualenv, no build step. Every config below was launched and
answered a live `tools/call` while this page was written.

## Which config do I use?

| Host | Config | You edit |
|------|--------|----------|
| Claude Code, via the plugin | `plugin/.mcp.json` | nothing — it ships with the plugin |
| Copilot CLI | `mcp-servers:` block inside `.github/agents/*.agent.md` | nothing — it ships with the agents |
| Any other MCP client (Claude Desktop, custom host, CI) | your host's own config file | the standalone block below |

## Claude Code — plugin-provided (shipped)

`plugin/.mcp.json`:

```json
{
  "mcpServers": {
    "teamkb": {
      "command": "/bin/bash",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/run_server.sh"],
      "env": {
        "TEAMKB_DEFAULT_VAULT": "${CLAUDE_PROJECT_DIR}/vault"
      }
    }
  }
}
```

`${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PROJECT_DIR}` are expanded by the host, so
the plugin is location-independent. Load it for a session with:

```bash
claude --plugin-dir plugin/
```

Tools then appear as `mcp__plugin_team-kb_teamkb__<tool>`.

Note the indirection through `run_server.sh` rather than calling Python
directly:

```bash
export TEAMKB_VAULT="${TEAMKB_VAULT:-${TEAMKB_DEFAULT_VAULT:?no vault configured}}"
exec python3 "$(dirname "${BASH_SOURCE[0]}")/teamkb_server.py"
```

This is what lets a battery run override the vault (`TEAMKB_VAULT` from the
environment wins) while the repo vault stays the default — and the server itself
stays strict, refusing to start with no vault at all rather than guessing.

## Copilot CLI — agent-provided (shipped)

Inside `.github/agents/kb-agent.agent.md` and `kb-curator.agent.md`:

```yaml
mcp-servers:
  teamkb:
    command: bash
    args: ["plugin/mcp/run_server.sh"]
    env:
      TEAMKB_DEFAULT_VAULT: "vault"
tools:
  - "teamkb/search_notes"
  - "teamkb/semantic_search"
  # … the rest of that agent's grant
```

Copilot has no plugin manifest, so each agent carries its own server definition
and its own tool allow-list. Tools are referenced as `teamkb/<tool>`.

## Any other MCP client — standalone

Verified working: `initialize` → `serverInfo {"name":"teamkb","version":"1.0.0"}`,
then `search_notes` returning a real hit.

```json
{
  "mcpServers": {
    "teamkb": {
      "command": "python3",
      "args": ["/absolute/path/to/team-kb/plugin/mcp/teamkb_server.py"],
      "env": {
        "TEAMKB_VAULT": "/absolute/path/to/team-kb/vault",
        "TEAMKB_EMBED_URL": "https://your-embedding-endpoint",
        "TEAMKB_EMBED_MODEL": "nomic-embed-text-v2-moe:latest"
      }
    }
  }
}
```

Use absolute paths — the host's working directory is not guaranteed. Calling
`teamkb_server.py` directly is fine here; `TEAMKB_VAULT` is set explicitly, so
the `run_server.sh` fallback logic buys you nothing.

## Environment variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `TEAMKB_VAULT` | **yes** | none — server exits 1 | Vault root. No fallback, deliberately: a silent wrong-vault run is worse than a startup failure. |
| `TEAMKB_EMBED_BACKEND` | no | `http` | `http` (Ollama-shaped endpoint) or `onnx` (local in-process ONNX Runtime — see "Local ONNX embeddings" below). |
| `TEAMKB_EMBED_URL` | http backend | none — http backend fails fast without it | Embedding endpoint base (your own Ollama, LM Studio, or a containerised ONNX service — the API shape is Ollama's `/api/embed`). Not needed for `TEAMKB_EMBED_BACKEND=onnx`. |
| `TEAMKB_EMBED_MODEL` | no | `nomic-embed-text-v2-moe:latest` (http) / `bge-micro-v2-onnx` (onnx) | Embedding model identity. Changing it changes vector space — the server stamps it in the vault db and refuses the semantic channel on mismatch; re-embed the corpus, never mix. |
| `TEAMKB_ONNX_MODEL_DIR` | onnx only | none | Directory containing `model_quantized.onnx` (or `model.onnx`) + `tokenizer.json`. |
| `TEAMKB_CORPUS_ROOTS` | no | unrestricted | Colon-separated roots that `submit_document` will accept. Set it to stop ingestion of arbitrary filesystem paths. |
| `TEAMKB_RUN_ID` | no | `run-<YYYYMMDD-HHMMSS>` | Labels every event from this run so a batch is filterable afterwards. |
| `TEAMKB_EVENTS` | no | `<vault>/.teamkb-events.jsonl` | Event-log path override. |
| `TEAMKB_TRACE` | no | off | `1` also writes raw request/response bodies to `<vault>/.teamkb-trace.jsonl`. |

`TEAMKB_DEFAULT_VAULT` is not read by the server — it is only the fallback that
`run_server.sh` consumes.

## Local ONNX embeddings

The server can embed entirely on-machine — no network — via ONNX Runtime.

```bash
# one-time: fetch model (~17 MB) and install the two runtime deps
plugin/scripts/fetch_onnx_model.sh                 # TaylorAI/bge-micro-v2, quantized
pip install onnxruntime tokenizers                 # the only non-stdlib deps, lazy-imported

export TEAMKB_EMBED_BACKEND=onnx
export TEAMKB_ONNX_MODEL_DIR=~/vault/.models/bge-micro-v2-onnx
```

Facts that matter:

- **Default model `bge-micro-v2`** (384-d, ~17 MB int8): chosen for speed —
  ~20 ms/chunk on CPU. Higher-quality alternative:
  `fetch_onnx_model.sh --model nomic-v1.5` (768-d, 137 MB int8) with
  `TEAMKB_EMBED_MODEL=nomic-embed-text-v1.5-onnx`.
- **Vector spaces never mix.** The model identity is stamped into the vault db
  at first use; starting the server with a different `TEAMKB_EMBED_MODEL`
  disables all semantic tools with an explanatory error until you either fix
  the env or wipe embeddings and re-ingest.
- **θ is seeded per model** (`0.30` nomic, `0.69` bge-micro — bge's true/junk
  score margin is narrow; recalibrate per corpus via
  `UPDATE meta SET value=... WHERE key='semantic_theta'` if misses appear).
- Task prefixes are applied automatically per model family (nomic
  `search_document:`/`search_query:`; bge query-instruction prefix).
- The server never downloads weights — `fetch_onnx_model.sh` is the only
  sanctioned path, and it preflights free disk before writing.

## Protocol details

- **Transport**: stdio, newline-delimited JSON-RPC 2.0.
- **Handshake**: classic `initialize` → `notifications/initialized` → `tools/list`,
  advertising `protocolVersion 2025-06-18` and `capabilities {"tools": {}}`.
- **Modern-era clients** (spec 2026-07-28, which opens with `server/discover`
  instead of a handshake) get a clean `-32601 Method not found` and fall back to
  the legacy handshake, which is why this server interoperates with both eras.
- **stdout carries protocol only.** All logging goes to stderr. A stray `print()`
  in this server would corrupt the stream — that is why it uses `log.info`.
- **Startup lines on stderr** name the vault, the endpoint and the run id:
  ```
  [teamkb] INFO vault=/…/team-kb/vault embed=https://…/nomic-embed-text-v2-moe:latest
  [teamkb] INFO events → /…/team-kb/vault/.teamkb-events.jsonl (run_id=run-20260813-170452)
  ```
  Read these first when something behaves unexpectedly — most confusion is a
  wrong vault.
- **Shutdown**: exits on stdin EOF. A test harness that closes stdin immediately
  will see a "silent server"; hold stdin open while asserting.

## Smoke-testing a config without a host

```bash
{ printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'; sleep 2; } \
| TEAMKB_VAULT=vault python3 plugin/mcp/teamkb_server.py 2>/dev/null | tail -1
```

Expect a `tools/list` result carrying 15 tools. For single calls during normal
work, `plugin/scripts/kbcall.py -t <tool> -a '<json>'` does the same handshake
for you.
