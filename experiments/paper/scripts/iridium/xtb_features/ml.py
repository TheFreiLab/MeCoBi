"""S. aureus activity of IrCpSB: does LightGBM on ECFP+RDKit improve with the xTB and surface descriptors?

    python ml.py [--seeds 5]

Same data, arms (gen0 -> gen1+2, gen0+1 -> gen2), seeds (42..), LightGBM settings and Youden threshold rule as
<IrCpSB_gen>/ML/rerun/_pipeline/exp_extra_lgbm.py, which is imported for them. Descriptors from xtb_features.csv
(features.py), joined on structure_stem; a complex without them keeps NaN (LightGBM handles it).
Feature sets: ECFP+RDKit (the published 2D model) | + xTB (electronic, solvation, geometry) | + xTB + surface |
RDKit + xTB + surface | xTB + surface alone. Controls without any xTB value (--controls): + area (total and
polar SASA) | + geometric surface (area, Cl and Ir exposure, buried volume, coverage; no charges).
Predictions are cached in ml_out/_ckpt; metrics in ml_out/metrics_xtb_lgbm.csv. For the 5-seed ensemble on the
gen2 no-leak subset, the ROC-AUC difference against ECFP+RDKit with a paired bootstrap (2,000 resamples of
complexes, 95% interval).
"""
import argparse
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parent
PIPE = Path(r"<DATA_ROOT>\York\Data\IrCpSB_gen\ML\rerun\_pipeline")
# Another structure set: XTB_FEATURES=<its xtb_features.csv> XTB_ML_OUT=<its output folder> python ml.py
FEAT = Path(os.environ.get("XTB_FEATURES", HERE / "xtb_features.csv"))
OUTD = Path(os.environ.get("XTB_ML_OUT", HERE / "ml_out"))
os.environ.setdefault("IRCPSB_OUT", str(OUTD))     # keeps the published outputs untouched
sys.path.insert(0, str(PIPE))
import exp_extra_lgbm as E  # noqa: E402
import exp_unified_multiseed as M  # noqa: E402
from features import ELEC, GEOM, SOLV, SURF  # noqa: E402

warnings.filterwarnings("ignore")
E.CK = str(OUTD / "_ckpt")
os.makedirs(E.CK, exist_ok=True)
XTB = pd.read_csv(FEAT, index_col=0)
AREA = ["SASA", "SASA_polar"]
GSURF = AREA + ["sasa_Cl", "sasa_Ir_p05", "Vbur50", "coverage"]
_cache = {}


def features(df, kind):
    key = (id(df), kind)
    if key not in _cache:
        full = M.featurize(df.fp_smiles.tolist())
        x = XTB.reindex(df.structure_stem)
        blocks = {"ECFP+RDKit": full, "RDKit": full[:, E.N_FP:], "xTB": x[ELEC + SOLV + GEOM].to_numpy(float),
                  "surface": x[SURF].to_numpy(float), "area": x[AREA].to_numpy(float),
                  "geometric surface": x[GSURF].to_numpy(float)}
        _cache[key] = np.hstack([blocks[p] for p in kind.split(" + ")])
    return _cache[key]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--controls", action="store_true", help="add the surface-only controls")
    a = ap.parse_args()
    E.features = features
    seeds = list(range(42, 42 + a.seeds))
    kinds = ["ECFP+RDKit", "ECFP+RDKit + xTB", "ECFP+RDKit + xTB + surface", "RDKit + xTB + surface",
             "xTB + surface"]
    if a.controls:
        kinds += ["ECFP+RDKit + area", "ECFP+RDKit + geometric surface", "RDKit + geometric surface",
                  "geometric surface"]
    m = pd.read_csv(M.MASTER)
    ok = m.conv_pass & m.SA_active.notna()
    print(f"xTB descriptors for {m.structure_stem.isin(XTB.index).sum()} of {len(m)} complexes", flush=True)
    rows, ens_by = [], {}
    for arm, tag, gens in [("gen0->gen1+2", "A_gen0", ["gen0"]), ("gen0+1->gen2", "B_gen01", ["gen0", "gen1"])]:
        train = m[m.generation.isin(gens) & ok].copy()
        pred = m[m.generation == "gen2"].copy()
        keys = set(m[m.generation.isin(gens) & m.conv_pass].bb_key)
        for kind in kinds:
            name = f"LightGBM:{kind}"
            sp, st = [], []
            for sd in seeds:
                probs, thr = E.cached(f"{tag}_{kind.replace(' + ', '__').replace('+', '_')}_s{sd}",
                                      lambda: E.run_lgbm(kind, train, pred, sd))
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
                if label == "conv>=40 (no leaks)":
                    ens_by[(arm, kind)] = (sub, ens)
            print(arm, name, "done", flush=True)
    out = M.summarise(pd.DataFrame(rows))
    tag = "_controls" if a.controls else ""
    out.to_csv(OUTD / f"metrics_xtb_lgbm{tag}.csv", index=False)
    v = out[(out.generation == "gen2") & (out.subset == "conv>=40 (no leaks)")
            & out.seed.isin(["mean", "std", "ensemble"])]
    lines = ["ROC-AUC, gen2 no-leak subset", v.pivot_table(index=["arm", "method"], columns="seed",
                                                          values="roc_auc").round(3).to_string(),
             "\nEnsemble ROC-AUC minus ECFP+RDKit, paired bootstrap over complexes (95% interval)"]
    rng = np.random.default_rng(0)
    for (arm, kind), (sub, ens) in ens_by.items():
        if kind == "ECFP+RDKit":
            continue
        s = sub.dropna(subset=["SA_active"])
        y = s.SA_active.astype(int).to_numpy()
        p0 = s.compound_id.astype(str).map(ens_by[(arm, "ECFP+RDKit")][1]).to_numpy(float)
        p1 = s.compound_id.astype(str).map(ens).to_numpy(float)
        diffs = []
        for _ in range(2000):
            i = rng.integers(0, len(y), len(y))
            if y[i].min() != y[i].max():
                diffs.append(roc_auc_score(y[i], p1[i]) - roc_auc_score(y[i], p0[i]))
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        lines.append(f"  {arm:<14} {kind:<28} {roc_auc_score(y, p1) - roc_auc_score(y, p0):+.3f} "
                     f"[{lo:+.3f}, {hi:+.3f}]  (n = {len(y)}, {int(y.sum())} active)")
    txt = "\n".join(lines)
    print(txt)
    (OUTD / f"metrics_xtb_lgbm{tag}.txt").write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    main()
