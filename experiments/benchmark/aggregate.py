"""Combine run.py shard results (_results_shard*.jsonl) into the benchmark table:
build-success rate, shape-class match, CShM, distance-matrix RMSD, bond RMSD --
overall and stratified by CN, OS, and metal. Writes benchmark_table.csv."""
from __future__ import annotations

import csv
import glob
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(st.median(xs), 3) if xs else None


def main():
    rows = []
    for f in glob.glob(str(HERE / "_results_shard*.jsonl")):
        for line in Path(f).read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    if not rows:
        print("no shard results found"); return

    with (HERE / "benchmark_results.csv").open("w", newline="", encoding="utf-8") as fh:
        cols = ["refcode", "metal", "ox", "cn", "built", "shape_match", "exp_cshm",
                "build_cshm", "poly_cshm", "dmat_rmsd", "bond_rmsd", "bond_offset", "error"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)

    scored = [r for r in rows if r.get("shape_match") is not None]
    built = [r for r in rows if r.get("built")]

    def summarise(name, groups):
        print(f"\n=== by {name} ===")
        print(f"{name:>8} {'n':>6} {'build%':>7} {'shape%':>7} {'poly':>6} {'CShM':>6} "
              f"{'dmat':>6} {'bond':>6}")
        for key in sorted(groups):
            g = groups[key]
            sc = [r for r in g if r.get("shape_match") is not None]
            b = sum(bool(r.get("built")) for r in g)
            sm = sum(bool(r.get("shape_match")) for r in sc)
            print(f"{str(key):>8} {len(g):>6} {100*b/len(g):>6.0f}% "
                  f"{(100*sm/len(sc)) if sc else 0:>6.0f}% "
                  f"{med([r.get('poly_cshm') for r in sc]) or 0:>6} "
                  f"{med([r.get('build_cshm') for r in sc]) or 0:>6} "
                  f"{med([r.get('dmat_rmsd') for r in sc]) or 0:>6} "
                  f"{med([r.get('bond_rmsd') for r in sc]) or 0:>6}")

    by_cn = defaultdict(list); by_os = defaultdict(list); by_metal = defaultdict(list)
    for r in rows:
        by_cn[r["cn"]].append(r); by_os[r["ox"]].append(r); by_metal[r["metal"]].append(r)

    print(f"=== MeCoBi structural benchmark (n={len(rows)}) ===")
    print(f"build success: {len(built)}/{len(rows)} = {100*len(built)/len(rows):.1f}%")
    print(f"scored:        {len(scored)}/{len(rows)}")
    sm = sum(bool(r.get('shape_match')) for r in scored)
    print(f"shape-class match: {sm}/{len(scored)} = {100*sm/max(len(scored),1):.1f}%")
    print(f"median build CShM: {med([r.get('build_cshm') for r in scored])}   "
          f"exp CShM: {med([r.get('exp_cshm') for r in scored])}")
    print(f"median poly CShM (build-vs-crystal, label-free): "
          f"{med([r.get('poly_cshm') for r in scored])}")
    print(f"median dmat RMSD: {med([r.get('dmat_rmsd') for r in scored])} A   "
          f"bond RMSD: {med([r.get('bond_rmsd') for r in scored])} A   "
          f"bond offset: {med([r.get('bond_offset') for r in scored])} A")
    summarise("CN", by_cn)
    summarise("OS", by_os)
    print(f"\nwrote {HERE/'benchmark_results.csv'}")


if __name__ == "__main__":
    main()
