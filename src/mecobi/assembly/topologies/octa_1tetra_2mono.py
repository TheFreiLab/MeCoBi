"""Octahedral (4,1,1): a planar tetradentate belt + two trans axial monodentates.

The classic salen/porphyrin/cyclam MX2 motif — the tetradentate wraps the
equatorial plane (like stk's Porphyrin, ligand centred on the metal) and two
monodentates cap the axial ±z sites.
"""
from __future__ import annotations

import stk

from .metal_complex import MetalComplex
from .vertices import (
    MetalVertex,
    PlanarTetraDentateLigandVertex,
    RobustMonoDentateLigandVertex,
)

_R = 2.5


class OctahedralTetraDentate2Mono(MetalComplex):

    _metal_vertex_prototypes = (MetalVertex(0, (0.0, 0.0, 0.0)),)
    _ligand_vertex_prototypes = (
        PlanarTetraDentateLigandVertex(1, (0.0, 0.0, 0.0)),   # equatorial belt
        RobustMonoDentateLigandVertex(2, (0.0, 0.0, _R)),     # axial +z
        RobustMonoDentateLigandVertex(3, (0.0, 0.0, -_R)),    # axial -z
    )
    _edge_prototypes = (
        stk.Edge(0, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(_R, 0.0, 0.0)),
        stk.Edge(1, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, _R, 0.0)),
        stk.Edge(2, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(-_R, 0.0, 0.0)),
        stk.Edge(3, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, -_R, 0.0)),
        stk.Edge(4, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=(0.0, 0.0, _R)),
        stk.Edge(5, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[2], position=(0.0, 0.0, -_R)),
    )
