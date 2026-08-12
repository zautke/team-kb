---
name: curate-tags
description: >
  Curation step CA-5/CA-6b: assign namespaced tags to a note under the
  registry-before-choice rule. Use when selecting or registering tags during
  document curation for the team-kb vault.
---

# curate-tags — registry-before-choice

1. Call `suggest_tags(text: <overview draft>)` — reuse the best-scoring
   registered tags that genuinely fit. Reuse ALWAYS beats registering a
   near-synonym (near-dups are rejected anyway).
2. A genuinely new facet → `register_tag(tag, description)` FIRST, then use it.
   - Closed namespaces only: `domain/ project/ status/ source/ machine/`.
   - Give every registered tag a one-line description (it feeds tag-embedding
     similarity for future suggestions).
3. Never write `kb/*` tags — the server mirrors class/status there itself.
4. 2-4 topical tags per note is plenty; tags are a search plane, not a summary.
5. The registry row is appended to `_meta/registries/tags.md` server-side in the
   same operation — never edit that file directly.
