"""Summarise a molSimplify deterministic run: built count, haptic-fallback builds, error histogram.

    python molsim_summary.py [results_dir]     # default: ./molsimplify_det, else arch_comparison/molsimplify
"""
from __future__ import annotations

import glob
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
d = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "molsimplify_det"
if not any(glob.glob(str(d / "_molsim_results_shard*.jsonl"))):
    d = HERE.parents[3] / "arch_comparison" / "molsimplify"  # older runs wrote here

recs = []
for f in sorted(glob.glob(str(d / "_molsim_results_shard*.jsonl"))):
    recs += [json.loads(line) for line in open(f, encoding="utf-8")]

built = [r for r in recs if r.get("built")]
fail = [r for r in recs if not r.get("built")]
haptic = [r for r in built if r.get("haptic_fallback")]
deffb = [r for r in built if r.get("default_fallback")]

print(f"results dir        : {d}")
print(f"records            : {len(recs)}")
print(f"built              : {len(built)}")
print(f"  crystal geometry : {len(built) - len(haptic) - len(deffb)}  (matched target core)")
print(f"  haptic fallback  : {len(haptic)}  (site collapse -> atom-CN default core, flagged)")
print(f"  default fallback : {len(deffb)}  (target core failed -> molSimplify default, flagged)")
print(f"failed             : {len(fail)}")


def bucket(e: str) -> str:
    if ".dat" in e and "FileNotFound" in e:
        return "dat_missing (geometry-code bug; should be 0)"
    if "KeyError: '0-1'" in e:
        return "keyerror_0-1 (molSimplify internal; default_fallback recovers sqp/spy only)"
    if "mismatch" in e:
        return "coord_mismatch (haptic/coord bug; should be 0)"
    if "hung" in e or "timeout" in e.lower():
        return "hung/timeout"
    if "no CN" in e or "no molSimplify" in e:
        return "honest skip (CN9/unsupported core)"
    return e.split(":")[0][:40] or "(empty)"


hist = Counter(bucket(r.get("error", "")) for r in fail)
print("failure buckets    :")
for k, n in hist.most_common():
    print(f"  {n:3d}  {k}")
