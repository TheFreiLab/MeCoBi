"""Every number of the iridium section for the structures rebuilt with the fixed MeCoBi (full_fix2).

    python numbers_fix2.py      -> ml_fix2/numbers_fix2.txt

Test sets, seeds (42-46), ensemble (mean probability) and LogP as MeCoBi_Paper/Data/make_si_extra.py.
Per-seed ROC-AUC (mean +/- s.d.), ensemble ROC-AUC, actives among the 40 highest, Spearman with LogP,
ROC-AUC within LogP terciles, ROC-AUC without the three amide-type amines (26, 36, 38), and paired
bootstrap differences (5,000 resamples, as in the manuscript).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Crippen
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
IR = Path(r"<DATA_ROOT>\MeCoBi_Paper\Data\IrCpSB\SA_classification")
CK = HERE / "ml_fix2" / "_sa_multiseed_ckpt"
XC = HERE / "xtb_features" / "ml_out_fix2" / "_ckpt"
SEEDS = range(42, 47)
ARMS = [("A_gen0", ["gen0"], "gen0"), ("B_gen01", ["gen0", "gen1"], "gen0 + gen1")]
MODELS = {"LightGBM ECFP": (IR / "seed_predictions_lgbm", "{t}_LightGBM_ECFP_s{s}.json"),
          "LightGBM RDKit": (IR / "seed_predictions_lgbm", "{t}_LightGBM_RDKit_s{s}.json"),
          "LightGBM ECFP+RDKit": (XC, "{t}_ECFP_RDKit_s{s}.json"),
          "LightGBM ECFP+RDKit+xTB": (XC, "{t}_ECFP_RDKit__xTB_s{s}.json"),
          "DimeNet++": (CK, "{t}_DimeNet_s{s}.json"),
          "GINE": (CK, "{t}_GINE_s{s}.json")}
AMIDE = ("26", "36", "38")
rng = np.random.default_rng(1)
m = pd.read_csv(IR / "master_groundtruth_SA.csv")
# LogP of the ligands as bound: Cp and Schiff base neutral, chloride as [Cl-] (fp_smiles writes it as HCl, Cl)
m["logp"] = [Crippen.MolLogP(Chem.MolFromSmiles(s.rsplit(".", 1)[0] + ".[Cl-]")) for s in m.fp_smiles]
ok = m[m.conv_pass]
out = []


def boot(y, a, b, n=5000):
    d = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() != y[i].max():
            d.append(roc_auc_score(y[i], a[i]) - roc_auc_score(y[i], b[i]))
    return roc_auc_score(y, a) - roc_auc_score(y, b), *np.percentile(d, [2.5, 97.5])


for tag, gens, name in ARMS:
    tr = ok[ok.generation.isin(gens)]
    te = ok[(ok.generation == "gen2") & ~ok.bb_key.isin(set(tr.bb_key))].reset_index(drop=True)
    y = te.SA_active.to_numpy(int)
    lp = te.logp.to_numpy()
    amine_no = te.compound_name.str.extract(r"IrCp\d[A-Z]+(\d+)_")[0]
    no_amide = ~amine_no.isin(AMIDE).to_numpy()
    q = np.asarray(pd.qcut(lp, 3, labels=["low", "middle", "high"]))
    out.append(f"\n=== trained on {name}: {len(y)} test complexes, {y.sum()} active; "
               f"without amines 26/36/38: {no_amide.sum()} ({y[no_amide].sum()} active) ===")
    out.append(f"  {'LogP (no model)':<26} ensemble {roc_auc_score(y, lp):.3f}   top40 {y[np.argsort(-lp)[:40]].mean():.0%}"
               f"   terciles " + " / ".join(f"{roc_auc_score(y[q == t], lp[q == t]):.2f}" for t in ('low', 'middle', 'high'))
               + f"   no-amide {roc_auc_score(y[no_amide], lp[no_amide]):.3f}")
    E = {"LogP": lp}
    for mod, (src, pat) in MODELS.items():
        P = np.array([te.compound_id.map(json.loads((src / pat.format(t=tag, s=s)).read_text())["probs"]).astype(float)
                      for s in SEEDS])
        if np.isnan(P).any():
            out.append(f"  {mod}: missing predictions for {int(np.isnan(P[0]).sum())} complexes")
            continue
        per = [roc_auc_score(y, p) for p in P]
        e = P.mean(0)
        E[mod] = e
        out.append(f"  {mod:<26} seeds {np.mean(per):.3f} ± {np.std(per, ddof=0):.3f}   ensemble {roc_auc_score(y, e):.3f}"
                   f"   top40 {y[np.argsort(-e)[:40]].mean():.0%}   rho(LogP) {spearmanr(e, lp)[0]:.2f}"
                   f"   terciles " + " / ".join(f"{roc_auc_score(y[q == t], e[q == t]):.2f}" for t in ('low', 'middle', 'high'))
                   + f"   no-amide {roc_auc_score(y[no_amide], e[no_amide]):.3f}")
    out.append("  paired bootstrap, ensemble ROC-AUC difference [2.5, 97.5]:")
    for a, b in [("DimeNet++", "LightGBM RDKit"), ("DimeNet++", "LightGBM ECFP+RDKit"), ("DimeNet++", "LightGBM ECFP+RDKit+xTB"),
                 ("DimeNet++", "LogP"), ("LightGBM ECFP+RDKit+xTB", "LightGBM ECFP+RDKit"), ("LightGBM ECFP+RDKit+xTB", "LogP")]:
        d, lo, hi = boot(y, E[a], E[b])
        out.append(f"    {a} - {b}: {d:+.3f} [{lo:+.3f}, {hi:+.3f}]")
txt = "\n".join(out)
print(txt)
(HERE / "ml_fix2" / "numbers_fix2.txt").write_text(txt, encoding="utf-8")
