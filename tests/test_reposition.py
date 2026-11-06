"""Reposition stranded monodentates (optimize.reposition_stranded_monodentates).

The site model seats donors on a generic 2.5 A shell and MCHammer pushes a bulky monodentate
out to ~3 A (OGOLAX). Slide it rigidly in to its CSD/covalent M-L reference. No xtb.
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


def test_slides_stranded_monodentate_to_reference(tmp_path):
    # W + a phenoxide O stranded at 3.2 A, its ring C 1.35 A beyond it (rigid ligand of 2 atoms).
    atoms = [
        ("W", (0.0, 0.0, 0.0)),
        ("O", (3.2, 0.0, 0.0)),                 # donor, stranded
        ("C", (3.2 + 1.35, 0.0, 0.0)),          # ring carbon bonded to O
    ]
    xyz = _xyz(tmp_path, atoms)
    con = _Constructed([(1, 2)])                # O-C bond; O and C are one ligand
    optimize.reposition_stranded_monodentates(xyz, con, metal_index=0, donor_indices=[1],
                                              metal_symbol="W", oxidation_state=6,
                                              coordination_number=5)
    out = optimize._read_xyz(xyz)
    ref = optimize._restraint_reference(3.2, "W", "O", ox=6, cn=5)
    w_o = math.dist(out[0][1], out[1][1])
    o_c = math.dist(out[1][1], out[2][1])
    assert abs(w_o - ref) < 1e-3                # donor slid to the CSD reference (~1.95 A)
    assert abs(o_c - 1.35) < 1e-3              # ligand translated rigidly -- internal bond intact


def test_leaves_a_well_placed_donor_alone(tmp_path):
    atoms = [("W", (0.0, 0.0, 0.0)), ("O", (1.95, 0.0, 0.0)), ("C", (3.3, 0.0, 0.0))]
    xyz = _xyz(tmp_path, atoms)
    before = xyz.read_text()
    optimize.reposition_stranded_monodentates(xyz, _Constructed([(1, 2)]), 0, [1],
                                              metal_symbol="W", oxidation_state=6,
                                              coordination_number=5)
    assert xyz.read_text() == before           # already at the reference -> untouched
