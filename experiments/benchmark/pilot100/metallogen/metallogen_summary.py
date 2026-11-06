"""Summarise a MetalloGen run: built count, generation-time stats, error buckets.

    python metallogen_summary.py [results_dir]     # default: ./metallogen_det
"""
from __future__ import annotations

import glob
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
d = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "metallogen_det"

recs = []
shard_walls = []                       # per-shard sum of wall_s -> the max is the real elapsed time
for f in sorted(glob.glob(str(d / "_metallogen_results_shard*.jsonl"))):
    shard = [json.loads(line) for line in open(f, encoding="utf-8")]
    recs += shard
    shard_walls.append(sum(r["wall_s"] for r in shard if r.get("wall_s") is not None))

if not recs:
    raise SystemExit(f"no _metallogen_results_shard*.jsonl under {d}")

built = [r for r in recs if r.get("built")]
fail = [r for r in recs if not r.get("built")]
walls = [r["wall_s"] for r in recs if r.get("wall_s") is not None]
bwalls = [r["wall_s"] for r in built if r.get("wall_s") is not None]

print(f"results dir        : {d}")
print(f"records            : {len(recs)}")
print(f"built              : {len(built)}")
print(f"failed             : {len(fail)}")
if walls:
    # sum(walls) is aggregate CPU-time (total compute); the shards ran in PARALLEL, so the real
    # wall-clock is the slowest shard (max per-shard sum), NOT the sum.
    cpu_min = sum(walls) / 60
    elapsed_min = max(shard_walls) / 60 if shard_walls else cpu_min
    print(f"generation time    : CPU-time {cpu_min:.1f} min over {len(walls)} runs | "
          f"est. elapsed {elapsed_min:.1f} min ({len(shard_walls)} shards, slowest-shard bound)")
    print(f"  per complex (all): median {st.median(walls):.1f}s  mean {st.mean(walls):.1f}s  "
          f"max {max(walls):.1f}s")
if bwalls:
    print(f"  per built complex: median {st.median(bwalls):.1f}s  mean {st.mean(bwalls):.1f}s")

buckets = Counter(r.get("run_status", "?") for r in fail)
if buckets:
    print("failure buckets    :")
    for kbucket, ncount in buckets.most_common():
        print(f"  {ncount:3d}  {kbucket}")
