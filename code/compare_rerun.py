"""Compare a fresh real-trace rerun with the archived submission outputs.

Only deterministic scientific metrics are compared; wall-clock timings are
intentionally excluded because they are machine dependent.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "results" / "real_traces"
RERUN = ROOT / "results" / "rerun"
TRACES = [
    "friendsforever_flat", "clownschool_flat", "sveltecomponent",
    "json-crdt-blog-post", "json-crdt-patch", "seph-blog1", "rustcode",
    "automerge-paper",
]
SCHEMES = ["FI-62", "Farey-SRI"]
FIELDS = [
    "n_txns", "n_ins", "n_del", "n_live", "final_chars",
    "gen_max_bits", "gen_p50_bits", "gen_p95_bits", "gen_p99_bits",
    "live_max_bits", "live_bytes", "total_gen_bytes",
]

def summary(path: Path):
    x = json.loads(path.read_text())
    return x.get("summary", x)

def main() -> None:
    checked = 0
    for trace in TRACES:
        for scheme in SCHEMES:
            a = ARCH / f"{trace}__{scheme}.json"
            b = RERUN / f"{trace}__{scheme}.json"
            if not b.is_file():
                raise SystemExit(f"MISSING rerun output: {b}")
            sa, sb = summary(a), summary(b)
            for field in FIELDS:
                if sa[field] != sb[field]:
                    raise SystemExit(
                        f"MISMATCH {trace} {scheme} {field}: archived={sa[field]!r}, rerun={sb[field]!r}"
                    )
            checked += 1
            print(f"{trace} {scheme}: deterministic metrics PASS")
    print(f"PASS: {checked} real-trace scheme outputs match archived deterministic metrics.")

if __name__ == "__main__":
    main()
