"""2D baselines with gradient boosting, and with the three descriptors of the cytotoxicity study.

Same data, splits, seeds and threshold rule as exp_unified_multiseed.py. Nothing of the earlier runs
is touched: predictions go to outputs/_sa_lgbm_ckpt, metrics to outputs/metrics_extra_lgbm.csv.

  engine LightGBM on: ECFP | RDKit (216 descriptors) | ECFP+RDKit | D3 (LogP, TPSA, MW) | ECFP+D3
  engine MLP (--mlp) on: D3 | ECFP+D3            (the MLP runs of the other feature sets exist already)

    python exp_extra_lgbm.py            # LightGBM only (about a minute)
    python exp_extra_lgbm.py --mlp      # adds the two MLP runs (slow)
"""
import argparse
import json
import os
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, rdMolDescriptors
from sklearn.model_selection import train_test_split

import exp_unified_multiseed as M

warnings.filterwarnings("ignore")
CK = os.path.join(M.OUT, "_sa_lgbm_ckpt")
os.makedirs(CK, exist_ok=True)
N_FP = 512
LGB = dict(n_estimators=500, learning_rate=0.05, num_leaves=31, min_child_samples=10, subsample=0.8,
           subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=4)
_cache = {}


def d3(smiles):
    m = Chem.MolFromSmiles(smiles)
    return [Crippen.MolLogP(m), rdMolDescriptors.CalcTPSA(m), Descriptors.MolWt(m)]


def features(df, kind):
    key = (id(df), kind)
    if key not in _cache:
        full = M.featurize(df.fp_smiles.tolist())
        three = np.array([d3(s) for s in df.fp_smiles], float)
        _cache[key] = {"ECFP": full[:, :N_FP], "RDKit": full[:, N_FP:], "ECFP+RDKit": full,
                       "D3": three, "ECFP+D3": np.hstack([full[:, :N_FP], three])}[kind]
    return _cache[key]


def run_lgbm(kind, train_df, pred_df, sd):
    Xtr, ytr, Xpr = features(train_df, kind), train_df.SA_active.astype(int).values, features(pred_df, kind)
    itr, iva = train_test_split(np.arange(len(ytr)), test_size=0.2, stratify=ytr, random_state=sd)
    fit = lambda X, y: lgb.LGBMClassifier(random_state=sd, **LGB).fit(X, y)
    thr = M.youden(ytr[iva], fit(Xtr[itr], ytr[itr]).predict_proba(Xtr[iva])[:, 1])
    return dict(zip(pred_df.compound_id, fit(Xtr, ytr).predict_proba(Xpr)[:, 1])), thr


def run_mlp(kind, train_df, pred_df, sd):
    Xtr, ytr, Xpr = features(train_df, kind), train_df.SA_active.astype(int).values, features(pred_df, kind)
    itr, iva = train_test_split(np.arange(len(ytr)), test_size=0.2, stratify=ytr, random_state=sd)
    thr = M.youden(ytr[iva], M.fp_prob(M.fp_fit(Xtr[itr], ytr[itr], "ECFP+Hybrid", sd), Xtr[iva]))
    return dict(zip(pred_df.compound_id, M.fp_prob(M.fp_fit(Xtr, ytr, "ECFP+Hybrid", sd), Xpr))), thr


def cached(tag, compute):
    fp = os.path.join(CK, tag + ".json")
    if os.path.exists(fp):
        d = json.load(open(fp, encoding="utf-8"))
        return d["probs"], float(d["thr"])
    probs, thr = compute()
    json.dump({"probs": {str(k): float(v) for k, v in probs.items()}, "thr": float(thr)},
              open(fp, "w", encoding="utf-8"))
    return probs, thr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mlp", action="store_true")
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()
    seeds = list(range(42, 42 + args.seeds))
    jobs = [("LightGBM", k, run_lgbm) for k in ("ECFP", "RDKit", "ECFP+RDKit", "D3", "ECFP+D3")]
    if args.mlp:
        jobs += [("MLP", k, run_mlp) for k in ("D3", "ECFP+D3")]
    m = pd.read_csv(M.MASTER)
    ok = m.conv_pass & m.SA_active.notna()
    arms = [("gen0->gen1+2", "A_gen0", ["gen0"]), ("gen0+1->gen2", "B_gen01", ["gen0", "gen1"])]
    rows = []
    for arm, tag, gens in arms:
        train = m[m.generation.isin(gens) & ok].copy()
        pred = m[m.generation == "gen2"].copy()
        keys = set(m[m.generation.isin(gens) & m.conv_pass].bb_key)
        for engine, kind, fn in jobs:
            name = f"{engine}:{kind}"
            sp, st = [], []
            for sd in seeds:
                probs, thr = cached(f"{tag}_{engine}_{kind.replace('+', '_')}_s{sd}",
                                    lambda: fn(kind, train, pred, sd))
                sp.append(probs)
                st.append(thr)
                for gen, label, sub in M.arm_subsets(pred, keys):
                    met = M.eval_subset(sub, name, probs, thr)
                    if met:
                        rows.append(dict(arm=arm, method=name, generation=gen, subset=label, seed=sd,
                                         thr=round(thr, 4), **met))
            ens = {c: float(np.mean([p[c] for p in sp])) for c in sp[0]}
            for gen, label, sub in M.arm_subsets(pred, keys):
                met = M.eval_subset(sub, name, ens, float(np.mean(st)))
                if met:
                    rows.append(dict(arm=arm, method=name, generation=gen, subset=label, seed="ensemble",
                                     thr=round(float(np.mean(st)), 4), **met))
            print(arm, name, "done", flush=True)
    out = M.summarise(pd.DataFrame(rows))
    out.to_csv(os.path.join(M.OUT, "metrics_extra_lgbm.csv"), index=False)
    v = out[(out.generation == "gen2") & (out.subset == "conv>=40 (no leaks)")
            & out.seed.isin(["mean", "std", "ensemble"])]
    print(v.pivot_table(index=["arm", "method"], columns="seed", values="roc_auc").round(3).to_string())


if __name__ == "__main__":
    main()
