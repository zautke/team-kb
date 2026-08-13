#!/usr/bin/env python3
"""Roll the raw event stream (.teamkb-events.jsonl) into per-document metrics:
one JSON object per ingested document, covering every runbook phase it passed
through, with timings, counts, gate results, and retrieval outcomes.

Usage: metrics_rollup.py -e <events.jsonl> [-o <metrics.jsonl>] [-r <run_id>]
                         [--summary]
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# submission id → permalink aliasing, so events recorded before the note existed
# (submit/chunk/embed) roll up with events recorded after (commit/retrieval).
INGEST_PHASES = ["GA-1.submit", "CA-1.strategy", "CA-2.chunk", "CA-3.embed",
                 "CA-2/3.chunk_embed", "CA-4.neighbors", "CA-5.tag_similarity",
                 "CA-6.metadata", "CA-7.propose", "CA-7.commit", "CA-7.link",
                 "CA-8.verify", "CA-9.reindex", "CA-10.dcf", "CA-11.report"]


def load(path, run_id=None):
    events = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if run_id and e.get("run_id") != run_id:
                continue
            events.append(e)
    return events


def build_aliases(events):
    """Chain source filename → submission id → committed permalink, so every
    phase of one document rolls into a single record."""
    alias = {}
    pending_path = None
    for e in events:
        tool, kind = e.get("tool"), e.get("kind")
        if tool == "submit_document" and kind == "tool.start":
            pending_path = (e.get("arguments") or {}).get("path")
        elif tool == "submit_document" and kind == "tool.end":
            sid = e.get("submission_id") or e.get("doc")
            if pending_path and sid and str(sid).startswith("sub-"):
                alias[Path(pending_path).name] = sid
            pending_path = None
        elif tool == "link_submission" and kind == "tool.start":
            a = e.get("arguments") or {}
            if a.get("submissionId") and a.get("permalink"):
                alias[a["submissionId"]] = a["permalink"]

    def resolve(k, depth=0):
        return k if (k not in alias or depth > 5) else resolve(alias[k], depth + 1)

    return {k: resolve(k) for k in alias}


def rollup(events):
    alias = build_aliases(events)

    def key(doc):
        return alias.get(doc, doc)

    docs = defaultdict(lambda: {
        "doc": None, "run_id": None, "submission_ids": set(), "source_path": None,
        "permalink": None, "entity_class": None, "phases": {}, "events": 0,
        "total_ms": 0.0, "errors": [], "gate_history": [],
        "retrieval": defaultdict(list), "status": "incomplete",
    })

    for e in events:
        doc = e.get("doc")
        if not doc or e.get("phase") == "run":
            continue
        k = key(doc)
        d = docs[k]
        d["doc"] = k
        d["run_id"] = d["run_id"] or e.get("run_id")
        d["events"] += 1
        if doc.startswith("sub-"):
            d["submission_ids"].add(doc)
        if e.get("source_path"):
            d["source_path"] = e["source_path"]
        if e.get("entity_class"):
            d["entity_class"] = e["entity_class"]
        if e.get("permalink"):
            d["permalink"] = e["permalink"]
        elif k.startswith(("knowledge/", "episodes/")):
            d["permalink"] = k

        phase = e.get("phase") or "other"
        ms = e.get("duration_ms") or 0.0
        if e["kind"] in ("tool.end", "chunk.done", "embed.done", "gate.eval",
                         "agent.step") or e["kind"].startswith("agent"):
            p = d["phases"].setdefault(phase, {"calls": 0, "ms": 0.0, "ok": True,
                                               "metrics": {}})
            p["calls"] += 1
            p["ms"] = round(p["ms"] + ms, 2)
            if not e.get("ok", True):
                p["ok"] = False
            d["total_ms"] = round(d["total_ms"] + ms, 2)
            for field in ("n_chunks", "doc_chars", "chunk_chars_mean", "n_texts",
                          "n_batches", "dim", "chars", "n_hits", "top_score",
                          "n_violations", "n_relations", "n_observations", "n_tags",
                          "confidence", "verdict", "n_relations_added", "chunks",
                          "notes", "edges", "accepted", "duplicate"):
                if field in e:
                    p["metrics"][field] = e[field]

        if e["kind"] == "gate.eval":
            d["gate_history"].append({
                "stage": phase, "passed": e.get("gates_passed", []),
                "failed": e.get("gates_failed", []),
                "violations": e.get("violations", []),
            })
        if e["kind"] == "tool.end" and phase.startswith("GA-3.retrieve"):
            d["retrieval"][phase.split(".")[-1]].append({
                "verdict": e.get("verdict"), "n_hits": e.get("n_hits"),
                "top_score": e.get("top_score"),
            })
        if not e.get("ok", True):
            d["errors"].append({"kind": e["kind"], "phase": phase,
                                "error": e.get("error") or e.get("violations")})
        if e["kind"] == "tool.end" and e.get("tool") == "commit_note" and e.get("permalink"):
            d["status"] = "committed"
        if e["kind"] == "submission.failed":
            d["status"] = "failed"

    out = []
    for k, d in docs.items():
        d["submission_ids"] = sorted(d["submission_ids"])
        d["retrieval"] = dict(d["retrieval"])
        d["phases_completed"] = [p for p in INGEST_PHASES if p in d["phases"]]
        d["n_gate_failures"] = sum(1 for g in d["gate_history"] if g["failed"])
        out.append(d)
    out.sort(key=lambda x: (x["status"] != "committed", x["doc"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-e", "--events", required=True)
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("-r", "--run-id", default=None)
    ap.add_argument("-s", "--summary", action="store_true")
    ns = ap.parse_args()

    events = load(ns.events, ns.run_id)
    rows = rollup(events)
    text = "\n".join(json.dumps(r, default=str) for r in rows) + "\n"
    if ns.output:
        Path(ns.output).write_text(text)
        print(f"wrote {len(rows)} document records → {ns.output}")
    else:
        sys.stdout.write(text)

    if ns.summary:
        committed = [r for r in rows if r["status"] == "committed"]
        failed = [r for r in rows if r["status"] == "failed"]
        print(f"\nevents={len(events)}  documents={len(rows)}  "
              f"committed={len(committed)}  failed={len(failed)}", file=sys.stderr)
        for r in rows:
            phases = len(r["phases_completed"])
            print(f"  {r['status']:9s} {r['doc'][:64]:66s} phases={phases:2d} "
                  f"gates_failed={r['n_gate_failures']} {r['total_ms']:9.1f}ms",
                  file=sys.stderr)


if __name__ == "__main__":
    main()
