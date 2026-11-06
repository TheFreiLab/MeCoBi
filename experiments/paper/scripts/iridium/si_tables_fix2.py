"""DimeNet++ and GINE rows of Supplementary Tables S13-S16 and S18 for the structures of the fixed MeCoBi (full_fix2).

    python si_tables_fix2.py      -> ml_fix2/si_tables_fix2.txt

Same definitions as MeCoBi_Paper/Data/make_si_extra.py (S13-S15) and the published S16/S18: test sets of the two
training arms (gen2, building-block combination absent from training, conversion >= 40%), ensemble = mean of the
five seeds' probabilities, LogP = Crippen of the ligands with the chloride as [Cl-]. S16: the ensemble at the mean
of the five seeds' thresholds; S18: per-seed ROC-AUC with the population s.d. The 2D models use no structure and
keep their published rows.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Crippen
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, cohen_kappa_score, matthews_corrcoef, roc_auc_score

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
DATA = Path(r"<DATA_ROOT>\MeCoBi_Paper\Data\IrCpSB")
IR, PRED = DATA / "SA_classification", DATA / "SA_classification_fix2" / "seed_predictions"
SEEDS = range(42, 47)
ARMS = [("A_gen0", ["gen0"], "gen0"), ("B_gen01", ["gen0", "gen1"], "gen0 + gen1")]
MODELS = [("DimeNet", "DimeNet++, MeCoBi structure"), ("GINE", "GINE (control), MeCoBi structure")]

m = pd.read_csv(IR / "master_groundtruth_SA.csv")
m["logp"] = [Crippen.MolLogP(Chem.MolFromSmiles(s.rsplit(".", 1)[0] + ".[Cl-]")) for s in m.fp_smiles]
ok = m[m.conv_pass]
bb = pd.read_csv(IR / "building_blocks.csv", dtype=str)
am = bb[(bb.kind == "amine") & bb.label.isin(["26", "36", "38"])].set_index("smiles").label
can = lambda s: Chem.MolToSmiles(Chem.MolFromSmiles(s))  # noqa: E731
am.index = [can(s) for s in am.index]
out = []
for tag, gens, name in ARMS:
    tr = ok[ok.generation.isin(gens)]
    te = ok[(ok.generation == "gen2") & ~ok.bb_key.isin(set(tr.bb_key))].reset_index(drop=True)
    y, lp = te.SA_active.to_numpy().astype(int), te.logp.to_numpy()
    q = np.asarray(pd.qcut(lp, 3, labels=["low", "middle", "high"]))
    amide = te.Amine_SMILES_can.map(can).map(am).notna().to_numpy()
    out.append(f"\n=== {name}: {len(y)} test complexes, {y.sum()} active ===")
    for key, label in MODELS:
        runs = [json.loads((PRED / f"{tag}_{key}_s{s}.json").read_text()) for s in SEEDS]
        P = np.array([te.compound_id.map(r["probs"]).astype(float).to_numpy() for r in runs])
        e, k = P.mean(0), ~np.isnan(P).any(0)
        yy, ee = y[k], e[k]
        out.append(f"[{label}] n = {k.sum()} ({yy.sum()} active)")
        out.append(f"  S13  ROC-AUC {roc_auc_score(yy, ee):.3f} | Spearman with LogP {spearmanr(ee, lp[k]).statistic:.2f}"
                   f" | active among the 40 highest {100 * yy[np.argsort(-ee)[:40]].mean():.0f}%")
        t = []
        for g in ("low", "middle", "high"):
            s = (q == g) & k
            t.append(f"{roc_auc_score(y[s], e[s]):.2f}" if 0 < y[s].sum() < s.sum() else "–")
        out.append("  S14  terciles low / middle / high: " + " / ".join(t))
        pct = pd.Series(ee).rank(pct=True).to_numpy()
        sa = amide[k]
        out.append(f"  S15  amines 26/36/38: {sa.sum()} ({yy[sa].sum()}) | mean percentile {100 * pct[sa].mean():.0f}"
                   f" | ROC-AUC all {roc_auc_score(yy, ee):.3f} | without them {roc_auc_score(yy[~sa], ee[~sa]):.3f}")
        thr = float(np.mean([r["thr"] for r in runs]))
        pr = (ee >= thr).astype(int)
        tp, fp = int(((pr == 1) & (yy == 1)).sum()), int(((pr == 1) & (yy == 0)).sum())
        fn, tn = int(((pr == 0) & (yy == 1)).sum()), int(((pr == 0) & (yy == 0)).sum())
        prec = tp / (tp + fp) if tp + fp else float("nan")
        rec, spec = tp / (tp + fn), tn / (tn + fp)
        npv = tn / (tn + fn) if tn + fn else float("nan")
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        out.append(f"  S16  {tp} / {fp} / {fn} / {tn} | thr {thr:.3f} | acc {(tp + tn) / len(yy):.3f}"
                   f" | bal.acc {(rec + spec) / 2:.3f} | precision {prec:.3f} | recall {rec:.3f}")
        out.append(f"       specificity {spec:.3f} | NPV " + ("–" if np.isnan(npv) else f"{npv:.3f}")
                   + f" | F1 {f1:.3f} | MCC {matthews_corrcoef(yy, pr):.3f} | kappa {cohen_kappa_score(yy, pr):.3f}"
                   f" | enrichment {prec / yy.mean():.3f} | ROC-AUC {roc_auc_score(yy, ee):.3f}"
                   f" | PR-AUC {average_precision_score(yy, ee):.3f}")
        per = [roc_auc_score(yy, p[k]) for p in P]
        out.append("  S18  " + " | ".join(f"{v:.3f}" for v in per) + f" | mean {np.mean(per):.3f} | s.d. {np.std(per):.3f}")
(HERE / "ml_fix2" / "si_tables_fix2.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
