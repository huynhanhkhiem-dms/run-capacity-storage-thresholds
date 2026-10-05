# Run-Capacity Profiles for Immutable Order Keys

Reproducibility package for the study **Run-Capacity Profiles for Immutable Order Keys: Predicting Database Storage Thresholds**.


## Scope


The study concerns sequential, immutable, relabeling-free order-key allocation. It does not present the minimum-denominator allocator as a new rational-number or dynamic-labeling method, and it does not claim a complete multi-replica CRDT identifier protocol. The paper's mechanism-level scholarly objects are the allocator-facing run-capacity profile, the finite-alphabet capacity envelope and cumulative-storage floor, the exact Greenspan/rocicorp directional capacity law, and the threshold-crossing signature that transfers cumulative capacity to physical storage limits and recovers or bounds capacity from observed crossings. The monotone-cost ordering of exact depth sequences is explicitly treated as the finite empirical form of the standard usual stochastic order, not as a new stochastic-order result. The Greenspan/rocicorp midpoint routine is an exact constant-profile instantiation; the minimum-denominator allocator is a comparison policy, not a claimed new rational or labeling method.
The archived machine-readable results use the historical label `Farey-SRI` for that minimum-denominator comparison policy; `Farey-SRI` and `SRI` refer to the same implementation and the label is not a novelty claim.


## Primary metric


All cross-scheme size comparisons use physical stored bytes. For the continued-fraction implementation, logical bit length is retained only as an internal diagnostic; padding to the final byte is included in reported stored size. This prevents comparisons between ASCII storage bits on one side and unpadded logical bits on the other.


## Contents


- code/cfkey.py: iterative minimum-denominator allocator, reduced-mediant diagnostic, and order-preserving continued-fraction byte encoding.
- code/orderkeys.py: iterative local implementation of the Greenspan/rocicorp fractional-indexing format.
- code/verify_core.py: deterministic correctness tests for rational allocation, byte ordering, the finite-alphabet capacity envelope and cumulative-storage floor, the sharp and identifiable run-capacity--cost correspondence, the standard monotone-cost ordering check, exact directional midpoint growth, cumulative-byte formulas, threshold-signature recovery, sparse-signature bounds, and payload-perturbation identification.
- code/validate_fi_reference.py: byte-for-byte comparison with fractional-indexing==0.1.3 when installed.
- code/replay_trace.py: sequential editing-trace replay; reports physical byte metrics and optional logical-bit diagnostics.
- code/reproduce_historical_recursion.py: reproduces the recursion-depth behavior of the historical Python port v0.1.3.
- code/synthetic_valid.py: synthetic workload patterns using stored-byte metrics.
- code/same_encoder_ablation.py: maps the canonical Greenspan midpoint positions to exact rationals and re-encodes both midpoint and SRI positions with the identical continued-fraction byte encoder, including a SQLite 4 KiB storage check.
- code/sqlite_scaling.py: controlled 4 KiB canonical-run SQLite scaling experiment with dbstat page-type accounting.
- code/sqlite_threshold_matrix.py: theory-predicted first-overflow-page validation across 1, 2, 4, and 8 KiB page sizes plus a 4 KiB fixed-payload sensitivity matrix (0, 16, 32, and 48 bytes).
- code/derive_tables.py: regenerates the real-trace summary CSV from archived per-trace JSON.
- code/dbexp.py: SQLite storage/timing experiment; new runs record Python, SQLite, OS, page size, and layout metadata.
- code/environment_report.py: writes the local execution environment to results/environment.json.
- code/reproduce_all.py: deterministic one-command pipeline and optional full trace rerun.
- TRACE_PROVENANCE.json: pinned external-corpus commit and Git blob SHAs.
- results/real_traces/: archived per-trace summaries used for the paper.
- results/sqlite_scaling.json: controlled 4 KiB SQLite scaling results, including overflow-page counts.
- results/sqlite_threshold_matrix.json: theory-predicted and observed first-overflow-page thresholds across seven distinct page-size/payload configurations.
- results/dbexp_single_run.json: archived real-trace SQLite stress-case experiment; latency fields are descriptive single-run measurements.
- results/synthetic_valid.json: regenerated synthetic stored-byte results.
- results/same_encoder_ablation.json: representation-controlled allocation-policy ablation reported in the manuscript.
- results/derived_real_trace_summary.csv: deterministic table derivation from the archived summaries.


## Environment and deterministic checks


Create an environment and run:

```bash
bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python code/reproduce_all.py
```


The core suite checks exhaustive ordering/round trips on 5,881 reduced rationals, 50,000 random pair comparisons, 10,000 brute-force minimum-denominator intervals, 20,049 random insert/delete allocations, the finite-alphabet capacity envelope and cumulative-storage floor against exact shortest-string packing for alphabets 2, 4, 16, 62, and 256, the capacity-profile depth/tail-sum identities, generalized nondecreasing depth-cost identity, strictly-monotone inversion on 250 deterministic variable profiles, 250 paired monotone-cost order constructions, deterministic polynomial/exponential capacity-growth examples, plus the constant-profile identity for capacities 1--32 and run lengths through 1,000, the exact base-62/base-36 directional midpoint formulas plus cumulative-byte identities for the first 250 insertions, the generalized threshold-crossing formula, exact threshold-signature recovery, sharp sparse-signature bounds, and inverse no-overflow criterion on 1,000 deterministic exact variable profiles plus 1,000 randomized constant-profile specializations with payload-perturbation checks, a direct cross-check of the closed-form canonical midpoint-to-rational mapping used by the same-encoder ablation, and 666 instances of the mediant-gap family.


## External editing traces and provenance


The artifact does not redistribute the josephg/editing-traces corpus. For new end-to-end runs, use the ASCII sequential traces from the snapshot recorded in TRACE_PROVENANCE.json:

- repository: josephg/editing-traces
- commit: 762fa6c51605c88a05ebe5c4b9d4540caca30b97
- directory: sequential_traces/ascii_only

For convenience, the artifact can fetch exactly those eight public files and verify their Git blob IDs before writing them:

```bash
bash
python code/fetch_traces.py
python code/reproduce_all.py --trace-dir external_traces
```


Alternatively, with an existing checkout, run:

```bash
bash
python code/reproduce_all.py --trace-dir /path/to/editing-traces/sequential_traces/ascii_only
```


The replay asserts the between-neighbor invariant and reconstructs the final document by sorting the stored (byte_key, character) pairs on the byte key alone.


## Provenance limitation of the archived JSON


The per-trace JSON summaries in results/real_traces/ were created before the original workflow recorded input hashes at run time. GitHub path history verified on 2026-09-21 shows that all eight pinned input paths have been unchanged since their listed 2023 commits, predating the 2026 experiments. The summaries are therefore retained as archived expected outputs, not described as contemporaneously hash-attested outputs. Fresh reruns are hash-gated by verify_trace_provenance.py and checked against those deterministic expected metrics by compare_rerun.py.


## Baseline boundaries


FI-36 changes only the fractional digit alphabet of the Greenspan-compatible allocator and is a radix-sensitivity test; it is not Jira LexoRank. The reduced-mediant result is an allocation-rule diagnostic, not a reproduction of ESBT. Weidner's position-strings is treated as a close modern implementation reference in the manuscript; its stronger uniqueness and non-interleaving semantics mean that its published benchmark is not presented as an interchangeable sequential baseline.


## SQLite experiments


code/sqlite_threshold_matrix.py tests the page-transition rule along two configured axes. At a 16-byte fixed payload, the predicted first-overflow-page insertions are r=1,041, 2,326, 4,901, and 10,041 for 1, 2, 4, and 8 KiB pages, respectively. At 4 KiB, fixed payloads of 0, 16, 32, and 48 bytes predict r=4,981, 4,901, 4,821, and 4,741. Thus each additional 16 payload bytes advances the boundary by exactly 80 insertions for this constant-capacity run. Every configuration checks r*-1 and r* with dbstat. The two axes contain seven distinct page-size/payload configurations because the 4 KiB/16-byte case is shared. code/sqlite_scaling.py separately follows the 4 KiB/16-byte case beyond its transition to quantify post-overflow file growth.

results/dbexp_single_run.json is a separate archived exploratory real-trace stress case on sveltecomponent, selected after the trace comparison because that trace has the largest observed FI-62/SRI live-byte ratio. It is retained as external-validity evidence rather than a representative database estimate.



## Submission reproducibility contract


- python code/reproduce_all.py runs the self-contained deterministic theorem/encoding/synthetic checks, the same-encoder ablation, the controlled SQLite scaling experiment, and regenerates derived tables and figures. The optional cross-check against the external PyPI package fractional-indexing==0.1.3 runs automatically when that package is installed; use --strict-reference to require it.
- python code/reproduce_all.py --trace-dir /path/to/editing-traces/sequential_traces/ascii_only first runs verify_trace_provenance.py, which computes Git blob SHA-1 directly from the local compressed bytes and checks all eight files against TRACE_PROVENANCE.json. It then replays FI-62 and Farey-SRI on every trace and runs compare_rerun.py; any mismatch in deterministic scientific metrics is a hard failure.
- Wall-clock timings are not part of the equality check because they are machine dependent. Counts, maximum/percentile key lengths, live bytes, and generated bytes are checked exactly.
- Raw public traces are not copied into the supplementary ZIP; their repository, commit, subdirectory, and blob IDs are pinned instead.

## Citation and authorship

Author: **Huynh Anh Khiem**  
Faculty of Information Technology, Ton Duc Thang University, Ho Chi Minh City, Vietnam  
ORCID: `0009-0007-7210-174X`

If you use this repository, please cite the accompanying article once its bibliographic record is available.

## Repository scope

This repository contains the code, archived derived results, figures, experiment configuration, and provenance metadata required to reproduce the reported analyses. It intentionally does not redistribute the external `josephg/editing-traces` corpus; the exact upstream commit and Git blob identifiers are pinned in `TRACE_PROVENANCE.json`.