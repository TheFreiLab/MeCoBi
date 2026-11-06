"""Cyclometalated complexes relax unrestrained (keeps the aryl σ), but that also freed the
CO-ligands: Ru(tpa)(ppy) lost two tpa pyridine arms (3.7 / 5.3 A) and a tpa carbon took a site
(2.06 A). Detect-then-fix re-relaxes with the co-ligand donors restrained and the aryl's ortho
carbons pinned in the ideal σ pose, accepted only if every donor ends bound and nothing slipped.
"""

import math

import pytest

from mecobi import pipeline


def _write(tmp_path, atoms):
    p = tmp_path / "t.xyz"
    p.write_text(f"{len(atoms)}\n\n" + "".join(f"{e} {x} {y} {z}\n" for e, (x, y, z) in atoms))
    return p


def test_co_ligand_drift_flags_a_detached_donor_and_an_intruder(tmp_path):
    atoms = [("Ru", (0, 0, 0)),
             ("N", (2.07, 0, 0)),     # bound co-ligand donor
             ("N", (0, 5.3, 0)),      # drifted co-ligand donor
             ("C", (0, -2.06, 0)),    # co-ligand backbone carbon in the vacated site
             ("C", (0, 0, 2.0)),      # the σ aryl carbon (cyclometalated ligand: ignored)
             ("C", (0, 0, -2.3))]     # cyclometalated ligand atom near M: ignored as intruder
    xyz = _write(tmp_path, atoms)
    drifted, intruders = pipeline._co_ligand_drift(
        xyz, 0, [1, 2], {4, 5}, [1, 2, 4], "Ru", 2, 6)
    assert drifted == [2]
    assert intruders == [3]


def test_sigma_ortho_pins_target_the_ideal_sigma_pose(tmp_path):
    # σ-C at 3 A (stranded) with two ring neighbours 1.40 A away
    atoms = [("Ru", (0, 0, 0)), ("C", (3.0, 0, 0)), ("C", (3.7, 1.21, 0)), ("C", (3.7, -1.21, 0))]
    xyz = _write(tmp_path, atoms)
    pins = pipeline._sigma_ortho_pins(xyz, [(1, 2), (1, 3)], 0, {1}, "Ru", 2, 6)
    assert [p[1] for p in pins] == [2, 3]
    for _, _, d in pins:   # M-C ~2.0-2.1 A + 1.40 A at 120 deg -> ~3.0 A, not the stranded ~4.2 A
        assert 2.8 < d < 3.2


def test_sigma_aryl_slipped_detects_an_ortho_carbon_on_the_metal(tmp_path):
    bonds = [(1, 2), (1, 3)]
    sigma = [("Ru", (0, 0, 0)), ("C", (2.0, 0, 0)), ("C", (2.7, 1.21, 0)), ("C", (2.7, -1.21, 0))]
    eta = [("Ru", (0, 0, 0)), ("C", (2.1, 0, 0)), ("C", (1.9, 1.3, 0.3)), ("C", (2.7, -1.21, 0))]
    assert not pipeline._sigma_aryl_slipped(_write(tmp_path, sigma), bonds, 0, {1})
    assert pipeline._sigma_aryl_slipped(_write(tmp_path, eta), bonds, 0, {1})


@pytest.mark.slow
def test_ru_tpa_ppy_keeps_every_donor_bound(tmp_path):
    from mecobi.model import Complex, Ligand, Metal

    cx = Complex(metal=Metal("Ru", 2), ligands=[
        Ligand("N(Cc1ccccn1)(Cc1ccccn1)Cc1ccccn1"), Ligand("C1(C2=NC=CC=C2)=CC=CC=[C-]1")])
    (res,) = pipeline.build_complex(cx, tmp_path, relax=True)
    lines = open(res.xyz_path).read().splitlines()[2:]
    atoms = [(ln.split()[0], tuple(map(float, ln.split()[1:4]))) for ln in lines if ln.strip()]
    m = atoms[res.metal_index][1]
    assert all(math.dist(atoms[d][1], m) < 2.4 for d in res.donor_indices)
    assert any("donor drift" in w and "every donor bound" in w for w in res.warnings)
