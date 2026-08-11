---
title: "team-kb Constitution v1.0.0"
type: meta
kb_version: "1.0.0"
status: active
created: 2026-08-11
provenance:
  - source: "docs/research/2026-08-11-kb-failure-postmortem-v2-formal.md"
    author: "agent:claude-fable-5"
---

# team-kb Constitution v1.0.0

CMA layering: this file is the **Constitution** (immutable without MAJOR bump + human approval);
`ontology.md` is the **Contract** (KGCL-gated); agent prompts are **Adaptation**; extractor
strategies are **Implementation** (freely replaceable).

Everything below is **enforced in the write path of `teamkb-mcp`** — never prose-only. That is the
single deepest lesson of the master-kb post-mortem: the machine gate existed (Picoschema,
`validation: error`) and no shape was ever declared. Here, a rule that is not enforced by code
does not belong in this file.

## Formal model

The vault is a typed property graph `G = (V, E, τ, π, ω)`:

- `τ : V → T` — closed node-type set (10 classes, `ontology.md`)
- `E ⊆ V × P × V` — closed predicate set P (14 verbs) with signatures `σ(p) = (dom(p), rng(p))`
  and partial involution `inv : P ⇀ P`
- `π : V → Props` — mandatory `{permalink, title, type, created, modified, provenance, status, confidence}`
- `ω : V → 2^(K × Text)` — closed observation-kind set K (12 kinds)

## Integrity constraints (validated shapes; violation = rejected write)

| # | Constraint | Enforcement |
|---|---|---|
| C1 | Type closure: `τ(v) ∈ T`; `folder(v) = path(τ(v))` is **derived** | server computes path; author cannot supply one |
| C2 | Identity key: `permalink` exclusive ∧ mandatory ∧ singleton; `permalink = norm(title)` | PG-Keys-style key check at commit |
| C3 | Edge signature: `∀(u,p,v): τ(u) = dom(p) ∧ τ(v) = rng(p)` | signature table checked pre-commit |
| C4 | Referential integrity: `∀(u,p,v): v ∈ V` — no dangling link, ever | write-time resolver; reject or auto-create typed stub + open task |
| C5 | Inverse closure: `inv(p)=q ⟹ ((u,p,v) ⟺ (v,q,u))` | inverse edges computed and materialized by server; never authored |
| C6 | Vocabulary closure: `∀(k,_) ∈ ω(v): k ∈ K` | K is an enum in the tool JSON Schema |
| C7 | Scope: `v ∈ V ⟺ file(v)` is `.md` ∧ ¬ backup/conflict artifact | indexer filter `(\.bak|conflict|~|\.orig)$` |
| C8 | Class non-vacuity: `|τ⁻¹(t)| ≥ 2` or `t` marked deprecated | nightly metrics job flags |

## Monotone curation invariants (t → t+1)

| # | Invariant | Enforcement |
|---|---|---|
| I1 | `orphans(G_{t+1}) ≤ orphans(G_t)` — every write connects (≥1 resolvable edge) or carries explicit `isolated_justification` | write gate |
| I2 | `violations(G_{t+1}) ≤ violations(G_t)` over the shapes graph | CI gate on the vault repo |
| I3 | `T`, `P`, `K` change only via KGCL ops carrying a reverse patch | evolution tool refuses ad-hoc vocabulary |
| I4 | Identity discipline: no `v₁,v₂` with equal `τ` and `sim(title) > θ` unless explicit `distinct_from` assertion | ER dedup gate at create (merge-or-distinguish, never `-1` suffix) |

## Write lifecycle (write ≠ commit)

`propose(note) → validate(C1-C8, I1, I4) → staged → commit` — TGMS/MemTX pattern. A staged belief is
not retrievable by default search. Contradiction at commit is resolved by the **declared operator for
the fact class** (see `maintenance.md` operator table), and the losing claim is preserved in an audit
block with `t_invalid` stamped (invalidate, never delete — Graphiti).

## Bi-temporal record

Every edge and every fact-bearing observation carries `t_valid / t_invalid / t_created / t_expired`.
Point-in-time queries ("what did we believe as of T?") are first-class.

## Provenance

Every note ≥1 provenance entry (source + author + captured_at); every observation may carry an
inline provenance ref. Placeholder sources (TBD/TODO/unknown) rejected at C-gate level.

## Anchor protection

`_meta/**` and any note tagged `status/anchor` are **exempt from automated consolidation edits**
(FadeMem identity-drift guard). Only humans or KGCL-gated evolution touch them.
