# REMEMBER — team-kb (append-only)

## 2026-08-11

- **Canonical repo**: <repo-root> (the authoring Mac). Build copy: the build host `C:\Users\me\dev\team-kb`
  (Windows, `ssh <build-host>`, dotnet 10.0.302, PowerShell default shell). The authoring Mac NEVER builds (no SDK,
  ENOSPC-prone boot volume).
- **The one rule of this project**: a rule not enforced by code does not belong in `_meta/`. Closed
  vocabularies live in MCP tool schemas; paths + inverse edges computed server-side; every write is
  staged propose→commit. (master-kb died of prose gates — post-mortem R5/R6.)
- **kb (basic-memory) is still the singular kb until team-kb replaces it** — rebuild research is
  mirrored there under `_governance/research/rebuild-2026-08/`.
- **macOS→Windows transfer gotchas**: AppleDouble `._*` files break csc (use `COPYFILE_DISABLE=1
  tar` or purge on extract); PowerShell double-quoted here-strings treat `\"` literally — transfer
  JSON as files.
- **.NET 10 notes**: C# 14 default (omit LangVersion); NU1015 = every PackageReference needs
  explicit Version; dotnet CLI chatter goes to stderr; MCP stdio servers must route ALL logging to
  stderr (`LogToStandardErrorThreshold = Trace`).
- **xunit.v3** (3.2.2) not xunit 2.x; test csproj needs `<OutputType>Exe</OutputType>`.
## 2026-08-12

- **C# stack punted in place** — never delete src/; it is the byte-parity reference for the Python
  server. Conformance map §F (in plan file + reviewer transcripts) holds the exact strings.
- **`5.6-luna-xtrahigh` = OpenAI `gpt-5.6-luna` + `xhigh` reasoning effort** (Copilot/Codex convention).
  NOT valid in Claude Code agent frontmatter (silent fallback on unknown model) — hence dual-target.
- **nomic-embed-text-v2 requires task prefixes** (`search_document:` / `search_query:`) or retrieval
  quality measurably degrades.
- **Claude Code plugin facts (verified 2026-08-12)**: components at plugin ROOT (not inside
  .claude-plugin/); commands merged into skills; plugin MCP tools named
  `mcp__plugin_<plugin>_<server>__<tool>`; agent `model:` accepts sonnet|opus|haiku|fable|inherit or
  claude-* IDs only, `effort:` separate field; plugin agents ignore hooks/mcpServers/permissionMode.
- **MCP spec 2026-07-28**: modern era has no initialize handshake (`server/discover`); dual-era
  clients fall back to legacy initialize — zero-dep legacy server stays interoperable if it returns
  clean JSON-RPC errors for unknown methods.

- **Hosted embed endpoint quirks (2026-08-12)**: Cloudflare 403s urllib's default User-Agent
  (set any custom UA); large /api/embed batches time out on the MoE model — sub-batch ≤8 texts,
  90s timeout. θ_semantic lives in db meta per vault (kb-test calibrated to 0.30).

## 2026-08-13 (later)

- **Semantic coverage does not survive a clone.** Document vectors derive from source corpus
  files, not from vault notes, so `reindex(rebuild=true)` restores FTS/tags/graph but leaves the
  semantic channel empty. Undecided fix — commit embeddings, or re-embed from note text.
- **Project-scope MCP servers need a session-start trust dialog.** Registering mid-session leaves
  `hasTrustDialogAccepted: false` and no `mcp__<server>__*` tools; the config is only picked up by
  a session that starts after the file exists.
- **`claude mcp add` writes absolute paths** — rewrite to `${CLAUDE_PROJECT_DIR:-.}` before
  committing, or the config is machine-specific.
- **TEAMKB_EMBED_URL still defaults to a personal tunnel** — the one value that must change before
  another team uses this.

- Old project's continuity archived at obsidian-vault-config `docs/proto-implementation/continuity/`;
  its compliance ontology is dead, its layered-fence/gate-server patterns remain referenceable.

## 2026-08-13 (onnx backend)

- **`nomic-embed-text-v2-moe` has NO ONNX export** (MoE; GGUF-only official quantization) —
  local ONNX means a different model, hence a different vector space.
- **Local backend shipped**: `TEAMKB_EMBED_BACKEND=onnx` + `TEAMKB_ONNX_MODEL_DIR`; default
  `bge-micro-v2` int8 (17 MB, 384-d, ~20 ms/chunk CPU; user chose speed). `nomic-v1.5` ONNX
  (137 MB, 768-d) documented alt. Deps `onnxruntime+tokenizers`, lazy-imported — http path stays
  zero-dep. Fetch via `plugin/scripts/fetch_onnx_model.sh` only; server never downloads.
- **θ is model-specific and seeded per family**: nomic 0.30, bge-micro 0.69 (bge true-match floor
  0.704 vs junk ceiling 0.680 — narrow margin is the model's ceiling).
- **Vector-space guard**: `embed_model` stamped in db meta; mismatch disables semantic tools with an
  explanatory REJECTED (never silent mixing, never runtime fallback between backends).
- One-time exception granted 2026-08-13: 17 MB bge model + onnx venv at `~/vault/.models/` on this
  machine for live verification (disk 27 Gi free at grant).
