"""Square-planar (3,1): a meridional pincer tridentate + one monodentate.

The Au(III)/Pt(II) pincer motif ([C^N^C]MX, [N^N^N]MX, ...): the tridentate
occupies three coplanar sites (its central donor trans to the leaving group) and
the monodentate takes the fourth.
"""
from __future__ import annotations

import stk

from .metal_complex import MetalComplex
from .vertices import MeridionalTriDentateLigandVertex, MetalVertex, RobustMonoDentateLigandVertex

_R = 2.5


class SquarePlanarTriDentateMono(MetalComplex):

    _metal_vertex_prototypes = (MetalVertex(0, (0.0, 0.0, 0.0)),)
    _ligand_vertex_prototypes = (
        # Meridional pincer: central donor -> central edge (+y), ends -> +x/-x (trans),
        # so the leaving group at -y lands trans to the central donor. The central-aware
        # vertex handles pincers whose central donor is not the middle atom (PNP with a
        # trailing pyridine-N), which the generic tridentate vertex mis-seats.
        MeridionalTriDentateLigandVertex(1, (0.0, _R / 3.0, 0.0)),   # pincer: +x, +y, -x
        RobustMonoDentateLigandVertex(2, (0.0, -_R, 0.0)),    # leaving group: -y
    )
    _edge_prototypes = (
        stk.Edge(0, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(_R, 0.0, 0.0)),
        stk.Edge(1, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, _R, 0.0)),
        stk.Edge(2, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(-_R, 0.0, 0.0)),
        stk.Edge(3, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=(0.0, -_R, 0.0)),
    )
