"""tmQM x MeCoBi benchmark: 2D floor for the prediction of DFT properties.

Complexes: the built MeCoBi benchmark structures (connectivity preserved) that are also in tmQM.
Features: count-Morgan fingerprint of the ligand set, a few ligand descriptors, metal, oxidation
state, total charge, coordination number and donor-element counts. No coordinates are used.
Targets (tmQM, TPSSh-D3BJ/def2-SVP on GFN2-xTB geometries): HOMO-LUMO gap, HOMO, LUMO (eV), dipole
moment (D), natural charge of the metal (e), polarisability (GFN2-xTB, a.u.).

Splits (10-fold, shared with the 3D models through folds.csv):
  random : by complex
  ligand : grouped by the largest ligand of each complex, so complexes of one ligand family stay
           in one fold

    python baseline_2d.py --tmqm ~/Downloads/tmQM_y.csv --out results_2d
"""
from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Crippen, Descriptors, rdFingerprintGenerator, rdMolDescriptors
from sklearn.model_selection import GroupKFold, KFold

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
BENCH = HERE.parent / "benchmark"
PT = Chem.GetPeriodicTable()
GEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
HARTREE_EV = 27.211386
TARGETS = {"HL_Gap": ("gap_eV", HARTREE_EV), "HOMO_Energy": ("homo_eV", HARTREE_EV),
           "LUMO_Energy": ("lumo_eV", HARTREE_EV), "Dipole_M": ("dipole_D", 1.0),
           "Metal_q": ("metal_q", 1.0), "Polarizability": ("polarizability", 1.0)}
DONORS = ["C", "N", "O", "P", "S", "Cl", "Br", "I", "F", "Se", "As", "H", "Si", "B"]
PARAMS = dict(n_estimators=800, learning_rate=0.03, num_leaves=31, min_child_samples=10,
              subsample=0.8, subsample_freq=1, colsample_bytree=0.3, reg_lambda=1.0, verbose=-1,
              n_jobs=-1, random_state=0)


def load_table(tmqm_csv: str, per_structure: str) -> pd.DataFrame:
    """Benchmark complexes built by MeCoBi with the connectivity preserved, joined to tmQM."""
    t = pd.read_csv(tmqm_csv, sep=";").set_index("CSD_code")
    b = pd.read_csv(per_structure)
    ok = (b.built.astype(str).str.lower() == "true") & (b.connectivity_ok.astype(str).str.lower() == "true")
    b = b[ok & b.refcode.isin(t.index)].reset_index(drop=True)
    bundle = {r["refcode"]: r for r in json.loads(gzip.open(BENCH / "benchmark_bundle.json.gz", "rt").read())}
    b = b[b.refcode.isin(bundle)].reset_index(drop=True)
    df = pd.DataFrame({"refcode": b.refcode, "metal": b.metal, "ox": b.ox, "cn": b.cn,
                       "n_hydride": b.n_hydride.fillna(0).astype(int),
                       "ligands": ["|".join(bundle[r]["ligands"]) for r in b.refcode],
                       "charge": [bundle[r]["ox"] + sum(bundle[r]["charges"]) for r in b.refcode],
                       "donor_elements": ["|".join(bundle[r]["donor_elements"]) for r in b.refcode]})
    for col, (name, f) in TARGETS.items():
        df[name] = t.loc[df.refcode, col].to_numpy(float) * f
    return df


def features(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in df.itertuples():
        f = {"metal_Z": PT.GetAtomicNumber(r.metal), "ox": r.ox, "charge": r.charge, "cn": r.cn,
             "n_ligands": r.ligands.count("|") + 1, "group": PT.GetNOuterElecs(PT.GetAtomicNumber(r.metal))}
        cnt = Counter(r.donor_elements.split("|"))
        f.update({f"don_{e}": cnt.get(e, 0) for e in DONORS})
        fp = np.zeros(2048)
        agg = Counter()
        for s in r.ligands.split("|"):
            m = Chem.MolFromSmiles(s)
            if m is None:
                continue
            fp += GEN.GetCountFingerprintAsNumPy(m)
            agg["L_mw"] += Descriptors.MolWt(m)
            agg["L_logp"] += Crippen.MolLogP(m)
            agg["L_tpsa"] += rdMolDescriptors.CalcTPSA(m)
            agg["L_heavy"] += m.GetNumHeavyAtoms()
            agg["L_arom"] += rdMolDescriptors.CalcNumAromaticRings(m)
            agg["L_rotb"] += rdMolDescriptors.CalcNumRotatableBonds(m)
            agg["L_halogen"] += sum(a.GetSymbol() in ("F", "Cl", "Br", "I") for a in m.GetAtoms())
        f.update(agg)
        f.update({f"fp{k}": v for k, v in enumerate(fp) if v})
        rows.append(f)
    X = pd.DataFrame(rows)
    fp_cols = sorted((c for c in X if c.startswith("fp")), key=lambda c: int(c[2:]))
    other = [c for c in X if not c.startswith("fp")]
    X = pd.concat([X[other].fillna(0), X[fp_cols].fillna(0)], axis=1)
    X["metal"] = df.metal.astype("category").to_numpy()
    X["metal"] = X["metal"].astype("category")
    return X


def ligand_groups(df: pd.DataFrame) -> np.ndarray:
    """One group per largest ligand (canonical SMILES; ties broken alphabetically).

    Linking complexes through any shared ligand chains half of the set into one component (PPh3,
    Cp and CO-free common ligands connect everything), which leaves one fold with most of the data.
    Grouping by the largest ligand keeps the complexes of one ligand family together without that.
    """
    keys = []
    for ligs in df.ligands:
        best = None
        for s in ligs.split("|"):
            m = Chem.MolFromSmiles(s)
            if m is None:
                continue
            k = (-m.GetNumHeavyAtoms(), Chem.MolToSmiles(m))
            best = k if best is None or k < best else best
        keys.append(best[1] if best else ligs)
    return pd.factorize(pd.Series(keys))[0]


def make_folds(df: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    out = pd.DataFrame({"refcode": df.refcode})
    out["random"] = -1
    for k, (_, te) in enumerate(KFold(10, shuffle=True, random_state=seed).split(df)):
        out.loc[te, "random"] = k
    g = ligand_groups(df)
    perm = np.random.RandomState(seed).permutation(g.max() + 1)
    out["ligand"] = -1
    for k, (_, te) in enumerate(GroupKFold(10).split(df, groups=perm[g])):
        out.loc[te, "ligand"] = k
    out["ligand_group"] = g
    return out


def metrics(y, p):
    e = y - p
    return np.abs(e).mean(), np.sqrt((e ** 2).mean()), 1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmqm", required=True)
    ap.add_argument("--per-structure", required=True, help="mecobi_30k_final_per_structure.csv")
    ap.add_argument("--out", default="results_2d")
    ap.add_argument("--targets", nargs="+", default=["gap_eV", "dipole_D", "metal_q", "homo_eV", "lumo_eV",
                                                     "polarizability"])
    a = ap.parse_args()
    out = HERE / a.out
    out.mkdir(exist_ok=True)
    df = load_table(a.tmqm, a.per_structure)
    X = features(df)
    folds = make_folds(df)
    df.to_csv(HERE / "table.csv", index=False)
    folds.to_csv(HERE / "folds.csv", index=False)
    print(f"{len(df)} complexes, {df.metal.nunique()} metals, {X.shape[1]} features, "
          f"{folds.ligand_group.nunique()} ligand groups (largest {folds.ligand_group.value_counts().max()})")
    lines, oof_all = [], {"refcode": df.refcode}
    for split in ("random", "ligand"):
        lines.append(f"\n[{split} split]")
        for t in a.targets:
            y = df[t].to_numpy(float)
            oof, base = np.zeros(len(y)), np.zeros(len(y))
            for k in range(10):
                te = (folds[split] == k).to_numpy()
                m = lgb.LGBMRegressor(**PARAMS).fit(X[~te], y[~te])
                oof[te] = m.predict(X[te])
                means = pd.Series(y[~te]).groupby(df.metal[~te].to_numpy()).mean()
                base[te] = df.metal[te].map(means).fillna(y[~te].mean()).to_numpy()
            mae, rmse, r2 = metrics(y, oof)
            bmae, _, br2 = metrics(y, base)
            fold_mae = [np.abs(y[folds[split] == k] - oof[folds[split] == k]).mean() for k in range(10)]
            lines.append(f"{t:<15} LightGBM 2D  MAE {mae:.3f} ± {np.std(fold_mae):.3f}  RMSE {rmse:.3f}  R2 {r2:.3f}"
                         f"   | mean per metal: MAE {bmae:.3f}  R2 {br2:.3f}   | s.d. of target {y.std():.3f}")
            oof_all[f"{t}_{split}"] = oof
    pd.DataFrame(oof_all).to_csv(out / "oof_2d.csv", index=False)
    text = "\n".join(lines)
    (out / "metrics.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
