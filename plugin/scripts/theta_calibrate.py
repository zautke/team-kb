#!/usr/bin/env python3
"""theta_calibrate — measure the semantic score distribution of a vault and
recommend a θ. Recommendation only: writes nothing; the per-vault override
(`UPDATE meta SET value=... WHERE key='semantic_theta'`) stays a human call.

Embeds K true-match queries (derived from note titles/overviews) and K junk
queries against the vault's doc embeddings, prints both distributions and the
midpoint recommendation.

Usage: theta_calibrate.py -v <vault> [-k <n-per-side>] [-j]
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS.parent / "mcp"))
import teamkb_server as srv  # noqa: E402

JUNK = ["french pastry recipes", "nba playoff schedule",
        "how to change a car tire", "tropical fish tank maintenance",
        "medieval castle architecture", "best hiking trails colorado",
        "guitar chord progressions", "sourdough starter feeding"]


def top_score(store, qv):
    best = 0.0
    for _, permalink, blob in store.db.execute(
            "SELECT submission_id, permalink, vector FROM doc_embeddings"):
        if permalink and permalink.startswith("inbox/"):
            continue
        best = max(best, srv.dot(qv, srv.unpack(blob)))
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-v", "--vault", required=True)
    ap.add_argument("-k", "--k", type=int, default=6, help="queries per side")
    ap.add_argument("-j", "--json", action="store_true")
    a = ap.parse_args()

    store = srv.Store(str(Path(a.vault).expanduser()))
    if getattr(store, "embed_model_mismatch", None):
        print(f"ABORT: {store.embed_model_mismatch}", file=sys.stderr)
        return 1

    rows = store.db.execute(
        """SELECT n.title, n.permalink FROM notes n
           JOIN doc_embeddings d ON d.permalink = n.permalink
           LIMIT ?""", (a.k,)).fetchall()
    if not rows:
        print("ABORT: no embedded notes in this vault — ingest first.", file=sys.stderr)
        return 1

    true_q = [f"tell me about {t}" for t, _ in rows]
    junk_q = JUNK[: a.k]
    qvecs = srv.embed_texts(true_q + junk_q, srv.QUERY_PREFIX,
                            phase="theta_calibrate")
    true_s = sorted(top_score(store, v) for v in qvecs[: len(true_q)])
    junk_s = sorted(top_score(store, v) for v in qvecs[len(true_q):])

    true_floor, junk_ceiling = min(true_s), max(junk_s)
    rec = round((true_floor + junk_ceiling) / 2, 3)
    current = store.meta_get("semantic_theta", "?")
    out = {"model": store.meta_get("embed_model", "?"),
           "true_scores": [round(s, 3) for s in true_s],
           "junk_scores": [round(s, 3) for s in junk_s],
           "true_floor": round(true_floor, 3),
           "junk_ceiling": round(junk_ceiling, 3),
           "margin": round(true_floor - junk_ceiling, 3),
           "current_theta": current, "recommended_theta": rec,
           "overlap": true_floor <= junk_ceiling}
    if a.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"model: {out['model']}   current θ: {current}")
        print(f"true  scores: {out['true_scores']}")
        print(f"junk  scores: {out['junk_scores']}")
        print(f"true floor {out['true_floor']}  vs  junk ceiling {out['junk_ceiling']}"
              f"  (margin {out['margin']})")
        if out["overlap"]:
            print("WARNING: distributions overlap — no clean θ exists; consider a "
                  "higher-quality embedding model.")
        print(f"recommended θ: {rec}   (apply manually: UPDATE meta SET "
              f"value='{rec}' WHERE key='semantic_theta')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
