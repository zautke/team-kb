---
name: curate-provenance
description: >
  Curation step CA-6c: attach real provenance to a note (PROV gate). Use when
  filling provenanceSource/provenanceAuthor during team-kb curation.
---

# curate-provenance — provenance or it didn't happen

- `provenanceSource`: the actual origin, precise enough to re-find it:
  repo-relative path (`docs/research/2026-08-11-x.md`), `url:…`, or
  `session:<date>-<topic>`.
- `provenanceAuthor`: who produced/captured it — `user`, `agent:curator`,
  or a named person if the source says so.
- Placeholders (`TBD`, `TODO`, `unknown`, empty) are rejected by the gate —
  if you can't source it, you can't write it.
- Observation-level refs: put a per-claim ref in the observation's
  `provenance` field (e.g. `url:…`, `§4.2`) when a claim's origin differs from
  the note's.
- Confidence tracks the SOURCE quality, not your enthusiasm: verified doc 0.9-1.0,
  inference from doc 0.6-0.8, hypothesis < 0.7 (HYP gate enforces this).
