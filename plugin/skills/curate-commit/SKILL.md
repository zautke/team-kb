---
name: curate-commit
description: >
  Curation step CA-7/CA-10/CA-11: the propose → fix → commit ritual, submission
  linking, DCF episode capture, and the final report. Use when finalizing a
  curated note into the team-kb vault.
---

# curate-commit — the write ritual

1. `propose_note(...)` with everything assembled by the earlier steps.
2. **REJECTED?** Read each `[GATE]` line, fix the CURATION (gate-table reference
   maps gate → fix), re-propose. Never work around a gate; never lower the bar
   to pass it (e.g. fake justification, placeholder provenance).
3. `commit_note(proposalId)` — a "Commit blocked" error means the vault moved;
   re-curate and re-propose.
4. `link_submission(submissionId, permalink)` — binds the doc vector to the note
   so semantic search returns permalinks.
5. `read_note(permalink)` — verify: frontmatter complete, tag plane present
   (`kb/<class>`, `kb/status/…`), relations render as `[[target]]` wikilinks,
   backlinks resolve on targets. Do NOT add duplicate wikilinks.
6. **DCF** (CA-10): `capture_episode(title: "DCF <submission-id>", body: <standard
   form>)` — submission id, source path, strategy, chunk count, neighbors, tags,
   violations hit/fixed, timestamps.
7. **Report** (CA-11): final message = one fenced JSON block (schema in agent
   instructions). Compact, high-signal, no prose padding.
