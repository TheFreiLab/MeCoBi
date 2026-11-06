"""Build benchmark_hydrides.json -- the located-hydride corrections hydrides.py layers over the
frozen bundle (see that module for the file format and how run.py / the scorers apply it).

For every complex whose CIF locates an M-H (the ``located`` rows of dataprep/hydride_scan.csv,
re-detected here from the CIF so the stored positions and the scan can never disagree):

  1. the M->H vectors are read from the crystal (same symmetry expansion + frame as the spheres);
  2. the input is corrected -- one ``[H-]`` ligand per hydride, OS and CN raised by as many;
  3. the geometry + site-map target is RE-READ from the crystal with the hydride as a donor
     (enrich_bundle_geometry.target_for, build-checked with a relax=False assembly), so the
     builder puts the H on the site it occupies in the crystal;
  4. the complex is classed: clean (1-2 H, corrected site CN <= 6), high_cn (1-2 H, site CN >= 7),
     polyhydride (>= 3 H: positions unreliable, eta2-H2 ambiguity), h2_mixed (an H-H contact
     next to the hydride) or short_mh (an M-H below 1.2 A: not a credible position). Only
     ``clean`` is applied unless asked (run.py --hydride-classes).

Complexes without a donor row (--donors) get no target: the correction still fixes the input,
and the build falls back to MeCoBi's heuristic geometry/isomer. Parallel; needs mecobi (no xtb).

    python dataprep/build_hydride_corrections.py           # whole bundle -> benchmark_hydrides.json
    python dataprep/build_hydride_corrections.py --refcodes pilot100/pilot_100.json --out _h.json
"""
from __future__ import annotations

import argparse
import csv
import glob
import gzip
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]   # benchmark root
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_overrides  # noqa: E402
import hydrides  # noqa: E402
from cif_geometry import SYM2NAME  # noqa: E402
from scan_hydrides import located  # noqa: E402


MH_MIN = 1.2   # A: a "located" H closer than this is not a credible hydride position


def classify(n_h: int, site_cn: int, n_h2: int, mh) -> str:
    if n_h2:
        return "h2_mixed"
    if min(mh) < MH_MIN:
        return "short_mh"
    if n_h >= 3:
        return "polyhydride"
    return "high_cn" if site_cn >= 7 else "clean"


def correct_one(args):
    r, donor_row, cif_path, build_check = args
    rc = r["refcode"]
    try:
        text = open(cif_path, errors="ignore").read()
        res = located(text, r["metal"])
        if not res or not res[0]:
            return rc, None
        vecs, dists, n_h2 = res
        n = len(vecs)
        h = {"n_h": n, "class": "", "ox": r["ox"] + n, "cn": r["cn"] + n,
             "mh": [round(x, 3) for x in dists],
             "h_rel": [[round(float(x), 4) for x in v] for v in vecs]}
        site_cn = h["cn"]
        if donor_row is not None:
            import enrich_bundle_geometry as EB   # lazy: pulls in mecobi + rdkit
            t = EB.target_for(hydrides.record(r, h), text, hydrides.donors(donor_row, h),
                              build_check=build_check, h_rel=h["h_rel"])
            h["target"] = {"refcode": rc, "metal": r["metal"], "cn": h["cn"], **t}
            site_cn = t.get("site_cn") or site_cn
        h["class"] = classify(n, site_cn, n_h2, dists)
        return rc, h
    except Exception as e:  # noqa: BLE001 -- one bad CIF must not stop the run
        return rc, {"error": f"{type(e).__name__}: {e}"[:120]}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cif-root", default=str(BENCH.parents[1] / "CCDC"))
    ap.add_argument("--scan", default=str(Path(__file__).resolve().parent / "hydride_scan.csv"),
                    help="scan_hydrides.py CSV: only its 'located' rows are processed "
                         "(absent -> every complex is checked)")
    ap.add_argument("--donors", default="benchmark_donors.json")
    ap.add_argument("--refcodes", default=None,
                    help="JSON list to restrict to (bench-root relative)")
    ap.add_argument("--no-build-check", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--out", default=str(BENCH / "benchmark_hydrides.json"))
    cfg = ap.parse_args()

    bundle = json.load(gzip.open(BENCH / "benchmark_bundle.json.gz", "rt"))
    keep = None
    if cfg.refcodes:
        keep = set(json.load(open(BENCH / cfg.refcodes)))
    elif os.path.exists(cfg.scan):
        keep = {r["refcode"] for r in csv.DictReader(open(cfg.scan, encoding="utf-8"))
                if r["hydride"] == "located"}
    donors = json.loads((BENCH / cfg.donors).read_text())
    overrides = bench_overrides.load()
    jobs = []
    for r in bundle:
        rc = r["refcode"]
        if keep is not None and rc not in keep:
            continue
        hits = glob.glob(os.path.join(cfg.cif_root, SYM2NAME.get(r["metal"], "?"), f"{rc}.*.cif"))
        if not hits:
            continue
        jobs.append((bench_overrides.record(r, overrides),
                     bench_overrides.donors(rc, donors.get(rc), overrides),
                     hits[0], not cfg.no_build_check))

    t0 = time.time()
    out, errors = {}, {}
    with ProcessPoolExecutor(max_workers=cfg.workers) as ex:
        for k, (rc, h) in enumerate(ex.map(correct_one, jobs, chunksize=8), 1):
            if h and "error" in h:
                errors[rc] = h["error"]
            elif h:
                out[rc] = h
            if k % 200 == 0:
                print(f"  {k}/{len(jobs)}  {time.time() - t0:.0f}s", flush=True)

    with open(cfg.out, "w", encoding="utf-8", newline="\n") as fh:   # one refcode per line
        fh.write("{\n" + ",\n".join(f'{json.dumps(rc)}: {json.dumps(out[rc])}'
                                    for rc in sorted(out)) + "\n}\n")

    print(f"\n{len(jobs)} checked, {len(out)} with a located hydride ({time.time() - t0:.0f}s)")
    print("class:", dict(Counter(h["class"] for h in out.values())))
    tg = Counter(h["target"].get("status", "?") if "target" in h else "no_donor_row"
                 for h in out.values())
    print("target:", dict(tg))
    clean = [h for h in out.values() if h["class"] == "clean"]
    print("clean -> geometry:", dict(Counter(h["target"].get("geometry") for h in clean
                                             if "target" in h)))
    if errors:
        print(f"errors ({len(errors)}):", list(errors.items())[:5])
    print(f"-> {cfg.out}")


if __name__ == "__main__":
    main()
