"""Squeezed donors, Y bond lengths and unbound donors after relax (QEMTOR / LAYFID, 2026-10-01).

* QEMTOR (Ti(IV), TMS-amido tripod): the assembly put an amido N 1.57 A from Ti (CSD 2.07). The
  short-multiple-bond guard in ``_restraint_reference`` read that as an imido and held it, so it
  relaxed to 1.66 A. Only a donor that can carry M=X / M#X keeps a short distance.
* LAYFID (Y(III)): Y was missing from the mined M-L table, so Y-N fell back to the covalent sum
  (2.61 A) x 1.3 trust and donors stranded at 2.9-3.3 A were kept there.
* Nothing flagged LAYFID: the dissociation guard only fires past max(3.1 A, 1.4 x reference).

Fast: no xtb, no torch.
"""

import pytest

from mecobi import optimize, pipeline


def _atoms(*spec):
    return [(el, tuple(p)) for el, p in spec]


@pytest.fixture
def table(monkeypatch):
    fake = {"metal_os_donor_cn": {}, "metal_os_donor": {},
            "metal_donor": {"Ti|N": {"mean": 2.07, "n": 500}, "Ti|O": {"mean": 1.95, "n": 500},
                            "Ti|Cl": {"mean": 2.30, "n": 500}}}
    monkeypatch.setattr(optimize, "_ML_LOADED", True)
    monkeypatch.setattr(optimize, "_ML_TABLE", fake)


def test_can_multiple_bond_distinguishes_imido_from_amido():
    ti = ("Ti", (0.0, 0.0, 0.0))
    # imido Ti=N-C: one heavy neighbour -> may be short
    imido = _atoms(ti, ("N", (1.70, 0, 0)), ("C", (3.15, 0, 0)))
    assert optimize._can_multiple_bond(imido, 1, 0)
    # terminal oxo: no heavy neighbour
    oxo = _atoms(ti, ("O", (1.62, 0, 0)), ("H", (2.5, 0, 0)))
    assert optimize._can_multiple_bond(oxo, 1, 0)
    # amido N(C)(Si): two heavy neighbours -> a short distance is a squeeze
    amido = _atoms(ti, ("N", (1.57, 0, 0)), ("C", (2.2, 1.2, 0)), ("Si", (2.3, -1.5, 0)))
    assert not optimize._can_multiple_bond(amido, 1, 0)
    # a halide never forms a multiple bond
    assert not optimize._can_multiple_bond(_atoms(ti, ("Cl", (1.3, 0, 0))), 1, 0)


def test_squeezed_amido_is_restrained_to_the_reference(table):
    # the multiple-bond guard is kept for oxo/imido ...
    assert optimize._restraint_reference(1.57, "Ti", "N", multiple_bond_ok=True) == 1.57
    # ... but a squeezed amido is pushed out to the CSD length
    assert optimize._restraint_reference(1.57, "Ti", "N", multiple_bond_ok=False) == 2.07
    # unaffected above the short-bond ratio
    assert optimize._restraint_reference(2.00, "Ti", "N", multiple_bond_ok=False) == 2.07


def test_squeezed_donor_without_csd_entry_gets_covalent_target(monkeypatch):
    monkeypatch.setattr(optimize, "_ML_LOADED", True)
    monkeypatch.setattr(optimize, "_ML_TABLE", None)
    target = optimize._cov_radius("Ru") + optimize._cov_radius("N")
    assert optimize._restraint_reference(1.2, "Ru", "N", multiple_bond_ok=False) == target
    assert optimize._restraint_reference(1.2, "Ru", "N") == 1.2  # default unchanged


def test_yttrium_is_in_the_shipped_bond_length_table(monkeypatch):
    monkeypatch.setattr(optimize, "_ML_LOADED", False)  # reload the shipped table
    # sigma and hapto carbons are separate classes: Y-C(alkyl/aryl) ~2.4 A, Y-C(Cp) ~2.7 A
    for donor, lo, hi in (("N", 2.3, 2.6), ("O", 2.2, 2.45), ("C", 2.3, 2.55), ("Cl", 2.5, 2.7),
                          (optimize.ETA_CARBON, 2.55, 2.8)):
        ref = optimize._ml_target("Y", 3, donor, 5)
        assert ref is not None and lo < ref < hi, (donor, ref)
    # LAYFID's stranded amido N (2.93 A) is no longer within the trusted window
    assert optimize._restraint_reference(2.93, "Y", "N", ox=3, cn=5) < 2.6


def test_unbound_donors_flags_donors_beyond_reference(tmp_path, table):
    xyz = tmp_path / "ti.xyz"
    # Ti with one bonded N (2.05), one N stranded at 3.1 (> 1.3 x 2.07) and one bonded Cl
    xyz.write_text("4\n\nTi 0 0 0\nN 2.05 0 0\nN 0 3.10 0\nCl 0 0 2.30\n", encoding="utf-8")
    out = pipeline._unbound_donors(xyz, 0, [1, 2, 3], "Ti", 4, 3)
    assert [(d, el) for d, el, _, _ in out] == [(2, "N")]
    assert out[0][3] == pytest.approx(2.07)
    assert pipeline._unbound_donors(xyz, 0, [1, 3], "Ti", 4, 3) == []
