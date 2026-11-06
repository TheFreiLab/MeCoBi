"""Manifest of the IrCpSB structures for the xTB single points (run_xtb_sp.py of metallipo_ml).

    python make_manifest.py [--structures <IrCpSB_gen>/ML/rerun/structures] [--out manifest.csv]

Every <stem>_OPT.xyz under gen0/ and gen1+2/: [Ir(Cp)(SB)Cl]+, charge +1, closed shell (Ir(III), d6).
Writes manifest.csv (complex_id = structure_stem, xyz relative to the structures folder).
"""
import argparse
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OLD = Path(r"<DATA_ROOT>\York\Data\IrCpSB_gen\ML\rerun\structures")

ap = argparse.ArgumentParser()
ap.add_argument("--structures", default=str(OLD))
ap.add_argument("--out", default=str(HERE / "manifest.csv"))
a = ap.parse_args()
root = Path(a.structures)
rows = []
for f in sorted(root.glob("*/*_OPT.xyz")):
    lines = f.read_text().splitlines()
    sym = [ln.split()[0] for ln in lines[2:2 + int(lines[0])]]
    rows.append({"complex_id": f.name.replace("_OPT.xyz", ""), "xyz": f"{f.parent.name}/{f.name}", "metal": "Ir",
                 "charge": 1, "uhf": 0, "metal_index": sym.index("Ir"), "n_atoms": len(sym)})
pd.DataFrame(rows).to_csv(a.out, index=False)
print(f"{len(rows)} structures from {root} -> {a.out}")
