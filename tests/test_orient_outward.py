"""Swing a folded ligand body away from the metal (optimize.orient_monodentate_body_outward).

A bidentate is rotated about its donor-donor axis; the move must not land its body in a
neighbouring ligand (ZIHHUT: two BINAPs rotated this way went from 0 to 19 interpenetrating
inter-ligand pairs, which nothing downstream untangles). No xtb.
"""

import math

from mecobi import optimize


class _Atom:
    def __init__(self, i): self._i = i
    def get_id(self): return self._i


class _Bond:
    def __init__(self, a, b): self._a, self._b = a, b
    def get_atom1(self): return _Atom(self._a)
    def get_atom2(self): return _Atom(self._b)


class _Constructed:
    def __init__(self, bonds): self._bonds = bonds
    def get_bonds(self): return [_Bond(a, b) for a, b in self._bonds]


def _xyz(tmp_path, atoms):
    lines = [str(len(atoms)), ""]
    lines += [f"{el} {x:.4f} {y:.4f} {z:.4f}" for el, (x, y, z) in atoms]
    p = tmp_path / "c.xyz"
    p.write_text("\n".join(lines) + "\n")
    return p


# Pt + a bidentate whose two donors lie on an axis at x = 1.5 and whose backbone carbons are
# folded toward the metal (x = 0.8, 0.94 A from Pt): a 180 deg turn about the P-P axis puts them
# at x = 2.2, on the far side.
_CHELATE = [
    ("Pt", (0.0, 0.0, 0.0)),
    ("P", (1.5, 1.5, 0.0)),
    ("P", (1.5, -1.5, 0.0)),
    ("C", (0.8, 0.5, 0.0)),
    ("C", (0.8, -0.5, 0.0)),
]
_CHELATE_BONDS = [(0, 1), (0, 2), (1, 3), (3, 4), (4, 2)]


def test_folded_chelate_is_swung_outward(tmp_path):
    xyz = _xyz(tmp_path, _CHELATE)
    n = optimize.orient_monodentate_body_outward(xyz, _Constructed(_CHELATE_BONDS), 0, [1, 2])
    out = optimize._read_xyz(xyz)
    assert n == 1
    assert min(math.dist(out[0][1], out[i][1]) for i in (3, 4)) > 2.0


def test_rotation_into_a_neighbour_is_reverted(tmp_path):
    # a monodentate whose body atom sits 0.3 A from where the chelate's backbone would land
    atoms = _CHELATE + [("P", (0.0, 0.0, -2.3)), ("C", (2.2, 0.5, 0.3)), ("C", (0.0, 0.0, -3.8))]
    bonds = _CHELATE_BONDS + [(0, 5), (5, 6), (5, 7)]
    xyz = _xyz(tmp_path, atoms)
    before = xyz.read_text()
    n = optimize.orient_monodentate_body_outward(xyz, _Constructed(bonds), 0, [1, 2, 5])
    assert n == 0
    assert xyz.read_text() == before
