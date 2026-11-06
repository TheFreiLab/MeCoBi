"""Planar-donor dihedral guard (pipeline._planar_donor_dihedrals + _monodentate_donors).

A MONODENTATE sp² donor (a lone pyridine N, carbonyl/imine O) binds with the metal in its ring plane
along the lone pair; the guard pins the M-D-A-B torsion so xtb can't bend the metal out of plane
(HUJCAR, MOFGEU). An sp² N is pinned AT the in-plane value (0/180), so a tilt a pre-relax step left
in the assembly is removed rather than frozen in; an sp² O keeps its assembled torsion.
Chelate/tripodal arms are excluded -- their orientation is set by the bite. Pure geometry, no xtb.
"""

from mecobi import pipeline


def _write_xyz(tmp_path, atoms):
    p = tmp_path / "frag.xyz"
    lines = [str(len(atoms)), ""]
    lines += [f"{el} {x:.4f} {y:.4f} {z:.4f}" for el, (x, y, z) in atoms]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


def _frag(donor, metal_z):
    return [
        ("Cu", (-1.00, -1.00, metal_z)),  # 0: metal, metal_z A above the donor's plane
        (donor, (0.00, 0.00, 0.00)),      # 1: donor
        ("C",  (1.30, 0.45, 0.00)),       # 2: ortho C (A)
        ("C",  (2.55, -0.20, 0.00)),      # 3: meta C  (B)
    ]


def test_sp2_nitrogen_is_pinned_in_plane(tmp_path):
    # A pyridine N whose assembly left the metal out of the ring plane (HUJCAR: the metal-excluded
    # UFF de-clash tipped the ring 50 deg) must be pinned AT the in-plane torsion, not at the tilted
    # assembled one -- pinning the assembled value froze the tilt in.
    atoms = _frag("N", 1.20)
    xyz = _write_xyz(tmp_path, atoms)
    bonds = [(0, 1), (1, 2), (2, 3)]
    dih = pipeline._planar_donor_dihedrals(xyz, bonds, metal_index=0, donor_indices=[1])
    assert len(dih) == 1
    m, d, a, b, target = dih[0]
    assert (m, d, a, b) == (0, 1, 2, 3)
    assembled = pipeline._dihedral(atoms[0][1], atoms[1][1], atoms[2][1], atoms[3][1])
    assert 20.0 < abs(assembled) < 90.0               # the fixture really is tilted (in-plane = 0)
    assert target == 0.0                              # ... and the pin is the in-plane value
    # snap=False reports the assembled torsion (how a tilt is measured)
    raw = pipeline._planar_donor_dihedrals(xyz, bonds, 0, [1], snap=False)[0][4]
    assert abs(raw - assembled) < 1e-6
    assert abs(pipeline._sp2_n_tilt(xyz, bonds, 0, [1]) - abs(assembled)) < 1e-6


def test_sp2_oxygen_keeps_the_assembled_value(tmp_path):
    # An sp² O (aryloxide/carbonyl) is NOT confined to the plane the way a pyridine N is: its pin
    # stays at whatever the assembly produced.
    atoms = _frag("O", 0.30)
    xyz = _write_xyz(tmp_path, atoms)
    bonds = [(0, 1), (1, 2), (2, 3)]
    target = pipeline._planar_donor_dihedrals(xyz, bonds, 0, [1])[0][4]
    assembled = pipeline._dihedral(atoms[0][1], atoms[1][1], atoms[2][1], atoms[3][1])
    assert abs(target - assembled) < 1e-6
    assert pipeline._sp2_n_tilt(xyz, bonds, 0, [1]) == 0.0   # only N donors count as tilted


def test_sp3_amine_is_left_free(tmp_path):
    # A σ amine (long N-C bond ~1.47, freely rotating) must NOT get a planar pin.
    atoms = [
        ("Cu", (-1.00, -1.00, 0.80)),
        ("N",  (0.00, 0.00, 0.00)),
        ("C",  (1.47, 0.00, 0.00)),     # sp3 C-N ~1.47 A -> fails the < 1.40 short-bond gate
        ("C",  (2.94, 0.00, 0.00)),
    ]
    xyz = _write_xyz(tmp_path, atoms)
    bonds = [(0, 1), (1, 2), (2, 3)]
    assert pipeline._planar_donor_dihedrals(xyz, bonds, 0, [1]) == []


# --------------------------------------------------------------------------- #
# monodentate scoping: only a ligand's SOLE donor gets the guard
# --------------------------------------------------------------------------- #

class _FakeAtom:
    def __init__(self, i):
        self._i = i

    def get_id(self):
        return self._i


class _FakeBond:
    def __init__(self, a, b):
        self._a, self._b = _FakeAtom(a), _FakeAtom(b)

    def get_atom1(self):
        return self._a

    def get_atom2(self):
        return self._b


class _FakeMol:
    def __init__(self, bonds):
        self._bonds = [_FakeBond(*b) for b in bonds]

    def get_bonds(self):
        return self._bonds


def test_monodentate_donors_excludes_chelate_arms():
    # metal 0; ligand A monodentate (donor 1, chain 1-2-3); ligand B bidentate (donors 4 & 7,
    # backbone 4-5-6-7). Only donor 1 is the sole donor of its ligand.
    bonds = [(0, 1), (0, 4), (0, 7),                 # metal-donor bonds (ignored by the backbone walk)
             (1, 2), (2, 3),                         # ligand A backbone
             (4, 5), (5, 6), (6, 7)]                 # ligand B backbone (connects the two donors)
    mol = _FakeMol(bonds)
    assert pipeline._monodentate_donors(mol, metal_index=0, donor_indices=[1, 4, 7]) == [1]


def test_monodentate_donors_all_monodentate():
    # three independent monodentate ligands -> all three donors are their ligand's sole donor
    bonds = [(0, 1), (0, 2), (0, 3), (1, 4), (2, 5), (3, 6)]
    mol = _FakeMol(bonds)
    assert pipeline._monodentate_donors(mol, 0, [1, 2, 3]) == [1, 2, 3]
