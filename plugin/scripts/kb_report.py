#!/usr/bin/env python3
"""kb_report — corpus health + run stats for a team-kb vault.

Reads the vault's derived index (.teamkb.db) and, optionally, a battery/run
events.jsonl. Stdlib only. Human table by default, --json for machines.

Usage: kb_report.py -v <vault> [-e <events.jsonl>] [-j]
"""
import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import metrics_rollup  # noqa: E402  (load/rollup/aggregate reused)


def corpus_health(vault: Path) -> dict:
    db_path = vault / ".teamkb.db"
    if not db_path.exists():
        return {"error": f"no index at {db_path} — run the server once to create it"}
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    q = lambda sql, *p: db.execute(sql, p).fetchall()  # noqa: E731
    one = lambda sql, *p: q(sql, *p)[0][0]  # noqa: E731

    notes = one("SELECT count(*) FROM notes")
    by_class = dict(q("SELECT class, count(*) FROM notes GROUP BY class ORDER BY 2 DESC"))
    by_status = dict(q("SELECT status, count(*) FROM notes GROUP BY status"))
    edges = one("SELECT count(*) FROM edges")
    # I1 view: notes with no edge in either direction (anchors legitimately isolated)
    no_edges = [r[0] for r in q(
        """SELECT permalink FROM notes WHERE permalink NOT IN
             (SELECT src FROM edges UNION SELECT dst FROM edges)""")]
    # episodes/ is the immutable, retrieval-excluded tier — edge-free is normal
    # there; only edge-free notes in the semantic tiers are I1-suspect.
    orphans = [p for p in no_edges if not p.startswith("episodes/")]
    edgefree_episodes = len(no_edges) - len(orphans)
    fts_rows = one("SELECT count(*) FROM notes_fts")
    md_files = sum(1 for p in vault.rglob("*.md")
                   if "_meta" not in p.parts and not p.name.startswith("._"))
    subs = dict(q("SELECT status, count(*) FROM submissions GROUP BY status"))
    chunks = one("SELECT count(*) FROM chunks")
    chunk_vecs = one("SELECT count(*) FROM chunk_embeddings")
    doc_vecs = one("SELECT count(*) FROM doc_embeddings")
    committed_subs = one("SELECT count(*) FROM submissions WHERE status='committed'")
    meta = dict(q("SELECT key, value FROM meta"))
    tags = one("SELECT count(*) FROM tags")
    staged = one("SELECT count(*) FROM staged")
    db.close()

    return {
        "vault": str(vault),
        "db_bytes": db_path.stat().st_size,
        "notes": notes,
        "notes_by_class": by_class,
        "notes_by_status": by_status,
        "edges": edges,
        "orphan_notes": orphans,
        "edge_free_episodes": edgefree_episodes,
        "tags_registered": tags,
        "staged_proposals": staged,
        "submissions_by_status": subs,
        "chunks": chunks,
        "semantic": {
            "chunk_embeddings": chunk_vecs,
            "doc_embeddings": doc_vecs,
            "committed_submissions": committed_subs,
            "embed_model": meta.get("embed_model"),
            "embed_dim": meta.get("embed_dim"),
            "theta": meta.get("semantic_theta"),
        },
        "parity": {
            "fts_rows": fts_rows,
            "fts_vs_notes_ok": fts_rows == notes,
            "md_files": md_files,
            "md_vs_notes_ok": md_files == notes,
        },
    }


def run_stats(events_path: Path) -> dict:
    events = metrics_rollup.load(events_path)
    rows = metrics_rollup.rollup(events)
    agg = metrics_rollup.aggregate(rows, events)
    ga = [e for e in events if e.get("kind") == "ga.score"]
    gate = [e for e in events if e.get("kind") == "gate.eval"]
    return {
        "events_file": str(events_path),
        "events": len(events),
        "run_ids": sorted({e.get("run_id") for e in events if e.get("run_id")}),
        "documents": len(rows),
        "gate_evals": len(gate),
        "gate_failures": sum(len(e.get("gates_failed", [])) for e in gate),
        "ga_scores": Counter(e.get("score") for e in ga) and
                     {"n": len(ga),
                      "mean": round(sum(e.get("score", 0) for e in ga) / len(ga), 3)
                      if ga else None},
        "aggregate": agg,
    }


def render_human(h: dict, r: dict | None) -> str:
    L = []
    a = L.append
    a(f"vault: {h['vault']}   db: {h['db_bytes'] / 1024:.0f} KiB")
    a(f"notes: {h['notes']}  edges: {h['edges']}  tags: {h['tags_registered']}"
      f"  staged: {h['staged_proposals']}  chunks: {h['chunks']}")
    a("  by class : " + ", ".join(f"{k}={v}" for k, v in h["notes_by_class"].items()))
    a("  by status: " + ", ".join(f"{k}={v}" for k, v in h["notes_by_status"].items()))
    s = h["semantic"]
    a(f"semantic: model={s['embed_model']} dim={s['embed_dim']} θ={s['theta']}"
      f"  doc_vecs={s['doc_embeddings']} chunk_vecs={s['chunk_embeddings']}")
    p = h["parity"]
    a(f"parity: fts={p['fts_rows']}/{h['notes']} {'OK' if p['fts_vs_notes_ok'] else 'MISMATCH'}"
      f"  md={p['md_files']}/{h['notes']} {'OK' if p['md_vs_notes_ok'] else 'MISMATCH'}")
    a(f"orphans (semantic tiers, no edges): {len(h['orphan_notes'])}"
      + (f" — {', '.join(h['orphan_notes'][:5])}" if h["orphan_notes"] else "")
      + f"   (edge-free episodes, normal: {h['edge_free_episodes']})")
    if h["submissions_by_status"]:
        a("submissions: " + ", ".join(f"{k}={v}" for k, v in h["submissions_by_status"].items()))
    if r:
        a("")
        a(f"run stats: {r['events']} events, runs {', '.join(r['run_ids'])}")
        a(f"  documents={r['documents']}  gate_evals={r['gate_evals']}"
          f"  gate_failures={r['gate_failures']}")
        if r["ga_scores"]:
            a(f"  ga: n={r['ga_scores']['n']} mean={r['ga_scores']['mean']}")
        for phase, st in sorted(r["aggregate"].get("phases", {}).items())[:12]:
            if isinstance(st, dict) and "p50_ms" in st:
                a(f"  {phase:34s} docs={st.get('docs', '?'):>3} p50={st['p50_ms']:>7.1f}ms"
                  f" p95={st.get('p95_ms', 0):>8.1f}ms fail={st.get('failures', 0)}")
    return "\n".join(L)


def gate_trends(event_paths) -> dict:
    """T2: gate.eval aggregation across events files, by gate x day."""
    by = {}
    totals = Counter()
    for p in event_paths:
        for e in metrics_rollup.load(Path(p)):
            if e.get("kind") != "gate.eval":
                continue
            day = (e.get("ts") or "")[:10]
            for g in e.get("gates_failed", []):
                by.setdefault(day, Counter())[g] += 1
                totals[g] += 1
            by.setdefault(day, Counter())["_evals"] += 1
    return {"days": {d: dict(c) for d, c in sorted(by.items())},
            "failures_by_gate": dict(totals)}


def check_embed(vault: Path) -> dict:
    """T3: one live 3-text embed round-trip via the server's own client."""
    import time as _t
    sys.path.insert(0, str(SCRIPTS.parent / "mcp"))
    import teamkb_server as srv
    try:
        t0 = _t.perf_counter()
        vecs = srv.embed_texts(["health", "check", "probe"], srv.DOC_PREFIX,
                               phase="report.check_embed")
        return {"ok": True, "backend": srv.EMBED_BACKEND, "model": srv.EMBED_MODEL,
                "dim": len(vecs[0]),
                "latency_ms": round((_t.perf_counter() - t0) * 1000, 1)}
    except srv.EmbedError as e:
        return {"ok": False, "backend": srv.EMBED_BACKEND, "model": srv.EMBED_MODEL,
                "error": str(e)}


def session_stats(event_paths) -> dict:
    """T5: agent-usage analytics — searches per modality, absent rate, GA."""
    tools = Counter()
    verdicts = Counter()
    ga = []
    days = set()
    for p in event_paths:
        for e in metrics_rollup.load(Path(p)):
            k = e.get("kind")
            if k == "tool.end":
                tools[e.get("tool", "?")] += 1
                v = str(e.get("result_head", e.get("result", "")))[:40]
                if e.get("tool") in ("search_notes", "semantic_search", "search_by_tag"):
                    verdicts["absent" if "verdict: absent" in v else "ok"] += 1
            elif k == "ga.score":
                ga.append(e.get("score", 0))
            if e.get("ts"):
                days.add(e["ts"][:10])
    n = sum(verdicts.values())
    return {"days": sorted(days), "tool_calls": dict(tools.most_common()),
            "search_verdicts": dict(verdicts),
            "absent_rate": round(verdicts["absent"] / n, 3) if n else None,
            "ga": {"n": len(ga), "mean": round(sum(ga) / len(ga), 3)} if ga else None}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-v", "--vault", required=True)
    ap.add_argument("-e", "--events", action="append", default=None)
    ap.add_argument("-j", "--json", action="store_true")
    ap.add_argument("-g", "--gates", action="store_true",
                    help="gate-violation trends across the given events files")
    ap.add_argument("-c", "--check-embed", action="store_true",
                    help="live embed round-trip health check")
    ap.add_argument("-s", "--sessions", action="store_true",
                    help="agent-usage analytics across the given events files")
    a = ap.parse_args()

    h = corpus_health(Path(a.vault).expanduser())
    if "error" in h:
        print(h["error"], file=sys.stderr)
        return 1
    extras = {}
    if a.gates:
        extras["gates"] = gate_trends(a.events or [])
    if a.check_embed:
        extras["embed_check"] = check_embed(Path(a.vault).expanduser())
    if a.sessions:
        extras["sessions"] = session_stats(a.events or [])
    r = run_stats(Path(a.events[0]).expanduser()) if a.events else None
    if a.json:
        print(json.dumps({"health": h, "run": r, **extras}, indent=2))
    else:
        print(render_human(h, r))
        for k, v in extras.items():
            print(f"\n{k}: {json.dumps(v, indent=2)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
