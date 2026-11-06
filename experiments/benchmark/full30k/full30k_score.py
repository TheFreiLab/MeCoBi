"""Score every structure of a full-benchmark run, in parallel, with the pilot report's scorer.

full30k_metrics.py summarises what run.py scored at build time. This script RE-SCORES each built
structure with ``pilot100/compare_tools.score`` -- the code behind the pilot-100 tool comparison --
so the 30k numbers are the same metrics, computed the same way: CN match, shape match, poly-CShM,
dmat RMSD, bond RMSD, depth-2 c-kmRMSD and D-MAE3 (see the README's Metrics section).

Pure geometry: needs the run dir (JSONL + structures/) and the frozen reference files of the repo,
no CIFs and no xtb. The reference carries a complex's located hydrides when the run was built with
the hydride corrections (run_meta.json) and the build has them. Resumable: finished refcodes are
kept in ``<run-dir>/_score.jsonl`` (``--rescore`` discards them, after a change to the metrics).

    python full30k/full30k_score.py --run-dir mecobi_30k_xtb671 --workers 48
        -> full30k/<run-dir>_per_structure.csv + full30k/<run-dir>_score_summary.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import gzip
import json
import math
import os
import statistics as st
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent   # full30k/
BENCH = HERE.parent                      # benchmark root: shared harness + frozen data
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(BENCH / "pilot100"))

METRICS = ["ckmrmsd", "dmae3", "poly_cshm", "dmat_rmsd", "bond_rmsd"]
COLS = ["refcode", "metal", "ox", "cn", "geometry_label", "built", "build_mode", "connectivity_ok",
        "wall_s", "build_s", "cn_expected", "cn_detected", "cn_match", "donor_source",
        "shape_match", *METRICS, "ckm_n_matched", "ckm_core_n", "dmae3_n_matched", "dmae3_core_n",
        "n_hydride", "error"]
CN_UNIQUE = {2: "linear", 3: "trigonal_planar", 6: "octahedral",
             7: "pentagonal_bipyramidal", 9: "tricapped_trigonal_prism"}


def _load(path):
    if str(path).endswith(".gz"):
        return json.loads(gzip.open(path, "rt", encoding="utf-8").read())
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _score_one(job):
    """Worker: one structure -> ``{"refcode", metrics...}`` (compare_tools.score)."""
    import compare_tools as ct
    import hydrides
    from metrics import parse_xyz
    rc, xyz_path, rec, spec, sphere, core, core3, h = job
    try:
        xyz = Path(xyz_path).read_text(encoding="utf-8")
        if h:   # the reference carries the located hydrides only if the build has them
            syms, P = parse_xyz(xyz)
            if rec["metal"] in syms and len(hydrides.build_hydrides(
                    syms, P, syms.index(rec["metal"]), h["n_h"])) == h["n_h"]:
                sphere, core = hydrides.sphere(sphere, h), hydrides.core(core, h)
        return {"refcode": rc, **ct.score(xyz, rec["metal"], rec["cn"], sphere, core, rec, spec,
                                          core3)}
    except Exception as e:  # noqa: BLE001 -- one bad structure must not stop the run
        return {"refcode": rc, "score_error": f"{type(e).__name__}: {e}"[:120]}


def run_setting(meta: dict, key: str):
    """A setting of the run from its run_meta.json. A run merged by merge_rerun.py keeps its two
    sources' metadata nested (``base_meta`` / ``rerun_meta``) and has no top-level settings: the
    value is read from those, and must be the same in both -- scoring half a run against hydride
    references and half without would be silent and wrong."""
    if key in meta:
        return meta[key]
    parts = [m for m in (meta.get("base_meta"), meta.get("rerun_meta")) if isinstance(m, dict)]
    values = {json.dumps(run_setting(m, key), sort_keys=True) for m in parts}
    if len(values) > 1:
        raise SystemExit(f"the merged run's sources disagree on {key!r} ({sorted(values)}): "
                         f"pass it explicitly")
    return json.loads(values.pop()) if values else None


def _finite(xs):
    return [x for x in xs if isinstance(x, (int, float)) and not isinstance(x, bool)
            and math.isfinite(x)]


def _pct(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return round(100 * sum(bool(v) for v in vals) / len(vals), 1) if vals else None


def _summ(rows):
    built = [r for r in rows if r.get("built")]
    out = {"n": len(rows), "build_pct": round(100 * len(built) / len(rows), 1) if rows else None,
           "conn_pct": _pct(built, "connectivity_ok"), "cn_match_pct": _pct(built, "cn_match"),
           "shape_pct": _pct(built, "shape_match")}
    for m in METRICS:
        v = _finite([r.get(m) for r in built])
        out[f"{m}_n"] = len(v)
        out[f"{m}_mean"] = round(st.mean(v), 3) if v else None
        out[f"{m}_median"] = round(st.median(v), 3) if v else None
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", default="mecobi_30k", help="relative to full30k/")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--cores-d3", default="benchmark_cores_d3.json.gz")
    ap.add_argument("--hydrides", default=None,
                    help="default: the file the run was built with (run_meta.json; for a merged "
                         "run, the one both of its sources used), if any")
    ap.add_argument("--limit", type=int, default=0, help="score only the first N (smoke test)")
    ap.add_argument("--rescore", action="store_true",
                    help="ignore the cached scores (<run-dir>/_score.jsonl) and score everything "
                         "again -- needed after a change to the metrics themselves")
    cfg = ap.parse_args()

    import bench_overrides
    import hydrides
    run_dir = HERE / cfg.run_dir
    rows = {}
    for f in sorted(glob.glob(str(run_dir / "_results_shard*.jsonl"))):
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rows[r["refcode"]] = r   # last row wins (resumed runs)
    if not rows:
        raise SystemExit(f"no results in {run_dir}")
    meta = _load(run_dir / "run_meta.json") if (run_dir / "run_meta.json").exists() else {}
    hyd_file = cfg.hydrides if cfg.hydrides is not None else run_setting(meta, "hydrides")
    hyd = hydrides.load(str(BENCH / hyd_file)) if hyd_file else {}
    commits = sorted({m.get("commit", "?") for m in (meta.get("base_meta"), meta.get("rerun_meta"))
                      if isinstance(m, dict)}) or [meta.get("commit", "?")]
    print(f"{len(rows)} rows in {run_dir.name} (commit {' + '.join(commits)}, xtb "
          f"{run_setting(meta, 'xtb_version') or '?'}); hydride corrections: {hyd_file or 'none'}")

    overrides = bench_overrides.load()
    bundle = {r["refcode"]: bench_overrides.record(r, overrides)
              for r in _load(BENCH / "benchmark_bundle.json.gz")}
    spheres = _load(BENCH / "benchmark_spheres_elem.json.gz")
    cores = _load(BENCH / "benchmark_cores_elem.json.gz")
    c3p = BENCH / cfg.cores_d3
    cores3 = _load(c3p) if c3p.exists() else {}
    if not cores3:
        print(f"[warn] {c3p.name} not found: no D-MAE3")
    donors = _load(BENCH / "benchmark_donors.json")
    geo = _load(BENCH / "benchmark_geom_labels.json") \
        if (BENCH / "benchmark_geom_labels.json").exists() else {}

    cache = run_dir / "_score.jsonl"
    done = {}
    if cfg.rescore and cache.exists():
        cache.unlink()
    if cache.exists():
        for line in cache.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                done[d["refcode"]] = d
    jobs = []
    for rc, r in rows.items():
        xyz = run_dir / "structures" / f"{rc}.xyz"
        if rc in done or not r.get("built") or rc not in spheres or rc not in bundle \
                or not xyz.exists():
            continue
        jobs.append((rc, str(xyz), bundle[rc], bench_overrides.donors(rc, donors.get(rc), overrides),
                     spheres[rc], cores.get(rc), cores3.get(rc), hyd.get(rc)))
    if cfg.limit:
        jobs = jobs[:cfg.limit]
    print(f"{len(done)} already scored, {len(jobs)} to score on {cfg.workers} workers")
    t0 = time.time()
    if jobs:
        with ProcessPoolExecutor(cfg.workers) as ex, cache.open("a", encoding="utf-8") as fh:
            for i, d in enumerate(ex.map(_score_one, jobs, chunksize=8), 1):
                done[d["refcode"]] = d
                fh.write(json.dumps(d) + "\n")
                if i % 500 == 0 or i == len(jobs):
                    fh.flush()
                    print(f"  [{i}/{len(jobs)}] {time.time() - t0:.0f}s", flush=True)

    out_rows = []
    for rc, r in rows.items():
        cn = bundle.get(rc, {}).get("cn", r.get("cn"))
        d = {k: r.get(k) for k in ("refcode", "metal", "ox", "built", "build_mode",
                                   "connectivity_ok", "wall_s", "build_s")}
        d["cn"] = cn
        d["geometry_label"] = (geo.get(rc, CN_UNIQUE.get(cn, f"cn{cn}")) if cn in (2, 4, 5, 8)
                               else CN_UNIQUE.get(cn, f"cn{cn}"))
        d["error"] = (r.get("error") or done.get(rc, {}).get("score_error") or "")[:120]
        d.update({k: v for k, v in done.get(rc, {}).items() if k in COLS and k != "refcode"})
        out_rows.append(d)

    per = HERE / f"{run_dir.name}_per_structure.csv"
    with per.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    overall = _summ(out_rows)
    scols = list(overall)
    summ = HERE / f"{run_dir.name}_score_summary.csv"
    with summ.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["stratum", "value", *scols])
        w.writerow(["overall", "all", *[overall[c] for c in scols]])
        for key, name in (("cn", "CN"), ("geometry_label", "geometry"), ("metal", "metal"),
                          ("build_mode", "build_mode")):
            groups = defaultdict(list)
            for d in out_rows:
                groups[d.get(key)].append(d)
            for val in sorted(groups, key=lambda x: (x is None, str(x))):
                s = _summ(groups[val])
                w.writerow([name, val, *[s[c] for c in scols]])

    print(f"\n=== {run_dir.name}: {overall['n']} structures ===")
    print(f"  build {overall['build_pct']}%  connectivity {overall['conn_pct']}%  "
          f"CN match {overall['cn_match_pct']}%  shape match {overall['shape_pct']}%")
    for m in METRICS:
        print(f"  {m:<10} median {overall[f'{m}_median']}  mean {overall[f'{m}_mean']}  "
              f"(n={overall[f'{m}_n']})")
    print(f"-> {per}\n-> {summ}")


if __name__ == "__main__":
    main()
