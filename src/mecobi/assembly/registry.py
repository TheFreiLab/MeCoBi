"""Topology registry: (geometry, denticity partition) -> custom stk topology graph.

The custom graphs own the geometry/isomer chemistry; this registry
just routes a perceived complex to the right one. A partition is the tuple of
ligand denticities sorted high-to-low (e.g. two bidentate + two monodentate ->
(2, 2, 1, 1)). Each topology's ligand vertices are grouped high-denticity-first,
so ``vertex_denticities`` doubles as the vertex-id -> denticity map.

If a (geometry, partition) pair is not registered -> hard error (invariant 3),
never a silent nearest-fit.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..model import Geometry
from .topologies.linear_2mono import Linear_2mono
from .topologies.metallocene import BentMetallocene, Metallocene
from .topologies.octa_1bi4mono import OctahedralOneBidentate
from .topologies.octa_1tetra_1bi import OctahedralTetraDentateBidentate
from .topologies.octa_1tetra_2mono import OctahedralTetraDentate2Mono
from .topologies.octa_2bi_2mono_cis import Octahedral_2bi_2mono
from .topologies.octa_2tri import OctahedralBisTriDentate
from .topologies.octa_3bi import IridiumTris
from .topologies.octa_6mono import Octahedral_6mono
from .topologies.piano_stool import PianoStoolChelateMono, PianoStool3Mono
from .topologies.square_1tri_1mono import SquarePlanarTriDentateMono
from .topologies.squareplanar_1bi_2mono import SquarePlanar_1bi_2mono
from .topologies.squareplanar_2bi import SquarePlanar_2bi
from .topologies.squareplanar_4mono import SquarePlanar_4mono
from .topologies.squareplanar_tetra import SquarePlanarTetraDentate


@dataclass(frozen=True)
class TopologyEntry:
    topology_class: type
    vertex_denticities: tuple[int, ...]  # denticity of each ligand vertex, in vertex-id order
    label: str                           # class name used in output filenames

    @property
    def n_sites(self) -> int:
        """Coordination number = number of metal binding sites."""
        return sum(self.vertex_denticities)


def _entry(cls, vertex_denticities, label) -> TopologyEntry:
    return TopologyEntry(cls, tuple(vertex_denticities), label)


# (geometry, partition-high-to-low) -> topology entry.
REGISTRY: dict[tuple[Geometry, tuple[int, ...]], TopologyEntry] = {
    (Geometry.LINEAR, (1, 1)): _entry(Linear_2mono, (1, 1), "linear_2mono"),

    (Geometry.SQUARE_PLANAR, (1, 1, 1, 1)): _entry(SquarePlanar_4mono, (1, 1, 1, 1), "square_4mono"),
    (Geometry.SQUARE_PLANAR, (2, 2)): _entry(SquarePlanar_2bi, (2, 2), "square_2bi"),
    (Geometry.SQUARE_PLANAR, (2, 1, 1)): _entry(SquarePlanar_1bi_2mono, (2, 1, 1), "square_1bi2mono"),
    (Geometry.SQUARE_PLANAR, (3, 1)): _entry(SquarePlanarTriDentateMono, (3, 1), "square_1tri1mono"),
    # General planar tetradentate (salen/cyclam/porphyrin), via our own vertex
    # rather than stk's porphyrin-specific one.
    (Geometry.SQUARE_PLANAR, (4,)): _entry(SquarePlanarTetraDentate, (4,), "square_1tetra"),

    (Geometry.OCTAHEDRAL, (1, 1, 1, 1, 1, 1)): _entry(Octahedral_6mono, (1,) * 6, "octa_6mono"),
    (Geometry.OCTAHEDRAL, (2, 1, 1, 1, 1)): _entry(OctahedralOneBidentate, (2, 1, 1, 1, 1), "octa_1bi4mono"),
    (Geometry.OCTAHEDRAL, (2, 2, 1, 1)): _entry(Octahedral_2bi_2mono, (2, 2, 1, 1), "octa_2bi2mono"),
    (Geometry.OCTAHEDRAL, (2, 2, 2)): _entry(IridiumTris, (2, 2, 2), "octa_3bi"),
    (Geometry.OCTAHEDRAL, (3, 3)): _entry(OctahedralBisTriDentate, (3, 3), "octa_2tri"),
    (Geometry.OCTAHEDRAL, (4, 1, 1)): _entry(OctahedralTetraDentate2Mono, (4, 1, 1), "octa_1tetra_2mono"),
    (Geometry.OCTAHEDRAL, (4, 2)): _entry(OctahedralTetraDentateBidentate, (4, 2), "octa_1tetra_1bi"),

    # Piano-stool / half-sandwich: an eta-bound cap (Cp*/arene, denticity 3) caps one face.
    (Geometry.OCTAHEDRAL, (3, 2, 1)): _entry(
        PianoStoolChelateMono, (3, 2, 1), "pianostool_bi_mono"),
    (Geometry.OCTAHEDRAL, (3, 1, 1, 1)): _entry(
        PianoStool3Mono, (3, 1, 1, 1), "pianostool_3mono"),

    # Metallocenes: two eta-caps sandwiching the metal (routed by geometry, not CN).
    (Geometry.METALLOCENE, (3, 3)): _entry(Metallocene, (3, 3), "metallocene"),
    (Geometry.METALLOCENE_BENT, (3, 3, 1, 1)): _entry(
        BentMetallocene, (3, 3, 1, 1), "metallocene_bent"),
}


def vertex_positions(entry: TopologyEntry) -> list:
    """Idealised positions of the ligand vertices, in vertex-id (0-based) order.

    Used to derive the vertex symmetry group for geometric-isomer enumeration.
    """
    import numpy as np

    protos = entry.topology_class._ligand_vertex_prototypes
    return [np.asarray(v.get_position(), dtype=float) for v in protos]


def vertex_sites(entry: TopologyEntry) -> list[list]:
    """Donor-site positions of each ligand vertex, in vertex-id (0-based) order.

    A vertex's sites are the positions of its metal-ligand edges in the topology
    graph — one per donor, so a bidentate vertex has two. Together with
    :func:`vertex_positions` this lets the 3D scene draw every coordination site
    rather than one blob per ligand.
    """
    import numpy as np

    protos = entry.topology_class._ligand_vertex_prototypes
    index_of = {v.get_id(): i for i, v in enumerate(protos)}
    sites: list[list] = [[] for _ in protos]
    for edge in entry.topology_class._edge_prototypes:
        for vid in (edge.get_vertex1_id(), edge.get_vertex2_id()):
            if vid in index_of:
                sites[index_of[vid]].append(np.asarray(edge.get_position(), dtype=float))
    return sites


def partition(denticities) -> tuple[int, ...]:
    """Denticities as a high-to-low tuple, e.g. [1, 2, 1] -> (2, 1, 1)."""
    return tuple(sorted(denticities, reverse=True))


def lookup(geometry: Geometry, denticities) -> TopologyEntry:
    """Return the topology entry for a geometry + ligand denticities.

    Raises:
        KeyError: if the (geometry, partition) pair has no registered topology.
    """
    return REGISTRY[(geometry, partition(denticities))]
