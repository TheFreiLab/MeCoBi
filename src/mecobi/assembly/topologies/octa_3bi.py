"""
Octahedral Delta
================

"""

from stk._internal.topology_graphs.edge import Edge

from .metal_complex import MetalComplex
from .vertices import ChelateVertex, MetalVertex


class IridiumTris(MetalComplex):

    _metal_vertex_prototypes = (MetalVertex(0, (0, 0, 0)),)
    # Three bidentate chelates spanning three mutually-orthogonal cis pairs of the
    # octahedral shell (+x/+y, -y/+z, -z/-x). Every donor site sits at radius 2.5;
    # each vertex sits on its chelate's bisector at radius 2.5 (2.5/sqrt(2)=1.7678).
    _ligand_vertex_prototypes = (
        ChelateVertex(1, (1.7678, 1.7678, 0)),
        ChelateVertex(2, (0, -1.7678, 1.7678)),
        ChelateVertex(3, (-1.7678, 0, -1.7678)),
    )

    _edge_prototypes = (
        Edge(
            id=0,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[0],
            position=(2.5, 0, 0),
        ),
        Edge(
            id=1,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[0],
            position=(0, 2.5, 0),
        ),
        Edge(
            id=4,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[1],
            position=(0, -2.5, 0),
        ),
        Edge(
            id=2,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[1],
            position=(0, 0, 2.5),
        ),
        Edge(
            id=5,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[2],
            position=(0, 0, -2.5),
        ),
        Edge(
            id=3,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[2],
            position=(-2.5, 0, 0),
        ),
    )
