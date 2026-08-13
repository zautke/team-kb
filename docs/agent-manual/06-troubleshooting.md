# 06 — Troubleshooting

Symptoms observed on real runs, and what they actually mean.

## Everything returns `absent`, even things you know are there

**First check the vault.** The server has no default vault and every symptom is
downstream of pointing at the wrong one:

```bash
python3 plugin/scripts/kbcall.py -t reindex -a '{}'
# {"vault": "/Users/derp/vault/kb-test", "notes": 29, …}
```

If `notes` is 0 but markdown files exist on disk, the index is missing — a fresh
clone, or a deleted database. Rebuild it from the markdown:

```bash
python3 plugin/scripts/kbcall.py -t reindex -a '{"rebuild":true}'
# {"notes": 29, "edges": 22, "rebuilt": {"files_parsed": 29, "parse_failures": [], "duration_ms": 6.5}}
```

Markdown is canonical, so this is lossless for notes, edges, tags and FTS.
Document embeddings derive from the *source corpus*, not from vault notes, so
semantic search only covers what that vault ingested; re-ingest a document to
re-embed it.

If `parse_failures` is non-empty, those files were hand-edited into a shape the
parser cannot read. Fix or remove them — and note that hand-editing vault
markdown is exactly what the write path exists to prevent.

## `FAILED: embedding endpoint failed after 3 attempts`

The hosted endpoint timed out or refused. The submission is marked `failed`,
which is correct behaviour — the run continues rather than blocking.

- Verify the endpoint directly:
  `curl -sS -o /dev/null -w '%{http_code}\n' -X POST $TEAMKB_EMBED_URL/api/embed -H 'Content-Type: application/json' -d '{"model":"nomic-embed-text-v2-moe:latest","input":["hi"]}'`
- `403` from a tunnelled endpoint is usually the User-Agent being filtered — the
  server already sends a custom one; a bare `curl` or `urllib` default may not.
- Timeouts on large documents mean batch size: the server sub-batches at 8 texts
  with a 90 s timeout because whole-document batches timed out in practice.
- Recover by re-running the same document: `submit_document` returns
  `DUPLICATE: submission sub-… (status failed)`, and you resume from that id
  rather than starting over.

Never wrap this in a retry loop. Record the failure, move to the next document,
rerun the failed set once the endpoint is healthy.

## `DUPLICATE: submission sub-… already covers this content`

Content-hash match — this exact file was submitted before.

- status `committed` → the work is done. Stop.
- status `failed` or `curating` → resume with that submission id.

Editing the source file changes its hash and produces a new submission, which is
what you want when the document genuinely changed.

## A note vanished from search but the file is on disk

```bash
python3 plugin/scripts/kbcall.py -t reindex -a '{}'
```

`missing_files` lists indexed notes whose file is gone (someone deleted markdown
out from under the index). The inverse — file present, not indexed — means the
note was never committed through the write path, or the index predates it. In
both cases `{"rebuild": true}` re-derives the truth from the files.

## Semantic search misses something obviously related

Read the reported top score. `absent — no semantic neighbors above θ=0.3 (top
score 0.267)` means the match existed but fell under the threshold.

θ lives per vault in the database:

```bash
sqlite3 <vault>/.teamkb.db "SELECT * FROM meta WHERE key='semantic_theta'"
sqlite3 <vault>/.teamkb.db "UPDATE meta SET value='0.28' WHERE key='semantic_theta'"
```

Calibrate against evidence, not vibes: score a handful of known-good and
known-unrelated queries and put θ between the two populations. On this corpus,
true matches floor around 0.30 and true absents ceiling around 0.17, which is why
0.30 is the seeded default. A vault left at the old 0.45 returned `absent` for a
genuine conceptual match — that failure is the reason the default changed.

## Everything is slow

Expected. Embedding is ~99.9% of pipeline wall time: p50 33 s, p95 91 s per
document. Every other phase — gates, chunking, commit, link, report — is
sub-millisecond. Confirm rather than assume:

```bash
python3 plugin/scripts/metrics_rollup.py -e <vault>/.teamkb-events.jsonl \
    -o /dev/null --aggregate phase-stats.json
```

If a non-embedding phase shows seconds, that is a real anomaly worth chasing.

## The same title keeps getting rejected (C2 or I4)

You are trying to write something that already exists. Read the existing note
before deciding — `read_note`, or `search_notes` on the title. Merge into it, or
supersede it explicitly with a distinguishable human title plus a `Supersedes`
relation. Suffixing the title to slip past the gate is the failure mode that
produced thirty-one duplicate slugs in the predecessor system.

## A staged proposal never became a note

`STAGED prop-…` is not a write. Call `commit_note` with that id. If you get
`No staged proposal 'prop-…'`, the id is wrong or it was already committed —
check whether the permalink exists before re-proposing.

## Commit fails after propose succeeded

```
ERROR: Commit blocked: C2: Permalink '…' already exists. Merge or supersede — never suffix.
```

Gates re-run at commit, so state moved between the two calls — usually a
concurrent commit of the same title. Re-curate against what is now there.

## The run produced no events

The event log is always on and lives at `<vault>/.teamkb-events.jsonl`. If it is
missing or empty, the server never started (check stderr — it logs the vault path
and events path at startup), or you are looking in a different vault. Set
`TEAMKB_RUN_ID` before a run to make its events filterable afterwards.
