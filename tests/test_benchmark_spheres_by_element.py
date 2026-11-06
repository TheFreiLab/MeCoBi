"""Crystal reference spheres/cores pick the donors by the bundle's DECLARED donor elements.

The frozen spheres took "the cn nearest non-H atoms": when a declared donor (here an iodide at
2.8 A) sits farther than a non-donor backbone carbon (2.6 A), the carbon stood in for it
(KUFZOD, ICIHAF, NAPMUO). By element, the declared I is taken and the C is not.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "benchmark"))
from cif_geometry import coordination_sphere, coordination_sphere_by_elements
from extract_cores import depth2_core

# P1, 20 A cubic cell: Ni with N at 2.0 (x2), a sigma C at 2.0, a stray backbone C at 2.6 and
# the declared iodide at 2.8 A.
CIF = """data_T
_cell_length_a 20
_cell_length_b 20
_cell_length_c 20
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_symmetry_space_group_name_H-M 'P 1'
loop_
_symmetry_equiv_pos_as_xyz
x,y,z
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Ni1 Ni 0.5 0.5 0.5
N1 N 0.6 0.5 0.5
N2 N 0.4 0.5 0.5
C1 C 0.5 0.6 0.5
I1 I 0.5 0.36 0.5
C2 C 0.5 0.5 0.63
"""
DECLARED = ["N", "N", "C", "I"]


def test_nearest_atoms_lose_the_declared_iodide():
    assert sorted(coordination_sphere(CIF, "Ni", 4)[2]) == ["C", "C", "N", "N"]


def test_sphere_by_element_takes_the_declared_iodide():
    _, donors, els = coordination_sphere_by_elements(CIF, "Ni", DECLARED)
    assert sorted(els) == sorted(DECLARED)
    assert any(abs(p[1] - 7.2) < 1e-6 for p in donors)          # the I at y = 0.36 * 20


def test_core_by_element_takes_the_declared_iodide():
    core = depth2_core(CIF, "Ni", 4, DECLARED)
    assert sorted(a["el"] for a in core["donors"]) == sorted(DECLARED)


def test_missing_declared_element_gives_none():
    assert coordination_sphere_by_elements(CIF, "Ni", ["N", "N", "C", "Br"]) is None
