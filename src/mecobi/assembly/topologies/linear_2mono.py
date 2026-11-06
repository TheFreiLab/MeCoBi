from __future__ import annotations
from stk._internal.topology_graphs.edge import Edge
from .metal_complex import MetalComplex
from .vertices import MetalVertex, RobustMonoDentateLigandVertex

class Linear_2mono(MetalComplex):
    _metal_vertex_prototypes = (MetalVertex(0, (0, 0, 0)),)
    _ligand_vertex_prototypes = (
        RobustMonoDentateLigandVertex(1, (4.5, 4.5, 0.0)),
        RobustMonoDentateLigandVertex(2, (-4.5, -4.5, 0.0)),
    )

    _edge_prototypes = (
        Edge(
            id=0,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[0],
        ),
        Edge(
            id=1,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[1],
        ),
    )