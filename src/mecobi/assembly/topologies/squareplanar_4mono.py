from __future__ import annotations
from stk._internal.topology_graphs.edge import Edge
from .metal_complex import MetalComplex
from .vertices import MetalVertex, RobustMonoDentateLigandVertex

class SquarePlanar_4mono(MetalComplex):
    _metal_vertex_prototypes = (MetalVertex(0, (0, 0, 0)),)
    _ligand_vertex_prototypes = (
            RobustMonoDentateLigandVertex(1, (2.5001, 0.0012, 0.0)),
            RobustMonoDentateLigandVertex(2, (0.0012, 2.5001, 0.0)),
            RobustMonoDentateLigandVertex(3, (-2.5001, -0.0012, 0.001)),
            RobustMonoDentateLigandVertex(4, (-0.0012, -2.5001, 0.0)),
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
        Edge(
            id=2,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[2],
        ),
        Edge(
            id=3,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[3],
        ),
    )