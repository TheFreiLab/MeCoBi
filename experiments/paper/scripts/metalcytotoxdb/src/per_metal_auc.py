"""Per-metal ROC-AUC breakdown of a multimetal 10CV run (no retraining).

Krasnov et al. (jm5c02755) report the multimetal model's 10CV ROC-AUC *per scarce-metal subset*
(Rh/Os/Re, 0.727-0.789), not as a single pooled number, and the LOMO transferability separately
(Rh 0.643, Re 0.658, Os 0.767). This reproduces the 10CV-per-metal view by joining the metal onto an
existing out-of-fold prediction file, so our combined model can be compared to their Figure 9b -- and
extended to Au/Ir, which their study did not report.

Two ROC-AUC estimates per metal:
    pooled     -- one AUC over all that metal's OOF rows (matches "10CV ROC-AUC on the subset")
    per-fold   -- mean +- s.d. of the AUC computed within each fold's rows of that metal
                  (only folds with both classes present are used; some scarce metals may skip folds)

Usage:
    python src/per_metal_auc.py --dataset data/processed/multimetal.parquet \
        --oof results/tables/lightgbm_doi_multimetal_oof.csv \
        --oof results/tables/mlp_doi_multimetal_oof.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent
DEFAULT_DATASET = PROJECT_ROOT / "data" / "processed" / "multimetal.parquet"


def _label(oof_path: Path) -> str:
    """lightgbm_doi_multimetal_oof.csv -> LightGBM ; mlp_... -> MLP ; else the stem."""
    stem = oof_path.stem.lower()
    if stem.startswith("lightgbm"):
        return "LightGBM"
    if stem.startswith("mlp"):
        return "MLP"
    if stem.startswith("dimenet"):
        return "DimeNet++"
    return oof_path.stem


def _safe_auc(y, p) -> float | None:
    y = np.asarray(y)
    if len(np.unique(y)) < 2:
        return None
    return float(roc_auc_score(y, p))


def per_metal(oof: pd.DataFrame, row_metal: pd.Series) -> pd.DataFrame:
    df = oof.copy()
    df["Metal"] = df["row_id"].map(row_metal)
    if df["Metal"].isna().any():
        n = int(df["Metal"].isna().sum())
        raise SystemExit(f"{n} OOF rows had no matching row_id in the dataset -- wrong parquet?")

    rows = []
    for metal, g in df.groupby("Metal"):
        pooled = _safe_auc(g["y"], g["prob"])
        fold_aucs = [a for _, fg in g.groupby("fold")
                     if (a := _safe_auc(fg["y"], fg["prob"])) is not None]
        rows.append({
            "Metal": metal,
            "n_rows": int(len(g)),
            "n_complexes": int(g["complex_id"].nunique()),
            "toxic_frac": round(float(g["y"].mean()), 3),
            "auc_pooled": round(pooled, 4) if pooled is not None else None,
            "auc_perfold_mean": round(float(np.mean(fold_aucs)), 4) if fold_aucs else None,
            "auc_perfold_std": round(float(np.std(fold_aucs, ddof=1)), 4) if len(fold_aucs) > 1 else None,
            "n_folds_scored": len(fold_aucs),
        })
    # overall (all metals pooled) for reference
    allp = _safe_auc(df["y"], df["prob"])
    rows.append({"Metal": "ALL", "n_rows": int(len(df)),
                 "n_complexes": int(df["complex_id"].nunique()),
                 "toxic_frac": round(float(df["y"].mean()), 3),
                 "auc_pooled": round(allp, 4) if allp is not None else None,
                 "auc_perfold_mean": None, "auc_perfold_std": None, "n_folds_scored": 0})
    out = pd.DataFrame(rows)
    # order scarce -> abundant so it reads like Krasnov's Re/Os/Rh emphasis, ALL last
    order = out[out.Metal != "ALL"].sort_values("n_rows")["Metal"].tolist() + ["ALL"]
    return out.set_index("Metal").loc[order].reset_index()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", type=Path, default=DEFAULT_DATASET,
                    help="curated multimetal parquet (must have row_id + Metal)")
    ap.add_argument("--oof", type=Path, action="append", required=True,
                    help="OOF csv (repeatable) with row_id/complex_id/y/prob/fold")
    ap.add_argument("--out", type=Path, default=None,
                    help="optional CSV to write the combined table to")
    args = ap.parse_args()

    ds = pd.read_parquet(args.dataset, columns=["row_id", "Metal"])
    row_metal = ds.set_index("row_id")["Metal"]

    tables = []
    for oof_path in args.oof:
        oof = pd.read_csv(oof_path)
        tbl = per_metal(oof, row_metal)
        model = _label(oof_path)
        tbl.insert(0, "model", model)
        tables.append(tbl)

        print(f"\n=== {model}  ({oof_path.name}) ===")
        print("metal   rows   cplx   tox    AUC(pool)   AUC(fold mean+-sd)   folds")
        for r in tbl.itertuples(index=False):
            pf = (f"{r.auc_perfold_mean:.3f} +- {r.auc_perfold_std:.3f}"
                  if r.auc_perfold_mean is not None and r.auc_perfold_std is not None
                  else (f"{r.auc_perfold_mean:.3f}" if r.auc_perfold_mean is not None else "   -"))
            pool = f"{r.auc_pooled:.3f}" if r.auc_pooled is not None else "  -"
            print(f"{r.Metal:<6} {r.n_rows:>5} {r.n_complexes:>5} {r.toxic_frac:>5.2f}   "
                  f"{pool:>8}    {pf:<18} {r.n_folds_scored:>4}")

    combined = pd.concat(tables, ignore_index=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(args.out, index=False)
        print(f"\n[written] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
