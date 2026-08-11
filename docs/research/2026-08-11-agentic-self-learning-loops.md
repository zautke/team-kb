---
title: "R2 — Agentic self-learning loops (agent: research-selflearn)"
type: research
status: active
created: 2026-08-11
provenance:
  - source: "session:2026-08-11-teamkb-rebuild-research"
    author: "agent:claude-fable-5"
tags: [research, rebuild, dossier-2026-08]
---

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
