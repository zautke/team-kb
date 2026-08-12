# CURRENT TASK STATE — team-kb

**As of:** 2026-08-12 · **Repo:** <repo-root> (origin: github:/zautke/team-kb) · **Phase:** plugin build (approved plan)

## State

- C# M0 stack **punted in place** (`src/`, 18/18 tests on build host, untouched). Live path = dual-target plugin.
- Approved plan: `~/.claude/plans/i-need-to-set-deep-lobster.md` — base plan + Appendix A (E2E battery runbook, GA/CA per-doc) + Appendix B (gap addendum: 12-tool server, embeddings, deterministic scoring).
- Docs scrubbed of machine refs (564a8ff). Vault `vault/` still to bootstrap; test vault `~/vault/kb-test` exists (bare `.obsidian`).

## Resume point

Implementation Phase 1 not yet started. Order:
1. Vault bootstrap (parameterized on TEAMKB_VAULT; run for repo `vault/` AND `~/vault/kb-test`; tier tree, tags registry seed, kb.base, merged .obsidian)
2. `plugin/` build: zero-dep Python MCP server (6 byte-parity tools ported from conformance-map §F exact strings + 6 new: submit_document, ingest_chunks, semantic_search, suggest_tags, search_by_tag, reindex, add_relations), unittest suite (ported GateTests), agents (kb-agent, kb-curator), skills (kb-prime, dispatch, 6 curate-*, kb-battery), hooks (PreCompact→episode), commands
3. Copilot side: `.github/agents/*.agent.md` (gpt-5.6-luna + xhigh — verify field names from Copilot docs first), skills copy
4. E2E battery per Appendix A/B on ≥5 docs from docs/research + docs/whitepapers → evidence to `docs/test-battery/run-<date>/` + VERIFY.md
5. Continuity + commit per phase

## Key constraints

- Embeddings: hosted `https://ollama2.braisenly.com` `/api/embed`, `nomic-embed-text-v2-moe:latest`, task prefixes `search_document:`/`search_query:` mandatory; NO local model weights on this Mac; `TEAMKB_EMBED_URL`/`TEAMKB_EMBED_MODEL` env-swappable.
- Agents: GA never gets propose/commit; CA never gets fs-write. Write path = gates only.
- Battery pass gate deterministic (recall@5, verdict correctness, expected-absent probe); LLM 0-1 scores commentary.
