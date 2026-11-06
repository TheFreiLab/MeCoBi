"""Metallocene topologies: two eta-bound Cp/arene caps sandwiching the metal.

Each cap is treated as a facial triad (denticity 3, the same perception as the
piano-stool half-sandwich), placed on a ``PlanarTriDentateLigandVertex`` whose
ring plane is held perpendicular to the cap->metal axis. Two caps on opposite
sides give a metallocene:

``Metallocene`` — (3, 3): a parallel sandwich, the two rings on the +z/-z axis
(ferrocene, ruthenocene, cobaltocene).

``BentMetallocene`` — (3, 3, 1, 1): the two rings splayed into a wedge with two
monodentate legs filling the open side (Cp2TiCl2 / Cp2ZrCl2 bent metallocenes).

The cap ring binds through a facial triad of ring carbons (assembly trims the
ring to three spread carbons, see ``assembly.build`` / ``_chem.facial_triad``);
xtb then relaxes each cap to true eta5/eta6.
"""
from __future__ import annotations

import numpy as np
import stk

from .metal_complex import MetalComplex
from .vertices import (
    MetalVertex,
    PlanarTriDentateLigandVertex,
    RobustMonoDentateLigandVertex,
)

_RING = 2.0   # metal -> ring-centroid distance along the cap axis (xtb relaxes)
_RC = 1.25    # ring-carbon radius from the cap axis (Cp-like)
_R = 2.5      # metal -> monodentate-leg distance


def _unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def _cap(axis):
    """(centroid, [edge0, edge1, edge2]) for an eta-cap along ``axis``.

    The centroid sits ``_RING`` along the (unit) axis; the three carbon binding
    points ring it at radius ``_RC`` in the plane perpendicular to the axis, so
    their common plane normal IS the axis — ``PlanarTriDentateLigandVertex`` then
    holds the ring perpendicular to the sandwich axis.
    """
    a = _unit(axis)
    centroid = _RING * a
    ref = np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = _unit(np.cross(a, ref))
    v = np.cross(a, u)
    edges = [
        tuple(centroid + _RC * (np.cos(t) * u + np.sin(t) * v))
        for t in (0.0, 2 * np.pi / 3, 4 * np.pi / 3)
    ]
    return tuple(centroid), edges


# Parallel sandwich: caps on +z / -z.
_TOP_C, _TOP_E = _cap((0.0, 0.0, 1.0))
_BOT_C, _BOT_E = _cap((0.0, 0.0, -1.0))


class Metallocene(MetalComplex):
    """(3, 3) parallel sandwich: two eta-caps on the +z / -z axis (ferrocene-type)."""

    _metal_vertex_prototypes = (MetalVertex(0, (0.0, 0.0, 0.0)),)
    _ligand_vertex_prototypes = (
        PlanarTriDentateLigandVertex(1, _TOP_C),
        PlanarTriDentateLigandVertex(2, _BOT_C),
    )
    _edge_prototypes = (
        stk.Edge(0, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=_TOP_E[0]),
        stk.Edge(1, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=_TOP_E[1]),
        stk.Edge(2, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=_TOP_E[2]),
        stk.Edge(3, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=_BOT_E[0]),
        stk.Edge(4, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=_BOT_E[1]),
        stk.Edge(5, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=_BOT_E[2]),
    )


# Bent metallocene: caps splayed into the +x/+z and -x/+z quadrants (~45 deg off
# +z), two monodentate legs in the open wedge below (+/-y, -z).
_BENT_A_C, _BENT_A_E = _cap((0.7071, 0.0, 0.7071))
_BENT_B_C, _BENT_B_E = _cap((-0.7071, 0.0, 0.7071))
_LEG_Y = _R * np.sin(np.deg2rad(50.0))
_LEG_Z = _R * np.cos(np.deg2rad(50.0))


class BentMetallocene(MetalComplex):
    """(3, 3, 1, 1) bent metallocene: two splayed eta-caps + two monodentate legs."""

    _metal_vertex_prototypes = (MetalVertex(0, (0.0, 0.0, 0.0)),)
    _ligand_vertex_prototypes = (
        PlanarTriDentateLigandVertex(1, _BENT_A_C),
        PlanarTriDentateLigandVertex(2, _BENT_B_C),
        RobustMonoDentateLigandVertex(3, (0.0, _LEG_Y, -_LEG_Z)),
        RobustMonoDentateLigandVertex(4, (0.0, -_LEG_Y, -_LEG_Z)),
    )
    _edge_prototypes = (
        stk.Edge(0, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=_BENT_A_E[0]),
        stk.Edge(1, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=_BENT_A_E[1]),
        stk.Edge(2, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=_BENT_A_E[2]),
        stk.Edge(3, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=_BENT_B_E[0]),
        stk.Edge(4, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=_BENT_B_E[1]),
        stk.Edge(5, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=_BENT_B_E[2]),
        stk.Edge(6, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[2], position=(0.0, _LEG_Y, -_LEG_Z)),
        stk.Edge(7, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[3], position=(0.0, -_LEG_Y, -_LEG_Z)),
    )
