using TeamKb.Core;
using Xunit;

namespace TeamKb.Tests;

/// <summary>
/// The M0 acceptance suite: each of the master-kb post-mortem failure classes, replayed
/// against the new write path. Every test asserts the defect is REJECTED (or unrepresentable).
/// Fixtures mirror real defects found in the 2026-08-11 audit.
/// </summary>
public sealed class GateTests : IDisposable
{
    private readonly string _dir = Path.Combine(Path.GetTempPath(), "teamkb-test-" + Guid.NewGuid().ToString("N"));
    private readonly VaultStore _store;

    public GateTests() => _store = new VaultStore(_dir);

    public void Dispose() { _store.Dispose(); Directory.Delete(_dir, true); }

    private Note Valid(string title = "Hybrid RAG", EntityClass cls = EntityClass.Concept) => new()
    {
        Title = title, Class = cls, Overview = "Test note.",
        Provenance = [new Provenance("session:test", "agent:test", DateTimeOffset.UtcNow)],
        IsolatedJustification = "test fixture",
    };

    private string CommitValid(string title, EntityClass cls = EntityClass.Concept)
    {
        var r = _store.Propose(Valid(title, cls));
        Assert.True(r.Accepted, string.Join(";", r.Violations.Select(v => v.Message)));
        return _store.Commit(r.ProposalId!);
    }

    // #1 gates-were-prose → validator rejects the write
    [Fact]
    public void MissingProvenance_Rejected()
    {
        var r = _store.Propose(Valid() with { Provenance = [] });
        Assert.False(r.Accepted);
        Assert.Contains(r.Violations, v => v.Gate == "PROV");
    }

    [Fact]
    public void PlaceholderProvenance_Rejected()
    {
        var r = _store.Propose(Valid() with { Provenance = [new("TBD", "agent:test", DateTimeOffset.UtcNow)] });
        Assert.False(r.Accepted);
        Assert.Contains(r.Violations, v => v.Gate == "PROV");
    }

    [Fact]
    public void HypothesisWithHighConfidence_Rejected()
    {
        var r = _store.Propose(Valid() with
        {
            Observations = [new(ObsKind.Hypothesis, "maybe")], Confidence = 0.95,
        });
        Assert.False(r.Accepted);
        Assert.Contains(r.Violations, v => v.Gate == "HYP");
    }

    // #2 free-text wikilinks → C4 write-time resolution
    [Fact]
    public void DanglingRelationTarget_Rejected()
    {
        var r = _store.Propose(Valid() with
        {
            IsolatedJustification = null,
            Relations = [new(Verb.Mentions, "knowledge/concept/does-not-exist", new DateOnly(2026, 8, 11))],
        });
        Assert.False(r.Accepted);
        Assert.Contains(r.Violations, v => v.Gate == "C4");
    }

    // #3 one-sided relations → C5 computed backlinks
    [Fact]
    public void Backlinks_AreComputed()
    {
        var target = CommitValid("Retrieval");
        var r = _store.Propose(Valid("Personalized PageRank") with
        {
            IsolatedJustification = null,
            Relations = [new(Verb.Mentions, target, new DateOnly(2026, 8, 11))],
        });
        Assert.True(r.Accepted);
        var src = _store.Commit(r.ProposalId!);
        var backs = _store.Backlinks(target).ToList();
        Assert.Contains(backs, b => b.Src == src && b.InverseVerb == "MENTIONED_BY");
    }

    // #4 folder anarchy → C1 path computed from class (structural: Note has no path input)
    [Fact]
    public void Path_IsDerivedFromClass()
    {
        var permalink = CommitValid("Team Alpha", EntityClass.Org);
        Assert.StartsWith("knowledge/org/", permalink);
        Assert.True(File.Exists(Path.Combine(_dir, "knowledge/org/team-alpha.md")));
    }

    // #5 no dedup on create → C2 + I4 merge-or-distinguish, never -1 suffix
    [Fact]
    public void ExactPermalinkCollision_Rejected()
    {
        CommitValid("Agent Specialist Color Theory");
        var r = _store.Propose(Valid("Agent Specialist Color Theory"));
        Assert.False(r.Accepted);
        Assert.Contains(r.Violations, v => v.Gate == "C2");
    }

    [Fact]
    public void NearDuplicateTitle_TitleCaseVsSlug_Rejected()
    {
        // the real master-kb twin: "Agent Specialist- Color Theory" vs "agent-specialist-color-theory"
        CommitValid("Agent Specialist- Color Theory");
        var r = _store.Propose(Valid("agent specialist color theory v2"));
        Assert.False(r.Accepted);
        Assert.Contains(r.Violations, v => v.Gate is "I4" or "C2");
    }

    // #6 orphans → I1 every write connects or justifies
    [Fact]
    public void UnlinkedUnjustified_Rejected()
    {
        var r = _store.Propose(Valid() with { IsolatedJustification = null });
        Assert.False(r.Accepted);
        Assert.Contains(r.Violations, v => v.Gate == "I1");
    }

    // #7 vocabulary sprawl → closed enums (structural) + C3 signatures
    [Fact]
    public void EdgeSignatureViolation_Rejected()
    {
        var concept = CommitValid("Some Concept");
        // PRECEDES requires Event → Event; a Concept source must be rejected.
        var r = _store.Propose(Valid("Another Concept") with
        {
            IsolatedJustification = null,
            Relations = [new(Verb.Precedes, concept, new DateOnly(2026, 8, 11))],
        });
        Assert.False(r.Accepted);
        Assert.Contains(r.Violations, v => v.Gate == "C3");
    }

    [Fact]
    public void UnregisteredTag_Rejected()
    {
        var r = _store.Propose(Valid() with { Tags = ["random-freeform-tag"] });
        Assert.False(r.Accepted);
        Assert.Contains(r.Violations, v => v.Gate == "TAG");
    }

    // junk scope (C7) — .bak/conflict unindexable
    [Theory]
    [InlineData("note.md", true)]
    [InlineData("note.md.bak", false)]
    [InlineData("note.bak.md", false)]
    [InlineData("conflict-files-obsidian-git.md", false)]
    [InlineData("note.orig.md", false)]
    public void ScopePredicate(string file, bool inScope) =>
        Assert.Equal(inScope, Ontology.InScope(file));

    // episodes: append-only capture works, immutable same-day duplicate blocked
    [Fact]
    public void EpisodeCapture_AppendOnly()
    {
        var p = _store.CaptureEpisode("Session retro", "It went fine.",
            new Provenance("session:test", "agent:test", DateTimeOffset.UtcNow));
        Assert.StartsWith("episodes/", p);
        Assert.Throws<InvalidOperationException>(() => _store.CaptureEpisode("Session retro", "again",
            new Provenance("session:test", "agent:test", DateTimeOffset.UtcNow)));
    }

    // search honesty: absent verdict, not empty list confusion
    [Fact]
    public void Search_FindsCommitted()
    {
        CommitValid("Bitemporal Invalidation");
        Assert.Contains(_store.Search("bitemporal"), h => h.Title == "Bitemporal Invalidation");
        Assert.Empty(_store.Search("nonexistent-topic-xyz"));
    }
}
