"""MLP control (Model 2): a fair neural baseline on the SAME 2D features and folds as LightGBM.

Purpose: separate "neural net vs gradient boosting" from "3D vs 2D". If DimeNet++ later beats
LightGBM, this MLP tells us whether that is just because it is a neural network on the same 2D
information. So it uses the EXACT article-baseline features (ECFP4-sum + LogP/TPSA/MW + charge +
exposure time + cell line) and the EXACT shared DOI folds.

Design (deliberately modest, per the brief):
    - continuous features (LogP/TPSA/MW/charge/exposure time) StandardScaler'd per-fold, fit on the
      outer-train rows only; ECFP counts and cell-line one-hot left as-is.
    - inner grouped validation carved from outer-train (same group key) for early stopping; the outer
      validation fold is never used for tuning/stopping/threshold.
    - class imbalance (30.9% toxic) handled with BCEWithLogitsLoss pos_weight = n_neg/n_pos (train).
    - ROC-AUC uses raw predicted probabilities (no threshold tuning on the outer fold).

Usage:
    python src/train_mlp.py --scheme doi
    python src/train_mlp.py --scheme doi --folds 0 1 2      # match a reduced DimeNet++ run
    python src/train_mlp.py --scheme doi --negative-control # scrambled labels -> ~0.5
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
                             confusion_matrix, f1_score, roc_auc_score, roc_curve)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from run_guard import guard_run  # noqa: E402
from feature_engineering import CONTEXT_HELP, feature_matrix, load_features, select_groups  # noqa: E402
from splitting import iter_folds  # noqa: E402

PROJECT_ROOT = _HERE.parent
DATASET = PROJECT_ROOT / "data" / "processed" / "ru_article.parquet"
SPLITS = PROJECT_ROOT / "splits"
REPORTDIR = PROJECT_ROOT / "results" / "reports"
TABLEDIR = PROJECT_ROOT / "results" / "tables"
FIGDIR = PROJECT_ROOT / "results" / "figures"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class MLP(nn.Module):
    def __init__(self, in_dim: int, hidden: tuple[int, ...], p: float):
        super().__init__()
        layers: list[nn.Module] = []
        d = in_dim
        for h in hidden:
            layers += [nn.Linear(d, h), nn.BatchNorm1d(h), nn.ReLU(), nn.Dropout(p)]
            d = h
        layers += [nn.Linear(d, 1)]
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x).squeeze(-1)


def set_seed(seed: int):
    np.random.seed(seed)
    torch.manual_seed(seed)


def train_one(Xtr, ytr, Xiv, yiv, in_dim, args) -> MLP:
    """Train with early stopping on inner-val ROC-AUC; return the best-state model."""
    model = MLP(in_dim, tuple(args.hidden), args.dropout).to(DEVICE)
    pos_weight = torch.tensor([(ytr == 0).sum() / max(1, (ytr == 1).sum())],
                              dtype=torch.float32, device=DEVICE)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    Xtr_t = torch.tensor(Xtr, dtype=torch.float32, device=DEVICE)
    ytr_t = torch.tensor(ytr, dtype=torch.float32, device=DEVICE)
    Xiv_t = torch.tensor(Xiv, dtype=torch.float32, device=DEVICE)
    n = len(Xtr_t)

    best_auc, best_state, bad = -1.0, None, 0
    for _epoch in range(args.epochs):
        model.train()
        perm = torch.randperm(n, device=DEVICE)
        for i in range(0, n, args.batch_size):
            b = perm[i:i + args.batch_size]
            opt.zero_grad()
            loss = loss_fn(model(Xtr_t[b]), ytr_t[b])
            loss.backward()
            opt.step()

        model.eval()
        with torch.no_grad():
            piv = torch.sigmoid(model(Xiv_t)).cpu().numpy()
        auc = roc_auc_score(yiv, piv) if len(np.unique(yiv)) > 1 else 0.5
        if auc > best_auc + 1e-4:
            best_auc, best_state, bad = auc, {k: v.detach().clone()
                                              for k, v in model.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= args.patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model


def run_cv(X, y, groups, cont_idx, manifest, args):
    oof_prob = np.full(len(y), np.nan)
    oof_fold = np.full(len(y), -1)
    rows = []
    gss = GroupShuffleSplit(n_splits=1, test_size=args.inner_val_frac, random_state=args.seed)

    for k, tr, va in iter_folds(manifest, only=args.folds):
        t0 = time.time()
        set_seed(args.seed + k)
        # inner grouped split of the outer-train rows for early stopping
        itr_rel, iiv_rel = next(gss.split(tr, y[tr], groups[tr]))
        itr, iiv = tr[itr_rel], tr[iiv_rel]

        Xs = X.copy()
        if cont_idx:   # --context may leave no continuous column to scale
            scaler = StandardScaler().fit(X[itr][:, cont_idx])
            Xs[:, cont_idx] = scaler.transform(X[:, cont_idx])

        # deep-ensemble over seeds (same fold/split/scaling; only init + batch order vary)
        Xva_t = torch.tensor(Xs[va], dtype=torch.float32, device=DEVICE)
        seed_probs, seed_aucs = [], []
        for s in range(args.n_seeds):
            set_seed(args.seed + k * 1000 + s)
            model = train_one(Xs[itr], y[itr], Xs[iiv], y[iiv], X.shape[1], args)
            model.eval()
            with torch.no_grad():
                p = torch.sigmoid(model(Xva_t)).cpu().numpy()
            seed_probs.append(p)
            seed_aucs.append(roc_auc_score(y[va], p))
        prob = np.mean(seed_probs, axis=0)
        pred = (prob >= 0.5).astype(int)
        oof_prob[va], oof_fold[va] = prob, k

        m = dict(fold=k, n_train=len(itr), n_inner_val=len(iiv), n_val=len(va),
                 roc_auc=roc_auc_score(y[va], prob),
                 seed_auc_mean=round(float(np.mean(seed_aucs)), 4),
                 seed_auc_std=round(float(np.std(seed_aucs, ddof=1)) if args.n_seeds > 1 else 0.0, 4),
                 pr_auc=average_precision_score(y[va], prob),
                 accuracy=accuracy_score(y[va], pred),
                 balanced_accuracy=balanced_accuracy_score(y[va], pred),
                 f1=f1_score(y[va], pred, zero_division=0),
                 seconds=round(time.time() - t0, 1))
        rows.append(m)
        sstr = (f" | per-seed {m['seed_auc_mean']:.3f}±{m['seed_auc_std']:.3f}"
                if args.n_seeds > 1 else "")
        print(f"  fold {k}: ROC-AUC={m['roc_auc']:.3f} acc={m['accuracy']:.3f} "
              f"({m['seconds']:.0f}s){sstr}")
    return pd.DataFrame(rows), oof_prob, oof_fold


def aggregate(dfm):
    return {c: {"mean": round(float(dfm[c].mean()), 4), "std": round(float(dfm[c].std(ddof=1)), 4)}
            for c in ["roc_auc", "pr_auc", "accuracy", "balanced_accuracy", "f1"]}


def save_figures(y, oof_prob, oof_fold, tag):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    mask = oof_fold >= 0
    yv, pv = y[mask], oof_prob[mask]
    FIGDIR.mkdir(parents=True, exist_ok=True)

    fpr, tpr, _ = roc_curve(yv, pv)
    plt.figure(figsize=(5, 5))
    plt.plot(fpr, tpr, label=f"pooled OOF (AUC={roc_auc_score(yv, pv):.3f})")
    plt.plot([0, 1], [0, 1], "--", color="grey")
    plt.xlabel("False positive rate"); plt.ylabel("True positive rate")
    plt.title(f"MLP {tag} — ROC"); plt.legend(loc="lower right")
    plt.tight_layout(); plt.savefig(FIGDIR / f"mlp_{tag}_roc.png", dpi=140); plt.close()

    cm = confusion_matrix(yv, (pv >= 0.5).astype(int))
    plt.figure(figsize=(4, 4))
    plt.imshow(cm, cmap="Blues")
    for (i, j), v in np.ndenumerate(cm):
        plt.text(j, i, str(v), ha="center", va="center",
                 color="white" if v > cm.max() / 2 else "black")
    plt.xticks([0, 1], ["nontoxic", "toxic"]); plt.yticks([0, 1], ["nontoxic", "toxic"])
    plt.xlabel("predicted"); plt.ylabel("true"); plt.title(f"MLP {tag} — confusion")
    plt.tight_layout(); plt.savefig(FIGDIR / f"mlp_{tag}_confusion.png", dpi=140); plt.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scheme", choices=["doi", "smiles"], default="doi")
    ap.add_argument("--manifest", type=Path, default=None)
    ap.add_argument("--folds", type=int, nargs="+", default=None)
    ap.add_argument("--hidden", type=int, nargs="+", default=[512, 128])
    ap.add_argument("--dropout", type=float, default=0.3)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--weight-decay", type=float, default=1e-5)
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--epochs", type=int, default=200)
    ap.add_argument("--patience", type=int, default=15)
    ap.add_argument("--inner-val-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-seeds", type=int, default=1,
                    help="deep-ensemble size: models per fold, probs averaged; >1 reports per-seed spread")
    ap.add_argument("--negative-control", action="store_true")
    ap.add_argument("--context", nargs="+", default=None, metavar="GROUP",
                    help=CONTEXT_HELP)
    ap.add_argument("--features", type=Path, default=None, help="features parquet (multi-metal)")
    ap.add_argument("--report", type=Path, default=None, help="features report json (multi-metal)")
    ap.add_argument("--dataset", type=Path, default=DATASET, help="curated parquet (for groups)")
    ap.add_argument("--tag-suffix", default="", help="appended to output filenames (e.g. multimetal, lomo)")
    ap.add_argument("--overwrite", action="store_true",
                    help="allow overwriting existing result files of the same tag")
    args = ap.parse_args()

    manifest = args.manifest or SPLITS / f"ru_{args.scheme}_10fold.json"
    if not manifest.exists():
        raise SystemExit(f"Manifest not found: {manifest}\nRun src/splitting.py first.")

    feats, meta = load_features(args.features, args.report) if args.features else load_features()
    ds = pd.read_parquet(args.dataset)
    assert feats["row_id"].tolist() == ds["row_id"].tolist(), "feature/dataset row mismatch"

    ctx_groups = select_groups(meta, args.context)
    X, cols = feature_matrix(feats, meta, ctx_groups)
    print(f"[context] feature groups: {ctx_groups}", flush=True)
    y = feats["y"].to_numpy().astype(int)
    cont_names = (meta["feature_groups"]["descriptors"] + ["formal_charge", "exposure_time_h"]
                  + meta["feature_groups"].get("metal", []))  # metal descriptors in multi-metal
    cont_names = [c for c in cont_names if c in cols]   # a dropped group has nothing to scale
    cont_idx = [cols.index(c) for c in cont_names]
    group_col = json.loads(manifest.read_text(encoding="utf-8"))["group_col"]
    groups = ds[group_col].to_numpy()

    if args.negative_control:
        y = np.random.default_rng(args.seed).permutation(y)

    tag = args.scheme + ("_negctrl" if args.negative_control else "") + (f"_{args.tag_suffix}" if args.tag_suffix else "")
    guard_run(args, default_dataset=DATASET,
              default_manifest=SPLITS / f"ru_{args.scheme}_10fold.json",
              outputs=[REPORTDIR / f"mlp_{tag}_metrics.json",
                       TABLEDIR / f"mlp_{tag}_oof.csv"])
    print(f"[MLP] device={DEVICE} scheme={args.scheme} hidden={args.hidden} "
          f"negctrl={args.negative_control}")
    print(f"[data] X={X.shape} pos_frac={y.mean():.3f} scaled_cont={cont_names}")

    t0 = time.time()
    dfm, oof_prob, oof_fold = run_cv(X, y, groups, cont_idx, manifest, args)
    agg = aggregate(dfm)
    maj = max(np.bincount(y)) / len(y)

    report = {
        "model": "MLP", "scheme": args.scheme, "negative_control": args.negative_control,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "context_groups": ctx_groups,
        "device": str(DEVICE),
        "config": {"hidden": args.hidden, "dropout": args.dropout, "lr": args.lr,
                   "weight_decay": args.weight_decay, "batch_size": args.batch_size,
                   "epochs": args.epochs, "patience": args.patience,
                   "inner_val_frac": args.inner_val_frac, "seed": args.seed,
                   "folds": args.folds or "all", "torch": torch.__version__},
        "ecfp_backend": meta["ecfp_backend"],
        "class_distribution": {int(k): int(v) for k, v in zip(*np.unique(y, return_counts=True))},
        "baseline_majority_accuracy": round(float(maj), 4),
        "per_fold": dfm.to_dict("records"), "aggregate": agg,
        # Ru-only reference (23 lines, no Au); not comparable to a --tag-suffix run's dataset.
        "reference_lightgbm_doi": {"roc_auc": "0.810 +- 0.041 (this repro)"} if not args.tag_suffix else None,
        "total_seconds": round(time.time() - t0, 1),
    }
    REPORTDIR.mkdir(parents=True, exist_ok=True); TABLEDIR.mkdir(parents=True, exist_ok=True)
    (REPORTDIR / f"mlp_{tag}_metrics.json").write_text(json.dumps(report, indent=2),
                                                       encoding="utf-8")
    oof = pd.DataFrame({"row_id": feats["row_id"], "complex_id": feats["complex_id"],
                        "y": y, "prob": oof_prob, "fold": oof_fold})
    oof[oof.fold >= 0].to_csv(TABLEDIR / f"mlp_{tag}_oof.csv", index=False)
    save_figures(y, oof_prob, oof_fold, tag)

    print(f"\n=== MLP {tag} — {len(dfm)} folds ===")
    print(f"ROC-AUC  {agg['roc_auc']['mean']:.3f} +- {agg['roc_auc']['std']:.3f}")
    print(f"Accuracy {agg['accuracy']['mean']:.3f} +- {agg['accuracy']['std']:.3f}")
    print(f"PR-AUC   {agg['pr_auc']['mean']:.3f}   F1 {agg['f1']['mean']:.3f}   "
          f"bal-acc {agg['balanced_accuracy']['mean']:.3f}")
    print(f"majority-class accuracy baseline: {maj:.3f}")
    if not args.tag_suffix:
        print(f"(reference LightGBM DOI ROC-AUC 0.810 +- 0.041)")
    print(f"total: {report['total_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
