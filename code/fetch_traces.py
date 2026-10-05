#!/usr/bin/env python3
"""Fetch the eight pinned public editing traces and verify their Git blob IDs."""
from __future__ import annotations
import argparse, hashlib, json, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "TRACE_PROVENANCE.json"

def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=ROOT / "external_traces")
    args = ap.parse_args()
    meta = json.loads(MANIFEST.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    base = f"https://raw.githubusercontent.com/{meta['repository']}/{meta['commit']}/{meta['subdirectory']}"
    for name, expected in meta["files"].items():
        url = f"{base}/{name}"
        out = args.output / name
        print(f"fetch {name}")
        with urllib.request.urlopen(url, timeout=120) as r:
            data = r.read()
        actual = git_blob_sha1(data)
        if actual != expected:
            raise SystemExit(f"Git blob SHA mismatch for {name}: {actual} != {expected}")
        out.write_bytes(data)
        print(f"  PASS {actual}")
    print(f"All {len(meta['files'])} traces fetched and verified in {args.output}")

if __name__ == "__main__":
    main()
