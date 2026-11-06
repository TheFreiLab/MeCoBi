"""LightGBM reproduction of the Ru cytotoxicity classifier (article milestone 1).

Faithful reproduction of Krasnov et al. (J. Med. Chem. 2026) Ru LightGBM classifier:
    - features: article baseline (ECFP4-sum + LogP/TPSA/MW + charge + exposure time + cell line)
    - 10-fold CV, DOI splitting (primary) or SMILES splitting, from the shared split manifests
    - Optuna hyperparameter optimisation, done NESTED inside each outer fold's training rows only
      (inner GroupKFold by the same group), so the outer validation fold is never seen during tuning
      or early stopping -> no leakage.
    - negative control: labels globally scrambled -> ROC-AUC should collapse to ~0.5

Published target (DOI split): ROC-AUC 0.810 +- 0.024, accuracy 0.773 +- 0.017. Being within the
+-0.024 band is success; bitwise reproduction is impossible (the authors' model/Optuna code is not
released, and molfeat/sklearn/lightgbm versions differ).

Usage:
    python src/train_lightgbm.py --scheme doi                 # primary
    python src/train_lightgbm.py --scheme doi --n-trials 40   # more tuning
    python src/train_lightgbm.py --scheme doi --no-optuna     # fast smoke run, fixed params
    python src/train_lightgbm.py --scheme doi --folds 0 1 2   # subset (match a reduced DimeNet run)
"""

from __future__ import annotations

import argparse
import json
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import lightgbm as lgb
import optuna
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
                             confusion_matrix, f1_score, roc_auc_score, roc_curve)
from sklearn.model_selection import GroupKFold

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_guard import guard_run  # noqa: E402
from feature_engineering import CONTEXT_HELP, feature_matrix, load_features, select_groups  # noqa: E402
from splitting import iter_folds  # noqa: E402

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent
DATASET = PROJECT_ROOT / "data" / "processed" / "ru_article.parquet"
SPLITS = PROJECT_ROOT / "splits"
REPORTDIR = PROJECT_ROOT / "results" / "reports"
TABLEDIR = PROJECT_ROOT / "results" / "tables"
FIGDIR = PROJECT_ROOT / "results" / "figures"

optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=r".*eval_set.*")  # lightgbm 4.7 wrapper deprecation
warnings.filterwarnings("ignore", category=FutureWarning)

# Sensible fixed params for the --no-optuna smoke run.
FIXED_PARAMS = dict(objective="binary", n_estimators=600, learning_rate=0.05, num_leaves=63,
                    max_depth=-1, min_child_samples=30, subsample=0.8,
                    colsample_bytree=0.8, reg_alpha=0.0, reg_lambda=1.0)
# n_jobs is set from --threads in main(). Do NOT use -1 here: with ~48 cores and the small
# per-fit datasets of the nested Optuna loop, LightGBM's thread-sync overhead dominates and the
# run gets catastrophically slower (48-thread thrash + contention with other jobs, e.g. ORCA).
BASE = dict(objective="binary", n_jobs=8, verbosity=-1, random_state=42, subsample_freq=1)


def suggest_params(trial: optuna.Trial) -> dict:
    return dict(
        learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        num_leaves=trial.suggest_int("num_leaves", 15, 255),
        max_depth=trial.suggest_int("max_depth", 3, 12),
        min_child_samples=trial.suggest_int("min_child_samples", 5, 100),
        subsample=trial.suggest_float("subsample", 0.6, 1.0),
        colsample_bytree=trial.suggest_float("colsample_bytree", 0.4, 1.0),
        reg_alpha=trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
        reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
    )


def _fit_es(params, Xtr, ytr, Xva, yva, max_rounds=2000):
    """Fit LightGBM with early stopping on (Xva, yva); return (model, best_iteration)."""
    model = lgb.LGBMClassifier(**BASE, **params, n_estimators=max_rounds)
    model.fit(Xtr, ytr, eval_set=[(Xva, yva)], eval_metric="auc",
              callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(0)])
    return model, model.best_iteration_ or max_rounds


def tune_fold(X, y, groups, tr_idx, n_trials, inner_splits, seed):
    """Optuna over inner GroupKFold on the outer-train rows. Returns (best_params, n_estimators)."""
    inner = GroupKFold(n_splits=inner_splits)
    inner_splits_list = list(inner.split(tr_idx, y[tr_idx], groups[tr_idx]))

    def objective(trial):
        params = suggest_params(trial)
        aucs, iters = [], []
        for itr, iva in inner_splits_list:
            a, b = tr_idx[itr], tr_idx[iva]
            model, best_it = _fit_es(params, X[a], y[a], X[b], y[b])
            aucs.append(roc_auc_score(y[b], model.predict_proba(X[b])[:, 1]))
            iters.append(best_it)
        trial.set_user_attr("mean_iter", int(np.mean(iters)))
        return float(np.mean(aucs))

    study = optuna.create_study(direction="maximize",
                                sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    best = study.best_params
    n_est = max(50, int(study.best_trial.user_attrs["mean_iter"]))
    return best, n_est


def run_cv(X, y, groups, manifest, folds, n_trials, inner_splits, seed, use_optuna):
    """Return per-fold metrics, OOF predictions, and per-fold best params."""
    oof_prob = np.full(len(y), np.nan)
    oof_fold = np.full(len(y), -1)
    rows, best_params = [], {}

    for k, tr, va in iter_folds(manifest, only=folds):
        t0 = time.time()
        if use_optuna:
            params, n_est = tune_fold(X, y, groups, tr, n_trials, inner_splits, seed)
        else:
            params = {kk: v for kk, v in FIXED_PARAMS.items()
                      if kk not in ("objective", "n_estimators")}
            n_est = FIXED_PARAMS["n_estimators"]
        model = lgb.LGBMClassifier(**BASE, **params, n_estimators=n_est)
        model.fit(X[tr], y[tr])
        prob = model.predict_proba(X[va])[:, 1]
        pred = (prob >= 0.5).astype(int)
        oof_prob[va], oof_fold[va] = prob, k

        m = dict(
            fold=k, n_train=len(tr), n_val=len(va),
            roc_auc=roc_auc_score(y[va], prob),
            pr_auc=average_precision_score(y[va], prob),
            accuracy=accuracy_score(y[va], pred),
            balanced_accuracy=balanced_accuracy_score(y[va], pred),
            f1=f1_score(y[va], pred, zero_division=0),
            n_estimators=n_est, seconds=round(time.time() - t0, 1),
        )
        rows.append(m)
        best_params[str(k)] = {"params": params, "n_estimators": n_est}
        print(f"  fold {k}: ROC-AUC={m['roc_auc']:.3f} acc={m['accuracy']:.3f} "
              f"({m['seconds']:.0f}s, n_est={n_est})")

    return pd.DataFrame(rows), oof_prob, oof_fold, best_params


def aggregate(dfm: pd.DataFrame) -> dict:
    out = {}
    for col in ["roc_auc", "pr_auc", "accuracy", "balanced_accuracy", "f1"]:
        out[col] = {"mean": round(float(dfm[col].mean()), 4),
                    "std": round(float(dfm[col].std(ddof=1)), 4)}
    return out


def save_figures(y, oof_prob, oof_fold, tag):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mask = oof_fold >= 0
    yv, pv = y[mask], oof_prob[mask]
    FIGDIR.mkdir(parents=True, exist_ok=True)

    fpr, tpr, _ = roc_curve(yv, pv)
    auc = roc_auc_score(yv, pv)
    plt.figure(figsize=(5, 5))
    plt.plot(fpr, tpr, label=f"pooled OOF (AUC={auc:.3f})")
    plt.plot([0, 1], [0, 1], "--", color="grey")
    plt.xlabel("False positive rate"); plt.ylabel("True positive rate")
    plt.title(f"LightGBM {tag} — ROC"); plt.legend(loc="lower right")
    plt.tight_layout(); plt.savefig(FIGDIR / f"lightgbm_{tag}_roc.png", dpi=140); plt.close()

    cm = confusion_matrix(yv, (pv >= 0.5).astype(int))
    plt.figure(figsize=(4, 4))
    plt.imshow(cm, cmap="Blues")
    for (i, j), v in np.ndenumerate(cm):
        plt.text(j, i, str(v), ha="center", va="center",
                 color="white" if v > cm.max() / 2 else "black")
    plt.xticks([0, 1], ["nontoxic", "toxic"]); plt.yticks([0, 1], ["nontoxic", "toxic"])
    plt.xlabel("predicted"); plt.ylabel("true"); plt.title(f"LightGBM {tag} — confusion")
    plt.tight_layout(); plt.savefig(FIGDIR / f"lightgbm_{tag}_confusion.png", dpi=140); plt.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scheme", choices=["doi", "smiles"], default="doi")
    ap.add_argument("--manifest", type=Path, default=None,
                    help="override split manifest (default splits/ru_<scheme>_10fold.json)")
    ap.add_argument("--folds", type=int, nargs="+", default=None,
                    help="subset of fold ids (default all)")
    ap.add_argument("--n-trials", type=int, default=25)
    ap.add_argument("--inner-splits", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-optuna", dest="optuna", action="store_false",
                    help="skip tuning, use fixed params (fast smoke run)")
    ap.add_argument("--negative-control", action="store_true",
                    help="scramble labels; expect ROC-AUC ~0.5")
    ap.add_argument("--context", nargs="+", default=None, metavar="GROUP",
                    help=CONTEXT_HELP)
    ap.add_argument("--features", type=Path, default=None, help="features parquet (multi-metal)")
    ap.add_argument("--report", type=Path, default=None, help="features report json (multi-metal)")
    ap.add_argument("--dataset", type=Path, default=DATASET, help="curated parquet (for groups)")
    ap.add_argument("--tag-suffix", default="", help="appended to output filenames (e.g. multimetal, lomo)")
    ap.add_argument("--overwrite", action="store_true",
                    help="allow overwriting existing result files of the same tag")
    ap.add_argument("--threads", type=int, default=8,
                    help="LightGBM n_jobs. Keep small (4-8): the nested-Optuna fits are on small "
                         "subsets, so many threads only add sync overhead (and fight other jobs).")
    args = ap.parse_args()

    BASE["n_jobs"] = args.threads

    manifest = args.manifest or SPLITS / f"ru_{args.scheme}_10fold.json"
    if not manifest.exists():
        raise SystemExit(f"Manifest not found: {manifest}\nRun src/splitting.py first.")

    feats, meta = load_features(args.features, args.report) if args.features else load_features()
    ds = pd.read_parquet(args.dataset)
    assert feats["row_id"].tolist() == ds["row_id"].tolist(), "feature/dataset row order mismatch"

    ctx_groups = select_groups(meta, args.context)
    X, _cols = feature_matrix(feats, meta, ctx_groups)
    print(f"[context] feature groups: {ctx_groups}", flush=True)
    y = feats["y"].to_numpy().astype(int)
    group_col = json.loads(manifest.read_text(encoding="utf-8"))["group_col"]
    groups = ds[group_col].to_numpy()

    if args.negative_control:
        rng = np.random.default_rng(args.seed)
        y = rng.permutation(y)

    tag = args.scheme + ("_negctrl" if args.negative_control else "") + (f"_{args.tag_suffix}" if args.tag_suffix else "")
    guard_run(args, default_dataset=DATASET,
              default_manifest=SPLITS / f"ru_{args.scheme}_10fold.json",
              outputs=[REPORTDIR / f"lightgbm_{tag}_metrics.json",
                       TABLEDIR / f"lightgbm_{tag}_oof.csv"])
    print(f"[LightGBM] scheme={args.scheme} optuna={args.optuna} trials={args.n_trials} "
          f"negctrl={args.negative_control}")
    print(f"[data] X={X.shape} pos_frac={y.mean():.3f} groups={pd.unique(groups).size} "
          f"({group_col})")

    t0 = time.time()
    dfm, oof_prob, oof_fold, best_params = run_cv(
        X, y, groups, manifest, args.folds, args.n_trials, args.inner_splits,
        args.seed, args.optuna)
    agg = aggregate(dfm)

    # Baselines
    maj = max(np.bincount(y)) / len(y)
    report = {
        "model": "LightGBM", "scheme": args.scheme, "negative_control": args.negative_control,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "context_groups": ctx_groups,
        "config": {"optuna": args.optuna, "n_trials": args.n_trials,
                   "inner_splits": args.inner_splits, "seed": args.seed,
                   "folds": args.folds or "all", "lightgbm": lgb.__version__},
        "ecfp_backend": meta["ecfp_backend"],
        "class_distribution": {int(k): int(v) for k, v in zip(*np.unique(y, return_counts=True))},
        "baseline_majority_accuracy": round(float(maj), 4),
        "per_fold": dfm.to_dict("records"),
        "aggregate": agg,
        # The published target is Ru-only (23 lines, no Au). It is NOT comparable to a multi-metal
        # or any other --tag-suffix run (different dataset), so only attach it to the plain Ru repro.
        "published_target": {"roc_auc": "0.810 +- 0.024", "accuracy": "0.773 +- 0.017"}
        if args.scheme == "doi" and not args.negative_control and not args.tag_suffix else None,
        "total_seconds": round(time.time() - t0, 1),
    }

    REPORTDIR.mkdir(parents=True, exist_ok=True)
    TABLEDIR.mkdir(parents=True, exist_ok=True)
    (REPORTDIR / f"lightgbm_{tag}_metrics.json").write_text(json.dumps(report, indent=2),
                                                            encoding="utf-8")
    (REPORTDIR / f"lightgbm_{tag}_best_params.json").write_text(
        json.dumps(best_params, indent=2), encoding="utf-8")
    oof = pd.DataFrame({"row_id": feats["row_id"], "complex_id": feats["complex_id"],
                        "y": y, "prob": oof_prob, "fold": oof_fold})
    oof[oof.fold >= 0].to_csv(TABLEDIR / f"lightgbm_{tag}_oof.csv", index=False)
    save_figures(y, oof_prob, oof_fold, tag)

    print(f"\n=== LightGBM {tag} — {len(dfm)} folds ===")
    print(f"ROC-AUC  {agg['roc_auc']['mean']:.3f} +- {agg['roc_auc']['std']:.3f}")
    print(f"Accuracy {agg['accuracy']['mean']:.3f} +- {agg['accuracy']['std']:.3f}")
    print(f"PR-AUC   {agg['pr_auc']['mean']:.3f}   F1 {agg['f1']['mean']:.3f}   "
          f"bal-acc {agg['balanced_accuracy']['mean']:.3f}")
    print(f"majority-class accuracy baseline: {maj:.3f}")
    if report["published_target"]:
        print(f"published target: ROC-AUC {report['published_target']['roc_auc']}, "
              f"accuracy {report['published_target']['accuracy']}")
    print(f"[written] {REPORTDIR / f'lightgbm_{tag}_metrics.json'}")
    print(f"total: {report['total_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
