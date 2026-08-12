---
title: "R5 — kb failure post-mortem v1 (agent: kb-postmortem)"
type: research
status: active
created: 2026-08-11
provenance:
  - source: "session:2026-08-11-teamkb-rebuild-research"
    author: "agent:kb-postmortem"
tags: [research, rebuild, dossier-2026-08, postmortem]
---

## kb (master-kb) failure audit — findings

All read-only. Basic-memory MCP, project `master-kb`. Counts from root depth-1 + per-folder listings; folders not individually listed are extrapolated and flagged.

### 1. Corpus shape

64 root items (59 dirs). Measured counts:

| Folder | Files | Note |
|---|---|---|
| concept/ | 90 | **bulk hotspot #1** (4 `.bak`) |
| runbooks/ | 38 | **hotspot #2** (14 `.bak` — 37% dupes) |
| _governance/ | 35 | prose rules, no executor |
| instruction/ | 29 | overlaps protocols/ + document/ |
| document/ | ~150+ | listing overflowed 50 KB at depth 1 — **hotspot #3** |
| event/ | 19 | 4 lowercase-slug dupes of Title-Case notes |
| project/ + projects/ | 14 + 33 subdirs | **duplicate taxonomy** |
| protocols/ 12, service/ 9, research/ 9, decision/ 7, incident/ 6, codebase/ 5, tool/ 5, indices/ 4, notes/ 4 | | |
| **person/ 1, organization/ 1, goal/ 1, technology/ 1** | | **hollow** |

Estimated total ~600–900 notes (extrapolated). person/organization/goal/technology contain *only* their own "Entity Class — Index" stub (goal/ literally says "folder was missing from disk", created 2026-05-08, never populated). Declared taxonomy folders `relations/` and `_versions/` **do not exist at root**. The Concept class absorbed everything that didn't fit — 90 notes vs 4 across all four hollow classes.

### 2. Schema compliance (13 notes sampled, non-`_governance`)

| Check | Pass |
|---|---|
| All 9 required frontmatter fields | 8/13 (62%) |
| `type` from legal enum (`entity`/`governance`/`relation`/`observation`) | 10/13 — 3 use illegal `type: note` |
| `## Relations` section present | 11/13 (85%) |
| **All relations in `REL_TYPE :: [[target]] {since:}` form** | **4/13 (31%)** |
| Observation `[kind]` prefixes from declared vocabulary | 8/13 — off-vocab kinds found: `[install] [config] [gotcha] [internals] [project] [schema] [root-cause] [blast-radius] [mitigation] [correction] [defect] [registry] [purpose] [governance]` |

Worst offenders: `protocols/non-negotiable-no-local-large-files…` — 6 of 9 required fields missing, zero Relations section (pure orphan) despite being a machine-wide blocking protocol. `master-kb/conflict-files-obsidian-git` — Obsidian Git conflict junk committed as a KB note, 3 frontmatter fields total. Three relation dialects coexist: `REL :: [[x]] {since:}`, `REL [[x]] since:2026-05-27`, and bare `related_to [[slug]]`.

### 3. Broken relations / orphans

12 wikilink targets spot-checked by permalink → **6 broken (50%)**:

- ✗ `hybrid-rag-architecture-sota-2025-2026`, `data-enrichment-flywheel-pattern`, `jcodemunch-mcp-mastery`, `notes/developer-environment-windows` — bare-slug links with no folder prefix; **the target file exists** for at least `Data Enrichment Flywheel Pattern` but the link doesn't resolve.
- ✗ `agent-kb/operations/macos/legacy-disk-space-hub` — points into the subtree **dissolved 2026-08-02**; the refile pass never rewrote inbound links.
- ✗ `project/docker-deployment` — cited as `CAUSED ::` target from an incident; doesn't exist.

Every relation sampled was **one-sided** — no back-edge on the target. `service/the authoring Mac` has two separate `## Relations` sections appended by different sessions. Permalink/path divergence: `_governance/Master KB — Non-Negotiable…` has permalink `governance/…` (no `governance/` folder exists).

### 4. Duplication / fragmentation

- **Singular/plural drift**: `project/` vs `projects/`, `document/` vs `docs/`, `tool/` vs `tools/`. Worse: `project/document/` nested inside `project/`.
- **Same-concept twins**: `concept/Agent Specialist- Color Theory.md` + `concept/agent-specialist-color-theory.md`; same for shadcn-theming, tailwind-bridge, ui-design, excellence-corpus, two-layer-design-token-architecture, 4× in `event/`. Collision resolved by permalink suffix (`…-1`) rather than merge — a 2026-05-15 healing-audit SUPERSEDE event exists but the loser was never deleted.
- **~40+ `.md.bak` files** indexed as notes (runbooks/ alone has 14).

### 5. Recent activity (30d)

Active, not abandoned — 25+ notes touched, mostly 2026-08-06/08-10 (runbooks, service, sessions, reference). But **new notes are as non-compliant as old ones**: `conflict-files-obsidian-git` (2026-08-09) and the 2026-08-06 protocol notes carry `type: note` + missing required fields. Curation effort is going into *writing*, not into gates.

### 6. Root-cause synthesis → required tooling countermeasures

1. **Gates were prose, never code.** `quality-gates.md`, `taxonomy.md`, `protocol-grammar.md` all exist and are all ignored. → **Write-path validator that rejects the write.** Schema check in the tool, not the docs.
2. **Free-text wikilinks.** Bare slugs and dead prefixes accepted silently. → **Resolve every `[[target]]` at write time; unresolvable link = rejected write, or auto-created stub.**
3. **Relations one-sided, hand-typed.** → **Relations as a first-class typed API arg, not body text; writing A→B auto-writes B→A.** Controlled REL_TYPE enum enforced server-side.
4. **Taxonomy unenforced at the folder layer.** Singular/plural, nested duplicates, missing declared folders. → **Folder set is a closed enum derived from the ontology; `write` takes `entity_class` and computes the path. No arbitrary folders.**
5. **No dedup on create.** Title-case vs slug twins resolved by `-1` suffix. → **Pre-write similarity check on title+aliases+permalink; collision forces merge-or-supersede, never silent suffix.**
6. **Sweeper existed only as a runbook.** `_governance/playbooks/KB Self-Healing Runbook.md`, `staleness-policy.md`, "attach within 7 days" — none ran; `.bak` and conflict files accumulated. → **Scheduled job (cron/hook) that actually executes: broken-link report, orphan report, staleness decay, junk-file quarantine — with output written back as a note.**

Bonus mechanism worth designing out: **vocabulary too large to hold** — 18 observation kinds + open relation set meant agents invented ~14 off-vocab kinds. Countermeasure: small closed enum surfaced *in the tool schema* so the model sees legal values at call time.
