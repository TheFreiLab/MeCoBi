"""Graceful xtb degradation (backlog item E): a hard case must not fail the build.

Uses [Cl-] ligands (perception is trivial, no torch) and monkeypatches xtb so the
tests stay fast and need no xtb binary.
"""

import time
from pathlib import Path

import pytest

from mecobi import optimize, pipeline
from mecobi.model import Complex, Geometry, Ligand, Metal


def _ptcl4():
    return Complex(metal=Metal("Pt", 2), geometry=Geometry.SQUARE_PLANAR,
                   ligands=[Ligand("[Cl-]") for _ in range(4)])


@pytest.fixture
def no_csd_table(monkeypatch):
    """Disable the shipped CSD table so the covalent-radius FALLBACK path is tested
    in isolation (it still governs any metal/donor absent from the mined table)."""
    monkeypatch.setattr(optimize, "_ML_LOADED", True)
    monkeypatch.setattr(optimize, "_ML_TABLE", None)


def test_restraint_reference_covers_broad_periodic_table(no_csd_table):
    # The covalent-radius restraint target must work beyond the ~27 hardcoded
    # metals — via an RDKit fallback — or a weak donor stranded on a large metal
    # (e.g. thioether S ~6 A off a Hf(IV)) is left un-restrained and xtb ejects it.
    assert optimize._cov_radius("Hf") is not None   # was None -> "trust assembly"
    assert optimize._cov_radius("In") is not None
    assert optimize._cov_radius("La") is not None
    # a grossly stranded Hf-S donor is pulled back toward a real bond, not trusted at 6 A
    assert optimize._restraint_reference(6.0, "Hf", "S") < 3.5
    # a well-placed donor at a reasonable distance is left untouched
    assert optimize._restraint_reference(2.4, "Hf", "N") == 2.4
    # a genuinely unknown element symbol still falls back to trusting the assembly
    assert optimize._cov_radius("Zzz") is None
    assert optimize._restraint_reference(6.0, "Zzz", "S") == 6.0


def test_trust_factor_tightened_for_short_bond_metals(no_csd_table):
    # Late/heavy metals keep the calibrated default so their weak, long dative
    # bonds are trusted (a Ru-N at 2.7 A is real, not a mis-placement).
    assert optimize._trust_factor("Ru") == optimize._TRUST_ASSEMBLED_FACTOR
    assert optimize._restraint_reference(2.7, "Ru", "N") == 2.7
    # Small, short-bond early transition metals get a tighter factor: a V-O
    # stranded at 2.6 A (V-O target ~2.19 A) is pulled back to a real bond, where
    # the flat 1.3x default (ceiling 2.85 A) would have trusted it long. A
    # well-placed V-O at 2.3 A is still left untouched.
    assert optimize._trust_factor("V") < optimize._TRUST_ASSEMBLED_FACTOR
    v_target = optimize._cov_radius("V") + optimize._cov_radius("O")
    assert optimize._restraint_reference(2.6, "V", "O") == v_target
    assert optimize._restraint_reference(2.3, "V", "O") == 2.3


def test_restraint_reference_uses_csd_table(monkeypatch):
    # When a CSD-mined average exists for (metal, OS, donor, CN) it is used as the
    # restraint target instead of the covalent-radius sum, and the hierarchy falls
    # back specific -> general. A terminal oxo (very short vs the dative average) is
    # left short by the multiple-bond guard.
    fake = {
        "metal_os_donor_cn": {"Ni|2|N|6": {"mean": 2.10, "n": 40}},
        "metal_os_donor": {"Ni|2|O": {"mean": 2.05, "n": 30}},
        "metal_donor": {"Ni|N": {"mean": 2.00, "n": 500}, "Mo|O": {"mean": 1.95, "n": 200}},
    }
    monkeypatch.setattr(optimize, "_ML_LOADED", True)
    monkeypatch.setattr(optimize, "_ML_TABLE", fake)
    # most-specific bin wins (fine over coarse)
    assert optimize._restraint_reference(2.30, "Ni", "N", ox=2, cn=6) == 2.10
    # no fine/marginal bin for CN4 -> falls back to the coarse Ni|N average
    assert optimize._restraint_reference(2.30, "Ni", "N", ox=2, cn=4) == 2.00
    # a bin below the sample floor is ignored -> covalent fallback
    monkeypatch.setitem(fake["metal_donor"], "Ni|N", {"mean": 2.00, "n": 3})
    assert optimize._restraint_reference(2.30, "Ni", "N", ox=2, cn=4) != 2.00
    # multiple-bond guard: a short M=O (1.55 < 0.8*1.95) is kept, not stretched
    assert optimize._restraint_reference(1.55, "Mo", "O", ox=6, cn=6) == 1.55


def test_xtb_failure_keeps_assembled_geometry(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise optimize.XtbError("xtb failed on x (rc=1):\nabnormal termination")

    monkeypatch.setattr(optimize, "relax_with_xtb", boom)
    # uff_fallback off -> the raw assembly is kept (the legacy graceful-degradation path)
    res = pipeline.build_complex(_ptcl4(), tmp_path, relax=True, uff_fallback=False)
    assert len(res) == 1
    assert Path(res[0].xyz_path).exists()          # assembled geometry written + kept
    assert res[0].total_energy is None             # nothing comparable to rank
    assert any("kept the assembled" in w for w in res[0].warnings)


def test_xtb_failure_falls_back_to_uff(tmp_path, monkeypatch):
    # When every xtb tier fails, the default UFF force-field fallback runs (MetalloGen-style):
    # a physically sensible geometry for metals GFN2 diverges on, instead of the raw assembly.
    def boom(*a, **k):
        raise optimize.XtbError("xtb failed on x (rc=1):\nabnormal termination")

    monkeypatch.setattr(optimize, "relax_with_xtb", boom)
    res = pipeline.build_complex(_ptcl4(), tmp_path, relax=True, uff_fallback=True)  # opt-in
    assert len(res) == 1
    assert Path(res[0].xyz_path).exists()
    assert res[0].total_energy is None             # a force-field fallback isn't energy-ranked
    assert any("UFF force-field" in w for w in res[0].warnings)
    assert not any("kept the assembled" in w for w in res[0].warnings)


def _write_xyz(path, atoms):
    lines = [str(len(atoms)), ""]
    lines += [f"{el} {x:.4f} {y:.4f} {z:.4f}" for el, (x, y, z) in atoms]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_two_stage_gfnff_prerelax_then_gfn2(tmp_path, monkeypatch):
    # Two-stage default: GFN-FF pre-relax FIRST, then GFN2. When GFN2 fails, the build
    # keeps the (already computed) GFN-FF pre-relaxed structure.
    calls = []

    def flaky(*a, **k):
        gfn = k.get("gfn")
        calls.append(gfn)
        if str(gfn) == "2":
            raise optimize.XtbError("scf did not converge")
        return Path(a[0])  # GFN-FF 'succeeds', returns the path unchanged

    monkeypatch.setattr(optimize, "relax_with_xtb", flaky)
    res = pipeline.build_complex(_ptcl4(), tmp_path, relax=True)
    # GFN-FF pre-relax, GFN2 (fails on the FF geometry), then a GFN2 retry from the
    # assembled geometry (also fails here) -> keep the GFN-FF pre-relaxed structure.
    assert calls == ["ff", 2, 2]
    assert any("GFN-FF" in w for w in res[0].warnings)
    assert res[0].total_energy is None              # GFN-FF energy excluded from ranking


def _staged_gfn2_cl_cl_collapse(xyz_in, *a, **k):
    """GFN-FF leaves a sane geometry; GFN2 'collapses' two chlorides onto each other
    (forging a Cl-Cl bond ~1.9 A)."""
    xyz = Path(xyz_in)
    if str(k.get("gfn")) == "2":
        atoms = optimize._read_xyz(xyz)
        cls = [i for i, (el, _) in enumerate(atoms) if el == "Cl"]
        x0, y0, z0 = atoms[cls[0]][1]
        atoms[cls[1]] = ("Cl", (x0 + 1.9, y0, z0))
        _write_xyz(xyz, atoms)
    return xyz


def test_gfn2_collapse_kept_by_default_and_flagged(tmp_path, monkeypatch):
    # Default: xtb is left FREE to change the connectivity (re-forming bonds repairs bad
    # initial placements), so a GFN2 connectivity change is KEPT -- not reverted -- and only
    # flagged (connectivity_ok False) for the caller to see.
    monkeypatch.setattr(optimize, "relax_with_xtb", _staged_gfn2_cl_cl_collapse)
    res = pipeline.build_complex(_ptcl4(), tmp_path, relax=True)
    assert res[0].connectivity_ok is False              # the change is flagged, not reverted
    assert not any("reverted" in w for w in res[0].warnings)


def test_gfn2_collapse_reverts_when_guard_opted_in(tmp_path, monkeypatch):
    # Opt-in guard (A/B only): with revert_on_bond_change=True the build REVERTS to the
    # GFN-FF structure, so the shipped geometry has correct connectivity (not the fused wreck).
    monkeypatch.setattr(optimize, "relax_with_xtb", _staged_gfn2_cl_cl_collapse)
    res = pipeline.build_complex(_ptcl4(), tmp_path, relax=True, revert_on_bond_change=True)
    assert res[0].connectivity_ok                   # reverted -> topology correct again
    assert any("reverted to the GFN-FF" in w for w in res[0].warnings)


def test_f_block_metal_skips_xtb_and_flags(tmp_path, monkeypatch):
    from mecobi import inputs

    assert inputs.is_f_block("La") and inputs.is_f_block("U") and not inputs.is_f_block("Fe")
    called = []
    monkeypatch.setattr(optimize, "relax_with_xtb",
                        lambda *a, **k: called.append(True) or Path(a[0]))
    cx = Complex(metal=Metal("La", 3), geometry=Geometry.OCTAHEDRAL,
                 ligands=[Ligand("[Cl-]") for _ in range(6)])
    res = pipeline.build_complex(cx, tmp_path, relax=True)  # relax requested...
    assert not called                                        # ...but xtb never invoked
    assert res[0].total_energy is None
    assert any("f-block" in w for w in res[0].warnings)


def test_linear_donor_angles_flags_end_on_only(tmp_path):
    # A cyanide C (metal + one N) is end-on -> a 180° M-C-N restraint; a ring/chelate donor
    # with two heavy neighbours is not. Purely graph-based, so coordinates are arbitrary.
    xyz = tmp_path / "x.xyz"
    _write_xyz(xyz, [("Pt", (0, 0, 0)), ("C", (2, 0, 0)), ("N", (3.1, 0, 0)),
                     ("C", (0, 2, 0)), ("C", (0, 3, 1)), ("C", (0, 3, -1))])
    bonds = [(0, 1), (1, 2), (0, 3), (3, 4), (3, 5)]  # Pt-C#N end-on; Pt-C(ring) chelate
    lin = pipeline._linear_donor_angles(xyz, bonds, metal_index=0, donor_indices=[1, 3])
    assert lin == [(0, 1, 2, 180.0)]                 # only the cyanide C, vertex = donor


class _FakeAtom:
    def __init__(self, aid, z, chg=0):
        self._id, self._z, self._c = aid, z, chg

    def get_id(self):
        return self._id

    def get_atomic_number(self):
        return self._z

    def get_charge(self):
        return self._c


class _FakeBond:
    def __init__(self, a, b, order):
        self._a, self._b, self._o = a, b, order

    def get_atom1(self):
        return self._a

    def get_atom2(self):
        return self._b

    def get_order(self):
        return self._o


class _FakeConstructed:
    def __init__(self, atoms, bonds):
        self._atoms, self._bonds = atoms, bonds

    def get_atoms(self):
        return iter(self._atoms)

    def get_bonds(self):
        return iter(self._bonds)


def test_ff_declash_relaxes_bond_and_freezes_donor(tmp_path):
    # UFF de-clash: a bonded C-C pair jammed to 0.8 A is pushed to a real bond length, with the
    # donor carbon (fixed) staying put. Topology-preserving; never breaks the bond.
    import math

    from mecobi import optimize
    xyz = tmp_path / "lig.xyz"
    _write_xyz(xyz, [("Pt", (0, 0, 0)), ("C", (2.0, 0, 0)), ("C", (2.8, 0, 0))])
    a = [_FakeAtom(0, 78), _FakeAtom(1, 6), _FakeAtom(2, 6)]
    constructed = _FakeConstructed(
        a, [_FakeBond(a[0], a[1], 1), _FakeBond(a[1], a[2], 1)])  # Pt-C (dative), C-C
    optimize.ff_declash(xyz, constructed, metal_index=0, donor_indices=[1])
    atoms = optimize._read_xyz(xyz)
    assert math.dist(atoms[1][1], (2.0, 0.0, 0.0)) < 0.2        # donor C softly held near its site
    cc = math.dist(atoms[1][1], atoms[2][1])
    assert 1.3 < cc < 1.8                                       # C-C pushed to a real bond length


def test_ff_declash_separates_two_clashing_ligands(tmp_path):
    # The point of the metal-excluded FF: two SEPARATE ligands (different components) overlapping
    # must be pushed apart by inter-ligand VdW, while their fixed donors stay put.
    import math

    from mecobi import optimize
    xyz = tmp_path / "two.xyz"
    # Pt + two O-H "ligands" at proper (non-clashing) donor sites, but their H's jammed together.
    o1, h1, o2, h2 = (2.0, 0.0, 0.0), (1.3, 0.9, 0.0), (0.0, 2.0, 0.0), (0.9, 1.3, 0.0)
    _write_xyz(xyz, [("Pt", (0, 0, 0)), ("O", o1), ("H", h1), ("O", o2), ("H", h2)])
    a = [_FakeAtom(0, 78), _FakeAtom(1, 8), _FakeAtom(2, 1), _FakeAtom(3, 8), _FakeAtom(4, 1)]
    constructed = _FakeConstructed(a, [_FakeBond(a[0], a[1], 1), _FakeBond(a[1], a[2], 1),
                                       _FakeBond(a[0], a[3], 1), _FakeBond(a[3], a[4], 1)])
    d_hh_before = math.dist(h1, h2)
    optimize.ff_declash(xyz, constructed, metal_index=0, donor_indices=[1, 3])
    atoms = optimize._read_xyz(xyz)
    assert (math.dist(atoms[1][1], o1) < 0.3                    # donors softly held near their sites
            and math.dist(atoms[3][1], o2) < 0.3)
    d_hh_after = math.dist(atoms[2][1], atoms[4][1])
    assert d_hh_after >= d_hh_before                            # the clashing H's pushed apart


def test_ff_declash_pulls_stranded_donor_to_bond_length(tmp_path):
    # #3 donor repositioning: a donor stranded far from the metal (bulky-ligand assembly) is
    # pulled back to a real M-L bond length before being fixed (DIBWAM's P at ~3 A).
    import math

    from mecobi import optimize
    xyz = tmp_path / "stranded.xyz"
    _write_xyz(xyz, [("Pd", (0, 0, 0)), ("P", (3.5, 0.0, 0.0)), ("C", (4.6, 0.6, 0.0))])
    a = [_FakeAtom(0, 46), _FakeAtom(1, 15), _FakeAtom(2, 6)]
    constructed = _FakeConstructed(a, [_FakeBond(a[0], a[1], 1), _FakeBond(a[1], a[2], 1)])
    optimize.ff_declash(xyz, constructed, metal_index=0, donor_indices=[1], oxidation_state=2)
    atoms = optimize._read_xyz(xyz)
    assert math.dist(atoms[1][1], (0, 0, 0)) < 2.9          # P pulled in from 3.5 A toward a bond


def test_ff_declash_pushes_nondonor_off_the_metal(tmp_path):
    # #2 metal-centre clearance: a non-donor atom folded onto the metal (0.7 A) must be pushed
    # clear, while the donor stays put (a bulky phosphine's aryl over the centre -- DIBWAM).
    import math

    from mecobi import optimize
    xyz = tmp_path / "onmetal.xyz"
    _write_xyz(xyz, [("Pt", (0, 0, 0)), ("C", (2.0, 0.0, 0.0)), ("C", (0.5, 0.5, 0.0))])
    a = [_FakeAtom(0, 78), _FakeAtom(1, 6), _FakeAtom(2, 6)]
    constructed = _FakeConstructed(a, [_FakeBond(a[0], a[1], 1), _FakeBond(a[1], a[2], 1)])
    assert math.dist((0.5, 0.5, 0.0), (0, 0, 0)) < 1.8       # C2 starts jammed on the metal
    optimize.ff_declash(xyz, constructed, metal_index=0, donor_indices=[1])
    atoms = optimize._read_xyz(xyz)
    assert atoms[1][1] == (2.0, 0.0, 0.0)                    # donor fixed
    assert math.dist(atoms[2][1], (0, 0, 0)) > 1.5          # non-donor pushed clear of the metal


def test_nondonor_on_metal_guard(tmp_path):
    # A non-donor atom collapsed onto the metal (0.8 A) is flagged; a donor in the sphere is not.
    from mecobi import pipeline
    xyz = tmp_path / "m.xyz"
    _write_xyz(xyz, [("Pt", (0, 0, 0)), ("P", (2.3, 0, 0)), ("C", (0.8, 0, 0))])
    assert pipeline._nondonor_on_metal(xyz, metal_index=0, donor_indices=[1]) is True   # C on metal
    # if that same close atom is a donor (e.g. an η-cap carbon), it is allowed
    assert pipeline._nondonor_on_metal(xyz, metal_index=0, donor_indices=[1, 2]) is False
    # a clean sphere (donor at a real bond length, nothing collapsed) passes
    _write_xyz(xyz, [("Pt", (0, 0, 0)), ("P", (2.3, 0, 0)), ("C", (3.4, 0, 0))])
    assert pipeline._nondonor_on_metal(xyz, metal_index=0, donor_indices=[1]) is False


def test_missing_xtb_is_reraised_not_swallowed(tmp_path, monkeypatch):
    def missing(*a, **k):
        raise optimize.XtbNotFound("xtb executable 'xtb' not found on PATH.")

    monkeypatch.setattr(optimize, "relax_with_xtb", missing)
    with pytest.raises(optimize.XtbNotFound):
        pipeline.build_complex(_ptcl4(), tmp_path, relax=True)


def test_inter_ligand_overlap_scores_only_cross_ligand_heavy_pairs():
    # two ligands (components 0 and 1) plus a metal (comp -1). Atoms 0,1 same ligand; 2 other.
    atoms = [("P", (0.0, 0.0, 0.0)), ("C", (1.8, 0.0, 0.0)), ("C", (0.9, 0.2, 0.0))]
    comp = [0, 0, 1]
    # atom0-atom2 (0.92 A, different ligands, C+P radii ~1.83*1.15) -> overlaps; 0-1 same ligand skipped
    over = optimize._inter_ligand_overlap(atoms, comp, clash_ratio=1.15)
    assert over > 0
    # push the second ligand far away -> no overlap
    atoms[2] = ("C", (9.0, 0.0, 0.0))
    assert optimize._inter_ligand_overlap(atoms, comp, clash_ratio=1.15) == 0.0


def test_xtb_surrogate_map(monkeypatch):
    assert optimize.xtb_surrogate("Y") == "Sc"       # Y(III) d0 -> Sc(III) d0 by default
    assert optimize.xtb_surrogate("Fe") is None      # a metal xtb handles keeps itself
    assert optimize.xtb_surrogate(None) is None
    monkeypatch.setenv("MECOBI_XTB_SURROGATE", "Y:La,Sc:In")
    assert optimize.xtb_surrogate("Y") == "La"       # env overrides the map
    assert optimize.xtb_surrogate("Sc") == "In"


def test_metal_surrogate_swaps_during_relax_and_restores(tmp_path, monkeypatch):
    # A Y complex is relaxed AS Sc (xtb-friendly), then the real Y symbol is restored.
    seen = {}

    def spy_relax(xyz, *a, **k):
        seen["during"] = optimize._read_xyz(Path(xyz))[k["metal_index"]][0]
        seen["metal_symbol"] = k.get("metal_symbol")
        seen["reference_metal"] = k.get("reference_metal")
        return Path(xyz), 0.0

    monkeypatch.setattr(pipeline, "_relax_tiered", spy_relax)
    ycl3 = Complex(metal=Metal("Y", 3), geometry=Geometry.TRIGONAL_PLANAR,
                   ligands=[Ligand("[Cl-]") for _ in range(3)])
    res = pipeline.build_complex(ycl3, tmp_path, relax=True, metal_surrogate=True)
    mi = res[0].metal_index
    assert seen["during"] == "Sc"                     # xtb saw the surrogate
    assert seen["metal_symbol"] == "Sc"               # the metal atom is found as the surrogate
    assert seen["reference_metal"] == "Y"             # but held at the REAL metal's M-L distances
    assert optimize._read_xyz(Path(res[0].xyz_path))[mi][0] == "Y"   # real metal restored
    assert any("surrogate" in w for w in res[0].warnings)


def test_metal_surrogate_off_keeps_real_metal(tmp_path, monkeypatch):
    seen = {}

    def spy_relax(xyz, *a, **k):
        seen["during"] = optimize._read_xyz(Path(xyz))[k["metal_index"]][0]
        return Path(xyz), 0.0

    monkeypatch.setattr(pipeline, "_relax_tiered", spy_relax)
    ycl3 = Complex(metal=Metal("Y", 3), geometry=Geometry.TRIGONAL_PLANAR,
                   ligands=[Ligand("[Cl-]") for _ in range(3)])
    res = pipeline.build_complex(ycl3, tmp_path, relax=True)  # metal_surrogate default False
    assert seen["during"] == "Y"
    assert not any("surrogate" in w for w in res[0].warnings)


# --------------------------------------------------------------------------- #
# Per-structure wall-clock budget (a timeout must not be spent twice)
# --------------------------------------------------------------------------- #

def test_timeout_skips_the_gfn2_retry(tmp_path, monkeypatch):
    # The GFN2 retry from the assembled geometry exists for an SCF non-convergence.
    # After a TIMEOUT it cannot help -- the same system, the same budget -- and running
    # it anyway is what let a 300 s allowance burn 609 s of wall clock (and behind a
    # reverse proxy, 502 the caller long before returning). GFN2 is tried exactly once.
    calls = []

    def timing_out(*a, **k):
        gfn = k.get("gfn")
        calls.append(gfn)
        if str(gfn) == "2":
            raise optimize.XtbTimeout("xtb timed out after 300s on x.xyz")
        return Path(a[0])  # GFN-FF pre-relax succeeds

    monkeypatch.setattr(optimize, "relax_with_xtb", timing_out)
    res = pipeline.build_complex(_ptcl4(), tmp_path, relax=True)
    assert calls == ["ff", 2]                       # no second GFN2 (was ["ff", 2, 2])
    warns = res[0].warnings
    assert any("GFN-FF pre-relaxed" in w for w in warns)
    assert res[0].total_energy is None
    # A timeout must SAY it was a timeout (not "failed"), and point end users at the local
    # build, where a longer optimisation limit than the web app's is allowed.
    assert any("time limit" in w and "run MeCoBi locally" in w for w in warns), warns


def test_non_timeout_failure_still_retries_gfn2(tmp_path, monkeypatch):
    # The regression guard for the above: a convergence failure must keep its retry.
    calls = []

    def flaky(*a, **k):
        gfn = k.get("gfn")
        calls.append(gfn)
        if str(gfn) == "2":
            raise optimize.XtbError("scf did not converge")
        return Path(a[0])

    monkeypatch.setattr(optimize, "relax_with_xtb", flaky)
    res = pipeline.build_complex(_ptcl4(), tmp_path, relax=True)
    assert calls == ["ff", 2, 2]
    # A genuine crash (not a timeout) must NOT carry the "run locally for more time" hint.
    assert not any("run MeCoBi locally" in w for w in res[0].warnings)


def test_xtb_timeout_is_an_xtb_error():
    # Every existing `except XtbError` handler must keep catching a timeout.
    assert issubclass(optimize.XtbTimeout, optimize.XtbError)


def test_budget_is_shared_across_tiers(tmp_path, monkeypatch):
    # `xtb_timeout_s` is the budget for the STRUCTURE, not for each xtb call: a
    # pre-relax that eats it all leaves nothing for GFN2, which is then skipped rather
    # than started with a fresh full allowance. Each tier is handed only what is left.
    seen = []

    def budget_eater(*a, **k):
        seen.append(k.get("timeout_s"))
        time.sleep(2.5)          # the GFN-FF tier spends most of the 6 s budget
        return Path(a[0])

    monkeypatch.setattr(optimize, "relax_with_xtb", budget_eater)
    res = pipeline.build_complex(_ptcl4(), tmp_path, relax=True, xtb_timeout_s=6)
    # GFN-FF was handed the whole budget and spent 2.5 s of it; GFN2 would start with
    # ~3.5 s left, under the _MIN_STAGE_S floor, so it is skipped instead of run. The
    # slice handed to a tier is int()-truncated, so the first one sees 5 or 6 depending
    # on sub-second timing -- assert the invariant, not the rounding.
    assert len(seen) == 1                            # GFN-FF ran; GFN2 never started
    assert 5 <= seen[0] <= 6                         # and it got the budget, not more
    assert any("GFN-FF pre-relaxed" in w for w in res[0].warnings)
