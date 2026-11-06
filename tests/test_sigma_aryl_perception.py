"""A pure-hydrocarbon sigma-aryl carbanion binds through its anionic carbon, not as an eta6 cap.

Regression: ``[c-]1ccccc1`` hit the pure-hydrocarbon arene rule, so Pb/Sn/Bi aryls (TUMTEC,
Pb(Ph)2(chelate)2) were built as bent metallocenes. ~4% of the CSD benchmark has such a ligand.
"""

import pytest

from mecobi import perception
from mecobi.model import Ligand


def _perceive(smiles):
    lig = Ligand(smiles)
    perception.perceive(lig)
    return lig


@pytest.mark.parametrize("smiles,donors", [
    ("[c-]1ccccc1", [0]),                       # phenyl
    ("Cc1cc[c-]cc1", [4]),                      # p-tolyl
    ("c1ccc(-c2cccc[c-]2)[c-]c1", [9, 10]),     # biphenyl-2,2'-diyl, sigma,sigma chelate
])
def test_sigma_aryl_carbanion_is_sigma(smiles, donors):
    lig = _perceive(smiles)
    assert lig.coord_atoms == donors
    assert lig.pi_sites == []
    assert lig.denticity == len(donors)


@pytest.mark.parametrize("smiles,ring", [
    ("c1ccccc1", 6),                            # benzene, eta6
    ("CC(C)c1ccc(C)cc1", 6),                    # p-cymene, eta6
    ("[cH-]1cccc1", 5),                         # Cp, eta5
    ("C[c-]1c(C)c(C)c(C)c1C", 5),               # Cp*: 5-ring charge on a methylated C, still eta5
])
def test_arenes_and_cp_stay_eta_caps(smiles, ring):
    lig = _perceive(smiles)
    assert [len(s) for s in lig.pi_sites] == [ring]
    assert lig.denticity == 1
