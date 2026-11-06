"""Octahedral (3,3): two meridional tridentates on perpendicular planes.

The bis-terpyridine / [M(N^N^N)2] motif — each tridentate spans three meridional
sites, the two ligand planes orthogonal so together they fill all six sites.
"""
from __future__ import annotations

import stk

from .metal_complex import MetalComplex
from .vertices import MetalVertex, TriDentateLigandVertex

_R = 2.5


class OctahedralBisTriDentate(MetalComplex):

    _metal_vertex_prototypes = (MetalVertex(0, (0.0, 0.0, 0.0)),)
    _ligand_vertex_prototypes = (
        TriDentateLigandVertex(1, (0.0, 0.0, _R / 3.0)),   # meridional in xz: +x, +z, -x
        TriDentateLigandVertex(2, (0.0, 0.0, -_R / 3.0)),  # meridional in yz: +y, -z, -y
    )
    _edge_prototypes = (
        stk.Edge(0, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(_R, 0.0, 0.0)),
        stk.Edge(1, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, 0.0, _R)),
        stk.Edge(2, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(-_R, 0.0, 0.0)),
        stk.Edge(3, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=(0.0, _R, 0.0)),
        stk.Edge(4, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=(0.0, -_R, 0.0)),
        stk.Edge(5, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=(0.0, 0.0, -_R)),
    )
