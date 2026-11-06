"""Persistent 10-fold split manifests for the Ru article reproduction.

Builds ONE source-of-truth set of folds that every model (LightGBM, MLP, DimeNet++) must reuse,
so the 2D-vs-3D comparison is controlled at the split level. Two schemes, both from the paper:

    doi     GroupKFold by DOI  -- all rows of a publication go to exactly one fold. This is the
            paper's rigorous/primary metric (target ROC-AUC ~0.810 +- 0.024).
    smiles  GroupKFold by complex -- the same complex never spans train and val, but complexes
            from one DOI can. This is the leakier split the paper also reports (~0.894).

Group cross-validators here are sklearn's; plain GroupKFold is deterministic (no shuffle), which
is why it reproduces without a seed. --stratified switches to StratifiedGroupKFold (shuffled,
seeded) to keep class balance across folds while preserving group separation -- a documented
deviation, since the paper does not specify which it used.

Storage: each fold stores only its VALIDATION row indices (0-based into ru_article.parquet's fixed
row order); train = all rows minus val. This guarantees train/val are an exact partition and keeps
the JSON small. Rich per-fold metadata (group ids in val, class balance, counts) is recorded for
the reproducibility report.

DimeNet++ note: do NOT create a reduced split. Run a SUBSET of these same fold ids (e.g. 0,1,2)
and compare the other models on the SAME subset. `iter_folds(..., only=[0,1,2])` supports this.

Usage:
    python src/splitting.py                         # doi + smiles, 10-fold GroupKFold
    python src/splitting.py --stratified            # StratifiedGroupKFold (seeded)
    python src/splitting.py --n-splits 5 --tag 5fold # a separate 5-fold manifest, if ever needed
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent
DEFAULT_DATASET = PROJECT_ROOT / "data" / "processed" / "ru_article.parquet"
DEFAULT_SPLITDIR = PROJECT_ROOT / "splits"

# scheme name -> column that defines the group (no shared group may cross the train/val line)
SCHEME_GROUP_COL = {"doi": "DOI", "smiles": "complex_id"}


def _class_counts(y: np.ndarray) -> dict[int, int]:
    vals, cnts = np.unique(y, return_counts=True)
    return {int(v): int(c) for v, c in zip(vals, cnts)}


def build_scheme(df: pd.DataFrame, scheme: str, n_splits: int, stratified: bool,
                 seed: int) -> dict:
    """Build one CV scheme; return a JSON-serialisable manifest dict."""
    group_col = SCHEME_GROUP_COL[scheme]
    groups = df[group_col].to_numpy()
    y = df["y"].to_numpy()
    n = len(df)
    idx = np.arange(n)

    if stratified:
        splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        split_iter = splitter.split(idx, y, groups)
        cv_name = "StratifiedGroupKFold"
    else:
        splitter = GroupKFold(n_splits=n_splits)
        split_iter = splitter.split(idx, y, groups)
        cv_name = "GroupKFold"

    folds = []
    seen_val = np.zeros(n, dtype=bool)
    for k, (tr, va) in enumerate(split_iter):
        # integrity: no group shared between train and val
        shared = set(groups[tr]) & set(groups[va])
        assert not shared, f"{scheme} fold {k}: {len(shared)} groups leak across train/val"
        seen_val[va] = True
        folds.append({
            "fold": k,
            "n_train": int(len(tr)),
            "n_val": int(len(va)),
            "n_val_groups": int(len(set(groups[va]))),
            "n_val_complexes": int(df.iloc[va]["complex_id"].nunique()),
            "train_class": _class_counts(y[tr]),
            "val_class": _class_counts(y[va]),
            "val_toxic_frac": round(float(y[va].mean()), 4),
            "val_rows": va.tolist(),  # 0-based indices into the frozen parquet
        })

    # integrity: the val sets are an exact partition of all rows
    assert seen_val.all(), f"{scheme}: some rows never appear in any validation fold"
    assert sum(f["n_val"] for f in folds) == n, f"{scheme}: val rows do not sum to {n}"

    return {
        "scheme": scheme,
        "group_col": group_col,
        "cv": cv_name,
        "n_splits": n_splits,
        "seed": seed if stratified else None,
        "n_rows": n,
        "n_groups": int(pd.unique(groups).size),
        "folds": folds,
    }


def iter_folds(manifest_path: Path, only: list[int] | None = None):
    """Yield (fold_index, train_idx, val_idx) for a manifest. Train = complement of val.

    `only` restricts to a subset of fold ids (use for a reduced DimeNet++ run on the SAME folds).
    """
    man = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    n = man["n_rows"]
    allidx = np.arange(n)
    for f in man["folds"]:
        if only is not None and f["fold"] not in only:
            continue
        val = np.array(f["val_rows"], dtype=int)
        mask = np.ones(n, dtype=bool)
        mask[val] = False
        yield f["fold"], allidx[mask], val


def _summary_md(dataset: Path, manifests: dict[str, dict]) -> str:
    lines = [
        "# Split manifests — Ru article reproduction",
        "",
        f"- generated (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"- dataset: `{dataset}`",
        "",
    ]
    for scheme, man in manifests.items():
        lines += [
            f"## {scheme} — {man['cv']} ({man['n_splits']} folds)",
            f"- group column: `{man['group_col']}`  ·  groups: {man['n_groups']}  ·  "
            f"rows: {man['n_rows']}  ·  seed: {man['seed']}",
            "",
            "| fold | n_train | n_val | val groups | val complexes | val toxic frac |",
            "|---|---|---|---|---|---|",
        ]
        for f in man["folds"]:
            lines.append(
                f"| {f['fold']} | {f['n_train']} | {f['n_val']} | {f['n_val_groups']} | "
                f"{f['n_val_complexes']} | {f['val_toxic_frac']} |"
            )
        fracs = [f["val_toxic_frac"] for f in man["folds"]]
        lines += ["", f"- toxic-frac spread across folds: "
                       f"min {min(fracs):.3f} / max {max(fracs):.3f} "
                       f"(overall {sum(f['val_class'].get(1, 0) for f in man['folds']) / man['n_rows']:.3f})",
                  ""]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", type=Path, default=DEFAULT_DATASET,
                    help="frozen curated parquet (row order defines the indices)")
    ap.add_argument("--splitdir", type=Path, default=DEFAULT_SPLITDIR)
    ap.add_argument("--n-splits", type=int, default=10)
    ap.add_argument("--schemes", nargs="+", default=["doi", "smiles"],
                    choices=list(SCHEME_GROUP_COL))
    ap.add_argument("--stratified", action="store_true",
                    help="use StratifiedGroupKFold (seeded) instead of plain GroupKFold")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--prefix", default="ru", help="output filename prefix (e.g. 'multimetal')")
    ap.add_argument("--tag", default=None,
                    help="filename tag, e.g. '10fold' (default derives from n-splits)")
    args = ap.parse_args()

    if not args.dataset.exists():
        raise SystemExit(f"Dataset not found: {args.dataset}\nRun src/data_curation.py first.")

    df = pd.read_parquet(args.dataset)
    for col in ("y", "complex_id", "DOI"):
        if col not in df.columns:
            raise SystemExit(f"Dataset missing required column '{col}'")

    args.splitdir.mkdir(parents=True, exist_ok=True)
    tag = args.tag or f"{args.n_splits}fold"
    strat = "_strat" if args.stratified else ""

    manifests: dict[str, dict] = {}
    for scheme in args.schemes:
        man = build_scheme(df, scheme, args.n_splits, args.stratified, args.seed)
        manifests[scheme] = man
        out = args.splitdir / f"{args.prefix}_{scheme}_{tag}{strat}.json"
        out.write_text(json.dumps(man, indent=2), encoding="utf-8")
        print(f"[written] {out}  ({man['cv']}, {man['n_splits']} folds, "
              f"{man['n_groups']} {scheme}-groups)")

    (args.splitdir / f"{args.prefix}_splits_{tag}{strat}_report.md").write_text(
        _summary_md(args.dataset, manifests), encoding="utf-8"
    )
    print(_summary_md(args.dataset, manifests))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
