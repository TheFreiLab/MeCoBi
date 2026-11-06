"""Coordinate-map embed for flexible high-denticity wrappers (MetalloGen-style).

Pin the donors of a flexible multidentate to their target coordination sites and let RDKit
distance geometry fold the backbone around them, instead of a free embed (which clumps the
donors so a rigid placement can never seat them -- the #3 failure). Pure RDKit/stk, no torch.
"""


import numpy as np

from mecobi.assembly import _chem


def _kabsch_rmsd(P, Q):
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    U, _, Vt = np.linalg.svd(Pc.T @ Qc)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return float(np.sqrt(((Pc @ R.T - Qc) ** 2).sum() / len(P)))


def test_coord_map_enabled_env(monkeypatch):
    monkeypatch.delenv("MECOBI_COORD_MAP", raising=False)
    assert _chem._coord_map_enabled() is True           # default ON
    monkeypatch.setenv("MECOBI_COORD_MAP", "0")
    assert _chem._coord_map_enabled() is False
    monkeypatch.setenv("MECOBI_COORD_MAP", "1")
    assert _chem._coord_map_enabled() is True


def test_coord_map_seats_flexible_wrapper_donors_on_sites(monkeypatch):
    # TIZJUI's ligand: a thiophosphoryl with three flexible salicylaldimine arms (6 donors) that
    # must fold to wrap an octahedron. site_dirs = the six octahedral directions.
    smiles = "CN(N=Cc1ccccc1[O-])P(=S)(N(C)N=Cc1ccccc1[O-])N(C)N=Cc1ccccc1[O-]"
    donors = [2, 10, 15, 23, 26, 34]
    oct_dirs = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    ml = 2.1
    target = ml * np.asarray(oct_dirs, float)

    monkeypatch.setenv("MECOBI_COORD_MAP", "1")
    on = _chem.ligand_building_block(smiles, donors, site_dirs=oct_dirs).get_position_matrix()
    monkeypatch.setenv("MECOBI_COORD_MAP", "0")
    off = _chem.ligand_building_block(smiles, donors, site_dirs=oct_dirs).get_position_matrix()

    rmsd_on = _kabsch_rmsd(np.asarray([on[d] for d in donors]), target)
    rmsd_off = _kabsch_rmsd(np.asarray([off[d] for d in donors]), target)
    # the coord-map fold reaches the octahedral sites markedly better than the free embed
    # (the semi-rigid aromatic arms can't hit the IDEAL octahedron exactly, but come far closer)
    assert rmsd_on < rmsd_off - 0.3
    assert rmsd_on < 1.8
