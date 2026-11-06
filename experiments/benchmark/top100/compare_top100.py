"""Score + compare the top-100-largest reruns (run_top100.sh) against the original full-30k run.

Every configuration -- the original run ("baseline") and each top100/runs/<config>/ -- is scored
the SAME way from its relaxed .xyz: run.score (poly_cshm, dmat, bond, shape match) against one
sphere file, plus depth-2 c-kmRMSD against benchmark_cores. built / connectivity_ok / error / wall_s
come from each run's JSONL. Prints a summary over all 100 and a PAIRED one (only refcodes every
config built, so the medians compare like with like), and writes:

    top100/compare_per_structure.csv   one row per (refcode, config)
    top100/compare_summary.csv         one row per config (all + paired)

    python top100/compare_top100.py                                  # from experiments/benchmark/
    python top100/compare_top100.py --baseline-dir full30k/mecobi_30k --configs fallback repoly

Without the baseline JSONLs (e.g. only the 68 .xyz copied locally), pass --baseline-dir to the
folder holding structures/ and the built/connectivity flags are read from
full30k_per_structure.csv instead.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import re
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
sys.path.insert(0, str(BENCH))
import run as R  # noqa: E402
from ckmrmsd import build_core_from_xyz, ckmrmsd  # noqa: E402

METRICS = ["ckmrmsd", "poly_cshm", "bond_rmsd", "dmat_rmsd"]


def _jsonl_rows(run_dir: Path) -> dict:
    rows = {}
    for f in sorted(glob.glob(str(run_dir / "_results_shard*.jsonl"))):
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rows[r["refcode"]] = r
    return rows


def _csv_rows(path: Path) -> dict:
    out = {}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        out[r["refcode"]] = {"refcode": r["refcode"], "built": r["built"] == "True",
                             "connectivity_ok": {"True": True, "False": False}.get(r["connectivity_ok"]),
                             "error": r["error"] or None}
    return out


def relax_level(xyz: str) -> "str | None":
    """Which geometry the build actually kept, from the .xyz comment line ('energy: <Eh>' when
    xtb wrote it): GFN2 totals run ~-1..-3 Eh/atom, GFN-FF ~-0.1..-0.3 Eh/atom; no energy = the
    assembled geometry (xtb timed out or failed before producing one). On large complexes a
    short --xtb-timeout leaves most builds at GFN-FF/assembled, where --uhf never acts."""
    lines = xyz.split("\n")
    try:
        n = int(lines[0])
    except (ValueError, IndexError):
        return None
    m = re.search(r"energy:\s*(-?[\d.]+)", lines[1] if len(lines) > 1 else "")
    if not m:
        return "assembled"
    return "GFN2" if float(m.group(1)) / n < -0.5 else "GFN-FF"


def _score(rc, meta, xyz_path: Path, spheres, cores):
    """Uniform re-score of one relaxed build; {} if there's no structure."""
    if not xyz_path.exists() or rc not in spheres:
        return {}
    xyz = xyz_path.read_text(encoding="utf-8")
    out = {"relax": relax_level(xyz)}
    try:
        sc = R.score(xyz, meta["metal"], meta["cn"], spheres[rc]) or {}
        out.update({k: sc.get(k) for k in ("shape_match", "poly_cshm", "dmat_rmsd", "bond_rmsd")})
    except Exception:  # noqa: BLE001
        pass
    if (cc := cores.get(rc)) is not None:
        try:
            bc = build_core_from_xyz(xyz, meta["metal"], meta["cn"])
            out["ckmrmsd"] = round(ckmrmsd(cc, bc)[0], 4) if bc else None
        except Exception:  # noqa: BLE001
            out["ckmrmsd"] = None
    if isinstance(out.get("poly_cshm"), (int, float)):
        p = out["poly_cshm"]
        out["poly_cshm"] = 100.0 if (not math.isfinite(p) or p > 100) else p  # full30k clamp
    return out


def _summ(rows):
    n = len(rows)
    built = [r for r in rows if r.get("built")]
    sc = [r for r in built if r.get("shape_match") is not None]
    s = {"n": n,
         "built_pct": round(100 * len(built) / n, 1) if n else None,
         "conn_pct": round(100 * sum(bool(r.get("connectivity_ok")) for r in built) / len(built), 1)
         if built else None,
         "shape_pct": round(100 * sum(bool(r["shape_match"]) for r in sc) / len(sc), 1) if sc else None}
    for m in METRICS:
        v = [r[m] for r in built if isinstance(r.get(m), (int, float)) and math.isfinite(r[m])]
        s[f"{m}_median"] = round(st.median(v), 3) if v else None
        s[f"{m}_mean"] = round(st.mean(v), 3) if v else None
    w = [r["wall_s"] for r in rows if isinstance(r.get("wall_s"), (int, float))]
    s["wall_s_median"] = round(st.median(w), 1) if w else None
    for lv, k in (("GFN2", "n_gfn2"), ("GFN-FF", "n_gfnff"), ("assembled", "n_assembled")):
        s[k] = sum(1 for r in built if r.get("relax") == lv)
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refcodes", default=str(HERE / "top100_largest.json"))
    ap.add_argument("--baseline-dir", default=str(BENCH / "full30k" / "mecobi_30k"),
                    help="original run dir (JSONL shards + structures/)")
    ap.add_argument("--runs-dir", default=str(HERE / "runs"))
    ap.add_argument("--configs", nargs="*", default=None,
                    help="configs under --runs-dir to include (default: every subfolder)")
    ap.add_argument("--spheres", default=None,
                    help="default: benchmark_spheres_fixed.json.gz if present, else the frozen one")
    cfg = ap.parse_args()

    rcs = json.loads(Path(cfg.refcodes).read_text())
    bundle = {r["refcode"]: r for r in R._load_bundle("benchmark_bundle")}
    sp = Path(cfg.spheres) if cfg.spheres else next(
        p for p in (BENCH / "benchmark_spheres_elem.json.gz", BENCH / "benchmark_spheres_fixed.json.gz",
                  BENCH / "benchmark_spheres.json.gz")
        if p.exists())
    spheres = R._load_json(sp)
    cores = R._load_json(BENCH / "benchmark_cores_elem.json.gz")
    print(f"scoring against {sp.name}")

    runs = {}
    base = Path(cfg.baseline_dir).expanduser()
    brows = _jsonl_rows(base)
    if not brows:
        brows = _csv_rows(BENCH / "full30k" / "full30k_per_structure.csv")
        print(f"(no JSONL in {base}; baseline built/connectivity from full30k_per_structure.csv)")
    runs["baseline"] = (brows, base / "structures")
    rdir = Path(cfg.runs_dir)
    names = cfg.configs
    if names is None:
        names = sorted(p.name for p in rdir.iterdir() if p.is_dir()) if rdir.exists() else []
    for c in names:
        runs[c] = (_jsonl_rows(rdir / c), rdir / c / "structures")

    table = []
    for c, (rows, sdir) in runs.items():
        for rc in rcs:
            src = rows.get(rc)
            meta = bundle[rc]
            r = {"refcode": rc, "config": c, "metal": meta["metal"], "cn": meta["cn"],
                 "ran": src is not None,
                 "built": bool(src and src.get("built")),
                 "connectivity_ok": src.get("connectivity_ok") if src else None,
                 "error": (src or {}).get("error"), "wall_s": (src or {}).get("wall_s")}
            if r["built"]:
                r.update(_score(rc, meta, sdir / f"{rc}.xyz", spheres, cores))
            table.append(r)
        n_ran = sum(1 for r in table if r["config"] == c and r["ran"])
        print(f"  {c:<10} {n_ran}/{len(rcs)} refcodes have a result")

    keys = ["refcode", "config", "metal", "cn", "ran", "built", "connectivity_ok", "shape_match",
            *METRICS, "relax", "wall_s", "error"]
    with (HERE / "compare_per_structure.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader(); w.writerows(table)

    by = {c: [r for r in table if r["config"] == c] for c in runs}
    paired = set.intersection(*({r["refcode"] for r in rs if r["built"]} for rs in by.values()))
    summ = []
    for scope, filt in (("all", None), ("paired", paired)):
        for c, rs in by.items():
            sel = [r for r in rs if filt is None or r["refcode"] in filt]
            summ.append({"scope": scope, "config": c, **_summ(sel)})

    # per-structure c-km change vs baseline (only where both built)
    base_ckm = {r["refcode"]: r.get("ckmrmsd") for r in by["baseline"] if r["built"]}
    for s in summ:
        if s["scope"] != "all" or s["config"] == "baseline":
            continue
        better = worse = 0
        for r in by[s["config"]]:
            b, n = base_ckm.get(r["refcode"]), r.get("ckmrmsd") if r["built"] else None
            if isinstance(b, (int, float)) and isinstance(n, (int, float)):
                better += n < b - 0.1
                worse += n > b + 0.1
        newly = sum(1 for r in by[s["config"]] if r["built"] and r["refcode"] not in base_ckm)
        s.update({"ckm_better_vs_base": better, "ckm_worse_vs_base": worse, "newly_built": newly})

    cols = ["scope", "config", "n", "built_pct", "conn_pct", "shape_pct",
            *[f"{m}_{k}" for m in METRICS for k in ("median", "mean")], "wall_s_median",
            "n_gfn2", "n_gfnff", "n_assembled",
            "newly_built", "ckm_better_vs_base", "ckm_worse_vs_base"]
    with (HERE / "compare_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(summ)

    short = ["config", "n", "built_pct", "conn_pct", "shape_pct", "ckmrmsd_median", "poly_cshm_median",
             "bond_rmsd_median", "dmat_rmsd_median", "wall_s_median", "n_gfn2", "n_gfnff",
             "n_assembled"]
    for scope in ("all", "paired"):
        print(f"\n=== {scope} ({'all ' + str(len(rcs)) if scope == 'all' else str(len(paired)) + ' built by every config'}) ===")
        print("  ".join(f"{k.replace('_median', ''):>10}" for k in short))
        for s in summ:
            if s["scope"] == scope:
                print("  ".join(f"{str(s.get(k) if s.get(k) is not None else '-'):>10}" for k in short))
    print("\nvs baseline (c-km change > 0.1 A, where both built):")
    for s in summ:
        if "newly_built" in s:
            print(f"  {s['config']:<10} newly built {s['newly_built']:>3}   better {s['ckm_better_vs_base']:>3}"
                  f"   worse {s['ckm_worse_vs_base']:>3}")
    print(f"\n-> {HERE / 'compare_per_structure.csv'}\n-> {HERE / 'compare_summary.csv'}")


if __name__ == "__main__":
    main()
