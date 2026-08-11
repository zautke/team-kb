---
title: "team-kb Ontology v1.0.0"
type: meta
kb_version: "1.0.0"
status: active
created: 2026-08-11
provenance:
  - source: "docs/research/2026-08-11 dossier (R1-R6)"
    author: "agent:claude-fable-5"
---

# team-kb Ontology v1.0.0

Aggressive reset from master-kb v0.2 (15 classes / ~40 rel types / 36 obs kinds → **10 / 14 / 12**).
Design rule: every vocabulary below is a **closed enum surfaced in the MCP tool JSON Schema** — an
off-vocabulary value is unrepresentable at the API, not rejected after the fact (post-mortem
countermeasure #7). Changes only via KGCL-typed evolution ops with reverse patches (invariant I3).

## Entity classes T (10)

| Class | Folder (derived) | Absorbs from v0.2 | Freshness half-life |
|---|---|---|---|
| `Person` | knowledge/person/ | Person | 180d |
| `Org` | knowledge/org/ | Organization | 180d |
| `Project` | knowledge/project/ | Project, Goal→`Project` w/ `kind: goal` | 90d |
| `Codebase` | knowledge/codebase/ | Codebase | 60d |
| `Technology` | knowledge/technology/ | Technology, Tool | 60d |
| `Artifact` | knowledge/artifact/ | Document, Service | 180d |
| `Concept` | knowledge/concept/ | Concept | 365d |
| `Event` | episodes/ | Event, Incident (`kind: incident`) | never (immutable) |
| `Decision` | knowledge/decision/ | Decision | never (immutable) |
| `Agent` | knowledge/agent/ | Agent, Instruction→procedure notes | 90d |

Folder path is **computed from class** by the server (constraint C1). Authors never supply paths.

## Core verbs P (14) — direction stored once; inverses computed (constraint C5)

| Verb | σ(p) = dom → rng | Inverse (computed name) | Absorbs from v0.2 |
|---|---|---|---|
| `IS_A` | Any → Concept | `HAS_INSTANCE` | (new) |
| `PART_OF` | Any → Any | `HAS_PART` | PART_OF, MEMBER_OF |
| `DEPENDS_ON` | Project\|Codebase\|Artifact\|Technology → Any | `REQUIRED_BY` | BLOCKS(neg), ENABLES(inv) |
| `USES` | Any → Technology\|Artifact\|Codebase | `USED_BY` | (rejected in v0.2; readmitted with signature) |
| `CAUSES` | Event\|Decision → Event\|Decision\|Project | `CAUSED_BY` | CAUSED, IMPACTS |
| `PRECEDES` | Event → Event | `FOLLOWS` | PRECEDED |
| `SUPERSEDES` | Any → Any (same class; DAG) | `SUPERSEDED_BY` | SUPERSEDES/REPLACED_BY |
| `DERIVES_FROM` | Artifact\|Concept\|Decision → Any | `SOURCE_OF` | DISTILLED_FROM, IMPLEMENTS (`mode: implements`) |
| `DESCRIBES` | Artifact\|Concept → Any | `DESCRIBED_BY` | DOCUMENTS, DESCRIBES, INDEXES |
| `GOVERNS` | Artifact(meta) → Any | `GOVERNED_BY` | GOVERNS |
| `OWNS` | Person\|Org\|Agent → Any | `OWNED_BY` | OWNS, CREATED_BY (`mode: created`) |
| `ADDRESSES` | Artifact\|Decision\|Project → Event\|Concept | `ADDRESSED_BY` | ADDRESSES, MITIGATES |
| `CONTRADICTS` | Any → Any (system-writable only) | symmetric | (contradiction lifecycle) |
| `MENTIONS` | Any → Any (weakest; auto-extracted allowed) | `MENTIONED_BY` | REFERENCES, INFORMS, SUPPLEMENTS |

Edge properties: `{since, until?, confidence?, weight?, mode?, t_valid, t_invalid?, t_created, t_expired?}` —
Graphiti 4-timestamp bi-temporal model; `mode` carries collapsed v0.2 nuance.

## Observation kinds K (12)

| Kind | Absorbs from v0.2 | Rule |
|---|---|---|
| `fact` | fact, status(durable) | verifiable |
| `hypothesis` | hypothesis | note confidence < 0.7 |
| `decision` | decision | immutable once committed |
| `constraint` | constraint, requirement, rule, boundary | hard rule |
| `preference` | preference, tool-policy | subjective |
| `lesson` | lesson, insight, technique, principle (grade via `weight`) | provenance to producing case |
| `procedure` | procedure, process, checklist | promotable to procedures/ if verified |
| `risk` | risk, gotcha, security, drift | |
| `question` | question | marks a gap |
| `status` | status(transient), short/mid/long_term (via `horizon:`) | transient; consolidation may prune |
| `contradiction` | contradiction | system-generated only |
| `deprecated` | deprecated | excluded from default queries |

## Tags

Namespaced only: `domain/*`, `project/*`, `status/*`, `source/*`, `machine/*`. Registry-enforced
(registry lives in `_meta/registries/tags.md`); free-form tags rejected at the API.

## v0.2 → v1.0 migration shims

Full mapping tables above are the shim. Unmapped v0.2 rel types (COLLABORATES_WITH, SPAWNS/SPAWNED_BY,
PLANS_FOR/PLANNED_BY, PROPOSES_CHANGE_TO) → `MENTIONS` with `mode:` preserving the original name;
migration report lists each downgrade for human review.
