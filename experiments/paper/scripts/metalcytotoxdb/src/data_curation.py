"""Reconstruct the exact article Ru dataset from the MetalCytoToxDB Zenodo snapshot.

Reproduces the dataset used in Krasnov et al., J. Med. Chem. 2026, 69, 8838-8851
(doi:10.1021/acs.jmedchem.5c02755) for the ruthenium cytotoxicity-classification benchmark.

Verified recipe (bit-exact against the published counts 11,294 / 4,399 / 23):

    1. keep Metal == Ru
    2. drop the authors' non-cancer cell lines (_NORMAL_LINES, taken verbatim from their
       Streamlit app, github.com/levakrasnovs/RuCytoToxDB)
    3. keep the six exposure times {24, 48, 72, 96, 120, 144} h
    4. drop duplicate (SMILES_Ligands, Cell_line, Time) combinations across DOIs/counterions
    5. keep the top-23 cancer cell lines by (deduplicated) entry count

The gate is defined on the RAW `SMILES_Ligands` string, exactly as the snapshot ships it,
because that is what reproduces the published unique-complex count. Canonical columns are added
as *extra* metadata for downstream fingerprinting / structure mapping and never change row identity.

Snapshot source: Zenodo 10.5281/zenodo.17106822 (the frozen article release; 26,801 rows, the five
paper metals, no Au). The current biometaldb `ic50.csv` is a *newer* database and must NOT be used
for the exact reproduction.

Outputs (under results/ and data/processed/):
    data/processed/ru_article.parquet   frozen modelling table (one row per measurement)
    data/processed/ru_article.csv        same, human-readable
    results/reports/ru_curation_report.json
    results/reports/ru_curation_report.md

Usage:
    python src/data_curation.py                 # Ru, strict gate on published counts
    python src/data_curation.py --metal Ir --no-strict   # reuse the machinery for the Ir subset
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------------------
# Constants pinned from the paper + the authors' released code
# --------------------------------------------------------------------------------------

# Non-cancer cell lines excluded prior to model development. Copied verbatim from the
# authors' Streamlit app (RuCytoToxDB/streamlit_app.py, `_NORMAL_LINES`).
NORMAL_LINES: frozenset[str] = frozenset({
    "HEK293", "MRC-5", "LO2", "BEAS-2B", "MCF-10A", "NIH-3T3", "HEK293T", "RPE-1", "L-929",
    "HL-7702", "HLF", "HaCaT", "HUVEC", "16HBE", "Vero", "NFF", "ARPE-19", "EA.hy926", "HK-2",
    "PBMC", "CHO", "V79", "WI-38", "IMR-90", "GES-1", "NCM460", "NP69", "PBMCs", "BHK-21",
    "CCD-19Lu", "HELF", "W138", "HMrSv5", "PBMC-PHA", "PBMC+PHA", "FLS", "DPSC", "BMSC", "C8-D1A",
})

# The six exposure times retained for the final Ru training set (paper, Results & Experimental).
EXPOSURE_TIMES: frozenset[float] = frozenset({24.0, 48.0, 72.0, 96.0, 120.0, 144.0})

# Toxic if IC50 (dark) < 10 uM. IC50_Dark_value is already in uM (M * 1e-6) with ">100" -> 100.0.
IC50_TOXIC_THRESHOLD_UM = 10.0

# Number of top cancer cell lines to keep (reproduces the paper's "23 cancer cell lines").
DEFAULT_N_CELL_LINES = 23

# Deduplication key: same molecule / cell line / exposure time is one measurement (paper wording).
DEDUP_KEYS = ["SMILES_Ligands", "Cell_line", "Time(h)"]

# Published gate for the Ru subset. Used for the strict assertion / diagnostic.
EXPECTED: dict[str, dict[str, int]] = {
    "Ru": {"rows": 11294, "complexes": 4399, "cell_lines": 23, "exposure_times": 6},
}

# Paths resolved relative to this file so the script is independent of the working directory.
_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent
DEFAULT_SNAPSHOT = PROJECT_ROOT / "article_sources" / "MetalCytoToxDB.csv"
DEFAULT_OUTDIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_REPORTDIR = PROJECT_ROOT / "results" / "reports"


# --------------------------------------------------------------------------------------
# Report bookkeeping
# --------------------------------------------------------------------------------------

@dataclass
class CurationReport:
    metal: str
    snapshot_path: str
    snapshot_sha256: str
    steps: list[dict] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    gate: dict = field(default_factory=dict)
    generated_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def step(self, name: str, df: pd.DataFrame, note: str = "") -> None:
        self.steps.append({
            "step": name,
            "rows": int(len(df)),
            "unique_complexes": int(df["SMILES_Ligands"].nunique()),
            "cell_lines": int(df["Cell_line"].nunique()),
            "note": note,
        })


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _frame_checksum(df: pd.DataFrame) -> str:
    """Stable content hash of the frozen table (order-independent over rows)."""
    key_cols = ["SMILES_Ligands", "Counterion", "Cell_line", "Time(h)", "DOI", "y",
                "IC50_Dark_value"]
    cols = [c for c in key_cols if c in df.columns]
    payload = (
        df[cols]
        .astype(str)
        .agg("|".join, axis=1)
        .sort_values()
        .str.cat(sep="\n")
        .encode("utf-8")
    )
    return hashlib.sha256(payload).hexdigest()


# --------------------------------------------------------------------------------------
# Canonicalisation (extra metadata; does NOT affect the gate)
# --------------------------------------------------------------------------------------

def canonical_complex_key(smiles_ligands: str) -> str | None:
    """Per-ligand RDKit canonicalisation, sorted and dot-joined.

    Used only to build a stable `complex_id` and a structure-mapping key; the row-level gate
    stays on the raw string. Returns None if any fragment fails to parse.
    """
    from rdkit import Chem  # local import so the gate works without rdkit

    frags = []
    for frag in str(smiles_ligands).split("."):
        frag = frag.strip()
        if not frag:
            continue
        mol = Chem.MolFromSmiles(frag)
        if mol is None:
            return None
        frags.append(Chem.MolToSmiles(mol))
    if not frags:
        return None
    return ".".join(sorted(frags))


def add_canonical_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Add `ligand_smiles_canonical` and a deterministic `complex_id`. Best-effort."""
    try:
        import rdkit  # noqa: F401
    except ImportError:
        df["ligand_smiles_canonical"] = pd.NA
        # Fall back to the raw string for id assignment so downstream still gets stable ids.
        canon_series = df["SMILES_Ligands"].astype(str)
        n_failed = -1  # signal "rdkit unavailable"
    else:
        cache: dict[str, str | None] = {}
        canon = []
        for s in df["SMILES_Ligands"]:
            if s not in cache:
                cache[s] = canonical_complex_key(s)
            canon.append(cache[s])
        df["ligand_smiles_canonical"] = canon
        n_failed = sum(v is None for v in cache.values())
        # For rows where canonicalisation failed, fall back to the raw string as the id key.
        canon_series = df["ligand_smiles_canonical"].where(
            df["ligand_smiles_canonical"].notna(), df["SMILES_Ligands"].astype(str)
        )

    # Deterministic complex_id over the sorted set of (canonical-or-raw) complex keys.
    id_prefix = df["Metal"].iloc[0].lower() if len(df) else "cx"
    ordered = sorted(canon_series.unique())
    width = max(5, len(str(len(ordered))))
    key_to_id = {k: f"{id_prefix}_{i:0{width}d}" for i, k in enumerate(ordered)}
    df["complex_id"] = canon_series.map(key_to_id)
    return df, n_failed


# --------------------------------------------------------------------------------------
# Curation
# --------------------------------------------------------------------------------------

def load_snapshot(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    required = {"SMILES_Ligands", "Metal", "Cell_line", "Time(h)", "IC50_Dark_value", "DOI"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Snapshot missing required columns: {sorted(missing)}")
    return df


def curate(df: pd.DataFrame, metal: str, n_lines: int, report: CurationReport) -> pd.DataFrame:
    report.step("snapshot_loaded", df.assign(SMILES_Ligands=df["SMILES_Ligands"]),
                note=f"{len(df)} total rows, metals={sorted(df['Metal'].dropna().unique())}")

    # 1. metal subset
    d = df[df["Metal"] == metal].copy()
    report.step(f"metal=={metal}", d)

    # 2. drop non-cancer lines
    d = d[~d["Cell_line"].isin(NORMAL_LINES)].copy()
    report.step("drop_noncancer_lines", d, note=f"{len(NORMAL_LINES)} normal lines excluded")

    # 3. keep the six exposure times
    d = d[d["Time(h)"].isin(EXPOSURE_TIMES)].copy()
    report.step("filter_exposure_times", d,
                note=f"kept {sorted(EXPOSURE_TIMES)}")

    # 4. dedup molecule / cell line / time. Sort first so the surviving representative is
    #    deterministic across runs (count is order-independent; representative was not).
    d = d.sort_values(DEDUP_KEYS + ["DOI", "IC50_Dark_value"], kind="mergesort")
    d = d.drop_duplicates(subset=DEDUP_KEYS, keep="first").copy()
    report.step("dedup_molecule_cellline_time", d, note=f"dedup on {DEDUP_KEYS}")

    # 5. keep the top-N cancer cell lines by (deduplicated) count. Tie-break by name for
    #    determinism (no tie at the 23/24 boundary for Ru: K-562=109 vs SGC-7901=99).
    counts = d["Cell_line"].value_counts()
    ranked = sorted(counts.index, key=lambda c: (-counts[c], c))
    top_lines = ranked[:n_lines]
    d = d[d["Cell_line"].isin(top_lines)].copy()
    report.step(f"top_{n_lines}_cancer_lines", d,
                note=f"cutoff count = {counts[top_lines[-1]]} ({top_lines[-1]})")

    return d


def build_modelling_table(d: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Attach labels, ids and the tidy column set used by every downstream model."""
    d = d.copy()
    d["y"] = (pd.to_numeric(d["IC50_Dark_value"], errors="coerce") < IC50_TOXIC_THRESHOLD_UM)
    d["y"] = d["y"].astype("int8")

    d, n_failed = add_canonical_columns(d)

    keep = [
        "complex_id",
        "SMILES_Ligands", "ligand_smiles_canonical", "Counterion",
        "Metal", "Oxidation_state", "Charge_complex",
        "Cell_line", "Time(h)",
        "IC50_Dark_value", "IC50_Dark(M*10^-6)",
        "y",
        "DOI", "Year",
    ]
    keep = [c for c in keep if c in d.columns]
    d = d[keep].reset_index(drop=True)
    d.insert(0, "row_id", [f"r_{i:06d}" for i in range(len(d))])
    return d, n_failed


def finalise_report(d: pd.DataFrame, report: CurationReport, metal: str, n_failed: int) -> None:
    report.summary = {
        "rows": int(len(d)),
        "unique_complexes": int(d["SMILES_Ligands"].nunique()),
        "cell_lines": int(d["Cell_line"].nunique()),
        "cell_line_list": sorted(d["Cell_line"].unique()),
        "exposure_times": sorted(float(t) for t in d["Time(h)"].unique()),
        "n_exposure_times": int(d["Time(h)"].nunique()),
        "unique_dois": int(d["DOI"].nunique()),
        "year_range": [int(d["Year"].min()), int(d["Year"].max())] if "Year" in d else None,
        "class_distribution": {int(k): int(v) for k, v in d["y"].value_counts().items()},
        "class_balance_toxic_frac": round(float(d["y"].mean()), 4),
        "canonicalisation_failures": n_failed,  # -1 => rdkit unavailable
        "frame_checksum_sha256": _frame_checksum(d),
    }

    exp = EXPECTED.get(metal)
    if exp:
        got = report.summary
        checks = {
            "rows": (got["rows"], exp["rows"]),
            "complexes": (got["unique_complexes"], exp["complexes"]),
            "cell_lines": (got["cell_lines"], exp["cell_lines"]),
            "exposure_times": (got["n_exposure_times"], exp["exposure_times"]),
        }
        report.gate = {
            name: {"got": g, "expected": e, "pass": g == e}
            for name, (g, e) in checks.items()
        }
        report.gate["all_pass"] = all(v["pass"] for v in report.gate.values()
                                       if isinstance(v, dict))
    else:
        report.gate = {"all_pass": None, "note": f"no published gate for metal={metal}"}


def write_outputs(d: pd.DataFrame, report: CurationReport, outdir: Path, reportdir: Path,
                  metal: str) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    reportdir.mkdir(parents=True, exist_ok=True)
    stem = f"{metal.lower()}_article"

    d.to_parquet(outdir / f"{stem}.parquet", index=False)
    d.to_csv(outdir / f"{stem}.csv", index=False)

    with open(reportdir / f"{stem}_curation_report.json", "w", encoding="utf-8") as fh:
        json.dump(report.__dict__, fh, indent=2)

    (reportdir / f"{stem}_curation_report.md").write_text(
        _markdown_report(report), encoding="utf-8"
    )


def _markdown_report(r: CurationReport) -> str:
    lines = [
        f"# Curation report — {r.metal} (article reproduction)",
        "",
        f"- generated (UTC): {r.generated_utc}",
        f"- snapshot: `{r.snapshot_path}`",
        f"- snapshot sha256: `{r.snapshot_sha256}`",
        "",
        "## Filtering steps",
        "",
        "| step | rows | unique complexes | cell lines | note |",
        "|---|---|---|---|---|",
    ]
    for s in r.steps:
        lines.append(f"| {s['step']} | {s['rows']} | {s['unique_complexes']} | "
                     f"{s['cell_lines']} | {s['note']} |")

    s = r.summary
    lines += [
        "",
        "## Final dataset",
        "",
        f"- rows (measurements): **{s['rows']}**",
        f"- unique complexes: **{s['unique_complexes']}**",
        f"- cancer cell lines: **{s['cell_lines']}**",
        f"- exposure times: {s['exposure_times']}",
        f"- unique DOIs: {s['unique_dois']}",
        f"- year range: {s['year_range']}",
        f"- class distribution (0=nontoxic, 1=toxic): {s['class_distribution']} "
        f"(toxic frac {s['class_balance_toxic_frac']})",
        f"- canonicalisation failures: {s['canonicalisation_failures']} "
        f"({'rdkit unavailable' if s['canonicalisation_failures'] == -1 else 'parsed'})",
        f"- frame checksum (sha256): `{s['frame_checksum_sha256']}`",
        "",
        f"- cell lines: {', '.join(s['cell_line_list'])}",
        "",
        "## Reproduction gate",
        "",
    ]
    if r.gate.get("all_pass") is None:
        lines.append(f"- {r.gate.get('note', 'no gate')}")
    else:
        for name, v in r.gate.items():
            if name == "all_pass":
                continue
            mark = "PASS" if v["pass"] else "FAIL"
            lines.append(f"- {name}: got {v['got']} / expected {v['expected']} — **{mark}**")
        lines.append("")
        lines.append(f"**Gate: {'PASS' if r.gate['all_pass'] else 'FAIL'}**")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT,
                    help="MetalCytoToxDB.csv (Zenodo article snapshot)")
    ap.add_argument("--metal", default="Ru", help="metal subset (default Ru)")
    ap.add_argument("--n-lines", type=int, default=DEFAULT_N_CELL_LINES,
                    help="number of top cancer cell lines to keep (default 23)")
    ap.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    ap.add_argument("--reportdir", type=Path, default=DEFAULT_REPORTDIR)
    ap.add_argument("--no-strict", dest="strict", action="store_false",
                    help="do not fail if the published gate is not met (diagnostic only)")
    args = ap.parse_args()

    if not args.snapshot.exists():
        raise SystemExit(f"Snapshot not found: {args.snapshot}\n"
                         "Download it from Zenodo 10.5281/zenodo.17106822 first.")

    report = CurationReport(
        metal=args.metal,
        snapshot_path=str(args.snapshot),
        snapshot_sha256=_sha256(args.snapshot),
    )

    df = load_snapshot(args.snapshot)
    curated = curate(df, args.metal, args.n_lines, report)
    table, n_failed = build_modelling_table(curated)
    finalise_report(table, report, args.metal, n_failed)
    write_outputs(table, report, args.outdir, args.reportdir, args.metal)

    # Console summary
    print(_markdown_report(report))
    print(f"[written] {args.outdir / (args.metal.lower() + '_article.parquet')}")
    print(f"[written] {args.reportdir / (args.metal.lower() + '_article_curation_report.md')}")

    gate_pass = report.gate.get("all_pass")
    if args.strict and gate_pass is False:
        raise SystemExit("\nGATE FAILED: curated counts do not match the published article "
                         "numbers. Investigate before training (see report). Use --no-strict "
                         "to override for a non-Ru subset.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
