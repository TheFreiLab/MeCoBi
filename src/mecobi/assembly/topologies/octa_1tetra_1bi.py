"""Octahedral (4,2): a folded tetradentate + one cis bidentate.

Unlike the planar (4,1,1) belt, a tetradentate that shares the octahedron with a
*bidentate* cannot stay planar — the chelate needs two cis sites, so the
tetradentate folds (cis-beta) onto the other four. Here the tetradentate takes
{+x, +y, -x, -z} via the generic (approximate) ``PolyDentateLigandVertex`` and
the bidentate takes the remaining cis pair {-y, +z} via ``ChelateVertex``; xtb
relaxes the fold. This is the salen/cyclam-plus-chelate motif.
"""
from __future__ import annotations

import stk

from .metal_complex import MetalComplex
from .vertices import ChelateVertex, MetalVertex, PolyDentateLigandVertex

_R = 2.5
_B = _R / 2 ** 0.5  # chelate vertex on the bisector of its two cis edges


class OctahedralTetraDentateBidentate(MetalComplex):
    """(4,2) octahedral: a folded (cis-beta) tetradentate + one cis bidentate."""

    _metal_vertex_prototypes = (MetalVertex(0, (0.0, 0.0, 0.0)),)
    _ligand_vertex_prototypes = (
        PolyDentateLigandVertex(1, (0.0, 0.0, 0.0)),          # folded tetradentate
        ChelateVertex(2, (0.0, -_B, _B)),                     # cis bidentate (-y, +z)
    )
    _edge_prototypes = (
        stk.Edge(0, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(_R, 0.0, 0.0)),
        stk.Edge(1, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, _R, 0.0)),
        stk.Edge(2, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(-_R, 0.0, 0.0)),
        stk.Edge(3, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, 0.0, -_R)),
        stk.Edge(4, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=(0.0, -_R, 0.0)),
        stk.Edge(5, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=(0.0, 0.0, _R)),
    )
