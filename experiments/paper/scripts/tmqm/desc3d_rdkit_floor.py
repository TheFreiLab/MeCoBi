"""Does the gain from the 3D descriptors survive a stronger 2D floor?

Same complexes, folds and 3D descriptors as desc3d_pilot.py (reads its cached files), but the 2D
model also receives the full RDKit descriptor block (all descriptors except Ipc) computed on the
ligand set. If the 3D gain on the dipole came from a weak 2D model, it disappears here.

    python desc3d_rdkit_floor.py
"""
from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors
from rdkit.ML.Descriptors.MoleculeDescriptors import MolecularDescriptorCalculator
from scipy.stats import ttest_rel

import baseline_2d as b

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
NAMES = [n for n, _ in Descriptors._descList if n != "Ipc"]
CALC = MolecularDescriptorCalculator(NAMES)


def rdkit_block(ligands: str) -> list[float]:
    m = Chem.MolFromSmiles(ligands.replace("|", "."))
    if m is None:
        return [np.nan] * len(NAMES)
    try:
        return list(CALC.CalcDescriptors(m))
    except Exception:  # noqa: BLE001
        return [np.nan] * len(NAMES)


def main():
    out = HERE / "results_desc3d"
    inc = pd.read_csv(HERE / "inclusion.csv")
    keep = set(inc[inc.include].refcode)
    df = pd.read_csv(HERE / "table.csv")
    df = df[df.refcode.isin(keep)].reset_index(drop=True)
    GT, GM = pd.read_pickle(out / "descriptors.pkl")
    X2 = pd.read_pickle(out / "X2.pkl")
    R = pd.DataFrame([rdkit_block(s) for s in df.ligands], columns=["rd_" + n for n in NAMES]).astype(float)
    R = R.replace([np.inf, -np.inf], np.nan).clip(-1e6, 1e6)
    XR = pd.concat([X2, R], axis=1)
    folds = pd.read_csv(HERE / "folds.csv").set_index("refcode").loc[df.refcode].reset_index()
    sets = {"2D (with RDKit block)": XR, "+ 3D (tmQM)": pd.concat([XR, GT], axis=1),
            "+ 3D (MeCoBi)": pd.concat([XR, GM], axis=1)}
    lines = [f"{len(df)} complexes; 2D features {X2.shape[1]} + {R.shape[1]} RDKit descriptors"]
    for split in ("random", "ligand"):
        for t in ("dipole_D", "gap_eV"):
            y = df[t].to_numpy(float)
            lines.append(f"\n[{split} split] {t}")
            fm = {}
            for name, F in sets.items():
                oof = np.zeros(len(y))
                for k in range(10):
                    te = (folds[split] == k).to_numpy()
                    oof[te] = lgb.LGBMRegressor(**b.PARAMS).fit(F[~te], y[~te]).predict(F[te])
                fm[name] = np.array([np.abs(y[folds[split] == k] - oof[folds[split] == k]).mean() for k in range(10)])
                e = y - oof
                extra = ""
                if name != "2D (with RDKit block)":
                    d = fm[name] - fm["2D (with RDKit block)"]
                    extra = (f" | vs 2D {d.mean():+.3f} (lower in {int((d < 0).sum())}/10 folds, "
                             f"paired t P = {ttest_rel(fm[name], fm['2D (with RDKit block)']).pvalue:.4f})")
                lines.append(f"  {name:<24} MAE {np.abs(e).mean():.3f} ± {fm[name].std():.3f}  "
                             f"R2 {1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum():.3f}{extra}")
    text = "\n".join(lines)
    (out / "metrics_rdkit_floor.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
