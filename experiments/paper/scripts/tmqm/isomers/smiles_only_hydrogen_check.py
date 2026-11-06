"""SMILES-only builds whose isomers all lack hydrogens of the tmQM entry (column "Evaluated" of Table S20).

    python smiles_only_hydrogen_check.py ISO_DIR STATUS_CSV INCLUSION_CSV OOF_XTB_CSV OUT_CSV

ISO_DIR is the single-point run of prepare_isomer_sp.py (manifest_isomers_xtb.csv, results_xtb/sp.csv,
xtb_structures/); STATUS_CSV is the output of smiles_only_table.py; INCLUSION_CSV and OOF_XTB_CSV are
../tmqm/inclusion.csv and ../tmqm/oof_xtb.csv. Needs ../geometries.pkl (tmQM and crystal-isomer geometries, written
by analyze_tmqm_xtb.py). The ligand SMILES mined from the CSD carry no hydride ligands, so a hydrido complex built
from the SMILES alone has fewer hydrogens than its tmQM entry and cannot be compared with its DFT values. Writes one
row per valid build in the 10,175 set with no isomer of the tmQM formula, and prints the counts per crystal CN.
"""
import pickle
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

iso_dir, status_csv, inclusion_csv, oof_csv, out = map(Path, sys.argv[1:6])
G = pickle.load(open(Path(__file__).resolve().parents[1] / "geometries.pkl", "rb"))["tmqm"]
st = pd.read_csv(status_csv).set_index("refcode")
inc = pd.read_csv(inclusion_csv).set_index("refcode")
in_set = set(pd.read_csv(oof_csv).refcode)
man = pd.read_csv(iso_dir / "manifest_isomers_xtb.csv")
sp = pd.read_csv(iso_dir / "results_xtb" / "sp.csv")
sp = sp[sp.ok].merge(man[["complex_id", "refcode"]], on="complex_id")


def atoms(cid):
    lines = (iso_dir / "xtb_structures" / f"{cid}.xyz").read_text().splitlines()
    return Counter(l.split()[0] for l in lines[2:2 + int(lines[0])])


rows = []
for rc, g in sp.groupby("refcode"):
    if rc not in in_set or rc not in G:
        continue
    ref = Counter(G[rc]["sym"])
    built = [atoms(c) for c in g.complex_id]
    if any(a == ref for a in built):
        continue
    other = {k for a in built for k in set(a) | set(ref) if a[k] != ref[k]}
    rows.append({"refcode": rc, "metal": st.metal[rc], "cn": int(st.cn[rc]), "n_isomers": len(built),
                 "n_hydride": int(inc.n_hydride[rc]), "elements_differing": " ".join(sorted(other)),
                 "dH": ",".join(f"{d:+d}" for d in sorted({a["H"] - ref["H"] for a in built}))})
o = pd.DataFrame(rows)
o.to_csv(out, index=False)
print(f"{len(o)} complexes; hydrogens missing = hydride ligands: {(o.n_hydride == -o.dH.str.split(',').str[0].astype(int)).sum()}")
print(o.groupby("cn").size().to_string())
