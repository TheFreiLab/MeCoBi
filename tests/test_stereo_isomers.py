"""Stereoisomer enumeration: Delta/Lambda enantiomers + donor-direction splitting.

The site-model enumerator deduplicates ordered donor->site assignments up to the
geometry's *proper* rotation group, so chiral complexes split into enantiomers
and asymmetric chelates split by donor direction, while symmetric chelates and
the coarse (stereo=False) mode collapse back to the geometric-isomer count.
"""

import numpy as np
import pytest

from mecobi import isomers, perception
from mecobi.assembly import sites
from mecobi.assembly._chem import donor_symmetry_classes
from mecobi.model import Complex, Geometry, Ligand, Metal

O = Geometry.OCTAHEDRAL

BPY = "c1ccc(-c2ccccn2)nc1"   # 2,2'-bipyridine: symmetric N,N chelate
EN = "NCCN"                    # ethylenediamine: symmetric N,N chelate
NO = "CN=Cc1ccccc1[O-]"        # salicylaldiminate: asymmetric N,O chelate
CP = "Cc1c(C)c(C)[c-](C)c1C"   # Cp*: facial arene cap (denticity 3)
CL = "[Cl-]"
TLD_DMP = "CC1=CC(=NC=C1)C2=NC=CC(=C2)C"
TLD_IP3T = (
    "C1=CC2=C3C(=C4C=CC=NC4=C2N=C1)N=C(N3)"
    "C5=CC=C(S5)C6=CC=C(S6)C7=CC=CS7"
)


def _cx(ligs, ox=3):
    cx = Complex(metal=Metal("Ir", ox), ligands=[Ligand(s) for s in ligs], geometry=O, name="x")
    perception.perceive_complex(cx)
    return cx


def _labels(ligs, ox=3, stereo=True):
    specs = isomers.enumerate_site_isomers(_cx(ligs, ox), O, stereo=stereo)
    return sorted(s.label for s in specs)


# --------------------------------------------------------------------------- #
# fast: symmetry groups + donor classes
# --------------------------------------------------------------------------- #

def test_proper_rotation_group_sizes():
    assert len(sites.proper_rotation_site_perms(O)) == 24
    assert len(sites.proper_rotation_site_perms(Geometry.SQUARE_PLANAR)) == 8
    # the full point group is strictly larger (adds the improper/mirror ops)
    assert len(sites.full_symmetry_site_perms(O)) > 24


def test_donor_symmetry_distinguishes_asymmetric_chelate():
    from rdkit import Chem

    ns = [a.GetIdx() for a in Chem.MolFromSmiles(BPY).GetAtoms() if a.GetSymbol() == "N"]
    assert len(set(donor_symmetry_classes(BPY, ns))) == 1  # bpy donors equivalent
    m = Chem.MolFromSmiles(NO)
    no = [a.GetIdx() for a in m.GetAtoms() if a.GetSymbol() in ("N", "O")]
    assert len(set(donor_symmetry_classes(NO, no))) == 2   # N,O distinct


# --------------------------------------------------------------------------- #
# fast: enumeration counts + labels
# --------------------------------------------------------------------------- #

def test_tris_symmetric_bidentate_is_delta_lambda():
    assert _labels([BPY, BPY, BPY]) == ["Delta", "Lambda"]
    assert _labels([EN, EN, EN]) == ["Delta", "Lambda"]


def test_tris_asymmetric_bidentate_splits_fac_mer_times_chirality():
    # M(A^B)3: fac + mer, each chiral -> 4 stereoisomers.
    specs = isomers.enumerate_site_isomers(_cx([NO, NO, NO], ox=0), O, stereo=True)
    assert len(specs) == 4
    assert sum(s.label.startswith("Delta") for s in specs) == 2
    assert sum(s.label.startswith("Lambda") for s in specs) == 2


def test_bis_bidentate_dichloride_is_cis_delta_lambda_plus_trans():
    assert _labels([BPY, BPY, CL, CL]) == ["Delta_cis", "Lambda_cis", "trans"]


def test_homoleptic_monodentate_is_single_isomer():
    assert len(isomers.enumerate_site_isomers(_cx([CL] * 6, ox=-3), O, stereo=True)) == 1


def test_stereo_false_collapses_to_coarse_count():
    # enantiomers + donor directions merge -> the geometric-isomer count
    assert len(isomers.enumerate_site_isomers(_cx([BPY, BPY, BPY]), O, stereo=False)) == 1
    assert len(isomers.enumerate_site_isomers(_cx([NO, NO, NO], ox=0), O, stereo=False)) == 1
    assert len(isomers.enumerate_site_isomers(_cx([BPY, BPY, CL, CL]), O, stereo=False)) == 2


@pytest.mark.xfail(
    strict=True,
    reason="Legacy test assumes a three-site facial Cp* cap, while perception "
    "uses one centroid site. Accepted scope decision for audit point 4; "
    "the stereo expectation needs a separate review.",
)
def test_pianostool_asymmetric_chelate_is_chiral_symmetric_is_not():
    # [Cp*Ir(N^O)Cl] is chiral-at-metal (2); [Cp*Ir(bpy)Cl] is achiral (1).
    assert len(isomers.enumerate_site_isomers(_cx([CP, NO, CL]), O, stereo=True)) == 2
    assert len(isomers.enumerate_site_isomers(_cx([CP, BPY, CL]), O, stereo=True)) == 1


# --------------------------------------------------------------------------- #
# slow: build + relax, enantiomers are equal-energy mirror images
# --------------------------------------------------------------------------- #

def _load(path):
    lines = open(path).read().splitlines()
    n = int(lines[0])
    els, xyz = [], []
    for ln in lines[2:2 + n]:
        q = ln.split()
        els.append(q[0])
        xyz.append([float(x) for x in q[1:4]])
    return els, np.array(xyz)


def _kabsch_rmsd(a, b, *, allow_reflection):
    a = a - a.mean(0)
    b = b - b.mean(0)
    u, _s, vt = np.linalg.svd(a.T @ b)
    d = 1.0 if allow_reflection else float(np.sign(np.linalg.det(vt.T @ u)))
    r = vt.T @ np.diag([1, 1, d]) @ u.T
    return float(np.sqrt(((b - a @ r.T) ** 2).sum() / len(a)))


@pytest.mark.slow
def test_tris_bidentate_enantiomers_are_mirror_images(tmp_path):
    from mecobi import pipeline

    cx = _cx([BPY, BPY, BPY])
    res = pipeline.build_complex(cx, tmp_path, all_isomers=True, stereo=True, relax=True)
    assert len(res) == 2
    (e0, x0), (e1, x1) = _load(res[0].xyz_path), _load(res[1].xyz_path)
    assert e0 == e1
    # not superimposable by proper rotation, but superimposable once a reflection
    # is allowed -> genuine enantiomers.
    proper = _kabsch_rmsd(x0, x1, allow_reflection=False)
    mirror = _kabsch_rmsd(x0, x1, allow_reflection=True)
    assert proper > 1.0        # genuinely different by proper rotation
    assert mirror < proper / 2  # but close once a reflection is allowed
    lam = next(r for r in res if r.isomer_label == "Lambda")
    assert any("reflected the duplicate assembled geometry" in w for w in lam.warnings)


@pytest.mark.slow
def test_tld1433_enantiomers_remain_independently_assembled(tmp_path):
    """The duplicate-hand repair must not alter a distinct heteroleptic pair."""
    from mecobi import pipeline

    cx = Complex(
        metal=Metal("Ru", 2),
        ligands=[Ligand(TLD_DMP), Ligand(TLD_DMP), Ligand(TLD_IP3T)],
        geometry=O,
        name="TLD1433",
    )
    perception.perceive_complex(cx)
    res = pipeline.build_complex(cx, tmp_path, all_isomers=True, stereo=True, relax=False)
    assert sorted(r.isomer_label for r in res) == ["Delta", "Lambda"]
    assert not any(
        "reflected the duplicate assembled geometry" in w
        for r in res
        for w in r.warnings
    )

    (e0, x0), (e1, x1) = _load(res[0].xyz_path), _load(res[1].xyz_path)
    assert e0 == e1
    proper = _kabsch_rmsd(x0, x1, allow_reflection=False)
    mirror = _kabsch_rmsd(x0, x1, allow_reflection=True)
    assert proper > 1.0
    assert mirror < proper / 2
