namespace TeamKb.Core;

public sealed record Relation(Verb Verb, string TargetPermalink, DateOnly Since,
    string? Mode = null, double? Confidence = null)
{
    /// <summary>Bi-temporal stamps (Graphiti). TValid defaults to Since at commit.</summary>
    public DateTimeOffset? TValid { get; init; }
    public DateTimeOffset? TInvalid { get; init; }
    public DateTimeOffset? TCreated { get; init; }
    public DateTimeOffset? TExpired { get; init; }
}

public sealed record Observation(ObsKind Kind, string Text, string? ProvenanceRef = null);

public sealed record Provenance(string Source, string Author, DateTimeOffset CapturedAt, double Confidence = 1.0);

public sealed record Note
{
    public required string Title { get; init; }
    public required EntityClass Class { get; init; }
    public string Permalink => $"{Ontology.PathFor(Class)}/{Ontology.NormalizeTitle(Title)}";
    public string Overview { get; init; } = "";
    public IReadOnlyList<Relation> Relations { get; init; } = [];
    public IReadOnlyList<Observation> Observations { get; init; } = [];
    public IReadOnlyList<Provenance> Provenance { get; init; } = [];
    public IReadOnlyList<string> Tags { get; init; } = [];
    public IReadOnlyList<string> Aliases { get; init; } = [];
    public string Status { get; init; } = "active";
    public double Confidence { get; init; } = 1.0;
    /// <summary>I1 escape hatch: a deliberately isolated note must say why.</summary>
    public string? IsolatedJustification { get; init; }
    public DateTimeOffset Created { get; init; } = DateTimeOffset.UtcNow;
    public DateTimeOffset Modified { get; init; } = DateTimeOffset.UtcNow;
}

public sealed record GateViolation(string Gate, string Message);

public sealed record ProposalResult(bool Accepted, string? ProposalId, IReadOnlyList<GateViolation> Violations);
