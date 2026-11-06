"""Write the tmQM and MeCoBi geometries of the 10,198 complexes as .xyz plus a manifest for run_xtb_sp.py.

    python prepare_tmqm_sp.py
    python ../../metallipo_ml/xtb_sp/run_xtb_sp.py --manifest manifest_tmqm.csv --structures structures \
        --out results --workers 6 --phases vac

One row per (refcode, geometry): complex_id = <REFCODE>__tmqm or <REFCODE>__mecobi. Charge from table.csv;
spin from the electron count (tmQM is closed shell, so uhf = 0 is expected everywhere).
"""
import argparse
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit.Chem import GetPeriodicTable

HERE = Path(__file__).resolve().parent
TM = HERE.parent
PT = GetPeriodicTable()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--charged-centred", action="store_true",
                    help="only the charged complexes, translated so that the centre of nuclear charge is at the "
                         "origin (xtb gives the dipole of an ion about the origin of the coordinates)")
    a = ap.parse_args()
    G = pickle.load(open(TM / "geometries.pkl", "rb"))
    inc = pd.read_csv(TM / "inclusion.csv")
    df = pd.read_csv(TM / "table.csv")
    df = df[df.refcode.isin(set(inc[inc.include].refcode))].reset_index(drop=True)
    if a.charged_centred:
        df = df[df.charge != 0].reset_index(drop=True)
    sdir = HERE / ("structures_charged_centred" if a.charged_centred else "structures")
    sdir.mkdir(exist_ok=True)
    rows, odd = [], 0
    for r in df.itertuples():
        for arm in ("tmqm", "mecobi"):
            g = G[arm][r.refcode]
            sym, xyz = g["sym"], g["xyz"].astype(float)
            if a.charged_centred:
                z = np.array([PT.GetAtomicNumber(s) for s in sym], float)
                xyz = xyz - (z[:, None] * xyz).sum(0) / z.sum()
            n_el = sum(PT.GetAtomicNumber(s) for s in sym) - int(r.charge)
            uhf = n_el % 2
            odd += uhf
            cid = f"{r.refcode}__{arm}"
            lines = [str(len(sym)), cid] + [f"{s} {x:.6f} {y:.6f} {z:.6f}" for s, (x, y, z) in zip(sym, xyz)]
            (sdir / f"{cid}.xyz").write_text("\n".join(lines) + "\n")
            rows.append({"complex_id": cid, "xyz": f"{cid}.xyz", "refcode": r.refcode, "arm": arm,
                         "metal": r.metal, "charge": int(r.charge), "uhf": uhf,
                         "metal_index": sym.index(r.metal), "n_atoms": len(sym)})
    man = pd.DataFrame(rows)
    man.to_csv(HERE / ("manifest_tmqm_charged_centred.csv" if a.charged_centred else "manifest_tmqm.csv"), index=False)
    print(f"{len(df)} complexes, {len(man)} structures -> {sdir}; odd electron count: {odd}")


if __name__ == "__main__":
    main()
