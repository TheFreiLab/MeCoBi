"""Metallocene + tetradentate topologies (registry/detection fast; builds slow)."""

from pathlib import Path

import pytest

from mecobi import geometry, perception, pipeline
from mecobi.assembly import registry
from mecobi.model import Complex, Geometry, Ligand, Metal

CP = "[cH-]1cccc1"           # cyclopentadienyl anion (perceives as an eta-cap)
CP_STAR = "C[c-]1c(C)c(C)c(C)c1C"       # Cp* (pentamethylcyclopentadienyl), an eta5 cap
CYMENE = "CC1=CC=C(C(C)C)C=C1"          # p-cymene, an eta6 arene cap
PPY = "[c-]1ccccc1-c1ccccn1"            # 2-phenylpyridine, cyclometalated C^N chelate
CO = "[C-]#[O+]"             # carbonyl
CYCLAM = "C1CNCCNCCCNCCNC1"  # tetraaza macrocycle (perceives as tetradentate)
SALEN = "[O-]c1ccccc1/C=N/CC/N=C/c1ccccc1[O-]"  # N2O2 tetradentate, charge -2
BPY = "c1ccc(-c2ccccn2)nc1"  # 2,2'-bipyridine (bidentate)


# --------------------------------------------------------------------------- #
# registry + detection — fast
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "geom,dents,label,n",
    [
        (Geometry.SQUARE_PLANAR, [4], "square_1tetra", 4),
        (Geometry.OCTAHEDRAL, [4, 2], "octa_1tetra_1bi", 6),
        (Geometry.METALLOCENE, [3, 3], "metallocene", 6),
        (Geometry.METALLOCENE_BENT, [3, 3, 1, 1], "metallocene_bent", 8),
    ],
)
def test_new_topologies_registered(geom, dents, label, n):
    e = registry.lookup(geom, dents)
    assert e.label == label
    assert e.n_sites == n


def test_detect_metallocene():
    assert geometry.detect_metallocene([3, 3], [True, True]) is Geometry.METALLOCENE
    assert geometry.detect_metallocene([3, 3, 1, 1], [True, True, False, False]) is Geometry.METALLOCENE_BENT
    # one cap, or a non-cap third ligand of denticity > 1 -> not a metallocene
    assert geometry.detect_metallocene([3, 2, 1], [True, False, False]) is None
    assert geometry.detect_metallocene([3, 3, 2], [True, True, False]) is None


def test_bare_sandwich_spin_is_metallocene_not_linear(tmp_path):
    # Regression: a bare centroid-cap sandwich is PLACED on the 2-site linear topology
    # (the centroid model has no (1,1) metallocene topology), but its crystal-field
    # splitting must be the metallocene's, not a linear ML2's. Ferrocene Fe(II) d6 is
    # diamagnetic (uhf 0); the linear (2,2,1) split would wrongly give a triplet (uhf 2).
    cx = Complex(metal=Metal("Fe", 2), ligands=[Ligand(smiles=CP), Ligand(smiles=CP)])
    assert pipeline.build_complex(cx, tmp_path, relax=False)[0].uhf == 0


def test_detect_piano_stool():
    assert geometry.detect_piano_stool([5]) is Geometry.PIANO_STOOL_CP
    assert geometry.detect_piano_stool([6]) is Geometry.PIANO_STOOL_ARENE
    # a sandwich is not a piano stool, and neither is an uncapped complex
    assert geometry.detect_piano_stool([5, 5]) is None
    assert geometry.detect_piano_stool([]) is None


def test_spin_geometry_resolves_centroid_caps():
    # One cap -> pseudo-octahedral piano stool, named by ring size (both split (3, 2)).
    assert geometry.spin_geometry(Geometry.TETRAHEDRAL, [5], 4) is Geometry.PIANO_STOOL_CP
    assert geometry.spin_geometry(Geometry.TETRAHEDRAL, [6], 4) is Geometry.PIANO_STOOL_ARENE
    # Two bare caps -> metallocene (the pre-existing rule, unchanged).
    assert geometry.spin_geometry(Geometry.LINEAR, [5, 5], 2) is Geometry.METALLOCENE
    # Two caps with legs already route to METALLOCENE_BENT, which splits (3, 2): pass through.
    assert geometry.spin_geometry(
        Geometry.METALLOCENE_BENT, [5, 5], 4) is Geometry.METALLOCENE_BENT
    # No cap -> the placement geometry is the splitting geometry, untouched.
    assert geometry.spin_geometry(Geometry.TETRAHEDRAL, [], 4) is Geometry.TETRAHEDRAL
    assert geometry.spin_geometry(Geometry.OCTAHEDRAL, [], 6) is Geometry.OCTAHEDRAL


@pytest.mark.parametrize(
    "metal,ox,ligs",
    [
        ("Mn", 1, [CP] + [CO] * 3),          # cymantrene, CpMn(CO)3
        ("Ir", 3, [CP_STAR, PPY, "[Cl-]"]),  # Cp*Ir(ppy)Cl
        ("Ru", 2, [CYMENE, PPY, "[Cl-]"]),   # (cymene)Ru(ppy)Cl -- eta6 cap
    ],
)
def test_piano_stool_spin_is_pseudo_octahedral(metal, ox, ligs, tmp_path):
    # Regression, the one-cap companion to the bare-sandwich case above. A piano stool is
    # PLACED on its centroid CN geometry (CN 4 -> tetrahedral), but the cap donates a facial
    # triad, so the field is pseudo-octahedral. These d6 centres are all diamagnetic (uhf 0);
    # the tetrahedral (2, 3) split wrongly gave a triplet (uhf 2), sending xtb --uhf 2.
    cx = Complex(metal=Metal(metal, ox), ligands=[Ligand(smiles=s) for s in ligs])
    assert pipeline.build_complex(cx, tmp_path, relax=False)[0].uhf == 0


def test_uncapped_complex_spin_is_unaffected(tmp_path):
    # Guard the passthrough: without a centroid cap the splitting geometry is the placement
    # geometry, so ordinary complexes keep their spin. Fe(III) d5 octahedral low-spin -> 1.
    cx = Complex(metal=Metal("Fe", 3), ligands=[Ligand(smiles="[C-]#N") for _ in range(6)])
    assert pipeline.build_complex(cx, tmp_path, relax=False)[0].uhf == 1


def test_bent_metallocene_stays_out_of_cn_map():
    # A bent metallocene (two caps + two legs) sums to denticity 8. Now that CN 8
    # resolves to square-antiprism, the protection is that detect_metallocene
    # catches it FIRST (routes by the two eta-caps, not the summed CN), so it must
    # never reach geometries_for_cn(8).
    assert geometry.detect_metallocene([3, 3, 1, 1], [True, True, False, False]) is (
        Geometry.METALLOCENE_BENT
    )


def test_cp_perceives_as_eta_cap():
    # unified hapticity model: each Cp is ONE centroid site (denticity 1), so ferrocene is CN2.
    cx = Complex(Metal("Fe", 2), [Ligand(CP), Ligand(CP)])
    perception.perceive_complex(cx)
    assert all(l.denticity == 1 and any(len(s) >= 3 for s in l.pi_sites) for l in cx.ligands)
    assert cx.coordination_number == 2


def test_donor_override_whole_ring_is_eta_cap():
    # Selecting the 5 carbons of an embedded Cp ring -> ONE eta-cap coordination
    # site at the ring centroid (denticity 1, a pi_site), not 5 sigma donors and not
    # a 3-site facial triad. This is the centroid-cap convention for donor overrides
    # (so metallocenes are linear and multi-Cp ligands work). Ferroquine's Cp ligand.
    smi = "CN(C)CC1=C[CH-]C=C1CNC2=C(C=CC(Cl)=C3)C3=NC=C2"
    lig = Ligand(smi, donor_override=[4, 5, 6, 7, 8])
    perception.perceive(lig)
    assert lig.denticity == 1
    assert lig.pi_sites == [[4, 5, 6, 7, 8]]
    # a non-cyclic 5-atom selection stays 5 separate donors
    lig2 = Ligand(smi, donor_override=[0, 1, 2, 3, 9])
    perception.perceive(lig2)
    assert not lig2.is_arene and lig2.denticity == 5


def test_ferroquine_substituted_cp_perceived_as_eta5():
    # Ferroquine: a plain Cp + a functionalised Cp (bearing the aminoquinoline). Both must perceive
    # as eta5 caps (one centroid site each) at PARSE time — pydentate alone mis-perceives the
    # substituted ring — so the complex is a CN2 metallocene.
    cx = Complex(Metal("Fe", 2), [
        Ligand("C1=CC=C[CH-]1"),
        Ligand("CN(C)CC1=C[CH-]C=C1CNC2=C(C=CC(Cl)=C3)C3=NC=C2"),
    ])
    perception.perceive_complex(cx)
    caps = [any(len(s) >= 3 for s in l.pi_sites) for l in cx.ligands]
    assert all(c and l.denticity == 1 for c, l in zip(caps, cx.ligands))
    assert cx.coordination_number == 2
    assert geometry.detect_metallocene(
        [l.denticity for l in cx.ligands], caps
    ) is Geometry.METALLOCENE


def test_build_complex_accepts_xtb_timeout(tmp_path):
    # The per-structure xtb timeout threads through without relaxation running.
    cx = Complex(Metal("Fe", 2), [Ligand(CP), Ligand(CP)])
    (r,) = pipeline.build_complex(cx, tmp_path, relax=False, xtb_timeout_s=120)
    assert Path(r.xyz_path).exists()


def test_metallocene_restrains_full_cap_rings(tmp_path, monkeypatch):
    # Regression (ferroquine "lopsided Cp"): an η-sandwich must restrain EVERY cap
    # ring carbon to the metal — not just the 3-carbon facial triad, and not with
    # the restraint off — or an asymmetric substituted Cp slips off-axis under free
    # xtb. Capture the kwargs the (stubbed) relaxer is called with.
    from mecobi import optimize

    captured: dict = {}
    monkeypatch.setattr(optimize, "relax_with_xtb",
                        lambda xyz, **k: captured.update(k) or Path(xyz))
    cx = Complex(Metal("Fe", 2), [Ligand(CP), Ligand(CP)])
    (r,) = pipeline.build_complex(cx, tmp_path, relax=True)
    assert captured["restrain_donors"] is True        # was False for η-sandwiches
    assert len(captured["donor_indices"]) == 10       # all ring C, not the 6-atom triad
    assert len(r.donor_indices) == 10                 # centroid cap: viewer bonds all 10 ring C


def test_metallocene_electron_count_no_false_hydride():
    # Ferrocene: each η5-Cp cap donates 6e (not the 2e a single site implies), so the electron
    # count must see 18e (d6 + 2·6) and the missing-hydride guard must stay quiet. The naive
    # d + 2·CN (CN2 for the centroid model) gave 10e -> a bogus "4 missing hydrides".
    from mecobi import pipeline, spin

    cx = Complex(Metal("Fe", 2), [Ligand(CP), Ligand(CP)])
    perception.perceive_complex(cx)
    assert pipeline._donor_electron_pairs(cx) == 6            # 2 caps × 3 pairs (6e each)
    assert spin.possible_missing_hydrides("Fe", 2, pipeline._donor_electron_pairs(cx)) == 0


def test_metallocene_spin_ferrocene_diamagnetic():
    from mecobi import spin

    # ferrocene Fe(II) d6 low-spin -> 0 unpaired; Cp2TiCl2 Ti(IV) d0 -> 0.
    assert spin.unpaired_electrons("Fe", 2, Geometry.METALLOCENE, spin.Spin.LOW) == 0
    assert spin.unpaired_electrons("Ti", 4, Geometry.METALLOCENE_BENT, spin.Spin.LOW) == 0


# --------------------------------------------------------------------------- #
# full builds — slow (perception + stk + MCHammer)
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_build_ferrocene(tmp_path):
    cx = Complex(Metal("Fe", 2), [Ligand(CP), Ligand(CP)])
    (r,) = pipeline.build_complex(cx, tmp_path, relax=False)
    assert r.total_charge == 0 and r.uhf == 0
    xyz = Path(r.xyz_path)
    assert int(xyz.read_text().splitlines()[0]) == 21  # Fe + 2x C5H5
    # unified centroid model: each Cp is one centroid site binding all five ring
    # carbons -> 10 topology bonds (all 10 C ~2.2 A after relaxation).
    assert len(r.donor_indices) == 10


@pytest.mark.slow
def test_ferrocene_relaxes_to_symmetric_eta5(tmp_path):
    # η-sandwiches restrain every cap ring carbon to the metal (pinning only the
    # 3-carbon facial triad slips the ring), so all 10 Fe-C settle to a uniform η5.
    import numpy as np

    cx = Complex(Metal("Fe", 2), [Ligand(CP), Ligand(CP)])
    (r,) = pipeline.build_complex(cx, tmp_path, relax=True)
    lines = Path(r.xyz_path).read_text().splitlines()[2:]
    syms, xyz = [], []
    for ln in lines:
        p = ln.split()
        if len(p) >= 4:
            syms.append(p[0]); xyz.append([float(x) for x in p[1:4]])
    xyz = np.array(xyz); fe = xyz[syms.index("Fe")]
    fec = sorted(float(np.linalg.norm(xyz[i] - fe)) for i, s in enumerate(syms) if s == "C")[:10]
    assert max(fec) - min(fec) < 0.3, f"Cp rings not symmetric η5: {fec}"
    assert 1.9 < min(fec) and max(fec) < 2.5


@pytest.mark.slow
def test_ferroquine_substituted_cp_not_lopsided(tmp_path):
    # Regression: ferroquine's substituted Cp is a localised carbanion ring that
    # GFN2 slips off-axis under free relaxation (lopsided sandwich). Restraining
    # every cap ring carbon holds it η5 — or, if xtb still ejects one, the
    # dissociation guard keeps the clean assembled sandwich. Either way no cap
    # carbon may end up "lopsided" (far off the metal) in the written structure.
    import numpy as np

    cx = Complex(Metal("Fe", 2), [
        Ligand("C1=CC=C[CH-]1"),
        Ligand("CN(C)CC1=C[CH-]C=C1CNC2=C(C=CC(Cl)=C3)C3=NC=C2"),
    ])
    (r,) = pipeline.build_complex(cx, tmp_path, relax=True)
    lines = Path(r.xyz_path).read_text().splitlines()[2:]
    syms, xyz = [], []
    for ln in lines:
        p = ln.split()
        if len(p) >= 4:
            syms.append(p[0]); xyz.append([float(x) for x in p[1:4]])
    xyz = np.array(xyz); fe = xyz[syms.index("Fe")]
    # the 10 nearest carbons are the two cap rings; none may be flung off-axis
    fec = sorted(float(np.linalg.norm(xyz[i] - fe)) for i, s in enumerate(syms) if s == "C")[:10]
    assert max(fec) < 2.9, f"a Cp carbon slipped lopsided off the metal: {fec}"


@pytest.mark.slow
def test_build_ruthenocene(tmp_path):
    cx = Complex(Metal("Ru", 2), [Ligand(CP), Ligand(CP)])
    (r,) = pipeline.build_complex(cx, tmp_path, relax=False)
    assert r.total_charge == 0
    assert Path(r.xyz_path).exists()


@pytest.mark.slow
def test_build_bent_metallocene_cp2ticl2(tmp_path):
    cx = Complex(
        Metal("Ti", 4),
        [Ligand(CP), Ligand(CP), Ligand("[Cl-]"), Ligand("[Cl-]")],
        geometry=Geometry.METALLOCENE_BENT,
    )
    (r,) = pipeline.build_complex(cx, tmp_path, relax=False)
    assert r.total_charge == 0 and r.uhf == 0
    assert Path(r.xyz_path).exists()


@pytest.mark.slow
def test_build_square_planar_tetradentate(tmp_path):
    cx = Complex(Metal("Ni", 2), [Ligand(CYCLAM)], geometry=Geometry.SQUARE_PLANAR)
    (r,) = pipeline.build_complex(cx, tmp_path, relax=False)
    assert r.total_charge == 2
    assert len(r.donor_indices) == 4
    assert Path(r.xyz_path).exists()


@pytest.mark.slow
def test_build_octahedral_tetradentate_bidentate(tmp_path):
    cx = Complex(Metal("Fe", 3), [Ligand(SALEN), Ligand(BPY)], geometry=Geometry.OCTAHEDRAL)
    (r,) = pipeline.build_complex(cx, tmp_path, relax=False)
    assert r.total_charge == 1  # Fe(III) + salen(2-) + neutral bpy
    assert len(r.donor_indices) == 6
    assert Path(r.xyz_path).exists()
