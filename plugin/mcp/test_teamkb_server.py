#!/usr/bin/env python3
"""Acceptance suite for teamkb_server.py — ported GateTests (real master-kb
defect fixtures) + serializer byte-parity checks + battery-surface tests.
Embedding-dependent paths use a fake embedder (no network in unit tests).
"""
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import teamkb_server as srv


def valid(title="Hybrid RAG", cls="Concept", **kw):
    defaults = dict(
        overview="Test note.",
        relations=[], observations=[],
        provenance=[{"source": "session:test", "author": "agent:test",
                     "captured_at": srv.utcnow(), "confidence": 1.0}],
        isolated_justification="test fixture")
    defaults.update(kw)
    return srv.make_note(title, cls, defaults.pop("overview"),
                         defaults.pop("relations"), defaults.pop("observations"),
                         defaults.pop("provenance"), **defaults)


class StoreCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="teamkb-test-")
        self.store = srv.Store(self.dir)

    def tearDown(self):
        self.store.db.close()
        shutil.rmtree(self.dir)

    def commit_valid(self, title, cls="Concept"):
        pid, violations = self.store.propose(valid(title, cls))
        self.assertIsNotNone(pid, violations)
        return self.store.commit_note(pid)


class GateTests(StoreCase):
    def gates(self, violations):
        return [g for g, _ in violations]

    def test_missing_provenance_rejected(self):
        pid, v = self.store.propose(valid(provenance=[]))
        self.assertIsNone(pid)
        self.assertIn("PROV", self.gates(v))

    def test_placeholder_provenance_rejected(self):
        pid, v = self.store.propose(valid(provenance=[
            {"source": "TBD", "author": "agent:test", "captured_at": srv.utcnow()}]))
        self.assertIsNone(pid)
        self.assertIn("PROV", self.gates(v))

    def test_hypothesis_high_confidence_rejected(self):
        pid, v = self.store.propose(valid(
            observations=[{"kind": "Hypothesis", "text": "maybe", "provenance_ref": None}],
            confidence=0.95))
        self.assertIsNone(pid)
        self.assertIn("HYP", self.gates(v))

    def test_dangling_relation_target_rejected(self):
        pid, v = self.store.propose(valid(
            isolated_justification=None,
            relations=[{"verb": "Mentions", "target": "knowledge/concept/does-not-exist",
                        "since": "2026-08-11", "mode": None, "confidence": None}]))
        self.assertIsNone(pid)
        self.assertIn("C4", self.gates(v))

    def test_backlinks_are_computed(self):
        target = self.commit_valid("Retrieval")
        pid, v = self.store.propose(valid(
            "Personalized PageRank", isolated_justification=None,
            relations=[{"verb": "Mentions", "target": target,
                        "since": "2026-08-11", "mode": None, "confidence": None}]))
        self.assertIsNotNone(pid, v)
        src = self.store.commit_note(pid)
        backs = self.store.backlinks(target)
        self.assertTrue(any(s == src and inv == "MENTIONED_BY" for s, _, inv in backs))

    def test_path_derived_from_class(self):
        permalink = self.commit_valid("Team Alpha", "Org")
        self.assertTrue(permalink.startswith("knowledge/org/"))
        self.assertTrue((Path(self.dir) / "knowledge/org/team-alpha.md").exists())

    def test_exact_permalink_collision_rejected(self):
        self.commit_valid("Agent Specialist Color Theory")
        pid, v = self.store.propose(valid("Agent Specialist Color Theory"))
        self.assertIsNone(pid)
        self.assertIn("C2", self.gates(v))

    def test_near_duplicate_title_rejected(self):
        self.commit_valid("Agent Specialist- Color Theory")
        pid, v = self.store.propose(valid("agent specialist color theory v2"))
        self.assertIsNone(pid)
        self.assertTrue({"I4", "C2"} & set(self.gates(v)))

    def test_unlinked_unjustified_rejected(self):
        pid, v = self.store.propose(valid(isolated_justification=None))
        self.assertIsNone(pid)
        self.assertIn("I1", self.gates(v))

    def test_edge_signature_violation_rejected(self):
        concept = self.commit_valid("Some Concept")
        pid, v = self.store.propose(valid(
            "Another Concept", isolated_justification=None,
            relations=[{"verb": "Precedes", "target": concept,
                        "since": "2026-08-11", "mode": None, "confidence": None}]))
        self.assertIsNone(pid)
        self.assertIn("C3", self.gates(v))

    def test_unregistered_tag_rejected(self):
        pid, v = self.store.propose(valid(tags=["random-freeform-tag"]))
        self.assertIsNone(pid)
        self.assertIn("TAG", self.gates(v))

    def test_scope_predicate(self):
        for name, expect in [("note.md", True), ("note.md.bak", False),
                             ("note.bak.md", False),
                             ("conflict-files-obsidian-git.md", False),
                             ("note.orig.md", False)]:
            self.assertEqual(expect, srv.in_scope(name), name)

    def test_episode_capture_append_only(self):
        prov = {"source": "session:test", "author": "agent:test",
                "captured_at": srv.utcnow(), "confidence": 1.0}
        p = self.store.capture_episode("Session retro", "It went fine.", prov)
        self.assertTrue(p.startswith("episodes/"))
        with self.assertRaises(ValueError):
            self.store.capture_episode("Session retro", "again", prov)

    def test_search_finds_committed(self):
        self.commit_valid("Bitemporal Invalidation")
        hits = self.store.search("bitemporal")
        self.assertTrue(any(t == "Bitemporal Invalidation" for _, t, _ in hits))
        self.assertEqual([], self.store.search("nonexistent-topic-xyz"))

    def test_search_kebab_token_quoted(self):
        self.commit_valid("Hyphen Test Note")
        self.assertEqual([], self.store.search("does-not-exist-kebab"))  # no FTS syntax error

    def test_commit_revalidates(self):
        pid1, _ = self.store.propose(valid("Race Note"))
        pid2, v2 = self.store.propose(valid("Race Note"))
        self.assertIsNotNone(pid2, v2)  # both staged before either committed
        self.store.commit_note(pid1)
        with self.assertRaises(ValueError) as cm:
            self.store.commit_note(pid2)
        self.assertIn("Commit blocked: C2", str(cm.exception))


class SerializerParity(unittest.TestCase):
    def test_frontmatter_shape(self):
        n = srv.make_note(
            "Team Alpha", "Org", "An org.",
            [{"verb": "PartOf", "target": "knowledge/org/parent", "since": "2026-08-11",
              "mode": "implements", "confidence": 0.8}],
            [{"kind": "Fact", "text": "exists", "provenance_ref": "url:https://x"}],
            [{"source": "session:test", "author": "user",
              "captured_at": datetime(2026, 8, 11, 14, 30, tzinfo=timezone.utc),
              "confidence": 1.0}],
            confidence=0.65, tags=["domain/rag"], aliases=["alpha"])
        n["created"] = n["modified"] = datetime(2026, 8, 11, 14, 30, tzinfo=timezone.utc)
        md = srv.to_markdown(n)
        lines = md.splitlines()
        self.assertEqual(lines[0], "---")
        self.assertEqual(lines[1], 'title: "Team Alpha"')
        self.assertEqual(lines[2], "type: entity")
        self.assertEqual(lines[3], 'kb_version: "1.0.0"')
        self.assertEqual(lines[4], "entity_class: Org")
        self.assertEqual(lines[5], "permalink: knowledge/org/team-alpha")
        self.assertEqual(lines[6], "created: 2026-08-11T14:30")   # unquoted, no seconds
        self.assertEqual(lines[8], "status: active")
        self.assertEqual(lines[9], "confidence: 0.65")
        self.assertEqual(lines[10], 'aliases: ["alpha"]')          # flow style
        self.assertIn("tags:", lines)
        ti = lines.index("tags:")
        self.assertEqual(lines[ti + 1], "  - kb/org")              # tag plane first
        self.assertEqual(lines[ti + 2], "  - kb/status/active")
        self.assertEqual(lines[ti + 3], "  - domain/rag")
        self.assertIn('    captured_at: "2026-08-11T14:30:00Z"', md)  # quoted + Z + seconds
        self.assertIn("- PART_OF :: [[knowledge/org/parent]] "
                      "{since: 2026-08-11, mode: implements, confidence: 0.8}", md)
        self.assertIn("- [fact] exists (provenance: url:https://x)", md)

    def test_confidence_format(self):
        self.assertEqual("1.0", srv.fmt_conf(1.0))
        self.assertEqual("0.65", srv.fmt_conf(0.65))
        self.assertEqual("0.5", srv.fmt_conf(0.5))

    def test_screaming_snake(self):
        self.assertEqual("IS_A", srv.screaming_snake("IsA"))
        self.assertEqual("DERIVES_FROM", srv.screaming_snake("DerivesFrom"))

    def test_normalize_title(self):
        self.assertEqual("agent-specialist-color-theory",
                         srv.normalize_title("Agent Specialist- Color Theory"))


class ParserRoundTrip(unittest.TestCase):
    def rich_note(self):
        n = srv.make_note(
            "Team Alpha", "Org", "An org.\n\nWith two paragraphs.",
            [{"verb": "PartOf", "target": "knowledge/org/parent", "since": "2026-08-11",
              "mode": "implements", "confidence": 0.8},
             {"verb": "Mentions", "target": "knowledge/concept/x", "since": "2026-08-12",
              "mode": None, "confidence": None}],
            [{"kind": "Fact", "text": "exists", "provenance_ref": "url:https://x"},
             {"kind": "Hypothesis", "text": "maybe grows", "provenance_ref": None}],
            [{"source": "session:test", "author": "user",
              "captured_at": datetime(2026, 8, 11, 14, 30, tzinfo=timezone.utc),
              "confidence": 1.0}],
            confidence=0.65, tags=["domain/rag"], aliases=["alpha", "team-a"])
        n["created"] = n["modified"] = datetime(2026, 8, 11, 14, 30, tzinfo=timezone.utc)
        return n

    def test_markdown_round_trips_byte_for_byte(self):
        md = srv.to_markdown(self.rich_note())
        self.assertEqual(md, srv.to_markdown(srv.parse_markdown(md)))

    def test_parsed_fields_match_original(self):
        n = self.rich_note()
        back = srv.parse_markdown(srv.to_markdown(n))
        for field in ("title", "class", "permalink", "status", "confidence",
                      "overview", "aliases", "tags"):
            self.assertEqual(n[field], back[field], field)
        self.assertEqual(2, len(back["relations"]))
        self.assertEqual("PartOf", back["relations"][0]["verb"])
        self.assertEqual(0.8, back["relations"][0]["confidence"])
        self.assertIsNone(back["relations"][1]["mode"])
        self.assertEqual("Hypothesis", back["observations"][1]["kind"])
        self.assertEqual("url:https://x", back["observations"][0]["provenance_ref"])
        self.assertEqual("session:test", back["provenance"][0]["source"])
        self.assertEqual(n["created"], back["created"])

    def test_isolated_justification_and_episode_round_trip(self):
        n = srv.make_note("Session retro", "Event", "It went fine.", [], [],
                          [{"source": "session:test", "author": "agent:test",
                            "captured_at": datetime(2026, 8, 11, 9, 0, tzinfo=timezone.utc),
                            "confidence": 1.0}],
                          isolated_justification="episodic capture; linked at consolidation")
        md = srv.to_markdown(n)
        self.assertEqual(md, srv.to_markdown(srv.parse_markdown(md)))
        self.assertEqual("episodic capture; linked at consolidation",
                         srv.parse_markdown(md)["isolated_justification"])

    def test_parser_rejects_garbage(self):
        with self.assertRaises(ValueError):
            srv.parse_markdown("no frontmatter here")


class RebuildTests(StoreCase):
    def test_index_rebuilds_from_markdown_alone(self):
        self.store.register_tag("domain/rag")
        target = self.commit_valid("Retrieval Target")
        pid, v = self.store.propose(valid(
            "Rebuild Source", isolated_justification=None, tags=["domain/rag"],
            observations=[{"kind": "Fact", "text": "distinctive bitemporal marker",
                           "provenance_ref": None}],
            relations=[{"verb": "Mentions", "target": target, "since": "2026-08-12",
                        "mode": None, "confidence": None}]))
        self.assertIsNotNone(pid, v)
        src = self.store.commit_note(pid)

        # nuke every derived table — markdown files are all that remain
        for table in ("notes", "edges", "note_tags", "notes_fts"):
            self.store.db.execute(f"DELETE FROM {table}")
        self.store.db.commit()
        self.assertEqual([], self.store.search("bitemporal"))

        report = json.loads(srv.t_reindex(self.store, {"rebuild": True}))
        self.assertEqual([], report["rebuilt"]["parse_failures"])
        self.assertEqual(2, report["rebuilt"]["files_parsed"])
        self.assertEqual(2, report["notes"])

        # every retrieval modality works again off the rebuilt index
        self.assertTrue(any(p == src for p, _, _ in self.store.search("bitemporal")))
        self.assertTrue(any(s == src and inv == "MENTIONED_BY"
                            for s, _, inv in self.store.backlinks(target)))
        self.assertIn(src, srv.t_search_by_tag(self.store, {"tag": "domain/rag"}))
        self.assertIn(src, srv.t_search_by_tag(self.store, {"tag": "kb/concept",
                                                            "prefix": True}))

    def test_rebuild_reports_unparseable_files(self):
        self.commit_valid("Good Note")
        (Path(self.dir) / "knowledge/concept/broken.md").write_text("not a note\n")
        report = json.loads(srv.t_reindex(self.store, {"rebuild": True}))
        self.assertEqual(1, report["rebuilt"]["files_parsed"])
        self.assertEqual(1, len(report["rebuilt"]["parse_failures"]))
        self.assertIn("broken.md", report["rebuilt"]["parse_failures"][0]["path"])


FAKE_DIM = 8


def fake_embed(texts, prefix, doc=None, phase=None):
    """Deterministic pseudo-embeddings: hash-derived, normalized. Prefix shifts nothing
    (parity between doc and query spaces for testing)."""
    out = []
    for t in texts:
        h = abs(hash(t.replace(srv.QUERY_PREFIX, "").replace(srv.DOC_PREFIX, ""))) or 1
        v = [((h >> (i * 4)) % 97) / 97.0 + 0.01 for i in range(FAKE_DIM)]
        out.append(srv.l2norm(v))
    return out


class BatterySurface(StoreCase):
    def setUp(self):
        super().setUp()
        self.corpus = Path(tempfile.mkdtemp(prefix="teamkb-corpus-"))
        (self.corpus / "doc1.md").write_text(
            "# Alpha\n\nIntro text about retrieval systems.\n\n## Detail\n" + "x" * 3000)

    def tearDown(self):
        shutil.rmtree(self.corpus)
        super().tearDown()

    def test_submit_dedupe_and_scope(self):
        r1 = json.loads(srv.t_submit_document(self.store, {"path": str(self.corpus / "doc1.md")}))
        self.assertTrue(r1["submission_id"].startswith("sub-"))
        r2 = srv.t_submit_document(self.store, {"path": str(self.corpus / "doc1.md")})
        self.assertTrue(r2.startswith("DUPLICATE"))
        r3 = srv.t_submit_document(self.store, {"path": str(self.corpus / "nope.md.bak")})
        self.assertTrue(r3.startswith("REJECTED"))

    def test_chunking_heading_aware_with_overlap(self):
        text = "# H1\n\n" + "a" * 5000 + "\n\n## H2\n\nshort"
        chunks = srv.chunk_markdown(text)
        self.assertGreater(len(chunks), 2)
        h1 = [c for c in chunks if c["heading_path"] == "H1"]
        self.assertGreater(len(h1), 1)  # size cap split
        self.assertEqual(h1[1]["span"][0], srv.CHUNK_CHARS - srv.OVERLAP_CHARS)
        h2 = [c for c in chunks if c["heading_path"] == "H1 > H2"][0]
        self.assertIn("short", h2["text"])  # section text keeps its heading line for context

    @mock.patch.object(srv, "embed_texts", side_effect=fake_embed)
    def test_ingest_semantic_and_link(self, _):
        sid = json.loads(srv.t_submit_document(
            self.store, {"path": str(self.corpus / "doc1.md")}))["submission_id"]
        rep = json.loads(srv.t_ingest_chunks(self.store, {"submissionId": sid}))
        self.assertGreaterEqual(rep["chunks"], 2)
        # semantic search by target finds nothing else (honest absent)
        out = srv.t_semantic_search(self.store, {"target": sid})
        self.assertIn("verdict: absent", out)
        # commit + link, then query search resolves permalinks
        permalink = self.commit_valid("Alpha Doc", "Artifact")
        self.assertIn("LINKED", srv.t_link_submission(
            self.store, {"submissionId": sid, "permalink": permalink}))
        row = self.store.db.execute(
            "SELECT permalink, status FROM submissions WHERE id=?", (sid,)).fetchone()
        self.assertEqual((permalink, "committed"), row)

    @mock.patch.object(srv, "embed_texts", side_effect=fake_embed)
    def test_ingest_failure_marks_failed(self, m):
        m.side_effect = srv.EmbedError("endpoint down")
        sid = json.loads(srv.t_submit_document(
            self.store, {"path": str(self.corpus / "doc1.md")}))["submission_id"]
        out = srv.t_ingest_chunks(self.store, {"submissionId": sid})
        self.assertTrue(out.startswith("FAILED"))
        self.assertEqual("failed", self.store.db.execute(
            "SELECT status FROM submissions WHERE id=?", (sid,)).fetchone()[0])

    def test_search_by_tag_and_prefix(self):
        self.store.register_tag("domain/rag")
        pid, v = self.store.propose(valid("Tagged Note", tags=["domain/rag"]))
        self.assertIsNotNone(pid, v)
        self.store.commit_note(pid)
        self.assertIn("knowledge/concept/tagged-note",
                      srv.t_search_by_tag(self.store, {"tag": "domain/rag"}))
        self.assertIn("knowledge/concept/tagged-note",
                      srv.t_search_by_tag(self.store, {"tag": "kb/concept", "prefix": True}))
        self.assertIn("verdict: absent", srv.t_search_by_tag(self.store, {"tag": "domain/none"}))

    def test_register_tag_hardening(self):
        self.assertIn("REJECTED", srv.t_register_tag(self.store, {"tag": "freeform"}))
        self.assertIn("REJECTED", srv.t_register_tag(self.store, {"tag": "kb/concept"}))
        self.assertEqual("REGISTERED domain/retrieval",
                         srv.t_register_tag(self.store, {"tag": "domain/retrieval"}))
        self.assertIn("too similar",
                      srv.t_register_tag(self.store, {"tag": "domain/retrievals"}))

    def test_add_relations_gated_and_written(self):
        a = self.commit_valid("Note A")
        b = self.commit_valid("Note B")
        out = srv.t_add_relations(self.store, {"permalink": a, "relations": [
            {"verb": "Mentions", "target": b, "since": "2026-08-12"}]})
        self.assertIn("ADDED 1", out)
        md = self.store.read_markdown(a)
        self.assertIn(f"- MENTIONS :: [[{b}]] {{since: 2026-08-12}}", md)
        self.assertTrue(any(s == a for s, _, _ in self.store.backlinks(b)))
        bad = srv.t_add_relations(self.store, {"permalink": a, "relations": [
            {"verb": "Mentions", "target": "knowledge/concept/ghost", "since": "2026-08-12"}]})
        self.assertIn("[C4]", bad)

    def test_semantic_theta_seeded_at_calibrated_value(self):
        # a fresh vault must start at the calibrated floor, not the original guess
        self.assertEqual("0.30", self.store.meta_get("semantic_theta"))

    def test_reindex_report(self):
        self.commit_valid("Indexed Note")
        rep = json.loads(srv.t_reindex(self.store, {}))
        self.assertEqual(1, rep["notes"])
        self.assertEqual([], rep["missing_files"])
        self.assertIn(str(self.store.root), rep["vault"])


class EventLogTests(StoreCase):
    def setUp(self):
        super().setUp()
        self.events = Path(self.dir) / "events.jsonl"
        srv._events["fp"] = self.events.open("a")
        srv._events["seq"] = 0
        srv.RUN_ID = "run-test"

    def tearDown(self):
        srv._events["fp"].close()
        srv._events["fp"] = None
        super().tearDown()

    def lines(self):
        return [json.loads(l) for l in self.events.read_text().splitlines() if l.strip()]

    def test_gate_events_record_every_gate(self):
        self.store.propose(valid(provenance=[]))
        ev = [e for e in self.lines() if e["kind"] == "gate.eval"][0]
        self.assertEqual(srv.ALL_GATES, ev["gates_evaluated"])
        self.assertIn("PROV", ev["gates_failed"])
        self.assertIn("C2", ev["gates_passed"])
        self.assertFalse(ev["ok"])
        self.assertEqual(1, ev["n_violations"])
        self.assertEqual("run-test", ev["run_id"])
        self.assertIsNotNone(ev["duration_ms"])

    def test_tool_call_emits_start_end_with_metrics(self):
        srv.handle(self.store, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                "params": {"name": "search_notes",
                                           "arguments": {"query": "nothing here"}}}, None)
        kinds = [e["kind"] for e in self.lines()]
        self.assertIn("tool.start", kinds)
        end = [e for e in self.lines() if e["kind"] == "tool.end"][0]
        self.assertEqual("GA-3.retrieve.fts", end["phase"])
        self.assertEqual("absent", end["verdict"])
        self.assertEqual(0, end["n_hits"])
        self.assertGreaterEqual(end["duration_ms"], 0)

    def test_chunk_and_embed_events(self):
        corpus = Path(self.dir) / "src.md"
        corpus.write_text("# H\n\n" + "y" * 3000)
        with mock.patch.object(srv, "embed_texts", side_effect=fake_embed):
            sid = json.loads(srv.t_submit_document(self.store, {"path": str(corpus)}))["submission_id"]
            srv.t_ingest_chunks(self.store, {"submissionId": sid})
        chunk_ev = [e for e in self.lines() if e["kind"] == "chunk.done"][0]
        self.assertEqual("CA-2.chunk", chunk_ev["phase"])
        self.assertEqual(sid, chunk_ev["doc"])
        self.assertGreaterEqual(chunk_ev["n_chunks"], 2)
        self.assertEqual(srv.CHUNK_CHARS, chunk_ev["cap"])
        self.assertIn("headings", chunk_ev)

    def test_embed_batch_events_record_retries(self):
        calls = {"n": 0}

        def flaky(*a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                raise TimeoutError("read timed out")
            return type("R", (), {"read": lambda s: json.dumps(
                {"embeddings": [[0.1] * 8]}).encode(),
                "__enter__": lambda s: s, "__exit__": lambda *x: None})()

        with mock.patch.object(srv.urllib.request, "urlopen", side_effect=flaky):
            srv.embed_texts(["hello"], srv.DOC_PREFIX, doc="sub-x")
        batches = [e for e in self.lines() if e["kind"] == "embed.batch"]
        self.assertEqual(2, len(batches))
        self.assertFalse(batches[0]["ok"])
        self.assertIn("TimeoutError", batches[0]["error"])
        self.assertTrue(batches[1]["ok"])
        self.assertEqual(2, batches[1]["attempt"])
        done = [e for e in self.lines() if e["kind"] == "embed.done"][0]
        self.assertEqual("sub-x", done["doc"])
        self.assertEqual(1, done["n_texts"])

    def test_pipeline_context_attributes_docless_tools(self):
        corpus = Path(self.dir) / "ctx.md"
        corpus.write_text("# C\n\nbody")
        with mock.patch.object(srv, "embed_texts", side_effect=fake_embed):
            out = srv.handle(self.store, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                          "params": {"name": "submit_document",
                                                     "arguments": {"path": str(corpus)}}}, None)
            sid = json.loads(out["result"]["content"][0]["text"])["submission_id"]
            self.store.register_tag("domain/x", "an x")
            srv.handle(self.store, {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                    "params": {"name": "suggest_tags",
                                               "arguments": {"text": "about x"}}}, None)
        tag_ev = [e for e in self.lines()
                  if e["kind"] == "tool.end" and e["tool"] == "suggest_tags"][0]
        self.assertEqual(sid, tag_ev["doc"])          # attributed to the in-flight doc
        # a retrieval call clears the context so corpus-level work isn't misattributed
        srv.handle(self.store, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                "params": {"name": "search_notes",
                                           "arguments": {"query": "x"}}}, None)
        with mock.patch.object(srv, "embed_texts", side_effect=fake_embed):
            srv.handle(self.store, {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                                    "params": {"name": "suggest_tags",
                                               "arguments": {"text": "later"}}}, None)
        later = [e for e in self.lines()
                 if e["kind"] == "tool.end" and e["tool"] == "suggest_tags"][-1]
        self.assertIsNone(later["doc"])

    def test_log_event_tool_captures_agent_steps(self):
        out = srv.t_log_event(self.store, {
            "phase": "CA-1.strategy", "doc": "sub-1", "summary": "default strategy",
            "metrics": {"strategy": "default", "reason": "single-note artifact"}})
        self.assertIn("LOGGED CA-1.strategy", out)
        ev = [e for e in self.lines() if e["phase"] == "CA-1.strategy"][0]
        self.assertEqual("agent.step", ev["kind"])
        self.assertEqual("default", ev["strategy"])
        self.assertEqual("sub-1", ev["doc"])

    def test_rollup_groups_by_document(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        import metrics_rollup

        corpus = Path(self.dir) / "doc.md"
        corpus.write_text("# T\n\nbody text here")
        with mock.patch.object(srv, "embed_texts", side_effect=fake_embed):
            sid = json.loads(srv.t_submit_document(self.store, {"path": str(corpus)}))["submission_id"]
            srv.t_ingest_chunks(self.store, {"submissionId": sid})
        srv.t_log_event(self.store, {"phase": "CA-1.strategy", "doc": sid,
                                     "metrics": {"strategy": "default"}})
        pid, _ = self.store.propose(valid("Rollup Doc", "Artifact"))
        permalink = self.store.commit_note(pid)
        srv.handle(self.store, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                "params": {"name": "link_submission",
                                           "arguments": {"submissionId": sid,
                                                         "permalink": permalink}}}, None)
        rows = metrics_rollup.rollup(self.lines())
        row = [r for r in rows if r["doc"] == permalink][0]
        self.assertIn(sid, row["submission_ids"])       # submission aliased to permalink
        self.assertIn("CA-2.chunk", row["phases"])      # pre-commit phase rolled in
        self.assertIn("CA-1.strategy", row["phases"])   # agent step rolled in
        self.assertGreater(row["total_ms"], 0)


class ProtocolTests(StoreCase):
    def test_initialize_tools_list_call(self):
        init = srv.handle(self.store, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                       "params": {}}, None)
        self.assertEqual("2025-06-18", init["result"]["protocolVersion"])
        listed = srv.handle(self.store, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, None)
        names = [t["name"] for t in listed["result"]["tools"]]
        for expected in ["propose_note", "commit_note", "capture_episode", "search_notes",
                         "read_note", "register_tag", "submit_document", "ingest_chunks",
                         "link_submission", "semantic_search", "suggest_tags",
                         "search_by_tag", "add_relations", "reindex"]:
            self.assertIn(expected, names)
        # enum enforcement is visible in the schema (tier-1 constitution gate)
        prop = next(t for t in listed["result"]["tools"] if t["name"] == "propose_note")
        self.assertEqual(srv.CLASSES, prop["inputSchema"]["properties"]["entityClass"]["enum"])
        self.assertEqual(srv.VERBS, prop["inputSchema"]["properties"]["relations"]
                         ["items"]["properties"]["verb"]["enum"])
        call = srv.handle(self.store, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                       "params": {"name": "search_notes",
                                                  "arguments": {"query": "anything"}}}, None)
        self.assertIn("verdict: absent", call["result"]["content"][0]["text"])
        self.assertFalse(call["result"]["isError"])

    def test_unknown_method_clean_error(self):
        resp = srv.handle(self.store, {"jsonrpc": "2.0", "id": 9,
                                       "method": "server/discover"}, None)
        self.assertEqual(-32601, resp["error"]["code"])

    def test_tool_error_is_content_not_protocol_error(self):
        resp = srv.handle(self.store, {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                                       "params": {"name": "commit_note",
                                                  "arguments": {"proposalId": "prop-x"}}}, None)
        self.assertTrue(resp["result"]["isError"])
        self.assertIn("No staged proposal 'prop-x'.", resp["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
