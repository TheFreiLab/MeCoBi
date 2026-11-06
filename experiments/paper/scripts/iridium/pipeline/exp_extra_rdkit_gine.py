"""Two extra S. aureus classification runs, same protocol as exp_unified_multiseed.py:

  * RDKit      -- the 216 RDKit descriptors alone (no fingerprint), same MLP as ECFP+Hybrid
  * GINE       -- the xyz2graph bond-graph control, now with five seeds instead of one

Nothing of the original run is touched: predictions are cached in outputs/_sa_extra_ckpt and the
metrics go to outputs/metrics_extra_rdkit_gine.csv (same columns as metrics_unified_multiseed.csv).

    python exp_extra_rdkit_gine.py [--seeds 5] [--models RDKit GINE]
"""
import argparse
import os

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

import exp_unified_multiseed as M

M.CKDIR = os.path.join(M.OUT, "_sa_extra_ckpt")
os.makedirs(M.CKDIR, exist_ok=True)
M.SFX["RDKit"] = "RDKit"
N_FP = 512                                   # featurize() = [ECFP 512 | RDKit descriptors]


def rdkit_feat(df):
    return M.featurize(df.fp_smiles.tolist())[:, N_FP:]


def run_rdkit(train_df, pred_df, sd):
    """run_fp of the original pipeline, on the descriptor block only (median imputation)."""
    Xtr, ytr = rdkit_feat(train_df), train_df.SA_active.astype(int).values
    Xpr = rdkit_feat(pred_df)
    itr, iva = train_test_split(np.arange(len(ytr)), test_size=0.2, stratify=ytr, random_state=sd)
    thr = M.youden(ytr[iva], M.fp_prob(M.fp_fit(Xtr[itr], ytr[itr], "ECFP+Hybrid", sd), Xtr[iva]))
    p = M.fp_prob(M.fp_fit(Xtr, ytr, "ECFP+Hybrid", sd), Xpr)
    return dict(zip(pred_df.compound_id, p)), thr


def run_arm(arm, train_df, pred_df, train_keys, models, seeds):
    rows, gcache = [], None
    for disp in models:
        if disp == "GINE" and not M._all_cached(arm, "GINE", seeds):
            gcache = dict(train=M.graphs_for(train_df, "GINE", True),
                          pred=M.graphs_for(pred_df, "GINE", False))
        seed_probs, seed_thr = [], []
        for sd in seeds:
            fn = ((lambda: run_rdkit(train_df, pred_df, sd)) if disp == "RDKit"
                  else (lambda: M.run_graph("GINE", gcache, sd)))
            probs, thr = M.load_or_train(arm, disp, sd, fn)
            seed_probs.append(probs)
            seed_thr.append(thr)
            for gen, label, sub in M.arm_subsets(pred_df, train_keys):
                met = M.eval_subset(sub, M.SFX[disp], probs, thr)
                if met:
                    rows.append(dict(arm=arm, method=disp, generation=gen, subset=label, seed=sd,
                                     thr=round(thr, 4), **met))
        ens = {c: float(np.mean([sp[c] for sp in seed_probs if c in sp])) for c in seed_probs[0]}
        ethr = float(np.mean(seed_thr))
        for gen, label, sub in M.arm_subsets(pred_df, train_keys):
            met = M.eval_subset(sub, M.SFX[disp], ens, ethr)
            if met:
                rows.append(dict(arm=arm, method=disp, generation=gen, subset=label,
                                 seed="ensemble", thr=round(ethr, 4), **met))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--models", nargs="+", default=["RDKit", "GINE"], choices=["RDKit", "GINE"])
    args = ap.parse_args()
    seeds = list(range(42, 42 + args.seeds))
    m = pd.read_csv(M.MASTER)
    ok = m.conv_pass & m.SA_active.notna()
    g0 = m.generation == "gen0"
    g01 = m.generation.isin(["gen0", "gen1"])
    rows = run_arm("gen0->gen1+2", m[g0 & ok].copy(), m[m.generation.isin(["gen1", "gen2"])].copy(),
                   set(m[g0 & m.conv_pass].bb_key), args.models, seeds)
    rows += run_arm("gen0+1->gen2", m[g01 & ok].copy(), m[m.generation == "gen2"].copy(),
                    set(m[g01 & m.conv_pass].bb_key), args.models, seeds)
    out = M.summarise(pd.DataFrame(rows))
    dest = os.path.join(M.OUT, "metrics_extra_rdkit_gine.csv")
    out.to_csv(dest, index=False)
    v = out[(out.generation == "gen2") & (out.subset == "conv>=40 (no leaks)")
            & (out.seed.isin(["mean", "std", "ensemble"]))]
    print(v.pivot_table(index=["arm", "method"], columns="seed", values="roc_auc").to_string())
    print("wrote", dest)


if __name__ == "__main__":
    main()
