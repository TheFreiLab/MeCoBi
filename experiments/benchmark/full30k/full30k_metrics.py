"""Summarise the full 30k benchmark run: rates + mean/median metrics + distributions + timing.

Reads mecobi_30k/_results_shard*.jsonl (run.py's --out-dir) and reports, overall and stratified by
CN / crystal geometry / metal: build success, connectivity-ok, shape-class match, and the MEAN and
MEDIAN of poly_cshm / dmat_rmsd / bond_rmsd (a collapsed/degenerate polyhedron's +inf CShM is
clamped to 100 so it counts as maximally deviant without poisoning the mean). Prints a CPU-time vs
elapsed timing report (shards run in parallel), and writes full30k_summary.csv (per-stratum rows).

Depth-2 c-kmRMSD is OFF by default (recomputing it for 30k structures is slow); pass --ckmrmsd to
include it.

    python full30k_metrics.py [--run-dir mecobi_30k] [--ckmrmsd]
"""
from __future__ import annotations

import argparse
import csv
import glob
import gzip
import json
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent   # full30k/: run dir + summary CSV
BENCH = HERE.parent                      # benchmark root: shared harness + frozen data
sys.path.insert(0, str(BENCH))
CONT = ["poly_cshm", "dmat_rmsd", "bond_rmsd"]
CN_UNIQUE = {2: "linear", 3: "trigonal_planar", 6: "octahedral",
             7: "pentagonal_bipyramidal", 9: "tricapped_trigonal_prism"}


def _load(path):
    if str(path).endswith(".gz"):
        return json.loads(gzip.open(path, "rt", encoding="utf-8").read())
    return json.loads(Path(path).read_text())


def _finite(xs):
    return [x for x in xs if x is not None and (not isinstance(x, float) or math.isfinite(x))]


def _clamp_cshm(x):
    if x is None:
        return None
    return 100.0 if (isinstance(x, (int, float)) and (not math.isfinite(x) or x > 100.0)) else x


def _summ(rows):
    n = len(rows)
    built = [r for r in rows if r.get("built")]
    scored = [r for r in rows if r.get("shape_match") is not None]
    out = {"n": n,
           "build_pct": round(100 * len(built) / n, 1) if n else None,
           "conn_pct": round(100 * sum(bool(r.get("connectivity_ok")) for r in built) / len(built), 1) if built else None,
           "shape_pct": round(100 * sum(bool(r.get("shape_match")) for r in scored) / len(scored), 1) if scored else None}
    for m in CONT:
        vals = _finite([_clamp_cshm(r.get(m)) if m.endswith("cshm") else r.get(m) for r in rows])
        out[f"{m}_mean"] = round(st.mean(vals), 3) if vals else None
        out[f"{m}_median"] = round(st.median(vals), 3) if vals else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default="mecobi_30k")
    ap.add_argument("--bundle", default="benchmark_bundle.json.gz")
    ap.add_argument("--ckmrmsd", action="store_true", help="also compute depth-2 c-kmRMSD (slow).")
    cfg = ap.parse_args()

    run_dir = HERE / cfg.run_dir
    bundle = {r["refcode"]: r for r in _load(BENCH / cfg.bundle)}
    geo = json.loads((BENCH / "benchmark_geom_labels.json").read_text()) \
        if (BENCH / "benchmark_geom_labels.json").exists() else {}

    def geom_label(rc):
        cn = bundle.get(rc, {}).get("cn")
        return geo.get(rc, CN_UNIQUE.get(cn, f"cn{cn}")) if cn in (2, 4, 5, 8) else CN_UNIQUE.get(cn, f"cn{cn}")

    rows, shard_walls = [], []
    for f in sorted(glob.glob(str(run_dir / "_results_shard*.jsonl"))):
        tot = 0.0
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                r["geometry_label"] = geom_label(r["refcode"])
                rows.append(r)
                if isinstance(r.get("wall_s"), (int, float)):
                    tot += r["wall_s"]
        shard_walls.append(tot)
    if not rows:
        print(f"no results in {run_dir}"); return

    if cfg.ckmrmsd:
        from ckmrmsd import build_core_from_xyz, ckmrmsd
        cores = _load(BENCH / "benchmark_cores_elem.json.gz")
        for r in rows:
            xyz = run_dir / "structures" / f"{r['refcode']}.xyz"
            cc = cores.get(r["refcode"])
            if cc and xyz.exists() and (b := bundle.get(r["refcode"])):
                try:
                    bc = build_core_from_xyz(xyz.read_text(encoding="utf-8"), b["metal"], b["cn"])
                    r["ckmrmsd"] = round(ckmrmsd(cc, bc)[0], 4) if bc else None
                except Exception:  # noqa: BLE001
                    r["ckmrmsd"] = None
        CONT.append("ckmrmsd")

    overall = _summ(rows)
    print(f"\n=== full benchmark ({overall['n']} structures) ===")
    print(f"  build {overall['build_pct']}%  connectivity {overall['conn_pct']}%  "
          f"shape-match {overall['shape_pct']}%")
    for m in CONT:
        print(f"  {m:<10} mean {overall[f'{m}_mean']}  median {overall[f'{m}_median']}")

    # timing (CPU-time = sum; elapsed ~ slowest shard, since shards run in parallel)
    walls = _finite([r.get("wall_s") for r in rows])
    cpu = sum(walls) / 3600 if walls else 0
    elapsed = max(shard_walls) / 3600 if shard_walls else 0
    print(f"\n  timing: CPU-time {cpu:.1f}h | est. elapsed {elapsed:.1f}h "
          f"({len(shard_walls)} shards) | median {round(st.median(walls), 1) if walls else '-'}s/cpx")

    # distributions -> CSV + console
    out_csv = HERE / "full30k_summary.csv"
    cols = (["stratum", "value", "n", "build_pct", "conn_pct", "shape_pct"]
            + [f"{m}_{k}" for m in CONT for k in ("mean", "median")])
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerow(["overall", "all"] + [overall[c] for c in cols[2:]])
        for key, kname in (("cn", "CN"), ("geometry_label", "geometry"), ("metal", "metal")):
            groups = defaultdict(list)
            for r in rows:
                groups[r.get(key)].append(r)
            for val in sorted(groups, key=lambda x: (x is None, x)):
                s = _summ(groups[val])
                w.writerow([kname, val] + [s[c] for c in cols[2:]])
    print(f"\n  by-CN / by-geometry / by-metal distributions -> {out_csv.name}")
    print("  === by CN ===")
    bycn = defaultdict(list)
    for r in rows:
        bycn[r.get("cn")].append(r)
    for cn in sorted(x for x in bycn if x is not None):
        s = _summ(bycn[cn])
        print(f"    CN{cn:<2} n={s['n']:<5} build {s['build_pct']}%  shape {s['shape_pct']}%  "
              f"poly {s['poly_cshm_median']}  dmat {s['dmat_rmsd_median']}  bond {s['bond_rmsd_median']}")


if __name__ == "__main__":
    main()
