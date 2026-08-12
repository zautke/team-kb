# Ontology digest (v1.0.0 — closed sets)

## Classes (10) → folders
Event → `episodes/`; all others → `knowledge/<class-lowercase>/`:
Person, Org, Project, Codebase, Technology, Artifact, Concept, Event, Decision, Agent.

## Verbs (14) with signatures (dom → rng; blank = any)
| Verb | dom | rng | inverse (computed) |
|------|-----|-----|--------------------|
| IsA | | Concept | HAS_INSTANCE |
| PartOf | | | HAS_PART |
| DependsOn | Project, Codebase, Artifact, Technology | | REQUIRED_BY |
| Uses | | Technology, Artifact, Codebase | USED_BY |
| Causes | Event, Decision | Event, Decision, Project | CAUSED_BY |
| Precedes | Event | Event | FOLLOWS |
| Supersedes | | | SUPERSEDED_BY |
| DerivesFrom | Artifact, Concept, Decision | | SOURCE_OF |
| Describes | Artifact, Concept | | DESCRIBED_BY |
| Governs | Artifact | | GOVERNED_BY |
| Owns | Person, Org, Agent | | OWNED_BY |
| Addresses | Artifact, Decision, Project | Event, Concept | ADDRESSED_BY |
| Contradicts | | | CONTRADICTS (symmetric) |
| Mentions | | | MENTIONED_BY |

Forward relations only — never author an inverse.

## Observation kinds (12)
fact, hypothesis, decision, constraint, preference, lesson, procedure, risk,
question, status, contradiction, deprecated.
Rule: any hypothesis ⟹ note confidence < 0.7 (HYP gate).

## Tags
Closed namespaces: `domain/ project/ status/ source/ machine/`.
`kb/*` is the server-computed plane (class + status mirror) — reserved.
Registry-before-choice: register (with description) before first use.
