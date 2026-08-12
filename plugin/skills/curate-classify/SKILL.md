---
name: curate-classify
description: >
  Curation step CA-6a: choose exactly one entity class for a document being
  ingested into the team-kb vault. Use when deciding where a note lives in the
  10-class taxonomy (C1 — folder is computed from class).
---

# curate-classify — pick the entity class

One class per note, from the closed set:

| Class | Choose when the note is fundamentally… | Folder |
|-------|----------------------------------------|--------|
| Concept | an idea, pattern, theory, model | knowledge/concept |
| Artifact | a produced thing: paper, whitepaper, report, spec, dataset | knowledge/artifact |
| Technology | a tool, framework, language, service | knowledge/technology |
| Codebase | a specific repository or module | knowledge/codebase |
| Project | an ongoing effort with goals | knowledge/project |
| Decision | a choice made, with rationale | knowledge/decision |
| Event | something that happened at a time (→ episode) | episodes |
| Person / Org / Agent | an actor | knowledge/person|org|agent |

Rules:
- Source documents ingested from a corpus are almost always **Artifact** (the
  document) — extract Concepts as separate notes only when they will be
  relation targets for other notes.
- Never invent hybrid classes; if torn between two, the note is probably two
  notes.
- The class fixes DerivesFrom/Describes/Governs dom eligibility — check the
  verb signatures (ontology digest) before finalizing.
