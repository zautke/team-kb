using Microsoft.Data.Sqlite;

namespace TeamKb.Core;

/// <summary>
/// Vault storage: markdown files canonical, SQLite (WAL) index derived — notes, backlinks
/// (C5 computed inverses), FTS5 search, staged proposals (write ≠ commit), episodes.
/// jcodemunch pattern: single db file + incremental reindex on write.
/// </summary>
public sealed class VaultStore : IVaultIndex, IDisposable
{
    private readonly string _root;
    private readonly SqliteConnection _db;
    private readonly NoteValidator _validator;

    public VaultStore(string vaultRoot)
    {
        _root = vaultRoot;
        Directory.CreateDirectory(vaultRoot);
        _db = new SqliteConnection($"Data Source={Path.Combine(vaultRoot, ".teamkb.db")}");
        _db.Open();
        Exec("PRAGMA journal_mode=WAL;");
        Exec("""
            CREATE TABLE IF NOT EXISTS notes(
              permalink TEXT PRIMARY KEY, title TEXT NOT NULL, class TEXT NOT NULL,
              status TEXT NOT NULL, confidence REAL NOT NULL, path TEXT NOT NULL,
              modified TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS edges(
              src TEXT NOT NULL, verb TEXT NOT NULL, dst TEXT NOT NULL,
              since TEXT NOT NULL, mode TEXT, confidence REAL,
              t_valid TEXT, t_invalid TEXT, t_created TEXT, t_expired TEXT,
              PRIMARY KEY(src, verb, dst));
            CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst);
            CREATE TABLE IF NOT EXISTS staged(
              id TEXT PRIMARY KEY, json TEXT NOT NULL, proposed_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tags(tag TEXT PRIMARY KEY);
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
              permalink UNINDEXED, title, overview, observations, tokenize='porter unicode61');
            """);
        SeedTags();
        _validator = new NoteValidator(this);
    }

    // ── write path: propose → commit ────────────────────────────────────────

    public ProposalResult Propose(Note note)
    {
        var violations = _validator.Validate(note);
        if (violations.Count > 0) return new(false, null, violations);
        var id = $"prop-{DateTimeOffset.UtcNow:yyyyMMddHHmmssfff}";
        Exec("INSERT INTO staged(id, json, proposed_at) VALUES($i,$j,$t)",
            ("$i", id), ("$j", System.Text.Json.JsonSerializer.Serialize(note)), ("$t", DateTimeOffset.UtcNow.ToString("O")));
        return new(true, id, []);
    }

    public string Commit(string proposalId)
    {
        var json = Scalar("SELECT json FROM staged WHERE id=$i", ("$i", proposalId))
            ?? throw new InvalidOperationException($"No staged proposal '{proposalId}'.");
        var note = System.Text.Json.JsonSerializer.Deserialize<Note>((string)json)!;

        // re-validate at commit time (state may have moved since propose)
        var violations = _validator.Validate(note);
        if (violations.Count > 0)
            throw new InvalidOperationException("Commit blocked: " + string.Join("; ", violations.Select(x => $"{x.Gate}: {x.Message}")));

        var rel = Path.Combine(Ontology.PathFor(note.Class), Ontology.NormalizeTitle(note.Title) + ".md");
        var abs = Path.Combine(_root, rel);
        Directory.CreateDirectory(Path.GetDirectoryName(abs)!);
        File.WriteAllText(abs, MarkdownSerializer.ToMarkdown(note));
        IndexNote(note, rel);
        Exec("DELETE FROM staged WHERE id=$i", ("$i", proposalId));
        return note.Permalink;
    }

    /// <summary>Episodes bypass propose (append-only, immutable, auto-captured) but still
    /// pass class/scope structure: they ARE Event-class notes.</summary>
    public string CaptureEpisode(string title, string body, Provenance prov, IReadOnlyList<Relation>? relations = null)
    {
        var note = new Note
        {
            Title = title, Class = EntityClass.Event, Overview = body,
            Provenance = [prov], Relations = relations ?? [],
            IsolatedJustification = relations is { Count: > 0 } ? null : "episodic capture; linked at consolidation",
        };
        var rel = Path.Combine("episodes", $"{DateTimeOffset.UtcNow:yyyy-MM-dd}-{Ontology.NormalizeTitle(title)}.md");
        var abs = Path.Combine(_root, rel);
        Directory.CreateDirectory(Path.GetDirectoryName(abs)!);
        if (File.Exists(abs)) throw new InvalidOperationException("Episodes are append-only; identical title today already captured.");
        File.WriteAllText(abs, MarkdownSerializer.ToMarkdown(note));
        IndexNote(note, rel);
        return note.Permalink;
    }

    private void IndexNote(Note n, string relPath)
    {
        Exec("INSERT OR REPLACE INTO notes VALUES($p,$t,$c,$s,$conf,$path,$m)",
            ("$p", n.Permalink), ("$t", n.Title), ("$c", n.Class.ToString()),
            ("$s", n.Status), ("$conf", n.Confidence), ("$path", relPath), ("$m", n.Modified.ToString("O")));
        Exec("DELETE FROM edges WHERE src=$p", ("$p", n.Permalink));
        foreach (var r in n.Relations)
            Exec("INSERT OR REPLACE INTO edges(src,verb,dst,since,mode,confidence,t_valid,t_created) VALUES($s,$v,$d,$since,$m,$c,$tv,$tc)",
                ("$s", n.Permalink), ("$v", MarkdownSerializer.ToScreamingSnake(r.Verb)), ("$d", r.TargetPermalink),
                ("$since", r.Since.ToString("yyyy-MM-dd")), ("$m", (object?)r.Mode ?? DBNull.Value),
                ("$c", (object?)r.Confidence ?? DBNull.Value),
                ("$tv", r.Since.ToString("yyyy-MM-dd")), ("$tc", DateTimeOffset.UtcNow.ToString("O")));
        Exec("DELETE FROM notes_fts WHERE permalink=$p", ("$p", n.Permalink));
        Exec("INSERT INTO notes_fts(permalink,title,overview,observations) VALUES($p,$t,$o,$obs)",
            ("$p", n.Permalink), ("$t", n.Title), ("$o", n.Overview),
            ("$obs", string.Join("\n", n.Observations.Select(o => o.Text))));
    }

    // ── read surface ────────────────────────────────────────────────────────

    public IEnumerable<(string Permalink, string Title, double Rank)> Search(string query, int limit = 10)
    {
        using var cmd = _db.CreateCommand();
        cmd.CommandText = "SELECT permalink, title, bm25(notes_fts) FROM notes_fts WHERE notes_fts MATCH $q ORDER BY bm25(notes_fts) LIMIT $l";
        cmd.Parameters.AddWithValue("$q", query);
        cmd.Parameters.AddWithValue("$l", limit);
        using var r = cmd.ExecuteReader();
        while (r.Read()) yield return (r.GetString(0), r.GetString(1), r.GetDouble(2));
    }

    /// <summary>C5 — backlinks are computed, never authored.</summary>
    public IEnumerable<(string Src, string Verb, string InverseVerb)> Backlinks(string permalink)
    {
        using var cmd = _db.CreateCommand();
        cmd.CommandText = "SELECT src, verb FROM edges WHERE dst=$d AND t_invalid IS NULL";
        cmd.Parameters.AddWithValue("$d", permalink);
        using var r = cmd.ExecuteReader();
        while (r.Read())
        {
            var verb = r.GetString(1);
            var parsed = Enum.GetValues<Verb>().First(v => MarkdownSerializer.ToScreamingSnake(v) == verb);
            yield return (r.GetString(0), verb, Ontology.InverseName(parsed));
        }
    }

    public string? ReadNoteMarkdown(string permalink)
    {
        var path = Scalar("SELECT path FROM notes WHERE permalink=$p", ("$p", permalink)) as string;
        return path is null ? null : File.ReadAllText(Path.Combine(_root, path));
    }

    // ── IVaultIndex ─────────────────────────────────────────────────────────

    public bool PermalinkExists(string permalink) =>
        Scalar("SELECT 1 FROM notes WHERE permalink=$p", ("$p", permalink)) is not null;

    public EntityClass? ClassOf(string permalink) =>
        Scalar("SELECT class FROM notes WHERE permalink=$p", ("$p", permalink)) is string s
            ? Enum.Parse<EntityClass>(s) : null;

    public IEnumerable<(string Permalink, string Title)> TitlesInClass(EntityClass c)
    {
        using var cmd = _db.CreateCommand();
        cmd.CommandText = "SELECT permalink, title FROM notes WHERE class=$c";
        cmd.Parameters.AddWithValue("$c", c.ToString());
        using var r = cmd.ExecuteReader();
        var rows = new List<(string, string)>();
        while (r.Read()) rows.Add((r.GetString(0), r.GetString(1)));
        return rows;
    }

    public bool TagRegistered(string tag) =>
        Scalar("SELECT 1 FROM tags WHERE tag=$t", ("$t", tag)) is not null;

    public void RegisterTag(string tag) => Exec("INSERT OR IGNORE INTO tags(tag) VALUES($t)", ("$t", tag));

    private void SeedTags()
    {
        foreach (var t in new[] { "status/anchor", "status/verified", "status/draft",
                 "source/session", "source/web", "source/paper", "source/code" })
            RegisterTag(t);
    }

    // ── helpers ─────────────────────────────────────────────────────────────

    private void Exec(string sql, params (string, object)[] args)
    {
        using var cmd = _db.CreateCommand();
        cmd.CommandText = sql;
        foreach (var (k, v) in args) cmd.Parameters.AddWithValue(k, v);
        cmd.ExecuteNonQuery();
    }

    private object? Scalar(string sql, params (string, object)[] args)
    {
        using var cmd = _db.CreateCommand();
        cmd.CommandText = sql;
        foreach (var (k, v) in args) cmd.Parameters.AddWithValue(k, v);
        return cmd.ExecuteScalar();
    }

    public void Dispose() => _db.Dispose();
}
