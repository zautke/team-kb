namespace TeamKb.Core;

/// <summary>
/// The constitution's gates, as code. C1/C6/C7 are structurally unrepresentable at the API
/// (enums + computed paths); this validator enforces what remains representable:
/// C2 identity key, C3 signatures, C4 referential integrity, I1 connectivity, I4 dedup,
/// provenance, hypothesis ceiling, tag registry.
/// </summary>
public sealed class NoteValidator(IVaultIndex index)
{
    public const double TitleSimilarityTheta = 0.85;

    public IReadOnlyList<GateViolation> Validate(Note note)
    {
        var v = new List<GateViolation>();

        // C2 — identity key: permalink unique among active/staged
        if (index.PermalinkExists(note.Permalink))
            v.Add(new("C2", $"Permalink '{note.Permalink}' already exists. Merge or supersede — never suffix."));

        // C3 — edge signature
        foreach (var r in note.Relations)
        {
            var (dom, rng) = Ontology.Signature(r.Verb);
            if (dom is not null && !dom.Contains(note.Class))
                v.Add(new("C3", $"{r.Verb} not valid from class {note.Class} (dom: {string.Join('|', dom)})."));
            if (rng is not null)
            {
                var targetClass = index.ClassOf(r.TargetPermalink);
                if (targetClass is not null && !rng.Contains(targetClass.Value))
                    v.Add(new("C3", $"{r.Verb} target '{r.TargetPermalink}' has class {targetClass} (rng: {string.Join('|', rng)})."));
            }
        }

        // C4 — referential integrity: every target must resolve
        foreach (var r in note.Relations)
            if (!index.PermalinkExists(r.TargetPermalink))
                v.Add(new("C4", $"Relation target '{r.TargetPermalink}' does not exist. Create it first or request an auto-stub."));

        // I1 — connectivity: every write connects, or justifies isolation
        if (note.Relations.Count == 0 && string.IsNullOrWhiteSpace(note.IsolatedJustification))
            v.Add(new("I1", "Note declares no relations. Add at least one, or set isolated_justification."));

        // I4 — identity discipline: near-duplicate titles in same class must merge or distinguish
        foreach (var (permalink, title) in index.TitlesInClass(note.Class))
        {
            if (permalink == note.Permalink) continue;
            if (TitleSimilarity(title, note.Title) > TitleSimilarityTheta)
                v.Add(new("I4", $"Title too similar to existing '{title}' ({permalink}). Merge, supersede, or assert distinct_from."));
        }

        // Provenance (I-1 heritage): at least one non-placeholder entry
        if (note.Provenance.Count == 0)
            v.Add(new("PROV", "At least one provenance entry (source + author) is required."));
        else foreach (var p in note.Provenance)
            if (string.IsNullOrWhiteSpace(p.Source) || p.Source is "TBD" or "TODO" or "unknown")
                v.Add(new("PROV", $"Placeholder provenance source '{p.Source}' rejected."));

        // Hypothesis ceiling (I-4 heritage)
        if (note.Observations.Any(o => o.Kind == ObsKind.Hypothesis) && note.Confidence >= 0.7)
            v.Add(new("HYP", $"Note contains [hypothesis] but confidence {note.Confidence:0.00} ≥ 0.7."));

        // Tag registry (C-3 registry-before-choice): namespaced + registered
        foreach (var t in note.Tags)
            if (!index.TagRegistered(t))
                v.Add(new("TAG", $"Tag '{t}' is not in the registry (_meta/registries/tags.md). Register it in the same commit."));

        return v;
    }

    /// <summary>Cheap normalized-trigram similarity — enough to catch title-vs-slug twins.
    /// ponytail: naive O(n) scan per class, swap for indexed similarity if classes grow >10k notes.</summary>
    public static double TitleSimilarity(string a, string b)
    {
        var na = Ontology.NormalizeTitle(a); var nb = Ontology.NormalizeTitle(b);
        if (na == nb) return 1.0;
        var ta = Trigrams(na); var tb = Trigrams(nb);
        if (ta.Count == 0 || tb.Count == 0) return 0.0;
        var inter = ta.Intersect(tb).Count();
        return (double)inter / (ta.Count + tb.Count - inter);
    }

    private static HashSet<string> Trigrams(string s)
    {
        var set = new HashSet<string>();
        for (var i = 0; i + 3 <= s.Length; i++) set.Add(s.Substring(i, 3));
        return set;
    }
}

/// <summary>Index surface the validator needs — implemented by VaultStore.</summary>
public interface IVaultIndex
{
    bool PermalinkExists(string permalink);
    EntityClass? ClassOf(string permalink);
    IEnumerable<(string Permalink, string Title)> TitlesInClass(EntityClass c);
    bool TagRegistered(string tag);
}
