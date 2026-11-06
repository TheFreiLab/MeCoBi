"""Metal-donor bond cut-offs consistent with the benchmark's own CN definition.

donor_map.ml_bonded decides whether an atom is bonded to the metal (to MEASURE a build's CN).
The CSD convention r(M) + r(X) + 0.4 A (Cordero radii) is too short for the long, weak bonds
the crystal reference itself counts: 6% of the 35.7k crystal spheres have a donor beyond it,
mostly Pb/Hg/Bi/Tl-O/N, Ag/Cd-O and Jahn-Teller Cu-O. So each (metal, donor element) pair gets
the 99th percentile of its crystal M-X distances when that is longer (pairs with >= 20
observations; others keep the covalent rule). Carbon (and H) donors are NOT lengthened: their
tail is extraction error, not weak bonding -- when the crystal extraction loses a donor, the
next-nearest atom, usually a backbone C ~3 A away, stands in for it (Ru-C p99 would be 3.37 A,
ICIHAF/NAPMUO). Written to benchmark_ml_cutoffs.json.

    python dataprep/build_ml_cutoffs.py
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BENCH))

import donor_map  # noqa: E402

MIN_OBS = 20
QUANTILE = 99


def main():
    spheres = json.load(gzip.open(BENCH / "benchmark_spheres_elem.json.gz", "rt"))
    bundle = {r["refcode"]: r for r in json.load(gzip.open(BENCH / "benchmark_bundle.json.gz",
                                                           "rt"))}
    dist = defaultdict(list)
    for rc, s in spheres.items():
        if rc not in bundle:
            continue
        metal = bundle[rc]["metal"]
        m = np.asarray(s["metal_xyz"], float)
        els = s.get("donor_elements") or bundle[rc]["donor_elements"]
        for e, p in zip(els, s["donors"]):
            dist[f"{metal}|{e}"].append(float(np.linalg.norm(np.asarray(p, float) - m)))
    out = {}
    for key, ds in sorted(dist.items()):
        metal, el = key.split("|")
        if el in ("C", "H"):
            continue
        cov = donor_map._r(metal) + donor_map._r(el) + donor_map.ML_SLACK
        if len(ds) >= MIN_OBS:
            q = float(np.percentile(ds, QUANTILE))
            if q > cov:
                out[key] = round(q, 3)
    path = BENCH / "benchmark_ml_cutoffs.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(out)} (metal, donor) pairs lengthened beyond r+r+{donor_map.ML_SLACK} -> {path}")


if __name__ == "__main__":
    main()
