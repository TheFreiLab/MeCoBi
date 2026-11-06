import re
"""Build the clean master ground-truth CSV across gen0/gen1/gen2 (SA activity only).

gen0 truth  <- IrCpSB_RT.csv (SA_activity == training AverageSA12.5)
gen1/2 truth<- AIChemy_Gen1_Gen2_LCMS_SDR_summary_Aug26.csv (updated)
             joined to old *_AllData.csv (clean component SMILES) via order-independent
             frozenset of canonical {Cp, aldehyde, amine} building blocks.
Schiff base is regenerated uniformly (gen1's AllData Schiff is missing; gen2's has 22
chemically dubious ester-condensation entries).
"""
import os
import pandas as pd
import numpy as np
from common import (ROOT, canon, make_schiff, assign_roles, active_label, fp_smiles,
                    ACTIVE_CUTOFF, CONV_MIN, COUNTERION)

OUT = os.path.join(ROOT, "outputs", "master_groundtruth_SA.csv")


def bb_key(cp, ald, am):
    parts = [canon(cp), canon(ald), canon(am)]
    return "|".join(sorted(p for p in parts if p))


def build_gen0():
    rt = pd.read_csv(os.path.join(ROOT, "IrCpSB_RT.csv"))
    rt = rt[rt["generation"] == "gen0"].copy()
    rows = []
    for _, r in rt.iterrows():
        cp = canon(r["Cp_SMILES_can"]); ald = canon(r["Aldehyde_SMILES_can"]); am = canon(r["Amine_SMILES_can"])
        schiff = make_schiff(r["Aldehyde_SMILES_can"], r["Amine_SMILES_can"]) or canon(r.get("Schiff_SMILES_can"))
        val = pd.to_numeric(r["SA_activity"], errors="coerce")
        conv = pd.to_numeric(r["Conversion"], errors="coerce")
        rows.append(dict(
            generation="gen0",
            compound_id=str(r["compound_id"]),
            compound_name=str(r["Compound_Name"]),
            structure_stem=str(r["Compound_Name"]),  # structures/gen0/<name>_OPT.xyz
            well=str(r.get("Well", "")),
            source="IrCpSB_RT.csv",
            Cp_SMILES_can=cp, Aldehyde_SMILES_can=ald, Amine_SMILES_can=am,
            Schiff_SMILES_can=schiff, counterion=COUNTERION,
            Conversion=conv, SA_value=val,
            SA_active=active_label(val),
            conv_pass=bool(conv >= CONV_MIN) if pd.notna(conv) else False,
            fp_smiles=fp_smiles(cp, schiff),
            bb_key=bb_key(cp, ald, am),
        ))
    return pd.DataFrame(rows)


def build_gen12():
    aug = pd.read_csv(os.path.join(ROOT, "AIChemy_Gen1_Gen2_LCMS_SDR_summary_Aug26.csv"))
    aug["generation"] = aug["File_name"].apply(lambda s: "gen1" if "G1" in str(s) else "gen2")
    aug["compound_id"] = aug["File_name"].str.replace("_rerun_Jul26", "", regex=False)
    act_col = "Average 12.5 uM activty against S. aureus"

    # structure_stem crosswalk: RT (updated) has Compound_Name == structure filename,
    # keyed by canonical building-block set (bb_key). Also carry Well.
    rt = pd.read_csv(os.path.join(ROOT, "IrCpSB_RT.csv"))
    rt = rt[rt["generation"].isin(["gen1", "gen2"])]
    stem_map, well_map = {}, {}
    for _, r in rt.iterrows():
        k = bb_key(r["Cp_SMILES_can"], r["Aldehyde_SMILES_can"], r["Amine_SMILES_can"])
        if k:
            stem_map[k] = str(r["Compound_Name"])
            well_map[k] = str(r.get("Well", ""))

    rows = []
    for _, r in aug.iterrows():
        parts = str(r["Combined_SMILES"]).split(".")
        # roles assigned by functional group (AllData component columns are unreliable:
        # Gen1_AllData has Aldehyde/Amine columns swapped).
        cp, ald, am = assign_roles(parts)
        schiff = make_schiff(ald, am) if (ald and am) else None
        val = pd.to_numeric(r[act_col], errors="coerce")
        conv = pd.to_numeric(r["Combined_conversion"], errors="coerce")
        k = bb_key(cp, ald, am)
        stem = stem_map.get(k, np.nan)  # == Compound_Name == structure filename stem
        # RT has 4 gen1 rows whose Compound_Name is mis-suffixed "_gen2"; force the
        # generation suffix to match the row's true generation (the .xyz files are correct).
        if isinstance(stem, str):
            stem = re.sub(r"_gen[012]$", "", stem) + "_" + str(r["generation"])
        rows.append(dict(
            generation=r["generation"],
            compound_id=str(r["compound_id"]),
            compound_name=stem if isinstance(stem, str) else str(r["compound_id"]),
            structure_stem=stem,
            well=well_map.get(k, ""),
            source="AIChemy_Gen1_Gen2_LCMS_SDR_summary_Aug26.csv",
            Cp_SMILES_can=cp, Aldehyde_SMILES_can=ald, Amine_SMILES_can=am,
            Schiff_SMILES_can=schiff, counterion=COUNTERION,
            Conversion=conv, SA_value=val,
            SA_active=active_label(val),
            conv_pass=bool(conv >= CONV_MIN) if pd.notna(conv) else False,
            fp_smiles=fp_smiles(cp, schiff),
            bb_key=bb_key(cp, ald, am),
        ))
    return pd.DataFrame(rows)


def main():
    g0 = build_gen0()
    g12 = build_gen12()
    master = pd.concat([g0, g12], ignore_index=True)

    # integrity report
    print("=== MASTER SUMMARY ===")
    for gen, d in master.groupby("generation"):
        passed = d[d["conv_pass"]]
        n_act = int((passed["SA_active"] == 1).sum())
        n_inact = int((passed["SA_active"] == 0).sum())
        print(f"{gen}: n={len(d)} | conv>=40: {len(passed)} | "
              f"active(<{ACTIVE_CUTOFF})={n_act} inactive={n_inact} | "
              f"missing_SMILES={int(d['Cp_SMILES_can'].isna().sum())} "
              f"missing_SA={int(d['SA_value'].isna().sum())} "
              f"missing_schiff={int(d['Schiff_SMILES_can'].isna().sum())} "
              f"has_structure_stem={int(d['structure_stem'].notna().sum())}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    master.to_csv(OUT, index=False)
    print(f"\nWrote {OUT}  ({len(master)} rows, {len(master.columns)} cols)")
    print("cols:", list(master.columns))


if __name__ == "__main__":
    main()
