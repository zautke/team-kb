---
title: "R6 — kb failure post-mortem v2: formal grounding (agent: kb-postmortem-2)"
type: research
status: active
created: 2026-08-11
provenance:
  - source: "session:2026-08-11-teamkb-rebuild-research"
    author: "agent:claude-fable-5"
tags: [research, rebuild, dossier-2026-08]
---

# master-kb Post-Mortem v2 — empirical re-audit + formal grounding (read-only, 2026-08-11)

Tooling note: codemunch could NOT index the legacy corpus — both `codemunch` and `codemunch-adagio` are hosted/remote and `resolve_repo /Users/derp/basic-memory` returns "Path does not exist". Fell back to read-only `find`/`python3` measurement (stated as required). Current master-kb sampled via kb MCP (`list_directory`, `schema_infer`, `schema_validate`).

## A. Empirical inventory

### A1. Legacy corpus `/Users/derp/basic-memory` — 653 .md, 8.2 MB, full census (not a sample)

| Defect | Measured |
|---|---|
| Frontmatter present | 653/653 (100%) — but field support tiers: permalink 653, type 644, title 641, tags 616, status 518, entity_type 509, created 495, modified 491 → **144 notes lack `entity_type`/`created`** |
| Relation dialects (coexisting) | `- **rel** …` **2405**; `- rel [[T]]` **1249**; `- [rel] [[T]]` **64**. 3 dialects, 433/653 notes carry relations |
| Wikilinks | 2451 total, **862 unresolvable = 35.2%** |
| Orphans (no inbound wikilink) | **351/653 = 53.8%** |
| Duplicate slugs | **31 colliding basenames** (`readme` ×10, `index` ×6, `tasks` ×4, `planning`/`project`/`contributing` ×3 …) |
| Filename dialect | **378/653 (57.9%)** title-cased-with-spaces vs slugified — two identifier conventions in one store |
| Observation kinds | **189 distinct tokens**; head fact 165 / technique 101 / principle 88 / requirement 73; tail is singletons |
| Category confusion (new, v1 missed) | Relation verbs used as **observation** kinds: `relates-to` 13, `uses` 11, `implements` 9 |
| Provenance drift | 29 notes live under dirs literally named `C:\Users\me\.gemini\…`, `C:\Users\me\dev\python\…` — Windows paths materialized as vault folders |
| Junk (.bak/conflict) | **0** in legacy — junk is a *current-kb* pathology, not inherited |

### A2. Current master-kb (kb MCP)

- **Root has 59 directories.** Singular/plural twins confirmed and quantified: `project/` (14 notes + 9 subdirs) vs `projects/` (33 subdirs); `document/` vs `docs/`; `tool/` vs `tools/`; `notes/` vs `observations/`. **12 project identities exist in both** (agent-toolkit, baker-app, blogg, chatgpt-index, claude-export-viewer, dnd-form-builder, dot-agents, graphrag, mdeditor, multi-agent-helm, ollama-dir, wxt-prompt).
- **Type/path conflation**: `project/document/` — a class folder nested inside an instance folder. Path is doing double duty as type and as container.
- **Hollow classes confirmed**: `person/`, `organization/`, `goal/`, `technology/` = exactly 1 note each, all "… Entity Class — Index" stubs (2026-05-08). Class declared, never populated.
- **NEW — vocabulary explosion is ~10× worse than v1 reported.** `schema_infer("note")` over 198 notes of one type yields **≈120 distinct observation kinds** (top `fact` 32%; long singleton tail: `host_binding`, `model_path`, `ops_tool`, `tool_path`, `working-dir`, `agent-roster`, `dod`, `bail` …) and **≈60 distinct relation predicates**. v1's "~14 invented kinds" understated by an order of magnitude.
- **NEW — case-dialect predicate twins** (same edge semantics, two names): `part_of` 41 / `PART_OF` 21; `preceded_by` 17 / `PRECEDED_BY` 1; `relates_to` 12 / `related_to` 5; `implements` 2 / `IMPLEMENTS` 3; `follows` 3 / `FOLLOWS` 1; plus `DOCUMENTS`/`DESCRIBES`/`DESCRIBED_BY`/`REFERENCES`/`REFERENCED_BY` overlapping.
- **NEW — malformed predicates from markdown bleed** (parser accepted them as relation names): `` `RELATED_TO ``, `**Related**:`, `**produced_by**:`, `**delivered_by**:`.
- **NEW — the machine gate existed and was never switched on.** `schema_validate("note")` → *"No schema found"*. basic-memory ships Picoschema + `settings.validation: warn|error`; **zero schema notes exist in master-kb**. v1's root cause "gates were prose, never code" sharpens to: *the code gate shipped in the tool, and no one declared a shape.*
- **Junk indexed**: `runbooks/` holds **14 `.md.bak`** files (matches v1's 37%); `projects/PROJECT_MANIFEST.md.bak`; root `conflict-files-obsidian-git.md`. Caveat: a root-level recursive `*.bak` glob at depth 4 returned **zero** while a depth-2 glob on `runbooks/` returned 14 — the listing tool's recursive glob is unreliable, so the global junk count is a **lower bound (≥15)**, not a census.

## B. Empirical failure → formal defect class → countermeasure → C# write-path enforcement

| Empirical failure | Formal defect class | Formal countermeasure | Enforcement in rebuilt C# MCP |
|---|---|---|---|
| 3 relation dialects; ~60 predicates; case twins; `**bold**:` garbage | Syntactic validity + consistency (Zaveri 18-dim) | Closed predicate vocabulary; SHACL `sh:path`+`sh:in` | Relation predicate is a **C# enum in the tool JSON Schema** — an off-vocab edge is unrepresentable, not rejected-later |
| ~120 observation kinds, singleton tail | Conciseness / semantic accuracy | Controlled vocabulary + shape `sh:in` | `ObservationKind` enum; new kinds require a KGCL-typed vocabulary-extension PR |
| 35.2% legacy / 50% v1-sampled broken wikilinks | Referential integrity (Zaveri: dereferenceability); dangling FK | PG-Keys foreign-key constraint; SHACL `sh:class`+`sh:minCount` | Write-time resolver: target must exist → else reject, or auto-create typed stub + open task |
| All relations one-sided | OOPS **P13 missing inverse relationships** | Declared `inv(p)` per predicate | Inverse edge is **computed and materialized** by the server; authors never write both sides |
| Predicates with no type discipline (`USES` on anything) | OOPS **P11 missing domain/range** | PG-Schema edge type signature `dom(p)→rng(p)` | Signature table checked pre-commit; violation = 4xx from `write_note` |
| project/ vs projects/, tool/ vs tools/, path-as-type | Schema/instance conflation; heterogeneity | PG-Schema node types; path derived from type | `type` is authoritative; **folder path is computed**, never author-supplied |
| Title-vs-slug twins suffixed `-1`; 31 dup slugs | Entity resolution / `owl:sameAs` identity crisis (Halpin et al.) | Key constraint: exclusive+mandatory+singleton (PG-Keys modes) | Canonical `permalink = norm(title)`; on collision → **merge-or-distinguish gate**, never silent `-1` |
| Hollow classes (1 stub each) vs concept/ 90, document/ 150+ | Completeness + degree-distribution skew (bulk-load signature) | Class-completeness estimators (Galárraga PCA; non-parametric class estimators) | Nightly metric job: per-class cardinality, orphan ratio, component count, degree Gini; class with n≤1 auto-flagged deprecated |
| 53.8% orphan rate | Graph connectivity defect (component explosion) | Monotone invariant: every write connects | `write_note` requires ≥1 resolvable edge, or an explicit `--isolated` justification recorded |
| ≥15 `.bak`/conflict files indexed as notes | Junk/noise in extraction scope | Scope predicate on V | Ingest filter: `.md` ∧ ¬`(\.bak|conflict|~|\.orig)$`; enforced in the indexer, not in prose |
| Prose gates, no schema notes | Absent validation layer | SHACL/ShEx shapes graph; Picoschema | Shapes are **checked into the repo and CI-run**; `validation: error` (not warn) |
| Ad-hoc taxonomy drift over time | Uncontrolled schema evolution | **KGCL** change ops + reverse patch | All vocabulary/type changes are KGCL ops with dry-run diff + rollback |

## C. Minimal formal model (constitution appendix)

Vault as a typed property graph `G = (V, E, τ, π, ω)`:
- `τ : V → T`, `T` a **closed** finite node-type set (concept, document, project, person, organization, technology, goal, runbook, protocol, session, incident, decision).
- `E ⊆ V × P × V`, `P` a **closed** predicate set with signature `σ(p) = (dom(p), rng(p)) ∈ T×T` and partial involution `inv : P ⇀ P`.
- `π : V → Props` with mandatory `{permalink, title, type, created, modified}`; `ω : V → 2^(K × Text)`, `K` a closed observation-kind set.

Integrity constraints (pseudo-SHACL / PG-Schema):
1. **C1 Type closure** — `∀v: τ(v) ∈ T`; `folder(v) = path(τ(v))` is *derived*.
2. **C2 Identity key** — `permalink` is EXCLUSIVE ∧ MANDATORY ∧ SINGLETON (PG-Keys mode); `permalink = norm(title)`.
3. **C3 Signature** — `∀(u,p,v) ∈ E: τ(u)=dom(p) ∧ τ(v)=rng(p)`.
4. **C4 Referential integrity** — `∀(u,p,v) ∈ E: v ∈ V` (no dangling link, ever).
5. **C5 Inverse closure** — `inv(p)=q ⟹ ((u,p,v) ∈ E ⟺ (v,q,u) ∈ E)`; server-computed.
6. **C6 Vocabulary closure** — `∀(k,_) ∈ ω(v): k ∈ K`.
7. **C7 Scope** — `v ∈ V ⟺ file(v)` is `.md` ∧ not a backup/conflict artifact.
8. **C8 Class non-vacuity** — `∀t ∈ T: |τ⁻¹(t)| ≥ 2` or `t` is marked `deprecated`.

Monotone curation invariants (t → t+1):
- **I1 Connectivity** — `orphans(G_{t+1}) ≤ orphans(G_t)`.
- **I2 Non-regression** — `violations(G_{t+1}) ≤ violations(G_t)` for the shapes graph; CI gate.
- **I3 Governed evolution** — `T`, `P`, `K` change only via KGCL ops carrying a reverse patch.
- **I4 Identity discipline** — no two `v₁,v₂` with `τ` equal and `sim(title) > θ` unless an explicit `distinct_from` assertion exists.

## D. Citations (all checked 2026-08-11)

1. Zaveri et al., *Quality Assessment for Linked Data: A Survey* (18 dimensions / 69 metrics) — https://doi.org/10.3233/sw-150175
2. Poveda-Villalón et al., *OOPS! (OntOlogy Pitfall Scanner!)* — 41 pitfalls incl. P11 missing domain/range, P13 missing inverse — https://oops.linkeddata.es/ ; https://www.semantic-web-journal.net/system/files/swj989.pdf
3. W3C, *SHACL — Shapes Constraint Language* (Recommendation) — https://www.w3.org/news/2017/shapes-constraint-language-shacl-is-now-a-w3c-recommendation/
4. *SHACL Validation under Graph Updates* (2025) — incremental re-validation on writes — https://arxiv.org/html/2508.00137v1
5. Angles, Bonifati et al., *PG-Schema: Schemas for Property Graphs*, SIGMOD/PACMMOD 2023 — https://arxiv.org/abs/2211.10962
6. *PG-Keys: Keys for Property Graphs* (exclusive/mandatory/singleton modes) — https://www.semanticscholar.org/paper/a2e52a7e9c0862d2d841e5a788f1e975e736d7c5
7. Halpin, Hayes et al., *When owl:sameAs Isn't the Same* — identity/ER pathology — https://link.springer.com/chapter/10.1007/978-3-642-17746-0_20
8. Galárraga & Suchanek, *Predicting Completeness in Knowledge Bases* (PCA/PCWA), WSDM 2017 — https://suchanek.name/work/publications/wsdm-2017.pdf
9. *Non-Parametric Class Completeness Estimators (Wikidata)* — https://arxiv.org/pdf/1909.01109
10. *Completeness, Recall, and Negation in Open-World KBs: A Survey* — https://arxiv.org/html/2305.05403
11. Matentzoglu et al., *A Change Language for Ontologies and Knowledge Graphs* (KGCL), Database (Oxford) 2025 — https://arxiv.org/abs/2409.13906 ; https://github.com/INCATools/kgcl
12. *Systematic Evaluation of Knowledge Graph Repair with LLMs* (2025) — violation-induced repair benchmarking — https://arxiv.org/pdf/2507.22419
13. *xpSHACL: Explainable SHACL Validation* (VLDB-W 2025) — https://arxiv.org/pdf/2507.08432

## Bottom line vs v1

v1 was directionally right and quantitatively low. Three material extensions: (1) vocabulary drift is ~120 observation kinds + ~60 predicates *in a single note type*, including case-dialect twins and markdown-corrupted predicate names; (2) legacy corpus is 53.8% orphaned and 35.2% dangling — the graph was never a graph, it was a folder of documents with decorative links; (3) the root cause is not "no gate existed" but "**a machine-checkable gate shipped in basic-memory (Picoschema + `validation: error`) and zero shapes were ever declared**". A C# rewrite that puts `T`, `P`, `K` into tool-schema enums and computes inverses/paths server-side makes most of this inventory structurally unrepresentable rather than merely discouraged.
