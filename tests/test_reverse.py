"""xyz -> SMILES reverse conversion (item T)."""

import pytest

from mecobi import reverse
from mecobi.model import Complex, Geometry, Ligand, Metal


def test_reverse_rejects_multi_metal():
    xyz = "2\n\nFe 0 0 0\nFe 2 0 0\n"
    with pytest.raises(reverse.ReverseError):
        reverse.reverse_xyz(xyz)


def test_reverse_lone_halide_is_anion():
    # metal + two chlorides far apart -> two [Cl-] ligands.
    xyz = "3\n\nZn 0 0 0\nCl 2.2 0 0\nCl -2.2 0 0\n"
    rc = reverse.reverse_xyz(xyz)
    assert rc.metal == "Zn"
    assert [l.smiles for l in rc.ligands] == ["[Cl-]", "[Cl-]"]
    assert rc.coordination_number == 2
    assert rc.backend == "builtin"
    assert rc.complex_smiles is None and rc.to_trex() is None


# --------------------------------------------------------------------------- #
# backend / notation selection
# --------------------------------------------------------------------------- #

def test_available_backends_and_notations():
    # builtin / isomer are always present; the optional extras appear only if
    # their package is installed (we don't assert on that, just the invariants).
    assert reverse.available_backends()[0] == "builtin"
    assert "isomer" in reverse.available_notations()
    for name in reverse.available_backends():
        assert name in ("builtin", "xyz2mol_tm")
    for name in reverse.available_notations():
        assert name in ("isomer", "trex")


def test_normalizes_extra_column_xyz():
    # atom lines carrying an extra gradient triple (7 tokens) must not break the
    # builtin reader, and must be cleaned to 4 columns for the third-party tools.
    xyz = "1\n energy: -1 gnorm: 0 xtb: 6.7.1 (x)\nZn 0 0 0 0.1 0.2 0.3\n"
    assert reverse._normalized_xyz(xyz).splitlines()[2].split() == ["Zn", "0.000000", "0.000000", "0.000000"]


def test_representation_registry_shape():
    for rep in reverse.available_representations():
        assert {"key", "label"} <= set(rep)
        assert rep["key"] in ("complex_smiles", "trex", "msmiles")
    with pytest.raises(reverse.ReverseError, match="unknown representation"):
        reverse.render_representation("1\n\nZn 0 0 0\n", "nope", 0)


def test_unknown_backend_raises():
    xyz = "3\n\nZn 0 0 0\nCl 2.2 0 0\nCl -2.2 0 0\n"
    with pytest.raises(reverse.ReverseError, match="unknown backend"):
        reverse.reverse_xyz(xyz, backend="nope")


def test_xyz2mol_tm_requires_charge():
    # Missing overall_charge is caught before we ever try to import the package.
    xyz = "3\n\nZn 0 0 0\nCl 2.2 0 0\nCl -2.2 0 0\n"
    with pytest.raises(reverse.ReverseError, match="overall_charge"):
        reverse.reverse_xyz(xyz, backend="xyz2mol_tm", overall_charge=None)


@pytest.mark.skipif(
    "xyz2mol_tm" in reverse.available_backends(),
    reason="xyz2mol_tm installed; testing the not-installed guidance path",
)
def test_xyz2mol_tm_missing_package_message():
    xyz = "3\n\nZn 0 0 0\nCl 2.2 0 0\nCl -2.2 0 0\n"
    with pytest.raises(reverse.ReverseError, match="reverse-tm"):
        reverse.reverse_xyz(xyz, backend="xyz2mol_tm", overall_charge=0)


@pytest.mark.skipif(
    "trex" in reverse.available_notations(),
    reason="trex installed; testing the not-installed guidance path",
)
def test_trex_missing_package_message():
    xyz = "3\n\nZn 0 0 0\nCl 2.2 0 0\nCl -2.2 0 0\n"
    with pytest.raises(reverse.ReverseError, match="trex"):
        reverse.to_trex(xyz, overall_charge=0)


# --------------------------------------------------------------------------- #
# slow: build then reverse (round trip through stk assembly, no xtb)
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_roundtrip_square_planar_pt(tmp_path):
    from mecobi import pipeline

    cx = Complex(metal=Metal("Pt", 2), geometry=Geometry.SQUARE_PLANAR,
                 ligands=[Ligand("N"), Ligand("N"), Ligand("[Cl-]"), Ligand("[Cl-]")])
    res = pipeline.build_complex(cx, tmp_path, relax=False)
    rc = reverse.reverse_xyz(res[0].xyz_path)
    assert rc.metal == "Pt"
    assert rc.coordination_number == 4
    smis = sorted(l.smiles for l in rc.ligands)
    assert smis == ["N", "N", "[Cl-]", "[Cl-]"]


@pytest.mark.slow
@pytest.mark.skipif(
    "xyz2mol_tm" not in reverse.available_backends(),
    reason="optional xyz2mol_tm backend not installed",
)
def test_roundtrip_xyz2mol_tm_backend(tmp_path):
    from mecobi import pipeline

    cx = Complex(metal=Metal("Pt", 2), geometry=Geometry.SQUARE_PLANAR,
                 ligands=[Ligand("N"), Ligand("N"), Ligand("[Cl-]"), Ligand("[Cl-]")])
    res = pipeline.build_complex(cx, tmp_path, relax=False)
    rc = reverse.reverse_xyz(res[0].xyz_path, backend="xyz2mol_tm", overall_charge=0)
    assert rc.backend == "xyz2mol_tm"
    # whole-complex SMILES includes the metal centre with dative bonds.
    assert rc.complex_smiles and "Pt" in rc.complex_smiles
    # per-ligand decomposition is still recovered alongside it.
    assert sorted(l.smiles for l in rc.ligands) == ["N", "N", "[Cl-]", "[Cl-]"]


@pytest.mark.slow
@pytest.mark.skipif(
    "trex" not in reverse.available_notations(),
    reason="optional trex package not installed",
)
def test_roundtrip_trex_notation(tmp_path):
    from mecobi import pipeline

    cx = Complex(metal=Metal("Pt", 2), geometry=Geometry.SQUARE_PLANAR,
                 ligands=[Ligand("N"), Ligand("N"), Ligand("[Cl-]"), Ligand("[Cl-]")])
    res = pipeline.build_complex(cx, tmp_path, relax=False)
    trex = reverse.to_trex(res[0].xyz_path, overall_charge=0)
    # canonical T-REX has the metal{ox} head and a ligand payload list.
    assert trex.startswith("Pt{+2}")
    assert "L=[" in trex


@pytest.mark.slow
def test_roundtrip_octahedral_bidentate_donor_indices(tmp_path):
    from mecobi import pipeline

    bipy = "c1ccc(-c2ccccn2)nc1"
    cx = Complex(metal=Metal("Ir", 3), geometry=Geometry.OCTAHEDRAL,
                 ligands=[Ligand(bipy), Ligand(bipy), Ligand("[Cl-]"), Ligand("[Cl-]")])
    res = pipeline.build_complex(cx, tmp_path, relax=False)
    rc = reverse.reverse_xyz(res[0].xyz_path)
    assert rc.metal == "Ir" and rc.coordination_number == 6
    chelates = [l for l in rc.ligands if len(l.donor_atoms) == 2]
    assert len(chelates) == 2
    # both recovered chelates coordinate through two atoms (the bipyridine N,N).
    assert all(len(l.donor_atoms) == 2 for l in chelates)
