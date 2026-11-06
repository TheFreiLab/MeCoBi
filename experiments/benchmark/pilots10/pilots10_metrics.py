"""Per-pilot metrics for the 10x100 stratified benchmark: average, median, and distributions.

For each pilot ``pilots10/pilot_rNN.json`` built into ``pilots10/run_rNN/`` (run.py's --out-dir),
this joins the shard metrics (shape-match, poly_cshm, dmat_rmsd, bond_rmsd, connectivity) with a
freshly computed depth-2 c-kmRMSD (structures/<rc>.xyz vs the crystal core -- pure geometry, no
xtb/torch), then reports, per pilot:

  * headline rates   -- build success, connectivity-ok, shape-class match;
  * central tendency -- MEAN and MEDIAN of poly_cshm / dmat_rmsd / bond_rmsd / c-kmRMSD;
  * distributions    -- the same metrics broken down by CN and by crystal geometry.

Across the 10 pilots it prints each headline/central metric as ``mean +/- sd`` -- the spread is the
run-to-run variance of the benchmark on interchangeable representative samples. Writes one
per-structure CSV per pilot plus ``pilots10/summary.csv`` (one row per pilot) and
``pilots10/summary_pooled.csv`` (by-CN and by-geometry over all 1000).

    python pilots10_metrics.py                       # default pilots10/, run dirs pilots10/run_rNN
    python pilots10_metrics.py --pilots-dir pilots10 --run-tmpl run_r{:02d}
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

HERE = Path(__file__).resolve().parent   # pilots10/
BENCH = HERE.parent                      # benchmark root: shared harness + frozen data;
                                         # --out / --pilots-dir are relative to it
sys.path.insert(0, str(BENCH))

import hydrides  # noqa: E402
from ckmrmsd import build_core_like, ckmrmsd  # noqa: E402


CONT = ["poly_cshm", "dmat_rmsd", "bond_rmsd", "ckmrmsd"]     # continuous metrics (lower = better)
CSHM_METRICS = {"poly_cshm", "exp_cshm", "build_cshm"}        # bounded [0, 100] by definition
SHARD_COLS = ["refcode", "metal", "ox", "cn", "built", "connectivity_ok", "target_geometry",
              "shape_match", "exp_cshm", "build_cshm", "poly_cshm", "dmat_rmsd", "bond_rmsd",
              "site_cn", "cap_collapsed", "wall_s"]


def _clamp(col, x):
    """A CShM is mathematically in [0, 100]; a collapsed/degenerate build polyhedron makes the
    scale-fit blow up to +inf (or a spurious >100). Clamp those to 100 (maximally deviant) so the
    MEAN stays finite and still counts the bad build, rather than dropping or infecting it."""
    if x is None:
        return None
    if col in CSHM_METRICS and isinstance(x, (int, float)):
        if not math.isfinite(x) or x > 100.0:
            return 100.0
    return x


def _load(path):
    if str(path).endswith(".gz"):
        return json.loads(gzip.open(path, "rt", encoding="utf-8").read())
    return json.loads(Path(path).read_text())


def _finite(xs):
    return [x for x in xs if x is not None and (not isinstance(x, float) or math.isfinite(x))]


def _mean(xs):
    xs = _finite(xs)
    return round(st.mean(xs), 3) if xs else None


def _median(xs):
    xs = _finite(xs)
    return round(st.median(xs), 3) if xs else None


def _shard_wall_sums(run_dir: Path) -> list[float]:
    """Per-shard sum of wall_s. Shards run in PARALLEL within a pilot (run_pilots10.sh), so the
    pilot's real elapsed time is the SLOWEST shard (max), not the sum -- the sum is CPU-time."""
    sums = []
    for f in sorted(glob.glob(str(run_dir / "_results_shard*.jsonl"))):
        tot = 0.0
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                w = json.loads(line).get("wall_s")
                if isinstance(w, (int, float)) and math.isfinite(w):
                    tot += w
        sums.append(tot)
    return sums


def _shard_rows(run_dir: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for f in sorted(glob.glob(str(run_dir / "_results_shard*.jsonl"))):
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rows[r["refcode"]] = r
    return rows


def _ckm(rc, run_dir, bundle, cores, h=None):
    """depth-2 c-kmRMSD for one built structure, or None. ``h``: the hydride correction the build
    was made with (hydrides.py) -- the crystal core then carries the located M-H too."""
    b, cc = bundle.get(rc), hydrides.core(cores.get(rc), h)
    xyz = run_dir / "structures" / f"{rc}.xyz"
    if b is None or cc is None or not xyz.exists():
        return None
    try:
        cc, bc = build_core_like(cc, xyz.read_text(encoding="utf-8"), b["metal"])
        if bc is None:
            return None
        return round(ckmrmsd(cc, bc)[0], 4)
    except Exception:  # noqa: BLE001
        return None


def _summarise(rows: list[dict]) -> dict:
    """Headline rates + mean/median of the continuous metrics over a set of per-structure rows."""
    n = len(rows)
    built = [r for r in rows if r.get("built")]
    scored = [r for r in rows if r.get("shape_match") is not None]
    out = {
        "n": n,
        "build_pct": round(100 * len(built) / n, 1) if n else None,
        "connok_pct": round(100 * sum(bool(r.get("connectivity_ok")) for r in built)
                            / len(built), 1) if built else None,
        "shape_pct": round(100 * sum(bool(r.get("shape_match")) for r in scored)
                           / len(scored), 1) if scored else None,
    }
    for m in CONT:
        out[f"{m}_mean"] = _mean([r.get(m) for r in rows])
        out[f"{m}_median"] = _median([r.get(m) for r in rows])
    walls = _finite([r.get("wall_s") for r in rows])
    out["wall_total_s"] = round(sum(walls), 1) if walls else None
    out["wall_mean_s"] = round(st.mean(walls), 1) if walls else None
    out["wall_median_s"] = round(st.median(walls), 1) if walls else None
    out["wall_max_s"] = round(max(walls), 1) if walls else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilots-dir", default="pilots10")
    ap.add_argument("--run-tmpl", default="run_r{:02d}", help="run out-dir name per pilot index.")
    ap.add_argument("--bundle", default="benchmark_bundle.json.gz")
    ap.add_argument("--cores", default="benchmark_cores_elem.json.gz")
    cfg = ap.parse_args()

    pdir = BENCH / cfg.pilots_dir
    bundle = {r["refcode"]: r for r in _load(BENCH / cfg.bundle)}
    cores = _load(BENCH / cfg.cores)
    hyd = hydrides.load(classes=None)   # applied per row, only where the run added the hydrides
    geo = json.loads((BENCH / "benchmark_geom_labels.json").read_text()) \
        if (BENCH / "benchmark_geom_labels.json").exists() else {}

    def geom_label(rc):
        cn = bundle[rc]["cn"]
        return geo.get(rc, f"cn{cn}") if cn in (2, 4, 5, 8) else f"cn{cn}"

    pilot_files = sorted(pdir.glob("pilot_r*.json"))
    if not pilot_files:
        print(f"no pilot_r*.json in {pdir}"); return

    per_pilot_summary = []
    pooled_rows: list[dict] = []
    for pf in pilot_files:
        pi = int(pf.stem.split("_r")[1])
        run_dir = pdir / cfg.run_tmpl.format(pi)
        refs = json.loads(pf.read_text())
        shard = _shard_rows(run_dir)
        rows = []
        for rc in refs:
            r = {c: _clamp(c, shard.get(rc, {}).get(c)) for c in SHARD_COLS}
            r["refcode"] = rc
            r["cn"] = bundle.get(rc, {}).get("cn")
            r["metal"] = bundle.get(rc, {}).get("metal")
            r["geometry_label"] = geom_label(rc) if rc in bundle else None
            r["ckmrmsd"] = _ckm(rc, run_dir, bundle, cores,
                                hyd.get(rc) if shard.get(rc, {}).get("hydrides_added") else None)
            rows.append(r)
        # per-structure CSV
        with (pdir / f"pilot_r{pi:02d}_metrics.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=SHARD_COLS + ["geometry_label", "ckmrmsd"],
                               extrasaction="ignore")
            w.writeheader(); w.writerows(rows)
        s = _summarise(rows)
        s["pilot"] = f"r{pi:02d}"
        sw = _shard_wall_sums(run_dir)
        s["n_shards"] = len(sw)
        s["wall_elapsed_s"] = round(max(sw), 1) if sw else None   # slowest shard = pilot elapsed
        per_pilot_summary.append(s)
        for r in rows:
            r["pilot"] = f"r{pi:02d}"
        pooled_rows += rows

    # summary.csv -- one row per pilot
    cols = (["pilot", "n", "build_pct", "connok_pct", "shape_pct"]
            + [f"{m}_{k}" for m in CONT for k in ("mean", "median")]
            + ["n_shards", "wall_total_s", "wall_elapsed_s", "wall_mean_s",
               "wall_median_s", "wall_max_s"])
    with (pdir / "summary.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(per_pilot_summary)

    # pooled distributions by CN and by geometry
    with (pdir / "summary_pooled.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["stratum", "value", "n", "build_pct", "shape_pct"]
                   + [f"{m}_{k}" for m in CONT for k in ("mean", "median")])
        for key, keyname in (("cn", "CN"), ("geometry_label", "geometry")):
            groups = defaultdict(list)
            for r in pooled_rows:
                groups[r.get(key)].append(r)
            for val in sorted(groups, key=lambda x: (x is None, x)):
                s = _summarise(groups[val])
                w.writerow([keyname, val, s["n"], s["build_pct"], s["shape_pct"]]
                           + [s[f"{m}_{k}"] for m in CONT for k in ("mean", "median")])

    # ---- console report ----
    print(f"\n=== per-pilot summary ({len(pilot_files)} pilots) -- values are mean/median ===")
    hdr = f"{'pilot':>6} {'n':>4} {'build%':>7} {'conn%':>6} {'shape%':>7} " + \
        " ".join(f"{m.split('_')[0][:8]:>13}" for m in CONT)
    print(hdr)
    def _f(x, w=0):
        return f"{'-' if x is None else x:>{w}}"

    for s in per_pilot_summary:
        line = f"{s['pilot']:>6} {s['n']:>4} {_f(s['build_pct'], 6)}% {_f(s['connok_pct'], 5)}% " \
               f"{_f(s['shape_pct'], 6)}% "
        line += " ".join(f"{_f(s[f'{m}_mean'])}/{_f(s[f'{m}_median'])}".rjust(13) for m in CONT)
        print(line)

    # ---- timing report (wall_s = build + relax per structure) ----
    # CPU-time = sum of all per-structure times (total compute). ELAPSED = real wall-clock: shards
    # run in parallel within a pilot so the pilot takes as long as its SLOWEST shard, and the ten
    # pilots run in series (run_pilots10.sh), so elapsed ~= sum of per-pilot slowest-shard times.
    print("\n=== timing (wall_s per structure = assembly + xtb relax) ===")
    print(f"{'pilot':>6} {'shards':>7} {'CPU-time':>9} {'elapsed':>8} "
          f"{'mean':>6} {'median':>7} {'max':>7}")
    for s in per_pilot_summary:
        cpu = s['wall_total_s'] or 0
        el = s['wall_elapsed_s']
        print(f"{s['pilot']:>6} {_f(s['n_shards'], 7)} {cpu/3600:>8.2f}h "
              f"{_f(f'{el/60:.1f}m' if el else '-', 8)} {_f(s['wall_mean_s'], 5)}s "
              f"{_f(s['wall_median_s'], 6)}s {_f(s['wall_max_s'], 6)}s")
    tot_cpu = sum(s['wall_total_s'] or 0 for s in per_pilot_summary)
    tot_elapsed = sum(s['wall_elapsed_s'] or 0 for s in per_pilot_summary)
    allw = _finite([r.get("wall_s") for r in pooled_rows])
    print(f"  ALL   CPU-time {tot_cpu/3600:.2f}h ({tot_cpu/60:.0f} CPU-min) | "
          f"est. elapsed {tot_elapsed/3600:.2f}h ({tot_elapsed/60:.0f} min, "
          f"{per_pilot_summary[0]['n_shards']} shards/pilot, pilots serial) | "
          f"{len(allw)} structures, mean {round(st.mean(allw), 1) if allw else '-'}s, "
          f"median {round(st.median(allw), 1) if allw else '-'}s")
    # slowest few, and per-CN timing (CN drives cost)
    slow = sorted((r for r in pooled_rows if r.get("wall_s") is not None),
                  key=lambda r: r["wall_s"], reverse=True)[:5]
    print("  slowest:", ", ".join(f"{r['refcode']}({r['wall_s']:.0f}s,CN{r['cn']})" for r in slow))
    bycn = defaultdict(list)
    for r in pooled_rows:
        if r.get("wall_s") is not None:
            bycn[r["cn"]].append(r["wall_s"])
    print("  by CN (median s):",
          "  ".join(f"CN{cn}:{round(st.median(v), 1)}" for cn, v in sorted(bycn.items())))

    # across-pilot mean +/- sd (run-to-run variance)
    print("\n=== across the 10 pilots (mean +/- sd) ===")
    for label, key in [("build %", "build_pct"), ("connectivity %", "connok_pct"),
                       ("shape-match %", "shape_pct")] + \
            [(f"{m} (mean)", f"{m}_mean") for m in CONT]:
        vals = [s[key] for s in per_pilot_summary if s.get(key) is not None]
        if vals:
            sd = round(st.pstdev(vals), 3) if len(vals) > 1 else 0.0
            print(f"  {label:<18} {round(st.mean(vals), 3):>8} +/- {sd}")
    print(f"\nwrote per-pilot CSVs + summary.csv + summary_pooled.csv -> {pdir}")


if __name__ == "__main__":
    main()
