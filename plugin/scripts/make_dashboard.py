#!/usr/bin/env python3
"""make_dashboard — single-file HTML evidence dashboard from battery telemetry.

Consumes one or more battery run dirs (each containing events.jsonl) plus the
live vault, renders run comparison, per-phase latency bars (inline SVG), gate
matrix, GA scorecard and corpus health. Stdlib only; output is fully
self-contained (no network resources).

Usage: make_dashboard.py -r <run-dir> [-r <run-dir> ...] -v <vault> -o <out.html>
"""
import argparse
import html
import json
import statistics as st
import sys
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import kb_report  # noqa: E402
import metrics_rollup  # noqa: E402


def load_run(run_dir: Path) -> dict:
    events = metrics_rollup.load(run_dir / "events.jsonl")
    rows = metrics_rollup.rollup(events)
    agg = metrics_rollup.aggregate(rows, events)
    eb = [e for e in events if e.get("kind") == "embed.batch"]
    ga = [e for e in events if e.get("kind") == "ga.score"]
    gate = [e for e in events if e.get("kind") == "gate.eval"]
    ts = sorted(e["ts"] for e in events if e.get("ts"))
    wall = ((datetime.fromisoformat(ts[-1]) - datetime.fromisoformat(ts[0]))
            .total_seconds() if len(ts) > 1 else 0.0)
    lat = sorted(e.get("duration_ms", 0) for e in eb)
    return {
        "name": run_dir.name,
        "run_ids": sorted({e.get("run_id") for e in events if e.get("run_id")}),
        "backend": next((e.get("backend") for e in eb if e.get("backend")), "http"),
        "model": next((e.get("model") for e in events
                       if e.get("kind") == "embed.done" and e.get("model")), "?"),
        "events": len(events),
        "docs": len(rows),
        "wall_s": round(wall, 1),
        "gate_evals": len(gate),
        "gate_failures": sum(len(e.get("gates_failed", [])) for e in gate),
        "gates_exercised": sorted({g for e in gate for g in e.get("gates_evaluated", [])}),
        "embed_batches": len(eb),
        "embed_retries": sum(1 for e in eb if e.get("attempt", 1) > 1 or e.get("ok") is False),
        "embed_p50": round(st.median(lat), 1) if lat else 0,
        "embed_p95": round(lat[int(0.95 * (len(lat) - 1))], 1) if lat else 0,
        "ga_n": len(ga),
        "ga_mean": round(sum(e.get("score", 0) for e in ga) / len(ga), 3) if ga else None,
        "ga_rows": [(e.get("modality") or e.get("phase", "?"), e.get("query", ""),
                     e.get("score")) for e in ga],
        "phases": agg.get("phases", {}),
    }


def svg_bars(items, width=640, row_h=22):
    """items: [(label, value_ms)] → horizontal bar SVG."""
    if not items:
        return ""
    mx = max(v for _, v in items) or 1.0
    h = row_h * len(items) + 4
    parts = [f'<svg width="{width}" height="{h}" font-family="monospace" font-size="12">']
    for i, (label, v) in enumerate(items):
        y = i * row_h + 2
        w = max(2, int((width - 300) * v / mx))
        parts.append(f'<text x="0" y="{y + 14}">{html.escape(label[:34])}</text>')
        parts.append(f'<rect x="240" y="{y + 3}" width="{w}" height="{row_h - 8}" '
                     f'fill="#4a7db5" rx="2"/>')
        parts.append(f'<text x="{244 + w}" y="{y + 14}" fill="#555">{v:.1f} ms</text>')
    parts.append("</svg>")
    return "".join(parts)


CSS = """
body{font-family:-apple-system,Segoe UI,sans-serif;margin:24px;max-width:1080px;color:#1c2733}
h1{font-size:22px} h2{font-size:17px;border-bottom:1px solid #d7dee6;padding-bottom:4px;margin-top:28px}
table{border-collapse:collapse;font-size:13px;margin:8px 0}
th,td{border:1px solid #d7dee6;padding:4px 10px;text-align:left}
th{background:#eef2f6} .ok{color:#1a7f37;font-weight:600} .bad{color:#c62828;font-weight:600}
.small{color:#667;font-size:12px} code{background:#f2f5f8;padding:1px 4px;border-radius:3px}
"""


def build(runs, health, generated):
    R = []
    a = R.append
    a(f"<!-- generated {generated} by make_dashboard.py — derived artifact, do not hand-edit -->")
    a(f"<style>{CSS}</style>")
    a("<h1>team-kb — evidence dashboard</h1>")
    a(f'<p class="small">generated {generated} from committed telemetry '
      f"(events.jsonl per run) and the live vault index. Regenerate: "
      f"<code>plugin/scripts/make_dashboard.py</code></p>")

    a("<h2>Battery run comparison</h2><table><tr><th>run</th><th>backend</th>"
      "<th>model</th><th>docs</th><th>wall</th><th>gate evals</th><th>gate failures</th>"
      "<th>embed batches</th><th>retries</th><th>embed p50/p95</th><th>GA mean</th></tr>")
    for r in runs:
        gf = f'<td class="{"ok" if r["gate_failures"] == 0 else "bad"}">{r["gate_failures"]}</td>'
        ga = f'<td class="{"ok" if (r["ga_mean"] or 0) >= 0.7 else "bad"}">{r["ga_mean"]}</td>'
        a(f'<tr><td>{html.escape(r["name"])}</td><td>{r["backend"]}</td>'
          f'<td>{html.escape(str(r["model"]))}</td><td>{r["docs"]}</td>'
          f'<td>{r["wall_s"]} s</td><td>{r["gate_evals"]}</td>{gf}'
          f'<td>{r["embed_batches"]}</td><td>{r["embed_retries"]}</td>'
          f'<td>{r["embed_p50"]} / {r["embed_p95"]} ms</td>{ga}</tr>')
    a("</table>")

    for r in runs:
        a(f"<h2>Per-phase latency — {html.escape(r['name'])} "
          f'<span class="small">({", ".join(r["run_ids"])})</span></h2>')
        items = [(ph, s["p95_ms"]) for ph, s in sorted(r["phases"].items())
                 if isinstance(s, dict) and s.get("p95_ms") is not None]
        a(svg_bars(items))
        a(f'<p class="small">bars = p95 per pipeline phase; gates exercised: '
          f'{", ".join(r["gates_exercised"])}</p>')

    ga_run = next((r for r in runs if r["ga_rows"]), None)
    if ga_run:
        a(f"<h2>GA scorecard — {html.escape(ga_run['name'])}</h2>"
          "<table><tr><th>modality</th><th>query</th><th>score</th></tr>")
        for mod, qy, sc in ga_run["ga_rows"]:
            cls = "ok" if (sc or 0) >= 0.7 else "bad"
            a(f'<tr><td>{html.escape(str(mod))}</td><td>{html.escape(str(qy))[:80]}</td>'
              f'<td class="{cls}">{sc}</td></tr>')
        a("</table>")

    h = health
    a("<h2>Corpus health (live vault)</h2><table>")
    p = h["parity"]
    s = h["semantic"]
    rows = [
        ("vault", h["vault"]),
        ("notes / edges / chunks", f"{h['notes']} / {h['edges']} / {h['chunks']}"),
        ("by class", ", ".join(f"{k}={v}" for k, v in h["notes_by_class"].items())),
        ("index parity", f"fts {p['fts_rows']}/{h['notes']} "
         f"{'OK' if p['fts_vs_notes_ok'] else 'MISMATCH'} · md {p['md_files']}/{h['notes']} "
         f"{'OK' if p['md_vs_notes_ok'] else 'MISMATCH'}"),
        ("semantic", f"model={s['embed_model']} θ={s['theta']} "
         f"doc_vecs={s['doc_embeddings']} chunk_vecs={s['chunk_embeddings']}"),
        ("orphans (semantic tiers)", str(len(h["orphan_notes"])) or "0"),
        ("staged proposals", str(h["staged_proposals"])),
        ("db size", f"{h['db_bytes'] / 1024:.0f} KiB"),
    ]
    for k, v in rows:
        a(f"<tr><th>{html.escape(k)}</th><td>{html.escape(str(v))}</td></tr>")
    a("</table>")
    return "\n".join(R)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-r", "--run-dir", action="append", required=True)
    ap.add_argument("-v", "--vault", required=True)
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()

    runs = [load_run(Path(d)) for d in a.run_dir]
    health = kb_report.corpus_health(Path(a.vault).expanduser())
    if "error" in health:
        print(health["error"], file=sys.stderr)
        return 1
    out = Path(a.output)
    out.write_text(build(runs, health, datetime.now().isoformat(timespec="seconds")))
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
