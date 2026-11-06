"""tmQM: the table of Figure 7 (and Table S18) from the out-of-fold predictions, with absolute and relative errors.

    python tmqm_table.py                   # random split (Figure 7)
    python tmqm_table.py --split ligand    # split by largest ligand (Table S18)

Reads the out-of-fold predictions written by table5_block1.py, xtb_sp/analyze_tmqm_xtb.py and
xtb_sp/isomer_average_xtb.py for the same split (ISO_DIR as for isomer_average_xtb.py) and writes
results/table_tmqm{_split}.csv and .txt. For every model and property:
  MAE    mean absolute error against the DFT value of tmQM
  rMAE   MAE relative to the mean DFT value of the complexes evaluated (%)
  R2     coefficient of determination
The per-complex relative error |pred - DFT| / DFT is not used: for the dipole moment it diverges for the complexes
with a DFT value near zero (most of them centrosymmetric). Also given: the MAE of the dipole moment for the complexes
with a DFT dipole moment below 1 D.
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

HERE = Path(__file__).resolve().parent
SPLIT = sys.argv[sys.argv.index("--split") + 1] if "--split" in sys.argv else "random"
TAG = "" if SPLIT == "ligand" else f"_{SPLIT}"
ISO_DIR = Path(os.environ.get("ISO_DIR", HERE / "isomers"))
T = ("dipole_D", "gap_eV")


def metrics(y, p):
    e = y - p
    return {"MAE": np.abs(e).mean(), "rMAE_%": 100 * np.abs(e).mean() / y.mean(),
            "R2": 1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum()}


def main():
    tab = pd.read_csv(HERE / "table.csv").set_index("refcode")
    xtb = pd.read_csv(HERE / "xtb_sp" / "results" / f"oof_tmqm_xtb{TAG}.csv").set_index("refcode")
    blk = pd.read_csv(HERE / "results_isomer" / f"oof_block1{TAG}.csv").set_index("refcode").loc[xtb.index]
    sys.path.insert(0, str(HERE / "xtb_sp"))
    from analyze_tmqm_xtb import calibrated, load  # noqa: E402

    df, x = load()
    pos = pd.Series(np.arange(len(df)), index=df.refcode).loc[xtb.index].to_numpy()
    fold = pd.read_csv(HERE / "folds.csv").set_index("refcode").loc[xtb.index, SPLIT].to_numpy()
    rows = []

    def add(block, model, inputs, y, p, n_low=None):
        for t in T:
            r = {"block": block, "model": model, "input": inputs, "property": t, "n": len(y[t]), **metrics(y[t], p[t])}
            if t == "dipole_D":
                low = y[t] < 1
                r["MAE_below_1D"], r["n_below_1D"] = np.abs(y[t][low] - p[t][low]).mean(), int(low.sum())
            rows.append(r)

    y = {t: tab.loc[xtb.index, t].to_numpy(float) for t in T}
    b1 = f"{len(xtb):,} complexes"
    add(b1, "LightGBM", "2D features (negative control)", y, {t: blk[f"{t}|2D features"].to_numpy() for t in T})
    add(b1, "LightGBM", "2D + isomer label", y, {t: blk[f"{t}|2D + isomer label"].to_numpy() for t in T})
    add(b1, "Linear fit", "xTB of the crystal-isomer structure alone", y,
        {t: calibrated(x["mecobi"][t].to_numpy(float)[pos], y[t], fold) for t in T})
    add(b1, "LightGBM", "2D + xTB of the crystal-isomer structure", y,
        {t: xtb[f"{t}|floor + xTB(MeCoBi)"].to_numpy() for t in T})
    add(b1, "LightGBM", "2D + xTB of the tmQM geometry (positive control)", y,
        {t: xtb[f"{t}|floor + xTB(tmQM)"].to_numpy() for t in T})

    iso = pd.read_csv(ISO_DIR / "results_xtb" / f"oof_metrics_isomer_average{TAG}.csv").set_index("refcode")
    y2 = {t: tab.loc[iso.index, t].to_numpy(float) for t in T}
    b2 = f"Structures built from the SMILES alone ({len(iso):,} complexes)"
    add(b2, "LightGBM", "2D features (negative control)", y2, {t: iso[f"{t}|floor"].to_numpy() for t in T})
    add(b2, "LightGBM", "2D + xTB of the lowest-energy SMILES-only isomer", y2,
        {t: iso[f"{t}|lowest"].to_numpy() for t in T})
    add(b2, "LightGBM", "2D + xTB, Boltzmann average over the SMILES-only isomers", y2,
        {t: iso[f"{t}|boltzmann"].to_numpy() for t in T})
    add(b2, "LightGBM", "2D + xTB of the crystal-isomer structure", y2,
        {t: iso[f"{t}|crystal isomer"].to_numpy() for t in T})
    for lab, m in (("one isomer", iso.n_isomers == 1), ("more than one isomer", iso.n_isomers > 1)):
        ys = {t: y2[t][m.to_numpy()] for t in T}
        for v, name in (("floor", "2D features"), ("lowest", "2D + xTB, lowest-energy isomer"),
                        ("crystal isomer", "2D + xTB, crystal isomer")):
            add(f"SMILES alone, {lab} ({int(m.sum()):,} complexes)", "LightGBM", name, ys,
                {t: iso.loc[m, f"{t}|{v}"].to_numpy() for t in T})

    out = pd.DataFrame(rows)
    out.to_csv(HERE / "results" / f"table_tmqm{TAG}.csv", index=False)
    wide = out.pivot_table(index=["block", "input"], columns="property", values=["MAE", "rMAE_%", "R2"], sort=False)
    low = out[out.property == "dipole_D"].set_index(["block", "input"])[["MAE_below_1D", "n_below_1D"]]
    txt = (f"split: {SPLIT}; mean DFT values: dipole {y['dipole_D'].mean():.2f} D, gap {y['gap_eV'].mean():.3f} eV "
           f"({len(xtb):,} complexes)\n" + wide.round(3).to_string() + "\n\nDipole, DFT below 1 D\n" + low.round(3).to_string())
    (HERE / "results" / f"table_tmqm{TAG}.txt").write_text(txt + "\n", encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
