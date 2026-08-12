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

## 2026-08-12

- **Never assume config-file shapes — research first.** Agent frontmatter `model:` guess
  (`5.6-luna-xtrahigh`) was wrong syntax for the harness; official-docs research resolved it to a
  different vendor's model+effort convention and forced a dual-target design. Verify agents.md /
  SKILL.md / plugin.json / MCP-spec shapes against official docs dated today before writing any file.
- **3-disparate-reviewer distillation works**: retrieval, orchestration, and integrity lenses each
  found gaps the others missed (task prefixes; wildcard tool-grant violation; DCF wrong-tier + I4
  trap). Distill to one addendum; record unanimous findings (no-RRF-at-MVP) as strong signals.
- **Runbooks must be reviewed against the tool surface they assume** — Appendix A silently required
  6 tools the base plan never shipped; all three reviewers caught it as the headline. Diff
  runbook-verbs vs tools/list before approving any runbook.
