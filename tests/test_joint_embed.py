"""Joint re-embedding of a crowded sphere of monodentates and chelates (mecobi.joint_embed).

Ligands are embedded one by one and seated rigidly, so the bodies of bulky neighbours never see
each other: Pt(PPh3)4 leaves the assembly with its phenyl rings threaded through one another
(dozens of inter-ligand atom pairs under 1.6 A) and P-Pt-P angles of 79-135 deg after MCHammer.
The repair embeds the whole complex in one distance-geometry run with the metal and the donors
pinned on their sites. Checked pre-xtb (relax off); donors are given, so no pydentate/torch.
"""
import itertools
import math

import numpy as np
import pytest

from mecobi import isomers, joint_embed, pipeline
from mecobi.model import Complex, Geometry, Ligand, Metal

PPH3 = "P(c1ccccc1)(c1ccccc1)c1ccccc1"


BINAP = ("c1ccc(P(c2ccccc2)c2ccc3ccccc3c2-c2c(P(c3ccccc3)c3ccccc3)ccc3ccccc23)cc1", [4, 23])
DPPE = ("c1ccc(P(CCP(c2ccccc2)c2ccccc2)c2ccccc2)cc1", [4, 7])
BIPY = ("c1ccc(-c2ccccn2)nc1", [9, 10])
PHEN = ("c1cnc2c(c1)ccc1cccnc12", [2, 12])


def _build(tmp_path, metal, ox, ligands, **opts):
    ligs = [Ligand(s if isinstance(s, str) else s[0]) for s in ligands]
    for lig, s in zip(ligs, ligands):
        lig.donor_override = [0] if isinstance(s, str) else list(s[1])
    cx = Complex(metal=Metal(metal, ox), name="t", ligands=ligs)
    res = pipeline.build_complex(cx, tmp_path, all_isomers=False, relax=False, **opts)[0]
    lines = open(res.xyz_path).read().splitlines()[2:]
    syms = [ln.split()[0] for ln in lines]
    xyz = np.array([[float(x) for x in ln.split()[1:4]] for ln in lines])
    return res, syms, xyz


def _ligand_ids(syms, per_ligand, n_ligands):
    """Ligand id per atom for a metal-first sphere of identical ligands (contiguous blocks)."""
    assert len(syms) == 1 + per_ligand * n_ligands
    return np.array([-1] + [k for k in range(n_ligands) for _ in range(per_ligand)])


def test_collapse_count_sees_only_interpenetration():
    elems = ["Pt", "C", "C", "C", "H"]
    comp = np.array([-1, 0, 0, 1, 1])
    apart = [[0, 0, 0], [2, 0, 0], [3.4, 0, 0], [-2, 0, 0], [-3, 0, 0]]
    assert joint_embed.collapse_count(apart, elems, comp) == 0
    # the bonded C-C of ligand 0 (1.4 A) is intra-ligand and never counts
    fused = [[0, 0, 0], [2, 0, 0], [3.4, 0, 0], [2.6, 1.0, 0], [-3, 0, 0]]
    assert joint_embed.collapse_count(fused, elems, comp) == 2   # C3 on both carbons of ligand 0


def test_tetrakis_triphenylphosphine_is_re_embedded_without_collapse(tmp_path):
    res, syms, xyz = _build(tmp_path, "Pt", 0, [PPH3] * 4)
    assert any("re-embedded the whole complex jointly" in w for w in res.warnings)

    comp = _ligand_ids(syms, 34, 4)                       # PPh3 = P + 18 C + 15 H
    assert joint_embed.collapse_count(xyz, syms, comp) == 0
    lig = np.where(comp >= 0)[0]
    d = np.linalg.norm(xyz[lig][:, None] - xyz[lig][None], axis=-1)
    other = np.triu(comp[lig][:, None] != comp[lig][None], 1)
    assert d[other].min() > 1.6, "ligand bodies still interpenetrate"

    # the donors stay ON their sites: an ideal tetrahedron at one common Pt-P distance
    ps = [i for i, s in enumerate(syms) if s == "P"]
    dist = [np.linalg.norm(xyz[p] - xyz[0]) for p in ps]
    assert max(dist) - min(dist) < 0.02
    for a, b in itertools.combinations(ps, 2):
        u, v = xyz[a] - xyz[0], xyz[b] - xyz[0]
        ang = math.degrees(math.acos(u @ v / np.linalg.norm(u) / np.linalg.norm(v)))
        assert abs(ang - 109.47) < 2.0

    # every P-C bond is still a P-C bond
    for p in ps:
        assert sum(1 for i, s in enumerate(syms)
                   if s == "C" and np.linalg.norm(xyz[i] - xyz[p]) < 2.0) == 3


def test_switch_off_keeps_the_old_assembly(tmp_path, monkeypatch):
    monkeypatch.setenv("MECOBI_JOINT_EMBED", "0")
    res, syms, xyz = _build(tmp_path, "Pt", 0, [PPH3] * 4)
    assert not any("re-embedded" in w for w in res.warnings)
    assert joint_embed.collapse_count(xyz, syms, _ligand_ids(syms, 34, 4)) > 0


def test_build_option_off_keeps_the_old_assembly(tmp_path):
    # the GUI "Untangle crowded ligands" toggle / run.py --no-reembed-crowded
    res, syms, xyz = _build(tmp_path, "Pt", 0, [PPH3] * 4, reembed_crowded=False)
    assert not any("re-embedded" in w for w in res.warnings)
    assert joint_embed.collapse_count(xyz, syms, _ligand_ids(syms, 34, 4)) > 0


@pytest.mark.parametrize("ligands", [["[Cl-]"] * 4, ["N", "N", "[Cl-]", "[Cl-]"]])
def test_uncrowded_sphere_is_left_alone(tmp_path, ligands):
    res, _, _ = _build(tmp_path, "Pt", 2, ligands)
    assert not any("re-embedded" in w for w in res.warnings)


# --------------------------------------------------------------------------- chelates
def _inter_ligand_min(syms, xyz, sizes):
    comp = np.array([-1] + [k for k, n in enumerate(sizes) for _ in range(n)])
    lig = np.where(comp >= 0)[0]
    d = np.linalg.norm(xyz[lig][:, None] - xyz[lig][None], axis=-1)
    other = np.triu(comp[lig][:, None] != comp[lig][None], 1)
    return joint_embed.collapse_count(xyz, syms, comp), float(d[other].min())


def test_two_interpenetrating_chelates_are_re_embedded(tmp_path):
    # ZIHHUT: Pt(0) with two BINAPs. Seated one by one the two ligands thread through each other
    # (dozens of inter-ligand pairs under 1.6 A); the whole-complex embedding meshes them.
    # Built on the crystal's site map (each BINAP spans two tetrahedral sites), as the benchmark does.
    spec = isomers.parse_topology_spec("0:0,2;1:1,3", Geometry.TETRAHEDRAL)
    res, syms, xyz = _build(tmp_path, "Pt", 0, [BINAP, BINAP], isomers_override=[spec])
    assert any("re-embedded the whole complex jointly" in w for w in res.warnings)
    per = (len(syms) - 1) // 2
    n, closest = _inter_ligand_min(syms, xyz, [per, per])
    assert n == 0 and closest > 1.6
    ps = [i for i, s in enumerate(syms) if s == "P"]
    assert len(ps) == 4 and all(np.linalg.norm(xyz[p] - xyz[0]) < 2.6 for p in ps)

    _, s0, x0 = _build(tmp_path, "Pt", 0, [BINAP, BINAP], isomers_override=[spec],
                       reembed_crowded=False)
    assert _inter_ligand_min(s0, x0, [per, per])[0] > 0        # the collapse it repairs


@pytest.mark.parametrize("metal, ligands", [
    ("Pd", [BIPY, "[Cl-]", "[Cl-]"]),
    ("Pd", [PHEN, "[Cl-]", "[Cl-]"]),
])
def test_uncollapsed_chelate_complex_is_left_alone(tmp_path, metal, ligands):
    # a bulky chelate that is NOT interpenetrating must never be re-drawn: the trigger looks at
    # the assembly as it is (chelates are not slid in by the pre-relax reposition). Rigid
    # chelates only: a flexible diphosphine's conformer depends on the RDKit version AND platform
    # (Pd(dppe)Cl2 under RDKit 2026.03 puts a backbone C 1.5 A from where a Cl- is seated, a real
    # collapse the re-embedding repairs; Pt(dppp)Cl2 re-embeds on Linux but not on Windows).
    res, _, _ = _build(tmp_path, metal, 2, ligands)
    assert not any("re-embedded" in w for w in res.warnings)


def test_bipy_stranded_by_mchammer_ends_bound_and_unthreaded(tmp_path):
    # Pd(bipy)(PPh3)Cl was in the left-alone list above while MCHammer's assembly had a bipy N at 2.78 A
    # (Pd-N 2.05 A): the stranded-donor term now rejects that assembly, and the raw placement it falls
    # back to has a PPh3 phenyl threaded through the bipy, so the complex IS re-embedded. What must hold
    # is the outcome: both N on the metal and no ligand passing through another.
    _, syms, xyz = _build(tmp_path, "Pd", 2, [BIPY, PPH3, "[Cl-]"])
    assert syms[0] == "Pd" and len(syms) == 1 + 20 + 34 + 1     # bipy C10H8N2, PPh3, Cl
    comp = np.array([-1] + [0] * 20 + [1] * 34 + [2])
    assert joint_embed.collapse_count(xyz, syms, comp) == 0
    n_dist = [np.linalg.norm(xyz[i] - xyz[0]) for i, s in enumerate(syms) if s == "N"]
    assert len(n_dist) == 2 and max(n_dist) < 2.3, n_dist


def test_halide_is_judged_where_it_will_be_seated(monkeypatch):
    # the site model leaves a halide on a ~1.25 A shell (ff_declash seats it later); judged there
    # it "collapses" onto any chelate atom near the metal. Seated at Pd-Cl 2.33 A it is clear.
    elems = ["Pd", "P", "C", "C", "Cl"]
    comp = np.array([-1, 0, 0, 0, 1])
    xyz = np.array([[0, 0, 0], [2.3, 0, 0], [3.0, 1.4, 0], [0.2, -0.6, 0.0], [0, -1.25, 0]])
    assert joint_embed.collapse_count(xyz, elems, comp) == 1      # C3 0.68 A from the shell Cl

    class _Asm:                                       # the one stk call joint_embed makes here
        def __init__(self, p):
            self.p = p

        def get_position_matrix(self):
            return self.p

    bonds = [(0, 1), (1, 2), (2, 3), (0, 4)]
    monkeypatch.setattr(joint_embed, "_topology", lambda c, m: (elems, 0, bonds, [1, 4], comp))
    monkeypatch.setattr(joint_embed, "_eligible", lambda *a: True)
    _, note = joint_embed.joint_embed(lambda mch: pytest.fail("re-embed triggered"),
                                      _Asm(xyz), "Pd", metal_ox=2, cn=4)
    assert note is None


def test_eligibility_excludes_haptic_and_high_denticity():
    # metal 0; ligand A = atoms 1-4 (donors 1, 2), ligand B = atoms 5-8 (donor 5)
    elems = ["Fe"] + ["C"] * 8
    comp = np.array([-1, 0, 0, 0, 0, 1, 1, 1, 1])
    chelate = [(0, 1), (0, 2), (0, 5), (1, 3), (3, 2), (3, 4), (5, 6), (6, 7), (7, 8)]
    assert joint_embed._eligible(elems, [1, 2, 5], comp, chelate)
    haptic = [(0, 1), (0, 2), (0, 5), (1, 2), (2, 3), (3, 4), (5, 6), (6, 7), (7, 8)]
    assert not joint_embed._eligible(elems, [1, 2, 5], comp, haptic)   # donors 1-2 are bonded
    # five donors on one ligand: never re-embedded
    elems5 = ["Fe"] + ["N"] * 5 + ["C"] * 5 + ["C"] * 4
    comp5 = np.array([-1] + [0] * 10 + [1] * 4)
    b5 = [(0, k) for k in range(1, 6)] + [(k, k + 5) for k in range(1, 6)]         + [(6, 7), (7, 8), (8, 9), (9, 10)] + [(0, 11), (11, 12), (12, 13), (13, 14)]
    assert not joint_embed._eligible(elems5, [1, 2, 3, 4, 5, 11], comp5, b5)


def test_self_clash_counts_a_ligand_folded_onto_itself():
    # a 7-atom chain on ligand 0: ends 6 bonds apart
    elems = ["Pt"] + ["C"] * 7
    comp = np.array([-1] + [0] * 7)
    bonds = [(0, 1)] + [(k, k + 1) for k in range(1, 7)]
    straight = [[0, 0, 0]] + [[2 + 1.5 * k, 0, 0] for k in range(7)]
    assert joint_embed._self_clashes(straight, elems, comp, bonds, 0) == 0
    folded = [list(p) for p in straight]
    folded[7] = [2.0, 1.8, 0.0]                      # the tail swung back onto the head
    assert joint_embed._self_clashes(folded, elems, comp, bonds, 0) >= 1


def test_stereo_check_keeps_a_biaryl_axis_sense():
    same = ([], [], [(3, 9, True)])
    assert joint_embed._same_stereo(same, ([], [], [(3, 9, True)]))
    assert not joint_embed._same_stereo(same, ([], [], [(3, 9, False)]))   # atropisomer flipped
    assert joint_embed._same_stereo(same, ([], [], []))                    # axis went flat: no sense
    assert not joint_embed._same_stereo(([("C1", "R")], [], []), ([("C1", "S")], [], []))
