#!/usr/bin/env python3
"""One-shot MCP client for the teamkb server: spawns the server over stdio,
performs the initialize handshake, executes one tools/call, prints the text
result. State persists in the vault's SQLite DB, so per-call spawning is safe.

Usage: kbcall.py -t <tool> [-a '<json-args>'] [-v <vault>]
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def rpc(proc, msg):
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()


def read_response(proc, want_id):
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("server closed stdout")
        resp = json.loads(line)
        if resp.get("id") == want_id:
            return resp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--tool", required=True)
    ap.add_argument("-a", "--args", default="{}", help="JSON arguments")
    ap.add_argument("-v", "--vault", default=os.environ.get("TEAMKB_VAULT"))
    ns = ap.parse_args()
    if not ns.vault:
        sys.exit("kbcall: vault required (-v or TEAMKB_VAULT)")

    server = Path(__file__).resolve().parents[1] / "mcp/teamkb_server.py"
    env = {**os.environ, "TEAMKB_VAULT": str(Path(ns.vault).expanduser())}
    proc = subprocess.Popen([sys.executable, str(server)], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            text=True, env=env)
    try:
        rpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                   "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                              "clientInfo": {"name": "kbcall", "version": "1.0"}}})
        read_response(proc, 1)
        rpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                   "params": {"name": ns.tool, "arguments": json.loads(ns.args)}})
        resp = read_response(proc, 2)
    finally:
        proc.stdin.close()
        proc.wait(timeout=10)
    if "error" in resp:
        print("PROTOCOL ERROR:", resp["error"]["message"])
        sys.exit(2)
    result = resp["result"]
    print(result["content"][0]["text"])
    sys.exit(1 if result.get("isError") else 0)


if __name__ == "__main__":
    main()
