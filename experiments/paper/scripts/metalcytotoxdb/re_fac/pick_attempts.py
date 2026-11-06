"""Combine the fac rebuild with its retries into one run directory for merge_mctdb.py.

    python pick_attempts.py --out ../structures_refac_final ../structures_refac_rerun ../structures_refac_retry_a ...

Per complex, the first attempt (in the order given) that built with connectivity_ok and whose three CO are fac
(check_fac.py criterion) wins. A complex with no such attempt is left out of the output, so in the merge it keeps
its structure of the base run (meridional); those are listed in left_out.txt.
"""
import argparse
import glob
import itertools
import json
import shutil
from pathlib import Path

import numpy as np


def is_fac(xyz):
    lines = Path(xyz).read_text().splitlines()
    rows = [ln.split() for ln in lines[2:2 + int(lines[0])]]
    sym = [r[0] for r in rows]
    x = np.array([[float(v) for v in r[1:4]] for r in rows])
    m = sym.index("Re")
    d = np.linalg.norm(x[:, None] - x[None], axis=2)
    # a CO: C within 2.3 A of Re with an O within 1.3 A (no test on its other neighbours, which a crowded
    # but intact sphere can bring within 1.9 A)
    co = [i for i, s in enumerate(sym) if s == "C" and d[m, i] < 2.3
          and any(sym[j] == "O" and d[i, j] < 1.3 for j in range(len(sym)))]
    if len(co) < 3:
        return False
    co = sorted(co, key=lambda i: d[m, i])[:3]
    u = [(x[i] - x[m]) / d[m, i] for i in co]
    return all(u[a] @ u[b] > np.cos(np.radians(150)) for a, b in itertools.combinations(range(3), 2))


ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("attempts", nargs="+")
a = ap.parse_args()
out = Path(a.out)
if out.exists():
    raise SystemExit(f"{out} exists; pick a new --out")
(out / "structures").mkdir(parents=True)
chosen, seen = {}, set()
for k, run in enumerate(a.attempts):
    for f in sorted(glob.glob(str(Path(run) / "_results_shard*.jsonl"))):
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            seen.add(r["name"])
            xyz = Path(run) / "structures" / f"{r['name']}.xyz"
            if r["name"] in chosen or not (r.get("built") and r.get("connectivity_ok") and xyz.exists()):
                continue
            if is_fac(xyz):
                chosen[r["name"]] = (k, r, xyz)
with (out / "_results_shard0of1.jsonl").open("w", encoding="utf-8") as fh:
    for name, (k, r, xyz) in sorted(chosen.items()):
        fh.write(json.dumps({**r, "attempt": a.attempts[k]}) + "\n")
        shutil.copyfile(xyz, out / "structures" / xyz.name)
left = sorted(seen - set(chosen))
(out / "left_out.txt").write_text("".join(f"{n}\n" for n in left))
per = {run: sum(1 for k, _, _ in chosen.values() if a.attempts[k] == run) for run in a.attempts}
print(f"{len(chosen)} fac with connectivity kept; {len(left)} left out (keep the base structure): {' '.join(left)}")
print(per)
