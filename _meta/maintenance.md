---
title: "team-kb Maintenance Procedures v1.0.0"
type: meta
kb_version: "1.0.0"
status: active
created: 2026-08-11
---

# Continued-Maintenance Procedures

Every procedure here is **executed by scheduled tooling** (cron / hooks / CI), not prose. Each run
writes its report back into the vault as an episode note (post-mortem countermeasure #6).

## 1. Nightly consolidation (Consolidator agent, sleep-time)
Episodes since last run → cluster → ACE delta bullets into playbooks → episodic→semantic promotions
via staged commit. Identity-drift guard: `_meta/` + `status/anchor` untouchable.

## 2. Weekly sweep (Sweeper agent)
- Staleness: per-class half-life decay on effective confidence; below-floor notes → `tentative`.
- Utility decay: MemRL uses/wins/losses aging; dead-weight notes → archive queue.
- Orphans: I1 makes new orphans impossible; sweep handles inherited/edge cases — suggest links
  (A-MEM) or archive.
- Junk: C7 makes junk unindexable; sweep verifies and reports.
- Broken links: C4 makes them impossible at write; sweep is the belt-and-suspenders verifier.

## 3. Contradiction operators (write-time, TOKI)

| Fact class | Operator | Behavior |
|---|---|---|
| Decision / constraint | await-confirmation | staged, human resolves; both claims visible |
| Benchmark / version / status | last-writer-wins | new claim commits, old gets t_invalid |
| Findings / lessons / facts | evidence-weighted | provenance-count + confidence merge; loser audited |
| Identity claims (who/what) | per-rule + I4 | merge-or-distinguish gate |

Losing claim always preserved with `t_invalid` in an audit block.

## 4. Retrieval-miss replay (SAGE loop, weekly)
Search verdicts `absent`/`low_confidence` that a human later resolved → repair batch: missing links,
aliases, or extraction fixes.

## 5. Usage reweighting (Cognee, continuous)
Retrievals-that-helped bump edge `weight` + note utility; feeds PPR, hub ranking, decay.

## 6. Quarterly schema re-induction (Ontologist agent, AutoSchemaKG)
Induce schema from corpus → diff vs T/P/K → KGCL evolution proposals → human gate. Never auto-applied.

## 7. Hub regeneration (Librarian agent, weekly)
Community detection on link graph → hubs/ rebuilt; report includes class-cardinality (C8), degree-Gini
(bulk-load signature), component count.

## 8. Session hooks
- sessionStart: prime with constitution digest + relevant playbook + domain cheatsheet.
- postWrite: auto-reindex (jcodemunch register_edit pattern).
- preCompact: session snapshot → episode note.
- CI (vault repo): shapes validation, I2 non-regression gate.
