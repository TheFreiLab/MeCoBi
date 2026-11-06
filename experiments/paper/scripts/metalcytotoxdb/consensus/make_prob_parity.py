"""Ruthenium benchmark (MetalCytoToxDB): predicted probability of LightGBM (2D) against DimeNet++ (3D), and the
consensus rules. Out-of-fold predictions on the 10,824 measurements of the DimeNet++ run (with descriptors).

    python make_prob_parity.py   -> prob_parity_2d_3d.{png,svg,pdf}, consensus_summary.txt
"""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, rankdata, spearmanr, ttest_rel
from sklearn.metrics import balanced_accuracy_score, precision_score, recall_score, roc_auc_score

HERE = Path(__file__).resolve().parent
D = HERE.parent / "Figure_5" / "data_fix6e0590a"
mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"], "font.size": 7,
                     "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
                     "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "pdf.fonttype": 42, "svg.fonttype": "none"})
MM = 1 / 25.4
TOX, NON = "#D55E00", "#0072B2"

lg = pd.read_csv(D / "lightgbm_doi_oof.csv")[["row_id", "y", "fold", "prob"]]
dn = pd.read_csv(D / "dimenet_doi_oof.csv")[["row_id", "prob"]]
d = lg.merge(dn, on="row_id", suffixes=("_lg", "_dn"))

# consensus scores and rules, per fold
auc = {k: [] for k in ("LightGBM", "DimeNet++", "rank mean", "rank min (AND)")}
rules = {k: [] for k in ("LightGBM", "DimeNet++", "AND", "OR")}
d["rk_lg"] = d["rk_dn"] = 0.0
for f, g in d.groupby("fold"):
    a, b = rankdata(g.prob_lg) / len(g), rankdata(g.prob_dn) / len(g)
    d.loc[g.index, "rk_lg"], d.loc[g.index, "rk_dn"] = a, b
    for k, s in (("LightGBM", a), ("DimeNet++", b), ("rank mean", (a + b) / 2), ("rank min (AND)", np.minimum(a, b))):
        auc[k].append(roc_auc_score(g.y, s))
    cut = 1 - d.y[d.fold != f].mean()  # toxic fraction of the training folds
    pa, pb = a > cut, b > cut
    for k, p in (("LightGBM", pa), ("DimeNet++", pb), ("AND", pa & pb), ("OR", pa | pb)):
        rules[k].append((precision_score(g.y, p), recall_score(g.y, p), balanced_accuracy_score(g.y, p), p.mean()))

lines = [f"{len(d):,} measurements, 10 DOI folds",
         f"probabilities: Pearson r {pearsonr(d.prob_lg, d.prob_dn)[0]:.2f}, Spearman rho {spearmanr(d.prob_lg, d.prob_dn)[0]:.2f}",
         "ROC-AUC (mean over folds; paired t-test against LightGBM):"]
for k, v in auc.items():
    lines.append(f"  {k:<16} {np.mean(v):.3f}" + ("" if k == "LightGBM" else f"   P = {ttest_rel(v, auc['LightGBM']).pvalue:.2f}"))
lines.append("Rules (each model flags the toxic fraction of the training folds): precision / recall / bal. acc. / flagged")
for k, v in rules.items():
    m = np.mean(v, axis=0)
    lines.append(f"  {k:<10} {m[0]:.2f} / {m[1]:.2f} / {m[2]:.3f} / {m[3]:.0%}")
txt = "\n".join(lines)
(HERE / "consensus_summary.txt").write_text(txt + "\n", encoding="utf-8")
print(txt)

fig, axes = plt.subplots(1, 2, figsize=(150 * MM, 68 * MM))
for ax, (xc, yc, lab, lim) in zip(axes, (("prob_lg", "prob_dn", "Predicted probability", (0, 1)),
                                         ("rk_lg", "rk_dn", "Rank within the test fold (0–1)", (0, 1)))):
    for yv, col, name in ((0, NON, "non-toxic"), (1, TOX, "toxic")):
        s = d[d.y == yv]
        ax.scatter(s[xc], s[yc], s=1.5, color=col, alpha=0.30, linewidths=0, rasterized=True,
                   label=f"{name} (n = {len(s):,})")
    ax.plot(lim, lim, ls="--", lw=0.6, color="#999999")
    ax.set_xlim(lim); ax.set_ylim(lim); ax.set_aspect("equal")
    ax.set_xlabel(f"LightGBM (2D), {lab.lower()}"); ax.set_ylabel(f"DimeNet++ (3D), {lab.lower()}")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
axes[0].legend(loc="upper left", frameon=False, fontsize=6, markerscale=4, handletextpad=0.2)
axes[0].text(0.0, 1.03, "a", transform=axes[0].transAxes, fontsize=8, fontweight="bold")
axes[1].text(0.0, 1.03, "b", transform=axes[1].transAxes, fontsize=8, fontweight="bold")
axes[0].set_title(f"r = {pearsonr(d.prob_lg, d.prob_dn)[0]:.2f}", fontsize=6.5, loc="right")
axes[1].set_title(f"ρ = {spearmanr(d.prob_lg, d.prob_dn)[0]:.2f}", fontsize=6.5, loc="right")
fig.tight_layout()
for ext in ("png", "svg", "pdf"):
    fig.savefig(HERE / f"prob_parity_2d_3d.{ext}", dpi=600 if ext == "png" else None)
