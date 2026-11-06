"""IrCpSB library -> MeCoBi inputs (inputs/complexes_ircpsb.csv).

    python prepare_inputs.py <master_groundtruth_SA.csv>

One row per complex [Ir(Cp)(SB)Cl]+: the Cp ligand as the cyclopentadienide anion (the master table stores the
neutral diene, e.g. Cp*H), the Schiff base, and chloride. Every Schiff base of the library is a 2-iminopyridine,
so its donors are fixed to the imine N and the pyridine N (kappa2-N,N): pydentate alone mis-assigns 24 of the
1,800 (a pendant pyridyl-amide or an alkyne counted as a third donor, or a carbonyl O instead of the pyridine N).
"""
import sys
from pathlib import Path

import pandas as pd
from rdkit import Chem

HERE = Path(__file__).resolve().parent
IMINOPYRIDINE = Chem.MolFromSmarts("[NX2:1]=[CH1]-c:[nX2:2]")


def cp_anion(smiles):
    mol = Chem.RWMol(Chem.MolFromSmiles(smiles))
    for ring in mol.GetRingInfo().AtomRings():
        if len(ring) != 5:
            continue
        sp3 = [a for a in ring if mol.GetAtomWithIdx(a).GetHybridization() == Chem.HybridizationType.SP3
               and mol.GetAtomWithIdx(a).GetTotalNumHs() > 0]
        if len(sp3) == 1:
            at = mol.GetAtomWithIdx(sp3[0])
            at.SetFormalCharge(-1)
            at.SetNumExplicitHs(at.GetTotalNumHs() - 1)
            at.SetNoImplicit(True)
            Chem.SanitizeMol(mol)
            return Chem.MolToSmiles(mol)
    raise ValueError(f"no cyclopentadiene ring in {smiles}")


def schiff_donors(smiles):
    hits = Chem.MolFromSmiles(smiles).GetSubstructMatches(IMINOPYRIDINE)
    if not hits:
        raise ValueError(f"not a 2-iminopyridine: {smiles}")
    return f"{hits[0][0]},{hits[0][3]}"


def main():
    m = pd.read_csv(sys.argv[1])
    cp = {s: cp_anion(s) for s in m.Cp_SMILES_can.unique()}
    out = pd.DataFrame({
        "compound_id": m.compound_id, "structure_stem": m.structure_stem, "generation": m.generation,
        "folder": m.generation.map({"gen0": "gen0", "gen1": "gen1+2", "gen2": "gen1+2"}),
        "metal": "Ir", "ox": 3,
        "cp": m.Cp_SMILES_can.map(cp), "schiff": m.Schiff_SMILES_can, "chloride": "[Cl-]",
        "schiff_donors": m.Schiff_SMILES_can.map(schiff_donors)})
    (HERE / "inputs").mkdir(exist_ok=True)
    out.to_csv(HERE / "inputs" / "complexes_ircpsb.csv", index=False)
    print(len(out), "complexes ->", HERE / "inputs" / "complexes_ircpsb.csv")
    print(out.folder.value_counts().to_dict())


if __name__ == "__main__":
    main()
