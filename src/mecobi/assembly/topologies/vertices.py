"""
Metal Complex Vertices
======================

"""

import numpy as np
from stk._internal.topology_graphs.vertex import Vertex

# euclidean / get_projection are defined further down (the local get_projection also
# handles a zero-length target); the scipy / stk imports they used to shadow were dead.


def _rotate_between_vectors(building_block, start, target, origin):
    """``with_rotation_between_vectors`` that no-ops on a degenerate vector.

    stk normalises both vectors; a near-zero one (e.g. the perpendicular
    component vanishes when a chelate's donor axis is parallel to its
    core->placer axis, or an edge pair coincides) yields NaN and crashes the
    rotation-matrix SVD. When that happens the earlier alignment is already
    adequate, so we skip the extra rotation rather than fail the whole build.
    """
    if np.linalg.norm(start) < 1e-6 or np.linalg.norm(target) < 1e-6:
        return building_block
    return building_block.with_rotation_between_vectors(
        start=start, target=target, origin=origin,
    )


class UnaligningVertex(Vertex):
    """
    A vertex which does no rotations.

    """

    def place_building_block(self, building_block, edges):
        return building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        ).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        return {fg_id: edge.get_id() for fg_id, edge in enumerate(edges)}


class MetalVertex(UnaligningVertex):
    """
    Places the metal in a :class:`.MetalComplex`.

    """

    pass

class MonoDentateLigandVertex(Vertex):
    """
    Places monodentate ligand in a :class:`.MetalComplex`.

    """

    def place_building_block(self, building_block, edges):
        building_block = building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        )
        assert building_block.get_num_functional_groups() == 1, (
            f"{building_block} needs to have exactly 1 functional "
            "group but has "
            f"{building_block.get_num_functional_groups()}."
        )
        (fg,) = building_block.get_functional_groups(0)
        fg_centroid = building_block.get_centroid(
            atom_ids=fg.get_placer_ids(),
        )
        core_centroid = building_block.get_centroid(
            atom_ids=building_block.get_core_atom_ids(),
        )
        edge_centroid = sum(edge.get_position() for edge in edges) / len(edges)
        return _rotate_between_vectors(building_block,
            start=fg_centroid - core_centroid,
            target=edge_centroid - self._position,
            origin=self._position,
        ).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        return {0: edges[0].get_id()}

class RobustMonoDentateLigandVertex(Vertex):    # Custom GCR 
    """
    Vertex for single-atom monodentate ligands (e.g., Cl⁻).
    Does not attempt to calculate rotations — only translates the atom to the edge position.
    """
    def place_building_block(self, building_block, edges):
        num_atoms = building_block.get_num_atoms()

        if num_atoms == 1:
            # --- Robust Logic (Translation Only) ---
            edge_pos = edges[0].get_position()
            # Fixed the parenthesis here:
            return building_block.with_centroid(
                position=edge_pos,
                atom_ids=building_block.get_placer_ids(),
            ).get_position_matrix()
        
        else:
            # --- Standard Logic (Translation + Rotation) ---
            # Orient a polyatomic monodentate so its donor faces the metal and its
            # body points radially OUTWARD; otherwise the ligand keeps RDKit's
            # arbitrary embedded orientation and can fold back onto the metal.
            building_block = building_block.with_centroid(
                position=self._position,
                atom_ids=building_block.get_placer_ids(),
            )

            (fg,) = building_block.get_functional_groups(0)
            placer_ids = list(fg.get_placer_ids())
            edge_centroid = sum(edge.get_position() for edge in edges) / len(edges)

            if len(placer_ids) == 2:
                # η²-π-site (alkene/alkyne): the FG's two bonder carbons ARE the
                # coordinating unit and the ligand body extends on BOTH sides of the
                # π-bond (an internal alkyne, e.g. phenylpropyne). The σ "point the
                # body radially outward" logic below is ill-defined here — the FG
                # centroid sits mid-ligand — and in a crowded sphere it tips a
                # non-donor backbone atom into the metal (DILZED: a C jammed to 1.2 Å,
                # xtb then crashes and the build falls back to the clashing pose).
                # Seat it side-on instead: rotate the C=C / C≡C bond axis into the
                # tangent plane (perpendicular to the metal→site radial) so the
                # substituents splay sideways and nothing points inward. xtb then
                # relaxes the symmetric η² from a clash-free start.
                outward = np.asarray(self._position, dtype=float) - edge_centroid
                if np.linalg.norm(outward) < 1e-3:
                    # site model: edge sits on the vertex; metal is at the origin, so
                    # self._position is the outward radial.
                    outward = np.asarray(self._position, dtype=float)
                on = np.linalg.norm(outward)
                P = building_block.get_position_matrix()
                axis = P[placer_ids[1]] - P[placer_ids[0]]
                an = np.linalg.norm(axis)
                if an > 1e-6 and on > 1e-6:
                    r_hat = outward / on
                    axis = axis / an
                    tangent = axis - np.dot(axis, r_hat) * r_hat
                    tn = np.linalg.norm(tangent)
                    if tn > 1e-3:
                        building_block = _rotate_between_vectors(
                            building_block, start=axis, target=tangent / tn,
                            origin=self._position,
                        )
                return building_block.get_position_matrix()

            fg_centroid = building_block.get_centroid(
                atom_ids=placer_ids,
            )
            core_centroid = building_block.get_centroid(
                atom_ids=building_block.get_core_atom_ids(),
            )

            to_metal = edge_centroid - self._position
            if np.linalg.norm(to_metal) < 1e-3:
                # Site model: the edge sits ON the vertex, so edge_centroid gives no
                # direction. The metal is at the origin of every MetalComplex
                # topology here, so self._position IS the metal->site (outward) axis;
                # align the donor->body vector with it to push the body outward.
                return _rotate_between_vectors(building_block,
                    start=core_centroid - fg_centroid,
                    target=self._position,
                    origin=self._position,
                ).get_position_matrix()

            return _rotate_between_vectors(building_block,
                start=fg_centroid - core_centroid,
                target=to_metal,
                origin=self._position,
            ).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        return {0: edges[0].get_id()}
    
class BiDentateLigandVertex(Vertex):
    """
    Places bidentate ligand in a :class:`.MetalComplex`.

    """

    def place_building_block(self, building_block, edges):
        building_block = building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        )
        assert building_block.get_num_functional_groups() == 2, (
            f"{building_block} needs to have exactly 2 functional "
            "groups but has "
            f"{building_block.get_num_functional_groups()}."
        )

        fg0_position, fg1_position = (
            building_block.get_centroid(fg.get_placer_ids())
            for fg in building_block.get_functional_groups()
        )
        edge_position1, edge_position2 = (
            edge.get_position() for edge in edges
        )
        building_block = _rotate_between_vectors(building_block,
            start=fg1_position - fg0_position,
            target=edge_position2 - edge_position1,
            origin=building_block.get_centroid(),
        )

        placer_centroid = building_block.get_centroid(
            atom_ids=building_block.get_placer_ids(),
        )
        core_centroid = building_block.get_centroid(
            atom_ids=building_block.get_core_atom_ids(),
        )
        core_to_placer = placer_centroid - core_centroid

        fg0_position, fg1_position = (
            building_block.get_centroid(fg.get_placer_ids())
            for fg in building_block.get_functional_groups()
        )
        fg_vector = fg1_position - fg0_position

        fg_vector_projection = get_projection(
            start=core_to_placer,
            target=fg_vector,
        )

        edge_centroid = sum(edge.get_position() for edge in edges) / len(edges)
        building_block = _rotate_between_vectors(building_block,
            start=core_to_placer - fg_vector_projection,
            target=edge_centroid - self._position,
            origin=building_block.get_centroid(),
        )

        return building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        ).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        (fg,) = building_block.get_functional_groups(0)
        fg_position = building_block.get_centroid(fg.get_placer_ids())

        def fg_distance(edge):
            return euclidean(edge.get_position(), fg_position)

        edges = sorted(edges, key=fg_distance)
        return {fg_id: edge.get_id() for fg_id, edge in enumerate(edges)}
    
def unit_vector(v):
    return v / np.linalg.norm(v)

def euclidean(v1, v2):
    return np.linalg.norm(v1 - v2)

def get_projection(start, target):
    """Projects the start vector onto the target vector."""
    target_norm = np.linalg.norm(target)
    if target_norm == 0:
        return np.zeros_like(start)
    return np.dot(start, target) / target_norm**2 * target

class ChelateVertex(Vertex):    # Custom
    """
    Bidentate placement that puts the two donors ON their coordination sites.

    ``BiDentateLigandVertex`` centres the donor pair on the vertex position
    (radius 2.5), which overshoots the cis-pair midpoint (2.5/sqrt(2)); MCHammer
    usually recovers, but bulky/asymmetric chelates (Schiff bases) stall against
    ring clashes and xtb then dissociates them. Here the donor centroid is
    translated to the midpoint of the vertex's two metal-ligand edges, so each
    donor starts straddling its ideal site for ANY bite distance — diimine,
    acac, Schiff base alike. Orientation logic is identical to
    ``BiDentateLigandVertex``; only the final translation differs.
    """

    def place_building_block(self, building_block, edges):
        building_block = building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        )
        assert building_block.get_num_functional_groups() == 2, (
            f"{building_block} needs to have exactly 2 functional "
            "groups but has "
            f"{building_block.get_num_functional_groups()}."
        )

        fg0_position, fg1_position = (
            building_block.get_centroid(fg.get_placer_ids())
            for fg in building_block.get_functional_groups()
        )
        edge_position1, edge_position2 = (
            edge.get_position() for edge in edges
        )
        building_block = _rotate_between_vectors(building_block,
            start=fg1_position - fg0_position,
            target=edge_position2 - edge_position1,
            origin=building_block.get_centroid(),
        )

        # Orient the ligand body away from the metal (at the origin) by scanning the rotation
        # about the donor-donor axis -- which keeps BOTH donors on their sites -- for the angle
        # that pushes the bulk furthest off the centre. This replaces the core->placer heuristic,
        # which DEGENERATES for a bulky symmetric bidentate whose core and donor centroids coincide
        # (DIBWAM's PPh2-anhydride-PPh2, six phenyls surrounding the two P): there the perpendicular
        # component vanished, the orientation rotation was skipped, and the phenyls folded onto the
        # metal. Pure geometry -- ~36 rotations x the atom count, negligible next to xtb.
        fg0_position, fg1_position = (
            building_block.get_centroid(fg.get_placer_ids())
            for fg in building_block.get_functional_groups()
        )
        edge_centroid = (edge_position1 + edge_position2) / 2
        axis = fg1_position - fg0_position
        axis_norm = np.linalg.norm(axis)
        if axis_norm < 1e-6:  # coincident donors -> no axis to orient about, keep the alignment
            return building_block.with_centroid(
                position=edge_centroid,
                atom_ids=building_block.get_placer_ids(),
            ).get_position_matrix()
        axis = axis / axis_norm
        placer_centroid = building_block.get_centroid(building_block.get_placer_ids())
        shift = edge_centroid - placer_centroid  # seats the donor midpoint at the site midpoint
        core = set(building_block.get_core_atom_ids())
        body = [a.get_id() for a in building_block.get_atoms()
                if a.get_id() in core and a.get_atomic_number() > 1] or list(core)
        best_bb, best_pen = building_block, None
        for k in range(36):  # 10-degree steps about the donor axis
            cand = building_block.with_rotation_about_axis(
                k * np.pi / 18.0, axis, placer_centroid)
            pos = cand.get_position_matrix() + shift  # metal at origin; donors at edge_centroid
            pen = sum(1.0 / max(float(np.linalg.norm(pos[i])), 0.5) for i in body)  # 1/r bulk-on-metal
            if best_pen is None or pen < best_pen:
                best_pen, best_bb = pen, cand

        return best_bb.with_centroid(
            position=edge_centroid,
            atom_ids=best_bb.get_placer_ids(),
        ).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        (fg,) = building_block.get_functional_groups(0)
        fg_position = building_block.get_centroid(fg.get_placer_ids())

        def fg_distance(edge):
            return euclidean(edge.get_position(), fg_position)

        edges = sorted(edges, key=fg_distance)
        return {fg_id: edge.get_id() for fg_id, edge in enumerate(edges)}


class TriDentateLigandVertex(Vertex):   # Custom GCR
    """
    Places tridentate ligand in a :class:`.MetalComplex`.
    """

    def place_building_block(self, building_block, edges):
        building_block = building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        )
        assert building_block.get_num_functional_groups() == 3, (
            f"{building_block} needs to have exactly 3 functional "
            f"groups but has {building_block.get_num_functional_groups()}."
        )

        # Get functional group centroids
        fg_positions = [
            building_block.get_centroid(fg.get_placer_ids())
            for fg in building_block.get_functional_groups()
        ]

        # Get edge positions
        edge_positions = [edge.get_position() for edge in edges]

        # Align vector between FG0 and FG1 to vector between Edge0 and Edge1
        building_block = _rotate_between_vectors(building_block,
            start=fg_positions[1] - fg_positions[0],
            target=edge_positions[1] - edge_positions[0],
            origin=building_block.get_centroid(),
        )

        # Align vector from core to placer to centroid of edges
        placer_centroid = building_block.get_centroid(
            atom_ids=building_block.get_placer_ids(),
        )
        core_centroid = building_block.get_centroid(
            atom_ids=building_block.get_core_atom_ids(),
        )
        core_to_placer = placer_centroid - core_centroid

        fg_vector = fg_positions[2] - fg_positions[0]
        fg_vector_projection = get_projection(
            start=core_to_placer,
            target=fg_vector,
        )

        edge_centroid = sum(edge_positions) / len(edge_positions)
        building_block = _rotate_between_vectors(building_block,
            start=core_to_placer - fg_vector_projection,
            target=edge_centroid - self._position,
            origin=building_block.get_centroid(),
        )

        return building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        ).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        # Match each FG to its closest edge
        fg_positions = [
            building_block.get_centroid(fg.get_placer_ids())
            for fg in building_block.get_functional_groups()
        ]

        def fg_distance(fg_pos, edge):
            return euclidean(edge.get_position(), fg_pos)

        edge_ids = [edge.get_id() for edge in edges]

        # Sort edges by proximity to each FG
        mapping = {}
        used_edges = set()
        for fg_id, fg_pos in enumerate(fg_positions):
            distances = [
                (eid, fg_distance(fg_pos, edge))
                for eid, edge in zip(edge_ids, edges)
                if eid not in used_edges
            ]
            closest = min(distances, key=lambda x: x[1])[0]
            mapping[fg_id] = closest
            used_edges.add(closest)

        return mapping

class PlanarTriDentateLigandVertex(Vertex):     # Custom GCR
    """
    Vertex for planar tridentate ligands (e.g., arene).
    Ensures that the plane defined by the 3 functional groups
    is parallel to the plane defined by the 3 edges.
    """

    def place_building_block(self, building_block, edges):
        assert building_block.get_num_functional_groups() == 3, (
            f"{building_block} must have exactly 3 functional groups, "
            f"but has {building_block.get_num_functional_groups()}."
        )

        # Center on the vertex
        building_block = building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        )

        # Functional group and edge positions
        fg_positions = [
            building_block.get_centroid(fg.get_placer_ids())
            for fg in building_block.get_functional_groups()
        ]
        edge_positions = [edge.get_position() for edge in edges]

        # Align FG0–FG1 vector with Edge0–Edge1 vector
        building_block = _rotate_between_vectors(building_block,
            start=fg_positions[1] - fg_positions[0],
            target=edge_positions[1] - edge_positions[0],
            origin=building_block.get_centroid(),
        )

        # Recalculate positions after rotation
        fg_positions = [
            building_block.get_centroid(fg.get_placer_ids())
            for fg in building_block.get_functional_groups()
        ]

        # Plane normals (FGs and edges)
        fg_normal = np.cross(
            fg_positions[1] - fg_positions[0],
            fg_positions[2] - fg_positions[0],
        )
        edge_normal = np.cross(
            edge_positions[1] - edge_positions[0],
            edge_positions[2] - edge_positions[0],
        )

        # Align ligand plane normal with edge plane normal
        building_block = _rotate_between_vectors(building_block,
            start=fg_normal,
            target=edge_normal,
            origin=building_block.get_centroid(),
        )

        # Recenter on the vertex
        return building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        ).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        # Map each FG to its closest edge
        fg_positions = [
            building_block.get_centroid(fg.get_placer_ids())
            for fg in building_block.get_functional_groups()
        ]

        mapping = {}
        used_edges = set()
        for fg_id, fg_pos in enumerate(fg_positions):
            distances = [
                (edge.get_id(), euclidean(edge.get_position(), fg_pos))
                for edge in edges if edge.get_id() not in used_edges
            ]
            closest = min(distances, key=lambda x: x[1])[0]
            mapping[fg_id] = closest
            used_edges.add(closest)

        return mapping


class MeridionalTriDentateLigandVertex(Vertex):     # Custom GCR
    """Meridional (pincer) tridentate: seats the CENTRAL donor on the central edge and the
    two ENDS on the trans edges, identifying the central donor GEOMETRICALLY (the one whose
    two neighbours flank it — the widest internal angle) rather than by functional-group
    order. :class:`TriDentateLigandVertex` / :class:`PlanarTriDentateLigandVertex` assume the
    middle FG is central, which is wrong for a PNP/NNN pincer whose central donor is not the
    middle atom in index order (a pyridine-N pincer whose N is last): they seat the central
    donor on an END site, so the leaving group no longer lands trans to it and the pincer
    tilts. This vertex is order-independent and keeps the donor plane parallel to the edge
    plane so the pincer stays flat."""

    @staticmethod
    def _central(points) -> int:
        """Index of the meridional-triple's central point: widest internal angle."""
        widest, idx = -2.0, 0
        for i in range(3):
            j, k = (x for x in range(3) if x != i)
            v1, v2 = points[j] - points[i], points[k] - points[i]
            cos = float(v1 @ v2 / ((np.linalg.norm(v1) * np.linalg.norm(v2)) or 1.0))
            if -cos > widest:
                widest, idx = -cos, i
        return idx

    def place_building_block(self, building_block, edges):
        building_block = building_block.with_centroid(
            position=self._position, atom_ids=building_block.get_placer_ids())
        assert building_block.get_num_functional_groups() == 3, (
            f"{building_block} must have exactly 3 functional groups, "
            f"but has {building_block.get_num_functional_groups()}."
        )
        fg = [building_block.get_centroid(f.get_placer_ids())
              for f in building_block.get_functional_groups()]
        ep = [edge.get_position() for edge in edges]
        cf = self._central(fg); ef = [x for x in range(3) if x != cf]
        ce = self._central(ep); ee = [x for x in range(3) if x != ce]
        # Align the donors' (end0 -> central) axis to the edges' (end0 -> central) axis.
        building_block = _rotate_between_vectors(building_block,
            start=fg[cf] - fg[ef[0]], target=ep[ce] - ep[ee[0]],
            origin=building_block.get_centroid())
        fg = [building_block.get_centroid(f.get_placer_ids())
              for f in building_block.get_functional_groups()]
        # Flatten: donor plane parallel to the edge plane.
        fg_normal = np.cross(fg[cf] - fg[ef[0]], fg[ef[1]] - fg[ef[0]])
        edge_normal = np.cross(ep[ce] - ep[ee[0]], ep[ee[1]] - ep[ee[0]])
        building_block = _rotate_between_vectors(building_block,
            start=fg_normal, target=edge_normal, origin=building_block.get_centroid())
        return building_block.with_centroid(
            position=self._position, atom_ids=building_block.get_placer_ids(),
        ).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        fg_positions = [building_block.get_centroid(fg.get_placer_ids())
                        for fg in building_block.get_functional_groups()]
        mapping, used = {}, set()
        for fg_id, fg_pos in enumerate(fg_positions):
            closest = min(
                ((edge.get_id(), euclidean(edge.get_position(), fg_pos))
                 for edge in edges if edge.get_id() not in used),
                key=lambda x: x[1],
            )[0]
            mapping[fg_id] = closest
            used.add(closest)
        return mapping


class PlanarTetraDentateLigandVertex(Vertex):
    """Vertex for a planar tetradentate ligand (salen, porphyrin, cyclam-in-plane).

    Places the four donors in one plane, parallel to the plane of its four
    coordination edges — the same plane-alignment strategy as
    :class:`PlanarTriDentateLigandVertex`, extended to four functional groups.
    Used for the equatorial belt of an octahedral (4,1,1)/(4,2) complex.
    """

    def place_building_block(self, building_block, edges):
        assert building_block.get_num_functional_groups() == 4, (
            f"{building_block} must have exactly 4 functional groups, "
            f"but has {building_block.get_num_functional_groups()}."
        )
        building_block = building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        )
        fg_positions = [
            building_block.get_centroid(fg.get_placer_ids())
            for fg in building_block.get_functional_groups()
        ]
        edge_positions = [edge.get_position() for edge in edges]

        # align first donor axis, then the ligand plane normal to the edge plane
        building_block = _rotate_between_vectors(building_block,
            start=fg_positions[1] - fg_positions[0],
            target=edge_positions[1] - edge_positions[0],
            origin=building_block.get_centroid(),
        )
        fg_positions = [
            building_block.get_centroid(fg.get_placer_ids())
            for fg in building_block.get_functional_groups()
        ]
        fg_normal = np.cross(fg_positions[1] - fg_positions[0], fg_positions[2] - fg_positions[0])
        edge_normal = np.cross(
            edge_positions[1] - edge_positions[0], edge_positions[2] - edge_positions[0]
        )
        building_block = _rotate_between_vectors(building_block,
            start=fg_normal, target=edge_normal, origin=building_block.get_centroid(),
        )
        return building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        ).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        fg_positions = [
            building_block.get_centroid(fg.get_placer_ids())
            for fg in building_block.get_functional_groups()
        ]
        mapping = {}
        used = set()
        for fg_id, fg_pos in enumerate(fg_positions):
            dists = [
                (edge.get_id(), euclidean(edge.get_position(), fg_pos))
                for edge in edges if edge.get_id() not in used
            ]
            closest = min(dists, key=lambda x: x[1])[0]
            mapping[fg_id] = closest
            used.add(closest)
        return mapping


class PolyDentateLigandVertex(Vertex):
    """Generic vertex for a high-denticity ligand (>=3 donors).

    Aligns the first donor axis and the donor plane to the coordination edges (the
    same strategy as the planar tri/tetradentate vertices) but works for any donor
    count, so it covers the macrocyclic / polydentate ligands of CN 7 and CN 9.
    The placement is approximate; xtb relaxation refines it.
    """

    def place_building_block(self, building_block, edges):
        n = building_block.get_num_functional_groups()
        assert n >= 3, f"{building_block} needs >=3 functional groups, has {n}."
        building_block = building_block.with_centroid(
            position=self._position, atom_ids=building_block.get_placer_ids(),
        )
        fg_pos = [building_block.get_centroid(fg.get_placer_ids())
                  for fg in building_block.get_functional_groups()]
        edge_pos = [edge.get_position() for edge in edges]
        building_block = _rotate_between_vectors(building_block,
            start=fg_pos[1] - fg_pos[0], target=edge_pos[1] - edge_pos[0],
            origin=building_block.get_centroid(),
        )
        fg_pos = [building_block.get_centroid(fg.get_placer_ids())
                  for fg in building_block.get_functional_groups()]
        fg_normal = np.cross(fg_pos[1] - fg_pos[0], fg_pos[2] - fg_pos[0])
        edge_normal = np.cross(edge_pos[1] - edge_pos[0], edge_pos[2] - edge_pos[0])
        building_block = _rotate_between_vectors(building_block,
            start=fg_normal, target=edge_normal, origin=building_block.get_centroid(),
        )
        return building_block.with_centroid(
            position=self._position, atom_ids=building_block.get_placer_ids(),
        ).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        fg_pos = [building_block.get_centroid(fg.get_placer_ids())
                  for fg in building_block.get_functional_groups()]
        mapping = {}
        used = set()
        for fg_id, p in enumerate(fg_pos):
            dists = [(e.get_id(), euclidean(e.get_position(), p))
                     for e in edges if e.get_id() not in used]
            closest = min(dists, key=lambda x: x[1])[0]
            mapping[fg_id] = closest
            used.add(closest)
        return mapping


class StableBiDentateLigandVertex(Vertex):      # Custom GCR, good for Schiff Bases
    def place_building_block(self, building_block, edges):
        building_block = building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        )

        fgs = list(building_block.get_functional_groups())
        
        # Passo 1: Alinhamento básico do eixo N-N
        fg0_pos = building_block.get_centroid(fgs[0].get_placer_ids())
        fg1_pos = building_block.get_centroid(fgs[1].get_placer_ids())
        edge_pos = [edge.get_position() for edge in edges]
        
        building_block = _rotate_between_vectors(building_block,
            start=fg1_pos - fg0_pos,
            target=edge_pos[1] - edge_pos[0],
            origin=building_block.get_centroid(),
        )

        # Passo 2: Localizar Carbonos da Base de Schiff (C=N)
        pos_matrix = building_block.get_position_matrix()
        
        # Pegamos os IDs dos Nitrogênios (placers)
        n1_idx = next(fgs[0].get_placer_ids())
        n2_idx = next(fgs[1].get_placer_ids())
        
        n1_pos = pos_matrix[n1_idx]
        n2_pos = pos_matrix[n2_idx]

        c1_idx, c2_idx = None, None
        min_dist1, min_dist2 = float('inf'), float('inf')

        for atom in building_block.get_atoms():
            # Tenta get_id(), se falhar usa .id (depende da subversão do stk)
            try:
                a_idx = atom.get_id()
            except AttributeError:
                a_idx = atom.id
                
            if a_idx in (n1_idx, n2_idx):
                continue

            # Tenta get_atomic_number(), se falhar usa .atomic_number
            try:
                a_num = atom.get_atomic_number()
            except AttributeError:
                a_num = atom.atomic_number

            if a_num != 6: # Carbono
                continue

            dist1 = np.linalg.norm(pos_matrix[a_idx] - n1_pos)
            if dist1 < min_dist1:
                min_dist1, c1_idx = dist1, a_idx
            
            dist2 = np.linalg.norm(pos_matrix[a_idx] - n2_pos)
            if dist2 < min_dist2:
                min_dist2, c2_idx = dist2, a_idx

        # Passo 3: Alinhamento de Plano (Normal do Plano C-N-N-C)
        if c1_idx is not None and c2_idx is not None:
            # Recalcular vetores com posições atuais
            pos_matrix = building_block.get_position_matrix()
            v_nn = pos_matrix[n2_idx] - pos_matrix[n1_idx]
            v_nc = pos_matrix[c1_idx] - pos_matrix[n1_idx]
            
            current_normal = np.cross(v_nn, v_nc)
            
            if np.linalg.norm(current_normal) > 1e-6:
                current_normal /= np.linalg.norm(current_normal)
                
                # Definir normal alvo (Perpendicular ao metal e ao eixo das edges)
                edge_v = edge_pos[1] - edge_pos[0]
                edge_mid = (edge_pos[0] + edge_pos[1]) / 2
                target_dir = edge_mid - self._position # Vetor Metal -> Meio da Ligação
                
                target_normal = np.cross( target_dir, edge_v)
                target_normal /= np.linalg.norm(target_normal)

                building_block = _rotate_between_vectors(building_block,
                    start=current_normal,
                    target=target_normal,
                    origin=building_block.get_centroid(),
                )

        return building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        ).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        # Mapeamento simples por proximidade
        return {i: edge.get_id() for i, edge in enumerate(edges)}

class CapMultiVertex(Vertex):
    """A ligand carrying two or more centroid η-caps (an ansa-metallocene, a
    Cp+donor constrained-geometry ligand). Each functional group's centroid — a Cp/
    arene ring centroid, or a σ-donor — is placed ON its coordination site by a rigid
    (Kabsch) fit of all the FG centroids onto the site positions, so both rings seat
    at η-cap distance instead of being dragged onto the metal like a σ-chelate. The
    ligand conformer is pre-folded to a sandwich (see ``ligand_building_block``), so
    the ring planes already face along the ring-ring axis. Donor k binds site k
    (edge order), matching the site model."""

    def place_building_block(self, building_block, edges):
        bb = building_block
        pmat = bb.get_position_matrix()
        fgs = list(bb.get_functional_groups())
        if len(fgs) != len(edges):
            return bb.with_centroid(
                position=self._position, atom_ids=bb.get_placer_ids()
            ).get_position_matrix()
        src = np.array([pmat[list(fg.get_bonder_ids())].mean(axis=0) for fg in fgs])
        dst = np.array([np.asarray(edge.get_position(), dtype=float) for edge in edges])
        src_c, dst_c = src.mean(axis=0), dst.mean(axis=0)
        H = (src - src_c).T @ (dst - dst_c)
        U, _, Vt = np.linalg.svd(H)
        D = np.sign(np.linalg.det(Vt.T @ U.T))
        R = Vt.T @ np.diag([1.0, 1.0, D]) @ U.T
        newpos = (pmat - src_c) @ R + dst_c
        return bb.with_position_matrix(newpos).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        # Donor k -> edge k (site model creates edges in donor order).
        return {i: edge.get_id() for i, edge in enumerate(edges)}


class CentroidCapVertex(Vertex):     # Custom: eta-cap centroid site
    """An eta-cap (Cp/arene) as ONE functional group whose bonders are all the ring
    atoms. Centres the ring centroid on the vertex and orients the ring plane
    perpendicular to the cap->metal axis, so the metal sits on the ring axis (eta5/
    eta6). xtb relaxes the exact hapticity. Used for a denticity-1 centroid cap."""

    def place_building_block(self, building_block, edges):
        building_block = building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        )
        fg = next(iter(building_block.get_functional_groups()))
        ids = list(fg.get_bonder_ids())
        pmat = building_block.get_position_matrix()
        pts = pmat[ids]
        c = pts.mean(axis=0)
        _, _, vt = np.linalg.svd(pts - c)
        normal = vt[2]                                  # ring-plane normal
        axis = -np.asarray(self._position, dtype=float)  # cap centroid -> metal (origin)
        if np.linalg.norm(axis) < 1e-9:
            axis = np.array([0.0, 0.0, 1.0])
        building_block = _rotate_between_vectors(
            building_block, start=normal, target=axis,
            origin=building_block.get_centroid(),
        )
        return building_block.with_centroid(
            position=self._position,
            atom_ids=building_block.get_placer_ids(),
        ).get_position_matrix()

    def map_functional_groups_to_edges(self, building_block, edges):
        return {0: edges[0].get_id()}
