"""Smoke tests for the scaffolded core: pure-logic pieces only (no migration yet)."""

import pytest

from mecobi import __version__
from mecobi.geometry import DenticityMismatchError, geometries_for_cn, propose_geometry
from mecobi.model import Complex, Geometry, Ligand, Metal, Spin
from mecobi.naming import format_charge, make_stem


def test_version():
    assert __version__


def test_charge_and_cn():
    # Ir(III) + tetradentate + 2x monodentate pyridine -> CN 6, charge +3.
    cx = Complex(
        metal=Metal("Ir", 3),
        ligands=[
            Ligand("SALEN", denticity=4),
            Ligand("c1ccncc1", denticity=1),
            Ligand("c1ccncc1", denticity=1),
        ],
    )
    assert cx.coordination_number == 6
    assert cx.total_charge == 3
    assert cx.spin is Spin.LOW


def test_anionic_ligand_lowers_charge():
    cx = Complex(metal=Metal("Pt", 2), ligands=[Ligand("[Cl-]", denticity=1, formal_charge=-1)])
    assert cx.total_charge == 1


@pytest.mark.parametrize(
    "cn,expected",
    [
        (2, (Geometry.LINEAR, Geometry.BENT)),
        (4, (Geometry.SQUARE_PLANAR, Geometry.TETRAHEDRAL)),
        (6, (Geometry.OCTAHEDRAL,)),
    ],
)
def test_geometry_registry(cn, expected):
    assert geometries_for_cn(cn) == expected


def test_unsupported_cn_hard_errors():
    # Invariant 3: no silent nearest-fit. CN 10+ has no geometry family -> hard error.
    with pytest.raises(DenticityMismatchError):
        geometries_for_cn(10)


def test_cn8_geometries():
    # CN 8 offers square-antiprism (default) and dodecahedral.
    assert geometries_for_cn(8) == (Geometry.SQUARE_ANTIPRISM, Geometry.DODECAHEDRAL)
    assert propose_geometry(8) is Geometry.SQUARE_ANTIPRISM


def test_propose_geometry_default():
    # CN4 is d-electron dependent: square-planar only for d8, else tetrahedral
    # (d10/main-group, and unknown d-count).
    assert propose_geometry(4, 8) is Geometry.SQUARE_PLANAR       # e.g. Pt(II)
    assert propose_geometry(4, 10) is Geometry.TETRAHEDRAL        # e.g. Ga(III)/Zn(II)
    assert propose_geometry(4) is Geometry.TETRAHEDRAL            # unknown d-count


def test_propose_geometry_cn4_chelation():
    # CN4 square-planar when the donors come from a strongly chelating (<=2 ligand)
    # set on a d4-d9 centre (single tetradentate / bis-bidentate enforce a plane);
    # four separate monodentates default tetrahedral.
    assert propose_geometry(4, 7, denticities=[4]) is Geometry.SQUARE_PLANAR          # tetradentate
    assert propose_geometry(4, 9, denticities=[2, 2]) is Geometry.SQUARE_PLANAR       # bis-bidentate
    assert propose_geometry(4, 6, denticities=[3, 1]) is Geometry.SQUARE_PLANAR       # tridentate+mono
    assert propose_geometry(4, 7, denticities=[2, 1, 1]) is Geometry.TETRAHEDRAL      # 3 ligands
    assert propose_geometry(4, 10, denticities=[1, 1, 1, 1]) is Geometry.TETRAHEDRAL  # 4 monodentate
    assert propose_geometry(4, 8, denticities=[1, 1, 1, 1]) is Geometry.SQUARE_PLANAR  # d8 still wins


def test_propose_geometry_cn4_chelate_rule_needs_d4_to_d9():
    # The chelate rule does not hold outside d4-d9: on the CSD benchmark <=2-ligand CN4
    # complexes are tetrahedral at d0 (63:0), d1-d3, d10 (260:177) and main group (336:8).
    assert propose_geometry(4, 0, denticities=[2, 2]) is Geometry.TETRAHEDRAL   # Ti(IV) HOLMEC
    assert propose_geometry(4, 2, denticities=[2, 2]) is Geometry.TETRAHEDRAL
    assert propose_geometry(4, 10, denticities=[2, 2]) is Geometry.TETRAHEDRAL  # Zn(acac)2
    assert propose_geometry(4, None, denticities=[2, 2]) is Geometry.TETRAHEDRAL  # main group


def test_propose_geometry_cn5_default_tbp():
    # CN5 tbp/spy is not input-predictable (Berry pseudorotation); default to the
    # majority (trigonal-bipyramidal), independent of d-count.
    assert geometries_for_cn(5)[0] is Geometry.TRIGONAL_BIPYRAMIDAL
    assert propose_geometry(5) is Geometry.TRIGONAL_BIPYRAMIDAL
    assert propose_geometry(5, 8) is Geometry.TRIGONAL_BIPYRAMIDAL
    assert propose_geometry(5, 2) is Geometry.TRIGONAL_BIPYRAMIDAL


def test_naming():
    assert format_charge(1) == "c1"
    assert format_charge(0) == "c0"
    assert format_charge(-1) == "cm1"
    assert make_stem("octa_3bi", -1, isomer_index=2) == "octa_3bi_iso02_cm1"
    assert make_stem("sq_2bi", 2, isomer_label="trans_AC") == "sq_2bi_trans_AC_c2"
