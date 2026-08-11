using System.Text;

namespace TeamKb.Core;

/// <summary>Markdown-canonical serialization. One dialect, emitted by the server only —
/// authors never hand-write relation lines (post-mortem countermeasure #3).</summary>
public static class MarkdownSerializer
{
    public static string ToMarkdown(Note n)
    {
        var sb = new StringBuilder();
        sb.AppendLine("---");
        sb.AppendLine($"title: \"{n.Title.Replace("\"", "'")}\"");
        sb.AppendLine($"type: entity");
        sb.AppendLine($"kb_version: \"{Ontology.Version}\"");
        sb.AppendLine($"entity_class: {n.Class}");
        sb.AppendLine($"permalink: {n.Permalink}");
        // Unquoted ISO date-time (no Z, no seconds) — Obsidian Properties parses this as a
        // typed "Date & time" field; quoted strings degrade to plain text and lose sorting/filtering.
        sb.AppendLine($"created: {n.Created:yyyy-MM-ddTHH:mm}");
        sb.AppendLine($"modified: {n.Modified:yyyy-MM-ddTHH:mm}");
        sb.AppendLine($"status: {n.Status}");
        sb.AppendLine($"confidence: {n.Confidence:0.0#}");
        if (n.Aliases.Count > 0)
            sb.AppendLine($"aliases: [{string.Join(", ", n.Aliases.Select(a => $"\"{a}\""))}]");
        // Tags are a second grouping/search plane in Obsidian (tag pane, Bases file.hasTag()).
        // Structural facets are mirrored as namespaced tags so class/status group natively,
        // alongside the note's own topical tags. Server-computed — authors never write these.
        var tags = new List<string>
        {
            $"kb/{n.Class.ToString().ToLowerInvariant()}",
            $"kb/status/{n.Status.ToString().ToLowerInvariant()}",
        };
        tags.AddRange(n.Tags.Where(t => !tags.Contains(t)));
        sb.AppendLine("tags:");
        foreach (var t in tags) sb.AppendLine($"  - {t}");
        if (n.IsolatedJustification is not null)
            sb.AppendLine($"isolated_justification: \"{n.IsolatedJustification.Replace("\"", "'")}\"");
        sb.AppendLine("provenance:");
        foreach (var p in n.Provenance)
        {
            sb.AppendLine($"  - source: \"{p.Source}\"");
            sb.AppendLine($"    author: \"{p.Author}\"");
            sb.AppendLine($"    captured_at: \"{p.CapturedAt:yyyy-MM-ddTHH:mm:ssZ}\"");
            sb.AppendLine($"    confidence: {p.Confidence:0.0#}");
        }
        sb.AppendLine("---");
        sb.AppendLine();
        if (!string.IsNullOrWhiteSpace(n.Overview))
        {
            sb.AppendLine("## Overview");
            sb.AppendLine(n.Overview.Trim());
            sb.AppendLine();
        }
        if (n.Relations.Count > 0)
        {
            sb.AppendLine("## Relations");
            foreach (var r in n.Relations)
            {
                var verb = ToScreamingSnake(r.Verb);
                var props = $"{{since: {r.Since:yyyy-MM-dd}" +
                            (r.Mode is not null ? $", mode: {r.Mode}" : "") +
                            (r.Confidence is not null ? $", confidence: {r.Confidence:0.0#}" : "") + "}";
                sb.AppendLine($"- {verb} :: [[{r.TargetPermalink}]] {props}");
            }
            sb.AppendLine();
        }
        if (n.Observations.Count > 0)
        {
            sb.AppendLine("## Observations");
            foreach (var o in n.Observations)
            {
                var prov = o.ProvenanceRef is not null ? $" (provenance: {o.ProvenanceRef})" : "";
                sb.AppendLine($"- [{o.Kind.ToString().ToLowerInvariant()}] {o.Text}{prov}");
            }
        }
        return sb.ToString();
    }

    public static string ToScreamingSnake(Verb v)
    {
        var s = v.ToString();
        var sb = new StringBuilder();
        for (var i = 0; i < s.Length; i++)
        {
            if (i > 0 && char.IsUpper(s[i])) sb.Append('_');
            sb.Append(char.ToUpperInvariant(s[i]));
        }
        return sb.ToString();
    }
}
