"""Curate the MULTI-METAL cytotoxicity dataset (all metals, incl. Au) from the current release.

Separate from data_curation.py (which does the exact Ru article reproduction from the Zenodo
snapshot). This one reads the current MetalCytoToxDB release (ic50.csv, which includes Au and the
metal-descriptor columns) and applies the same filtering rules across ALL metals, for the multi-metal
3D-vs-2D experiment that Krasnov et al. did NOT run (they modelled Ru and Ir separately).

Rules (same as the Ru pipeline): drop non-cancer lines, keep the six exposure times
{24,48,72,96,120,144} h, dedup (SMILES_Ligands, Cell_line, Time), keep the top-N cancer lines by count.
Complex identity is (canonical ligand SMILES, Metal, Oxidation_state) — the same key the 3D structures
(bmdb) are built on, so two metals sharing a ligand set are distinct complexes.

Metal-descriptor columns (Atomic_number, Oxidation_state, Valence_e, Charge_complex) are carried
through for the 2D baselines (LightGBM/MLP need them to tell metals apart; DimeNet++ gets the metal for
free as the node atomic number).

Usage (Keisan):
    python src/curate_multimetal.py \
        --source <MECOBI_REPO>/experiments/biometaldb/ic50.csv --n-lines 40
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

NORMAL_LINES = frozenset({
    "HEK293", "MRC-5", "LO2", "BEAS-2B", "MCF-10A", "NIH-3T3", "HEK293T", "RPE-1", "L-929",
    "HL-7702", "HLF", "HaCaT", "HUVEC", "16HBE", "Vero", "NFF", "ARPE-19", "EA.hy926", "HK-2",
    "PBMC", "CHO", "V79", "WI-38", "IMR-90", "GES-1", "NCM460", "NP69", "PBMCs", "BHK-21",
    "CCD-19Lu", "HELF", "W138", "HMrSv5", "PBMC-PHA", "PBMC+PHA", "FLS", "DPSC", "BMSC", "C8-D1A"})
EXPOSURE_TIMES = frozenset({24.0, 48.0, 72.0, 96.0, 120.0, 144.0})
IC50_TOXIC_THRESHOLD_UM = 10.0
DEDUP_KEYS = ["SMILES_Ligands", "Cell_line", "Time(h)"]

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent
DEFAULT_OUT = PROJECT_ROOT / "data" / "processed" / "multimetal.parquet"
DEFAULT_REPORT = PROJECT_ROOT / "results" / "reports" / "multimetal_curation_report.json"


def canonical_complex_key(smiles_ligands: str) -> str | None:
    from rdkit import Chem
    frags = []
    for frag in str(smiles_ligands).split("."):
        frag = frag.strip()
        if not frag:
            continue
        m = Chem.MolFromSmiles(frag)
        if m is None:
            return None
        frags.append(Chem.MolToSmiles(m))
    return ".".join(sorted(frags)) if frags else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, required=True,
                    help="current-release ic50.csv (has all metals incl. Au + metal descriptors)")
    ap.add_argument("--metals", nargs="+", default=["all"],
                    help="metals to keep (default: all present)")
    ap.add_argument("--n-lines", type=int, default=40, help="top-N cancer cell lines to keep")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = ap.parse_args()

    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")

    df = pd.read_csv(args.source, low_memory=False)
    steps = [{"step": "loaded", "rows": len(df), "metals": df.Metal.value_counts().to_dict()}]

    if args.metals != ["all"]:
        df = df[df.Metal.isin(args.metals)].copy()
    d = df[~df.Cell_line.isin(NORMAL_LINES) & df["Time(h)"].isin(EXPOSURE_TIMES)].copy()
    d = d.sort_values(DEDUP_KEYS + ["DOI", "IC50_Dark_value"], kind="mergesort")
    d = d.drop_duplicates(subset=DEDUP_KEYS, keep="first").copy()
    counts = d.Cell_line.value_counts()
    top_lines = sorted(counts.index[:args.n_lines], key=lambda c: (-counts[c], c))
    d = d[d.Cell_line.isin(top_lines)].copy()

    # label (prefer precomputed IC50_class; fall back to threshold on IC50_Dark_value)
    if "IC50_class" in d.columns:
        d["y"] = d["IC50_class"].astype("int8")
    else:
        d["y"] = (pd.to_numeric(d["IC50_Dark_value"], errors="coerce")
                  < IC50_TOXIC_THRESHOLD_UM).astype("int8")

    # canonical key + complex_id keyed on (canonical SMILES, Metal, Oxidation_state)
    cache: dict[str, str | None] = {}
    canon = []
    for s in d["SMILES_Ligands"]:
        if s not in cache:
            cache[s] = canonical_complex_key(s)
        canon.append(cache[s])
    d["ligand_smiles_canonical"] = canon
    key = (d["ligand_smiles_canonical"].fillna(d["SMILES_Ligands"].astype(str)) + "|"
           + d["Metal"].astype(str) + "|" + d["Oxidation_state"].astype(str))
    ordered = sorted(key.unique())
    key_to_id = {k: f"cx_{i:05d}" for i, k in enumerate(ordered)}
    d["complex_id"] = key.map(key_to_id)

    keep = ["complex_id", "SMILES_Ligands", "ligand_smiles_canonical", "Counterion",
            "Metal", "Oxidation_state", "Atomic_number", "Valence_e", "Charge_complex",
            "Cell_line", "Time(h)", "IC50_Dark_value", "y", "DOI", "Year"]
    keep = [c for c in keep if c in d.columns]
    d = d[keep].reset_index(drop=True)
    d.insert(0, "row_id", [f"r_{i:06d}" for i in range(len(d))])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    d.to_parquet(args.out, index=False)
    d.to_csv(args.out.with_suffix(".csv"), index=False)

    rep = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(args.source), "metals": args.metals, "n_lines": args.n_lines,
        "steps": steps,
        "rows": int(len(d)), "unique_complexes": int(d.complex_id.nunique()),
        "cell_lines": int(d.Cell_line.nunique()), "cell_line_list": sorted(top_lines),
        "unique_dois": int(d.DOI.nunique()),
        "per_metal": {m: {"rows": int(len(g)), "complexes": int(g.complex_id.nunique())}
                      for m, g in d.groupby("Metal")},
        "class_distribution": {int(k): int(v) for k, v in d.y.value_counts().items()},
        "toxic_frac": round(float(d.y.mean()), 4),
    }
    args.report.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    print(f"\n[written] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
