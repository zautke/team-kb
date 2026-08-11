# INSTRUCTIONAL INSIGHTS — team-kb (append-only)

## 2026-08-11

- **Replay real defects as the acceptance suite.** GateTests fixtures are literal master-kb failures
  (twin titles, dangling slugs, .bak junk). The suite caught 2 genuine bugs on first run (scope-regex
  anchor, FTS5 hyphen) — proof the pattern works. Keep growing tests from post-mortem inventory, not
  from imagination.
- **Cross-machine bring-up finds a distinct bug class**: Windows file locking (sqlite pool),
  AppleDouble pollution, shell-quoting corruption. Budget one bring-up pass per platform; never
  claim "verified" from source-reading alone.
- **A silent server is not a working server.** Handshake smoke (initialize → tools/list with
  parsed responses) is the minimum bar before any MCP server is called done — logging to stderr and
  building clean prove nothing about the protocol path.
- **Research agents: harvest reports from transcripts via SendMessage extraction** — idle
  notifications don't carry payloads; grep the session jsonl for the final SendMessage.
