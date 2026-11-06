"""Add an sp-carbon donor class (``C_sp``: carbonyl, cyanide, isocyanide) to MeCoBi's M-L distance
reference, src/mecobi/data/ml_reference.json.

The table is keyed by donor ELEMENT, so its ``C`` bins average carbonyl carbons with Cp / arene /
alkyl / aryl carbons: Fe(0) CN5 "C" = 2.03 A, while a real Fe-CO is ~1.77 A. The xtb distance
restraint then holds every M-CO / M-CN ~0.13 A too long (pilot-100: +0.13 A mean over 14
complexes, up to +0.31 A; MetalloGen, unrestrained, -0.03 A).

Mined from the benchmark's own crystal spheres (benchmark_spheres_elem.json.gz), using only the
complexes where EVERY carbon donor is an sp carbon (C bonded to exactly one atom, N or O, by a
triple bond in the ligand SMILES), so each crystal M-C distance is unambiguously an sp-carbon one
-- no atom matching needed. Written at the table's three levels (metal|OS|C_sp|CN,
metal|OS|C_sp, metal|C_sp) in its own format; optimize._ml_target falls back to the ``C`` bins
where no ``C_sp`` bin has enough samples.

    python dataprep/mine_sp_carbon_reference.py            # updates ml_reference.json in place
"""
from __future__ import annotations

import gzip
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from rdkit import Chem, RDLogger

BENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCH))

import bench_overrides  # noqa: E402

RDLogger.DisableLog("rdApp.*")
TABLE = BENCH.parents[1] / "src" / "mecobi" / "data" / "ml_reference.json"
KEY = "C_sp"


def is_sp_carbon(mol, idx: int) -> bool:
    a = mol.GetAtomWithIdx(idx)
    if a.GetSymbol() != "C" or a.GetDegree() != 1:
        return False
    b = a.GetBonds()[0]
    return b.GetBondType() == Chem.BondType.TRIPLE and b.GetOtherAtom(a).GetSymbol() in ("N", "O")


def _stat(v):
    n = len(v)
    sd = st.stdev(v) if n > 1 else None
    return {"mean": round(st.fmean(v), 4), "n": n, "sd": None if sd is None else round(sd, 4),
            "sem": None if sd is None else round(sd / n ** 0.5, 4)}


def main():
    bundle = json.load(gzip.open(BENCH / "benchmark_bundle.json.gz", "rt"))
    spheres = json.load(gzip.open(BENCH / "benchmark_spheres_elem.json.gz", "rt"))
    donors = json.loads((BENCH / "benchmark_donors.json").read_text())
    overrides = bench_overrides.load()
    bins = {"metal_os_donor_cn": defaultdict(list), "metal_os_donor": defaultdict(list),
            "metal_donor": defaultdict(list)}
    used = 0
    for r in bundle:
        rc = r["refcode"]
        s = spheres.get(rc)
        row = bench_overrides.donors(rc, donors.get(rc), overrides)
        if not s or not row or s.get("by_element") is False:
            continue
        r = bench_overrides.record(r, overrides)
        n_sp = n_c = 0
        for smi, dd in zip(r["ligands"], row):
            mol = Chem.MolFromSmiles(smi)
            if mol is None:
                n_c = -1
                break
            for d in dd:
                if mol.GetAtomWithIdx(d).GetSymbol() == "C":
                    n_c += 1
                    n_sp += is_sp_carbon(mol, d)
        if n_c <= 0 or n_sp != n_c:
            continue                      # no C donor, or a non-sp C donor present
        m = np.asarray(s["metal_xyz"], float)
        ds = [float(np.linalg.norm(np.asarray(p, float) - m))
              for e, p in zip(s["donor_elements"], s["donors"]) if e == "C"]
        if len(ds) != n_c or max(ds) > 2.6:
            continue                      # sphere does not match the declaration
        used += 1
        metal, ox, cn = r["metal"], r["ox"], r["cn"]
        bins["metal_os_donor_cn"][f"{metal}|{ox}|{KEY}|{cn}"] += ds
        bins["metal_os_donor"][f"{metal}|{ox}|{KEY}"] += ds
        bins["metal_donor"][f"{metal}|{KEY}"] += ds
    table = json.loads(TABLE.read_text(encoding="utf-8"))
    for level, d in bins.items():
        sub = table.setdefault(level, {})
        for k in [k for k in sub if f"|{KEY}" in k]:
            del sub[k]                    # re-mined from scratch every run
        for k, v in sorted(d.items()):
            sub[k] = _stat(v)
    TABLE.write_text(json.dumps(table, indent=1), encoding="utf-8")
    md = bins["metal_donor"]
    print(f"{used} complexes with only sp-carbon C donors; "
          f"{sum(len(v) for v in md.values())} M-C distances; {len(md)} metals -> {TABLE}")
    for k, v in sorted(md.items(), key=lambda t: -len(t[1]))[:12]:
        c = table["metal_donor"].get(k.replace(KEY, "C"), {})
        print(f"  {k:10} n={len(v):5} mean {st.fmean(v):.3f}   (table C: {c.get('mean')})")


if __name__ == "__main__":
    main()
