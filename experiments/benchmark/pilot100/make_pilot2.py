"""Build pilot_2.json -- a SECOND 100-complex validation set, independent of pilot_1.

Same coordination-number distribution as pilot_1, scorable (has ground-truth donors + an
extracted crystal sphere), non-lanthanide (the f-block relaxes poorly under GFN2-xTB), and
disjoint from pilot_1. Reproducible: fixed seed, sorted pools.

    python make_pilot2.py            # -> pilot_2.json (+ prints the coverage)
"""
from __future__ import annotations

import gzip
import json
import random
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent   # pilot100/: pilot_100.json in, pilot_2.json out
BENCH = HERE.parent                      # benchmark root: frozen bundle/donors/spheres
# 15 lanthanides (La-Lu). Sc/Y stay -- they are group-3 d-block, not lanthanides.
LANTHANIDES = {"La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy",
               "Ho", "Er", "Tm", "Yb", "Lu"}


def _load_set(path):
    if str(path).endswith(".gz"):
        return set(json.loads(gzip.open(path, "rt", encoding="utf-8").read()))
    return set(json.loads(Path(path).read_text()))


def main():
    bundle = {r["refcode"]: r
              for r in json.loads(gzip.open(BENCH / "benchmark_bundle.json.gz", "rt").read())}
    pilot1 = set(json.loads((HERE / "pilot_100.json").read_text()))
    donors = _load_set(BENCH / "benchmark_donors.json")
    spheres = _load_set(BENCH / "benchmark_spheres.json.gz")

    cn_dist = Counter(bundle[rc]["cn"] for rc in pilot1)
    eligible: dict[int, list[str]] = {}
    for rc, r in bundle.items():
        if (rc in donors and rc in spheres and rc not in pilot1
                and r["metal"] not in LANTHANIDES):
            eligible.setdefault(r["cn"], []).append(rc)

    rng = random.Random(2)  # pilot_2 seed (pilot_1 used a different one)
    pilot2: list[str] = []
    for cn, need in sorted(cn_dist.items()):
        pool = sorted(eligible.get(cn, []))
        if len(pool) < need:
            print(f"WARNING: CN{cn} wants {need} but only {len(pool)} eligible; taking all.")
        pilot2 += rng.sample(pool, min(need, len(pool)))
    pilot2 = sorted(pilot2)

    assert not (set(pilot2) & pilot1), "pilot_2 overlaps pilot_1"
    (HERE / "pilot_2.json").write_text(json.dumps(pilot2))
    print(f"pilot_2: {len(pilot2)} complexes -> {HERE / 'pilot_2.json'}")
    print("CN dist :", dict(sorted(Counter(bundle[rc]['cn'] for rc in pilot2).items())),
          "(pilot_1:", dict(sorted(cn_dist.items())), ")")
    print("metals  :", dict(Counter(bundle[rc]['metal'] for rc in pilot2).most_common(12)))
    print("overlap with pilot_1:", len(set(pilot2) & pilot1),
          "| lanthanides:", sum(bundle[rc]["metal"] in LANTHANIDES for rc in pilot2))


if __name__ == "__main__":
    main()
