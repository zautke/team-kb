# 00 — Zero to a running knowledge base

**Read this first if the KB does not exist yet.** It takes an agent from an empty
directory to a vault that is being actively used: bootstrapped, wired, seeded,
holding its first real document, and answering all four retrieval modalities.

Every command and output below comes from an actual run of this procedure
against a fresh vault. Expect to spend about ten minutes, most of it waiting on
embeddings.

If the KB already exists and you just need to use it, skip to
[01-quickstart.md](01-quickstart.md).

---

## Step 0 — Decide three things

| Decision | Default | Why it matters |
|----------|---------|----------------|
| **Where the vault lives** | `<repo>/vault` | Version it with the code if the team should get knowledge on clone; keep it outside the repo if it is private or huge. |
| **Embedding backend** | `TEAMKB_EMBED_BACKEND=http` | `http` needs a network endpoint; `onnx` runs a local model in-process, no network — see [07-mcp-server-config.md](07-mcp-server-config.md) "Local ONNX embeddings" (one 17 MB model + `pip install onnxruntime tokenizers`). |
| **Which embedding endpoint** | `TEAMKB_EMBED_URL` (Ollama `/api/embed` shape) | http backend only. Semantic search and neighbour discovery depend on it. Everything else works without it. |
| **Which embedding model** | `nomic-embed-text-v2-moe:latest` (http) / `bge-micro-v2-onnx` (onnx) | Changing it later changes the vector space — the server refuses to mix; you would have to re-embed the whole corpus, so choose once. |

Requirements are otherwise nil: Python 3 standard library only. No pip install,
no virtualenv, no build.

Confirm the endpoint before you depend on it:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$TEAMKB_EMBED_URL/api/embed" \
  -H 'Content-Type: application/json' \
  -d '{"model":"nomic-embed-text-v2-moe:latest","input":["hello"]}'
# 200
```

Anything other than `200` — fix it now, or accept that you are running without
semantic search until you do. FTS, tags and graph traversal do not need it.

## Step 1 — Bootstrap the vault

```bash
python3 plugin/scripts/bootstrap_vault.py --vault /path/to/newkb
```

```
Bootstrapped vault: /path/to/newkb
  dir  inbox
  dir  episodes
  dir  playbooks
  …20 directories
  created .obsidian/app.json
  created _meta/registries/tags.md
  created _meta/bases/kb.base
```

This creates the tier tree (`inbox/ episodes/ knowledge/<class>/ playbooks/
procedures/ hubs/ _meta/`), an Obsidian config, the tag registry file, and the
dashboard. It is **idempotent and non-destructive**: run it against an existing
Obsidian vault and it merges settings rather than overwriting them, so pointing
it at a vault someone already uses is safe.

## Step 2 — Wire the server and confirm it answers

Set the vault for your shell, or configure your MCP host per
[07-mcp-server-config.md](07-mcp-server-config.md):

```bash
export TEAMKB_VAULT=/path/to/newkb
python3 plugin/scripts/kbcall.py -t reindex -a '{}'
```

```json
{"vault": "/path/to/newkb", "notes": 0, "edges": 0, "chunks": 0,
 "doc_embeddings": 0, "tags": 7, "missing_files": [], "embed_pending": []}
```

**Check the `vault` field matches what you intended.** Nearly every confusing
symptom later traces back to a server pointed somewhere else.

`tags: 7` is the seeded registry — `status/anchor`, `status/verified`,
`status/draft`, `source/session`, `source/web`, `source/paper`, `source/code`.
Zero notes is correct; you have not written any yet.

## Step 3 — Register the tags this KB will actually use

Tags are registry-before-choice: `propose_note` rejects unregistered ones, so
decide the domains up front. Namespaces are closed — `domain/ project/ status/
source/ machine/` — and `kb/*` belongs to the server.

```bash
python3 plugin/scripts/kbcall.py -t register_tag -a '{
  "tag":"domain/onboarding","description":"getting a new KB running"}'
# REGISTERED domain/onboarding
```

Three to eight `domain/` tags is a healthy start. Give each a real description —
it feeds the similarity that `suggest_tags` uses later. Resist inventing a tag
per document; tags are a coarse search plane, not a summary.

## Step 4 — Plant genesis anchors

An empty vault has a bootstrapping problem: gate I1 requires every note to
connect to something, and there is nothing to connect to. Anchors are the
sanctioned exception.

Watch what happens without the escape hatch:

```bash
python3 plugin/scripts/kbcall.py -t propose_note -a '{
  "title":"Unlinked Example","entityClass":"Concept","overview":"x",
  "relations":[],"observations":[],
  "provenanceSource":"session:2026-08-13-kb-setup","provenanceAuthor":"agent:curator"}'
```

```
REJECTED:
[I1] Note declares no relations. Add at least one, or set isolated_justification.
```

That is the system working. For a genuine first anchor, say why it is isolated:

```bash
python3 plugin/scripts/kbcall.py -t propose_note -a '{
  "title":"Team Knowledge Base","entityClass":"Concept",
  "overview":"The team knowledge base: a gated markdown vault where every write passes constitution gates and every retrieval returns an explicit verdict.",
  "relations":[],
  "observations":[{"kind":"Fact","text":"Markdown is canonical; the SQLite index is derived and rebuildable."}],
  "provenanceSource":"session:2026-08-13-kb-setup","provenanceAuthor":"agent:curator",
  "confidence":0.9,"tags":["domain/onboarding"],
  "isolatedJustification":"genesis anchor"}'
```

```
STAGED prop-20260813170808077627 → knowledge/concept/team-knowledge-base. Call commit_note to finalize.
```

**Staging is not writing.** Commit it:

```bash
python3 plugin/scripts/kbcall.py -t commit_note -a '{"proposalId":"prop-20260813170808077627"}'
# COMMITTED knowledge/concept/team-knowledge-base
```

The file now exists at `knowledge/concept/team-knowledge-base.md` — you never
supplied that path; it was computed from the entity class and title.

Plant **two or three** anchors covering the concepts your corpus keeps
returning to. They are what the first real documents attach to. `"genesis
anchor"` is only honest while the vault is empty; once anchors exist, later
notes must find real relations.

## Step 5 — Ingest the first real document

```bash
python3 plugin/scripts/kbcall.py -t submit_document -a '{"path":"/abs/path/to/doc.md"}'
# {"submission_id": "sub-20260813170818813", "source_path": "…", "status": "staged"}

python3 plugin/scripts/kbcall.py -t ingest_chunks -a '{"submissionId":"sub-20260813170818813"}'
# {"submission_id": "sub-…", "chunks": 1, "dim": 768, "headings": ["Research Dossier — team-kb rebuild (2026-08-11)"]}
```

Chunking is deterministic and server-side; embedding is the slow part (tens of
seconds for a substantial document). Ask for neighbours:

```bash
python3 plugin/scripts/kbcall.py -t semantic_search -a '{"target":"sub-20260813170818813","limit":3}'
# verdict: absent — no semantic neighbors above θ=0.3 (top score 0.000). The knowledge likely does not exist yet.
```

Correct and expected on a nearly-empty vault — there is nothing to be near. From
roughly the fifth document onward this returns real neighbours, and those become
your relation candidates.

Curate and commit, linking to an anchor:

```bash
python3 plugin/scripts/kbcall.py -t propose_note -a '{
  "title":"Research Dossier Index","entityClass":"Artifact",
  "overview":"Index of the six-report research dossier grounding the team-kb rebuild.",
  "relations":[{"verb":"Mentions","target":"knowledge/concept/team-knowledge-base","since":"2026-08-13"}],
  "observations":[{"kind":"Fact","text":"Six parallel research reports R1-R6 ground the rebuild design."}],
  "provenanceSource":"docs/research/README.md","provenanceAuthor":"agent:curator",
  "confidence":0.9,"tags":["domain/onboarding"]}'
# STAGED prop-… → knowledge/artifact/research-dossier-index. Call commit_note to finalize.

python3 plugin/scripts/kbcall.py -t commit_note -a '{"proposalId":"prop-…"}'
# COMMITTED knowledge/artifact/research-dossier-index

python3 plugin/scripts/kbcall.py -t link_submission -a '{
  "submissionId":"sub-20260813170818813",
  "permalink":"knowledge/artifact/research-dossier-index"}'
# LINKED sub-20260813170818813 → knowledge/artifact/research-dossier-index
```

`link_submission` binds the document vector to the note, so semantic search
returns permalinks rather than submission ids. Skipping it leaves the note
unreachable by meaning.

The full eleven-step pipeline — strategy, tag similarity, DCF episode, reporting
— is in [02-populate-the-kb.md](02-populate-the-kb.md). The five calls above are
its irreducible core.

## Step 6 — Prove all four modalities

Do not declare the KB working until each one answers:

```bash
python3 plugin/scripts/kbcall.py -t search_notes    -a '{"query":"research dossier","limit":2}'
# verdict: ok
# -0.00  knowledge/artifact/research-dossier-index  Research Dossier Index

python3 plugin/scripts/kbcall.py -t semantic_search -a '{"query":"what research grounds this project","limit":2}'
# verdict: ok
# 0.320  knowledge/artifact/research-dossier-index

python3 plugin/scripts/kbcall.py -t search_by_tag   -a '{"tag":"domain/onboarding"}'
# verdict: ok
# knowledge/artifact/research-dossier-index  Research Dossier Index

python3 plugin/scripts/kbcall.py -t read_note -a '{"permalink":"knowledge/concept/team-knowledge-base"}'
# ## Backlinks (computed)
# - MENTIONED_BY ← [[knowledge/artifact/research-dossier-index]] (stored as MENTIONS)
```

Note the last one: you authored `Mentions` in one direction and the inverse
appeared on the other note without anyone writing it.

Then prove the KB can say no:

```bash
python3 plugin/scripts/kbcall.py -t search_notes -a '{"query":"sourdough hydration"}'
# verdict: absent — no notes match. The knowledge likely does not exist yet.
```

**A KB that never says `absent` is broken, not thorough.** This probe is part of
acceptance, not an afterthought.

## Step 7 — Calibrate the semantic threshold

θ defaults to 0.30, calibrated against a research-and-whitepaper corpus. Yours
may differ. Once you have ten or so documents, score a few queries you know the
answer to and a few you know are unrelated, then place θ between the two
populations:

```bash
sqlite3 <vault>/.teamkb.db "SELECT * FROM meta WHERE key='semantic_theta'"
sqlite3 <vault>/.teamkb.db "UPDATE meta SET value='0.28' WHERE key='semantic_theta'"
```

This matters more than it looks. A vault left at an uncalibrated 0.45 returned
`absent` for a genuinely matching conceptual query — the retrieval was correct,
the threshold was wrong, and only the recorded scores made it visible. Set θ
from evidence, and record what you based it on.

## Step 8 — Establish the operating rhythm

The KB is now live. Four habits keep it healthy:

1. **Ingest through the pipeline, never by hand.** Editing vault markdown
   directly bypasses all eight gates and desynchronises the index. There is no
   tool that lets an agent do it, and that is deliberate.
2. **Every batch ends with an episode.** `capture_episode` writes the run's own
   report back into `episodes/`, so the KB records how it was built.
3. **Run a relation back-pass after a batch.** Relations you skipped because the
   target had not landed yet go in with `add_relations`; otherwise graph density
   becomes an accident of ingestion order.
4. **Read the telemetry rather than trusting the narration.** Every phase emits
   metrics:
   ```bash
   python3 plugin/scripts/metrics_rollup.py -e <vault>/.teamkb-events.jsonl \
       -o metrics.jsonl --aggregate phase-stats.json --summary
   ```

## Acceptance checklist

The KB is genuinely running when all of these are true:

- [ ] `reindex` reports the vault path you intended, with `missing_files: []`
- [ ] The tag registry holds the domains this KB will use, each with a description
- [ ] Two or three genesis anchors are committed
- [ ] At least one real document is ingested, committed and linked
- [ ] All four modalities return `verdict: ok` for that document
- [ ] An out-of-corpus probe returns `verdict: absent`
- [ ] A backlink appears on an anchor without anyone authoring it
- [ ] θ has been set from observed scores, not left at a guess
- [ ] `<vault>/.teamkb-events.jsonl` exists and has events from your run

## If the vault already has markdown but no index

Someone cloned a vault, or the database was lost. Markdown is canonical, so
rebuild rather than re-ingest:

```bash
python3 plugin/scripts/kbcall.py -t reindex -a '{"rebuild":true}'
# {"notes": 29, "edges": 22, "rebuilt": {"files_parsed": 29, "parse_failures": [], "duration_ms": 6.5}}
```

Notes, edges, tags and FTS come back exactly. Document embeddings derive from the
*source corpus* rather than from vault notes, so the semantic channel stays empty
until those documents are re-ingested — the other three modalities work
immediately.

## Where to go next

| Next | Read |
|------|------|
| Ingest a whole corpus properly | [02-populate-the-kb.md](02-populate-the-kb.md) |
| Something got rejected | [03-gates-playbook.md](03-gates-playbook.md) |
| Search well and know when to stop | [04-retrieval-playbook.md](04-retrieval-playbook.md) |
| Look up a tool | [05-tool-reference.md](05-tool-reference.md) |
| Something broke | [06-troubleshooting.md](06-troubleshooting.md) |
| Wire another host | [07-mcp-server-config.md](07-mcp-server-config.md) |
