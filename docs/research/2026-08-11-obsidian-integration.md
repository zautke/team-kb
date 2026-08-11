# R7 — Obsidian as the tooled UI for team-kb

Researched 2026-08-11 (Tavily; current-state sources dated Mar-Jul 2026). Companion to R1-R6.

## Finding 1 — Properties are the contract surface

Obsidian Properties (1.4+) render YAML frontmatter as typed fields: text, list, number,
checkbox, date, date & time. Rules that matter for our serializer:

- **Dates must be unquoted ISO** (`2026-08-11` / `2026-08-11T14:30`). Quoted strings or
  suffixed `Z`/seconds degrade to plain text — lose sorting, filtering, date pickers.
- **`tags` is a magic key**: frontmatter tags == inline `#tags` — tag pane, tag search,
  `file.hasTag()` in Bases. This is the second grouping/search plane.
- **`aliases` is a magic key**: quick-switcher + link autocomplete resolve aliases.
- **Nested objects (our `provenance:`) don't render** in the panel; they survive as raw
  YAML. Acceptable: canonical data > panel prettiness. Don't flatten.
- Recommended vocabulary discipline mirrors ours: closed, typed, template-emitted — we're
  stricter (server-emitted, gate-checked).

**Adopted**: serializer emits unquoted `yyyy-MM-ddTHH:mm` dates; structural facet tags
`kb/<class>`, `kb/status/<status>` computed server-side and merged with topical tags.
(MarkdownSerializer.cs, this commit.)

## Finding 2 — Bases is the query UI (2026 default over Dataview)

Bases: core plugin (team-maintained), `.base` YAML files → live table/card/list/map views
over properties. Filters (`file.hasTag`, `file.inFolder`, property predicates), formulas,
groupBy, summaries, embeds in markdown. Consensus 2026: Bases covers ~80% of Dataview use,
native + faster + editable; Dataview only for query logic Bases can't express.

**Adopted**: server emits `.base` dashboards as vault artifacts — `vault/_meta/bases/kb.base`
(views: all / by-class / needs-review confidence<0.7 / stale 90d+ / deprecated). Bases are
derived UI, like the SQLite index: disposable, regenerable, never authored by hand.
Future (M3): consolidation daemon emits per-project and per-sprint bases.

## Finding 3 — Programmatic bridge: Obsidian CLI is the 2026 direction

- Obsidian 1.12 (Mar 2026) shipped a **first-class CLI** (standalone binary, socket file);
  community integration tooling is migrating from the Local REST API plugin to CLI.
- `obsidian-cli-rest` plugin (dsebastien) wraps the CLI as local HTTP API + MCP server
  (localhost, API key, per-command blocking). `mcp-obsidian` (MarkusPfundstein, REST-based)
  still maintained; several MCP servers expose frontmatter/tag management.
- Filesystem-direct access (what team-kb does) remains the recommended default for
  external tools: works with Obsidian closed, no plugin fragility.

**Adopted stance**: team-kb stays filesystem-canonical — the MCP server IS the write path,
Obsidian is a *read/browse/light-edit* UI over the same files. No REST plugin dependency.
Optional M2+ nicety: shell out to `obsidian` CLI (when installed) for `open`/reveal
commands — deep-link a retrieval result into the UI (`obsidian://open?vault=...&file=...`
URI works today with zero dependencies).

## Finding 4 — Division of labor (kb engine vs Obsidian UI)

| Concern | team-kb server | Obsidian |
|---|---|---|
| Writes, gates, ontology | ALL writes, C1-C8 | read-mostly; human edits land in inbox tier, re-gated on promote (M1 watcher) |
| Search | FTS5/RRF/PPR, verdict contract | quick nav: tag pane, quick switcher, Bases filters |
| Grouping | typed graph edges | tag plane (`kb/...`), Bases groupBy, folders=tiers |
| Dashboards | — | Bases (server-emitted `.base`) |
| Graph viz | Neo4j mirror (M2) | built-in graph view (wikilinks) — free local viz |
| Semantic search | M1 embeddings | (optionally Smart Connections v4, local embeddings — do NOT adopt as engine; UI-only) |

Risk noted: human edits in Obsidian bypass gates. Mitigation (M1): file watcher diffs
mtimes vs index, re-validates changed notes, flags violations as curation work items —
Obsidian edits become *proposals* post-hoc rather than unguarded commits.

## Sources

- obsidianmate.com properties guide (Jul 2026); dsebastien.net properties + Bases guides (Jul 2026)
- kepano/obsidian-skills obsidian-bases SKILL.md (.base schema reference)
- blakecrosley.com Obsidian MCP guide (Apr-Jun 2026 CLI timeline); contextbolt.com MCP comparison
- github.com/dsebastien/obsidian-cli-rest; MarkusPfundstein/mcp-obsidian
