"""Main-group ns² lone pair drives CN5 to square-pyramidal.

Regression for EPAQOE (BiCl3Br2): Bi(III) has a stereochemically active 6s² lone
pair, so its five donors are square-pyramidal, not trigonal-bipyramidal. The CN5
default (tbp) is right for transition metals but wrong for inert-pair cations.
"""
from mecobi import geometry, spin
from mecobi.model import Geometry


def test_lone_pair_detector():
    # inert-pair cations: ns2 lone pair retained
    assert spin.has_stereo_active_lone_pair("Bi", 3)
    assert spin.has_stereo_active_lone_pair("Sn", 2)
    assert spin.has_stereo_active_lone_pair("Pb", 2)
    assert spin.has_stereo_active_lone_pair("Sb", 3)
    assert spin.has_stereo_active_lone_pair("Te", 4)
    # no lone pair: fully oxidised or no ns2
    assert not spin.has_stereo_active_lone_pair("Bi", 5)
    assert not spin.has_stereo_active_lone_pair("Sn", 4)
    assert not spin.has_stereo_active_lone_pair("Al", 3)
    # transition metals aren't in the main-group table
    assert not spin.has_stereo_active_lone_pair("Fe", 2)
    assert not spin.has_stereo_active_lone_pair("Os", 2)


def test_cn5_lone_pair_is_square_pyramidal():
    lp = spin.has_stereo_active_lone_pair("Bi", 3)
    assert geometry.propose_geometry(5, None, lone_pair=lp) is Geometry.SQUARE_PYRAMIDAL


def test_cn5_transition_metal_stays_tbp():
    # d-count metals keep the tbp majority default (no lone pair)
    for m, ox in [("Fe", 2), ("Mn", 2), ("Co", 3)]:
        lp = spin.has_stereo_active_lone_pair(m, ox)
        g = geometry.propose_geometry(5, spin.d_count_or_none(m, ox), lone_pair=lp)
        assert g is Geometry.TRIGONAL_BIPYRAMIDAL


def test_lone_pair_only_affects_cn5():
    # the flag must not perturb other CNs (CN6 octahedral regardless)
    assert geometry.propose_geometry(6, None, lone_pair=True) is Geometry.OCTAHEDRAL
    assert geometry.propose_geometry(4, None, lone_pair=True) is Geometry.TETRAHEDRAL
