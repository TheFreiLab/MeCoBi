from __future__ import annotations
import stk
from .vertices import MetalVertex, BiDentateLigandVertex, RobustMonoDentateLigandVertex

class Octahedral_2bi_2mono(stk.metal_complex.Octahedral):

    _metal_vertex_prototypes = (MetalVertex(0, (0.0, 0.0, 0.0)),)

    _ligand_vertex_prototypes = (
        BiDentateLigandVertex(1, (2.5, 0.0, 0.0)),   
        BiDentateLigandVertex(2, (-2.5, 0.0, 0.0)),  
        
        RobustMonoDentateLigandVertex(3, (0.0, 0.0, 2.5)),  
        RobustMonoDentateLigandVertex(4, (0.0, 0.0, -2.5)), 
    )

    _edge_prototypes = (
        stk.Edge(0, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, 2.5, 0.0)),
        stk.Edge(1, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, -2.5, 0.0)),

        stk.Edge(2, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=(0.0, 2.5, 0.0)),
        stk.Edge(3, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=(0.0, -2.5, 0.0)),

        stk.Edge(4, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[2], position=(0.0, 0.0, 2.5)),

        stk.Edge(5, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[3], position=(0.0, 0.0, -2.5)),
    )