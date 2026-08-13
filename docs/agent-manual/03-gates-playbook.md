# 03 — Gates playbook: reading a rejection and fixing it

A rejection looks like this:

```
REJECTED:
[C4] Relation target 'knowledge/concept/does-not-exist' does not exist. Create it first or request an auto-stub.
[TAG] Tag 'random-freeform-tag' is not in the registry (_meta/registries/tags.md). Register it in the same commit.
```

Every line is `[GATE] message`. Fix the curation and propose again. **Never work
around a gate** — no placeholder provenance to satisfy PROV, no invented relation
to satisfy I1, no `-v2` suffix to dodge C2. Those are precisely the failures this
system was built to make impossible.

Gates run twice: at propose, and again at commit against current state. A commit
that fails after a successful propose means the vault moved underneath you
(usually someone committed the same title first) and returns
`Commit blocked: C2: …`.

## The eight gates

### C2 — permalink uniqueness
```
Permalink 'knowledge/concept/hybrid-rag' already exists. Merge or supersede — never suffix.
```
The permalink is derived from the title, so this says: a note with this title
already exists. Read it. Then either add your new material to it as observations
and relations, or — if yours genuinely supersedes it — give your note a title
that says so and add `Supersedes` pointing at the old one. Do not retitle to
"… v2" purely to get past the gate; that is how a knowledge base ends up with
thirty-one duplicate slugs, which is what happened to the system this one
replaced.

### C3 — relation signature
```
Precedes not valid from class Concept (dom: Event).
Uses target 'knowledge/person/alice' has class Person (rng: Technology|Artifact|Codebase).
```
Each verb constrains the classes at one or both ends. The first form means your
note's class cannot be the *source* of that verb; the second means the target's
class cannot be its *destination*. Pick a verb whose signature fits both ends —
the table is in `plugin/skills/kb-agent/references/ontology-digest.md`. If no verb
fits, the relation you have in mind probably is not the one the ontology models;
`Mentions` is unconstrained and always available as the honest weak link.

### C4 — referential integrity
```
Relation target 'knowledge/concept/does-not-exist' does not exist. Create it first or request an auto-stub.
```
There is no auto-stub today, despite what the message offers — it is preserved
verbatim from the original implementation. Three real options: commit the target
first (reorder the batch), drop the relation now and add it in the back-pass with
`add_relations`, or check whether you have the permalink slightly wrong. Search
for the target before assuming it is missing — `knowledge/concept/gates-as-code`
and `knowledge/concepts/gates-as-code` differ by one character.

### I1 — connectivity
```
Note declares no relations. Add at least one, or set isolated_justification.
```
Isolated notes are how a graph decays into a folder. Find the real relation —
the neighbours from CA-4 are the obvious place to look. Use
`isolatedJustification` only when isolation is genuinely true and you can say why
("genesis anchor" in an empty vault is the standard case). A justification that
is not true is worse than a missing note.

### I4 — near-duplicate title
```
Title too similar to existing 'Agent Specialist- Color Theory' (knowledge/concept/agent-specialist-color-theory). Merge, supersede, or assert distinct_from.
```
Trigram similarity above 0.85 within the same class. Two documents whose titles
differ only by a version marker will trip this — that is the point. Read the
existing note first: if it is the same subject, merge into it; if it truly
supersedes, retitle so a human can tell them apart *and* add `Supersedes`.
Watch for this when ingesting `…-v1.md` and `…-v2.md` from the same folder: give
them distinct human titles rather than filename-derived ones.

### PROV — provenance
```
At least one provenance entry (source + author) is required.
Placeholder provenance source 'TBD' rejected.
```
`TBD`, `TODO`, `unknown` and empty are all refused. If you cannot name where the
claim came from, you cannot write it. Use a repo-relative path, a URL, or
`session:<date>-<topic>` for something established during a working session.

### HYP — hypothesis ceiling
```
Note contains [hypothesis] but confidence 0.95 ≥ 0.7.
```
A note carrying an unverified claim cannot also claim high confidence. Either
lower confidence below 0.7, or — if you actually have the evidence — promote the
observation from `hypothesis` to `fact` and cite it. Do not delete the hypothesis
to raise the number.

### TAG — registry before choice
```
Tag 'random-freeform-tag' is not in the registry (_meta/registries/tags.md). Register it in the same commit.
```
Register it first with `register_tag` (namespaced, with a description), then
propose again. `register_tag` has its own refusals: a namespace outside
`domain/ project/ status/ source/ machine/`, anything starting `kb/` (server
plane, reserved), and near-duplicates of tags already registered — that last one
pushes you toward reusing the existing tag, which is the intent.

## Gates you will never see fail

C1 (folder from class), C6 (closed vocabulary) and C7 (junk file scope) are
enforced structurally rather than by validation: there is no path argument to get
wrong, class/verb/kind are enums in the tool schema, and out-of-scope filenames
are unindexable. If you find yourself wanting to pass a path or a custom verb,
the answer is not a workaround — it is that the model does not work that way.

## Verifying you were actually stopped

Every validator pass emits a `gate.eval` event listing all eight gates as passed
or failed with messages. If you want proof that a rejection happened and why:

```bash
python3 -c "
import json
for l in open('<vault>/.teamkb-events.jsonl'):
    e = json.loads(l)
    if e['kind'] == 'gate.eval' and e['gates_failed']:
        print(e['doc'], e['gates_failed'], e['violations'])"
```
