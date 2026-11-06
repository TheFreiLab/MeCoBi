"""Article-baseline feature engineering for the Ru reproduction.

Reproduces the paper's ligand-based representation (Krasnov et al., J. Med. Chem. 2026):

    [ ECFP4 (2048, summed over ligands),
      Crippen LogP, TPSA, MW  (over the ligand combination),
      formal charge of the complex,
      exposure time (hours, RAW here; StandardScaler applied per-fold in training),
      cell line (one-hot) ]

ECFP: per-LIGAND ECFP4 (radius 2, 2048 bits) summed element-wise -> the complex fingerprint is the
"linear combination of its constituent ligands" (paper). Summing 0/1 ligand vectors yields per-bit
counts. Descriptors (LogP/TPSA/MW) are computed on the dot-joined multi-fragment mol, which is
additive and equals "the combination of all ligands". Formal charge is taken from the DB column
`Charge_complex` (authoritative), not recomputed.

Fingerprint backend: molfeat's FPCalculator("ecfp") if available (matches the paper's molfeat path);
otherwise RDKit's Morgan generator (radius 2, 2048 bits) -- functionally the same ECFP4. The backend
actually used is recorded in the feature report for reproducibility.

Scaling is intentionally NOT baked in: continuous columns are stored raw and scaled per training fold
(fit on train only) to avoid leakage. Trees ignore scaling; the MLP/DimeNet head scale via
`scale_continuous`. The SAME feature file feeds LightGBM, MLP, and the DimeNet++ context head.

Usage:
    python src/feature_engineering.py
Outputs:
    data/processed/ru_features.parquet          row-aligned features (+ row_id, complex_id, y)
    results/reports/ru_features_report.json      dims, feature groups, backend/version, failures
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ECFP_RADIUS = 2
ECFP_BITS = 2048

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent
DEFAULT_DATASET = PROJECT_ROOT / "data" / "processed" / "ru_article.parquet"
DEFAULT_OUT = PROJECT_ROOT / "data" / "processed" / "ru_features.parquet"
DEFAULT_REPORT = PROJECT_ROOT / "results" / "reports" / "ru_features_report.json"

# Columns scaled per-fold by neural models (fit on train only). Trees don't care.
CONTINUOUS_COLS = ["desc_logp", "desc_tpsa", "desc_mw", "exposure_time_h"]


# --------------------------------------------------------------------------------------
# Fingerprint backend (molfeat if present, else RDKit Morgan)
# --------------------------------------------------------------------------------------

def _make_ecfp_backend():
    """Return (fn(mol)->np.uint(2048,) bit vector, backend_description)."""
    try:
        import molfeat
        from molfeat.calc import FPCalculator
        calc = FPCalculator("ecfp", radius=ECFP_RADIUS, length=ECFP_BITS)

        def fp(mol):
            from rdkit import Chem
            return np.asarray(calc(Chem.MolToSmiles(mol)), dtype=np.int16)

        return fp, f"molfeat=={molfeat.__version__} FPCalculator(ecfp,r{ECFP_RADIUS},{ECFP_BITS})"
    except ImportError:
        from rdkit.Chem import rdFingerprintGenerator
        gen = rdFingerprintGenerator.GetMorganGenerator(radius=ECFP_RADIUS, fpSize=ECFP_BITS)

        def fp(mol):
            return gen.GetFingerprintAsNumPy(mol).astype(np.int16)

        import rdkit
        return fp, f"rdkit=={rdkit.__version__} MorganGenerator(r{ECFP_RADIUS},{ECFP_BITS})"


# --------------------------------------------------------------------------------------
# Per-complex features (computed once per unique complex, then broadcast to rows)
# --------------------------------------------------------------------------------------

def complex_features(smiles_ligands: str, ecfp_fn) -> tuple[np.ndarray, float, float, float, int]:
    """Return (ecfp_sum[2048], logp, tpsa, mw, n_ligand_parse_failures) for one complex."""
    from rdkit import Chem
    from rdkit.Chem import Descriptors

    ecfp = np.zeros(ECFP_BITS, dtype=np.int32)
    n_fail = 0
    for frag in str(smiles_ligands).split("."):
        frag = frag.strip()
        if not frag:
            continue
        mol = Chem.MolFromSmiles(frag)
        if mol is None:
            n_fail += 1
            continue
        ecfp += ecfp_fn(mol)

    # Descriptors on the whole ligand combination (additive; equals sum of per-ligand values).
    combined = Chem.MolFromSmiles(str(smiles_ligands))
    if combined is None:
        logp = tpsa = mw = np.nan
    else:
        logp = Descriptors.MolLogP(combined)   # Crippen LogP
        tpsa = Descriptors.TPSA(combined)
        mw = Descriptors.MolWt(combined)
    return ecfp, float(logp), float(tpsa), float(mw), n_fail


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")  # parse failures are tracked explicitly below

    ecfp_fn, backend = _make_ecfp_backend()

    # Compute once per unique complex (4,399), keyed on the raw SMILES string.
    uniq = df.drop_duplicates("SMILES_Ligands")[["SMILES_Ligands"]].reset_index(drop=True)
    ecfp_mat = np.zeros((len(uniq), ECFP_BITS), dtype=np.int32)
    logp = np.empty(len(uniq)); tpsa = np.empty(len(uniq)); mw = np.empty(len(uniq))
    lig_fail = 0
    desc_fail = 0
    for i, s in enumerate(uniq["SMILES_Ligands"]):
        e, lp, tp, m, nf = complex_features(s, ecfp_fn)
        ecfp_mat[i] = e
        logp[i], tpsa[i], mw[i] = lp, tp, m
        lig_fail += nf
        desc_fail += int(np.isnan(lp))

    ecfp_cols = [f"ecfp_{i}" for i in range(ECFP_BITS)]
    uniq_feat = pd.concat([
        uniq,
        pd.DataFrame(ecfp_mat, columns=ecfp_cols),
        pd.DataFrame({"desc_logp": logp, "desc_tpsa": tpsa, "desc_mw": mw}),
    ], axis=1)

    # Metal descriptors are added as features only when the set spans >1 metal (multi-metal
    # experiment); for the 2D baselines to tell metals apart. DimeNet++ gets the metal from the
    # graph instead, so it never uses these.
    metal_src = ["Atomic_number", "Valence_e", "Oxidation_state"]
    has_metal = ("Metal" in df.columns and df["Metal"].nunique() > 1
                 and all(c in df.columns for c in metal_src))

    # Broadcast per-complex features back to every measurement row.
    base = ["row_id", "complex_id", "SMILES_Ligands", "Charge_complex", "Cell_line", "Time(h)", "y"]
    if has_metal:
        base += metal_src
    out = df[base].merge(uniq_feat, on="SMILES_Ligands", how="left")

    out = out.rename(columns={"Charge_complex": "formal_charge", "Time(h)": "exposure_time_h"})
    out["formal_charge"] = out["formal_charge"].astype("int16")
    out["exposure_time_h"] = out["exposure_time_h"].astype("float32")
    if has_metal:
        out = out.rename(columns={"Atomic_number": "metal_atomic_number",
                                  "Valence_e": "metal_valence_e",
                                  "Oxidation_state": "metal_oxidation_state"})
        for c in ["metal_atomic_number", "metal_valence_e", "metal_oxidation_state"]:
            out[c] = out[c].astype("float32")

    # Cell line one-hot with a FIXED, sorted category order (stable across runs/splits).
    cell_categories = sorted(df["Cell_line"].unique())
    cl = pd.get_dummies(
        pd.Categorical(out["Cell_line"], categories=cell_categories),
        prefix="cl", dtype="int8",
    )
    out = pd.concat([out.drop(columns=["Cell_line", "SMILES_Ligands"]), cl], axis=1)

    feature_groups = {
        "ecfp": ecfp_cols,
        "descriptors": ["desc_logp", "desc_tpsa", "desc_mw"],
        "charge": ["formal_charge"],
        "exposure_time": ["exposure_time_h"],
        "cell_line": list(cl.columns),
    }
    metal_cols = ["metal_atomic_number", "metal_valence_e", "metal_oxidation_state"]
    if has_metal:
        feature_groups["metal"] = metal_cols
    continuous_cols = CONTINUOUS_COLS + (metal_cols if has_metal else [])
    meta = {
        "ecfp_backend": backend,
        "ecfp_radius": ECFP_RADIUS,
        "ecfp_bits": ECFP_BITS,
        "ecfp_combination": "sum of per-ligand ECFP4 bit vectors (per-bit counts)",
        "n_rows": int(len(out)),
        "n_feature_cols": int(sum(len(v) for v in feature_groups.values())),
        "feature_groups": feature_groups,
        "continuous_cols": continuous_cols,
        "has_metal_features": has_metal,
        "cell_line_categories": cell_categories,
        "ligand_parse_failures": int(lig_fail),
        "descriptor_parse_failures": int(desc_fail),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    return out, meta


# --------------------------------------------------------------------------------------
# Loading / per-fold scaling helpers (used by training scripts)
# --------------------------------------------------------------------------------------

def load_features(path: Path = DEFAULT_OUT, report: Path = DEFAULT_REPORT):
    """Return (features_df, meta_dict). Row order matches ru_article.parquet."""
    df = pd.read_parquet(path)
    meta = json.loads(Path(report).read_text(encoding="utf-8"))
    return df, meta


CONTEXT_HELP = ("feature groups the model sees: ecfp descriptors charge exposure_time cell_line "
                "[metal]. Default: everything the trainer used before (ablation: e.g. --context "
                "ecfp cell_line). Requires --tag-suffix so default outputs are not overwritten.")


def select_groups(meta: dict, requested=None, default=None) -> list[str]:
    """Validate ``--context`` against the groups present in this dataset, keep canonical order."""
    avail = list(meta["feature_groups"])
    if requested is None:
        return list(default) if default is not None else avail
    bad = [g for g in requested if g not in avail]
    if bad:
        raise SystemExit(f"--context: unknown group(s) {bad}; available: {avail}")
    if not requested:
        raise SystemExit("--context needs at least one group")
    return [g for g in avail if g in requested]


def feature_matrix(df: pd.DataFrame, meta: dict, groups: list[str] | None = None) -> np.ndarray:
    """Assemble the X matrix from selected feature groups. Default: ALL groups present (so the
    2D baselines automatically pick up the 'metal' group in the multi-metal experiment)."""
    groups = groups or list(meta["feature_groups"].keys())
    cols = [c for g in groups for c in meta["feature_groups"][g]]
    return df[cols].to_numpy(dtype=np.float32), cols


def scale_continuous(train: pd.DataFrame, *others: pd.DataFrame, cols=CONTINUOUS_COLS):
    """StandardScaler fit on TRAIN only, applied to train + any other frames. Returns copies."""
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler().fit(train[cols].to_numpy(dtype=np.float64))
    out = []
    for frame in (train, *others):
        f = frame.copy()
        f[cols] = scaler.transform(f[cols].to_numpy(dtype=np.float64))
        out.append(f)
    return (*out, scaler)


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = ap.parse_args()

    if not args.dataset.exists():
        raise SystemExit(f"Dataset not found: {args.dataset}\nRun src/data_curation.py first.")

    df = pd.read_parquet(args.dataset)
    feats, meta = build_features(df)

    assert len(feats) == len(df), "feature rows misaligned with dataset"
    assert feats["row_id"].tolist() == df["row_id"].tolist(), "row_id order changed"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    feats.to_parquet(args.out, index=False)
    args.report.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"[backend] {meta['ecfp_backend']}")
    print(f"[shape]   {meta['n_rows']} rows x {meta['n_feature_cols']} feature cols")
    for g, cols in meta["feature_groups"].items():
        print(f"   {g:14s} {len(cols)}")
    print(f"[failures] ligand-parse={meta['ligand_parse_failures']} "
          f"descriptor-parse={meta['descriptor_parse_failures']}")
    print(f"[written] {args.out}")
    print(f"[written] {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
