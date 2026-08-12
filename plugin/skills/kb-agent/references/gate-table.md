# Gate table — what a REJECTED propose means

| Gate | Trigger | Fix |
|------|---------|-----|
| C2 | permalink already exists | merge into or supersede the existing note; never suffix titles |
| C3 | verb dom/rng signature violated | pick a verb whose signature fits both classes (see ontology digest) |
| C4 | relation target doesn't exist | commit the target first, or drop to a back-pass via add_relations |
| I1 | no relations, no justification | find a real relation, or set isolated_justification (rare, must be true) |
| I4 | title trigram-similar (>0.85) to same-class note | merge, supersede, or genuinely distinguish the title |
| PROV | no provenance / placeholder (TBD, TODO, unknown) | supply real source + author |
| HYP | [hypothesis] observation with confidence ≥ 0.7 | lower confidence below 0.7 or upgrade the observation to fact with evidence |
| TAG | unregistered tag | register_tag first (closed namespaces only), or reuse an existing tag |

Commit re-validates: a proposal can pass propose and fail commit if the vault
moved (e.g. C2 race) — "Commit blocked: <gate>: <msg>" means re-curate, re-propose.
