"""Build 10 disjoint validation pilots of 100 complexes each, stratified by (CN, geometry).

Each pilot mirrors the natural (coordination-number, crystal-shape) distribution of the eligible
benchmark pool, so the 10 runs are interchangeable representative samples -- the spread across them
measures run-to-run variance of the metrics, not sampling bias. The 1000 refcodes are disjoint from
each other and from pilot_1 / pilot_2, scorable (ground-truth donors + a crystal sphere), and
non-lanthanide (the f-block relaxes poorly under GFN2-xTB).

Geometry label comes from the crystal SPHERE (metrics.best_shape on the donor directions) -- pure
geometry, no CIF/xtb/torch. For a CN whose ideal shape is unique (2,3,6,7,9) every complex gets the
same label, so the stratum collapses to CN; CN 4/5/8 split by real crystal shape, which is where a
representative geometry mix actually matters. Reproducible (fixed seed, sorted pools).

    python make_pilots10.py                 # -> pilots10/pilot_r01.json ... pilot_r10.json (+ coverage)
    python make_pilots10.py --total 1000 --pilots 10 --seed 10
"""
from __future__ import annotations

import argparse
import gzip
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent   # pilots10/
BENCH = HERE.parent                      # benchmark root: shared harness + frozen data;
                                         # --out / --pilots-dir are relative to it
sys.path.insert(0, str(BENCH))

import metrics as M  # noqa: E402

LANTHANIDES = {"La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy",
               "Ho", "Er", "Tm", "Yb", "Lu"}


def _load_set(path):
    if str(path).endswith(".gz"):
        return set(json.loads(gzip.open(path, "rt", encoding="utf-8").read()))
    return set(json.loads(Path(path).read_text()))


# Only these CN have more than one common geometry; every other CN has a unique ideal shape, so
# its stratum is just the CN (and we skip the ~15 ms/complex CShM there).
_AMBIGUOUS_CN = {4, 5, 8}


def _geom_label(sphere_entry, cn) -> str:
    """(shape) label from the crystal sphere, or ``cn{n}`` when the shape is unique/undetermined.

    CN 4/5/8 split (square-planar vs tetrahedral, tbp vs square-pyramidal, antiprism vs
    dodecahedron) -- computed by CShM. Every other CN has one ideal shape, so the label is just
    ``cn{n}``; a sphere whose donor count doesn't match CN (haptic caps) also falls back to it."""
    if cn not in _AMBIGUOUS_CN:
        return f"cn{cn}"
    try:
        m = np.asarray(sphere_entry["metal_xyz"], float)
        d = np.asarray(sphere_entry["donors"], float)
        if len(d) == cn:
            dirs = (d - m) / np.linalg.norm(d - m, axis=1, keepdims=True)
            name, _ = M.best_shape(dirs, cn)
            if name:
                return name
    except Exception:  # noqa: BLE001
        pass
    return f"cn{cn}"


def _allocate(freq: dict, total: int) -> dict:
    """Largest-remainder allocation of ``total`` slots across strata by frequency (sums to total)."""
    tot = sum(freq.values())
    raw = {k: total * v / tot for k, v in freq.items()}
    base = {k: int(v) for k, v in raw.items()}
    short = total - sum(base.values())
    for k in sorted(freq, key=lambda k: raw[k] - base[k], reverse=True)[:short]:
        base[k] += 1
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--total", type=int, default=1000, help="total refcodes across all pilots.")
    ap.add_argument("--pilots", type=int, default=10)
    ap.add_argument("--seed", type=int, default=10)
    ap.add_argument("--out", default="pilots10", help="output dir for pilot_rNN.json files.")
    cfg = ap.parse_args()
    assert cfg.total % cfg.pilots == 0, "total must divide evenly among pilots"
    per = cfg.total // cfg.pilots

    bundle = {r["refcode"]: r
              for r in json.loads(gzip.open(BENCH / "benchmark_bundle.json.gz", "rt").read())}
    spheres = json.loads(gzip.open(BENCH / "benchmark_spheres.json.gz", "rt").read())
    donors = _load_set(BENCH / "benchmark_donors.json")
    used = _load_set(BENCH / "pilot100" / "pilot_100.json") | _load_set(BENCH / "pilot100" / "pilot_2.json")

    # geometry labels: cached (CShM is ~15 ms/complex for CN 4/5/8), so the first build is a few
    # minutes and every later run is instant. Only ambiguous-CN labels are stored.
    cache_path = BENCH / "benchmark_geom_labels.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    eligible = [rc for rc, r in bundle.items()
                if rc in donors and rc in spheres and rc not in used
                and r["metal"] not in LANTHANIDES]
    todo = [rc for rc in eligible if bundle[rc]["cn"] in _AMBIGUOUS_CN and rc not in cache]
    if todo:
        print(f"labelling geometry for {len(todo)} CN-4/5/8 complexes (cached after)...", flush=True)
        for k, rc in enumerate(todo, 1):
            cache[rc] = _geom_label(spheres[rc], bundle[rc]["cn"])
            if k % 2000 == 0:
                print(f"  {k}/{len(todo)}", flush=True)
        cache_path.write_text(json.dumps(cache))

    # eligible pool + stratum (CN, geometry), stratum -> sorted refcode list
    strata: dict[tuple, list[str]] = defaultdict(list)
    for rc in eligible:
        cn = bundle[rc]["cn"]
        label = cache.get(rc, f"cn{cn}") if cn in _AMBIGUOUS_CN else f"cn{cn}"
        strata[(cn, label)].append(rc)
    for k in strata:
        strata[k].sort()
    freq = {k: len(v) for k, v in strata.items()}
    print(f"eligible pool: {sum(freq.values())} refcodes in {len(freq)} (CN,shape) strata")

    # proportional allocation of `total`, capped at what each stratum can supply; top up the deficit
    rng = random.Random(cfg.seed)
    alloc = _allocate(freq, cfg.total)
    picked_by_stratum: dict[tuple, list[str]] = {}
    deficit = 0
    for k, need in alloc.items():
        take = min(need, len(strata[k]))
        picked_by_stratum[k] = rng.sample(strata[k], take)
        deficit += need - take
    if deficit:  # under-populated strata -> refill from the largest remaining pools
        remaining = [rc for k, v in strata.items() for rc in v if rc not in set(picked_by_stratum[k])]
        remaining.sort()
        picked_by_stratum[("_topup", "")] = rng.sample(remaining, min(deficit, len(remaining)))

    # deal each stratum's picks round-robin across the pilots so every pilot is representative
    pilots: list[list[str]] = [[] for _ in range(cfg.pilots)]
    flat = [rc for k in sorted(picked_by_stratum, key=str) for rc in picked_by_stratum[k]]
    rng.shuffle(flat)                                   # break any residual stratum ordering
    flat.sort(key=lambda rc: (bundle[rc]["cn"], rc))    # then re-block by CN for even round-robin
    for idx, rc in enumerate(flat):
        pilots[idx % cfg.pilots].append(rc)

    out_dir = BENCH / cfg.out
    out_dir.mkdir(exist_ok=True)
    all_picked = [rc for p in pilots for rc in p]
    assert len(all_picked) == len(set(all_picked)), "pilots overlap"
    assert not (set(all_picked) & used), "overlaps pilot_1/pilot_2"

    for pi, refs in enumerate(pilots, 1):
        (out_dir / f"pilot_r{pi:02d}.json").write_text(json.dumps(sorted(refs)))

    # coverage report
    print(f"\nwrote {cfg.pilots} pilots of ~{per} -> {out_dir}/pilot_rNN.json  "
          f"({len(all_picked)} total, all disjoint)")
    print("\nCN distribution (target vs each pilot):")
    print(f"  {'CN':>4} {'pool%':>6} " + " ".join(f"p{p+1:02d}" for p in range(cfg.pilots)))
    for cn in sorted({bundle[rc]['cn'] for rc in all_picked}):
        poolpct = 100 * sum(1 for rc in all_picked if bundle[rc]['cn'] == cn) / len(all_picked)
        row = [sum(1 for rc in p if bundle[rc]['cn'] == cn) for p in pilots]
        print(f"  {cn:>4} {poolpct:>5.0f}% " + " ".join(f"{x:>3}" for x in row))
    shapes = Counter((bundle[rc]['cn'], _geom_label(spheres[rc], bundle[rc]['cn']))
                     for rc in all_picked)
    print("\n(CN,shape) strata across all 1000:")
    for k, c in sorted(shapes.items()):
        print(f"  CN{k[0]:<2} {k[1]:<24} {c}")
    print("\nmetals (top 15):",
          dict(Counter(bundle[rc]['metal'] for rc in all_picked).most_common(15)))


if __name__ == "__main__":
    main()
