from __future__ import annotations
from stk._internal.topology_graphs.edge import Edge
from .metal_complex import MetalComplex
from .vertices import MetalVertex, RobustMonoDentateLigandVertex

class Octahedral_6mono(MetalComplex):
    _metal_vertex_prototypes = (MetalVertex(0, (0, 0, 0)),)

    _ligand_vertex_prototypes = (
        RobustMonoDentateLigandVertex(1, (2.5001, 0.0, 0.0)),   # X+
        RobustMonoDentateLigandVertex(2, (-2.5001, 0.0, 0.0)),  # X-
        RobustMonoDentateLigandVertex(3, (0.0, 2.5001, 0.0)),   # Y+
        RobustMonoDentateLigandVertex(4, (0.0, -2.5001, 0.0)),  # Y-
        RobustMonoDentateLigandVertex(5, (0.0, 0.0, 2.5001)),   # Z+
        RobustMonoDentateLigandVertex(6, (0.0, 0.0, -2.5001)),  # Z-
    )

    _edge_prototypes = (
        Edge(0, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0]),
        Edge(1, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1]),
        Edge(2, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[2]),
        Edge(3, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[3]),
        Edge(4, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[4]),
        Edge(5, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[5]),
    )