#!/usr/bin/env python3
"""team-kb MCP server — zero-dependency stdlib stdio JSON-RPC.

Byte-parity port of the C# M0 stack (src/TeamKb.Core + TeamKb.Mcp): 6 tools,
8 gates, serializer, FTS5 index — exact strings preserved. Plus the M0.5
battery surface: submissions, deterministic chunking, hosted embeddings,
semantic/tag search, reindex, add_relations.

Protocol: legacy MCP initialize handshake (dual-era clients fall back to it);
unknown methods get a clean JSON-RPC error. stdout is protocol ONLY; all
logging goes to stderr. Exits on stdin EOF.

Config (env, SSoT — no fallbacks for the vault):
  TEAMKB_VAULT         required. Vault root.
  TEAMKB_EMBED_URL     no default — required for the http backend
  TEAMKB_EMBED_MODEL   default nomic-embed-text-v2-moe:latest
  TEAMKB_CORPUS_ROOTS  optional colon-separated allowed submit roots
  TEAMKB_TRACE         "1" → append every tools/call req+resp to
                       $TEAMKB_VAULT/.teamkb-trace.jsonl
"""
import hashlib
import json
import logging
import math
import os
import re
import sqlite3
import struct
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("teamkb")
logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="[teamkb] %(levelname)s %(message)s")

# ── Event log: structured per-phase metrics + events, one JSON object per line.
# Always on (cheap, append-only); path override via TEAMKB_EVENTS.
# Correlation keys on every line: run_id, seq, doc (submission id / permalink /
# source path), phase (runbook step), kind (event type).

RUN_ID = os.environ.get("TEAMKB_RUN_ID", "")
_events = {"fp": None, "seq": 0}


def emit(kind, phase=None, doc=None, duration_ms=None, ok=True, **fields):
    """Append one event line. Never raises — telemetry must not break the pipe."""
    fp = _events["fp"]
    if fp is None:
        return
    _events["seq"] += 1
    rec = {"ts": utcnow().isoformat(), "run_id": RUN_ID, "seq": _events["seq"],
           "kind": kind, "phase": phase, "doc": doc, "ok": ok}
    if duration_ms is not None:
        rec["duration_ms"] = round(duration_ms, 2)
    rec.update(fields)
    try:
        fp.write(json.dumps(rec, default=str) + "\n")
        fp.flush()
    except Exception as e:  # pragma: no cover - telemetry is best-effort
        log.warning("event emit failed: %s", e)

# ── Ontology (port of Ontology.cs; closed sets surface as JSON-Schema enums) ──

CLASSES = ["Person", "Org", "Project", "Codebase", "Technology", "Artifact",
           "Concept", "Event", "Decision", "Agent"]
VERBS = ["IsA", "PartOf", "DependsOn", "Uses", "Causes", "Precedes", "Supersedes",
         "DerivesFrom", "Describes", "Governs", "Owns", "Addresses", "Contradicts", "Mentions"]
OBS_KINDS = ["Fact", "Hypothesis", "Decision", "Constraint", "Preference", "Lesson",
             "Procedure", "Risk", "Question", "Status", "Contradiction", "Deprecated"]
KB_VERSION = "1.0.0"
THETA_TITLE = 0.85

INVERSE = {
    "IsA": "HAS_INSTANCE", "PartOf": "HAS_PART", "DependsOn": "REQUIRED_BY",
    "Uses": "USED_BY", "Causes": "CAUSED_BY", "Precedes": "FOLLOWS",
    "Supersedes": "SUPERSEDED_BY", "DerivesFrom": "SOURCE_OF", "Describes": "DESCRIBED_BY",
    "Governs": "GOVERNED_BY", "Owns": "OWNED_BY", "Addresses": "ADDRESSED_BY",
    "Contradicts": "CONTRADICTS", "Mentions": "MENTIONED_BY",
}

SIGNATURE = {  # verb -> (dom, rng); None = unconstrained
    "IsA": (None, ["Concept"]),
    "DependsOn": (["Project", "Codebase", "Artifact", "Technology"], None),
    "Uses": (None, ["Technology", "Artifact", "Codebase"]),
    "Causes": (["Event", "Decision"], ["Event", "Decision", "Project"]),
    "Precedes": (["Event"], ["Event"]),
    "DerivesFrom": (["Artifact", "Concept", "Decision"], None),
    "Describes": (["Artifact", "Concept"], None),
    "Governs": (["Artifact"], None),
    "Owns": (["Person", "Org", "Agent"], None),
    "Addresses": (["Artifact", "Decision", "Project"], ["Event", "Concept"]),
}


def path_for(cls: str) -> str:
    return "episodes" if cls == "Event" else f"knowledge/{cls.lower()}"


def normalize_title(title: str) -> str:
    slug = "".join(ch if ch.isalnum() else "-" for ch in title.strip().lower())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def permalink_for(cls: str, title: str) -> str:
    return f"{path_for(cls)}/{normalize_title(title)}"


def screaming_snake(verb: str) -> str:
    out = []
    for i, ch in enumerate(verb):
        if i > 0 and ch.isupper():
            out.append("_")
        out.append(ch.upper())
    return "".join(out)


VERB_FROM_SNAKE = {screaming_snake(v): v for v in VERBS}
_SCOPE_JUNK = re.compile(r"\.bak|conflict|~|\.orig", re.IGNORECASE)


def in_scope(file_name: str) -> bool:
    return file_name.lower().endswith(".md") and not _SCOPE_JUNK.search(file_name)


def fmt_conf(c: float) -> str:
    """C# '0.0#' — min 1, max 2 decimals (1.0, 0.65, 0.5)."""
    s = f"{c:.2f}".rstrip("0")
    return s + "0" if s.endswith(".") else s


def utcnow():
    return datetime.now(timezone.utc)


# ── Serializer (byte-parity port of MarkdownSerializer.cs) ──────────────────

def to_markdown(n: dict) -> str:
    L = ["---",
         'title: "{}"'.format(n["title"].replace('"', "'")),
         "type: entity",
         f'kb_version: "{KB_VERSION}"',
         f"entity_class: {n['class']}",
         f"permalink: {n['permalink']}",
         f"created: {n['created'].strftime('%Y-%m-%dT%H:%M')}",
         f"modified: {n['modified'].strftime('%Y-%m-%dT%H:%M')}",
         f"status: {n['status']}",
         f"confidence: {fmt_conf(n['confidence'])}"]
    if n.get("aliases"):
        L.append("aliases: [{}]".format(", ".join(f'"{a}"' for a in n["aliases"])))
    tags = [f"kb/{n['class'].lower()}", f"kb/status/{n['status'].lower()}"]
    tags += [t for t in n.get("tags", []) if t not in tags]
    L.append("tags:")
    L += [f"  - {t}" for t in tags]
    if n.get("isolated_justification") is not None:
        L.append('isolated_justification: "{}"'.format(
            n["isolated_justification"].replace('"', "'")))
    L.append("provenance:")
    for p in n["provenance"]:
        L += [f'  - source: "{p["source"]}"',
              f'    author: "{p["author"]}"',
              '    captured_at: "{}"'.format(p["captured_at"].strftime("%Y-%m-%dT%H:%M:%SZ")),
              f"    confidence: {fmt_conf(p.get('confidence', 1.0))}"]
    L += ["---", ""]
    if n.get("overview", "").strip():
        L += ["## Overview", n["overview"].strip(), ""]
    if n.get("relations"):
        L.append("## Relations")
        for r in n["relations"]:
            props = "{{since: {}".format(r["since"])
            if r.get("mode") is not None:
                props += f", mode: {r['mode']}"
            if r.get("confidence") is not None:
                props += f", confidence: {fmt_conf(r['confidence'])}"
            props += "}"
            L.append(f"- {screaming_snake(r['verb'])} :: [[{r['target']}]] {props}")
        L.append("")
    if n.get("observations"):
        L.append("## Observations")
        for o in n["observations"]:
            prov = f" (provenance: {o['provenance_ref']})" if o.get("provenance_ref") else ""
            L.append(f"- [{o['kind'].lower()}] {o['text']}{prov}")
    return "\n".join(L) + "\n"


# ── Parser: markdown → note (exact inverse of to_markdown) ──────────────────
# Markdown is canonical per the constitution; the SQLite index is derived. A
# derived artifact that cannot be re-derived is a defect, so the vault must be
# rebuildable from its own files alone (clone → reindex → working retrieval).

_REL_LINE = re.compile(r"^- ([A-Z_]+) :: \[\[(.+?)\]\] \{(.*)\}$")
_OBS_LINE = re.compile(r"^- \[([a-z]+)\] (.*?)(?: \(provenance: (.+)\))?$")


def _unquote(v: str) -> str:
    v = v.strip()
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] == '"' else v


def parse_markdown(text: str) -> dict:
    """Inverse of to_markdown. Raises ValueError on anything it cannot round-trip."""
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    fm_end = text.index("\n---\n", 3)
    fm, body = text[4:fm_end + 1], text[fm_end + 5:]

    n = {"tags": [], "aliases": [], "provenance": [], "relations": [],
         "observations": [], "overview": "", "isolated_justification": None,
         "status": "active", "confidence": 1.0}
    section = None
    for line in fm.splitlines():
        if not line.strip():
            continue
        if line.startswith(("  - ", "    ")):          # list / nested item
            if section == "tags":
                n["tags"].append(line.strip()[2:])
            elif section == "provenance":
                k, _, v = line.strip().lstrip("- ").partition(": ")
                if k == "source":
                    n["provenance"].append({"source": _unquote(v)})
                elif n["provenance"]:
                    cur = n["provenance"][-1]
                    if k == "captured_at":
                        cur["captured_at"] = datetime.fromisoformat(
                            _unquote(v).replace("Z", "+00:00"))
                    elif k == "confidence":
                        cur["confidence"] = float(v)
                    else:
                        cur[k] = _unquote(v)
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if key in ("tags", "provenance") and not val:
            section = key
            continue
        section = None
        if key == "title":
            n["title"] = _unquote(val)
        elif key == "entity_class":
            n["class"] = val
        elif key == "permalink":
            n["permalink"] = val
        elif key in ("created", "modified"):
            n[key] = datetime.fromisoformat(val).replace(tzinfo=timezone.utc)
        elif key == "status":
            n["status"] = val
        elif key == "confidence":
            n["confidence"] = float(val)
        elif key == "isolated_justification":
            n["isolated_justification"] = _unquote(val)
        elif key == "aliases":
            n["aliases"] = [_unquote(a) for a in val.strip("[]").split(", ") if a]

    for required in ("title", "class", "permalink", "created", "modified"):
        if required not in n:
            raise ValueError(f"frontmatter missing '{required}'")
    # the kb/* plane is server-computed on serialize — never store it as a tag
    n["tags"] = [t for t in n["tags"] if not t.startswith("kb/")]

    part = None
    overview = []
    for line in body.splitlines():
        if line.startswith("## "):
            part = line[3:].strip().lower()
            continue
        if part == "overview":
            overview.append(line)
        elif part == "relations" and line.startswith("- "):
            m = _REL_LINE.match(line)
            if not m:
                raise ValueError(f"unparseable relation line: {line}")
            verb_snake, target, props = m.groups()
            rel = {"verb": VERB_FROM_SNAKE[verb_snake], "target": target,
                   "mode": None, "confidence": None}
            for prop in props.split(", "):
                k, _, v = prop.partition(": ")
                if k == "since":
                    rel["since"] = v
                elif k == "mode":
                    rel["mode"] = v
                elif k == "confidence":
                    rel["confidence"] = float(v)
            n["relations"].append(rel)
        elif part == "observations" and line.startswith("- ["):
            m = _OBS_LINE.match(line)
            if not m:
                raise ValueError(f"unparseable observation line: {line}")
            kind, obs_text, prov = m.groups()
            n["observations"].append({
                "kind": kind.capitalize() if kind != "isa" else kind,
                "text": obs_text, "provenance_ref": prov})
    n["overview"] = "\n".join(overview).strip()
    return n


# ── Validator (port of NoteValidator.cs — exact gate messages) ───────────────

def trigrams(s: str):
    return {s[i:i + 3] for i in range(len(s) - 2)}


def title_similarity(a: str, b: str) -> float:
    na, nb = normalize_title(a), normalize_title(b)
    if na == nb:
        return 1.0
    ta, tb = trigrams(na), trigrams(nb)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    return inter / (len(ta) + len(tb) - inter)


ALL_GATES = ["C2", "C3", "C4", "I1", "I4", "PROV", "HYP", "TAG"]


def validate(store, n: dict, stage="propose"):
    t0 = time.perf_counter()
    v = _validate(store, n)
    failed = sorted({g for g, _ in v})
    emit("gate.eval", phase=f"CA-7.{stage}", doc=n.get("permalink"),
         duration_ms=(time.perf_counter() - t0) * 1000, ok=not v,
         gates_evaluated=ALL_GATES, gates_failed=failed,
         gates_passed=[g for g in ALL_GATES if g not in failed],
         n_violations=len(v),
         violations=[{"gate": g, "message": m} for g, m in v],
         n_relations=len(n.get("relations", [])),
         n_observations=len(n.get("observations", [])),
         n_tags=len(n.get("tags", [])), entity_class=n.get("class"),
         confidence=n.get("confidence"))
    return v


def _validate(store, n: dict):
    v = []
    if store.permalink_exists(n["permalink"]):
        v.append(("C2", f"Permalink '{n['permalink']}' already exists. Merge or supersede — never suffix."))
    for r in n.get("relations", []):
        dom, rng = SIGNATURE.get(r["verb"], (None, None))
        if dom is not None and n["class"] not in dom:
            v.append(("C3", f"{r['verb']} not valid from class {n['class']} (dom: {'|'.join(dom)})."))
        if rng is not None:
            tc = store.class_of(r["target"])
            if tc is not None and tc not in rng:
                v.append(("C3", f"{r['verb']} target '{r['target']}' has class {tc} (rng: {'|'.join(rng)})."))
    for r in n.get("relations", []):
        if not store.permalink_exists(r["target"]):
            v.append(("C4", f"Relation target '{r['target']}' does not exist. Create it first or request an auto-stub."))
    if not n.get("relations") and not (n.get("isolated_justification") or "").strip():
        v.append(("I1", "Note declares no relations. Add at least one, or set isolated_justification."))
    for permalink, title in store.titles_in_class(n["class"]):
        if permalink == n["permalink"]:
            continue
        if title_similarity(title, n["title"]) > THETA_TITLE:
            v.append(("I4", f"Title too similar to existing '{title}' ({permalink}). Merge, supersede, or assert distinct_from."))
    if not n.get("provenance"):
        v.append(("PROV", "At least one provenance entry (source + author) is required."))
    else:
        for p in n["provenance"]:
            if not (p.get("source") or "").strip() or p["source"] in ("TBD", "TODO", "unknown"):
                v.append(("PROV", f"Placeholder provenance source '{p.get('source')}' rejected."))
    if any(o["kind"] == "Hypothesis" for o in n.get("observations", [])) and n["confidence"] >= 0.7:
        v.append(("HYP", f"Note contains [hypothesis] but confidence {n['confidence']:.2f} ≥ 0.7."))
    for t in n.get("tags", []):
        if not store.tag_registered(t):
            v.append(("TAG", f"Tag '{t}' is not in the registry (_meta/registries/tags.md). Register it in the same commit."))
    return v


# ── Embedding client (hosted only — never local weights) ────────────────────

# No default endpoint: committed config must never point at anyone's private
# infrastructure. http backend without an explicit URL fails fast and clean.
EMBED_URL = os.environ.get("TEAMKB_EMBED_URL", "").rstrip("/")
EMBED_BACKEND = os.environ.get("TEAMKB_EMBED_BACKEND", "http")  # http | onnx
ONNX_MODEL_DIR = os.environ.get("TEAMKB_ONNX_MODEL_DIR", "")
EMBED_MODEL = os.environ.get(
    "TEAMKB_EMBED_MODEL",
    "bge-micro-v2-onnx" if EMBED_BACKEND == "onnx" else "nomic-embed-text-v2-moe:latest")

# Task prefixes are a property of the model family, not the backend.
# nomic models REQUIRE search_document:/search_query:; bge models use a bare
# document and an instruction-prefixed query.
if "nomic" in EMBED_MODEL:
    DOC_PREFIX = "search_document: "
    QUERY_PREFIX = "search_query: "
elif "bge" in EMBED_MODEL:
    DOC_PREFIX = ""
    QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
else:
    DOC_PREFIX = ""
    QUERY_PREFIX = ""


class EmbedError(Exception):
    pass


EMBED_BATCH = 8       # large batches time out on the hosted MoE model
EMBED_TIMEOUT = 90


def embed_texts(texts, prefix, doc=None, phase="CA-3.embed"):
    """Batch-embed (sub-batched) via the configured backend. L2-normalized vectors."""
    fn = _embed_batch_onnx if EMBED_BACKEND == "onnx" else _embed_batch_http
    out = []
    t0 = time.perf_counter()
    n_batches = (len(texts) + EMBED_BATCH - 1) // EMBED_BATCH
    for i in range(0, len(texts), EMBED_BATCH):
        out.extend(fn(texts[i:i + EMBED_BATCH], prefix,
                      doc=doc, phase=phase, batch=i // EMBED_BATCH))
    emit("embed.done", phase=phase, doc=doc,
         duration_ms=(time.perf_counter() - t0) * 1000,
         n_texts=len(texts), n_batches=n_batches, dim=len(out[0]) if out else 0,
         model=EMBED_MODEL, backend=EMBED_BACKEND, prefix=prefix.strip(),
         chars=sum(len(t) for t in texts))
    return out


_ONNX = None  # (session, tokenizer, input_names) — lazy, only when backend=onnx


def _onnx_session():
    global _ONNX
    if _ONNX is not None:
        return _ONNX
    try:
        import onnxruntime
        import tokenizers
    except ImportError as e:
        raise EmbedError(
            "TEAMKB_EMBED_BACKEND=onnx requires: pip install onnxruntime tokenizers"
        ) from e
    if not ONNX_MODEL_DIR:
        raise EmbedError("TEAMKB_EMBED_BACKEND=onnx requires TEAMKB_ONNX_MODEL_DIR")
    d = Path(ONNX_MODEL_DIR)
    model = next((p for n in ("model_quantized.onnx", "model.onnx")
                  if (p := d / n).exists()), None)
    tok_file = d / "tokenizer.json"
    if model is None or not tok_file.exists():
        raise EmbedError(f"no model_quantized.onnx/model.onnx + tokenizer.json in {d}")
    sess = onnxruntime.InferenceSession(str(model), providers=["CPUExecutionProvider"])
    tok = tokenizers.Tokenizer.from_file(str(tok_file))
    tok.enable_truncation(max_length=512)   # bge-micro max seq; matches chunk cap
    tok.no_padding()                        # we pad manually per batch
    _ONNX = (sess, tok, [i.name for i in sess.get_inputs()])
    log.info("onnx model=%s dim probe on first batch", model.name)
    return _ONNX


def _embed_batch_onnx(texts, prefix, doc=None, phase="CA-3.embed", batch=0):
    sess, tok, input_names = _onnx_session()
    t0 = time.perf_counter()
    encs = [tok.encode(prefix + t) for t in texts]
    max_len = max(len(e.ids) for e in encs)
    ids = [e.ids + [0] * (max_len - len(e.ids)) for e in encs]
    mask = [[1] * len(e.ids) + [0] * (max_len - len(e.ids)) for e in encs]
    feeds = {"input_ids": ids, "attention_mask": mask}
    if "token_type_ids" in input_names:
        feeds["token_type_ids"] = [[0] * max_len for _ in encs]
    try:
        import numpy as np  # onnxruntime dependency, always present with it
        feeds = {k: np.asarray(v, dtype=np.int64) for k, v in feeds.items()}
        hidden = sess.run(None, feeds)[0]  # (batch, seq, dim) last_hidden_state
    except Exception as e:
        emit("embed.batch", phase=phase, doc=doc, ok=False,
             duration_ms=(time.perf_counter() - t0) * 1000,
             batch=batch, size=len(texts), backend="onnx",
             error=f"{type(e).__name__}: {e}")
        raise EmbedError(f"onnx inference failed: {e}") from e
    m = np.asarray(mask, dtype=np.float32)[:, :, None]
    pooled = (hidden * m).sum(axis=1) / m.sum(axis=1)  # mask-weighted mean pool
    vecs = [l2norm([float(x) for x in row]) for row in pooled]
    emit("embed.batch", phase=phase, doc=doc,
         duration_ms=(time.perf_counter() - t0) * 1000,
         batch=batch, size=len(texts), backend="onnx", attempt=1,
         chars=sum(len(t) for t in texts))
    return vecs


def _embed_batch_http(texts, prefix, doc=None, phase="CA-3.embed", batch=0):
    if not EMBED_URL:
        raise EmbedError(
            "TEAMKB_EMBED_URL is not set. Point it at an Ollama-compatible "
            "/api/embed endpoint, or use TEAMKB_EMBED_BACKEND=onnx for fully "
            "local embeddings (see docs/agent-manual/07-mcp-server-config.md).")
    body = json.dumps({"model": EMBED_MODEL, "input": [prefix + t for t in texts]}).encode()
    # Cloudflare rejects urllib's default "Python-urllib/x" User-Agent with 403.
    req = urllib.request.Request(f"{EMBED_URL}/api/embed", data=body,
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "teamkb-mcp/1.0"})
    last = None
    for attempt in range(3):
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=EMBED_TIMEOUT) as resp:
                data = json.loads(resp.read())
            vecs = [l2norm(v) for v in data["embeddings"]]
            emit("embed.batch", phase=phase, doc=doc,
                 duration_ms=(time.perf_counter() - t0) * 1000,
                 batch=batch, size=len(texts), backend="http", attempt=attempt + 1,
                 chars=sum(len(t) for t in texts))
            return vecs
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as e:
            last = e
            emit("embed.batch", phase=phase, doc=doc, ok=False,
                 duration_ms=(time.perf_counter() - t0) * 1000,
                 batch=batch, size=len(texts), attempt=attempt + 1,
                 error=f"{type(e).__name__}: {e}")
            log.warning("embed attempt %d failed: %s", attempt + 1, e)
    raise EmbedError(f"embedding endpoint failed after 3 attempts: {last}")


def l2norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def pack(v):
    return struct.pack(f"<{len(v)}f", *v)


def unpack(b):
    return list(struct.unpack(f"<{len(b) // 4}f", b))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


# ── Chunker (deterministic, server-side; ~512 tok ≈ 2048 chars, 256 overlap) ─

CHUNK_CHARS = 2048
OVERLAP_CHARS = 256
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def chunk_markdown(text: str):
    """Heading-aware split; size-capped windows with overlap WITHIN a section only."""
    sections, stack = [], []
    pos = 0
    matches = list(_HEADING.finditer(text))
    bounds = [(m.start(), m.group(1), m.group(2).strip()) for m in matches]
    bounds.append((len(text), "", ""))
    if bounds[0][0] > 0:
        sections.append(("(preamble)", text[: bounds[0][0]]))
    for i in range(len(bounds) - 1):
        start, hashes, title = bounds[i]
        depth = len(hashes)
        stack = stack[: depth - 1] + [title]
        sections.append((" > ".join(stack), text[start: bounds[i + 1][0]]))
    chunks = []
    for heading_path, body in sections:
        body = body.strip()
        if not body:
            continue
        i = 0
        while i < len(body):
            piece = body[i: i + CHUNK_CHARS]
            chunks.append({"heading_path": heading_path, "text": piece,
                           "span": [i, i + len(piece)]})
            if i + CHUNK_CHARS >= len(body):
                break
            i += CHUNK_CHARS - OVERLAP_CHARS
    for idx, c in enumerate(chunks):
        c["id"] = idx
    return chunks


# ── Store (port of VaultStore.cs + battery tables) ───────────────────────────

class Store:
    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / ".teamkb.db")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
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
            CREATE TABLE IF NOT EXISTS tags(tag TEXT PRIMARY KEY, description TEXT);
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
              permalink UNINDEXED, title, overview, observations, tokenize='porter unicode61');
            CREATE TABLE IF NOT EXISTS note_tags(
              permalink TEXT NOT NULL, tag TEXT NOT NULL, PRIMARY KEY(permalink, tag));
            CREATE TABLE IF NOT EXISTS submissions(
              id TEXT PRIMARY KEY, source_path TEXT NOT NULL, sha256 TEXT NOT NULL,
              status TEXT NOT NULL CHECK(status IN ('staged','curating','committed','failed')),
              created_at TEXT NOT NULL, permalink TEXT);
            CREATE TABLE IF NOT EXISTS chunks(
              submission_id TEXT NOT NULL, chunk_id INTEGER NOT NULL,
              heading_path TEXT, text TEXT NOT NULL, span TEXT,
              PRIMARY KEY(submission_id, chunk_id));
            CREATE TABLE IF NOT EXISTS chunk_embeddings(
              submission_id TEXT NOT NULL, chunk_id INTEGER NOT NULL, vector BLOB NOT NULL,
              PRIMARY KEY(submission_id, chunk_id));
            CREATE TABLE IF NOT EXISTS doc_embeddings(
              submission_id TEXT PRIMARY KEY, permalink TEXT, vector BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS tag_embeddings(
              tag TEXT PRIMARY KEY, vector BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
        """)
        for t in ("status/anchor", "status/verified", "status/draft",
                  "source/session", "source/web", "source/paper", "source/code"):
            self.db.execute("INSERT OR IGNORE INTO tags(tag) VALUES(?)", (t,))
        # θ is model-specific. nomic v2-moe: calibrated 2026-08-12 (true matches
        # floor ~0.30, absents ceiling ~0.17). bge-micro-v2: calibrated
        # 2026-08-13 (true floor ~0.70, junk ceiling ~0.68 — narrow margin is
        # the model's quality ceiling; recalibrate per corpus if misses appear).
        # Per-vault override: UPDATE meta SET value=... WHERE key='semantic_theta'.
        theta = "0.69" if "bge" in EMBED_MODEL else "0.30"
        self.db.execute("INSERT OR IGNORE INTO meta VALUES('semantic_theta',?)", (theta,))
        self.db.execute("INSERT OR IGNORE INTO meta VALUES(?,?)",
                        ("embed_model", f"{EMBED_MODEL}"))
        self.db.commit()
        # Vector-space guard: vectors from different models are incompatible.
        # A stamped model != the configured model means every stored embedding
        # belongs to another space — refuse the semantic channel, never mix.
        stamped = self.db.execute(
            "SELECT value FROM meta WHERE key='embed_model'").fetchone()[0]
        self.embed_model_mismatch = (
            None if stamped == EMBED_MODEL else
            f"vault embeddings were built with '{stamped}' but the server is "
            f"configured for '{EMBED_MODEL}' — semantic tools disabled. Fix "
            f"TEAMKB_EMBED_MODEL/TEAMKB_EMBED_BACKEND, or wipe embeddings and "
            f"re-ingest to move the vault to the new model's vector space.")
        if self.embed_model_mismatch:
            log.critical(self.embed_model_mismatch)

    # index surface
    def permalink_exists(self, p):
        return self.db.execute("SELECT 1 FROM notes WHERE permalink=?", (p,)).fetchone() is not None

    def class_of(self, p):
        r = self.db.execute("SELECT class FROM notes WHERE permalink=?", (p,)).fetchone()
        return r[0] if r else None

    def titles_in_class(self, cls):
        return self.db.execute("SELECT permalink, title FROM notes WHERE class=?", (cls,)).fetchall()

    def tag_registered(self, t):
        return self.db.execute("SELECT 1 FROM tags WHERE tag=?", (t,)).fetchone() is not None

    def register_tag(self, t, description=None):
        self.db.execute("INSERT OR IGNORE INTO tags(tag, description) VALUES(?,?)", (t, description))
        self.db.commit()

    # write path
    def propose(self, n: dict):
        violations = validate(self, n)
        if violations:
            return None, violations
        pid = "prop-" + utcnow().strftime("%Y%m%d%H%M%S%f")
        self.db.execute("INSERT INTO staged VALUES(?,?,?)",
                        (pid, json.dumps(n, default=str), utcnow().isoformat()))
        self.db.commit()
        return pid, []

    def commit_note(self, pid: str):
        row = self.db.execute("SELECT json FROM staged WHERE id=?", (pid,)).fetchone()
        if row is None:
            raise ValueError(f"No staged proposal '{pid}'.")
        n = json.loads(row[0])
        n["created"] = datetime.fromisoformat(n["created"])
        n["modified"] = datetime.fromisoformat(n["modified"])
        for p in n["provenance"]:
            p["captured_at"] = datetime.fromisoformat(p["captured_at"])
        violations = validate(self, n, stage="commit")
        if violations:
            raise ValueError("Commit blocked: " + "; ".join(f"{g}: {m}" for g, m in violations))
        rel = f"{path_for(n['class'])}/{normalize_title(n['title'])}.md"
        abs_path = self.root / rel
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(to_markdown(n))
        self.index_note(n, rel)
        self.db.execute("DELETE FROM staged WHERE id=?", (pid,))
        self.db.commit()
        return n["permalink"]

    def capture_episode(self, title, body, prov, relations=None):
        n = make_note(title, "Event", body, relations or [], [], [prov],
                      isolated_justification=None if relations else
                      "episodic capture; linked at consolidation")
        rel = f"episodes/{utcnow().strftime('%Y-%m-%d')}-{normalize_title(title)}.md"
        abs_path = self.root / rel
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        if abs_path.exists():
            raise ValueError("Episodes are append-only; identical title today already captured.")
        abs_path.write_text(to_markdown(n))
        self.index_note(n, rel)
        self.db.commit()
        return n["permalink"]

    def index_note(self, n, rel_path):
        self.db.execute("INSERT OR REPLACE INTO notes VALUES(?,?,?,?,?,?,?)",
                        (n["permalink"], n["title"], n["class"], n["status"],
                         n["confidence"], rel_path, n["modified"].isoformat()))
        self.db.execute("DELETE FROM edges WHERE src=?", (n["permalink"],))
        for r in n.get("relations", []):
            self.db.execute(
                "INSERT OR REPLACE INTO edges(src,verb,dst,since,mode,confidence,t_valid,t_created)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (n["permalink"], screaming_snake(r["verb"]), r["target"], r["since"],
                 r.get("mode"), r.get("confidence"), r["since"], utcnow().isoformat()))
        self.db.execute("DELETE FROM notes_fts WHERE permalink=?", (n["permalink"],))
        self.db.execute("INSERT INTO notes_fts(permalink,title,overview,observations) VALUES(?,?,?,?)",
                        (n["permalink"], n["title"], n.get("overview", ""),
                         "\n".join(o["text"] for o in n.get("observations", []))))
        self.db.execute("DELETE FROM note_tags WHERE permalink=?", (n["permalink"],))
        all_tags = [f"kb/{n['class'].lower()}", f"kb/status/{n['status'].lower()}"]
        all_tags += [t for t in n.get("tags", []) if t not in all_tags]
        for t in all_tags:
            self.db.execute("INSERT OR IGNORE INTO note_tags VALUES(?,?)", (n["permalink"], t))

    # read surface
    def search(self, query, limit=10):
        safe = " ".join('"{}"'.format(t.replace('"', '""'))
                        for t in query.split())
        if not safe:
            return []
        return self.db.execute(
            "SELECT permalink, title, bm25(notes_fts) FROM notes_fts WHERE notes_fts MATCH ?"
            " ORDER BY bm25(notes_fts) LIMIT ?", (safe, limit)).fetchall()

    def backlinks(self, permalink):
        rows = self.db.execute(
            "SELECT src, verb FROM edges WHERE dst=? AND t_invalid IS NULL", (permalink,)).fetchall()
        return [(src, verb, INVERSE[VERB_FROM_SNAKE[verb]]) for src, verb in rows]

    def read_markdown(self, permalink):
        r = self.db.execute("SELECT path FROM notes WHERE permalink=?", (permalink,)).fetchone()
        return (self.root / r[0]).read_text() if r else None

    def meta_get(self, key, default=None):
        r = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return r[0] if r else default


def make_note(title, cls, overview, relations, observations, provenance,
              confidence=1.0, tags=None, aliases=None, isolated_justification=None,
              status="active"):
    now = utcnow()
    return {
        "title": title, "class": cls, "permalink": permalink_for(cls, title),
        "overview": overview, "relations": relations, "observations": observations,
        "provenance": provenance, "tags": tags or [], "aliases": aliases or [],
        "status": status, "confidence": confidence,
        "isolated_justification": isolated_justification,
        "created": now, "modified": now,
    }


# ── Tool implementations ─────────────────────────────────────────────────────

def note_from_args(a):
    # Closed vocabularies are enforced by tool-schema enums for well-behaved
    # MCP clients — but the server must hold the line for ANY caller, so the
    # same enums are re-checked here (C1/C3/C6 tier-1 enforcement).
    if a["entityClass"] not in CLASSES:
        raise ValueError(f"[C1] Unknown entity class '{a['entityClass']}'. "
                         f"Closed set: {', '.join(CLASSES)}.")
    for r in a.get("relations", []):
        if r["verb"] not in VERBS:
            raise ValueError(f"[C3] Unknown relation verb '{r['verb']}'. "
                             f"Closed set: {', '.join(VERBS)}.")
    for o in a.get("observations", []):
        if o["kind"] not in OBS_KINDS:
            raise ValueError(f"[C6] Unknown observation kind '{o['kind']}'. "
                             f"Closed set: {', '.join(OBS_KINDS)}.")
    relations = [{"verb": r["verb"], "target": r["target"], "since": r["since"],
                  "mode": r.get("mode"), "confidence": None}
                 for r in a.get("relations", [])]
    observations = [{"kind": o["kind"], "text": o["text"],
                     "provenance_ref": o.get("provenance")}
                    for o in a.get("observations", [])]
    prov = [{"source": a["provenanceSource"], "author": a["provenanceAuthor"],
             "captured_at": utcnow(), "confidence": 1.0}]
    return make_note(a["title"], a["entityClass"], a["overview"], relations,
                     observations, prov, confidence=a.get("confidence", 1.0),
                     tags=a.get("tags") or [],
                     isolated_justification=a.get("isolatedJustification"))


def t_propose_note(store, a):
    n = note_from_args(a)
    pid, violations = store.propose(n)
    if pid:
        return f"STAGED {pid} → {n['permalink']}. Call commit_note to finalize."
    return "REJECTED:\n" + "\n".join(f"[{g}] {m}" for g, m in violations)


def t_commit_note(store, a):
    return "COMMITTED " + store.commit_note(a["proposalId"])


def t_capture_episode(store, a):
    prov = {"source": a["provenanceSource"], "author": a["provenanceAuthor"],
            "captured_at": utcnow(), "confidence": 1.0}
    return "CAPTURED " + store.capture_episode(a["title"], a["body"], prov)


def t_search_notes(store, a):
    hits = store.search(a["query"], a.get("limit", 10))
    if not hits:
        return "verdict: absent — no notes match. The knowledge likely does not exist yet."
    return "verdict: ok\n" + "\n".join(f"{rank:0.2f}  {p}  {t}" for p, t, rank in hits)


def t_read_note(store, a):
    md = store.read_markdown(a["permalink"])
    if md is None:
        return f"verdict: absent — no note '{a['permalink']}'."
    bl = store.backlinks(a["permalink"])
    if bl:
        md += "\n## Backlinks (computed)\n" + "\n".join(
            f"- {inv} ← [[{src}]] (stored as {verb})" for src, verb, inv in bl)
    return md


NAMESPACES = ("domain", "project", "status", "source", "machine")


def t_register_tag(store, a):
    tag = a["tag"]
    # the reserved-plane check must precede the namespace check, or `kb/x` gets
    # the generic "not in the closed namespace set" message and the agent never
    # learns that kb/* is written by the server
    if tag.startswith("kb/"):
        return "REJECTED: namespace 'kb/' is server-computed and reserved."
    ns = tag.split("/")[0] if "/" in tag else ""
    if ns not in NAMESPACES:
        return f"REJECTED: namespace '{ns}/' is not in the closed namespace set."
    for (existing,) in store.db.execute("SELECT tag FROM tags").fetchall():
        if existing != tag and title_similarity(existing, tag) > THETA_TITLE:
            return f"REJECTED: too similar to registered tag '{existing}'. Reuse it or pick a distinct name."
    store.register_tag(tag, a.get("description"))
    reg = store.root / "_meta/registries/tags.md"
    if reg.exists() and f"| {tag} " not in reg.read_text():
        with reg.open("a") as f:
            f.write(f"| {tag} | {a.get('description', '')} | {utcnow():%Y-%m-%d} |\n")
    return f"REGISTERED {tag}"


CORPUS_ROOTS = [Path(p).expanduser().resolve()
                for p in os.environ.get("TEAMKB_CORPUS_ROOTS", "").split(":") if p]


def t_submit_document(store, a):
    src = Path(a["path"]).expanduser().resolve()
    if not src.exists() or not in_scope(src.name):
        return f"REJECTED: '{src}' does not exist or is out of scope."
    if CORPUS_ROOTS and not any(str(src).startswith(str(r) + os.sep) for r in CORPUS_ROOTS):
        return f"REJECTED: '{src}' is outside the approved corpus roots."
    sha = hashlib.sha256(src.read_bytes()).hexdigest()
    dup = store.db.execute("SELECT id, status FROM submissions WHERE sha256=?", (sha,)).fetchone()
    if dup:
        return f"DUPLICATE: submission {dup[0]} (status {dup[1]}) already covers this content."
    sid = "sub-" + utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
    store.db.execute("INSERT INTO submissions VALUES(?,?,?,?,?,NULL)",
                     (sid, str(src), sha, "staged", utcnow().isoformat()))
    store.db.commit()
    return json.dumps({"submission_id": sid, "source_path": str(src), "status": "staged"})


def _space_guard(store):
    """Non-None message when semantic channel is disabled by model mismatch."""
    m = getattr(store, "embed_model_mismatch", None)
    return f"REJECTED: {m}" if m else None


def t_ingest_chunks(store, a):
    if (g := _space_guard(store)):
        return g
    sid = a["submissionId"]
    row = store.db.execute("SELECT source_path FROM submissions WHERE id=?", (sid,)).fetchone()
    if row is None:
        return f"REJECTED: no submission '{sid}'."
    text = Path(row[0]).read_text()
    t0 = time.perf_counter()
    chunks = chunk_markdown(text)
    store.db.execute("DELETE FROM chunks WHERE submission_id=?", (sid,))
    store.db.execute("DELETE FROM chunk_embeddings WHERE submission_id=?", (sid,))
    for c in chunks:
        store.db.execute("INSERT INTO chunks VALUES(?,?,?,?,?)",
                         (sid, c["id"], c["heading_path"], c["text"], json.dumps(c["span"])))
    sizes = [len(c["text"]) for c in chunks]
    emit("chunk.done", phase="CA-2.chunk", doc=sid,
         duration_ms=(time.perf_counter() - t0) * 1000,
         n_chunks=len(chunks), doc_chars=len(text),
         chunk_chars_min=min(sizes, default=0), chunk_chars_max=max(sizes, default=0),
         chunk_chars_mean=round(sum(sizes) / len(sizes), 1) if sizes else 0,
         cap=CHUNK_CHARS, overlap=OVERLAP_CHARS,
         headings=sorted({c["heading_path"] for c in chunks})[:20],
         source_path=row[0])
    try:
        vecs = embed_texts([c["text"] for c in chunks], DOC_PREFIX, doc=sid)
    except EmbedError as e:
        store.db.execute("UPDATE submissions SET status='failed' WHERE id=?", (sid,))
        store.db.commit()
        emit("submission.failed", phase="CA-3.embed", doc=sid, ok=False,
             error=str(e), n_chunks=len(chunks))
        return f"FAILED: {e} — submission marked failed; rerun after endpoint recovery."
    for c, v in zip(chunks, vecs):
        store.db.execute("INSERT INTO chunk_embeddings VALUES(?,?,?)", (sid, c["id"], pack(v)))
    dim = len(vecs[0])
    store.db.execute("INSERT OR IGNORE INTO meta VALUES('embed_dim',?)", (str(dim),))
    doc_vec = l2norm([sum(v[i] for v in vecs) / len(vecs) for i in range(dim)])
    store.db.execute("INSERT OR REPLACE INTO doc_embeddings VALUES(?,NULL,?)", (sid, pack(doc_vec)))
    store.db.execute("UPDATE submissions SET status='curating' WHERE id=?", (sid,))
    store.db.commit()
    return json.dumps({"submission_id": sid, "chunks": len(chunks), "dim": dim,
                       "headings": [c["heading_path"] for c in chunks[:12]]})


def t_link_submission(store, a):
    """Bind a committed permalink to a submission (called by curator after commit_note)."""
    sid, permalink = a["submissionId"], a["permalink"]
    if not store.permalink_exists(permalink):
        return f"REJECTED: permalink '{permalink}' not committed."
    store.db.execute("UPDATE submissions SET status='committed', permalink=? WHERE id=?",
                     (permalink, sid))
    store.db.execute("UPDATE doc_embeddings SET permalink=? WHERE submission_id=?",
                     (permalink, sid))
    store.db.commit()
    return f"LINKED {sid} → {permalink}"


def t_semantic_search(store, a):
    if (g := _space_guard(store)):
        return g
    theta = float(store.meta_get("semantic_theta", "0.45"))
    phase = "CA-4.neighbors" if a.get("target") else "GA-3.retrieve.semantic"
    if a.get("query"):
        qv = embed_texts([a["query"]], QUERY_PREFIX, doc=a.get("target"),
                         phase=phase + ".embed_query")[0]
    elif a.get("target"):
        row = store.db.execute(
            "SELECT vector FROM doc_embeddings WHERE permalink=? OR submission_id=?",
            (a["target"], a["target"])).fetchone()
        if row is None:
            return f"verdict: absent — no embedding for '{a['target']}'."
        qv = unpack(row[0])
    else:
        return "REJECTED: provide query or target."
    rows = store.db.execute(
        "SELECT submission_id, permalink, vector FROM doc_embeddings").fetchall()
    scored = []
    for sid, permalink, blob in rows:
        ident = permalink or sid
        if ident == a.get("target"):
            continue
        if permalink and permalink.startswith("inbox/"):
            continue
        scored.append((ident, dot(qv, unpack(blob))))
    scored.sort(key=lambda x: -x[1])
    scored = scored[: a.get("limit", 10)]
    top = scored[0][1] if scored else 0.0
    hits = [(i, s) for i, s in scored if s >= theta]
    if not hits:
        return (f"verdict: absent — no semantic neighbors above θ={theta} "
                f"(top score {top:.3f}). The knowledge likely does not exist yet.")
    return "verdict: ok\n" + "\n".join(f"{s:.3f}  {i}" for i, s in hits)


def t_suggest_tags(store, a):
    if (g := _space_guard(store)):
        return g
    rows = store.db.execute(
        "SELECT tag, description FROM tags WHERE tag NOT LIKE 'kb/%'").fetchall()
    if not rows:
        return "verdict: absent — tag registry is empty."
    missing = [(t, d) for t, d in rows
               if store.db.execute("SELECT 1 FROM tag_embeddings WHERE tag=?", (t,)).fetchone() is None]
    if missing:
        vecs = embed_texts([f"{t}: {d or t}" for t, d in missing], DOC_PREFIX,
                           phase="CA-5.tag_similarity.embed_registry")
        for (t, _), v in zip(missing, vecs):
            store.db.execute("INSERT OR REPLACE INTO tag_embeddings VALUES(?,?)", (t, pack(v)))
        store.db.commit()
    qv = embed_texts([a["text"]], QUERY_PREFIX, phase="CA-5.tag_similarity.embed_query")[0]
    scored = [(t, dot(qv, unpack(b))) for t, b in
              store.db.execute("SELECT tag, vector FROM tag_embeddings").fetchall()]
    scored.sort(key=lambda x: -x[1])
    return "\n".join(f"{s:.3f}  {t}" for t, s in scored[: a.get("limit", 8)])


def t_search_by_tag(store, a):
    tag = a["tag"]
    if a.get("prefix"):
        rows = store.db.execute(
            "SELECT nt.permalink, n.title FROM note_tags nt JOIN notes n USING(permalink)"
            " WHERE nt.tag LIKE ? || '%'", (tag,)).fetchall()
    else:
        rows = store.db.execute(
            "SELECT nt.permalink, n.title FROM note_tags nt JOIN notes n USING(permalink)"
            " WHERE nt.tag = ?", (tag,)).fetchall()
    if not rows:
        return f"verdict: absent — no notes tagged '{tag}'."
    return "verdict: ok\n" + "\n".join(f"{p}  {t}" for p, t in sorted(set(rows)))


def t_add_relations(store, a):
    src = a["permalink"]
    cls = store.class_of(src)
    if cls is None:
        return f"REJECTED: no note '{src}'."
    violations = []
    for r in a["relations"]:
        dom, rng = SIGNATURE.get(r["verb"], (None, None))
        if dom is not None and cls not in dom:
            violations.append(f"[C3] {r['verb']} not valid from class {cls} (dom: {'|'.join(dom)}).")
        if not store.permalink_exists(r["target"]):
            violations.append(f"[C4] Relation target '{r['target']}' does not exist. Create it first or request an auto-stub.")
        if rng is not None:
            tc = store.class_of(r["target"])
            if tc is not None and tc not in rng:
                violations.append(f"[C3] {r['verb']} target '{r['target']}' has class {tc} (rng: {'|'.join(rng)}).")
    if violations:
        return "REJECTED:\n" + "\n".join(violations)
    path_row = store.db.execute("SELECT path FROM notes WHERE permalink=?", (src,)).fetchone()
    fp = store.root / path_row[0]
    content = fp.read_text()
    lines = ["- {} :: [[{}]] {{since: {}}}".format(screaming_snake(r["verb"]), r["target"], r["since"])
             for r in a["relations"]]
    if "## Relations" in content:
        idx = content.index("## Relations") + len("## Relations")
        content = content[:idx] + "\n" + "\n".join(lines) + content[idx:]
    else:
        block = "\n## Relations\n" + "\n".join(lines) + "\n"
        if "## Observations" in content:
            oidx = content.index("## Observations")
            content = content[:oidx] + block.lstrip("\n") + "\n" + content[oidx:]
        else:
            content = content.rstrip("\n") + "\n" + block
    fp.write_text(content)
    for r in a["relations"]:
        store.db.execute(
            "INSERT OR REPLACE INTO edges(src,verb,dst,since,mode,confidence,t_valid,t_created)"
            " VALUES(?,?,?,?,NULL,NULL,?,?)",
            (src, screaming_snake(r["verb"]), r["target"], r["since"], r["since"],
             utcnow().isoformat()))
    store.db.commit()
    return "ADDED {} relation(s) to {}".format(len(a["relations"]), src)


def t_log_event(store, a):
    """Agent-side runbook steps that aren't tool calls (CA-1 strategy, CA-6
    metadata rationale, CA-11 report, GA scoring) land in the same event log."""
    metrics = a.get("metrics") or {}
    if isinstance(metrics, str):
        try:
            metrics = json.loads(metrics)
        except json.JSONDecodeError:
            metrics = {"note": metrics}
    emit(a.get("kind", "agent.step"), phase=a["phase"], doc=a.get("doc"),
         ok=a.get("ok", True), summary=a.get("summary"), **metrics)
    return f"LOGGED {a['phase']}" + (f" ({a['doc']})" if a.get("doc") else "")


def t_reindex(store, a):
    rebuilt = None
    if a.get("rebuild"):
        rebuilt = rebuild_index(store)
    missing = []
    for permalink, path in store.db.execute("SELECT permalink, path FROM notes").fetchall():
        if not (store.root / path).exists():
            missing.append(permalink)
    pending = store.db.execute(
        "SELECT s.id FROM submissions s LEFT JOIN doc_embeddings d ON d.submission_id=s.id"
        " WHERE d.submission_id IS NULL AND s.status IN ('staged','curating')").fetchall()
    counts = {
        "vault": str(store.root),
        "notes": store.db.execute("SELECT COUNT(*) FROM notes").fetchone()[0],
        "edges": store.db.execute("SELECT COUNT(*) FROM edges").fetchone()[0],
        "chunks": store.db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
        "doc_embeddings": store.db.execute("SELECT COUNT(*) FROM doc_embeddings").fetchone()[0],
        "tags": store.db.execute("SELECT COUNT(*) FROM tags").fetchone()[0],
        "missing_files": missing,
        "embed_pending": [r[0] for r in pending],
    }
    if rebuilt is not None:
        counts["rebuilt"] = rebuilt
    return json.dumps(counts)


def rebuild_index(store):
    """Re-derive notes/edges/tags/FTS from the vault's markdown alone, then
    re-embed doc-level vectors from note text so the semantic channel also
    survives a markdown-only clone. Chunk embeddings stay source-corpus-derived
    (re-created on re-ingestion); doc-level recall is what a clone needs.
    Embedding failures degrade gracefully: the structural rebuild always
    completes and unembedded notes are reported as embed_pending.
    """
    t0 = time.perf_counter()
    parsed, failures = [], []
    for path in sorted(store.root.rglob("*.md")):
        rel = path.relative_to(store.root).as_posix()
        if rel.startswith("_meta/") or not in_scope(path.name):
            continue
        try:
            n = parse_markdown(path.read_text())
        except (ValueError, KeyError) as e:
            failures.append({"path": rel, "error": f"{type(e).__name__}: {e}"})
            continue
        parsed.append((n, rel))

    for table in ("notes", "edges", "note_tags"):
        store.db.execute(f"DELETE FROM {table}")
    store.db.execute("DELETE FROM notes_fts")
    for n, rel in parsed:
        store.index_note(n, rel)
    store.db.commit()

    # Semantic channel: doc vectors from note text (title + overview +
    # observations). episodes/ and inbox/ are retrieval-excluded tiers.
    to_embed = [(n, p) for n, p in [(n, rel[:-3]) for n, rel in parsed]
                if not p.startswith(("episodes/", "inbox/"))
                and store.db.execute(
                    "SELECT 1 FROM doc_embeddings WHERE permalink=?", (p,)
                ).fetchone() is None]
    embedded, embed_pending = 0, []
    if to_embed:
        texts = [" ".join(filter(None, [n["title"], n.get("overview", "")]
                                 + [o["text"] for o in n.get("observations", [])]))
                 for n, _ in to_embed]
        try:
            vecs = embed_texts(texts, DOC_PREFIX, phase="CA-9.reindex.re_embed")
            for (_, p), v in zip(to_embed, vecs):
                store.db.execute(
                    "INSERT OR REPLACE INTO doc_embeddings VALUES(?,?,?)",
                    (f"rebuild:{p}", p, pack(v)))
            store.db.execute("INSERT OR IGNORE INTO meta VALUES('embed_dim',?)",
                             (str(len(vecs[0])),))
            store.db.commit()
            embedded = len(vecs)
        except EmbedError as e:
            embed_pending = [p for _, p in to_embed]
            log.warning("rebuild re-embed skipped: %s", e)

    report = {"files_parsed": len(parsed), "parse_failures": failures,
              "re_embedded": embedded, "embed_pending": embed_pending,
              "duration_ms": round((time.perf_counter() - t0) * 1000, 2)}
    emit("index.rebuild", phase="CA-9.reindex", ok=not failures,
         duration_ms=report["duration_ms"], files_parsed=len(parsed),
         n_failures=len(failures), re_embedded=embedded,
         n_embed_pending=len(embed_pending))
    return report


# ── Tool registry + JSON-RPC loop ────────────────────────────────────────────

def S(**props):
    required = [k for k, v in props.items() if not v.pop("_opt", False)]
    return {"type": "object", "properties": props, "required": required}


RELATION_SCHEMA = {"type": "array", "items": {"type": "object", "properties": {
    "verb": {"type": "string", "enum": VERBS},
    "target": {"type": "string", "description": "Target note permalink"},
    "since": {"type": "string", "description": "YYYY-MM-DD"},
    "mode": {"type": "string"}}, "required": ["verb", "target", "since"]}}
OBSERVATION_SCHEMA = {"type": "array", "items": {"type": "object", "properties": {
    "kind": {"type": "string", "enum": OBS_KINDS},
    "text": {"type": "string"},
    "provenance": {"type": "string"}}, "required": ["kind", "text"]}}

TOOLS = {
    "propose_note": {
        "fn": t_propose_note,
        "description": ("Stage a new knowledge note (write ≠ commit). Runs all constitution gates; "
                        "returns either a proposal id or the list of violations. Folder path is "
                        "computed from entity_class — never supplied."),
        "schema": S(title={"type": "string"},
                    entityClass={"type": "string", "enum": CLASSES},
                    overview={"type": "string"},
                    relations=RELATION_SCHEMA,
                    observations=OBSERVATION_SCHEMA,
                    provenanceSource={"type": "string"},
                    provenanceAuthor={"type": "string"},
                    confidence={"type": "number", "_opt": True},
                    tags={"type": "array", "items": {"type": "string"}, "_opt": True},
                    isolatedJustification={"type": "string", "_opt": True})},
    "commit_note": {
        "fn": t_commit_note,
        "description": ("Commit a staged proposal: re-validates gates, writes canonical markdown, "
                        "indexes FTS + edges (computed backlinks). Returns the committed permalink."),
        "schema": S(proposalId={"type": "string"})},
    "capture_episode": {
        "fn": t_capture_episode,
        "description": ("Append an immutable episodic record (session log, incident, event). "
                        "Bypasses staging — episodes are append-only and linked later by consolidation."),
        "schema": S(title={"type": "string"}, body={"type": "string"},
                    provenanceSource={"type": "string"}, provenanceAuthor={"type": "string"})},
    "search_notes": {
        "fn": t_search_notes,
        "description": ("FTS5/BM25 search over titles, overviews, observations. Returns a verdict: "
                        "ok | absent. absent means the knowledge does not exist — report the gap, "
                        "do not re-search with synonyms."),
        "schema": S(query={"type": "string"}, limit={"type": "integer", "_opt": True})},
    "read_note": {
        "fn": t_read_note,
        "description": ("Read a note's canonical markdown plus its computed backlinks "
                        "(who points here, with inverse verb names)."),
        "schema": S(permalink={"type": "string"})},
    "register_tag": {
        "fn": t_register_tag,
        "description": ("Register a namespaced tag (domain/…, project/…, status/…, source/…, machine/…) "
                        "so notes may use it. Registry-before-choice: unregistered tags are rejected "
                        "by propose_note. kb/* is reserved. Near-duplicates of registered tags rejected."),
        "schema": S(tag={"type": "string"}, description={"type": "string", "_opt": True})},
    "submit_document": {
        "fn": t_submit_document,
        "description": ("Submit a source markdown document for curation. Returns a submission id. "
                        "Content-hash deduped; path must be inside the approved corpus roots."),
        "schema": S(path={"type": "string"})},
    "ingest_chunks": {
        "fn": t_ingest_chunks,
        "description": ("Deterministically chunk (heading-aware, ~512-token cap, overlap within "
                        "sections) and embed a submission via the hosted endpoint. Persists chunk "
                        "and mean-pooled doc vectors. On endpoint failure marks submission failed."),
        "schema": S(submissionId={"type": "string"})},
    "link_submission": {
        "fn": t_link_submission,
        "description": "Bind a committed note permalink to its submission (curator calls after commit_note).",
        "schema": S(submissionId={"type": "string"}, permalink={"type": "string"})},
    "semantic_search": {
        "fn": t_semantic_search,
        "description": ("Cosine similarity over document embeddings. Provide query (text) OR target "
                        "(permalink/submission id) for neighbor search. Honest verdict: absent when "
                        "top score < θ (calibrated, stored in db meta). Excludes inbox tier."),
        "schema": S(query={"type": "string", "_opt": True},
                    target={"type": "string", "_opt": True},
                    limit={"type": "integer", "_opt": True})},
    "suggest_tags": {
        "fn": t_suggest_tags,
        "description": ("Rank registered tags by embedding similarity to the given text. "
                        "Suggestions only — registration still goes through register_tag."),
        "schema": S(text={"type": "string"}, limit={"type": "integer", "_opt": True})},
    "search_by_tag": {
        "fn": t_search_by_tag,
        "description": "Find notes by exact namespaced tag, or by tag prefix (e.g. kb/concept).",
        "schema": S(tag={"type": "string"}, prefix={"type": "boolean", "_opt": True})},
    "add_relations": {
        "fn": t_add_relations,
        "description": ("Gated (C3/C4) append-only relation addition to an existing note — markdown "
                        "and edge index both updated. Use for the post-corpus relation back-pass."),
        "schema": S(permalink={"type": "string"}, relations=RELATION_SCHEMA)},
    "log_event": {
        "fn": t_log_event,
        "description": ("Record a runbook phase event (metrics + outcome) to the run's "
                        "event log. Use for steps that are agent judgment rather than tool "
                        "calls: CA-1 strategy selection, CA-6 metadata rationale, CA-11 "
                        "report, GA retrieval scoring. phase is the runbook step id."),
        "schema": S(phase={"type": "string", "description": "Runbook step id, e.g. CA-1.strategy"},
                    doc={"type": "string", "_opt": True,
                         "description": "submission id or permalink this step belongs to"},
                    summary={"type": "string", "_opt": True},
                    kind={"type": "string", "_opt": True,
                          "description": "event kind, default agent.step"},
                    ok={"type": "boolean", "_opt": True},
                    metrics={"type": "object", "_opt": True,
                             "description": "arbitrary numeric/string metrics for this phase"})},
    "reindex": {
        "fn": t_reindex,
        "description": ("Index consistency report: note-file existence check, counts (notes/edges/"
                        "chunks/embeddings/tags), pending embeddings, vault path. With "
                        "rebuild=true, re-derives notes, edges, tags and FTS from the vault's "
                        "markdown alone — use after cloning a vault or if the index is lost "
                        "(markdown is canonical; embeddings are preserved)."),
        "schema": S(rebuild={"type": "boolean", "_opt": True})},
}


def tool_list():
    return [{"name": name, "description": t["description"], "inputSchema": t["schema"]}
            for name, t in TOOLS.items()]


# ── Event correlation + metric extraction ───────────────────────────────────

PHASE_OF_TOOL = {
    "submit_document": "GA-1.submit",
    "ingest_chunks": "CA-2/3.chunk_embed",
    "suggest_tags": "CA-5.tag_similarity",
    "propose_note": "CA-7.propose",
    "commit_note": "CA-7.commit",
    "link_submission": "CA-7.link",
    "register_tag": "CA-5.register_tag",
    "read_note": "CA-8.verify|GA-3.retrieve.graph",
    "reindex": "CA-9.reindex",
    "capture_episode": "CA-10.dcf|episode",
    "search_notes": "GA-3.retrieve.fts",
    "search_by_tag": "GA-3.retrieve.tag",
    "add_relations": "CA-7.backpass",
    "log_event": "agent",
}


def phase_for(tool, args):
    if tool == "semantic_search":
        return "CA-4.neighbors" if args.get("target") else "GA-3.retrieve.semantic"
    return PHASE_OF_TOOL.get(tool, "other")


# Tools with no document argument that nonetheless belong to the document
# currently in the pipeline (CA-5 tag similarity, CA-10 DCF capture). The
# pipeline is strictly sequential per document, so a single context slot is
# sufficient; retrieval calls clear it so corpus-level work is never
# misattributed to the last ingested document.
_ctx = {"doc": None}
CTX_TOOLS = {"suggest_tags", "capture_episode"}
CTX_CLEARING_TOOLS = {"search_notes", "search_by_tag", "reindex"}


def doc_for(store, tool, args, text):
    """Correlate every event to one document: submission id, permalink, or path."""
    if tool in CTX_CLEARING_TOOLS or (tool == "semantic_search" and args.get("query")):
        _ctx["doc"] = None
    if tool in CTX_TOOLS:
        return _ctx["doc"]
    for key in ("submissionId", "permalink", "target"):
        if args.get(key):
            return args[key]
    if tool == "submit_document" and text.startswith("{"):
        try:
            return json.loads(text)["submission_id"]
        except (json.JSONDecodeError, KeyError):
            pass
    if args.get("path"):
        return Path(args["path"]).name
    if tool == "commit_note" and text.startswith("COMMITTED "):
        return text.split()[-1]
    if tool == "propose_note" and " → " in text:
        return text.split(" → ")[1].split(".")[0]
    return None


def set_ctx(tool, args, doc):
    """Remember which document the pipeline is currently working on."""
    if tool in ("submit_document", "ingest_chunks") and doc:
        _ctx["doc"] = args.get("submissionId") or doc


def metrics_for(tool, text):
    """Pull structured numbers out of the tool's text return."""
    m = {}
    if text.startswith("verdict: "):
        m["verdict"] = "ok" if text.startswith("verdict: ok") else "absent"
        lines = [l for l in text.splitlines()[1:] if l.strip()]
        if tool in ("search_notes", "semantic_search", "search_by_tag"):
            m["n_hits"] = len(lines) if m["verdict"] == "ok" else 0
            scores = []
            for l in lines:
                try:
                    scores.append(float(l.split()[0]))
                except (ValueError, IndexError):
                    pass
            if scores:
                m["top_score"] = scores[0]
                m["scores"] = scores[:10]
            m["hits"] = [l.split()[1] for l in lines[:10] if len(l.split()) > 1]
        if m["verdict"] == "absent" and "top score" in text:
            try:
                m["top_score"] = float(text.split("top score ")[1].split(")")[0])
            except (ValueError, IndexError):
                pass
    elif text.startswith("REJECTED"):
        m["accepted"] = False
        m["violations"] = [l.split("]")[0].lstrip("[") for l in text.splitlines()
                           if l.startswith("[")]
        m["n_violations"] = len(m["violations"])
    elif text.startswith("STAGED"):
        m["accepted"] = True
        m["proposal_id"] = text.split()[1]
    elif text.startswith(("COMMITTED", "CAPTURED")):
        m["permalink"] = text.split()[-1]
    elif text.startswith("{"):
        try:
            m.update({k: v for k, v in json.loads(text).items()
                      if isinstance(v, (int, float, str, list))})
        except json.JSONDecodeError:
            pass
    elif "## Backlinks (computed)" in text:
        m["n_backlinks"] = sum(1 for l in text.splitlines()
                               if l.startswith("- ") and "←" in l)
        m["verdict"] = "ok"
    elif text.startswith("DUPLICATE"):
        m["duplicate"] = True
    elif text.startswith("ADDED"):
        try:
            m["n_relations_added"] = int(text.split()[1])
        except (ValueError, IndexError):
            pass
    return m


def handle(store, req, trace_fp):
    method = req.get("method")
    rid = req.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "teamkb", "version": KB_VERSION}}}
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": tool_list()}}
    if method == "tools/call":
        name = req["params"]["name"]
        args = req["params"].get("arguments", {})
        if name not in TOOLS:
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32602, "message": f"Unknown tool '{name}'"}}
        phase = phase_for(name, args)
        emit("tool.start", phase=phase, doc=doc_for(store, name, args, ""), tool=name,
             arguments=args)
        t0 = time.perf_counter()
        try:
            text = TOOLS[name]["fn"](store, args)
            result = {"content": [{"type": "text", "text": text}], "isError": False}
        except Exception as e:  # tool errors surface as isError content, not protocol errors
            log.exception("tool %s failed", name)
            text = f"ERROR: {e}"
            result = {"content": [{"type": "text", "text": text}], "isError": True}
        end_doc = doc_for(store, name, args, text)
        set_ctx(name, args, end_doc)
        emit("tool.end", phase=phase, doc=end_doc, tool=name,
             duration_ms=(time.perf_counter() - t0) * 1000,
             ok=not result["isError"] and not text.startswith(("REJECTED", "FAILED")),
             **metrics_for(name, text),
             **({"error": text} if result["isError"] else {}))
        if trace_fp:
            trace_fp.write(json.dumps({"ts": utcnow().isoformat(), "tool": name,
                                       "arguments": args, "result": result}) + "\n")
            trace_fp.flush()
        return {"jsonrpc": "2.0", "id": rid, "result": result}
    if rid is None:
        return None  # unknown notification — ignore
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": f"Method not found: {method}"}}


def main():
    vault = os.environ.get("TEAMKB_VAULT")
    if not vault:
        log.error("TEAMKB_VAULT is required (no fallback).")
        sys.exit(1)
    store = Store(vault)
    global RUN_ID
    if not RUN_ID:
        RUN_ID = utcnow().strftime("run-%Y%m%d-%H%M%S")
    events_path = Path(os.environ.get("TEAMKB_EVENTS")
                       or store.root / ".teamkb-events.jsonl")
    events_path.parent.mkdir(parents=True, exist_ok=True)
    # T6 rotation: unbounded append on a long-lived vault; over the cap the old
    # log is archived next to itself and a fresh one starts. No daemon.
    max_mb = float(os.environ.get("TEAMKB_EVENTS_MAX_MB", "64"))
    if events_path.exists() and events_path.stat().st_size > max_mb * 1024 * 1024:
        rotated = events_path.with_name(
            events_path.stem + utcnow().strftime(".%Y%m%d-%H%M%S") + ".jsonl")
        events_path.rename(rotated)
        log.info("event log over %.0f MB — rotated to %s", max_mb, rotated.name)
    _events["fp"] = events_path.open("a")
    log.info("vault=%s embed=%s/%s", store.root, EMBED_URL, EMBED_MODEL)
    log.info("events → %s (run_id=%s)", events_path, RUN_ID)
    emit("run.start", phase="run", vault=str(store.root), embed_url=EMBED_URL,
         embed_model=EMBED_MODEL, pid=os.getpid(),
         semantic_theta=store.meta_get("semantic_theta"))
    trace_fp = None
    if os.environ.get("TEAMKB_TRACE") == "1":
        trace_fp = (store.root / ".teamkb-trace.jsonl").open("a")
        log.info("trace → %s", trace_fp.name)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(store, req, trace_fp)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
    emit("run.end", phase="run", events=_events["seq"])
    log.info("stdin EOF — exiting")


if __name__ == "__main__":
    main()
