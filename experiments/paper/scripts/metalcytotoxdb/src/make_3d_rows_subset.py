"""Restrict the six-metal dataset to the measurements the 3D model was trained on.

Copy to ~/biometaldb-ml/ on Keisan and run there. It writes three files that the existing
training scripts accept unchanged, so LightGBM and the MLP can be retrained on exactly the
measurements and folds of the DimeNet++ run (structures that passed the filter):

    data/processed/multimetal_3drows.parquet            curated table, filtered
    data/processed/multimetal_3drows_features.parquet   features, filtered
    splits/multimetal_3drows_doi_10fold.json            same folds, row positions renumbered

    python make_3d_rows_subset.py \
        --oof results/tables/dimenet_doi_context_multimetal_xtb671_oof.csv

Then:
    python src/train_lightgbm.py --scheme doi --manifest splits/multimetal_3drows_doi_10fold.json \
        --features data/processed/multimetal_3drows_features.parquet \
        --report results/reports/multimetal_features_report.json \
        --dataset data/processed/multimetal_3drows.parquet --tag-suffix multimetal_3drows --threads 8
    python src/train_mlp.py --scheme doi --manifest splits/multimetal_3drows_doi_10fold.json \
        --features data/processed/multimetal_3drows_features.parquet \
        --report results/reports/multimetal_features_report.json \
        --dataset data/processed/multimetal_3drows.parquet --tag-suffix multimetal_3drows
(use the same extra options, such as --n-seeds, as in the original six-metal MLP run)
"""
import argparse
import json
from pathlib import Path

import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--oof", required=True, help="out-of-fold predictions of the 3D model (row_id, fold)")
ap.add_argument("--dataset", default="data/processed/multimetal.parquet")
ap.add_argument("--features", default="data/processed/multimetal_features.parquet")
ap.add_argument("--manifest", default="splits/multimetal_doi_10fold.json")
ap.add_argument("--tag", default="3drows")
ap.add_argument("--force", action="store_true")
a = ap.parse_args()

oof = pd.read_csv(a.oof).set_index("row_id")
ds, ft = pd.read_parquet(a.dataset), pd.read_parquet(a.features)
assert ds["row_id"].tolist() == ft["row_id"].tolist(), "dataset and features are not in the same order"
man = json.loads(Path(a.manifest).read_text(encoding="utf-8"))

# folds are those of the 3D run; the manifest must agree with them
man_fold = {}
for f in man["folds"]:
    for i in f["val_rows"]:
        man_fold[ds["row_id"].iloc[i]] = f["fold"]
fold_of = oof["fold"].to_dict()
bad = sum(man_fold.get(r) != k for r, k in fold_of.items())
if bad and not a.force:
    raise SystemExit(f"{bad} rows are in a different fold in the 3D run and in {a.manifest}: wrong manifest? "
                     "(--force uses the folds of the 3D run anyway)")

keep = ds["row_id"].isin(oof.index).to_numpy()
ds2, ft2 = ds[keep].reset_index(drop=True), ft[keep].reset_index(drop=True)
folds = []
for f in man["folds"]:
    rows = [int(i) for i in ds2.index[ds2["row_id"].map(fold_of) == f["fold"]]]
    y = ds2["y"].iloc[rows]
    folds.append({"fold": f["fold"], "n_train": len(ds2) - len(rows), "n_val": len(rows),
                  "val_class": {"0": int((y == 0).sum()), "1": int((y == 1).sum())}, "val_rows": rows})
man2 = {**{k: v for k, v in man.items() if k != "folds"}, "n_rows": len(ds2),
        "n_groups": int(ds2[man["group_col"]].nunique()), "folds": folds,
        "note": f"rows of {Path(a.oof).name}; folds unchanged, positions renumbered"}

stem = Path(a.dataset).stem
out_ds = Path(a.dataset).with_name(f"{stem}_{a.tag}.parquet")
out_ft = Path(a.dataset).with_name(f"{stem}_{a.tag}_features.parquet")
out_man = Path(a.manifest).with_name(f"{stem}_{a.tag}_doi_10fold.json")
ds2.to_parquet(out_ds, index=False)
ft2.to_parquet(out_ft, index=False)
out_man.write_text(json.dumps(man2), encoding="utf-8")
print(f"{len(ds2)} of {len(ds)} rows kept, {ds2['complex_id'].nunique()} complexes")
print("fold sizes:", [f["n_val"] for f in folds])
print("written:", out_ds, out_ft, out_man, sep="\n  ")
