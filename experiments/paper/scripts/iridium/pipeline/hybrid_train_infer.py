"""ECFP + Hybrid (ECFP512 + RDKit descriptors, minus Ipc) MLP.

Trained on gen0 (conv>=40) with CORRECTED labels (active = SA_value < 0.20 => 1).
GroupKFold by Cp for CV + Youden threshold; final model on all gen0; infer gen1/2.
Fingerprint SMILES = Cp.Schiff.Cl (same assembly as the ECFP baseline).
"""
import os
import random
import warnings
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_curve
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.ML.Descriptors.MoleculeDescriptors import MolecularDescriptorCalculator
import joblib
warnings.filterwarnings("ignore")
from common import ROOT, ecfp, classification_metrics

MASTER = os.path.join(ROOT, "outputs", "master_groundtruth_SA.csv")
MODEL_OUT = os.path.join(ROOT, "outputs", "model_ECFP_Hybrid.pkl")

DESC_NAMES = [n for n, _ in Descriptors._descList if n != "Ipc"]  # drop Ipc (explodes)
_CALC = MolecularDescriptorCalculator(DESC_NAMES)


def set_seed(s=42):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)


def descriptors(smiles):
    m = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
    if m is None:
        return np.full(len(DESC_NAMES), np.nan, dtype=np.float64)
    try:
        return np.array(_CALC.CalcDescriptors(m), dtype=np.float64)
    except Exception:
        return np.full(len(DESC_NAMES), np.nan, dtype=np.float64)


def featurize(smiles_list):
    fp = np.stack([ecfp(s) for s in smiles_list]).astype(np.float64)
    de = np.stack([descriptors(s) for s in smiles_list]).astype(np.float64)
    de[~np.isfinite(de)] = np.nan
    return np.hstack([fp, de])


class MLP(nn.Module):
    def __init__(self, input_dim, hidden=(64, 32)):
        super().__init__()
        layers, last = [], input_dim
        for h in hidden:
            layers += [nn.Linear(last, h), nn.ReLU()]; last = h
        layers += [nn.Linear(last, 1)]
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x).squeeze(1)


def train_model(Xtr, ytr, input_dim, epochs=300, seed=42):
    set_seed(seed)
    model = MLP(input_dim)
    opt = torch.optim.Adam(model.parameters(), lr=3e-4, weight_decay=1e-3)
    loss_fn = nn.BCEWithLogitsLoss()
    dl = DataLoader(TensorDataset(torch.tensor(Xtr, dtype=torch.float32),
                                  torch.tensor(ytr, dtype=torch.float32)),
                    batch_size=64, shuffle=True)
    for _ in range(epochs):
        model.train()
        for xb, yb in dl:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
    return model


def probs(model, X):
    model.eval()
    with torch.no_grad():
        return torch.sigmoid(model(torch.tensor(X, dtype=torch.float32))).numpy()


def main():
    m = pd.read_csv(MASTER)
    g0 = m[(m["generation"] == "gen0") & (m["conv_pass"]) & m["SA_active"].notna()].copy()
    X0 = featurize(g0["fp_smiles"].tolist())
    y0 = g0["SA_active"].astype(int).values
    groups = g0["Cp_SMILES_can"].values
    input_dim = X0.shape[1]
    print(f"gen0 train: n={len(g0)} features={input_dim} (512 ECFP + {len(DESC_NAMES)} desc) "
          f"active={int(y0.sum())}")

    # --- CV for threshold (GroupKFold by Cp), active=1 positive ---
    thrs, aucs = [], []
    for tr, va in GroupKFold(n_splits=4).split(X0, y0, groups):
        imp = SimpleImputer(strategy="median").fit(X0[tr])
        sc = StandardScaler().fit(imp.transform(X0[tr]))
        Xtr = sc.transform(imp.transform(X0[tr])).astype(np.float32)
        Xva = sc.transform(imp.transform(X0[va])).astype(np.float32)
        model = train_model(Xtr, y0[tr], input_dim)
        p = probs(model, Xva)
        if len(set(y0[va])) == 2:
            fpr, tpr, t = roc_curve(y0[va], p)
            thrs.append(float(t[np.argmax(tpr - fpr)]))
            from sklearn.metrics import roc_auc_score
            aucs.append(roc_auc_score(y0[va], p))
    best_thr = float(np.median(thrs)) if thrs else 0.5
    print(f"CV mean ROC-AUC={np.mean(aucs):.3f} | chosen active-threshold={best_thr:.3f}")

    # --- final model on all gen0 ---
    imp = SimpleImputer(strategy="median").fit(X0)
    sc = StandardScaler().fit(imp.transform(X0))
    Xall = sc.transform(imp.transform(X0)).astype(np.float32)
    final = train_model(Xall, y0, input_dim)
    joblib.dump({"state_dict": final.state_dict(), "imputer": imp, "scaler": sc,
                 "threshold": best_thr, "input_dim": input_dim, "desc_names": DESC_NAMES}, MODEL_OUT)

    # --- inference gen1/2 ---
    ev = m[(m["generation"].isin(["gen1", "gen2"])) & (m["conv_pass"]) & m["SA_active"].notna()].copy()
    Xe = sc.transform(imp.transform(featurize(ev["fp_smiles"].tolist()))).astype(np.float32)
    p_active = probs(final, Xe)
    pred_active = (p_active >= best_thr).astype(int)

    preds = pd.DataFrame(dict(
        method="ECFP+Hybrid", target="SA", generation=ev["generation"].values,
        compound_id=ev["compound_id"].values, SA_value=ev["SA_value"].values,
        SA_active=ev["SA_active"].astype(int).values,
        P_active=np.round(p_active, 4), pred_active=pred_active))
    preds.to_csv(os.path.join(ROOT, "outputs", "pred_ECFP_Hybrid.csv"), index=False)

    rows = []
    for gen, g in preds.groupby("generation"):
        rows.append(dict(method="ECFP+Hybrid", target="SA", generation=gen,
                         **classification_metrics(g["SA_active"], g["pred_active"], g["P_active"])))
    met = pd.DataFrame(rows)
    met.to_csv(os.path.join(ROOT, "outputs", "metrics_ECFP_Hybrid.csv"), index=False)
    print(met.to_string(index=False))


if __name__ == "__main__":
    main()
