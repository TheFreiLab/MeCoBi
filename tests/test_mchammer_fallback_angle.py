"""MCHammer-fallback angular score is frame-free (rotation + donor-matching invariant).

Regression: Au(III)(ppy)(1,3-dithiolate) built as ONE isomer went through the fixed
``square_2bi`` topology, which seats donors on the diagonals (45 deg off the site-model
axes). The old fixed-frame greedy score charged both candidates a bogus ~70 deg RMS, so the
fallback discarded the correct MCHammer placement (M-L 2.3 A) for the raw one (M-L 2.9 A).
"""

import math
from pathlib import Path

import numpy as np

from mecobi import pipeline
from mecobi.assembly import sites
from mecobi.model import Complex, Geometry, Ligand, Metal

PPY = "C1(C2=NC=CC=C2)=CC=CC=[C-]1"     # cyclometalated C^N
DITHIOLATE = "[S-]CCC(CCCCCC)[S-]"      # S^S, 6-ring chelate


def _rot(axis, deg):
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    t = math.radians(deg)
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(t) * k + (1 - math.cos(t)) * k @ k


def test_angular_score_is_rotation_and_order_invariant():
    for geom, cn in ((Geometry.LINEAR, 2), (Geometry.SQUARE_PLANAR, 4),
                     (Geometry.OCTAHEDRAL, 6), (Geometry.TETRAHEDRAL, 4)):
        sv = np.asarray(sites.site_positions(geom, cn), float)
        dv = (sv @ _rot((1, 2, 3), 37).T)[::-1]          # rotated AND relabelled
        dv /= np.linalg.norm(dv, axis=1)[:, None]
        assert pipeline._angular_rms_deviation(dv, sv) < 1e-3


def test_angular_score_still_flags_a_real_collapse():
    sv = np.asarray(sites.site_positions(Geometry.SQUARE_PLANAR, 4), float)
    dv = np.array([[1, 0, 0], [0.9, 0.44, 0], [0, 1, 0], [-1, 0, 0]], float)  # two donors 26 deg apart
    dv /= np.linalg.norm(dv, axis=1)[:, None]
    assert pipeline._angular_rms_deviation(dv, sv) > 25.0


def test_single_isomer_au_ppy_dithiolate_keeps_mchammer(tmp_path):
    cx = Complex(metal=Metal("Au", 3), ligands=[
        Ligand(PPY, donor_override=[2, 11]), Ligand(DITHIOLATE, donor_override=[0, 10])])
    (res,) = pipeline.build_complex(cx, tmp_path, relax=False)
    assert not any(pipeline.MCH_WORSE_MSG in w for w in res.warnings)
    lines = Path(res.xyz_path).read_text().splitlines()[2:]
    xyz = [(ln.split()[0], np.array(ln.split()[1:4], float)) for ln in lines if ln.strip()]
    au = next(p for e, p in xyz if e == "Au")
    ml = sorted(float(np.linalg.norm(p - au)) for e, p in xyz if e != "H" and e != "Au")[:4]
    assert max(ml) < 2.6, ml   # the raw placement left every M-L at ~2.9 A
