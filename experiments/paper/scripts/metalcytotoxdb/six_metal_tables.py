"""Six-metal results of the paper from the out-of-fold predictions in ../../metalcytotoxdb/oof.

    python six_metal_tables.py [METALCYTOTOXDB_DIR]

Every model is scored on the 21,554 measurements of the DimeNet++ file (structure passed the filter). Writes, in
METALCYTOTOXDB_DIR (default ../../metalcytotoxdb):
  multimetal_per_metal_retrained.csv  ROC-AUC per metal, 2D models retrained on those measurements (Table S12)
  multimetal_per_metal.csv            the same with the 2D models trained on all 22,358 measurements
  per_metal_difference.csv            DimeNet++ - LightGBM (retrained) per metal, 95% t interval over the folds
  family_roc_auc.csv                  rows of the six-metal set (set = multimetal) recomputed; ruthenium rows kept
and prints the rank-mean consensus of LightGBM and DimeNet++ (and of LightGBM and the MLP).
ROC-AUC per metal: mean over the ten folds; P: two-sided paired t-test over the folds. Family ROC-AUC: pooled over
the folds, as in Figure S2.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "metalcytotoxdb"
METALS = ["Re", "Os", "Rh", "Ir", "Au", "Ru", "All"]
FAMILY = {"DMSO / azole (NAMI-A, KP1019 type)": "DMSO / azole"}

oof = {k: pd.read_csv(D / "oof" / f"six_metals_{k}.csv")
       for k in ("dimenet", "lightgbm", "mlp", "lightgbm_all_rows", "mlp_all_rows")}
rows = set(oof["dimenet"]["row_id"])
oof = {k: v[v["row_id"].isin(rows)] for k, v in oof.items()}
metal = pd.read_csv(D / "rows_six_metals.csv").set_index("row_id")["Metal"]


def per_fold(df, g):
    if g != "All":
        df = df[df["row_id"].map(metal) == g]
    return pd.Series({k: roc_auc_score(x["y"], x["prob"]) for k, x in df.groupby("fold") if x["y"].nunique() == 2})


def table(lgbm, mlp):
    out = []
    for g in METALS:
        sub = oof["dimenet"] if g == "All" else oof["dimenet"][oof["dimenet"]["row_id"].map(metal) == g]
        r = {"Metal": g, "n": len(sub), "complexes": sub["complex_id"].nunique()}
        f = {"LightGBM": per_fold(oof[lgbm], g), "MLP": per_fold(oof[mlp], g), "DimeNet++": per_fold(oof["dimenet"], g)}
        for m, v in f.items():
            r.update({m: round(v.mean(), 4), f"{m}_sem": round(v.std() / np.sqrt(len(v)), 4),
                      f"{m}_sd": round(v.std(), 4)})
        r["P_dime_vs_lgbm"] = round(stats.ttest_rel(f["DimeNet++"], f["LightGBM"]).pvalue, 4)
        r["P_dime_vs_mlp"] = round(stats.ttest_rel(f["DimeNet++"], f["MLP"]).pvalue, 4)
        out.append(r)
    return pd.DataFrame(out)


table("lightgbm", "mlp").to_csv(D / "multimetal_per_metal_retrained.csv", index=False)
table("lightgbm_all_rows", "mlp_all_rows").to_csv(D / "multimetal_per_metal.csv", index=False)

diff = []
for g in METALS:
    a, b = per_fold(oof["dimenet"], g), per_fold(oof["lightgbm"], g)
    d = a - b
    h = stats.t.ppf(0.975, len(d) - 1) * d.std() / np.sqrt(len(d))
    sub = oof["dimenet"] if g == "All" else oof["dimenet"][oof["dimenet"]["row_id"].map(metal) == g]
    diff.append({"metal": g, "measurements": len(sub), "complexes": sub["complex_id"].nunique(), "folds": len(d),
                 "lightgbm": b.mean(), "dimenet": a.mean(), "diff": d.mean(), "lo": d.mean() - h, "hi": d.mean() + h,
                 "p": stats.ttest_rel(a, b).pvalue})
pd.DataFrame(diff).sort_values("metal", key=lambda s: s.map({"All": "zz"}).fillna(s)).to_csv(
    D / "per_metal_difference.csv", index=False)

fam = pd.read_csv(D / "families_six_metals.csv").set_index("row_id")["family"].replace(FAMILY)
fr = []
for f, x in oof["dimenet"].assign(family=oof["dimenet"]["row_id"].map(fam)).groupby("family"):
    l2 = oof["lightgbm"][oof["lightgbm"]["row_id"].isin(x["row_id"])]
    fr.append({"family": f, "measurements": len(x), "complexes": x["complex_id"].nunique(),
               "toxic": round(x["y"].mean(), 3), "auc_lightgbm": round(roc_auc_score(l2["y"], l2["prob"]), 3),
               "auc_dimenet": round(roc_auc_score(x["y"], x["prob"]), 3), "set": "multimetal"})
old = pd.read_csv(D / "family_roc_auc.csv")
order = list(old.loc[old["set"] == "multimetal", "family"])
new = pd.DataFrame(fr).set_index("family").loc[order].reset_index()
pd.concat([old[old["set"] != "multimetal"], new], ignore_index=True).to_csv(D / "family_roc_auc.csv", index=False)

for other in ("lightgbm", "mlp"):
    m = oof[other].merge(oof["dimenet" if other == "lightgbm" else "lightgbm"], on=["row_id", "y", "fold"])
    c, base = [], []
    for _, g in m.groupby("fold"):
        c.append(roc_auc_score(g["y"], (g["prob_x"].rank(pct=True) + g["prob_y"].rank(pct=True)) / 2))
        base.append(roc_auc_score(g["y"], g["prob_x" if other == "lightgbm" else "prob_y"]))
    c, base = np.array(c), np.array(base)
    name = "LightGBM + DimeNet++" if other == "lightgbm" else "LightGBM + MLP"
    print(f"six metals, rank mean {name}: {c.mean():.3f} against LightGBM {base.mean():.3f} "
          f"(delta {c.mean() - base.mean():+.3f}, P = {stats.ttest_rel(c, base).pvalue:.2f}, "
          f"higher in {(c > base).sum()} of {len(c)} folds)")
