"""Twist of a side-on (eta2) alkene/alkyne about its metal-midpoint axis is set by the site model.

It used to be whatever the placement produced: the same isomer built from two equivalent site
numberings came out with the C#C bond "lying" along one axis or "standing" 90 deg off, and xtb
does not cross between the two (DILZED). Now ``sites.eta2_axis`` prescribes it from the site the
ligand sits on, so a site assignment fixes it. Assembly only (relax off); donors given.
"""
import math

import numpy as np
import pytest

from mecobi import isomers, pipeline
from mecobi.assembly import sites
from mecobi.model import Complex, Geometry, Ligand, Metal


def _angle(u, v):
    c = abs(float(u @ v) / (np.linalg.norm(u) * np.linalg.norm(v)))
    return math.degrees(math.acos(min(1.0, c)))          # 0 = parallel (a bond has no direction)


def _build(tmp_path, metal, ox, ligands, geometry, site_map):
    ligs = [Ligand(s) for s, _ in ligands]
    for lig, (_, donors) in zip(ligs, ligands):
        lig.donor_override = list(donors)
    cx = Complex(metal=Metal(metal, ox), name="t", ligands=ligs)
    spec = isomers.parse_topology_spec(site_map, geometry)
    res = pipeline.build_complex(cx, tmp_path, relax=False, isomers_override=[spec])[0]
    lines = open(res.xyz_path).read().splitlines()[2:]
    syms = [ln.split()[0] for ln in lines]
    return syms, np.array([[float(x) for x in ln.split()[1:4]] for ln in lines])


def test_reference_axis_per_geometry():
    # octahedral site 3 (-y): the lowest-numbered perpendicular site is 0 (+x)
    assert sites.eta2_reference_site(Geometry.OCTAHEDRAL, 3) == 0
    assert sites.eta2_reference_site(Geometry.OCTAHEDRAL, 0) == 2
    pos = sites.site_positions(Geometry.OCTAHEDRAL)
    assert _angle(sites.eta2_axis(Geometry.OCTAHEDRAL, 3), pos[0]) < 1e-6
    # square planar: every other site is in the plane -> the bond stands on the plane normal
    sq = sites.site_positions(Geometry.SQUARE_PLANAR)
    normal = np.cross(sq[0], sq[1])
    for s in range(4):
        assert _angle(sites.eta2_axis(Geometry.SQUARE_PLANAR, s), normal) < 1e-6


def test_square_planar_alkene_stands_perpendicular_to_the_plane(tmp_path):
    # Zeise's anion [PtCl3(C2H4)]-: ethylene perpendicular to the PtCl3 plane
    ligands = [("C=C", [0, 1]), ("[Cl-]", [0]), ("[Cl-]", [0]), ("[Cl-]", [0])]
    syms, xyz = _build(tmp_path, "Pt", 2, ligands, Geometry.SQUARE_PLANAR, "0:0;1:1;2:2;3:3")
    cl = [i for i, s in enumerate(syms) if s == "Cl"]
    c = [i for i, s in enumerate(syms) if s == "C"]
    normal = np.cross(xyz[cl[0]] - xyz[0], xyz[cl[1]] - xyz[0])
    if np.linalg.norm(normal) < 0.5:                      # the two picked Cl happened to be trans
        normal = np.cross(xyz[cl[0]] - xyz[0], xyz[cl[2]] - xyz[0])
    assert _angle(xyz[c[1]] - xyz[c[0]], normal) < 20.0


@pytest.mark.parametrize("site_map,parallel_to", [
    ("0:3;1:0;2:1;3:2;4:4;5:5", "x"),     # alkyne on -y: reference site 0 (+x)
    ("0:0;1:2;2:3;3:1;4:4;5:5", "y"),     # alkyne on +x: reference site 2 (+y)
])
def test_octahedral_alkyne_follows_the_site_numbering(tmp_path, site_map, parallel_to):
    ligands = [("CC#CC", [1, 2])] + [("[C-]#[O+]", [0])] * 5
    syms, xyz = _build(tmp_path, "W", 0, ligands, Geometry.OCTAHEDRAL, site_map)
    # 2-butyne is the first ligand: atoms 1..4 are its carbons, 1 and 2 (0-based in ligand) bind
    cc = xyz[3] - xyz[2]
    axis = {"x": np.array([1.0, 0, 0]), "y": np.array([0, 1.0, 0])}[parallel_to]
    other = {"x": np.array([0, 0, 1.0]), "y": np.array([0, 0, 1.0])}[parallel_to]
    assert _angle(cc, axis) < 25.0, "the C#C bond is not along its reference site axis"
    assert _angle(cc, other) > 60.0
