"""Tripodal tridentates bind facially; the default isomer used to force every non-arene
tridentate meridional, which wrenched DECLUU's bis(2-pyridyl)ethyl-aryl tripod through its
neighbours under xtb (pyridine N-N and C-C fusions)."""

import itertools

import pytest

from mecobi import assembly, pipeline
from mecobi.assembly import sites
from mecobi.model import Complex, Geometry, Ligand, Metal

TRIPOD = "CC(c1[c-]cccc1)(c1ccccn1)c1ccccn1"   # DECLUU C,N,N tripod


def _lig(smiles, donors):
    return Ligand(smiles, donor_override=donors, denticity=len(donors))


@pytest.mark.parametrize("smiles,donors,tripodal", [
    ("C1CNCCNCCN1", [2, 5, 8], True),                         # tacn
    (TRIPOD, [3, 13, 19], True),
    ("CC(CP(C)C)(CP(C)C)CP(C)C", [3, 7, 11], True),         # triphos-type
    ("c1ccc(-c2cccc(-c3ccccn3)n2)nc1", [14, 15, 16], False),  # terpy
    ("NCCNCCN", [0, 3, 6], False),                            # dien
    ("CN(C)Cc1cccc(CN(C)C)[c-]1", [1, 10, 13], False),         # NCN pincer
])
def test_is_tripodal(smiles, donors, tripodal):
    assert assembly.is_tripodal(_lig(smiles, donors)) is tripodal


def _facial(assignment_sites, adj):
    return all(b in adj[a] for a, b in itertools.combinations(assignment_sites, 2))


def test_default_isomer_puts_a_tripod_on_a_facial_triple():
    cx = Complex(metal=Metal("Pd", 4), ligands=[
        _lig("[Cl-]", [0]), _lig("[Cl-]", [0]), _lig(TRIPOD, [3, 13, 19]), _lig("[Cl-]", [0])])
    spec = assembly.default_isomer(cx, Geometry.OCTAHEDRAL)
    adj = sites._adjacency(Geometry.OCTAHEDRAL, 6)
    assert _facial(spec.assignment[2], adj)


def test_terpy_default_stays_meridional():
    cx = Complex(metal=Metal("Ru", 2), ligands=[
        _lig("c1ccc(-c2cccc(-c3ccccn3)n2)nc1", [14, 15, 16])] + [_lig("[Cl-]", [0])] * 3)
    spec = assembly.default_isomer(cx, Geometry.OCTAHEDRAL)
    adj = sites._adjacency(Geometry.OCTAHEDRAL, 6)
    assert not _facial(spec.assignment[0], adj)


def test_all_isomers_enumerates_tripods_facially():
    cx = Complex(metal=Metal("Pd", 4), ligands=[
        _lig("[Cl-]", [0]), _lig("[Br-]", [0]), _lig(TRIPOD, [3, 13, 19]), _lig("[Cl-]", [0])])
    from mecobi import isomers
    specs = isomers.enumerate_site_isomers(cx, Geometry.OCTAHEDRAL)
    adj = sites._adjacency(Geometry.OCTAHEDRAL, 6)
    assert specs and all(_facial(s.assignment[2], adj) for s in specs)
    # the pipeline safety net keeps them all (nothing meridional to drop)
    assert pipeline._drop_meridional_tripods(cx, Geometry.OCTAHEDRAL, specs) == specs
