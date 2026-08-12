#!/usr/bin/env python3
"""Bootstrap a team-kb Obsidian vault: tier tree, .obsidian config (merge, never
clobber), tag registry seed, Bases dashboard, property types.

Idempotent. Parameterized on the target vault root.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

TIER_DIRS = [
    "inbox", "episodes", "playbooks", "procedures", "hubs",
    "knowledge/person", "knowledge/org", "knowledge/project", "knowledge/codebase",
    "knowledge/technology", "knowledge/artifact", "knowledge/concept",
    "knowledge/decision", "knowledge/agent",
    "_meta/bases", "_meta/registries",
]

# Merged key-by-key into existing files; existing user values win.
OBSIDIAN_DEFAULTS = {
    "app.json": {
        "alwaysUpdateLinks": True,
        "newLinkFormat": "relative",
        "useMarkdownLinks": False,
        "attachmentFolderPath": "_meta/attachments",
        "showUnsupportedFiles": False,
    },
    "appearance.json": {"baseTheme": "obsidian"},
    "core-plugins.json": {
        "file-explorer": True, "global-search": True, "graph": True,
        "backlink": True, "outgoing-link": True, "tag-pane": True,
        "page-preview": True, "properties": True, "bases": True,
        "command-palette": True, "file-recovery": True,
    },
    "graph.json": {
        "colorGroups": [
            {"query": "path:episodes", "color": {"a": 1, "rgb": 14701138}},
            {"query": "path:knowledge", "color": {"a": 1, "rgb": 5431378}},
            {"query": "path:hubs", "color": {"a": 1, "rgb": 16748574}},
            {"query": "path:playbooks", "color": {"a": 1, "rgb": 11621088}},
            {"query": "path:procedures", "color": {"a": 1, "rgb": 5419488}},
            {"query": "path:inbox", "color": {"a": 1, "rgb": 9079434}},
        ],
        "showTags": True,
    },
    "types.json": {
        "types": {
            "created": "datetime",
            "modified": "datetime",
            "confidence": "number",
            "kb_version": "text",
            "entity_class": "text",
            "permalink": "text",
            "status": "text",
        }
    },
}

# Seed registry mirrors VaultStore.SeedTags — the TAG gate reads the DB; this file is
# the human-readable registry the gate message points at.
TAGS_REGISTRY = """# Tag Registry

Closed namespaces: `domain/` `project/` `status/` `source/` `machine/`.
Registry-before-choice: a tag must have a row here (and be registered via
`register_tag`) before any note may use it. The `kb/*` plane is server-computed
and reserved — never register or hand-write `kb/*` tags.

| tag | description | registered |
|-----|-------------|------------|
| status/anchor | protected anchor note; automated edits forbidden | seed |
| status/verified | content verified against its provenance | seed |
| status/draft | unverified draft | seed |
| source/session | captured from an agent session | seed |
| source/web | captured from a web source | seed |
| source/paper | captured from a paper | seed |
| source/code | captured from source code | seed |
"""


def merge_json(path: Path, default):
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            existing = None
        if isinstance(existing, dict) and isinstance(default, dict):
            merged = {**default, **existing}  # existing wins
            path.write_text(json.dumps(merged, indent=2) + "\n")
            return "merged"
        if isinstance(existing, list) and isinstance(default, list):
            merged = existing + [x for x in default if x not in existing]
            path.write_text(json.dumps(merged, indent=2) + "\n")
            return "merged"
        return "kept"  # unknown shape: never clobber
    path.write_text(json.dumps(default, indent=2) + "\n")
    return "created"


def main():
    ap = argparse.ArgumentParser(description="Bootstrap a team-kb Obsidian vault.")
    ap.add_argument("-v", "--vault", required=True, help="Vault root directory")
    ap.add_argument("-b", "--base-src", default=None,
                    help="Path to kb.base to install (default: repo vault/_meta/bases/kb.base if present)")
    args = ap.parse_args()

    root = Path(args.vault).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    report = []

    for d in TIER_DIRS:
        p = root / d
        p.mkdir(parents=True, exist_ok=True)
        keep = p / ".gitkeep"
        if not any(p.iterdir()):
            keep.touch()
        report.append(f"dir  {d}")

    obs = root / ".obsidian"
    obs.mkdir(exist_ok=True)
    for name, default in OBSIDIAN_DEFAULTS.items():
        action = merge_json(obs / name, default)
        report.append(f"{action:7s} .obsidian/{name}")

    reg = root / "_meta/registries/tags.md"
    if not reg.exists():
        reg.write_text(TAGS_REGISTRY)
        report.append("created _meta/registries/tags.md")
    else:
        report.append("kept    _meta/registries/tags.md")

    base_dst = root / "_meta/bases/kb.base"
    if not base_dst.exists():
        src = Path(args.base_src) if args.base_src else \
            Path(__file__).resolve().parents[2] / "vault/_meta/bases/kb.base"
        if src.exists() and src.resolve() != base_dst.resolve():
            shutil.copy(src, base_dst)
            report.append("created _meta/bases/kb.base")
        else:
            report.append("MISSING kb.base source — pass --base-src")
    else:
        report.append("kept    _meta/bases/kb.base")

    print(f"Bootstrapped vault: {root}")
    for line in report:
        print("  " + line)


if __name__ == "__main__":
    sys.exit(main())
