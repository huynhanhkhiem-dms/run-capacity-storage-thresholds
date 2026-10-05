"""Submission reproduction entry point.

Default mode runs every self-contained deterministic check and regenerates
synthetic tables/figures.  Supplying --trace-dir additionally verifies the
byte identity of the public editing-traces inputs, replays all eight traces,
and compares deterministic rerun metrics with the archived submission outputs.
"""
from __future__ import annotations
import argparse, importlib.util, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "code"
RESULTS = ROOT / "results"
TRACES = [
    "friendsforever_flat", "clownschool_flat", "sveltecomponent",
    "json-crdt-blog-post", "json-crdt-patch", "seph-blog1", "rustcode",
    "automerge-paper",
]

def run(*args):
    print("+", *map(str, args), flush=True)
    proc = subprocess.run(
        [str(a) for a in args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n", flush=True)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace-dir", type=Path, help="directory containing the eight pinned *.json.gz trace files")
    ap.add_argument("--strict-reference", action="store_true", help="require fractional-indexing==0.1.3 cross-check")
    args = ap.parse_args()

    # Run the exact-rational SQLite ablation first.  On memory-constrained
    # runners, earlier large integer stress tests can temporarily slow this
    # experiment even after their subprocess exits.
    run(sys.executable, CODE / "same_encoder_ablation.py")

    run(sys.executable, CODE / "verify_core.py")
    if importlib.util.find_spec("fractional_indexing") is not None:
        run(sys.executable, CODE / "validate_fi_reference.py")
    elif args.strict_reference:
        raise SystemExit("fractional-indexing==0.1.3 is required by --strict-reference; install requirements.txt")
    else:
        print("SKIP: optional byte-for-byte fractional-indexing==0.1.3 cross-check (package not installed).")

    run(sys.executable, CODE / "synthetic_valid.py")
    run(sys.executable, CODE / "sqlite_scaling.py")
    run(sys.executable, CODE / "sqlite_threshold_matrix.py")
    run(sys.executable, CODE / "derive_tables.py")
    run(sys.executable, CODE / "environment_report.py")

    if args.trace_dir:
        run(sys.executable, CODE / "verify_trace_provenance.py", "--trace-dir", args.trace_dir,
            "--write-sha256", RESULTS / "rerun_trace_hashes.json")
        rr = RESULTS / "rerun"
        rr.mkdir(exist_ok=True)
        for trace in TRACES:
            for scheme, label in [("fi62", "FI-62"), ("sri", "Farey-SRI")]:
                run(sys.executable, CODE / "replay_trace.py", "--trace-dir", args.trace_dir,
                    "--trace", trace, "--scheme", scheme,
                    "--output", rr / f"{trace}__{label}.json",
                    "--keys-output", rr / f"{trace}__{label}.pkl")
        run(sys.executable, CODE / "compare_rerun.py")

    run(sys.executable, CODE / "make_figures.py")
    print("PASS: submission artifact pipeline completed.")

if __name__ == "__main__":
    main()
