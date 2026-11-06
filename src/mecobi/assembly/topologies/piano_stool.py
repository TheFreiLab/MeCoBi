"""Half-sandwich / piano-stool topologies.

An eta-bound facial cap -- an arene (eta6) or, far more commonly, a Cp/Cp*
cyclopentadienyl (eta5) -- occupies one face of the octahedron (three fac sites,
hardcoded denticity 3 by perception) and the remaining "legs" occupy the
opposite face:

    cap face   {+x, +y, +z}
    leg face   {-x, -y, -z}

``PianoStoolChelateMono`` — (3, 2, 1): cap + a cis bidentate chelate (spanning
two leg sites) + one monodentate on the third leg. This is the classic
[Cp*Ir(N^N / N^O)Cl] / [(arene)Ru(N^O)Cl] organometallic-anticancer motif.

``PianoStool3Mono`` — (3, 1, 1, 1): cap + three monodentate legs.

The cap ring binds via a facial triad of ring carbons (assembly trims the ring
to three spread carbons, see ``assembly.build``); ``PlanarTriDentateLigandVertex``
keeps the ring plane parallel to the leg face. xtb then relaxes to true eta5/eta6.
"""

from __future__ import annotations

import stk

from .metal_complex import MetalComplex
from .vertices import (
    ChelateVertex,
    MetalVertex,
    PlanarTriDentateLigandVertex,
    RobustMonoDentateLigandVertex,
)

_R = 2.5
_F = _R / 3 ** 0.5  # 1.4434: arene centroid on the (1,1,1) face axis


class PianoStoolChelateMono(MetalComplex):
    """(3, 2, 1) piano stool: facial cap (Cp*/arene) + cis chelate + one monodentate leg."""

    _metal_vertex_prototypes = (MetalVertex(0, (0.0, 0.0, 0.0)),)
    _ligand_vertex_prototypes = (
        PlanarTriDentateLigandVertex(1, (_F, _F, _F)),        # arene face cap
        ChelateVertex(2, (-_R / 2 ** 0.5, -_R / 2 ** 0.5, 0.0)),  # bidentate legs
        RobustMonoDentateLigandVertex(3, (0.0, 0.0, -_R)),    # monodentate leg
    )
    _edge_prototypes = (
        stk.Edge(0, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(_R, 0.0, 0.0)),
        stk.Edge(1, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, _R, 0.0)),
        stk.Edge(2, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, 0.0, _R)),
        stk.Edge(3, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=(-_R, 0.0, 0.0)),
        stk.Edge(4, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=(0.0, -_R, 0.0)),
        stk.Edge(5, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[2], position=(0.0, 0.0, -_R)),
    )


class PianoStool3Mono(MetalComplex):
    """(3, 1, 1, 1) piano stool: facial cap (Cp*/arene) + three monodentate legs."""

    _metal_vertex_prototypes = (MetalVertex(0, (0.0, 0.0, 0.0)),)
    _ligand_vertex_prototypes = (
        PlanarTriDentateLigandVertex(1, (_F, _F, _F)),
        RobustMonoDentateLigandVertex(2, (-_R, 0.0, 0.0)),
        RobustMonoDentateLigandVertex(3, (0.0, -_R, 0.0)),
        RobustMonoDentateLigandVertex(4, (0.0, 0.0, -_R)),
    )
    _edge_prototypes = (
        stk.Edge(0, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(_R, 0.0, 0.0)),
        stk.Edge(1, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, _R, 0.0)),
        stk.Edge(2, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[0], position=(0.0, 0.0, _R)),
        stk.Edge(3, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[1], position=(-_R, 0.0, 0.0)),
        stk.Edge(4, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[2], position=(0.0, -_R, 0.0)),
        stk.Edge(5, _metal_vertex_prototypes[0], _ligand_vertex_prototypes[3], position=(0.0, 0.0, -_R)),
    )
