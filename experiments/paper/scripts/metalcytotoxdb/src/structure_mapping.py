"""Map the 4,399 article Ru complexes to their generated 3D structures, and audit the mapping.

The brief requires an audited mapping (identity-verified, no silent substitution) between each article
complex and a `.xyz` file, before any 3D modelling. This script:

    1. matches every article complex -> bmdb Name by (raw SMILES_Ligands, oxidation state) first
       (RDKit-version-independent; the article and manifest share the source strings), falling back to
       canonical ligand SMILES + OS for any residual -- so cross-machine RDKit differences don't drop rows;
    2. checks whether structures/<Name>.xyz exists in the isomer build;
    3. joins per-structure quality from biometaldb_assessment.csv (cshm, connectivity_ok, n_clashes,
       worst_contact_ratio);
    4. writes ru_structure_map.csv (one row per complex) + an audit report with the usability funnel in
       both complexes AND measurement rows, flagging missing structures and low quality.

Quality policy (configurable): quality_ok requires xyz present + connectivity_ok (the graph survived xtb).
Clashes are NOT filtered by default (the 0.75x-vdW flag catches many mild contacts); add --clash-free or
--min-contact-ratio R (require worst_contact_ratio >= R) or --cshm-max C for stricter geometry cuts.

Usage (on Keisan):
    python src/structure_mapping.py --structures ../mecobi_build_isomers/structures \
        --assessment ../biometaldb_assessment.csv
    # stricter geometry:
    python src/structure_mapping.py ... --min-contact-ratio 0.7 --cshm-max 10
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent
BIOMETALDB = PROJECT_ROOT.parent
DEFAULT_ARTICLE = PROJECT_ROOT / "data" / "processed" / "ru_article.parquet"
DEFAULT_MANIFEST = BIOMETALDB / "biometaldb_manifest.csv"
DEFAULT_STRUCTURES = BIOMETALDB / "mecobi_build_isomers" / "structures"
DEFAULT_ASSESSMENT = BIOMETALDB / "biometaldb_assessment.csv"
OUT_MAP = PROJECT_ROOT / "data" / "processed" / "ru_structure_map.csv"
REPORT = PROJECT_ROOT / "results" / "reports" / "ru_structure_map_report"


def canon(smiles_ligands: str) -> str | None:
    from rdkit import Chem
    frags = []
    for f in str(smiles_ligands).split("."):
        f = f.strip()
        if not f:
            continue
        m = Chem.MolFromSmiles(f)
        if m is None:
            return None
        frags.append(Chem.MolToSmiles(m))
    return ".".join(sorted(frags)) if frags else None


def _find_col(df, *needles):
    for c in df.columns:
        lc = c.lower()
        if all(n in lc for n in needles):
            return c
    return None


def _to_bool(series) -> pd.Series:
    return series.map(lambda v: str(v).strip().lower() in ("true", "1", "yes", "t"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--article", type=Path, default=DEFAULT_ARTICLE)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--structures", type=Path, default=DEFAULT_STRUCTURES)
    ap.add_argument("--assessment", type=Path, default=DEFAULT_ASSESSMENT)
    ap.add_argument("--metal", default="Ru")
    ap.add_argument("--clash-free", action="store_true",
                    help="require n_clashes == 0 (strict)")
    ap.add_argument("--min-contact-ratio", type=float, default=None,
                    help="require worst_contact_ratio >= this (softer clash cut)")
    ap.add_argument("--cshm-max", type=float, default=None,
                    help="require CShM <= this (geometry-fidelity cut)")
    ap.add_argument("--out", type=Path, default=OUT_MAP)
    args = ap.parse_args()

    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")

    art = pd.read_parquet(args.article)
    acx = art.drop_duplicates("complex_id")[
        ["complex_id", "SMILES_Ligands", "ligand_smiles_canonical", "Metal",
         "Oxidation_state"]].copy()

    man = pd.read_csv(args.manifest)
    ru = man if args.metal == "all" else man[man.Metal == args.metal].copy()
    ru = ru.copy()
    ru["canon"] = ru.SMILES_Ligands.map(canon)

    # --- identity match on (raw SMILES, Metal, OS) first, (canon, Metal, OS) as fallback ---
    # Metal is in the key so the same ligand set on different metals stays distinct.
    raw_map = {(s, mt, o): n
               for s, mt, o, n in zip(ru.SMILES_Ligands, ru.Metal, ru.Oxidation_state, ru.Name)}
    can_map = {(c, mt, o): n
               for c, mt, o, n in zip(ru.canon, ru.Metal, ru.Oxidation_state, ru.Name)
               if pd.notna(c)}

    def match(row):
        n = raw_map.get((row.SMILES_Ligands, row.Metal, row.Oxidation_state))
        if n is None:
            n = can_map.get((row.ligand_smiles_canonical, row.Metal, row.Oxidation_state))
        return n, ("raw" if raw_map.get((row.SMILES_Ligands, row.Metal, row.Oxidation_state))
                   else ("canon" if n else "none"))

    matched = acx.apply(match, axis=1, result_type="expand")
    acx["bmdb_name"] = matched[0]
    acx["match_via"] = matched[1]
    m = acx
    n_matched = int(m.bmdb_name.notna().sum())

    # --- .xyz existence (NaN-safe) ---
    # Store ABSOLUTE paths so the map works regardless of the cwd the trainer runs from.
    struct_dir = args.structures.resolve()

    def _xyz_path(n):
        return str(struct_dir / f"{n}.xyz") if isinstance(n, str) and n else None
    m["xyz_path"] = m.bmdb_name.map(_xyz_path)
    structures_present = args.structures.exists()
    if structures_present:
        m["xyz_exists"] = m["xyz_path"].map(lambda p: isinstance(p, str) and Path(p).exists())
    else:
        m["xyz_exists"] = pd.NA

    # --- quality join ---
    assessment_present = args.assessment.exists()
    detected = {}
    if assessment_present:
        a = pd.read_csv(args.assessment)
        name_c = _find_col(a, "name") or a.columns[0]
        cshm_c = _find_col(a, "cshm")
        conn_c = _find_col(a, "connectivity")
        clash_c = _find_col(a, "n", "clash") or _find_col(a, "clash", "free")
        ratio_c = _find_col(a, "worst", "contact") or _find_col(a, "contact", "ratio")
        detected = {"all_columns": list(a.columns), "name": name_c, "cshm": cshm_c,
                    "connectivity": conn_c, "n_clashes": clash_c, "worst_contact_ratio": ratio_c}
        keep = {name_c: "bmdb_name"}
        for src, dst in [(cshm_c, "cshm"), (conn_c, "connectivity_ok"),
                         (clash_c, "n_clashes"), (ratio_c, "worst_contact_ratio")]:
            if src:
                keep[src] = dst
        m = m.merge(a[list(keep)].rename(columns=keep), on="bmdb_name", how="left")

    # --- quality_ok (vectorised) ---
    if structures_present and assessment_present:
        q = m["xyz_exists"].fillna(False).astype(bool)
        conn_pass = _to_bool(m["connectivity_ok"]) if "connectivity_ok" in m else pd.Series(True, index=m.index)
        q &= conn_pass
        if args.clash_free and "n_clashes" in m:
            q &= (pd.to_numeric(m["n_clashes"], errors="coerce").fillna(1) == 0)
        if args.min_contact_ratio is not None and "worst_contact_ratio" in m:
            q &= (pd.to_numeric(m["worst_contact_ratio"], errors="coerce").fillna(0)
                  >= args.min_contact_ratio)
        if args.cshm_max is not None and "cshm" in m:
            q &= (pd.to_numeric(m["cshm"], errors="coerce").fillna(1e9) <= args.cshm_max)
        m["quality_ok"] = q
    else:
        m["quality_ok"] = pd.NA

    # --- write map ---
    args.out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["complex_id", "bmdb_name", "match_via", "Oxidation_state", "xyz_path", "xyz_exists",
            "cshm", "connectivity_ok", "n_clashes", "worst_contact_ratio", "quality_ok"]
    m[[c for c in cols if c in m.columns]].to_csv(args.out, index=False)

    # --- report with funnel (complexes AND rows) ---
    usable_cids = set(m.loc[m["quality_ok"] == True, "complex_id"]) if structures_present else set()  # noqa: E712
    rep = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "metal": args.metal,
        "article_complexes": int(len(acx)),
        "matched_to_bmdb": n_matched,
        "matched_via_raw": int((m.match_via == "raw").sum()),
        "matched_via_canon": int((m.match_via == "canon").sum()),
        "unmatched": int(len(acx) - n_matched),
        "structures_dir_present": structures_present,
        "assessment_present": assessment_present,
        "assessment_columns_detected": detected,
        "quality_policy": {"require_connectivity": True, "clash_free": args.clash_free,
                           "min_contact_ratio": args.min_contact_ratio, "cshm_max": args.cshm_max},
    }
    if structures_present:
        rep["xyz_present"] = int(m.xyz_exists.fillna(False).sum())
        rep["xyz_missing"] = int((~m.xyz_exists.fillna(False) & m.bmdb_name.notna()).sum())
    if assessment_present and "connectivity_ok" in m:
        rep["connectivity_pass"] = int(_to_bool(m["connectivity_ok"]).sum())
    if assessment_present and "n_clashes" in m:
        nc = pd.to_numeric(m["n_clashes"], errors="coerce")
        rep["clash_free_count"] = int((nc == 0).sum())
        rep["with_clashes_count"] = int((nc > 0).sum())
    if assessment_present and "cshm" in m:
        cs = pd.to_numeric(m["cshm"], errors="coerce")
        rep["cshm"] = {"median": round(float(cs.median()), 3),
                       "frac_lt_2": round(float((cs < 2).mean()), 3),
                       "frac_lt_5": round(float((cs < 5).mean()), 3),
                       "frac_lt_10": round(float((cs < 10).mean()), 3)}
    if structures_present:
        rep["quality_ok_complexes"] = len(usable_cids)
        rep["quality_ok_rows"] = int(art.complex_id.isin(usable_cids).sum())
        rep["total_rows"] = int(len(art))
        rep["row_coverage"] = round(rep["quality_ok_rows"] / len(art), 3)

    Path(f"{REPORT}.json").parent.mkdir(parents=True, exist_ok=True)
    Path(f"{REPORT}.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    print(f"\n[written] {args.out}")
    if not structures_present:
        print(f"[note] structures dir not found ({args.structures}); run on the isomer-build machine.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
