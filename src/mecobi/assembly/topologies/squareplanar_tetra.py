"""Square-planar tetradentate (4,): a single planar tetradentate ligand.

The general salen / cyclam / porphyrin square-planar motif — four coplanar
donors wrapping the metal in the xy-plane. Unlike routing (4,) to stk's built-in
``Porphyrin`` (which assumes a porphyrin-like functional-group layout), this
custom class uses ``PlanarTetraDentateLigandVertex`` so any planar tetradentate
(salen, cyclam, phthalocyanine, porphyrin) places its four donors on the ±x/±y
sites and lets xtb relax the ring.
"""
from __future__ import annotations

import stk

from .metal_complex import MetalComplex
from .vertices import MetalVertex, PlanarTetraDentateLigandVertex

_R = 2.5


class SquarePlanarTetraDentate(MetalComplex):
    """(4,) square planar: one planar tetradentate ligand in the equatorial plane."""

    _metal_vertex_prototypes = (MetalVertex(0, (0.0, 0.0, 0.0)),)
    _ligand_vertex_prototypes = (
        PlanarTetraDentateLigandVertex(1, (0.0, 0.0, 0.0)),
    )
    _edge_prototypes = (
        stk.Edge(0, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(_R, 0.0, 0.0)),
        stk.Edge(1, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, _R, 0.0)),
        stk.Edge(2, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(-_R, 0.0, 0.0)),
        stk.Edge(3, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, -_R, 0.0)),
    )
