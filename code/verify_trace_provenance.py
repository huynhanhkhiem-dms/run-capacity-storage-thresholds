"""Verify local editing-traces files against the pinned Git blob IDs.

Git's blob object ID is SHA1(b"blob <size>\\0" + file_bytes).  This check
therefore verifies byte identity without requiring a Git checkout.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "TRACE_PROVENANCE.json"

def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    hdr = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(hdr + data).hexdigest()

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace-dir", type=Path, required=True)
    ap.add_argument("--write-sha256", type=Path, help="optional JSON output with SHA-256 values")
    args = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    out = {}
    for name, expected in manifest["files"].items():
        path = args.trace_dir / name
        if not path.is_file():
            raise SystemExit(f"MISSING: {path}")
        got = git_blob_sha1(path)
        if got != expected:
            raise SystemExit(f"BLOB MISMATCH: {name}: expected {expected}, got {got}")
        out[name] = {"git_blob_sha1": got, "sha256": sha256(path), "bytes": path.stat().st_size}
        print(f"{name}: {got} PASS")
    if args.write_sha256:
        args.write_sha256.parent.mkdir(parents=True, exist_ok=True)
        args.write_sha256.write_text(json.dumps(out, indent=2) + "\n")
    print(f"PASS: {len(out)} trace files match the pinned Git snapshot.")

if __name__ == "__main__":
    main()
