"""Four-way generation timing: MeCoBi (heuristic) vs MeCoBi (oracle) vs Architector vs
molSimplify.

Joins the per-complex JSONL each runner writes and reports build success rate + per-structure
wall time (median / quartiles / total) per series, plus the median wall time on the subset every
series built. Writes a per-complex CSV. Pure stdlib.

Sources (each searched in its per-tool folder first -- from run.py/*.py --out-dir -- then the
benchmark root, so it works whether or not you organised into subfolders):
  MeCoBi heuristic | MeCoBi oracle : _multigeom_shard*of*.jsonl  (run_multigeom.py; ONE file gives
                                     both series -- row["heuristic"]/["oracle"] built flags and
                                     heuristic_time_s/oracle_time_s)
  Architector                       : _arch_results_shard*of*.jsonl  (arch_run.py; wall_s)
  molSimplify                       : _molsim_results_shard*of*.jsonl (molsim_run.py; wall_s)

A series appears only if its files are present. molSimplify UFF wall time is not like-for-like
with the xtb series (its `ff` is printed). The oracle wall time includes assembling ALL
candidates for the pre-opt selection (that is the oracle's real selection cost).

    python pilot100/compare_timing.py [--refcodes pilot_100.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics as st
from pathlib import Path

HERE = Path(__file__).parent

# (key, label, [glob candidates: folder first, then root], built_fn, time_fn)
TOOLS = [
    ("mecobi_heuristic", "MeCoBi heuristic",
     ["mecobi/_multigeom_shard*of*.jsonl", "../legacy/_multigeom_shard*of*.jsonl"],
     lambda r: r.get("heuristic") is not None, lambda r: r.get("heuristic_time_s")),
    ("mecobi_oracle", "MeCoBi oracle",
     ["mecobi/_multigeom_shard*of*.jsonl", "../legacy/_multigeom_shard*of*.jsonl"],
     lambda r: r.get("oracle") is not None, lambda r: r.get("oracle_time_s")),
    ("architector", "Architector",
     ["architector/_arch_results_shard*of*.jsonl"],
     lambda r: bool(r.get("built")), lambda r: r.get("wall_s")),
    ("molsim", "molSimplify",
     ["molsimplify/molsimplify_det/_molsim_results_shard*of*.jsonl",
      "molsimplify/_molsim_results_shard*of*.jsonl"],
     lambda r: bool(r.get("built")), lambda r: r.get("wall_s")),
]


def _load(globs, time_fn) -> dict[str, dict]:
    """Merge shard JSONLs (folder + root) into {refcode: row}. A row that carries a time for
    this series wins over one that doesn't (drops stale untimed rows from older runs)."""
    rows: dict[str, dict] = {}
    files: list[Path] = []
    for g in globs:
        files += sorted(HERE.glob(g))
    for f in files:
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            prev = rows.get(r["refcode"])
            if prev is None or time_fn(r) is not None or time_fn(prev) is None:
                rows[r["refcode"]] = r
    return rows


def _summary(vals) -> "dict | None":
    vals = [v for v in vals if isinstance(v, (int, float))]
    if not vals:
        return None
    q = st.quantiles(vals, n=4, method="inclusive") if len(vals) > 1 else [vals[0]] * 3
    return {"n": len(vals), "median": st.median(vals), "mean": st.fmean(vals),
            "p25": q[0], "p75": q[2], "max": max(vals), "total": sum(vals)}


def _fmt(s) -> str:
    if not s:
        return "no timed builds"
    return (f"n={s['n']:>3}  median={s['median']:7.1f}s  mean={s['mean']:7.1f}s  "
            f"p25={s['p25']:7.1f}s  p75={s['p75']:7.1f}s  max={s['max']:7.1f}s  "
            f"total={s['total']/60:6.1f} min")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="compare_timing.csv")
    ap.add_argument("--refcodes", default=None,
                     help="JSON list (e.g. pilot_100.json) to restrict the comparison to.")
    cfg = ap.parse_args()

    data = {}  # key -> {refcode: row}
    for key, _, globs, _, time_fn in TOOLS:
        data[key] = _load(globs, time_fn)
    series = [(k, lbl, bf, tf) for k, lbl, _, bf, tf in TOOLS if data[k]]
    if not series:
        raise SystemExit("No result JSONLs found. Run run_multigeom.py / arch_run.py / molsim_run.py.")

    if cfg.refcodes:
        keep = set(json.loads((HERE / cfg.refcodes if not Path(cfg.refcodes).is_absolute()
                               else Path(cfg.refcodes)).read_text(encoding="utf-8")))
        data = {k: {rc: r for rc, r in v.items() if rc in keep} for k, v in data.items()}

    built = {k: {rc for rc, r in data[k].items() if bf(r)} for k, _, bf, _ in series}
    all_rc = sorted(set().union(*(set(data[k]) for k, *_ in series)))
    common = set.intersection(*(built[k] for k, *_ in series)) if series else set()

    # per-complex CSV
    out_csv = Path(cfg.csv if Path(cfg.csv).is_absolute() else HERE / cfg.csv)
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        header = ["refcode", "metal", "cn"]
        for k, _, _, _ in series:
            header += [f"{k}_built", f"{k}_time_s"]
        w.writerow(header)
        for rc in all_rc:
            meta = next((data[k][rc] for k, *_ in series if rc in data[k]), {})
            vals = [rc, meta.get("metal"), meta.get("cn")]
            for k, _, bf, tf in series:
                r = data[k].get(rc)
                vals += [bool(r and bf(r)), tf(r) if r else None]
            w.writerow(vals)

    # ---- console report ----
    print("=" * 82)
    print("generation timing:  " + "  vs  ".join(lbl for _, lbl, _, _ in series))
    print("=" * 82)
    print("complexes attempted : " + "   ".join(f"{lbl} {len(data[k])}" for k, lbl, _, _ in series))
    print("build success       : " + "   ".join(
        f"{lbl} {len(built[k])}/{len(data[k])} ({100*len(built[k])/max(len(data[k]),1):.0f}%)"
        for k, lbl, _, _ in series))
    print()
    print("per-structure wall time (built only):")
    for k, lbl, _, tf in series:
        s = _summary([tf(data[k][rc]) for rc in built[k]])
        tag = ""
        if k == "molsim":
            ffs = {r.get("ff") for r in data[k].values() if r.get("ff")}
            tag = f"   [ff={'/'.join(sorted(ffs))}]" if ffs else ""
        print(f"  {lbl:18}: {_fmt(s)}{tag}")
    print()
    print(f"built by ALL {len(series)} series: {len(common)} complexes")
    if common:
        for k, lbl, _, tf in series:
            med = st.median([tf(data[k][rc]) for rc in common
                             if isinstance(tf(data[k][rc]), (int, float))])
            print(f"  {lbl:18} median wall on common set: {med:7.1f}s")
    print("\n(oracle wall includes assembling all candidates for the pre-opt selection.)")
    print(f"per-complex CSV -> {out_csv}")


if __name__ == "__main__":
    main()
