"""Stage 3 tests: spin/uhf + isomer enumeration (fast); xtb relaxation (slow)."""

from pathlib import Path

import pytest

from mecobi import inputs, pipeline, spin
from mecobi.isomers import enumerate_isomers
from mecobi.model import Complex, Geometry, Ligand, Metal, Spin
from mecobi.optimize import (
    DISSOCIATION_THRESHOLD_A,
    XtbError,
    _metal_donors,
    _write_constraint_file,
    relax_with_xtb,
    spin_to_uhf,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_CSV = Path(__file__).resolve().parent / "fixtures" / "test_compounds.csv"

O, SP, L = Geometry.OCTAHEDRAL, Geometry.SQUARE_PLANAR, Geometry.LINEAR
T = Geometry.TETRAHEDRAL


# --------------------------------------------------------------------------- #
# spin model — fast
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "symbol,ox,geom,spin_state,expected_uhf",
    [
        ("Ir", 3, O, Spin.LOW, 0),    # d6 LS
        ("Ir", 3, O, Spin.HIGH, 4),   # d6 HS
        ("Fe", 3, O, Spin.LOW, 1),    # d5 LS
        ("Fe", 3, O, Spin.HIGH, 5),   # d5 HS
        ("Ni", 2, O, Spin.LOW, 2),    # d8
        ("Pt", 2, SP, Spin.LOW, 0),   # d8 square planar
        ("Au", 1, L, Spin.LOW, 0),    # d10
        ("Cr", 3, O, Spin.LOW, 3),    # d3
        # CN 3/5/7-9 used to fall back to 5 degenerate orbitals (LOW came out HIGH)
        ("Ir", 3, Geometry.SQUARE_PYRAMIDAL, Spin.LOW, 0),       # d6 IrHCl(PCN), was 4
        ("Fe", 0, Geometry.TRIGONAL_BIPYRAMIDAL, Spin.LOW, 0),   # d8 Fe(CO)5, was 2
        ("Cu", 2, Geometry.SQUARE_PYRAMIDAL, Spin.LOW, 1),       # d9
        ("Ni", 2, Geometry.SQUARE_PYRAMIDAL, Spin.LOW, 0),       # d8 LS
        ("Co", 2, Geometry.SQUARE_PYRAMIDAL, Spin.LOW, 1),       # d7 LS
        ("Mo", 4, Geometry.DODECAHEDRAL, Spin.LOW, 0),           # d2 [Mo(CN)8]4-, was 2
        ("Mo", 4, Geometry.SQUARE_ANTIPRISM, Spin.LOW, 0),       # d2
        ("Cu", 1, Geometry.TRIGONAL_PLANAR, Spin.LOW, 0),        # d10
        ("Fe", 3, Geometry.TRIGONAL_BIPYRAMIDAL, Spin.HIGH, 5),  # HIGH is unchanged
        ("Ru", 2, Geometry.TRIGONAL_BIPYRAMIDAL, Spin.LOW, 0),   # d6 CN5 placed TBP: SP singlet
        ("Cr", 3, Geometry.SQUARE_PYRAMIDAL, Spin.LOW, 3),       # d3 quartet, like t2g^3
        ("Fe", 4, Geometry.SQUARE_PYRAMIDAL, Spin.LOW, 2),       # d4 triplet
    ],
)
def test_unpaired_electrons(symbol, ox, geom, spin_state, expected_uhf):
    assert spin.unpaired_electrons(symbol, ox, geom, spin_state) == expected_uhf


@pytest.mark.parametrize(
    "symbol,ox,expected_uhf",
    [
        ("Sn", 4, 0),   # d10s0 closed shell
        ("Sn", 2, 0),   # 5s2 lone pair, diamagnetic
        ("Pb", 2, 0),
        ("Bi", 3, 0),
        ("Bi", 5, 0),
        ("Ga", 3, 0),
        ("In", 3, 0),
        ("Tl", 1, 0),
        ("Ge", 4, 0),
        ("Sn", 3, 1),   # main-group radical (odd valence) -> one unpaired
        ("Sn", -4, 0),  # over-reduced (8 s+p e-) still even -> closed
    ],
)
def test_main_group_unpaired(symbol, ox, expected_uhf):
    # geometry/spin are irrelevant for main-group centres
    assert spin.unpaired_electrons(symbol, ox, O, Spin.LOW) == expected_uhf
    assert spin.unpaired_electrons(symbol, ox, T, Spin.HIGH) == expected_uhf


@pytest.mark.parametrize(
    "symbol,ox,geom,n_mult,spin_state,expected_uhf",
    [
        ("Re", 5, O, 2, Spin.LOW, 0),    # trans-[ReO2(PR3)4]+: d2 paired in dxy
        ("Re", 5, O, 1, Spin.LOW, 0),    # ReOCl3(PPh3)2 mono-oxo
        ("Tc", 5, SP, 1, Spin.LOW, 0),   # [TcOCl4]- (any splitting pattern)
        ("Os", 6, O, 2, Spin.LOW, 0),    # trans-OsO2 d2
        ("Re", 5, O, 0, Spin.LOW, 2),    # no oxo: plain octahedral t2g triplet
        ("V", 3, O, 0, Spin.LOW, 2),     # [V(H2O)6]3+ stays a triplet
        ("Re", 5, O, 2, Spin.HIGH, 2),   # explicit high spin still forces the triplet
        ("Mo", 5, O, 1, Spin.LOW, 1),    # d1 oxo: one electron is one electron
        ("Re", 3, O, 1, Spin.LOW, 2),    # d4 untouched by the rule (t2g LS -> 2)
    ],
)
def test_d2_terminal_oxo_singlet(symbol, ox, geom, n_mult, spin_state, expected_uhf):
    assert spin.unpaired_electrons(symbol, ox, geom, spin_state,
                                   n_terminal_multiple=n_mult) == expected_uhf


def test_uhf_for_counts_terminal_oxo_ligands():
    pnp = ("N(CCC[P+](C1=CC=CC=C1)(C2=CC=CC=C2)C3=CC=CC=C3)(CP(C4=CC=CC=C4)C5=CC=CC=C5)"
           "CP(C6=CC=CC=C6)C7=CC=CC=C7")
    cx = Complex(metal=Metal("Re", 5),
                 ligands=[Ligand(pnp), Ligand(pnp), Ligand("[O-2]"), Ligand("[O-2]")])
    assert pipeline._n_terminal_oxo_nitrido_ligands(cx) == 2
    warnings: list[str] = []
    assert pipeline._uhf_for(cx, O, warnings) == 0
    assert any("singlet" in w for w in warnings)
    # aqua / hydroxide carry H: not terminal multiple-bond donors
    aq = Complex(metal=Metal("V", 3), ligands=[Ligand("O")] * 5 + [Ligand("[OH-]")])
    assert pipeline._n_terminal_oxo_nitrido_ligands(aq) == 0
    assert pipeline._uhf_for(aq, O, []) == 2


def test_main_group_over_oxidised_raises():
    with pytest.raises(spin.SpinError):
        spin.unpaired_electrons("Sn", 6, O, Spin.LOW)  # removes >4 valence e-


def test_spin_unknown_metal_raises():
    with pytest.raises(spin.SpinError):
        spin.unpaired_electrons("Xx", 2, O, Spin.LOW)


def test_spin_to_uhf_passthrough():
    assert spin_to_uhf(3) == 3


# --------------------------------------------------------------------------- #
# isomer enumeration — fast
# --------------------------------------------------------------------------- #

def _complex(denticities, distinct=True):
    ligs = [
        Ligand(chr(65 + i) if distinct else "X", denticity=d)
        for i, d in enumerate(denticities)
    ]
    return Complex(Metal("Pt", 2), ligs)


@pytest.mark.parametrize(
    "denticities,distinct,geom,expected",
    [
        ([1, 1, 1, 1], True, SP, 3),    # MABCD square planar
        ([1, 1, 1, 1], False, SP, 1),   # MA4
        ([2, 2], True, SP, 1),          # M(AA)(BB) square planar (cis only)
        ([1, 1, 1, 1, 1, 1], False, O, 1),  # MA6 octahedral
    ],
)
def test_isomer_counts(denticities, distinct, geom, expected):
    cx = _complex(denticities, distinct=distinct)
    assert len(enumerate_isomers(cx, geom)) == expected


def test_ma2b2_square_planar_gives_cis_and_trans():
    cx = Complex(Metal("Pt", 2), [Ligand(s, denticity=1) for s in "AABB"])
    assert len(enumerate_isomers(cx, SP)) == 2


# --------------------------------------------------------------------------- #
# xtb — slow
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_xtb_relaxes_small_molecule(tmp_path):
    xyz = tmp_path / "water.xyz"
    xyz.write_text("3\nwater\nO 0.00 0.00 0.00\nH 0.96 0.00 0.00\nH -0.24 0.93 0.00\n")
    out = relax_with_xtb(xyz, charge=0, uhf=0, workdir=tmp_path, timeout_s=120)
    assert out.exists()
    assert int(out.read_text().splitlines()[0]) == 3


@pytest.mark.slow
def test_xtb_missing_binary_raises(tmp_path):
    xyz = tmp_path / "water.xyz"
    xyz.write_text("1\nx\nO 0.0 0.0 0.0\n")
    with pytest.raises(XtbError):
        relax_with_xtb(xyz, charge=0, uhf=0, workdir=tmp_path, xtb_bin="xtb_does_not_exist")


@pytest.mark.slow
def test_pipeline_relax_square_2bi(tmp_path):
    cx = next(c for c in inputs.parse_csv(PROTOTYPE_CSV) if c.name == "Sq2b_Pt_1")
    results = pipeline.build_complex(cx, tmp_path, relax=True)
    r = results[0]
    assert r.total_charge == 2 and r.uhf == 0
    xyz = Path(r.xyz_path)
    assert xyz.exists() and int(xyz.read_text().splitlines()[0]) == 41


# --------------------------------------------------------------------------- #
# coordination-sphere restraint (gas-phase dissociation guard) — fast helpers
# --------------------------------------------------------------------------- #

def test_metal_donors_picks_nearest_heavy_atoms():
    atoms = [
        ("Fe", (0.0, 0.0, 0.0)),
        ("N", (2.0, 0.0, 0.0)),
        ("N", (0.0, 2.1, 0.0)),
        ("H", (0.5, 0.0, 0.0)),   # closer than the donors, but H is never a donor
        ("C", (5.0, 0.0, 0.0)),   # too far to be in the coordination sphere
    ]
    metal_idx, donors = _metal_donors(atoms, "Fe", 2)
    assert metal_idx == 0
    assert [i for i, _ in donors] == [1, 2]  # the two N, not the H or the distant C


@pytest.mark.slow
def test_intramolecular_bonds_restrained_through_xtb(tmp_path):
    # A fragile bicyclic ligand (indazole) used to have its ring pulled open by
    # xtb; the bond restraints must keep every covalent bond intact.
    import numpy as np

    ind = "C1(NN=C2)=C2C=CC=C1"
    cx = Complex(metal=Metal("Ru", 2), geometry=Geometry.OCTAHEDRAL,
                 ligands=[Ligand(ind)] + [Ligand("[Cl-]") for _ in range(4)] + [Ligand(ind)])

    def intact_heavy_bonds(xyz):
        lines = Path(xyz).read_text().splitlines()
        n = int(lines[0])
        syms, X = [], []
        for ln in lines[2:2 + n]:
            q = ln.split(); syms.append(q[0]); X.append([float(x) for x in q[1:4]])
        X = np.array(X)
        c = 0
        for i in range(n):
            for j in range(i + 1, n):
                if {syms[i], syms[j]} & {"H", "Ru", "Cl"}:
                    continue
                if np.linalg.norm(X[i] - X[j]) < 1.8:
                    c += 1
        return c

    res = pipeline.build_complex(cx, tmp_path, relax=True)
    # two intact indazoles => 10 heavy ring/backbone bonds each = 20.
    assert intact_heavy_bonds(res[0].xyz_path) == 20
    # donor indices are reported for the 3D viewer (metal + its bonded donors).
    assert res[0].metal_index is not None and len(res[0].donor_indices) == 6


def test_write_constraint_file_is_one_indexed(tmp_path):
    con = tmp_path / "c.inp"
    _write_constraint_file(con, [(0, 1, 2.0), (0, 2, 2.1)], force_constant=0.5)
    txt = con.read_text()
    assert "$constrain" in txt and "force constant=0.5" in txt and "$end" in txt
    # xtb input files are 1-based: (0,1)->1,2 and (0,2)->1,3
    assert "distance: 1, 2, 2.000" in txt
    assert "distance: 1, 3, 2.100" in txt


def test_resolve_donors_prefers_explicit_indices():
    from mecobi.optimize import _resolve_donors
    # a bulky ligand: the nearest heavy atom (index 1, at 1.8) is a backbone atom;
    # the TRUE donor (index 3, at 2.3) is farther. Explicit indices must win.
    atoms = [
        ("Cu", (0.0, 0.0, 0.0)),
        ("C", (1.8, 0.0, 0.0)),    # backbone carbon, closest heavy atom
        ("C", (0.0, 1.9, 0.0)),    # another backbone carbon
        ("N", (2.3, 0.0, 0.0)),    # the real donor, farther out
    ]
    mi, donors = _resolve_donors(atoms, metal_index=0, donor_indices=[3],
                                 metal_symbol="Cu", coordination_number=1)
    assert mi == 0 and [i for i, _ in donors] == [3]  # true donor, not the nearer C
    # without explicit indices it falls back to nearest-heavy (the backbone C)
    _mi, nn = _resolve_donors(atoms, None, None, "Cu", 1)
    assert [i for i, _ in nn] == [1]


def test_restrain_donors_requires_some_donor_source(tmp_path):
    xyz = tmp_path / "x.xyz"
    xyz.write_text("2\nx\nFe 0 0 0\nCl 2 0 0\n")
    # no donor source given at all -> error, before any xtb call (fast)
    with pytest.raises(XtbError):
        relax_with_xtb(xyz, charge=0, uhf=0, restrain_donors=True, workdir=tmp_path)


# --------------------------------------------------------------------------- #
# coordination-sphere restraint — slow (needs xtb)
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_constrained_relax_keeps_coordination_intact(tmp_path):
    """A complex with labile donors must keep every donor bound after relaxation:
    the coordination restraint stops gas-phase xtb from ejecting them."""
    cx = Complex(
        metal=Metal("Fe", 3),
        ligands=[Ligand("[Cl-]"), Ligand("[Cl-]"), Ligand("[Cl-]"),
                 Ligand("O"), Ligand("O"), Ligand("O")],
    )
    results = pipeline.build_complex(cx, tmp_path, relax=True)
    r = results[0]
    atoms = [
        (p.split()[0], tuple(float(x) for x in p.split()[1:4]))
        for p in Path(r.xyz_path).read_text().splitlines()[2:]
        if p.strip()
    ]
    _mi, donors = _metal_donors(atoms, "Fe", cx.coordination_number)
    assert max(d for _i, d in donors) <= DISSOCIATION_THRESHOLD_A


def test_raise_stack_limit_lifts_soft_to_hard(monkeypatch):
    """xtb's main thread inherits ulimit -s; a small soft limit segfaults it on big complexes."""
    from mecobi import optimize

    resource = pytest.importorskip("resource")  # POSIX only
    calls = []
    monkeypatch.setattr(resource, "getrlimit", lambda r: (8 * 1024 * 1024, resource.RLIM_INFINITY))
    monkeypatch.setattr(resource, "setrlimit", lambda r, v: calls.append(v))
    optimize._raise_stack_limit()
    assert calls == [(resource.RLIM_INFINITY, resource.RLIM_INFINITY)]
