"""P1 + P3 error hardening (from the benchmark error analysis).

P1 — enumerate_isomers raises a typed UnsupportedTopology (not a raw KeyError) for a
(geometry, partition) with no fixed vertex topology, and build_complex(all_isomers=True)
falls back to the site model instead of crashing.
P3 — a ligand with no perceived donors gives a clear, ligand-naming error.
"""
import tempfile

import pytest

from mecobi import isomers, perception, pipeline
from mecobi.model import Complex, Geometry, Ligand, Metal


def _perceived(metal, ox, ligands, geometry=None):
    cx = Complex(metal=Metal(metal, ox), ligands=ligands, geometry=geometry)
    perception.perceive_complex(cx)
    return cx


def test_enumerate_isomers_raises_typed_unsupported_topology():
    # CN5 trigonal-bipyramidal is a site-model geometry with no fixed registry entry.
    cx = _perceived("Fe", 3, [Ligand("[Cl-]") for _ in range(5)])
    with pytest.raises(isomers.UnsupportedTopology):
        isomers.enumerate_isomers(cx, Geometry.TRIGONAL_BIPYRAMIDAL)


def test_all_isomers_falls_back_instead_of_keyerror():
    # denticity-4 ligand -> enumerate_site_isomers raises StereoNotSupported; the CN5
    # geometry has no fixed topology -> enumerate_isomers would KeyError. build_complex
    # must fall back to the single canonical isomer, not crash.
    trien = Ligand("NCCNCCNCCN", donor_override=[0, 3, 6, 9])  # linear tetraamine
    cx = Complex(
        metal=Metal("Fe", 3), ligands=[trien, Ligand("[Cl-]")],
        geometry=Geometry.TRIGONAL_BIPYRAMIDAL,
    )
    with tempfile.TemporaryDirectory() as d:
        results = pipeline.build_complex(cx, d, all_isomers=True, relax=False)
    assert len(results) >= 1


def test_zero_donor_ligand_gives_clear_named_error():
    # A ligand that perceives no donors (simulated with an empty override) must be
    # named, not surface a cryptic SiteAssignmentError.
    cx = Complex(
        metal=Metal("Fe", 2),
        ligands=[Ligand("[Cl-]"), Ligand("[Cl-]"), Ligand("CCOCC", donor_override=[])],
    )
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(perception.PerceptionError, match="No coordinating atoms"):
            pipeline.build_complex(cx, d, relax=False)
