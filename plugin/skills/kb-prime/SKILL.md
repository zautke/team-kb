---
name: kb-prime
description: >
  Prime the primary coding agent for the team-kb vault scheme. Use at session
  start, when the user says "prime the KB" / "load the knowledge base", or before
  any task that reads or writes vault knowledge. Loads the constitution digest,
  ontology vocabulary, verdict contract, and the propose→commit ritual.
---

# kb-prime — session priming for team-kb

You are now operating against the **team-kb vault** (markdown-canonical,
SQLite-indexed, gate-protected). Playbooks and cheatsheet tiers are empty at M0 —
this digest is the priming payload; nothing else is pretended to exist.

## 1. Constitution digest (what the gates enforce)

| Gate | Rule |
|------|------|
| C1 | Folder computed from entity class — you never supply paths |
| C2 | Permalink = normalized title, unique. Merge or supersede — never suffix |
| C3 | Relation verbs have dom/rng signatures (see ontology digest) |
| C4 | Relation targets must already exist — order writes accordingly |
| I1 | Every note has ≥1 relation OR an isolated_justification |
| I4 | Near-duplicate titles (trigram > 0.85, same class) rejected |
| PROV | ≥1 provenance (source+author); TBD/TODO/unknown rejected |
| HYP | Any [hypothesis] observation ⟹ confidence < 0.7 |
| TAG | Only registered namespaced tags (domain/ project/ status/ source/ machine/) |

Anchor protection: never write under `_meta/**` or edit `status/anchor` notes.
Vocabulary (classes/verbs/kinds) is closed — no tool can change it; never propose to.

## 2. Ontology vocabulary

- **Classes (10)**: Person, Org, Project, Codebase, Technology, Artifact, Concept,
  Event, Decision, Agent. Event → `episodes/`; others → `knowledge/<class>`.
- **Verbs (14, forward-only; inverses computed)**: IsA, PartOf, DependsOn, Uses,
  Causes, Precedes, Supersedes, DerivesFrom, Describes, Governs, Owns, Addresses,
  Contradicts, Mentions.
- **Observation kinds (12)**: fact, hypothesis, decision, constraint, preference,
  lesson, procedure, risk, question, status, contradiction, deprecated.

## 3. Verdict honesty contract (hard rule)

`search_notes` / `semantic_search` / `read_note` return `verdict: ok | absent`.
**absent = the knowledge does not exist. Report the gap and STOP searching.**
No synonym retries. This is the single most important retrieval behavior.

## 4. Write ritual

`propose_note` → violations? fix curation, re-propose → `commit_note` → done.
Never treat a propose as a commit. Never hand-edit vault markdown — the MCP
server is the only write path; hand edits bypass every gate.

## 5. Delegation

- Ingest/curate a document → `/team-kb:kb-curator` (the Curator agent)
- Search/read/submit as a user of the KB → `/team-kb:kb-agent`
- Batch operations end with `capture_episode` (maintenance rule: every run
  writes its report back as an episode).
