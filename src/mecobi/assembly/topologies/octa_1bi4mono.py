from stk._internal.topology_graphs.edge import Edge

from .metal_complex import MetalComplex
from .vertices import MetalVertex, MonoDentateLigandVertex, StableBiDentateLigandVertex

class OctahedralOneBidentate(MetalComplex):

    _metal_vertex_prototypes = (MetalVertex(0, (0, 0, 0)),)
    _ligand_vertex_prototypes = (
        StableBiDentateLigandVertex(1, (2.0, 2.0, 0)),
        MonoDentateLigandVertex(2, (-3.0, 0, 0)),
        MonoDentateLigandVertex(3, (0, -3.0, 0)),
        MonoDentateLigandVertex(4, (0, 0.0, -3.0)),
        MonoDentateLigandVertex(5, (0, 0, 2.0)),
    )

    _edge_prototypes = (
        Edge(
            id=0,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[0],
            position=(3.0, 0, 0),
        ),
        Edge(
            id=1,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[0],
            position=(0, 3.0, 0),
        ),
        Edge(
            id=2,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[1],
            position=(0, 0, 2.0),
        ),
        Edge(
            id=3,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[2],
            position=(-2.0, 0, 0),
        ),
        Edge(
            id=4,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[3],
            position=(0, -2.0, 0),
        ),
        Edge(
            id=5,
            vertex1=_metal_vertex_prototypes[0],
            vertex2=_ligand_vertex_prototypes[4],
            position=(0, 0, -2.0),
        ),
    )