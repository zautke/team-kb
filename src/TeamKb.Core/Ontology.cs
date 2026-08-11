namespace TeamKb.Core;

/// <summary>
/// Ontology v1.0.0 — the closed sets T, P, K of the constitution's formal model.
/// These enums surface directly in MCP tool JSON Schemas: an off-vocabulary value is
/// unrepresentable at the API (post-mortem countermeasure #7).
/// </summary>
public enum EntityClass
{
    Person, Org, Project, Codebase, Technology, Artifact, Concept, Event, Decision, Agent,
}

public enum Verb
{
    IsA, PartOf, DependsOn, Uses, Causes, Precedes, Supersedes,
    DerivesFrom, Describes, Governs, Owns, Addresses, Contradicts, Mentions,
}

public enum ObsKind
{
    Fact, Hypothesis, Decision, Constraint, Preference, Lesson,
    Procedure, Risk, Question, Status, Contradiction, Deprecated,
}

public enum Tier { Inbox, Episode, Knowledge, Playbook, Procedure, Hub }

public static class Ontology
{
    public const string Version = "1.0.0";

    /// <summary>C1 — folder path derived from class. Authors never supply paths.</summary>
    public static string PathFor(EntityClass c) => c switch
    {
        EntityClass.Event => "episodes",
        _ => $"knowledge/{c.ToString().ToLowerInvariant()}",
    };

    /// <summary>C5 — computed inverse names. Direction is stored once; inverses are derived.</summary>
    public static string InverseName(Verb v) => v switch
    {
        Verb.IsA => "HAS_INSTANCE",
        Verb.PartOf => "HAS_PART",
        Verb.DependsOn => "REQUIRED_BY",
        Verb.Uses => "USED_BY",
        Verb.Causes => "CAUSED_BY",
        Verb.Precedes => "FOLLOWS",
        Verb.Supersedes => "SUPERSEDED_BY",
        Verb.DerivesFrom => "SOURCE_OF",
        Verb.Describes => "DESCRIBED_BY",
        Verb.Governs => "GOVERNED_BY",
        Verb.Owns => "OWNED_BY",
        Verb.Addresses => "ADDRESSED_BY",
        Verb.Contradicts => "CONTRADICTS", // symmetric
        Verb.Mentions => "MENTIONED_BY",
        _ => throw new ArgumentOutOfRangeException(nameof(v)),
    };

    /// <summary>C3 — edge signatures σ(p) = (dom, rng). Null set = any class.</summary>
    public static (EntityClass[]? Dom, EntityClass[]? Rng) Signature(Verb v) => v switch
    {
        Verb.IsA => (null, new[] { EntityClass.Concept }),
        Verb.DependsOn => (new[] { EntityClass.Project, EntityClass.Codebase, EntityClass.Artifact, EntityClass.Technology }, null),
        Verb.Uses => (null, new[] { EntityClass.Technology, EntityClass.Artifact, EntityClass.Codebase }),
        Verb.Causes => (new[] { EntityClass.Event, EntityClass.Decision }, new[] { EntityClass.Event, EntityClass.Decision, EntityClass.Project }),
        Verb.Precedes => (new[] { EntityClass.Event }, new[] { EntityClass.Event }),
        Verb.DerivesFrom => (new[] { EntityClass.Artifact, EntityClass.Concept, EntityClass.Decision }, null),
        Verb.Describes => (new[] { EntityClass.Artifact, EntityClass.Concept }, null),
        Verb.Governs => (new[] { EntityClass.Artifact }, null),
        Verb.Owns => (new[] { EntityClass.Person, EntityClass.Org, EntityClass.Agent }, null),
        Verb.Addresses => (new[] { EntityClass.Artifact, EntityClass.Decision, EntityClass.Project }, new[] { EntityClass.Event, EntityClass.Concept }),
        _ => (null, null), // PartOf, Supersedes, Contradicts, Mentions: unconstrained
    };

    /// <summary>C2 — permalink = norm(title): lowercase kebab, ascii, collapsed.</summary>
    public static string NormalizeTitle(string title)
    {
        var slug = new string(title.Trim().ToLowerInvariant()
            .Select(ch => char.IsLetterOrDigit(ch) ? ch : '-').ToArray());
        while (slug.Contains("--")) slug = slug.Replace("--", "-");
        return slug.Trim('-');
    }

    /// <summary>C7 — scope predicate: junk is unindexable.</summary>
    public static bool InScope(string fileName) =>
        fileName.EndsWith(".md", StringComparison.OrdinalIgnoreCase)
        && !System.Text.RegularExpressions.Regex.IsMatch(
            fileName, @"(\.bak|conflict|~|\.orig)(\.md)?$", System.Text.RegularExpressions.RegexOptions.IgnoreCase);
}
