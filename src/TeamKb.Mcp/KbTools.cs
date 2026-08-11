using System.ComponentModel;
using ModelContextProtocol.Server;
using TeamKb.Core;

namespace TeamKb.Mcp;

/// <summary>
/// M0 tool surface. Enums (EntityClass, Verb, ObsKind) appear directly in the generated JSON
/// Schema, so callers see the legal vocabulary at call time and off-vocabulary values are
/// unrepresentable (constitution C1/C6 + post-mortem countermeasure #7).
/// </summary>
[McpServerToolType]
public static class KbTools
{
    public record RelationArg(
        [Description("Relation verb (closed set; inverses are computed server-side, never authored)")] Verb Verb,
        [Description("Target note permalink, e.g. knowledge/concept/hybrid-rag")] string Target,
        [Description("When this relation became true (YYYY-MM-DD)")] string Since,
        [Description("Optional nuance qualifier, e.g. implements|distills|created")] string? Mode = null);

    public record ObservationArg(
        [Description("Observation kind (closed set)")] ObsKind Kind,
        [Description("Observation text, one line")] string Text,
        [Description("Optional inline provenance ref, e.g. url:https://…")] string? Provenance = null);

    [McpServerTool(Name = "propose_note"), Description(
        "Stage a new knowledge note (write ≠ commit). Runs all constitution gates; returns either " +
        "a proposal id or the list of violations. Folder path is computed from entity_class — never supplied.")]
    public static string ProposeNote(
        VaultStore store,
        [Description("Note title (permalink = normalized title)")] string title,
        [Description("Entity class (closed set; determines folder)")] EntityClass entityClass,
        [Description("1-3 sentence overview")] string overview,
        [Description("Typed relations; at least one unless isolatedJustification given")] RelationArg[] relations,
        [Description("Typed observations")] ObservationArg[] observations,
        [Description("Provenance source, e.g. session:2026-08-11-x or url:…")] string provenanceSource,
        [Description("Provenance author, e.g. agent:curator or user")] string provenanceAuthor,
        [Description("Note confidence 0..1 (must be <0.7 if any hypothesis observation)")] double confidence = 1.0,
        [Description("Registered namespaced tags, e.g. domain/rag")] string[]? tags = null,
        [Description("Why this note is deliberately unlinked (rare)")] string? isolatedJustification = null)
    {
        var note = new Note
        {
            Title = title,
            Class = entityClass,
            Overview = overview,
            Confidence = confidence,
            Tags = tags ?? [],
            IsolatedJustification = isolatedJustification,
            Relations = relations.Select(r => new Relation(r.Verb, r.Target, DateOnly.Parse(r.Since), r.Mode)).ToList(),
            Observations = observations.Select(o => new Observation(o.Kind, o.Text, o.Provenance)).ToList(),
            Provenance = [new Provenance(provenanceSource, provenanceAuthor, DateTimeOffset.UtcNow)],
        };
        var result = store.Propose(note);
        return result.Accepted
            ? $"STAGED {result.ProposalId} → {note.Permalink}. Call commit_note to finalize."
            : "REJECTED:\n" + string.Join("\n", result.Violations.Select(x => $"[{x.Gate}] {x.Message}"));
    }

    [McpServerTool(Name = "commit_note"), Description(
        "Commit a staged proposal: re-validates gates, writes canonical markdown, indexes FTS + edges " +
        "(computed backlinks). Returns the committed permalink.")]
    public static string CommitNote(VaultStore store,
        [Description("Proposal id returned by propose_note")] string proposalId)
        => "COMMITTED " + store.Commit(proposalId);

    [McpServerTool(Name = "capture_episode"), Description(
        "Append an immutable episodic record (session log, incident, event). Bypasses staging — " +
        "episodes are append-only and linked later by consolidation.")]
    public static string CaptureEpisode(VaultStore store,
        [Description("Episode title")] string title,
        [Description("Episode body (what happened, evidence)")] string body,
        [Description("Provenance source")] string provenanceSource,
        [Description("Provenance author")] string provenanceAuthor)
        => "CAPTURED " + store.CaptureEpisode(title, body,
               new Provenance(provenanceSource, provenanceAuthor, DateTimeOffset.UtcNow));

    [McpServerTool(Name = "search_notes"), Description(
        "FTS5/BM25 search over titles, overviews, observations. Returns a verdict: ok | absent. " +
        "absent means the knowledge does not exist — report the gap, do not re-search with synonyms.")]
    public static string SearchNotes(VaultStore store,
        [Description("FTS5 query")] string query,
        [Description("Max results")] int limit = 10)
    {
        var hits = store.Search(query, limit).ToList();
        return hits.Count == 0
            ? "verdict: absent — no notes match. The knowledge likely does not exist yet."
            : "verdict: ok\n" + string.Join("\n", hits.Select(h => $"{h.Rank:0.00}  {h.Permalink}  {h.Title}"));
    }

    [McpServerTool(Name = "read_note"), Description(
        "Read a note's canonical markdown plus its computed backlinks (who points here, with inverse verb names).")]
    public static string ReadNote(VaultStore store,
        [Description("Note permalink")] string permalink)
    {
        var md = store.ReadNoteMarkdown(permalink);
        if (md is null) return $"verdict: absent — no note '{permalink}'.";
        var backlinks = store.Backlinks(permalink)
            .Select(b => $"- {b.InverseVerb} ← [[{b.Src}]] (stored as {b.Verb})").ToList();
        return md + (backlinks.Count > 0
            ? "\n## Backlinks (computed)\n" + string.Join("\n", backlinks) : "");
    }

    [McpServerTool(Name = "register_tag"), Description(
        "Register a namespaced tag (domain/…, project/…, status/…, source/…, machine/…) so notes may use it. " +
        "Registry-before-choice: unregistered tags are rejected by propose_note.")]
    public static string RegisterTag(VaultStore store,
        [Description("Namespaced tag, e.g. domain/retrieval")] string tag)
    {
        var ns = tag.Split('/').FirstOrDefault() ?? "";
        if (ns is not ("domain" or "project" or "status" or "source" or "machine"))
            return $"REJECTED: namespace '{ns}/' is not in the closed namespace set.";
        store.RegisterTag(tag);
        return $"REGISTERED {tag}";
    }
}
