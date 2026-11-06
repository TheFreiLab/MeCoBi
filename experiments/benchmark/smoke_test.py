"""Environment smoke test for the MeCoBi structural benchmark.

Builds a handful of diverse complexes end-to-end with xtb relaxation and reports
success + per-complex wall-time. Run this FIRST to confirm the install works
(rdkit, stk, torch/pydentate, and the xtb binary) and to size the full run before
launching the large sharded benchmark.

    python experiments/benchmark/smoke_test.py

Exit code 0 = all built. Non-zero = something in the toolchain is missing.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from mecobi import pipeline
from mecobi.model import Complex, Ligand, Metal

# (name, metal, oxidation state, ligand SMILES) — spans the confident donor classes
CASES = [
    ("cis-PtN2Cl2", "Pt", 2, ["N", "N", "[Cl-]", "[Cl-]"]),          # sq-planar, X + L
    ("Fe(bpy)3",    "Fe", 2, ["c1ccc(-c2ccccn2)nc1"] * 3),          # octahedral tris-chelate
    ("Ni(acac)2+2N", "Ni", 2, ["CC(=O)/C=C(\\[O-])C", "CC(=O)/C=C(\\[O-])C", "N", "N"]),
    ("Cu(NH3)4",    "Cu", 2, ["N", "N", "N", "N"]),                  # sq-planar L4
    ("Co(en)3",     "Co", 3, ["NCCN", "NCCN", "NCCN"]),             # octahedral diamine
]


def main() -> int:
    out = Path(__file__).parent / "_smoke"
    out.mkdir(exist_ok=True)
    ok = 0
    print(f"MeCoBi smoke test - building {len(CASES)} complexes with xtb relaxation\n")
    for name, metal, ox, smiles in CASES:
        cx = Complex(metal=Metal(metal, ox), name=name,
                     ligands=[Ligand(s) for s in smiles])
        t0 = time.perf_counter()
        try:
            res = pipeline.build_complex(cx, out, relax=True, xtb_timeout_s=180)
            dt = time.perf_counter() - t0
            xyz = Path(res[0].xyz_path)
            n_atoms = int(xyz.read_text().splitlines()[0])
            warns = "; ".join(res[0].warnings) if res[0].warnings else ""
            print(f"  OK   {name:14} {n_atoms:3d} atoms  {dt:5.1f}s  {warns}")
            ok += 1
        except Exception as e:  # noqa: BLE001
            dt = time.perf_counter() - t0
            print(f"  FAIL {name:14} {dt:5.1f}s  {type(e).__name__}: {e}")
    print(f"\n{ok}/{len(CASES)} built. "
          + ("Environment OK - ready for the full run." if ok == len(CASES)
             else "Some builds failed - check the install (see README)."))
    return 0 if ok == len(CASES) else 1


if __name__ == "__main__":
    sys.exit(main())
