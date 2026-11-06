"""Structural family of each complex from its ligand SMILES, and how LightGBM (2D) and DimeNet++ (3D) do on each
family (out-of-fold predictions).

    python ru_classes.py [ru|multimetal]   -> {set}_classes.csv (per measurement), {set}_classes_summary.txt

ru: the 10,824 ruthenium measurements; multimetal: the 21,554 measurements of the six metals with a DimeNet++
structure (LightGBM retrained on the same measurements and folds).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from scipy.stats import rankdata, spearmanr
from sklearn.metrics import roc_auc_score

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
D = HERE.parent / "Figure_5" / "data_fix6e0590a"
SET = sys.argv[1] if len(sys.argv) > 1 else "ru"
META = Path(r"<BIOMETALDB_ML>\data\processed\ru_article.csv") if SET == "ru" else D / "multimetal.csv"
TAG = "" if SET == "ru" else "_multimetal"
NN = [Chem.MolFromSmarts(s) for s in ("[n;r6]:[c;r6]-[c;r6]:[n;r6]", "[n;r6]:[c;r6]:[c;r6]:[n;r6]")]
CP = Chem.MolFromSmarts("[c-,C-;r5]")
DMSO = Chem.MolFromSmarts("[CH3][SX3](=O)[CH3]")
AZOLE = Chem.MolFromSmarts("[nX2;r5]")
PHOS = Chem.MolFromSmarts("[PX3]([#6])([#6])[#6]")


def is_arene(m):
    if any(a.GetFormalCharge() for a in m.GetAtoms()) or any(a.GetSymbol() not in ("C", "H") for a in m.GetAtoms()):
        return False
    return any(len(r) == 6 and all(m.GetAtomWithIdx(i).GetIsAromatic() for i in r) for r in m.GetRingInfo().AtomRings())


def family(smi):
    frags = [f for f in (Chem.MolFromSmiles(s) for s in smi.split(".")) if f is not None]
    if not frags:
        return "unparsed"
    if any(f.HasSubstructMatch(CP) and f.GetNumAtoms() <= 16 and all(a.GetSymbol() in ("C", "H") for a in f.GetAtoms())
           for f in frags):
        return "Cp / Cp*"
    if any(is_arene(f) for f in frags):
        return "η6-arene"
    if sum(any(f.HasSubstructMatch(p) for p in NN) for f in frags) >= 2:
        return "polypyridyl"
    if any(f.HasSubstructMatch(DMSO) for f in frags) or (any(f.HasSubstructMatch(AZOLE) for f in frags) and
                                                          sum(s == "[Cl-]" for s in smi.split(".")) >= 3):
        return "DMSO / azole (NAMI-A, KP1019 type)"
    if any(f.HasSubstructMatch(PHOS) for f in frags):
        return "phosphine"
    return "other"


meta = pd.read_csv(META)
meta["family"] = meta.SMILES_Ligands.map({s: family(s) for s in meta.SMILES_Ligands.unique()})
lg = pd.read_csv(D / f"lightgbm_doi{TAG}_oof.csv")[["row_id", "complex_id", "y", "fold", "prob"]]
dn = pd.read_csv(D / f"dimenet_doi{TAG}_oof.csv")[["row_id", "prob"]]
d = lg.merge(dn, on="row_id", suffixes=("_lg", "_dn")).merge(meta[["row_id", "family", "Cell_line", "Metal"]],
                                                               on="row_id")
d["flag_lg"] = d["flag_dn"] = False
for f, g in d.groupby("fold"):
    cut = 1 - d.y[d.fold != f].mean()
    d.loc[g.index, "flag_lg"] = rankdata(g.prob_lg) / len(g) > cut
    d.loc[g.index, "flag_dn"] = rankdata(g.prob_dn) / len(g) > cut
d["ok_lg"], d["ok_dn"] = d.flag_lg == d.y.astype(bool), d.flag_dn == d.y.astype(bool)
d.to_csv(HERE / f"{SET}_classes.csv", index=False)


def table(groups):
    rows = []
    for key, g in groups:
        two = g.y.nunique() == 2
        rows.append({"group": key, "measurements": len(g), "complexes": g.complex_id.nunique(), "toxic": g.y.mean(),
                     "AUC LightGBM": roc_auc_score(g.y, g.prob_lg) if two else np.nan,
                     "AUC DimeNet++": roc_auc_score(g.y, g.prob_dn) if two else np.nan,
                     "rho": spearmanr(g.prob_lg, g.prob_dn)[0], "both right": (g.ok_lg & g.ok_dn).mean(),
                     "both wrong": (~g.ok_lg & ~g.ok_dn).mean()})
    return pd.DataFrame(rows).sort_values("measurements", ascending=False).to_string(
        index=False, float_format=lambda v: f"{v:.2f}")


txt = f"{SET}: {len(d):,} measurements; by family\n" + table(d.groupby("family"))
if SET != "ru":
    txt += "\n\nby metal\n" + table(d.groupby("Metal"))
    big = d.groupby(["Metal", "family"]).filter(lambda g: len(g) >= 150)
    txt += "\n\nby metal and family (>= 150 measurements)\n" + table(big.groupby(["Metal", "family"]))
# the measurements both models get most confidently wrong
r = d.prob_lg.rank(pct=True) + d.prob_dn.rank(pct=True)
d["conf_err"] = np.where(d.y == 1, -r, r)
worst = d.sort_values("conf_err", ascending=False).head(300)
txt += "\n\nfamily share among the 300 most confident joint errors vs overall:\n"
txt += pd.concat([worst.family.value_counts(normalize=True).rename("worst300"),
                  d.family.value_counts(normalize=True).rename("all")], axis=1).fillna(0).to_string(
    float_format=lambda v: f"{v:.2f}")
txt += "\n\nby cell line (>= 300 measurements)\n" + table(d.groupby("Cell_line").filter(lambda g: len(g) >= 300)
                                                          .groupby("Cell_line"))
(HERE / f"{SET}_classes_summary.txt").write_text(txt + "\n", encoding="utf-8")
print(txt)
