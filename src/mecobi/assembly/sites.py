"""Canonical coordination sites + dynamic topology graphs.

The fixed topology classes in :mod:`.topologies` encode ONE arrangement each
(e.g. ``octa_2bi_2mono`` places its monodentates trans), so they cannot express
user-chosen isomers — cis vs trans monodentates, Delta/Lambda chelate windings,
or which donor of an asymmetric chelate points where. This module numbers the
coordination sites of each geometry canonically and builds an stk topology graph
*from a site assignment*: ligand index -> ordered tuple of site ids, where donor
k of the ligand binds site k of the tuple. That ordering is what makes
asymmetric bidentates (N,O-chelates etc.) controllable.

Each geometry's site directions (and its site numbering, invariant 7 — shared
with the 3D scene and the future index mode) live in one module per geometry
under :mod:`.topologies.geometries`; ``SITE_VECTORS`` below is assembled from
them. e.g. linear = 0:+x 1:-x; square planar = 0:+x 1:+y 2:-x 3:-y; octahedral
= 0:+x 1:-x 2:+y 3:-y 4:+z 5:-z.
"""

from __future__ import annotations

import numpy as np
import stk

from ..model import Geometry
from .._text import plural
from .topologies.geometries import SITE_VECTORS
from .topologies.geometries import metallocene_bent as _bent
from .topologies.metal_complex import MetalComplex
from .topologies.vertices import (
    CapMultiVertex,
    CentroidCapVertex,
    ChelateVertex,
    MetalVertex,
    PlanarTriDentateLigandVertex,
    PolyDentateLigandVertex,
    RobustMonoDentateLigandVertex,
    TriDentateLigandVertex,
)

_R = 2.5  # site shell radius, matches the fixed topology classes

_VERTEX_FOR_DENTICITY = {
    1: RobustMonoDentateLigandVertex,
    2: ChelateVertex,  # donors land ON their sites — robust for any bidentate
    3: TriDentateLigandVertex,
}


def _vertex_class_for(d: int):
    """Vertex class for a ligand of denticity ``d`` (>=4 use the generic poly vertex)."""
    return _VERTEX_FOR_DENTICITY.get(d, PolyDentateLigandVertex)


class SiteAssignmentError(ValueError):
    """Raised when a site assignment is malformed or chemically impossible."""


def _unit_vectors(geometry: Geometry, n_sites: "int | None" = None) -> tuple:
    """Unit site directions for a geometry. The bent metallocene is generated for the
    requested site count (2 caps + ancillary); the rest come from the fixed tables."""
    if geometry == Geometry.METALLOCENE_BENT:
        if not n_sites:
            raise SiteAssignmentError("Bent metallocene needs a site count.")
        return _bent.vectors(n_sites)
    vecs = SITE_VECTORS.get(geometry)
    if not vecs:
        raise SiteAssignmentError(f"No site model for geometry {geometry.value!r}.")
    return vecs


def _n_sites(geometry: Geometry, denticities: "list[int] | None" = None) -> int:
    """Site count for a geometry — fixed for the tabulated ones, the denticity sum
    for the bent metallocene (which has as many sites as the complex has donors)."""
    if geometry == Geometry.METALLOCENE_BENT:
        return sum(denticities or ())
    return len(SITE_VECTORS.get(geometry, ()))


def site_positions(geometry: Geometry, n_sites: "int | None" = None) -> list[np.ndarray]:
    """Positions of the geometry's numbered sites (unit direction * shell radius)."""
    return [np.array(v, dtype=float) * _R for v in _unit_vectors(geometry, n_sites)]


def eta2_reference_site(geometry: Geometry, site: int,
                        n_sites: "int | None" = None) -> "int | None":
    """The site whose axis an eta2 (2-atom pi) ligand on ``site`` lays its C=C / C#C bond along.

    A side-on alkene/alkyne has one more degree of freedom than a sigma donor: the twist of its
    bond about the metal-midpoint axis. Left to the placement it came out arbitrary -- the same
    isomer built from two equivalent site numberings gave the bond "lying" in one and "standing"
    (90 deg off) in the other, and xtb does not cross between the two wells (DILZED). The rule
    ties the twist to the site numbering: the bond is parallel to the vector of the most
    PERPENDICULAR other site, lowest site number on a tie -- octahedral site 3 (-y) -> site 0 (+x).
    So an explicit site assignment (GUI "Assign", a benchmark site map) fixes the orientation, and
    equivalent numberings of one isomer express the different twists. None if there is no other
    site reasonably perpendicular (|cos| > 0.5)."""
    pos = site_positions(geometry, n_sites)
    if not 0 <= site < len(pos) or len(pos) < 2:
        return None
    v = pos[site] / (np.linalg.norm(pos[site]) or 1.0)
    best = None
    for j, w in enumerate(pos):
        if j == site:
            continue
        c = abs(float(v @ w) / (float(np.linalg.norm(w)) or 1.0))
        if best is None or c < best[0] - 1e-6:
            best = (c, j)
    return best[1] if best is not None and best[0] <= 0.5 else None


def eta2_axis(geometry: Geometry, site: int, n_sites: "int | None" = None) -> "np.ndarray | None":
    """Unit vector an eta2 ligand on ``site`` lays its C=C / C#C bond along: the reference site
    axis (:func:`eta2_reference_site`), except in a SQUARE-PLANAR sphere, where every other site
    lies in the coordination plane and the bond stands perpendicular to it (Zeise's salt, the d8
    preference). A trigonal-planar d10 alkene lies IN the plane, which the reference-site rule
    already gives. None when the geometry offers no reference."""
    ref = eta2_reference_site(geometry, site, n_sites)
    if ref is None:
        return None
    pos = site_positions(geometry, n_sites)
    v, w = pos[site], pos[ref]
    if geometry == Geometry.SQUARE_PLANAR:
        w = np.cross(v, w)
    n = float(np.linalg.norm(w))
    return None if n < 1e-9 else w / n


def _is_meridional_triple(positions: "list[np.ndarray]") -> bool:
    """True if a 3-site set spans a trans (~180°) pair — a meridian. A tridentate on
    such a triple is planar and meridional (terpy, pincer, ONO), not a facial triple."""
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            a, b = positions[i], positions[j]
            denom = float(np.linalg.norm(a)) * float(np.linalg.norm(b)) or 1.0
            if float(a @ b) / denom < -0.9:
                return True
    return False


def cis_pairs(geometry: Geometry, n_sites: "int | None" = None) -> list[tuple[int, int]]:
    """Adjacent site-id pairs — the pairs a bidentate chelate may span.

    Adjacent = separated by less than ~134 deg (cos > -0.7): neighbours, not the
    trans/opposite sites. For octahedral and square-planar this is exactly the
    90 deg cis pairs (180 deg trans excluded), unchanged; it also generalises to
    the trigonal/bipyramidal/prismatic geometries where neighbours sit at 72-120 deg.
    """
    if geometry == Geometry.LINEAR:
        # The two sites are trans, yet a CN2 chelate may span them: a long diphosphine or a
        # macrocycle on a d10 metal (geometry.propose_geometry picks linear only there).
        return [(0, 1)]
    pos = site_positions(geometry, n_sites)
    out = []
    for i in range(len(pos)):
        for j in range(i + 1, len(pos)):
            cos = float(pos[i] @ pos[j]) / (float(np.linalg.norm(pos[i])) * float(np.linalg.norm(pos[j])))
            if -0.7 < cos < 0.99:
                out.append((i, j))
    return out


def _adjacency(geometry: Geometry, n_sites: "int | None" = None) -> dict[int, set[int]]:
    n = n_sites if n_sites is not None else len(SITE_VECTORS[geometry])
    adj: dict[int, set[int]] = {i: set() for i in range(n)}
    for i, j in cis_pairs(geometry, n_sites):
        adj[i].add(j); adj[j].add(i)
    return adj


def _connected_groups(d: int, free: set[int], adj: dict[int, set[int]]) -> list[tuple[int, ...]]:
    """All connected site-subsets of size ``d`` drawn from ``free`` (d=1 -> singletons).

    A ligand of denticity d binds d mutually-reachable sites; enumerating connected
    subsets covers both facial (clique) and meridional (path) chelate modes.
    """
    if d == 1:
        return [(s,) for s in sorted(free)]
    results: list[tuple[int, ...]] = []
    seen: set = set()

    def grow(current: frozenset):
        if len(current) == d:
            if current not in seen:
                seen.add(current)
                results.append(tuple(sorted(current)))
            return
        frontier = sorted({x for c in current for x in adj[c] if x in free and x not in current})
        for x in frontier:
            grow(current | {x})

    for seed in sorted(free):
        grow(frozenset({seed}))
    return results


def _orthonormal_frame(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Right-handed orthonormal frame (as columns) with e1 along ``a`` and ``b``
    lying in the e1-e2 plane. ``a`` and ``b`` must be non-collinear."""
    e1 = a / np.linalg.norm(a)
    b_perp = b - float(b @ e1) * e1
    e2 = b_perp / np.linalg.norm(b_perp)
    e3 = np.cross(e1, e2)
    return np.column_stack([e1, e2, e3])


def _collinear_symmetry_perms(pos: np.ndarray, n: int) -> list[tuple[int, ...]]:
    """Symmetry site perms for a degenerate (all-collinear) geometry, e.g. linear
    CN2: the identity plus, if the point set is symmetric about the origin, the
    reversal (a proper C2 about any perpendicular axis)."""
    perms = {tuple(range(n))}
    rev: list[int] = []
    for i in range(n):
        k = next((t for t in range(n) if np.allclose(-pos[i], pos[t], atol=1e-6)), None)
        if k is None:
            break
        rev.append(k)
    if len(rev) == n and len(set(rev)) == n:
        perms.add(tuple(rev))
    return sorted(perms)


def _symmetry_site_perms(geometry: Geometry, *, proper: bool) -> list[tuple[int, ...]]:
    """Site permutations induced by the geometry's symmetry operations.

    Finds every orthogonal map (proper rotations, plus reflections when
    ``proper`` is False) that carries the site set onto itself, by sending a
    fixed reference frame (two non-collinear sites) onto every geometrically
    congruent pair of sites — both the right- and left-handed target frame for
    the full group. This is general to any coordination geometry, not only the
    axis-aligned ones (octahedral/square-planar), for which the earlier
    signed-axis-permutation trick silently undercounted the group.
    """
    pos = np.asarray(site_positions(geometry), dtype=float)
    n = len(pos)
    if n == 0:
        return [()]

    a0 = pos[0]
    i1 = next((k for k in range(1, n) if np.linalg.norm(np.cross(a0, pos[k])) > 1e-6), None)
    if i1 is None:  # all sites collinear (degenerate, e.g. linear)
        return _collinear_symmetry_perms(pos, n)

    b0 = pos[i1]
    F = _orthonormal_frame(a0, b0)
    n0a, n0b, d0 = float(a0 @ a0), float(b0 @ b0), float(a0 @ b0)
    signs = (1.0,) if proper else (1.0, -1.0)
    perms: set[tuple[int, ...]] = set()

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            a1, b1 = pos[i], pos[j]
            # The reference pair must map to a geometrically congruent pair.
            if (abs(float(a1 @ a1) - n0a) > 1e-6 or abs(float(b1 @ b1) - n0b) > 1e-6
                    or abs(float(a1 @ b1) - d0) > 1e-6
                    or np.linalg.norm(np.cross(a1, b1)) <= 1e-6):
                continue
            G = _orthonormal_frame(a1, b1)
            for s in signs:
                Gs = G.copy()
                Gs[:, 2] *= s  # left-handed target frame gives the improper op
                R = Gs @ F.T
                perm: list[int] = []
                for p in pos:
                    rp = R @ p
                    k = next((t for t in range(n) if np.allclose(rp, pos[t], atol=1e-6)), None)
                    if k is None:
                        break
                    perm.append(k)
                if len(perm) == n and len(set(perm)) == n:
                    perms.add(tuple(perm))
    return sorted(perms)


def proper_rotation_site_perms(geometry: Geometry) -> list[tuple[int, ...]]:
    """Site permutations induced by the geometry's proper rotation group.

    Each returned tuple ``p`` maps site id ``i`` -> site id ``p[i]`` under one
    proper rotation that carries the site set onto itself (octahedral -> 24,
    square-planar -> 8, linear -> the axial subgroup). Used to canonicalise a
    site assignment: two assignments related by such a permutation are the SAME
    isomer, whereas the improper (mirror) operations are deliberately excluded so
    Delta/Lambda enantiomers stay distinct.
    """
    return _symmetry_site_perms(geometry, proper=True)


def full_symmetry_site_perms(geometry: Geometry) -> list[tuple[int, ...]]:
    """Site permutations of the full point group (proper + improper/mirror ops).

    Deduplicating over this larger group merges enantiomers, so it drives the
    achiral ``stereo=False`` enumeration that reproduces the coarse isomer count.
    """
    return _symmetry_site_perms(geometry, proper=False)


def improper_site_perms(geometry: Geometry) -> list[tuple[int, ...]]:
    """The improper (mirror/rotoreflection) site perms: full group minus proper.

    Any one of these realigns a mirror-reflected assignment back onto the site
    framework, so it serves as the geometry-agnostic reflection used to test a
    complex for chirality (Delta/Lambda)."""
    proper = set(proper_rotation_site_perms(geometry))
    return [p for p in full_symmetry_site_perms(geometry) if p not in proper]


def _facial_triples(free: set[int], adj: dict[int, set[int]]) -> list[tuple[int, ...]]:
    """All free site triples that are mutually cis (a clique) — a facial triad,
    where an eta-arene / Cp cap must sit (its three donors are all ~cis)."""
    fr = sorted(free)
    out: list[tuple[int, ...]] = []
    for a in range(len(fr)):
        for b in range(a + 1, len(fr)):
            if fr[b] not in adj[fr[a]]:
                continue
            for c in range(b + 1, len(fr)):
                if fr[c] in adj[fr[a]] and fr[c] in adj[fr[b]]:
                    out.append((fr[a], fr[b], fr[c]))
    return out


def _bent_assignment(
    denticities: list[int], cap_ligands: set, cap_site_counts: "dict[int, int] | None" = None,
) -> dict[int, tuple[int, ...]]:
    """Bent metallocene filling: the two cap sites (0,1) take the η-caps, the wedge
    sites (2..) take the ancillary donors. Each cap ligand contributes
    ``cap_site_counts[lig]`` rings (caps come first in its donor order) followed by any
    σ donors of the SAME ligand (a Cp+pyridine ligand: 2 caps + its N in the wedge)."""
    cap_site_counts = cap_site_counts or {}
    n = sum(denticities)
    cap_pool, wedge_pool = list(range(2)), list(range(2, n))
    ci = wi = 0
    assignment: dict[int, tuple[int, ...]] = {}
    for lig, d in enumerate(denticities):
        nc = cap_site_counts.get(lig, 0) if lig in cap_ligands else 0
        picks = [cap_pool[ci + k] for k in range(nc)]
        ci += nc
        picks += [wedge_pool[wi + k] for k in range(d - nc)]
        wi += d - nc
        assignment[lig] = tuple(picks)
    if ci != 2 or wi != len(wedge_pool):
        raise SiteAssignmentError(
            "A bent metallocene needs exactly two η-cap sites plus the ancillary donors "
            f"(got {plural(ci, 'cap site')}, {plural(wi, 'wedge donor')})."
        )
    return dict(sorted(assignment.items()))


def default_assignment(
    geometry: Geometry, denticities: list[int], arene_ligands: "set[int] | None" = None,
    cap_ligands: "set[int] | None" = None, cap_site_counts: "dict[int, int] | None" = None,
) -> dict[int, tuple[int, ...]]:
    """A canonical {ligand index -> site ids} filling: bidentates take a free cis
    pair (high-denticity first), monodentates the next free site.

    ``arene_ligands`` (ligand indices) are eta-arene / Cp facial caps: their three
    donors are placed on a mutually-cis facial triad rather than any connected
    triple, so a half-sandwich comes out as a proper piano stool.

    ``cap_ligands`` are ligands carrying one or more centroid eta-caps (denticity-1
    each); their donors are NOT constrained to a connected/cis group (an ansa
    metallocene's two Cp span trans sites, a Cp+pyridine spreads over the polyhedron),
    so they may take any free-site combination.

    Matches the fixed topologies' default arrangement (e.g. octahedral bis-chelate
    ends up with trans monodentates), so builds are consistent whether or not the
    3D scene is used.
    """
    import itertools

    arene_ligands = arene_ligands or set()
    cap_ligands = cap_ligands or set()
    if geometry == Geometry.METALLOCENE_BENT:
        return _bent_assignment(denticities, cap_ligands, cap_site_counts)
    n_sites = len(SITE_VECTORS.get(geometry, ()))
    if not n_sites:
        raise SiteAssignmentError(f"No site model for geometry {geometry.value!r}.")
    if sum(denticities) != n_sites:
        raise SiteAssignmentError(
            f"Denticities {denticities} sum to {sum(denticities)} but "
            f"{geometry.value} has {n_sites} sites."
        )
    adj = _adjacency(geometry, n_sites)
    free = set(range(n_sites))
    assignment: dict[int, tuple[int, ...]] = {}
    # place high-denticity ligands first (they are the most constrained)
    order = sorted(range(len(denticities)), key=lambda i: denticities[i], reverse=True)

    def place(k: int) -> bool:
        if k == len(order):
            return not free
        lig = order[k]
        d = denticities[lig]
        if lig in cap_ligands:
            # Caps aren't bound to a connected/cis group — any d free sites.
            groups = [tuple(g) for g in itertools.combinations(sorted(free), d)]
        elif lig in arene_ligands:
            groups = _facial_triples(free, adj)
        else:
            groups = _connected_groups(d, free, adj)
        for group in groups:
            assignment[lig] = group
            free.difference_update(group)
            if place(k + 1):
                return True
            free.update(group)
            del assignment[lig]
        return False

    if not place(0):
        raise SiteAssignmentError(
            f"Denticities {denticities} cannot fill the {n_sites} "
            f"{geometry.value} sites."
        )
    return dict(sorted(assignment.items()))


def validate_assignment(
    geometry: Geometry, denticities: list[int], assignment: dict[int, tuple[int, ...]],
    cap_ligands: "set[int] | None" = None,
) -> None:
    """Check a {ligand index -> ordered site ids} assignment; raise on any hole."""
    cap_ligands = cap_ligands or set()
    n_sites = _n_sites(geometry, denticities)
    if not n_sites:
        raise SiteAssignmentError(f"No site model for geometry {geometry.value!r}.")
    if sorted(assignment) != list(range(len(denticities))):
        raise SiteAssignmentError("Every ligand must be assigned exactly once.")
    used: list[int] = []
    cis = set(cis_pairs(geometry, n_sites))
    for lig, sites in assignment.items():
        d = denticities[lig]
        if len(sites) != d:
            raise SiteAssignmentError(
                f"Ligand {lig} has denticity {d} but {plural(len(sites), 'site')} assigned."
            )
        if any(s < 0 or s >= n_sites for s in sites):
            raise SiteAssignmentError(f"Ligand {lig}: site id out of range 0..{n_sites - 1}.")
        used.extend(sites)
        # A bidentate must span a cis pair -- but a cap ligand's two Cp can be trans.
        if d == 2 and lig not in cap_ligands and tuple(sorted(sites)) not in cis:
            raise SiteAssignmentError(
                f"Ligand {lig}: sites {sites} are trans — a bidentate must span two cis sites."
            )
    if len(used) != len(set(used)):
        raise SiteAssignmentError("Two donors were assigned to the same site.")
    if len(used) != n_sites:
        raise SiteAssignmentError(
            f"{plural(len(used), 'donor')} assigned but {geometry.value} has {n_sites} sites."
        )


def topology_from_sites(
    geometry: Geometry,
    denticities: list[int],
    assignment: dict[int, tuple[int, ...]],
    planar_ligands: "set[int] | None" = None,
    cap_ligands: "set[int] | None" = None,
) -> type:
    """Build a MetalComplex topology class for one explicit site assignment.

    One ligand vertex per ligand (positioned on the bisector of its sites), one
    metal-ligand edge per assigned site, edges created in the ligand's donor
    order so donor k aligns with site k (the vertex placement code aligns the
    fg0->fg1 axis with the edge0->edge1 axis in that order).

    ``planar_ligands`` are ligand indices whose denticity-3 donor set is a planar
    facial cap (eta-arene/Cp); they use :class:`PlanarTriDentateLigandVertex` so
    the ring plane stays parallel to its face, instead of the generic tridentate
    vertex.
    """
    validate_assignment(geometry, denticities, assignment, cap_ligands=cap_ligands)
    planar_ligands = planar_ligands or set()
    cap_ligands = cap_ligands or set()
    pos = site_positions(geometry, _n_sites(geometry, denticities))

    metal_proto = (MetalVertex(0, (0.0, 0.0, 0.0)),)
    ligand_protos = []
    edges = []
    edge_id = 0
    for lig in sorted(assignment):
        sites = assignment[lig]
        d = denticities[lig]
        if d == 1 and lig in cap_ligands:
            vclass = CentroidCapVertex          # η-cap centroid: 1 multi-bonder FG
        elif d >= 2 and lig in cap_ligands:
            vclass = CapMultiVertex             # ansa/Cp+donor: caps ON their sites
        elif d == 3 and lig in planar_ligands:
            vclass = PlanarTriDentateLigandVertex
        elif d == 3 and lig not in cap_ligands and _is_meridional_triple([pos[s] for s in sites]):
            # A planar MERIDIONAL tridentate (terpy, pincer, ONO): align its plane to
            # its meridian, so two of them (bis-terpy) sit on perpendicular planes and
            # don't interpenetrate the way the generic tridentate vertex lets them.
            vclass = PlanarTriDentateLigandVertex
        elif d < 1:
            raise SiteAssignmentError(f"Ligand {lig} has denticity {d}.")
        else:
            vclass = _vertex_class_for(d)
        centroid = np.mean([pos[s] for s in sites], axis=0)
        norm = np.linalg.norm(centroid)
        vpos = centroid / norm * _R if norm > 1e-6 else pos[sites[0]]  # mer-tridentate fallback
        vertex = vclass(len(ligand_protos) + 1, tuple(vpos))
        ligand_protos.append(vertex)
        for s in sites:
            edges.append(
                stk.Edge(edge_id, metal_proto[0], vertex, position=tuple(pos[s]))
            )
            edge_id += 1

    return type(
        f"SiteAssigned_{geometry.value}",
        (MetalComplex,),
        {
            "_metal_vertex_prototypes": metal_proto,
            "_ligand_vertex_prototypes": tuple(ligand_protos),
            "_edge_prototypes": tuple(edges),
        },
    )
