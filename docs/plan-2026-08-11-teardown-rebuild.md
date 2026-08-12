# Tear-Down & Rebuild: Self-Evolving Agentic Knowledge Vault for a Software Team

**Status:** COMPLETE — all 5 research agents reported (SOTA KG, self-learning, C# MAF/MCP, jcodemunch, kb post-mortem); full reports in appendix.

## Context

Prior build (vault-mcp + vault-curator) drifted compliance-heavy ("HR notebook"). User verdict: tear down, rebuild as a **better reworked master-kb** — a self-evolving agentic knowledge base for a software team. Knowledge spans: domain, project, code, concepts, documents. Curator must master ontologies, graph theory, formal search, hybrid RAG, semantic ingestion, embeddings. Memory model: short/long-term, episodic, hierarchical. Deliverables demanded: ≥4 formal-structure propositions, continued-maintenance procedures, full C# MAF agents-as-MCP-tools, living neural knowledge vault, jcodemunch-mirroring agent.

## Crossover baseline (from kb master-kb `_`-folders — read 2026-08-11)

Existing master-kb `_governance` is substantial and largely REUSABLE (this is the "not much crosses over from the vault-kit, but plenty crosses over from kb" surprise):

- **Ontology v0.2** (`_governance/ontology.md`): 15 entity classes (incl. Agent, Instruction), ~40 SCREAMING_SNAKE rel types w/ inverses + rejection list (anti-dilution), 36 observation kinds w/ semantics + confidence rules. Versioned, evolution-gated.
- **Taxonomy** (`_governance/taxonomy.md`): flat class folders, frontmatter schema (provenance list, confidence, status, kb_version, cascade_role primer|protocol|operation|retrospective, machine), four-document cascade, bilateral failure/excellence corpus.
- **Evolution rules** (`evolution-rules.md`): t→t+1 monotonic gain, semver schema (PATCH/MINOR/MAJOR + shims), contradiction lifecycle, guard rails E-G1..E-G5, feedback-driven evolution proposals (non-coercive).
- **Three-Tier Memory** (Letta-inspired): T1 working (`observations/session-context/`), T2 semantic (entity folders, Neo4j-projected), T3 archival (status-based, never deleted). Promotion daemon gate Δ>ε=0.35.
- **Staleness policy**: per-class MUA + exponential confidence decay λ (half-life per class), weekly sweeper, confidence floor 0.3, hard-prune criteria.
- **Quality gates G-1..G-7** (kb-curator write gates): BNF frontmatter, class registered, hypothesis ceiling, dedup (permalink+semantic 0.85), provenance, orphan check, Neo4j mirror projection.
- **Playbooks**: add/merge/split/deprecate entity, evolve-ontology, frontmatter-normalization, self-healing runbook.
- **Neo4j mirror**: schema.cypher + schema.graphql + kb_mirror.py (<docker-host>:5604/5605, container graphrag-neo4j).
- **Non-negotiables**: C-1 ports >10000, C-2 config SSoT, C-3 registry-before-choice.
- `_versions/` semver history v0.1→0.2 (append-only). `__handover/` = inbox drops (incl. jCodeMunch plugin note, copilot hooks/otel tutorials).

Known weaknesses to fix in rebuild (evidence in kb itself): vocabulary noncompliance 345/598 at v0.2 audit; obs-kind sprawl (36, some overlapping); rel-type sprawl (40, agents can't hold in head); Neo4j mirror manual/optional; no embedding pipeline in gates (semantic dedup aspirational); working-memory tier under-used; no code-graph integration.

## What crosses over from the vault-kit repo (assess: little)

- TBD after design; candidates: esbuild-bundled node:sqlite FTS5 MCP server skeleton, layered write-fence pattern (hook + git pre-commit), gate-server propose/accept pattern, deploy scripts shape. Compliance ontology (GLBA/17a-4, clearance, retention) DIES.

## Locked user decisions (2026-08-11)

1. **Fresh system replacing basic-memory** with custom tooling. Borrow kb's best features; better-invented/evolving/curated; richer agentic involvement. **Incremental**: start small+simple, nail core fundamentals out of the gate. Includes a research+discussion spike on kb's holes: broken relations, orphans, bulk-loading skew on few concepts, empty classes/notes (post-mortem agent running).
2. **C# MAF end-to-end** — curator + specialists as Microsoft Agent Framework agents exposed as MCP tools (ModelContextProtocol C# SDK).
3. **Target = different machine + team**: LMStudio + ONNX engine available (local inference legal there — no-local-models ban applies only to the original authoring Mac). **Poach neo4j-graphrag** heavily; settle appropriate vector store during design.
4. **Aggressive ontology reset** → v1.0: ~8-10 entity classes, ~12-16 core verbs (qualifiers as edge properties), ~12 obs kinds; migration shims from v0.2.

## Additional kb assets found (crossover)

- **SOTA dossier 2026-05** (`_governance/research/sota-2026-05.md`): already validates Graphiti bi-temporal invalidation, MAGMA dual-path ingestion (fast sync write / slow async enrichment), SmartVector 3-stage confidence decay (exp + feedback ±2.67x asym + access reinforcement + ripple penalty 0.15/(hop+1)), KARMA multi-agent debate for contradictions, CMA 4-layer governance (constitution/contract/adaptation/implementation), anti-patterns AP-1..AP-7. New research must go BEYOND this (it's 3 months old).
- **Protocol grammar** (I-1..I-8 + full BNF + dual-hypothesis correction logging): machine-checkable invariants — provenance, time-anchored relations, ontology-registered class, hypothesis confidence <0.7, deprecated read-exclusion, SUPERSEDES DAG, reciprocal-or-justified relations, permalink uniqueness. KEEP as constitution layer, enforce in C# tooling this time (kb's fatal flaw: gates were prose, not code).

## Research findings (checked 2026-08-11)

### A. 10 self-evolving KG systems (ranked; steal-notes)

1. **Graphiti/Zep** (arXiv:2501.13956, Apache-2.0, Neo4j) — bi-temporal 4-timestamp edges (t_valid/t_invalid/t_created/t_expired), invalidate-never-delete, hybrid semantic+BM25+traversal conflict detection, LLM-free retrieval. LongMemEval 63.8%. **Steal: the 4-timestamp schema in frontmatter + Neo4j mirror.**
2. **SAGE** (arXiv:2605.12061, NeurIPS'26) — writer↔reader closed loop: failed retrievals become extraction-repair signals. **Steal: log retrieval misses, replay as curation feedback.**
3. **TOKI** (arXiv:2606.06240) — contradiction resolution as write-time concurrency control: typed bitemporal operators (last-writer-wins / evidence-weighted / await-confirmation / per-rule policy) with provenance audit rows. **Steal: explicit resolution operator per fact class.**
4. **Cognee/memify** (Apache-2.0, MCP-native) — usage-signal edge reweighting: retrievals-that-helped strengthen links, rest decay. **Steal: cheapest self-evolution mechanism; candidate for Neo4j mirror layer.**
5. **Google OKF v0.1** (2026-06) — knowledge = markdown+YAML dir; only mandatory field `type`; links ARE edges; per-bundle `index.md` + `log.md`. **Steal: adopt conventions wholesale — highest steal-to-effort.**
6. **HAGE** (arXiv:2605.09942) — four orthogonal relation views (Semantic/Temporal/Causal/Entity) over shared nodes, query-intent-routed traversal. **Steal: 4-view edge typing without the RL.**
7. **Codebase-Memory MCP** (arXiv:2603.27277) — tree-sitter KG 158 langs, 2-pass (syntactic + LSP type-aware), SQLite + background watcher, sub-ms; 83% answer quality, 10x fewer tokens. **Steal: code-graph substrate the prose KB links into (complements jcodemunch mirror).**
8. **TGMS + MemTX** (arXiv:2607.10265 / 2607.23929) — 13 typed temporal operators as agent tools; write≠commit: staged snapshot-isolated writes, beliefs mature tentative→action-safe, retraction cascades typed repair. **Steal: trace-grounded verification + staged-commit write path.**
9. **AutoSchemaKG** (ACL'26, HKUST) — schema INDUCED from corpus (92% alignment w/ human schemas), events first-class. **Steal: induce ontology from existing notes, freeze top-N, re-induce quarterly with human gate.**
10. **FadeMem + consolidation-without-identity-drift** (arXiv:2601.18642 / 2607.01988) — differential decay by relevance×frequency×recency; **drift guard: consolidation forbidden from mutating anchor/protocol notes.**

Key negatives: Mem0 dropped its graph module in v3 (PR#4805, 2026-04) — do NOT build on Mem0ᵍ. GraphRAG/LightRAG/HippoRAG = retrieval reference but treat graph as static middleware.

**Converged core (unanimous across systems):** bi-temporal 4-timestamp; invalidate-never-delete; contradiction = write-time typed operator; write≠commit (staged belief lifecycle); schema induced + human-gated; episodes/events first-class; retrieval feedback rewrites edge weights (THE 2026 delta); guarded decay with anchor exemption; typed multi-relational edges; markdown+links legitimate substrate with graph DB as derived mirror.

### B. 10 agentic self-learning loops (ranked; KB mapping)

1. **ACE — Agentic Context Engineering** (arXiv:2510.04618, ICLR'26) — Generator→Reflector→Curator emits append-only *delta bullets* into structured playbooks; never full rewrite (kills brevity bias + context collapse). +10.6% agents. **KB = the playbook.**
2. **Reflexion** (2303.11366) + FORGE (2605.16233) — failure → typed verbal critique artifact. **Retrospective note per incident; cheapest, highest signal/token.**
3. **AWM + Memp** (2409.07429 ICML'25 / 2508.06433) — mine repeated successful action subsequences → named parameterized workflow notes; Build/Retrieve/Update lifecycle. **Pattern seen ≥3x → promoted procedure note.**
4. **ExpeL** (2308.10144) — dual retrieval channels: exemplar cases + abstracted insights, provenance-linked.
5. **Dynamic Cheatsheet** (2504.07952, EACL'26) + Buffer of Thoughts — persistent per-domain hot cheatsheet; GPT-4o Game-of-24 10%→99%.
6. **Voyager** (2305.16291) — verification gate: only artifacts that PASS A TEST enter the skill library. **`verified: true` frontmatter; curator refuses unverified promotion.**
7. **HippoRAG 2** (2502.14802, ICML'25) — retrieval = seed query-matched notes, walk link graph with Personalized PageRank; not flat embedding top-k.
8. **A-MEM** (2502.12110, NeurIPS'25) — Zettelkasten: on every write, link + retro-update linked notes' attributes ("memory evolution"). **Near-literal for our substrate.**
9. **Sleep-time compute / consolidation daemon** (2504.13171, Letta; EverMemOS) — idle-time agent promotes episodic→semantic, re-summarizes, prunes. **The cron curator daemon — makes loops 1-8 durable.**
10. **MemRL / Evo-Memory** (2601.03192 / 2511.20857) — utility scores per memory updated from outcome feedback; usage decay ~1.5x recent boost → 0.3x unused. **Frontmatter uses/wins/losses/last_used.**

**Composed stack:** Read path: playbook (hot) → procedures → graph-walk into cases/insights. Write path: capture (Reflexion) → curate (ACE deltas) → promote-if-verified (AWM+Voyager) → consolidate+decay nightly (sleep-time+MemRL). Measure on replayed task streams.

### C. jcodemunch functional spec (verified from source, v1.108.155)

Python/uv tool; tree-sitter parser (2226-line lang map); SQLite WAL per-repo `{slug}.db` (~/.code-index/) with meta/checksum sidecars, byte-offset symbol spans (exact seek retrieval + drift verify); BM25+identity signals+PageRank-tiebreak ranking; RRF signal fusion (identity/lexical/semantic channels, tunable weights); optional ONNX MiniLM embeddings in-db; honesty contract verdicts (ok/low_confidence/absent/degraded + coverage + did_you_mean); plan_turn session routing (confidence→read budgets high:2/medium:5/low:10, none = stop searching); session journal + turn budget (warn 80%, auto-compact); PostToolUse auto-reindex + PreCompact snapshot hooks; SCIP + runtime-signal ingestion.

**Top-10 to mirror in the vault curator:** plan_turn analogue; unified verdict contract; outline-first reading; exact-span+drift verify; context bundle (note+links+backlinks bounded payload); RRF fusion w/ link-graph PageRank tiebreak; impact/safety checks before rename/delete (backlinks, blast radius); SQLite WAL index + incremental watcher; session journal+budget; write hooks (auto-reindex + precompact snapshot). Analytics mapping: hotspots/churn→over-edited notes, dead-code→orphans, dep-cycles→circular links, render_diagram→vault graph views.

### D. C# MAF agents-as-MCP-tools (verified 2026-08-11)

- **MAF GA 1.0 (2026-04-03), current 1.17.0** (weekly cadence). Stable: `Microsoft.Agents.AI`, `.Abstractions`, `.OpenAI`, `.Workflows[.Declarative|.Generators|.Declarative.Mcp]`. Preview: `.Hosting`, `.Anthropic`, A2A/AGUI, DevUI. TFMs net8/9/10; use .NET 8+.
- Abstractions: `AIAgent` → `ChatClientAgent` (wraps any `IChatClient`); `chatClient.AsAIAgent(...)`; sessions `CreateSessionAsync()` + `SerializeSessionAsync`; orchestrations sequential/concurrent/group-chat/handoff; graph workflows w/ `CheckpointManager`.
- **Agent → MCP tool is a first-party 2-liner**: `McpServerTool.Create(agent.AsAIFunction())` + `AddMcpServer().WithStdioServerTransport().WithTools([...])` (sample Agent_Step07_AsMcpTool). Agent Name/Description become tool name/description.
- **MCP C# SDK `ModelContextProtocol` 2.1.0** (Apache-2.0): `[McpServerToolType]`/`[McpServerTool]` + `WithToolsFromAssembly()`; `.AspNetCore` for Streamable HTTP (`MapMcp()`). 2.0 breaking: stateless HTTP default; elicitation/sampling → MRTR `InputRequiredResult` pattern.
- MAF consumes MCP tools natively: `McpClientFactory.CreateAsync(...)` → `ListToolsAsync()` → pass as `AITool`s.
- Memory: `AIContextProvider` (released `ChatHistoryMemoryProvider` over `Microsoft.Extensions.VectorData` VectorStore); workflow checkpointing; Neo4j/Redis providers listed preview but NuGet IDs unverified — plan custom provider.
- **Embeddings remote, zero local weights**: `Microsoft.Extensions.AI[.OpenAI]` 10.8.3 `IEmbeddingGenerator` against any OpenAI-compatible endpoint (LMStudio on target / ollama2 tunnel), or `OllamaSharp` 5.4.30. Vector store: `Microsoft.SemanticKernel.Connectors.SqliteVec` 1.74.0-preview (sqlite-vec) — swappable via VectorData abstraction.
- Exemplars: microsoft/agent-framework (12.7k★), modelcontextprotocol/csharp-sdk (4.5k★), microsoft/mcp (3.6k★), kernel-memory (2.2k★, research-grade), dotnet/ai-samples, rwjdk/MicrosoftAgentFrameworkSamples, microsoft/mcp-dotnet-samples.

### E. kb failure post-mortem (audited 2026-08-11, ~600-900 notes)

**Numbers**: frontmatter compliance 8/13 sampled (62%); relation-format compliance 4/13 (31%) — three relation dialects coexist; broken wikilinks 6/12 spot-checked (50%); every sampled relation one-sided; ~14 off-vocab observation kinds invented; hollow classes (person/org/goal/technology = 1 stub each) vs bulk hotspots (concept/ 90, document/ 150+, runbooks/ 38 w/ 37% .bak dupes); singular/plural folder drift (project/ vs projects/, document/ vs docs/, nested project/document/); title-case-vs-slug twin notes resolved by `-1` suffix instead of merge; ~40 .bak/conflict files indexed as notes; declared folders (relations/, _versions/ at root) never created; dissolved-subtree inbound links never rewritten. Curation is ACTIVE (25+ notes/30d) but new notes are as non-compliant as old — effort goes into writing, not gates.

**Root causes → tooling countermeasures (all bake into teamkb-mcp):**
1. Gates were prose → **validator rejects the write** (grammar in code).
2. Free-text wikilinks → **every [[target]] resolved at write time; unresolvable = reject or auto-stub**.
3. One-sided hand-typed relations → **relations are a typed API argument, not body text; backlinks computed; REL enum enforced server-side**.
4. Folder anarchy → **path computed from entity_class; folder set is a closed enum; no arbitrary folders**.
5. No dedup at create → **pre-write similarity (title+aliases+permalink); collision forces merge-or-supersede, never suffix**.
6. Sweeper was a runbook → **scheduled job that actually executes (cron/hook), writes its report back as a note**.
7. Vocabulary too large to hold → **small closed enums surfaced IN THE MCP TOOL SCHEMA so the model sees legal values at call time**.

### E2. Post-mortem v2 (formal grounding + full legacy census, 2026-08-11)

v1 was directionally right, quantitatively LOW. Extensions:
- **Legacy corpus full census (653 notes, <legacy-corpus-path>)**: 35.2% dangling wikilinks (862/2451); **53.8% orphans**; 3 relation dialects (2405 / 1249 / 64 uses); 31 duplicate slugs; 57.9% filename-dialect split; **189 distinct observation kinds** (singleton tail); relation verbs leaking into obs kinds. "The graph was never a graph — a folder of documents with decorative links."
- **Current kb worse than v1 said**: ~**120 obs kinds + ~60 predicates within ONE note type** (schema_infer over 198 notes); case-dialect predicate twins (part_of 41 vs PART_OF 21…); markdown-corrupted predicate names (`**Related**:`); 12 project identities duplicated across project/ vs projects/; class folder nested inside instance folder (project/document/).
- **Sharpened root cause**: basic-memory SHIPPED a machine gate (Picoschema + `validation: error`) — **zero schema notes were ever declared**. Not "no gate existed"; "gate never switched on."
- **Formal defect mapping** (full table in appendix report): Zaveri quality dimensions; OOPS! P11 missing domain/range + P13 missing inverse; SHACL (+ incremental revalidation arXiv:2508.00137, xpSHACL explanations); PG-Schema/PG-Keys (exclusive∧mandatory∧singleton keys); Halpin sameAs identity pathology → merge-or-distinguish gate; Galárraga completeness estimators → class-cardinality metrics job; **KGCL** (INCATools) as the typed change language for all T/P/K evolution with reverse patches.
- **Formal model adopted into constitution** (appendix C of v2 report): typed property graph G=(V,E,τ,π,ω); closed sets T (node types), P (predicates w/ signatures σ(p)=(dom,rng) + partial involution inv), K (obs kinds); constraints C1-C8 (type closure w/ derived path, permalink key, signature check, referential integrity, server-computed inverse closure, vocabulary closure, scope predicate excluding junk, class non-vacuity |τ⁻¹(t)|≥2); monotone invariants I1-I4 (orphans non-increasing, shape violations non-increasing CI gate, KGCL-only evolution, similarity-θ identity discipline w/ explicit distinct_from).
- Design consequence: enums in tool schemas + server-computed inverses/paths make most of the failure inventory **structurally unrepresentable**, not merely rejected.
- Tooling note: codemunch could not index the legacy corpus (hosted server, path invisible) — census done via read-only find/python; codemunch reserved for code-side integration (M5).

## Four formal-structure propositions

All four share the settled core (non-negotiable, from research convergence): markdown+frontmatter canonical / graph DB derived; bi-temporal 4 timestamps; invalidate-never-delete; write≠commit (staged proposal → validated → committed); provenance mandatory; typed edges with computed (not authored) inverses — **authored reciprocity (old I-7) is abolished**: direction stored once, backlinks derived by tooling (kills kb's #1 breakage class).

### P1 — Stratified Memory Organism (folders = memory strata) — RECOMMENDED

```
team-kb/
├── _meta/            # constitution, ontology, versions, registries (CMA constitution+contract layers)
├── episodes/         # EPISODIC: immutable session/event/incident records, append-only, auto-captured
├── knowledge/        # SEMANTIC: entity notes by class subfolder (person/ org/ project/ concept/ …)
├── playbooks/        # PROCEDURAL-hot: ACE delta-bullet playbooks per domain + per-domain cheatsheets
├── procedures/       # PROCEDURAL-cold: verified, parameterized workflow notes (AWM/Voyager-gated)
├── hubs/             # HIERARCHICAL: auto-regenerated community/index notes (curator-owned)
└── inbox/            # working memory: untriaged capture, quarantined from retrieval
```
Lifecycle encoded in location; tier promotion = curator move with audit. Consolidation daemon: episodes→knowledge/playbooks nightly. Identity-drift guard: `_meta/` + anchor notes exempt from consolidation edits. **Why recommended**: maps 1:1 onto the composed self-learning stack (capture→curate→promote→consolidate); folder = retrieval scope = decay policy; simplest mental model for humans AND agents.

### P2 — Graph-native flat corpus

Flat entity folders (kb v0.2 shape), all structure in edges; HAGE 4-view edge typing (semantic/temporal/causal/entity); Neo4j is primary query surface, markdown a serialization. Strongest analytics, weakest human ergonomics; repeats kb's failure (structure lived in prose+links nobody enforced).

### P3 — Event-sourced ledger

Append-only episode log is THE source of truth; every semantic note is a rebuildable projection (TGMS/MemTX end-state). Perfect audit + time travel; highest complexity; projection lag; overkill for v1. **Adopt its write-ahead staging only.**

### P4 — Federated OKF bundles

Per-domain bundles (project/codebase/domain) each self-contained: `index.md` + `log.md` + notes; ontology induced per bundle (AutoSchemaKG), aligned globally quarterly. Most incremental, portable; risks re-creating silos/Bridge-Protocol problems kb already solved.

**Recommendation: P1 chassis + P3's staged write-ahead episode capture + P4's per-bundle index.md/log.md conventions inside knowledge/ subtrees.**

## Ontology v1.0 (aggressive reset)

- **Entity classes (10)**: Person, Org, Project, Codebase, Technology, Artifact (doc/tool/service), Concept, Event (absorbs Incident via `kind:`), Decision, Goal, Agent. (Exactly at AP-1 boundary; Instruction becomes a procedure note, not a class.)
- **Core verbs (14, direction stored once, inverses computed)**: IS_A, PART_OF, DEPENDS_ON, USES, CAUSES, PRECEDES, SUPERSEDES, DERIVES_FROM, DESCRIBES, GOVERNS, OWNS, ADDRESSES, CONTRADICTS, MENTIONS. Nuance moves to edge properties: `{mode: implements|distills|induces, since, until, confidence, weight}`. v0.2's 40 types map down via shim table.
- **Observation kinds (12)**: fact, hypothesis, decision, constraint, preference, lesson (absorbs insight/technique/principle via `weight`), procedure (absorbs process/checklist), risk (absorbs gotcha/security), question, status, contradiction, deprecated.
- **Tags**: namespaced only (`domain/x`, `project/x`, `status/x`, `source/x`) — registry-enforced (C-3), free-form tags rejected at gate.
- Schema evolution: keep semver + E-G guard rails; ADD AutoSchemaKG quarterly re-induction proposing (never auto-applying) vocabulary changes.

## Memory model (short/long-term, episodic, hierarchical)

| Tier | Location | Write path | Retrieval | Decay |
|---|---|---|---|---|
| Working (short-term) | inbox/ + session journal | any agent, ungated | excluded from default search | session end → episode or discard |
| Episodic | episodes/ | auto-capture, append-only, immutable | temporal + provenance queries | FadeMem differential decay; never deleted |
| Semantic (long-term) | knowledge/ | curator-gated staged commit | hybrid RRF + PPR graph walk | per-class half-life + utility scores |
| Procedural | playbooks/ (hot) + procedures/ (verified) | ACE deltas / Voyager gate | loaded-first (cheatsheet), then on-demand | usage-based (MemRL uses/wins/losses) |
| Hierarchical | hubs/ | curator-regenerated (community detection) | entry points, progressive disclosure | rebuilt, not decayed |

## Continued-maintenance procedures (all tooling-enforced, not prose)

1. **Nightly consolidation** (sleep-time agent): episodes→semantic/playbook deltas; drift guard on anchors.
2. **Weekly sweep**: staleness (per-class MUA + decay), utility decay, orphan queue (auto-adopt via link suggestions or archive), broken-link scan (should be ~impossible: computed backlinks + referential check at commit).
3. **Contradiction handling at WRITE time**: TOKI operator per fact class — decisions=await-confirmation, benchmarks/status=last-writer-wins, findings=evidence-weighted; loser kept in audit block.
4. **Retrieval-miss replay** (SAGE): failed retrievals logged → weekly curation repair batch.
5. **Usage reweighting** (Cognee): retrievals-that-helped bump edge weights + note utility; feeds hub regeneration + decay.
6. **Quarterly schema re-induction** (AutoSchemaKG) → evolution proposals → human gate.
7. **Hub regeneration**: community detection on link graph → hubs/ rebuilt; empty-class and bulk-skew report to operator.
8. **Session hooks**: sessionStart primes (constitution + relevant playbook + cheatsheet); postWrite auto-reindex; preCompact snapshot→episode.

## C# MAF architecture (agents-as-MCP-tools)

One .NET solution, two processes:
- **`teamkb-mcp`** (MCP server, stdio+HTTP): read/search surface + staged-write gateway. Tools follow jcodemunch patterns: `plan_turn`-style router w/ confidence+read-budget, verdict contract (ok/low_confidence/absent/degraded + coverage + did_you_mean), outline-first note reading, context bundles, RRF hybrid search (FTS + vectors + PPR link-walk), impact checks (backlinks/blast-radius/safe-delete), `propose`/`commit` staged writes running grammar gates G-1..G-7 in code.
- **`teamkb-agents`** (MAF host): specialist agents each exposed as an MCP tool — Curator (gatekeeper), Ontologist (schema induction+evolution), Consolidator (sleep-time), Sweeper, Contradiction-Resolver, Librarian (hubs/communities), **Code-Cartographer (jcodemunch mirror: indexes team codebases, links code symbols ↔ knowledge notes)**.
- Storage: SQLite WAL (FTS5 + vector table) as index; markdown canonical; Neo4j mirror (poach neo4j-graphrag pipeline patterns: KG builder, retrievers vector/hybrid/text2cypher) for analytics/PPR/GDS.
- Embeddings: target machine runs LMStudio/ONNX — IEmbeddingGenerator against local OpenAI-compatible endpoint; model pinned in `.env` (C-2).
- (exact packages/versions: pending research-maf agent → section D)

## Phasing (start small, nail fundamentals)

- **M0 Core**: repo scaffold, _meta constitution (I-1..I-8 rev2: I-7 replaced by computed backlinks), grammar validator, staged-commit write tool, FTS search, episode capture. USABLE ALONE.
- **M1 Retrieval**: embeddings + RRF hybrid + verdict contract + plan_turn router.
- **M2 Graph**: Neo4j mirror + PPR retrieval + link analytics + hubs.
- **M3 Self-learning**: consolidation daemon, decay+utility, contradiction operators, retrieval-miss replay.
- **M4 Specialists**: ontologist (induction), sweeper, librarian, full MAF agents-as-tools.
- **M5 Code integration**: Code-Cartographer + codebase↔knowledge linking.

## Execution scope on approval (first tranche)

1. **File the research**: create `docs/research/2026-08-11-*` dossier notes (5 full reports, appendix below) in the rebuild repo + stage to kb per deferred-sync if kb write intended.
2. **Author the v1.0 constitution set** (`_meta/`): ontology v1.0 (10 classes/14 verbs/12 obs kinds + v0.2 shim table), grammar+invariants rev2 (I-7 → computed backlinks), **formal appendix from pmv2: typed property graph G=(V,E,τ,π,ω), constraints C1-C8 as validatable shapes, monotone invariants I1-I4, KGCL-governed T/P/K evolution**, memory-model spec, maintenance-procedures spec, contradiction-operator table.
3. **Scaffold M0** (.NET solution): `teamkb-mcp` (ModelContextProtocol 2.1.0, stdio) with: staged `propose`/`commit` write path running gates in code, path-computed-from-class, write-time link resolution, dedup-at-create, closed enums in tool schemas, FTS5 search, episode capture. Smoke tests proving each post-mortem countermeasure rejects its failure case.
4. M1+ per phasing table (separate approvals).

## Verification

- M0 smoke suite: each of the 7 post-mortem failure classes replayed against `teamkb-mcp` → write REJECTED with actionable error (the kb corpus provides real fixture material: `type: note` notes, bare-slug links, off-vocab kinds, twin titles).
- Ontology shim: run v0.2→v1.0 mapping over a sample of existing kb notes, zero unmapped rel-types/obs-kinds (or explicit rejection list).
- MCP conformance: server handshake + tool listing via MCP inspector; agent-as-tool roundtrip once MAF host lands (M4).

---

# APPENDIX — Full research reports (verbatim, checked 2026-08-11)

To be filed as research dossier notes on execution.


## R1 — Self-evolving KG construction (agent: research-kg)

RESEARCH REPORT — Self-evolving KG construction & agentic memory for SE teams. All sources checked 2026-08-11. Caveat: entries built from search-result snippets + abstract pages; mechanism claims marked (abs) are abstract-level, not full-text verified.

# Ranked 10

**1. Graphiti / Zep (temporal KG)** — arXiv:2501.13956 (Jan 2025) | github.com/getzep/graphiti | neo4j.com/blog/developer/graphiti-knowledge-graph-memory/
Bi-temporal edges: t_valid/t_invalid (world time) + t_created/t_expired (ingest time). Episode → LLM extract → hybrid (semantic+BM25+traversal) conflict detection → contradicting edge gets t_invalid stamp, never deleted. Auto-ontology with node dedup; custom entity/edge types as Pydantic models. Retrieval does zero LLM calls. LongMemEval 63.8% (GPT-4o) vs Mem0 49.0%. STEAL: the 4-timestamp schema + invalidate-don't-delete rule — maps directly onto markdown frontmatter fields plus Neo4j mirror. Production OSS, Apache-2.0, Python, Neo4j/FalkorDB. Strongest temporal modeling in the field.

**2. SAGE — Self-Evolving Agentic Graph-Memory Engine** — arXiv:2605.12061 (May 2026, NeurIPS 2026) | github.com/aFastHero/sage_self_evolving_graph_memory
Two coupled roles: memory *writer* incrementally constructs graph memory from interaction history; Graph-Foundation-Model memory *reader* feeds retrieval outcomes back as training signal to the writer (abs). Explicitly attacks the "GraphRAG treats graph as static retrieval middleware" failure. Gains on multi-hop QA, open-domain retrieval, long-term agent-memory benchmarks. STEAL: closed writer↔reader loop — every retrieval that failed to recover an evidence chain becomes a repair instruction for extraction. For a team KB: log which notes retrieval *should* have surfaced, replay as extraction feedback. Research-grade code only.

**3. TOKI — bitemporal operator algebra for contradiction resolution** — arXiv:2606.06240 (Jun 2026, HKUST)
Reframes contradiction resolution as WRITE-TIME CONCURRENCY CONTROL. Types the four production heuristics — last-writer-wins, evidence-weighted merge, await-confirmation, per-rule policy — as one family of bitemporal operators over a dual-row schema, each with a declared isolation precondition and a provenance annotation preserving the losing fact in an audit row. 43pp with proofs. STEAL: stop hand-waving "the agent updates the note." Pick an explicit resolution operator per fact class (decisions = await-confirmation; benchmarks = last-writer-wins; incident findings = evidence-weighted) and keep the superseded claim in an audit block. Spec, no production impl.

**4. Cognee (memify)** — cognee.ai/blog/guides/ai-coding-agent-persistent-codebase-memory | particula.tech/blog/agent-memory-frameworks-tested-mem0-zep-letta-cognee-2026 (2026)
Apache-2.0, Python, MCP-native. Pipeline: AST-level code parsing → cognify (entity/relation extraction) → hybrid graph+vector store → **memify** refinement: rated responses feed back into edge weights, prunes stale nodes, reweights by usage signals, adds derived facts. 14 retrieval modes. Claimed >1M pipelines/month, ~70 companies. STEAL: usage-signal edge reweighting is the cheapest self-evolution mechanism available — count retrievals-that-helped per link, decay the rest. Top OSS scorer on storage architecture + self-improvement in 2026 comparisons. Best off-the-shelf candidate for the Neo4j mirror layer.

**5. Google Open Knowledge Format (OKF) v0.1** — cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing | marktechpost.com/2026/06/16/... (pub. 2026-06-12)
Knowledge = directory of markdown + YAML frontmatter; only mandatory field is `type`. Concepts cross-link via plain markdown links → the directory IS the graph. Optional per-bundle `index.md` (progressive disclosure) and `log.md` (chronological change history). Full spec fits one page. STEAL: this is literally our architecture, standardized — adopt `type:` + link-as-edge + per-bundle `log.md` and the markdown KB becomes machine-portable, zero new surfaces, no vendor lock-in. Highest steal-to-effort ratio on this list.

**6. HAGE — RL-driven weighted graph evolution** — arXiv:2605.09942 (2026-05-11) | github.com/FredJiang0324/HAGE_MVPReview
Memory = four orthogonal relation views (Semantic, Temporal, Causal, Entity) over shared nodes; each edge carries a trainable relation feature vector. LLM classifier detects the query's relational intent; a QueryRouter MLP modulates matching edge dimensions; retrieval = query-conditioned sequential traversal. Edge features + router co-trained by policy-gradient RL on downstream reward (abs). STEAL: the four-view decomposition even without the RL — a team KB fact is rarely "related," it is caused-by, superseded-by, co-occurred-with, or about-same-entity. Typing edges that way makes traversal answerable. Research code.

**7. Codebase-Memory MCP** — arXiv:2603.27277 (Mar 2026) | github.com/DeusData/codebase-memory-mcp
Tree-sitter KG over 158 languages, two-pass: syntactic tree-sitter pass (defs/calls/imports) + hybrid LSP type-aware pass refining call edges via import graph and cross-file definition registry. Call-graph traversal, impact analysis, community discovery. Persisted in SQLite, kept fresh by a background watcher → sub-ms queries against the working tree. 31 repos: 83% answer quality, 10× fewer tokens, 2.1× fewer tool calls. Single static binary, zero deps. STEAL: incremental-watcher + community-detection combo; the code graph is the substrate the prose KB should link into. Production-grade OSS.

**8. TGMS + MemTX (agent-native temporal DB layer)** — TGMS arXiv:2607.10265 | MemTX arXiv:2607.23929 | also MemTxn arXiv:2607.27834 (Jul 2026)
TGMS: bi-temporal property graph exposing **13 verified temporal operators as agent tools** — typed, deterministic, bounded, cost-guarded; separates valid from transaction time so "as of T, what did we believe?" is answerable; LLM plans operator calls, system computes, and every numeric/entity/ordering/pattern claim is checked against a content-addressed execution trace. MemTX: writes staged in snapshot-isolated transactions, validate-and-commit admission, beliefs mature tentative → action-safe, irreversible tool calls gated on in-flight belief state, retraction triggers typed cascading repair of derived records. STEAL: trace-grounded answer checking, and never letting an agent's write be a commit.

**9. AutoSchemaKG** — arXiv:2505.23628 / ACL 2026 long (aclanthology.org/2026.acl-long.942/) | github.com/HKUST-KnowComp/AutoSchemaKG
No predefined schema: LLM simultaneously extracts triples AND induces the schema via conceptualization + clustering + semantic alignment. Built ATLAS from 50M+ docs → 900M+ nodes, 5.9B edges. Schema induction hits 92% semantic alignment with human-crafted schemas, zero manual intervention. Events are first-class citizens, capturing causality, temporality, procedural knowledge that entity-only graphs drop. STEAL: don't pre-declare the team ontology — induce it from existing notes, freeze the top-N concepts as the frontmatter `type:` vocabulary, re-induce quarterly. Schema evolution with a human gate. OSS, Python.

**10. FadeMem + Episodic→Semantic Consolidation** — FadeMem arXiv:2601.18642 (Jan 2026) | Episodic-to-Semantic Consolidation Without Identity Drift arXiv:2607.01988 (Jul 2026)
FadeMem: differential decay rates per memory, modulated by semantic relevance × access frequency × temporal pattern — biologically-inspired forgetting for cost control. The consolidation paper attaches an explicit forgetting curve so older un-rehearsed memories decay while episodic traces are promoted into semantic abstractions, with an identity-drift guard preventing consolidation from rewriting who/what the agent is. STEAL: the drift guard. Session logs (episodic) → distilled protocol notes (semantic) is the right pipeline, but consolidation must be forbidden from mutating anchor/protocol notes.

## Runners-up (evaluated, ranked out)
- HippoRAG 2 / LightRAG / MS GraphRAG — still the retrieval-mechanism reference (PPR seeds, dual-level retriever + incremental index patches, community summaries) but all treat the graph as static middleware. Survey: arXiv:2506.05690.
- **Mem0 — dropped its graph module entirely in v3** (commit a488e190, PR #4805, merged 2026-04-14). Do NOT build on Mem0ᵍ.
- Letta / MemGPT — OS-style RAM/disk paging; best for stateful runtimes, not KG construction.
- Structurally Aligned Subtask-Level Memory for SE Agents — arXiv:2602.21611 (+4.7pp mean Pass@1 SWE-bench Verified; memory keyed to functional decomposition, not task instance).
- Survey list: github.com/DEEP-PolyU/Awesome-GraphMemory.

# Synthesis — the converged proven core (10 lines)
1. Bi-temporal is settled. Valid-time vs transaction-time, 4 timestamps. Graphiti, TOKI, TGMS, MemTX land here independently.
2. Invalidate, never delete. Contradiction = stamp t_invalid + keep the loser in an audit row. Unanimous.
3. Contradiction handling is a WRITE-time concern, not a retrieval hack — declare the resolution operator and its isolation level per fact class.
4. Write ≠ commit. Staged, validated, provenance-carrying belief lifecycle before a fact becomes action-safe.
5. Schema is induced, not declared — LLM co-extracts triples and schema; humans gate the vocabulary.
6. Events/episodes are first-class nodes, not just entities — that's where causality and procedure live.
7. Retrieval feedback rewrites the graph. This is THE 2026 delta: edge weights from usage (Cognee), from RL reward (HAGE), from failed evidence chains (SAGE).
8. Decay is required and must be guarded — differential forgetting by relevance×frequency×recency, with anchor/protocol notes exempt from consolidation drift.
9. Typed multi-relational edges beat one "related" edge — semantic / temporal / causal / entity views over shared nodes.
10. Markdown + frontmatter + links is now a legitimate substrate (OKF v0.1); the graph DB is a mirror/index, not the source of truth — exactly the markdown+MCP+optional-Neo4j shape.

RECOMMENDED STEAL-STACK: OKF frontmatter conventions (`type:`, `log.md`) → Graphiti 4-timestamp bi-temporal fields → TOKI operator-per-fact-class resolution → Cognee-style usage reweighting → FadeMem decay with protocol-note exemption → Codebase-Memory MCP as the code-side substrate the prose links into.

## R2 — Agentic self-learning loops (agent: research-selflearn)

# 10 most proven no-weight-update agentic self-learning loops (current 2026-08-11)

Rank = replicated gain × durability of written artifact × fit to a markdown KB + curator agent. Caveat: 26xx arXiv IDs are fresh preprints — promising, not settled.

**1. ACE — Agentic Context Engineering** (arXiv 2510.04618, Oct 2025; ICLR 2026)
Generator runs task → Reflector diffs trajectory vs outcome → Curator emits *delta bullets* (append/edit, never full rewrite) into a structured "playbook"; grow-and-refine dedups. Retrieval: playbook loaded section-scoped at task start. +10.6% agents, +8.6% finance; ReAct+ACE matched IBM CUGA on AppWorld using DeepSeek-V3.1, +8.4% TGC with online adaptation. Explicitly kills *brevity bias* and *context collapse* — the two failure modes that destroy naive "summarize your notes" curators.
KB map: the KB *is* the playbook. Curator writes atomic delta bullets with IDs into topic notes; never regenerates a note wholesale.

**2. Reflexion — verbal RL** (arXiv 2303.11366, 2023; still the substrate)
Task fails → self-generated verbal critique → episodic buffer → prepended next attempt. 91% HumanEval pass@1 (GPT-4 baseline 80%). 2026 descendant FORGE (2605.16233) converts failed trajectories into *typed* artifacts — Rules, Examples, Mixed — via population broadcast.
KB map: note type `retrospective`/`failure-mode`, one per incident, typed rule-vs-example. Cheapest loop, highest signal per token.

**3. AWM — Agent Workflow Memory** (arXiv 2409.07429, ICML 2025) + **Memp** (2508.06433)
Mine repeated action subsequences from successful trajectories → induce named, parameterized *workflow* → inject relevant ones; workflows compose on earlier workflows. +24.6% rel. Mind2Web, +51.1% rel. WebArena, fewer steps; +8.9→14.0 abs. as train/test gap widens. Memp adds the Build/Retrieve/**Update** lifecycle for procedural memory.
KB map: **procedure notes** (protocols, skills, runbooks). Curator promotes any pattern seen ≥N times into a named procedure.

**4. ExpeL — experiential learner** (arXiv 2308.10144, AAAI 2024)
Pool successes+failures → cross-task abstraction into NL *insights* (guidelines/constraints) → test time recalls top-k similar trajectories **plus** insights. Two retrieval channels (exemplar + rule) is the durable idea; still the standard 2026 baseline. Related: CBR-for-LLM-agents review (2504.06943) — retrieve/reuse/revise/retain.
KB map: `insight` notes linked to the `case` notes that produced them. Provenance link mandatory.

**5. Dynamic Cheatsheet** (arXiv 2504.07952; EACL 2026) + **Buffer of Thoughts** (NeurIPS 2024)
After each problem the model rewrites a persistent cheatsheet of strategies/code snippets; DC-RS retrieves similar past items first. No labels, no human feedback. GPT-4o Game-of-24 10%→99%; Claude 3.5 Sonnet AIME accuracy >2×. BoT's meta-buffer generalizes to reusable *thought templates* (+11% Game of 24, +51% Checkmate-in-One).
KB map: a short **hot cheatsheet note per domain**, distinct from the deep archive. Templates as `pattern` notes.

**6. Voyager — verified skill library + auto-curriculum** (arXiv 2305.16291, 2023)
Curriculum proposes task → write executable code → **environment verification gate** → only verified code enters the skill library, indexed by embedded docstring → retrieved and composed later. 3.3× more items, 15.3× faster tech-tree, zero-shot transfer to new worlds. Lesson: artifacts must pass a test before entering the KB.
KB map: skills/scripts dir with `verified: true` frontmatter; curator refuses unverified promotion.

**7. HippoRAG 2 — Personalized-PageRank graph memory** (arXiv 2502.14802, ICML 2025)
Extract triples → dual-node KG (passages + phrases) → query seeds PPR; LLM filters irrelevant triples online. +7 F1 associative/multi-hop over best embedding retriever, better sense-making, fewer tokens. Framed as *non-parametric continual learning*. RAPTOR (2401.18059) = cheaper hierarchical-summary cousin.
KB map: the wikilink graph is the KG. Retrieve by seeding on query-matched notes and walking backlinks with PPR weighting — not flat embedding top-k.

**8. A-MEM — Zettelkasten agentic memory** (arXiv 2502.12110, NeurIPS 2025)
Each memory becomes a structured note (context, keywords, tags) → agent finds relevant historical notes and writes links → **linking retro-updates the linked notes' attributes** (memory evolution). Beat SOTA baselines across six foundation models. Only mechanism where writing a note *improves old notes*.
KB map: near-literal for Obsidian/basic-memory. On every write: link, then revise what you linked to.

**9. Sleep-time compute / episodic→semantic consolidation** (arXiv 2504.13171, 2025; Letta; EverMemOS 2601.02163; AutoDream 2026)
Idle-time background agent re-reads raw episodic traces, clusters, promotes repeated episodes to durable semantic facts/rules, re-summarizes entities, drops the raw trace. Cuts online latency and token cost. EverMemOS stages it MemCell → MemScene → reconstructive recall.
KB map: the **curator daemon on cron**. Session logs = episodic; nightly job promotes to permanent notes and prunes. This scheduler is what makes loops 1–8 durable rather than one-shot.

**10. MemRL — utility-scored memory / RL in context space** (arXiv 2601.03192, Jan 2026) + **Evo-Memory/ReMem** (2511.20857)
Retrieved memories carry learned *utility scores* updated from outcome feedback; two-phase retrieval filters noise; usage-based decay (~1.5× recent boost → 0.3× unused) evicts dead weight. Beats SOTA on HLE, BigCodeBench, ALFWorld, LifelongAgentBench; directly targets stability-plasticity. Evo-Memory is the streaming benchmark (10+ modules, 10 datasets) to measure any of the above. Generative Agents' recency×importance×relevance (2304.03442) is the hand-tuned ancestor of this score.
KB map: frontmatter `uses`/`wins`/`losses`/`last_used`; curator demotes and archives decayed notes.

**Deliberately below the line:** MemGPT/Letta paging (infrastructure, not learning), Self-RAG/CRAG (per-query quality gate, no persisted artifact), TextGrad (optimizes prompts, not a KB), pure self-evolving curricula (weak outside embodied envs).

---

## Synthesis — 5 loops that compose into one coherent team-KB stack

1. **Reflexion capture** (#2) — every failed or notable run emits one typed retrospective note. Raw, episodic, cheap.
2. **ACE delta curation** (#1) — curator merges retrospectives as append-only delta bullets into domain playbooks. Never rewrite whole; this is what stops context collapse as the KB grows.
3. **AWM/Memp promotion with Voyager's gate** (#3 + #6) — anything recurring ≥3× becomes a named executable procedure note, and only after it passes a real check.
4. **A-MEM linking + PPR retrieval** (#8 + #7) — on write, link and retro-update neighbors; on read, seed-and-walk the wikilink graph instead of flat vector top-k.
5. **Sleep-time consolidation + utility decay** (#9 + #10) — nightly cron daemon consolidates episodic→semantic, updates per-note utility from usage/outcomes, archives decayed notes.

Read path: playbook (hot, ACE) → procedures (AWM) → graph walk into cases/insights (A-MEM/HippoRAG).
Write path: capture (Reflexion) → curate (ACE) → promote-if-verified (AWM/Voyager) → consolidate + decay nightly (sleep-time/MemRL).
Measure on Evo-Memory-style replayed task streams, not one-shot benchmarks.

Sources:
- ACE https://arxiv.org/abs/2510.04618 · ICLR'26 https://proceedings.iclr.cc/paper_files/paper/2026/file/8a94ff6f922d995d7d3f4ebf4143e442-Paper-Conference.pdf
- FORGE https://arxiv.org/abs/2605.16233 · Self-Improvements in Modern Agentic Systems: A Survey https://arxiv.org/abs/2607.13104
- AWM https://arxiv.org/abs/2409.07429 · https://github.com/zorazrw/agent-workflow-memory · Memp https://huggingface.co/papers/2508.06433
- ExpeL https://arxiv.org/pdf/2308.10144 · CBR review https://arxiv.org/pdf/2504.06943
- Dynamic Cheatsheet https://arxiv.org/abs/2504.07952 · https://github.com/suzgunmirac/dynamic-cheatsheet · BoT https://openreview.net/forum?id=ANO1i9JPtb
- Voyager https://voyager.minedojo.org/
- HippoRAG 2 https://arxiv.org/abs/2502.14802 · https://github.com/osu-nlp-group/hipporag
- A-MEM https://arxiv.org/abs/2502.12110 · https://github.com/WujiangXu/A-mem
- Sleep-time Compute https://arxiv.org/html/2504.13171v1 · https://www.letta.com/blog/sleep-time-compute/ · AI Meets Brain https://arxiv.org/pdf/2512.23343
- MemRL https://arxiv.org/abs/2601.03192 · https://github.com/MemTensor/MemRL · Evo-Memory https://arxiv.org/abs/2511.20857 · mem0 2026 state-of-agent-memory https://mem0.ai/blog/state-of-ai-agent-memory-2026

## R3 — C# MAF agents-as-MCP-tools (agent: research-maf)

REPORT NOT FOUND

## R4 — jcodemunch functional spec (agent: explore-jcodemunch)

# jcodemunch — functional spec (read-only recon, verified from source)

## Identity
`~/.local/bin/jcodemunch-mcp` → uv-tool shim → Python pkg `jcodemunch_mcp` **v1.108.155** at `~/.local/share/uv/tools/jcodemunch-mcp/lib/python3.14/site-packages/`. Siblings: `jdocmunch-mcp`, `gcm`, `munch-bench`. Source repo on disk: `<local-clone-of jgravelle/jcodemunch-mcp>` (older than installed; ARCHITECTURE.md/SPEC.md still accurate). Live MCP surface = `mcp__codemunch-<host>__*`, ~95 tools.

## Capability groups
**Indexing/lifecycle** — index_repo, index_folder, index_file, index_dependency, resolve_repo, list_repos, list_workspaces, invalidate_cache, register_edit, get_watch_status, embed_repo, import_scip, import_runtime_signal.
**Search** — search_symbols (kind/language/file_pattern/decorator filters), search_text (regex + context_lines), search_ast, search_columns (dbt/SQLMesh), find_similar_symbols, find_implementations, suggest_queries, suggest_corrections, winnow_symbols.
**Reading** — get_file_outline, get_symbol_source (exact byte-offset span + drift verify), get_context_bundle, get_ranked_context, get_file_content, get_repo_outline, get_file_tree, get_repo_map, summarize_repo, digest.
**Relationships** — find_references, check_references, find_importers, get_dependency_graph, get_dependency_cycles, get_call_hierarchy, get_class_hierarchy, get_blast_radius, get_impact_preview, get_related_symbols, check_edit_safe / check_rename_safe / check_delete_safe, get_endpoint_impact, get_signal_chains, get_cross_repo_map.
**Analytics** — get_hotspots, get_churn_rate, get_symbol_complexity, get_repo_health, health_radar, get_file_risk, get_coupling_metrics, get_architecture_metrics, get_layer_violations, find_dead_code / get_dead_code_v2, find_unused_paths, get_untested_symbols, get_decorator_census, get_extraction_candidates, plan_refactoring, get_pr_risk_profile, get_delivery_metrics, get_parity_map, get_tectonic_map, observatory, render_diagram (mermaid).
**Session** — plan_turn, announce_model / set_tool_tier, get_session_context, get_session_stats, get_session_snapshot, session_journal, turn_budget, assemble_task_context, decision_context, get_symbol_provenance, audit_agent_config, tune_weights, get_redaction_log.

## Verified internals
- **Parser**: tree-sitter. `parser/languages.py` = 2226 lines ext→lang map with disambiguation heuristics (`.m` MATLAB/ObjC, Ansible paths, OpenAPI basenames). Plus complexity.py, fqn.py, parse_cache.py, sql_preprocessor.py, hierarchy.py, imports.py.
- **Storage**: SQLite **WAL**, one `{repo_slug}.db` per repo under `~/.code-index/` (`CODE_INDEX_PATH` override). Tables: meta, symbols, files, imports, raw_cache, content_blob + branch_deltas/branch_meta, runtime_* (calls/edges/imports/columns/stack_events/redaction_log), scip_*. Sidecars: `.meta` (list without opening DB), `.checksum` SHA-256, `{slug}/` cached raw sources. Legacy `.json` indexes auto-migrate. LRU index cache w/ mtime invalidation, process locks, WAL checkpoint on shutdown. Symbols store byte offsets → exact retrieval by seek, no reparse.
- **Ranking**: BM25 over symbol fields + identity signals (exact / substring / word-overlap / signature / summary / docstring) + PageRank centrality bonus (log-scaled) as tiebreaker; bounded-heap top-k. `retrieval/signal_fusion.py` = **RRF**: `score(s) = Σ weight[c] / (k + rank(c,s))` across identity / similarity(semantic) / lexical channels; weights overridable, `tune_weights` persists.
- **Embeddings**: optional, float32 BLOBs in `symbol_embeddings` table inside the same .db (stdlib `array`, no numpy). Local ONNX all-MiniLM-L6-v2, 384-dim, ~23 MB, lazy download. ⚠️ that download breaks the authoring-Mac no-local-models rule — mirror the *interface*, not the local encoder.
- **Honesty contract** (`retrieval/verdict.py`): states `ok` / `low_confidence` / `absent` / `degraded`, with scanned counts, coverage disclosure attached on absent/degraded, `did_you_mean`, versioned heuristic pin. Legacy `negative_evidence` emitted additively.
- **Session routing**: `plan_turn` scores symbols → confidence `high|medium|low`, escalates to `none` when index says the feature doesn't exist; `max_supplementary_reads = {high:2, medium:5, low:10}`; returns recommended_symbols/files, `session_overlap` from journal, insertion-point suggestion when low/none, budget advisor at >60% used.
- **Budget** (`tools/turn_budget.py`): turn boundary inferred from inter-call gap; `record_output()` emits `budget_warning` at >80% and on exhaustion; `should_compact()` drives auto-compaction.
- **Journal** (`tools/session_journal.py`): in-memory, thread-safe, per-dict cap 5000, LRU-by-last_ts eviction; tracks reads, queries (+result counts), edits, tool-call counts, negative-evidence log.
- **Model tiering** (`tier_resolver.py`): normalizes model id (strip provider prefix, `[1m]` bracket, `-YYYYMMDD`), matches exact → glob → longest substring → `*` → `full` fallback; narrows exposed tool list.
- **Hooks** (`cli/hooks.py`): PreToolUse steers off native Grep/Read; PostToolUse auto-reindexes after Edit/Write (plus a Copilot-CLI payload adapter); PreCompact writes a session snapshot; WorktreeCreate/Remove append to `~/.claude/jcodemunch-worktrees.jsonl` (present on this machine) driving `watch-claude` incremental reindex via `watchfiles`.
- **Other**: SCIP ingestion (`evidence/scip*.py`), runtime signal ingest + OTel + redaction (`runtime/`), org rollup store + license (`org/`), retrieval extras (confidence, freshness, entropy_prune, embed_drift, provenance, query_shape, regret).

## Top 10 to mirror in a knowledge-vault curator agent
1. **plan_turn analogue** — confidence (high/medium/low/none) + hard read budget before touching any note; `none` = report the gap, stop searching.
2. **Unified verdict contract** — ok / low_confidence / absent / degraded, with scan counts + coverage + did_you_mean. Kills re-query loops.
3. **Outline-first reading** — frontmatter + heading tree before body; body only by anchor.
4. **Exact-span retrieval + drift verification** — byte offsets into cached content; detect stale index vs edited note.
5. **Context bundle** — note + links/backlinks/related as one bounded, deduped payload instead of N reads.
6. **RRF signal fusion** — identity + lexical(BM25) + semantic channels with tunable weights; centrality (PageRank on link graph) as tiebreaker.
7. **Impact/safety checks** — backlinks, blast radius, check_rename_safe/check_delete_safe before moving or deleting a note.
8. **SQLite WAL single-file index + meta/checksum sidecars + incremental mtime→hash reindex** — cheap listing, safe concurrency with a watcher.
9. **Session journal + turn budget** — track reads/queries/edits, warn at 80%, auto-compact; feeds session_overlap dedupe.
10. **Edit hooks** — PostToolUse auto-reindex on write (`register_edit`) + PreCompact snapshot so context survives compaction.

Bonus mapping: hotspots/churn → stale & over-edited notes; find_dead_code / find_unused_paths → orphan notes; get_dependency_cycles → circular link loops; render_diagram → vault graph views.

Note: one Bash call failed mid-recon with `ENOSPC ... /private/tmp/claude-503/...` — tmp pressure on the authoring Mac, retried smaller and completed. No indexing commands were run; all findings read from source.

## R5 — kb failure post-mortem (agent: kb-postmortem)

REPORT NOT FOUND


## R6 — kb failure post-mortem v2: formal grounding (agent: kb-postmortem-2)

# master-kb Post-Mortem v2 — empirical re-audit + formal grounding (read-only, 2026-08-11)

Tooling note: codemunch could NOT index the legacy corpus — both `codemunch` and `codemunch-remote` are hosted/remote and `resolve_repo <legacy-corpus-path>` returns "Path does not exist". Fell back to read-only `find`/`python3` measurement (stated as required). Current master-kb sampled via kb MCP (`list_directory`, `schema_infer`, `schema_validate`).

## A. Empirical inventory

### A1. Legacy corpus `<legacy-corpus-path>` — 653 .md, 8.2 MB, full census (not a sample)

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

