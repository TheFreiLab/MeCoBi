"""First block of Table 5: LightGBM on the 2D features and on 2D + isomer label, mean prediction of three seeds.

    python table5_block1.py                 -> results_isomer/table5_block1.txt (+ oof_block1.csv)
    python table5_block1.py --split random  -> results_isomer/table5_block1_random.txt (+ oof_block1_random.csv)

Same models as lgbm_seeds.py (floor and floor + isomer label, ligand split, folds.csv, seeds 0-2, the complexes of
exclude_overlap.txt left out of training and evaluation), without the SOAP sets; the isomer label is rebuilt for the
current table with isomer_control.build_label_table. The complexes whose GFN2-xTB single point failed on either geometry
are left out as well, so that every row of Table 5 is on the same 10,175 complexes.
"""
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

import baseline_2d as b
from isomer_control import build_label_table

HERE = Path(__file__).resolve().parent
SPLIT = sys.argv[sys.argv.index("--split") + 1] if "--split" in sys.argv else "ligand"
TAG = "" if SPLIT == "ligand" else f"_{SPLIT}"
inc = pd.read_csv(HERE / "inclusion.csv")
df = pd.read_csv(HERE / "table.csv")
df = df[df.refcode.isin(set(inc[inc.include].refcode))].reset_index(drop=True)
XR = pd.read_pickle(HERE / "results_soap" / "floor.pkl")
L = build_label_table(df)
L.to_pickle(HERE / "results_isomer" / "isomer_features.pkl")
feat = L[[c for c in L if c != "label_source"]]
sets = {"2D features": XR, "2D + isomer label": pd.concat([XR, feat], axis=1)}
folds = pd.read_csv(HERE / "folds.csv").set_index("refcode").loc[df.refcode, SPLIT].to_numpy()
drop = df.refcode.isin(set((HERE / "exclude_overlap.txt").read_text().split())).to_numpy()
sys.path.insert(0, str(HERE / "xtb_sp"))
from analyze_tmqm_xtb import load as load_xtb  # noqa: E402

_, x = load_xtb()
xtb_fail = ~(np.isfinite(x["tmqm"].gap_eV.to_numpy(float)) & np.isfinite(x["mecobi"].gap_eV.to_numpy(float)))
overlap, drop = drop, drop | xtb_fail
res, lines = {"refcode": df.refcode}, [f"split: {SPLIT} (folds.csv)", f"{len(df)} complexes, {int((~drop).sum())} evaluated (exclude_overlap: "
                                       f"{int(overlap.sum())}, xTB failed: {int((xtb_fail & ~overlap).sum())}); "
                                       f"isomer label source: {L.label_source.value_counts().to_dict()}"]
for t in ("dipole_D", "gap_eV"):
    y = df[t].to_numpy(float)
    for name, X in sets.items():
        P = []
        for seed in (0, 1, 2):
            p = np.zeros(len(y))
            for k in range(10):
                te = folds == k
                p[te] = lgb.LGBMRegressor(**{**b.PARAMS, "random_state": seed}).fit(
                    X[~te & ~drop], y[~te & ~drop]).predict(X[te])
            P.append(p)
        e = np.mean(P, axis=0)
        res[f"{t}|{name}"] = e
        per = [np.abs(y - p)[~drop].mean() for p in P]
        lines.append(f"{t:<9} {name:<20} MAE of the 3-seed mean {np.abs(y - e)[~drop].mean():.3f}   "
                     f"(single seeds {np.mean(per):.3f} +/- {np.std(per):.3f})")
        print(lines[-1], flush=True)
pd.DataFrame(res).to_csv(HERE / "results_isomer" / f"oof_block1{TAG}.csv", index=False)
(HERE / "results_isomer" / f"table5_block1{TAG}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
