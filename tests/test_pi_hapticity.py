"""Prototype: eta2 alkene/alkyne and chelating dienes occupy ONE coordination site
per pi-bond (at the bond midpoint), not one per carbon -- so CN and geometry family
come out right. See feat/pi-hapticity-prototype."""
import pytest
from rdkit import Chem

from mecobi import geometry, perception, spin
from mecobi.model import Complex, Geometry, Ligand, Metal


def _perceive(smiles, donors):
    lig = Ligand(smiles, donor_override=donors)
    perception.perceive(lig)
    return lig


def test_eta2_alkene_is_one_site():
    lig = _perceive("C=C", [0, 1])
    assert lig.denticity == 1
    assert lig.pi_sites == [[0, 1]]


def test_eta2_alkyne_is_one_site():
    lig = _perceive("CC#CC", [1, 2])
    assert lig.denticity == 1
    assert lig.pi_sites == [[1, 2]]


def test_chelating_diene_is_two_sites():
    # 1,5-cyclooctadiene: two independent C=C -> bidentate
    lig = _perceive("C1CC=CCCC=C1", [2, 3, 6, 7])
    assert lig.denticity == 2
    assert len(lig.pi_sites) == 2


def test_diene_donors_given_as_ch2_snap_to_alkenes():
    # COD stored as C1=CCCC=CCC1 (alkenes 0,1,4,5) but donors indexed against the OTHER
    # traversal -> the saturated CH2 carbons [2,3,6,7]. Perception snaps them to the alkene
    # carbons so the eta2 sites are recovered (else denticity 4, a chair, wrong CN).
    lig = _perceive("C1=CCCC=CCC1", [2, 3, 6, 7])
    assert lig.denticity == 2
    assert lig.pi_sites == [[0, 1], [4, 5]]
    assert lig.coord_atoms == [0, 1, 4, 5]
    assert lig.donor_override == [0, 1, 4, 5]  # effective_donors stays consistent for assembly


def test_diene_snap_leaves_correct_donors_untouched():
    lig = _perceive("C1=CCCC=CCC1", [0, 1, 4, 5])
    assert lig.denticity == 2
    assert lig.pi_sites == [[0, 1], [4, 5]]


def test_diene_snap_does_not_touch_single_sp3_carbon_donor():
    # a lone sp3 carbon donor (an alkyl / cyclometalated benzyl next to an AROMATIC ring)
    # is not a diene signature -> never snapped.
    lig = _perceive("c1ccccc1C", [6])
    assert lig.denticity == 1
    assert lig.pi_sites == []
    assert lig.coord_atoms == [6]


def test_eta2_terminal_alkyne_acetylide_is_reprotonated():
    # BATKOX: an eta2 terminal alkyne mined as the acetylide anion [C-]#C-R (H stripped) -> the
    # built structure loses the terminal CH. Re-protonate to the neutral alkyne (0 charge, CH back).
    lig = _perceive("[C-]#CC(=C)C", [0, 1])
    assert lig.denticity == 1
    assert lig.pi_sites == [[0, 1]]
    assert lig.formal_charge == 0
    m = Chem.MolFromSmiles(lig.smiles)
    assert m.GetAtomWithIdx(0).GetTotalNumHs() == 1  # terminal CH restored


def test_sigma_acetylide_not_reprotonated():
    # a sigma acetylide (only the terminal C is a donor, denticity 1, NOT an eta2 pi-site) is a
    # real anion -> left as [C-], charge -1.
    lig = _perceive("[C-]#Cc1ccccc1", [0])
    assert lig.pi_sites == []
    assert lig.formal_charge == -1


def test_sigma_ligand_unaffected():
    lig = _perceive("N", [0])
    assert lig.denticity == 1
    assert lig.pi_sites == []


def test_zeise_is_square_planar_cn4():
    # [PtCl3(C2H4)]- : 3 Cl + one eta2 ethylene -> CN4, not CN5
    ligs = [Ligand("C=C", donor_override=[0, 1])] + [
        Ligand("[Cl-]", donor_override=[0]) for _ in range(3)
    ]
    cx = Complex(metal=Metal("Pt", 2), name="zeise", ligands=ligs)
    perception.perceive_complex(cx)
    assert cx.coordination_number == 4
    g = geometry.propose_geometry(
        cx.coordination_number, spin.d_count_or_none("Pt", 2),
        denticities=[l.denticity for l in cx.ligands],
    )
    assert g is Geometry.SQUARE_PLANAR


def test_pt_cod_cl2_is_cn4():
    # Pt(COD)Cl2 : chelating diene (2 sites) + 2 Cl -> CN4, not CN6
    ligs = [Ligand("C1CC=CCCC=C1", donor_override=[2, 3, 6, 7])] + [
        Ligand("[Cl-]", donor_override=[0]) for _ in range(2)
    ]
    cx = Complex(metal=Metal("Pt", 2), name="cod", ligands=ligs)
    perception.perceive_complex(cx)
    assert cx.coordination_number == 4


@pytest.mark.slow
def test_zeise_builds_and_relaxes_to_eta2():
    """xtb relaxes the eta2 ethylene to a symmetric, perpendicular pi-bond."""
    import tempfile
    import numpy as np
    from mecobi import pipeline

    ligs = [Ligand("C=C", donor_override=[0, 1])] + [
        Ligand("[Cl-]", donor_override=[0]) for _ in range(3)
    ]
    cx = Complex(metal=Metal("Pt", 2), name="zeise", ligands=ligs)
    with tempfile.TemporaryDirectory() as d:
        res = pipeline.build_complex(cx, d, relax=True, xtb_timeout_s=150)[0]
        lines = open(res.xyz_path).read().splitlines()
        n = int(lines[0])
        syms, P = [], []
        for ln in lines[2:2 + n]:
            p = ln.split(); syms.append(p[0]); P.append([float(x) for x in p[1:4]])
        P = np.array(P)
        M = P[res.metal_index]
        cC = [i for i in range(len(syms)) if syms[i] == "C"]
        C1, C2 = P[cC[0]], P[cC[1]]
        mid = (C1 + C2) / 2
        axis = (C2 - C1) / np.linalg.norm(C2 - C1)
        v = M - mid
        perp = np.degrees(np.arccos(abs(np.dot(v / np.linalg.norm(v), axis))))
        # symmetric, perpendicular eta2 coordination
        assert abs(np.linalg.norm(M - C1) - np.linalg.norm(M - C2)) < 0.2
        assert perp > 75
