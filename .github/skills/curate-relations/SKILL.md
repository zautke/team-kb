---
name: curate-relations
description: >
  Curation step CA-4/CA-7a: choose typed relations for a note — verb selection,
  signature conformance, C4 dependency ordering, I1 connectivity. Use when
  wiring a new note into the team-kb graph.
---

# curate-relations — wire the note into the graph

1. **Candidates**: CA-4 semantic neighbors + anything the source text explicitly
   cites or supersedes. Real connections only — a relation is a claim.
2. **Verb choice**: most specific verb whose signature fits (ontology digest).
   Common ingestion verbs: `DerivesFrom` (doc → its sources), `Describes`
   (doc → concept it explains), `Supersedes` (v2 → v1), `Contradicts`,
   `Mentions` (weakest — use when nothing stronger is true).
3. **Forward only** — never author the inverse; the server computes it.
4. **C4 ordering**: every target must already be committed. Order the batch
   (anchors → sources → dependents). A target landing later? Leave it out now,
   add it in the post-corpus back-pass with `add_relations`.
5. **I1**: ≥1 relation, or a truthful `isolatedJustification`. Genesis anchors
   into an empty vault use `"genesis anchor"`.
6. `since` = the date the relation became true (source doc date, not today,
   when known).
