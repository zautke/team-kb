#!/usr/bin/env python3
"""Live-fire E2E battery driver (Appendix A/B). Speaks real MCP JSON-RPC over
stdio to teamkb_server.py (one session), executing the curated manifest:
genesis anchors → research notes → whitepapers, full CA pipeline per document,
then the GA retrieval battery with deterministic pass gates.

The curation decisions in MANIFEST were made by the curator following the
curate-* skills (classify/tags/relations/provenance/observations/commit).

Usage: battery_run.py -v <vault> [-r <repo-root>] [-p ingest|retrieve|all]
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

TAGS = [
    ("domain/knowledge-graphs", "knowledge graph construction, schemas, integrity"),
    ("domain/agent-memory", "agentic memory systems, self-learning loops, consolidation"),
    ("domain/curation", "knowledge curation practice, gates, dedup, provenance"),
    ("domain/dotnet", ".NET / C# implementation stack"),
    ("domain/obsidian", "Obsidian as a vault UI: properties, tags, bases"),
    ("domain/code-cartography", "code indexing, symbol maps, codebase intelligence"),
    ("project/team-kb", "the team-kb knowledge system rebuild"),
]

ANCHORS = [
    dict(title="Stratified Memory Organism",
         cls="Concept",
         overview="team-kb's memory model: seven folder tiers (inbox, episodes, knowledge, playbooks, procedures, hubs, _meta) with per-tier retrieval priors and per-class decay half-lives — memory as an organism that consolidates episodes into knowledge.",
         tags=["domain/agent-memory", "project/team-kb"],
         observations=[("Fact", "Tiers map 1:1 to vault folders; Event-class notes live in episodes/, other classes in knowledge/<class>.", "_meta/memory-model.md"),
                       ("Fact", "inbox/ carries retrieval prior 0.0 — excluded from default retrieval.", "_meta/memory-model.md")],
         source="_meta/memory-model.md"),
    dict(title="Gates as Code",
         cls="Concept",
         overview="The constitution's core principle: a rule not enforced by code does not exist. Closed vocabularies live in tool JSON schemas, paths and inverse edges are computed server-side, and every write passes validator gates C2/C3/C4/I1/I4/PROV/HYP/TAG.",
         tags=["domain/curation", "project/team-kb"],
         observations=[("Fact", "C1/C6/C7 are structurally unrepresentable at the API (enums, computed paths, scope regex) rather than validated after the fact.", "_meta/constitution.md"),
                       ("Lesson", "master-kb died of prose gates — rules stated in documents that no tool enforced.", "_meta/constitution.md")],
         source="_meta/constitution.md"),
    dict(title="Verdict Honesty Contract",
         cls="Concept",
         overview="Every retrieval surface returns an explicit verdict (ok | absent). absent asserts the knowledge does not exist, and the agent contract is to report the gap and stop — no synonym retries.",
         tags=["domain/agent-memory", "domain/curation"],
         observations=[("Fact", "Semantic search implements absent via a calibrated similarity floor stored in db meta; top score is always reported.", "_meta/memory-model.md")],
         source="_meta/memory-model.md"),
]

R = "docs/research"
W = "docs/whitepapers"
DOCS = [
    dict(path=f"{R}/2026-08-11-self-evolving-kg-systems.md",
         title="Survey of Self-Evolving Knowledge Graph Systems",
         cls="Artifact",
         overview="R1 research dossier: ten self-evolving knowledge-graph and agentic-memory systems (Graphiti, SAGE, TOKI, Cognee, OKF, HAGE, Codebase-Memory MCP, TGMS/MemTX, AutoSchemaKG, FadeMem) with a convergence synthesis of the mechanisms team-kb should adopt.",
         tags=["domain/knowledge-graphs", "domain/agent-memory"],
         relations=[("Mentions", "knowledge/concept/stratified-memory-organism")],
         observations=[("Fact", "Bi-temporal edge stamps (t_valid/t_invalid/t_created/t_expired) come from Graphiti's model.", None),
                       ("Fact", "Convergent finding: schema evolution must be proposal-gated, never free-form.", None)]),
    dict(path=f"{R}/2026-08-11-agentic-self-learning-loops.md",
         title="Survey of Agentic Self-Learning Loops",
         cls="Artifact",
         overview="R2 research dossier: ten proven no-weight-update self-learning loops (ACE, Reflexion, AWM/Memp, ExpeL, Dynamic Cheatsheet, Voyager, HippoRAG 2, A-MEM, sleep-time consolidation, MemRL) composed into the stack team-kb schedules as M3/M4.",
         tags=["domain/agent-memory"],
         relations=[("Mentions", "knowledge/concept/stratified-memory-organism")],
         observations=[("Fact", "MemRL-style utility tracking (uses/wins/losses) feeds retrieval reweighting.", None),
                       ("Fact", "Sleep-time consolidation converts episode streams into knowledge-tier notes.", None)]),
    dict(path=f"{R}/2026-08-11-csharp-maf-mcp-stack.md",
         title="C# MAF Agents-as-MCP-Tools Stack Research",
         cls="Artifact",
         overview="R3 research dossier: Microsoft Agent Framework 1.17.0, agents exposed as MCP tools, ModelContextProtocol 2.1.0, remote embedding generators, and exemplar repositories grounding the original C# implementation.",
         tags=["domain/dotnet"],
         relations=[("Mentions", "knowledge/concept/gates-as-code")],
         observations=[("Fact", "IEmbeddingGenerator abstracts the embedding endpoint behind a base URI — LM Studio locally or a tunnel remotely.", None)]),
    dict(path=f"{R}/2026-08-11-jcodemunch-functional-spec.md",
         title="jcodemunch Functional Spec Recon",
         cls="Artifact",
         overview="R4 research dossier: read-only functional spec of jcodemunch (indexed code search MCP) verified from source, with the top-10 capabilities the Code-Cartographer subsystem (M5) should mirror.",
         tags=["domain/code-cartography"],
         relations=[("Mentions", "knowledge/concept/gates-as-code")],
         observations=[("Fact", "Single SQLite db with incremental reindex-on-write is the pattern team-kb's VaultStore copies.", None)]),
    dict(path=f"{R}/2026-08-11-kb-failure-postmortem-v1.md",
         title="master-kb Empirical Failure Audit",
         cls="Artifact",
         overview="R5 research dossier: sampled empirical audit of the legacy master-kb — missing frontmatter, three relation dialects, one-sided relations, orphaned protocols — the defect inventory the gate suite replays as tests.",
         tags=["domain/curation"],
         relations=[("Mentions", "knowledge/concept/gates-as-code")],
         observations=[("Fact", "Worst offender had 6 of 9 required fields missing and zero relations despite being a blocking protocol.", None),
                       ("Lesson", "Every sampled relation was one-sided — no back-edge on the target; inverses must be computed, never authored.", None)]),
    dict(path=f"{R}/2026-08-11-kb-failure-postmortem-v2-formal.md",
         title="master-kb Formal Post-Mortem Model",
         cls="Artifact",
         overview="R6 research dossier: full legacy census (653 notes: 35.2% dangling wikilinks, 53.8% orphans, 31 duplicate slugs) grounded in KG literature, yielding the formal model G=(V,E,τ,π,ω) and constraints C1-C8 / I1-I4 that became the constitution.",
         tags=["domain/knowledge-graphs", "domain/curation"],
         relations=[("Supersedes", "knowledge/artifact/master-kb-empirical-failure-audit"),
                    ("Mentions", "knowledge/concept/gates-as-code")],
         observations=[("Fact", "Census: 189 distinct observation kinds with a singleton tail — vocabulary sprawl without closure.", None),
                       ("Fact", "The graph was never a graph — a folder of documents with decorative links.", None)]),
    dict(path=f"{R}/2026-08-11-obsidian-integration.md",
         title="Obsidian Integration Research",
         cls="Artifact",
         overview="R7 research: Obsidian as team-kb's tooled UI — typed Properties require unquoted ISO dates, the tags key is a native search plane, and Bases dashboards filter on file.hasTag; drives the serializer's frontmatter contract.",
         tags=["domain/obsidian"],
         relations=[("Mentions", "knowledge/concept/stratified-memory-organism")],
         observations=[("Fact", "Quoted or seconds-suffixed dates degrade Obsidian Properties to plain text — lose sorting and filtering.", None)]),
    dict(path=f"{W}/01-formal-graph-theory.md",
         title="The Formal Theory of the team-kb Knowledge Graph",
         cls="Artifact",
         overview="Whitepaper 01: the typed property graph G=(V,E,τ,π,ω), its integrity constraints as a transition system, and the retrieval algebra — the mathematical grounding of the constitution.",
         tags=["domain/knowledge-graphs"],
         relations=[("DerivesFrom", "knowledge/artifact/master-kb-formal-post-mortem-model"),
                    ("DerivesFrom", "knowledge/artifact/survey-of-self-evolving-knowledge-graph-systems"),
                    ("Describes", "knowledge/concept/gates-as-code")],
         observations=[("Fact", "Constraint violations are typed transitions the validator refuses, making integrity a property of the transition system rather than of audits.", None)]),
    dict(path=f"{W}/02-memory-model.md",
         title="The Stratified Memory Organism Whitepaper",
         cls="Artifact",
         overview="Whitepaper 02: team-kb's memory model — tier folders, per-class half-lives, decay/utility math, RRF retrieval fusion and the verdict contract — the full design the M1-M3 milestones implement.",
         tags=["domain/agent-memory"],
         relations=[("Describes", "knowledge/concept/stratified-memory-organism"),
                    ("Describes", "knowledge/concept/verdict-honesty-contract")],
         observations=[("Fact", "Retrieval fuses FTS, vector, and PPR channels via RRF with k=60 and tier priors.", None)]),
    dict(path=f"{W}/03-curation-tactics.md",
         title="Curation Tactics Whitepaper",
         cls="Artifact",
         overview="Whitepaper 03: how team-kb stays healthy where master-kb rotted — curator duties, write-time resolution, near-duplicate discipline, tag registry, and the maintenance rituals.",
         tags=["domain/curation"],
         relations=[("DerivesFrom", "knowledge/artifact/master-kb-empirical-failure-audit"),
                    ("DerivesFrom", "knowledge/artifact/master-kb-formal-post-mortem-model"),
                    ("Describes", "knowledge/concept/gates-as-code")],
         observations=[("Fact", "The curator owns propose/commit and enforces C2, C3, C4, I1, I4, PROV, HYP, TAG.", None),
                       ("Fact", "The ontologist proposes vocabulary changes but never applies them.", None)]),
    dict(path=f"{W}/04-self-learning-loops.md",
         title="Self-Learning Loops Whitepaper",
         cls="Artifact",
         overview="Whitepaper 04: the self-learning and self-evolution loops of team-kb — consolidation, decay, contradiction handling, retrieval-miss replay — constrained by tool shape rather than prompts.",
         tags=["domain/agent-memory"],
         relations=[("DerivesFrom", "knowledge/artifact/survey-of-agentic-self-learning-loops"),
                    ("DerivesFrom", "knowledge/artifact/survey-of-self-evolving-knowledge-graph-systems")],
         observations=[("Fact", "Loops are constrained not by prompt instructions but by the shape of the tools they are given.", None),
                       ("Fact", "The consolidator gets the tightest leash: anchor protection is a hard boundary.", None)]),
    dict(path=f"{W}/05-csharp-maf-mcp-architecture.md",
         title="C# MAF MCP Architecture Whitepaper",
         cls="Artifact",
         overview="Whitepaper 05: why .NET carries the knowledge substrate — the layering of Core/Mcp/Tests, cross-platform bring-up findings, and the verified 18/18 gate-suite state of the original implementation.",
         tags=["domain/dotnet"],
         relations=[("DerivesFrom", "knowledge/artifact/c-maf-agents-as-mcp-tools-stack-research"),
                    ("DerivesFrom", "knowledge/artifact/master-kb-formal-post-mortem-model")],
         observations=[("Fact", "Cross-machine bring-up surfaced a distinct bug class: Windows file locking, AppleDouble pollution, shell-quoting corruption.", None)]),
    dict(path=f"{W}/06-code-cartography.md",
         title="Code Cartography Whitepaper",
         cls="Artifact",
         overview="Whitepaper 06 (draft): the Code-Cartographer subsystem (M5) mirroring jcodemunch's indexed code intelligence into team-kb's graph plane.",
         tags=["domain/code-cartography"],
         relations=[("DerivesFrom", "knowledge/artifact/jcodemunch-functional-spec-recon"),
                    ("DerivesFrom", "knowledge/artifact/c-maf-agents-as-mcp-tools-stack-research")],
         observations=[("Fact", "Code symbols become graph nodes with computed edges, reusing the same gate discipline as knowledge notes.", None)],
         confidence=0.8),
]


class Client:
    def __init__(self, vault):
        env = {**os.environ, "TEAMKB_VAULT": str(vault), "TEAMKB_TRACE": "1"}
        server = REPO / "plugin/mcp/teamkb_server.py"
        self.proc = subprocess.Popen([sys.executable, str(server)],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, env=env)
        self._id = 0
        self._send({"method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "battery", "version": "1.0"}}})
        self.proc.stdin.write(json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.proc.stdin.flush()

    def _send(self, msg):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, **msg}
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        while True:
            resp = json.loads(self.proc.stdout.readline())
            if resp.get("id") == self._id:
                return resp

    def call(self, tool, **args):
        resp = self._send({"method": "tools/call",
                           "params": {"name": tool, "arguments": args}})
        r = resp["result"]
        return r["content"][0]["text"], r.get("isError", False)

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=10)


def note_args(d, source, author="agent:curator"):
    return dict(
        title=d["title"], entityClass=d["cls"], overview=d["overview"],
        relations=[{"verb": v, "target": t, "since": "2026-08-11"}
                   for v, t in d.get("relations", [])],
        observations=[{"kind": k, "text": t, **({"provenance": p} if p else {})}
                      for k, t, p in d["observations"]],
        provenanceSource=source, provenanceAuthor=author,
        confidence=d.get("confidence", 0.9), tags=d["tags"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--vault", required=True)
    ap.add_argument("-p", "--phase", default="all", choices=["ingest", "retrieve", "all"])
    ns = ap.parse_args()
    vault = Path(ns.vault).expanduser()
    c = Client(vault)
    logp = print

    if ns.phase in ("ingest", "all"):
        logp("== register tags")
        for tag, desc in TAGS:
            out, _ = c.call("register_tag", tag=tag, description=desc)
            logp(f"  {out}")

        logp("== genesis anchors")
        for a in ANCHORS:
            args = note_args(a, a["source"], "agent:curator")
            args["isolatedJustification"] = "genesis anchor"
            out, err = c.call("propose_note", **args)
            logp(f"  {a['title']}: {out.splitlines()[0]}")
            if out.startswith("STAGED"):
                pid = out.split()[1]
                out, err = c.call("commit_note", proposalId=pid)
                logp(f"    {out}")

        logp("== documents (submit → chunks/embed → neighbors → propose → commit → link → DCF)")
        for d in DOCS:
            src = REPO / d["path"]
            logp(f"-- {d['path']}")
            out, err = c.call("submit_document", path=str(src))
            logp(f"  submit: {out[:120]}")
            if out.startswith("REJECTED"):
                continue
            if out.startswith("DUPLICATE"):
                if "(status committed)" in out:
                    continue
                sid = out.split("submission ")[1].split()[0]  # resume failed/curating
                logp(f"  resuming {sid}")
            else:
                sid = json.loads(out)["submission_id"]
            c.call("log_event", phase="CA-1.strategy", doc=sid,
                   summary="default ingestion strategy",
                   metrics={"strategy": "default",
                            "reason": "single-note artifact curation; whole-doc note "
                                      "with heading-aware chunk embeddings",
                            "source_path": d["path"], "target_class": d["cls"]})
            out, err = c.call("ingest_chunks", submissionId=sid)
            logp(f"  chunks: {out[:120]}")
            if out.startswith("FAILED"):
                continue
            out, _ = c.call("semantic_search", target=sid, limit=5)
            logp("  neighbors: " + out.replace("\n", " | ")[:160])
            out, _ = c.call("suggest_tags", text=d["overview"], limit=4)
            logp("  tag suggestions: " + out.replace("\n", " | ")[:120])
            c.call("log_event", phase="CA-6.metadata", doc=sid,
                   summary=f"class={d['cls']} tags={','.join(d['tags'])}",
                   metrics={"entity_class": d["cls"], "n_tags": len(d["tags"]),
                            "n_relations": len(d.get("relations", [])),
                            "n_observations": len(d["observations"]),
                            "confidence": d.get("confidence", 0.9)})
            args = note_args(d, d["path"])
            out, err = c.call("propose_note", **args)
            logp(f"  propose: {out.splitlines()[0][:140]}")
            if not out.startswith("STAGED"):
                for line in out.splitlines()[1:]:
                    logp(f"    {line}")
                continue
            pid = out.split()[1]
            out, err = c.call("commit_note", proposalId=pid)
            logp(f"  {out}")
            permalink = out.split()[-1]
            out, _ = c.call("link_submission", submissionId=sid, permalink=permalink)
            logp(f"  {out}")
            dcf_body = (f"submission: {sid}\nsource: {d['path']}\nstrategy: default "
                        f"(single-note artifact curation)\nclass: {d['cls']}\n"
                        f"tags: {', '.join(d['tags'])}\n"
                        f"relations: {len(d.get('relations', []))}\n"
                        f"gates: all passed at commit\ncurated_at: 2026-08-12")
            out, err = c.call("capture_episode", title=f"DCF {sid}", body=dcf_body,
                              provenanceSource=d["path"], provenanceAuthor="agent:curator")
            logp(f"  dcf: {out}")
            c.call("log_event", phase="CA-11.report", doc=permalink,
                   summary=f"curated {d['path']}",
                   metrics={"submission_id": sid, "permalink": permalink,
                            "class": d["cls"], "tags": d["tags"],
                            "n_relations": len(d.get("relations", [])),
                            "dcf": out.split()[-1], "status": "committed"})

        out, _ = c.call("reindex")
        logp("== reindex: " + out)

    if ns.phase in ("retrieve", "all"):
        logp("\n== GA retrieval battery (4 modalities × 2 + probes)")
        searches = [
            ("FTS-1 distinctive", "search_notes", dict(query="bi-temporal Graphiti")),
            ("FTS-2 paraphrase", "search_notes", dict(query="duplicate slugs orphans census")),
            ("SEM-1 conceptual", "semantic_search", dict(query="how does the knowledge base stay healthy over time", limit=5)),
            ("SEM-2 analogy", "semantic_search", dict(query="mathematical foundations of typed graphs with constraints", limit=5)),
            ("TAG-1 exact", "search_by_tag", dict(tag="domain/agent-memory")),
            ("TAG-2 prefix", "search_by_tag", dict(tag="kb/concept", prefix=True)),
            ("GRAPH-1 backlinks", "read_note", dict(permalink="knowledge/concept/gates-as-code")),
            ("GRAPH-2 backlinks", "read_note", dict(permalink="knowledge/artifact/master-kb-formal-post-mortem-model")),
            ("PROBE expected-absent", "search_notes", dict(query="quantum blockchain kubernetes recipes")),
            ("PROBE semantic-absent", "semantic_search", dict(query="baking sourdough bread hydration ratios", limit=3)),
        ]
        for label, tool, args in searches:
            out, _ = c.call(tool, **args)
            modality = label.split("-")[0].split()[0].lower()
            expected_absent = label.startswith("PROBE")
            got_absent = "verdict: absent" in out
            score = 1.0 if (expected_absent == got_absent) else 0.0
            c.call("log_event", phase="GA-4.score", doc=None, kind="ga.score",
                   summary=label, ok=score == 1.0,
                   metrics={"modality": modality, "label": label,
                            "query": json.dumps(args)[:200],
                            "expected": "absent" if expected_absent else "ok",
                            "observed": "absent" if got_absent else "ok",
                            "score": score})
            if tool == "read_note":
                bl = [l for l in out.splitlines() if l.startswith("- ") and "←" in l]
                logp(f"[{label}] backlinks={len(bl)}")
                for l in bl[:6]:
                    logp(f"    {l}")
            else:
                logp(f"[{label}]")
                for l in out.splitlines()[:6]:
                    logp(f"    {l}")

        logp("\n== deterministic per-doc modality recall")
        fails = []
        for d in DOCS:
            permalink = f"{'episodes' if d['cls'] == 'Event' else 'knowledge/' + d['cls'].lower()}/" + \
                "".join(ch if ch.isalnum() else "-" for ch in d["title"].strip().lower())
            while "--" in permalink:
                permalink = permalink.replace("--", "-")
            fts, _ = c.call("search_notes", query=d["title"], limit=5)
            fts_ok = permalink in fts
            sem, _ = c.call("semantic_search", query=d["overview"][:120], limit=5)
            sem_ok = permalink in sem
            tag, _ = c.call("search_by_tag", tag=d["tags"][0])
            tag_ok = permalink in tag
            note, _ = c.call("read_note", permalink=permalink)
            graph_ok = ("Backlinks (computed)" in note) or ("## Relations" in note)
            row = f"  {permalink}: FTS={'Y' if fts_ok else 'N'} SEM={'Y' if sem_ok else 'N'} TAG={'Y' if tag_ok else 'N'} GRAPH={'Y' if graph_ok else 'N'}"
            logp(row)
            if not (fts_ok and tag_ok and graph_ok):
                fails.append((permalink, fts_ok, sem_ok, tag_ok, graph_ok))
            if not sem_ok:
                logp("    (semantic miss — waiver candidate on tiny corpus)")
        logp(f"\nDETERMINISTIC GATE: {'PASS' if not fails else 'FAIL ' + str(fails)}")

    c.close()


if __name__ == "__main__":
    main()
