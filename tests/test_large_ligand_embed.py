"""Regression: large, flexible ligands must embed (CSD benchmark top-100-by-size failures).

~260 benchmark structures never built because RDKit's default distance-geometry start
(eigen-decomposition of the sampled distance matrix) fails on big flexible ligands -- first
inside ``stk.BuildingBlock(smiles=...)`` ("Embedding with seed value of 4 failed."), a
throwaway embed whose coordinates were always overwritten, then in MeCoBi's own ETKDGv3 embed.
The stk skeleton is now built without an embed, and MeCoBi's embed retries from random
coordinates (seeded, so still deterministic) only when the default start fails.
Pure RDKit/stk, no xtb.
"""

import numpy as np
import pytest
import stk
from rdkit import Chem
from rdkit.Chem import AllChem

from mecobi.assembly import _chem

# EGEJUY / LANMAS (Zn/Co): 2,6-bis(1-hexadecylbenzimidazol-2-yl)-4-hexadecyloxypyridine,
# ~180 atoms with H. Fails the default ETKDG start with both stk's and MeCoBi's seed.
BIP_C16 = ("CCCCCCCCCCCCCCCCOc1cc(-c2nc3ccccc3n2CCCCCCCCCCCCCCCC)"
           "nc(-c2nc3ccccc3n2CCCCCCCCCCCCCCCC)c1")


def _bond_key(bb):
    return sorted((b.get_atom1().get_id(), b.get_atom2().get_id(), b.get_order())
                  for b in bb.get_bonds())


@pytest.mark.parametrize("smiles", [
    "c1ccncc1CC[N-]C",                      # aromatic + anionic donor
    "CC(C)(C)c1cc(C=NCCN=Cc2ccccc2[O-])c([O-])cc1",  # salen-type
    "[C-]#[O+]",                            # carbonyl
    "c1cc[cH-]c1",                          # Cp-
    "O=C([O-])CN(CC(=O)[O-])CC(=O)[O-]",    # NTA
])
def test_skeleton_matches_stk_smiles_constructor(smiles):
    """Same atoms, charges, bonds AND bond orders (Kekulé, not aromatic 1.5) as stk builds."""
    ref = stk.BuildingBlock(smiles=smiles)
    sk = _chem._stk_skeleton(smiles)
    assert ([(a.get_atomic_number(), a.get_charge()) for a in ref.get_atoms()]
            == [(a.get_atomic_number(), a.get_charge()) for a in sk.get_atoms()])
    assert _bond_key(ref) == _bond_key(sk)


def test_default_embed_fails_on_bip_c16():
    """Guard the premise: if RDKit ever embeds this by default, the fallback is untested."""
    mol = Chem.AddHs(Chem.MolFromSmiles(BIP_C16))
    params = AllChem.ETKDGv3()
    params.randomSeed = 0xF00D
    assert AllChem.EmbedMolecule(mol, params=params) != 0


def test_large_flexible_tridentate_builds():
    mol = Chem.MolFromSmiles(BIP_C16)
    # donors: pyridine N + the two benzimidazole imine N (the aromatic N with no substituent)
    donors = [a.GetIdx() for a in mol.GetAtoms()
              if a.GetSymbol() == "N" and a.GetIsAromatic() and a.GetDegree() == 2]
    assert len(donors) == 3
    bb = _chem.ligand_building_block(BIP_C16, donors)
    P = bb.get_position_matrix()
    assert bb.get_num_atoms() == Chem.AddHs(mol).GetNumAtoms()
    assert np.isfinite(P).all() and np.ptp(P, axis=0).max() > 5.0  # a real conformer, not zeros
    atoms = list(bb.get_atoms())
    worst = max(np.linalg.norm(P[b.get_atom1().get_id()] - P[b.get_atom2().get_id()])
                for b in bb.get_bonds()
                if atoms[b.get_atom1().get_id()].get_atomic_number() > 1
                and atoms[b.get_atom2().get_id()].get_atomic_number() > 1)
    assert worst < 1.8


def test_fallback_is_deterministic_and_restores_params():
    params = AllChem.ETKDGv3()
    params.randomSeed = 0xF00D
    confs = []
    for _ in range(2):
        mol = Chem.AddHs(Chem.MolFromSmiles(BIP_C16))
        assert _chem._embed(mol, params)
        confs.append(mol.GetConformer().GetPositions())
    assert np.allclose(confs[0], confs[1])
    assert params.useRandomCoords is False
