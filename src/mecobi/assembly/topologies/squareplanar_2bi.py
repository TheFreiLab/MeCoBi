from __future__ import annotations
from stk._internal.topology_graphs.edge import Edge
from .metal_complex import MetalComplex
from .vertices import MetalVertex, BiDentateLigandVertex

class SquarePlanar_2bi(MetalComplex):
    _metal_vertex_prototypes = (MetalVertex(0, (0, 0, 0)),)
    _ligand_vertex_prototypes = (
        BiDentateLigandVertex(1, (2.5, 0.0, 0.0)),
        BiDentateLigandVertex(2, (-2.5, 0.0, 0.0)),
    )

    _edge_prototypes = (
        Edge(
            id=0,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[0],
            position=(0.1, 2.5, 0.0), 
        ),
        Edge(
            id=1,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[0],
            position=(0.1, -2.5, 0.0), 
        ),
        
        Edge(
            id=2,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[1],
            position=(-0.1, 2.5, 0.0), 
        ),
        Edge(
            id=3,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[1],
            position=(-0.1, -2.5, 0.0), 
        ),
    )