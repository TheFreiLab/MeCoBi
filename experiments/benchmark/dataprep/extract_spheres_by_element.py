"""Re-extract the crystal coordination spheres choosing the donors BY ELEMENT from the bundle's
declared ``donor_elements`` (cif_geometry.coordination_sphere_by_elements), instead of "the cn
nearest non-H atoms" (dataprep/extract_spheres.py).

Why: the bundle's donor elements were corrected after the spheres were frozen (the eta-carbocycle
re-ship, ec66783) and the nearest-atom rule never takes an H, so 11% of the frozen spheres hold a
different element multiset than the bundle declares -- a backbone C ~3 A away standing in for a
lost I/Cl/H donor (KUFZOD, ICIHAF, NAPMUO, LAZKIG). Each new sphere also records
``n_unbonded``: declared donors still beyond the metal-donor bond criterion (donor_map.ml_bonded)
-- a long weak contact or an atom the CIF lacks near the metal; flag, not dropped.

The depth-2 cores for c-kmRMSD (extract_cores.depth2_core) are re-extracted the same way.

    python dataprep/extract_spheres_by_element.py --workers 8
        # -> benchmark_spheres_elem.json.gz + benchmark_cores_elem.json.gz
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCH))

import numpy as np  # noqa: E402

import bench_overrides  # noqa: E402
from cif_geometry import SYM2NAME, coordination_sphere_by_elements  # noqa: E402
from extract_cores import _DEFAULT_CIF_ROOT, depth2_core, is_placeholder  # noqa: E402


def _one(args):
    rec, cif_root = args
    import donor_map

    rc, metal = rec["refcode"], rec["metal"]
    folder = SYM2NAME.get(metal)
    cifs = glob.glob(f"{cif_root}/{folder}/{rc}.*.cif") if folder else []
    if not cifs or is_placeholder(cifs[0]):
        return rc, None, None, "missing"
    text = Path(cifs[0]).read_text(errors="ignore")
    try:
        sph = coordination_sphere_by_elements(text, metal, rec["donor_elements"])
    except Exception:  # noqa: BLE001
        sph = None
    try:
        core = depth2_core(text, metal, rec["cn"], rec["donor_elements"])
    except Exception:  # noqa: BLE001
        core = None
    if not sph:
        return rc, None, core, "fail"
    m = np.asarray(sph[0], float)
    unb = sum(1 for e, p in zip(sph[2], sph[1]) if e != "H" and not donor_map.ml_bonded(
        metal, e, float(np.linalg.norm(np.asarray(p, float) - m))))
    return rc, {"metal_xyz": sph[0], "donors": sph[1], "donor_elements": sph[2],
                "cn_contacts": len(sph[1]), "n_unbonded": unb}, core, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cif-root", default=None)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=str(BENCH / "benchmark_spheres_elem.json.gz"))
    ap.add_argument("--cores-out", default=str(BENCH / "benchmark_cores_elem.json.gz"),
                    help="depth-2 crystal cores (ckmrmsd), donors chosen the same way")
    cfg = ap.parse_args()
    cif_root = cfg.cif_root or os.environ.get("MECOBI_CIF_ROOT") or _DEFAULT_CIF_ROOT
    overrides = bench_overrides.load()
    with gzip.open(BENCH / "benchmark_bundle.json.gz", "rt", encoding="utf-8") as fh:
        recs = [bench_overrides.record(r, overrides) for r in json.load(fh)]
    if cfg.limit:
        recs = recs[:cfg.limit]
    out, cores, stat = {}, {}, {"ok": 0, "missing": 0, "fail": 0}
    with ProcessPoolExecutor(cfg.workers) as ex:
        for k, (rc, sph, core, st) in enumerate(
                ex.map(_one, [(r, cif_root) for r in recs], chunksize=64), 1):
            stat[st] += 1
            if sph:
                out[rc] = sph
            if core:
                cores[rc] = core
            if k % 5000 == 0:
                print(f"  {k}/{len(recs)} {stat}", flush=True)
    # a declared element the CIF lacks near the metal (mostly an unlocated H): keep the old
    # nearest-atom sphere / core for that refcode, flagged, so no refcode loses its reference
    n_fb = 0
    for name, new in (("benchmark_spheres.json.gz", out), ("benchmark_cores.json.gz", cores)):
        with gzip.open(BENCH / name, "rt", encoding="utf-8") as fh:
            old = json.load(fh)
        for rc, v in old.items():
            if rc not in new:
                new[rc] = {**v, "by_element": False}
                n_fb += new is out
    print(f"fallback to the nearest-atom sphere: {n_fb}")
    with gzip.open(cfg.out, "wt", encoding="utf-8") as fh:
        json.dump(out, fh)
    with gzip.open(cfg.cores_out, "wt", encoding="utf-8") as fh:
        json.dump(cores, fh)
    print(f"depth-2 cores: {len(cores)} -> {cfg.cores_out}")
    unb = sum(1 for s in out.values() if s["n_unbonded"])
    print(f"spheres: {len(out)}  {stat}  with an unbonded declared donor: {unb} -> {cfg.out}")


if __name__ == "__main__":
    main()
