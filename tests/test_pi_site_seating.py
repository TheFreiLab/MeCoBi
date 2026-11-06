"""Regression: an internal eta2 alkyne must seat side-on (pi-bond axis tangential
to the metal) so no backbone atom is jammed into the metal.

Guards the DILZED failure: methyl-C#C-phenyl was oriented by the generic
"point the body radially outward" rule (ill-defined when the FG centroid sits
mid-ligand), tipping a non-donor carbon to ~1.2 A from Mo -> xtb crash. The fix
in RobustMonoDentateLigandVertex rotates the C#C axis into the tangent plane.
No xtb needed -- this is an assembly-seating property.
"""
import tempfile

import numpy as np

from mecobi import pipeline
from mecobi.model import Complex, Ligand, Metal


def _build_assembled(ligs, metal, ox):
    cx = Complex(metal=Metal(metal, ox), name="pi_seat", ligands=ligs)
    with tempfile.TemporaryDirectory() as d:
        r = pipeline.build_complex(cx, d, relax=False)[0]
        lines = open(r.xyz_path).read().splitlines()
        n = int(lines[0].split()[0])
        els, xyz = [], []
        for ln in lines[2:2 + n]:
            s = ln.split()
            els.append(s[0])
            xyz.append([float(x) for x in s[1:4]])
        return els, np.array(xyz), r.metal_index, r.donor_indices


def test_internal_alkyne_seats_side_on_no_backbone_clash():
    # methyl-C#C-phenyl (an internal alkyne with heavy substituents on BOTH sides
    # of the pi-bond) + three chlorides.
    ligs = [Ligand("CC#Cc1ccccc1", donor_override=[1, 2])] + [
        Ligand("[Cl-]", donor_override=[0]) for _ in range(3)
    ]
    els, xyz, mi, donors = _build_assembled(ligs, "Mo", 2)
    m = xyz[mi]

    # the two alkyne carbons are the pi-site donors; they should straddle the vertex
    alkyne = [i for i in donors if els[i] == "C"]
    assert len(alkyne) == 2, f"expected 2 alkyne donor carbons, got {alkyne}"
    d_alkyne = [float(np.linalg.norm(xyz[i] - m)) for i in alkyne]
    assert all(1.8 < d < 2.8 for d in d_alkyne), f"alkyne C not seated: {d_alkyne}"

    # NO heavy atom may be jammed into the metal: nothing closer than ~1.8 A, and
    # in particular no atom closer than the nearer alkyne carbon minus a margin
    # (the backbone must not tip inward past the coordinating pi-bond).
    for i, el in enumerate(els):
        if i == mi or el == "H":
            continue
        d = float(np.linalg.norm(xyz[i] - m))
        assert d > 1.8, f"atom {i}{el} jammed into metal at {d:.2f} A"

    # side-on geometry: the C#C axis is ~perpendicular to the metal->midpoint vector
    c1, c2 = xyz[alkyne[0]], xyz[alkyne[1]]
    axis = (c2 - c1) / np.linalg.norm(c2 - c1)
    mid = (c1 + c2) / 2
    r = (mid - m) / np.linalg.norm(mid - m)
    perp = np.degrees(np.arccos(abs(np.dot(axis, r))))
    assert perp > 60, f"alkyne not side-on: axis-vs-radial only {perp:.0f} deg from perpendicular-ish"
