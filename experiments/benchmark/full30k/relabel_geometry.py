"""Re-aggregate full30k_summary.csv from full30k_per_structure.csv with the corrected geometry
labels (rebuilt CN-4/5/8 cache from the fixed crystal spheres). The run shards are not local, so we
cannot re-run full30k_metrics.py; instead we reproduce its summary aggregation exactly from the
per-structure CSV -- the per-structure metric VALUES are unchanged, only which geometry stratum each
CN-4/5/8 complex falls into. A self-check first reproduces the CURRENT summary from the CSV's own
geometry column to prove the aggregation is faithful before the new labels are applied.
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import os
import statistics as st
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent   # full30k/: per-structure + summary CSVs
BENCH = HERE.parent                      # benchmark root: frozen bundle + geometry-label cache
# Folder holding the Figure 2 copies of the summary/per-structure CSVs (env MECOBI_FIG2_DIR);
# defaults to this folder, i.e. the canonical CSVs only.
FIG2 = Path(os.environ.get("MECOBI_FIG2_DIR", HERE))
CONT = ["poly_cshm", "dmat_rmsd", "bond_rmsd", "ckmrmsd"]  # ckm included: the run used --ckmrmsd
CN_UNIQUE = {2: "linear", 3: "trigonal_planar", 6: "octahedral",
             7: "pentagonal_bipyramidal", 9: "tricapped_trigonal_prism"}


def _load(p):
    p = str(p)
    if p.endswith(".gz"):
        return json.load(gzip.open(p, "rt", encoding="utf-8"))
    return json.load(open(p, encoding="utf-8"))


def _f(x):
    try:
        v = float(x)
        return v
    except (TypeError, ValueError):
        return None


def _b(x):
    s = str(x).strip().lower()
    return True if s in ("true", "1") else False if s in ("false", "0") else None


def _finite(xs):
    return [x for x in xs if x is not None and math.isfinite(x)]


def _clamp_cshm(m, x):
    if x is None:
        return None
    if m.endswith("cshm") and (not math.isfinite(x) or x > 100.0):
        return 100.0
    return x


def _summ(rows):
    n = len(rows)
    built = [r for r in rows if r["built"]]
    usable = [r for r in rows if r.get("sphere_ok", True)]
    scored = [r for r in usable if r["shape_match"] is not None]
    out = {"n": n,
           "n_clean": len(usable),
           "build_pct": round(100 * len(built) / n, 1) if n else None,
           "conn_pct": round(100 * sum(bool(r["connectivity_ok"]) for r in built) / len(built), 1) if built else None,
           "shape_pct": round(100 * sum(bool(r["shape_match"]) for r in scored) / len(scored), 1) if scored else None}
    for m in CONT:
        vals = _finite([_clamp_cshm(m, r[m]) for r in usable])
        out[f"{m}_mean"] = round(st.mean(vals), 3) if vals else None
        out[f"{m}_median"] = round(st.median(vals), 3) if vals else None
    return out


COLS = (["stratum", "value", "n", "n_clean", "build_pct", "conn_pct", "shape_pct"]
        + [f"{m}_{k}" for m in CONT for k in ("mean", "median")])


def build_summary(rows, geom_key):
    lines = [COLS]
    overall = _summ(rows)
    lines.append(["overall", "all"] + [overall[c] for c in COLS[2:]])
    for key, kname in (("cn", "CN"), (geom_key, "geometry"), ("metal", "metal")):
        groups = defaultdict(list)
        for r in rows:
            groups[r.get(key)].append(r)
        for val in sorted(groups, key=lambda x: (x is None, x)):
            s = _summ(groups[val])
            lines.append([kname, val] + [s[c] for c in COLS[2:]])
    return lines


def fmt(v):
    return "" if v is None else str(v)


def main():
    cache = _load(BENCH / "benchmark_geom_labels.json")
    bundle = {r["refcode"]: r for r in _load(BENCH / "benchmark_bundle.json.gz")}

    def geom_label(rc):
        cn = bundle.get(rc, {}).get("cn")
        if cn in (2, 4, 5, 8):
            return cache.get(rc, CN_UNIQUE.get(cn, f"cn{cn}"))
        return CN_UNIQUE.get(cn, f"cn{cn}")

    ps_path = HERE / "full30k_per_structure.csv"
    with open(ps_path, encoding="utf-8") as fh:
        raw = list(csv.DictReader(fh))

    rows = []
    for r in raw:
        rows.append({
            "refcode": r["refcode"], "metal": r["metal"], "cn": int(r["cn"]) if r["cn"] else None,
            "geometry_csv": r["geometry"],
            "built": _b(r["built"]), "connectivity_ok": _b(r["connectivity_ok"]),
            "sphere_ok": _b(r["sphere_ok"]) if r["sphere_ok"] != "" else True,
            "shape_match": _b(r["shape_match"]),
            "poly_cshm": _f(r["poly_cshm"]), "dmat_rmsd": _f(r["dmat_rmsd"]),
            "bond_rmsd": _f(r["bond_rmsd"]), "ckmrmsd": _f(r["ckmrmsd"]),
            "error": r.get("error", ""), "error_class": r.get("error_class", ""),
        })

    # --- self-check: reproduce the CURRENT summary from the CSV's own geometry column ---
    check = build_summary(rows, "geometry_csv")
    cur_path = FIG2 / "full30k_summary.csv"
    cur = list(csv.reader(open(cur_path, encoding="utf-8")))
    check_str = [[fmt(x) for x in row] for row in check]
    ok = check_str == cur
    print(f"self-check: re-aggregated CURRENT summary == committed full30k_summary.csv ? {ok}")
    if not ok:
        # show first divergence to diagnose
        for i, (a, b) in enumerate(zip(check_str, cur)):
            if a != b:
                print(f"  first diff at row {i}:\n    mine: {a}\n    file: {b}")
                break
        if len(check_str) != len(cur):
            print(f"  row count differs: mine={len(check_str)} file={len(cur)}")
        raise SystemExit("aggregation does not reproduce current summary; aborting before writing.")

    # --- apply corrected labels ---
    changed = 0
    for r in rows:
        newlbl = geom_label(r["refcode"])
        if newlbl != r["geometry_csv"]:
            changed += 1
        r["geometry_new"] = newlbl
    print(f"rows re-labelled vs CSV: {changed}")

    # rewrite per_structure.csv geometry column (backup first)
    import shutil
    shutil.copy(ps_path, HERE / "full30k_per_structure.csv.pre_spherefix.bak")
    with open(ps_path, encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    gi = header.index("geometry")
    with open(HERE / "full30k_per_structure.csv.pre_spherefix.bak", encoding="utf-8") as fh:
        allrows = list(csv.reader(fh))
    by_rc_newlbl = {r["refcode"]: r["geometry_new"] for r in rows}
    rc_i = header.index("refcode")
    for row in allrows[1:]:
        row[gi] = by_rc_newlbl.get(row[rc_i], row[gi])
    with open(ps_path, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(allrows)

    # also update the Figure_2 per-structure copy so both stay in sync
    fig2_ps = FIG2 / "full30k_per_structure.csv"
    if fig2_ps.exists():
        shutil.copy(ps_path, fig2_ps)

    # rebuild summary with corrected labels -> write to benchmark/ (canonical) AND Figure_2
    newsum = build_summary(rows, "geometry_new")
    for out in (HERE / "full30k_summary.csv", cur_path):
        with open(out, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            for row in newsum:
                w.writerow([fmt(x) for x in row])

    # report the geometry rows before/after
    print("\nnew by-geometry rows:")
    for row in newsum:
        if row[0] == "geometry":
            print("  " + ",".join(fmt(x) for x in row[:9]))


if __name__ == "__main__":
    main()
