---
name: curate-observations
description: >
  Curation step CA-6d: extract typed observations from a source document
  (12 closed kinds; hypothesis confidence ceiling). Use when writing the
  observations array during team-kb curation.
---

# curate-observations — typed claims, one line each

- Kinds (closed): fact, hypothesis, decision, constraint, preference, lesson,
  procedure, risk, question, status, contradiction, deprecated.
- One claim per observation, one line, self-contained (readable without the
  source open).
- Kind discipline:
  - **fact** — verifiable in the source as stated
  - **hypothesis** — plausible but unverified ⟹ note confidence MUST be < 0.7
  - **lesson/decision/constraint** — only when the source actually records one
  - **contradiction** — records a conflict with another note; pair it with a
    `Contradicts` relation
- 3-8 high-signal observations beat 20 shallow ones; the FTS index searches
  observation text — write them with retrieval keywords intact.
- Per-claim provenance ref when it differs from the note's source.
