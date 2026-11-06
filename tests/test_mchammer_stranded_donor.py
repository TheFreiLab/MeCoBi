"""MCHammer must not be kept when it strands a sigma donor that the raw stk placement had bound.

Regression: for [Cp*Ir(N^N)Cl]+ (iminopyridine Schiff base) the raw stk placement put both chelate
N at 2.0 A, MCHammer pushed them to 2.4-3.4 A, and the fallback check kept MCHammer because its
only distance term fired beyond a fixed 3.3 A. One N then stayed off the metal through xtb in about
a fifth of a 1,800-complex library.
"""

import math
from pathlib import Path

import pytest

from mecobi import pipeline
from mecobi.model import Complex, Ligand, Metal


class _Atom:
    def __init__(self, idx):
        self._id = idx

    def get_id(self):
        return self._id


def _atom(el, idx):
    return type(el, (_Atom,), {})(idx)


class _Bond:
    def __init__(self, a, b):
        self._a, self._b = a, b

    def get_atom1(self):
        return self._a

    def get_atom2(self):
        return self._b


class _Constructed:
    """The three accessors _metal_bonded_donors / _stranded_donors read from an stk molecule."""

    def __init__(self, elements, positions, metal_bonds, other_bonds=()):
        self._atoms = [_atom(e, i) for i, e in enumerate(elements)]
        self._pos = positions
        self._bonds = [_Bond(self._atoms[0], self._atoms[j]) for j in metal_bonds]
        self._bonds += [_Bond(self._atoms[i], self._atoms[j]) for i, j in other_bonds]

    def get_atoms(self):
        return iter(self._atoms)

    def get_bonds(self):
        return iter(self._bonds)

    def get_position_matrix(self):
        return self._pos


def _piano_stool(r_n1, r_n2, r_cp=2.8):
    """Ir at the origin, a Cp ring (five bonded carbons) on +z, two N and a Cl on the other side."""
    els, pos = ["Ir"], [(0.0, 0.0, 0.0)]
    for k in range(5):
        a = 2 * math.pi * k / 5
        pos.append((1.2 * math.cos(a), 1.2 * math.sin(a), math.sqrt(r_cp ** 2 - 1.44)))
        els.append("C")
    for r, v in ((r_n1, (1, 0, -1)), (r_n2, (0, 1, -1)), (2.40, (-1, -1, -1))):
        n = math.sqrt(sum(c * c for c in v))
        pos.append(tuple(r * c / n for c in v))
    els += ["N", "N", "Cl"]
    ring = [(i, i % 5 + 1) for i in range(1, 6)]
    return _Constructed(els, pos, metal_bonds=range(1, 9), other_bonds=ring)


def test_bound_chelate_is_not_stranded():
    assert pipeline._stranded_donors(_piano_stool(2.05, 2.05), "Ir", 3) == 0


def test_chelate_n_far_out_is_stranded_below_the_fixed_ceiling():
    # 3.0 A is under the old fixed 3.3 A ceiling but ~1.45x the Ir-N reference
    assert pipeline._stranded_donors(_piano_stool(2.05, 3.0), "Ir", 3) == 1


def test_hapto_carbons_are_not_judged_by_distance():
    # the raw placement seats a Cp ring ~2.8 A out; xtb moves it on -- not a stranded donor
    assert pipeline._stranded_donors(_piano_stool(2.05, 2.05, r_cp=3.2), "Ir", 3) == 0


@pytest.mark.slow
def test_cp_ir_iminopyridine_chelate_is_seated_at_assembly(tmp_path):
    schiff = Ligand("COc1ccc(N=Cc2ccccn2)cc1OC")
    schiff.donor_override = [6, 13]
    cx = Complex(metal=Metal("Ir", 3), name="cpir_nn",
                 ligands=[Ligand("Cc1c(C)c(C)[c-](C)c1C"), schiff, Ligand("[Cl-]")])
    b = pipeline.build_complex(cx, tmp_path, relax=False)[0]
    lines = Path(b.xyz_path).read_text(encoding="utf-8").splitlines()
    atoms = [(ln.split()[0], tuple(map(float, ln.split()[1:4])))
             for ln in lines[2:2 + int(lines[0])]]
    ir = next(p for e, p in atoms if e == "Ir")
    n_dist = sorted(math.dist(p, ir) for e, p in atoms if e == "N")[:2]
    assert max(n_dist) < 2.3, n_dist


@pytest.mark.slow
def test_raw_fallback_does_not_fold_the_chelate_onto_the_metal(tmp_path):
    # once MCHammer is rejected, the raw placement it falls back to had this iminopyridine folded
    # onto Ir (imine C 1.87 A, both N at 2.0 A): the chelate repair must run on it first
    schiff = Ligand("COc1ccc2cc(N=Cc3ccccn3)ccc2c1")
    schiff.donor_override = [8, 15]
    cx = Complex(metal=Metal("Ir", 3), name="cpir_nn_fold",
                 ligands=[Ligand("Cc1c(C)c(C)[c-](C)c1C"), schiff, Ligand("[Cl-]")])
    b = pipeline.build_complex(cx, tmp_path, relax=False)[0]
    lines = Path(b.xyz_path).read_text(encoding="utf-8").splitlines()
    atoms = [(ln.split()[0], tuple(map(float, ln.split()[1:4])))
             for ln in lines[2:2 + int(lines[0])]]
    ir = atoms[b.metal_index][1]
    donors = set(b.donor_indices)
    n_dist = sorted(math.dist(p, ir) for i, (e, p) in enumerate(atoms) if e == "N" and i in donors)
    others = [math.dist(p, ir) for i, (e, p) in enumerate(atoms)
              if e != "H" and i != b.metal_index and i not in donors]
    assert len(n_dist) == 2 and max(n_dist) < 2.3, n_dist
    assert min(others) > 2.2, min(others)
