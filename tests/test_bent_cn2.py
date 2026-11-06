"""CN2 with a single chelate: bent on main-group and d8 centres, trans-spanning linear on d10.

A chelate spans two adjacent sites and the two linear sites are trans, so CN2 complexes held by
one bidentate failed with "Denticities [2] cannot fill the 2 linear sites" (175 of the full
benchmark's failures). In the crystal, the main-group ones (Ge/Sn/Pb(II), Ga/In/Tl(I)
beta-diketiminates, amidinates ...) are bent (donor-M-donor median 84 deg, 141 of 143 below
120), while the d10 ones (Ag(I), Cu(I), Au(I), Pd(0), Pt(0) with long diphosphines and
macrocycles) are near linear (median 163 deg). Either way the ligand is fitted around the metal
with both donors on their sites: its rigid conformer, seated on the sites, rarely reaches them.
"""

import numpy as np
import pytest

from mecobi import isomers, pipeline
from mecobi.assembly import sites
from mecobi.geometry import geometries_for_cn, propose_geometry
from mecobi.model import Complex, Geometry, Ligand, Metal

# Ge(II) beta-diketiminate (CSD ACEPOP); the nitrogens are atoms 2 and 25.
NACNAC = ("C=C([N-]c1c(C(C)C)cccc1C(C)C)C(Cc1ccccc1)=C(C)[N-]c1c(C(C)C)cccc1C(C)C", [2, 25])
# Pd(0) with a trans-spanning bis(diisopropylphosphino) ligand (CSD JOPJUV, P-Pd-P 163 deg).
TRANS_DIPHOS = ("CC(C)P(c1ccccc1CCc1ccccc1P(C(C)C)C(C)C)C(C)C", [3, 18])
FIT_NOTE = "CN2 chelate: ligand re-embedded around the metal"


def _geometry(res):
    rows = open(res.xyz_path).read().splitlines()[2:]
    X = np.array([[float(v) for v in r.split()[1:4]] for r in rows])
    m, (a, b) = res.metal_index, res.donor_indices[:2]
    v1, v2 = X[a] - X[m], X[b] - X[m]
    angle = float(np.degrees(np.arccos(v1 @ v2 / np.linalg.norm(v1) / np.linalg.norm(v2))))
    return angle, float(np.linalg.norm(v1)), float(np.linalg.norm(v2))


def _build(tmp_path, metal, ox, smiles, donors=None, n=1, **kw):
    lig = [Ligand(smiles=smiles, donor_override=donors) for _ in range(n)]
    (res,) = pipeline.build_complex(Complex(metal=Metal(metal, ox), ligands=lig, name="cn2"),
                                    tmp_path, relax=False, **kw)
    return res


def test_cn2_offers_linear_and_bent():
    assert geometries_for_cn(2) == (Geometry.LINEAR, Geometry.BENT)


@pytest.mark.parametrize("d_count, dents, expected", [
    (None, [2], Geometry.BENT),     # main group (no d count): one chelate is bent
    (8, [2], Geometry.BENT),        # d8 Rh(I)/Ir(I): bent too
    (10, [2], Geometry.LINEAR),     # d10: trans-spanning chelate
    (10, [1, 1], Geometry.LINEAR),  # two monodentates: unchanged
    (None, [1, 1], Geometry.LINEAR),
    (None, None, Geometry.LINEAR),  # no denticities known: unchanged
])
def test_proposed_cn2_geometry(d_count, dents, expected):
    assert propose_geometry(2, d_count, denticities=dents) is expected


def test_a_cn2_chelate_may_span_bent_or_linear_sites():
    assert sites.cis_pairs(Geometry.BENT) == [(0, 1)]
    assert sites.cis_pairs(Geometry.LINEAR) == [(0, 1)]       # trans-spanning chelate
    assert sites.default_assignment(Geometry.BENT, [2]) == {0: (0, 1)}
    assert sites.default_assignment(Geometry.LINEAR, [2]) == {0: (0, 1)}
    assert sites.default_assignment(Geometry.LINEAR, [1, 1]) == {0: (0,), 1: (1,)}


def test_cn2_chelate_has_one_isomer():
    lig = Ligand(smiles=NACNAC[0], donor_override=NACNAC[1])
    pipeline.resolve_perception(Complex(metal=Metal("Ge", 2), ligands=[lig]))
    cx = Complex(metal=Metal("Ge", 2), ligands=[lig])
    assert len(isomers.enumerate_site_isomers(cx, Geometry.BENT)) == 1


def test_main_group_cn2_chelate_builds_bent(tmp_path):
    res = _build(tmp_path, "Ge", 2, *NACNAC)
    assert res.connectivity_ok
    assert 60 < _geometry(res)[0] < 120


def test_d10_cn2_chelate_spans_trans_and_is_fitted_around_the_metal(tmp_path):
    res = _build(tmp_path, "Pd", 0, *TRANS_DIPHOS)
    assert any(FIT_NOTE in w for w in res.warnings)
    angle, d1, d2 = _geometry(res)
    assert angle > 165                       # rigid placement left it at 160 with a P far out
    assert 2.0 < d1 < 2.5 and 2.0 < d2 < 2.5  # both P at bonding distance before xtb


def test_without_the_fit_the_rigid_placement_is_kept(tmp_path):
    res = _build(tmp_path, "Pd", 0, *TRANS_DIPHOS, reembed_crowded=False)
    assert not any(FIT_NOTE in w for w in res.warnings)


def test_two_monodentates_stay_linear_and_are_not_refitted(tmp_path):
    res = _build(tmp_path, "Ag", 1, "N", n=2)
    assert _geometry(res)[0] > 150
    assert not any(FIT_NOTE in w for w in res.warnings)
