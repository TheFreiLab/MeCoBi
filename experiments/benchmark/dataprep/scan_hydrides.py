"""Scan the benchmark bundle for hydrido complexes the CSD-mined inputs lost.

The mined ligand SMILES carry NO hydrides (0 of 35 956 entries), so a hydrido complex enters the
benchmark with its CN too low and -- because the oxidation state comes from a charge balance that
never saw the H- -- its OS one unit too low per hydride (Ni(II)-H mines as Ni(I), Rh(III)-H as
Rh(II)). This scan flags such complexes two independent ways and writes one CSV row per refcode:

  A. located hydride -- the CIF has an H within --mh (2.0 A) of the metal that is bonded to nothing
     else (no non-metal atom within the covalent-radius bond cutoff, never tighter than 1.25 A:
     hydrides.metal_only_h, so an Si-H / P-H / B-H near the metal is a ligand H, not a hydride).
     Bridging M-H-M counts; an H whose only short contact is another H is recorded separately as
     a possible eta2-H2. Many X-ray structures do not locate M-H, so A has false negatives but
     essentially no false positives.
  B. odd oxidation state --
       B1  a p-block centre with an odd valence-electron count (Ge(III), Sn(III), Ga(II), ...):
           a main-group radical, almost always a data error;
       B2  a rare OS ONE BELOW a common one (LOW_RARE_OS: Ni(I), Rh(II), Ru(I), Pt(I), ...) --
           exactly what dropping a hydride from the charge balance produces. Upper-side rare
           states (Ni(III), Fe(IV), Mo(V)) are NOT flagged: a lost hydride lowers the OS, never
           raises it (full bundle: 0% of those carry a located M-H, vs 38% of the low side).
  plus, for comparison, the current core heuristic (spin.possible_missing_hydrides, 18e rule).

Reads CIFs from --cif-root/<ElementName>/<REFCODE>.*.cif (the local CCDC tree). Parallel,
pure geometry (no xtb/torch).

    python dataprep/scan_hydrides.py                          # whole bundle -> dataprep/hydride_scan.csv
    python dataprep/scan_hydrides.py --refcodes pilot100/pilot_100.json --out pilot100_hydrides.csv
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

import numpy as np

BENCH = Path(__file__).resolve().parents[1]   # benchmark root
sys.path.insert(0, str(BENCH))
from cif_geometry import SYM2NAME, _cell_and_atoms  # noqa: E402
from hydrides import MH_MAX, metal_only_h  # noqa: E402

# Rare transition-metal oxidation states sitting ONE BELOW a common state: what a charge balance
# that dropped a hydride produces (true OS - 1). Real but unusual; common states are not listed.
LOW_RARE_OS = {
    "Ni": {1}, "Pd": {1}, "Pt": {1}, "Rh": {0, 2}, "Ir": {0, 2}, "Co": {0}, "Ru": {1},
    "Os": {1}, "Fe": {1}, "Mn": {0}, "Re": {2}, "Cu": {0}, "Ag": {0}, "Au": {0},
    "Zn": {0, 1}, "Cd": {0, 1}, "Hg": {0}, "Mo": {1}, "W": {1, 3}, "Cr": {1}, "V": {1},
    "Tc": {2},
}
P_BLOCK_GROUP = {  # valence electrons of the neutral atom
    "B": 3, "Al": 3, "Ga": 3, "In": 3, "Tl": 3, "Si": 4, "Ge": 4, "Sn": 4, "Pb": 4,
    "As": 5, "Sb": 5, "Bi": 5, "Se": 6, "Te": 6,
}


def _cif(root, rc, metal):
    hits = glob.glob(os.path.join(root, SYM2NAME.get(metal, "?"), f"{rc}.*.cif"))
    return hits[0] if hits else None


def located(cif_text, metal, mh_max=MH_MAX):
    """``(M->H vectors, M-H distances, n_h2)`` of the located hydrides, or None if unparseable."""
    M, atoms, symops = _cell_and_atoms(cif_text)
    if M is None:
        return None
    elems, fracs = atoms
    mi = [i for i, e in enumerate(elems) if e == metal]
    if not mi:
        return None
    trans = [np.array([i, j, k]) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)]
    X = np.vstack([(fracs @ R.T + t + tr) @ M.T for R, t in symops for tr in trans])
    E = np.array(list(elems) * (len(X) // len(elems)))
    mc = fracs[mi[0]] @ M.T
    near = np.linalg.norm(X - mc, axis=1) < mh_max + 2.5      # all the bond test can reach
    X, E = X[near], E[near]
    idx, n_h2 = metal_only_h(E, X, mc, metals=set(SYM2NAME), mh_max=mh_max)
    vecs = [X[j] - mc for j in idx]
    return vecs, [float(np.linalg.norm(v)) for v in vecs], n_h2


def scan_one(args):
    rc, metal, ox, cn, root, mh_max = args
    out = {"refcode": rc, "metal": metal, "ox": ox, "cn": cn, "cif": False,
           "n_mh": 0, "mh_dists": "", "n_h2": 0}
    path = _cif(root, rc, metal)
    if not path:
        return out
    try:
        res = located(open(path, errors="ignore").read(), metal, mh_max)
        if res is None:
            return out
        _, dists, n_h2 = res
        out.update({"cif": True, "n_mh": len(dists), "n_h2": n_h2,
                    "mh_dists": " ".join(f"{x:.2f}" for x in sorted(dists))})
    except Exception as e:  # noqa: BLE001 -- a malformed CIF is recorded, not fatal
        out["error"] = f"{type(e).__name__}: {e}"[:80]
    return out


def os_flags(metal, ox):
    b1 = metal in P_BLOCK_GROUP and (P_BLOCK_GROUP[metal] - ox) % 2 == 1
    b2 = ox in LOW_RARE_OS.get(metal, set())
    return b1, b2


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cif-root", default=str(BENCH.parents[1] / "CCDC"))
    ap.add_argument("--refcodes", default=None, help="JSON list to restrict to (bench-root relative)")
    ap.add_argument("--mh", type=float, default=MH_MAX, help="max M-H distance (A)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "hydride_scan.csv"))
    cfg = ap.parse_args()

    from mecobi import spin
    bundle = json.load(gzip.open(BENCH / "benchmark_bundle.json.gz", "rt"))
    if cfg.refcodes:
        keep = set(json.load(open(BENCH / cfg.refcodes)))
        bundle = [r for r in bundle if r["refcode"] in keep]
    jobs = [(r["refcode"], r["metal"], r["ox"], r["cn"], cfg.cif_root, cfg.mh)
            for r in bundle]
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=cfg.workers) as ex:
        for k, res in enumerate(ex.map(scan_one, jobs, chunksize=64), 1):
            rows.append(res)
            if k % 2000 == 0:
                print(f"  {k}/{len(jobs)}  {time.time() - t0:.0f}s", flush=True)
    for r in rows:
        r["os_pblock_odd"], r["os_rare"] = os_flags(r["metal"], r["ox"])
        try:
            r["heuristic_18e"] = spin.possible_missing_hydrides(r["metal"], r["ox"], r["cn"])
        except Exception:  # noqa: BLE001
            r["heuristic_18e"] = 0

    for r in rows:   # certain (located) > suspected (odd OS, H not located) > none
        r["hydride"] = ("located" if r["n_mh"] else
                        "suspected" if (r["os_pblock_odd"] or r["os_rare"]) else "")
    cols = ["refcode", "metal", "ox", "cn", "cif", "hydride", "n_mh", "mh_dists", "n_h2",
            "os_pblock_odd", "os_rare", "heuristic_18e", "error"]
    with open(cfg.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    cif = [r for r in rows if r["cif"]]
    A = [r for r in cif if r["n_mh"]]
    B1 = [r for r in rows if r["os_pblock_odd"]]
    B2 = [r for r in rows if r["os_rare"]]
    H = [r for r in rows if r["heuristic_18e"]]
    print(f"\n{n} complexes, CIF parsed for {len(cif)} ({time.time() - t0:.0f}s)")
    print(f"A  located M-H:            {len(A):5d} ({100 * len(A) / max(1, len(cif)):.1f}% of parsed)"
          f"  by #H {dict(sorted(Counter(r['n_mh'] for r in A).items()))}")
    print(f"   possible eta2-H2 only:   {sum(1 for r in cif if r['n_h2'] and not r['n_mh']):5d}")
    print(f"B1 odd-electron p-block:   {len(B1):5d}   of which located M-H: {sum(1 for r in B1 if r['n_mh'])}")
    print(f"B2 low-side rare TM OS:    {len(B2):5d}   of which located M-H: {sum(1 for r in B2 if r['n_mh'])}")
    print(f"18e heuristic flag:        {len(H):5d}   of which located M-H: {sum(1 for r in H if r['n_mh'])}")
    print(f"located M-H caught by B1/B2: {sum(1 for r in A if r['os_pblock_odd'] or r['os_rare'])}/{len(A)}"
          f"   by 18e heuristic: {sum(1 for r in A if r['heuristic_18e'])}/{len(A)}")
    sus = [r for r in rows if r["hydride"] == "suspected"]
    print(f"suspected (odd OS, no located H): {len(sus)}  -> located + suspected = "
          f"{len(A) + len(sus)} ({100 * (len(A) + len(sus)) / n:.1f}% of the bundle)")
    print("located M-H by metal:", Counter(r["metal"] for r in A).most_common(12))
    print(f"-> {cfg.out}")


if __name__ == "__main__":
    main()
