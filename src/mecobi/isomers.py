"""Isomer determination.

Three modes, all resolving to the same downstream contract:
    1. "All isomers" — enumerate distinct geometric isomers via the topology
       graphs' vertex geometry (this module).
    2. Specific isomer via the 3D scene — donor-to-numbered-vertex assignment.
    3. Specific isomer via index/topology string — non-visual, same numbering as
       the 3D scene (invariant 7).

Enumeration here deduplicates ligand placements up to the **vertex symmetry
group** (isometries of the idealised vertex positions that preserve denticity)
and up to identical ligands. It is a geometric-isomer approximation: donor-
direction isomers (reversing a bidentate's two donors) and explicit Delta/Lambda
enantiomer splitting are refinements left for later. The topology-specification
string format (mode 3) remains DEFERRED.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import permutations, product

from .model import Complex, Geometry, Ligand


@dataclass(frozen=True)
class IsomerSpec:
    """A resolved donor-to-site (or vertex) assignment for one isomer.

    ``assignment`` maps ligand index -> tuple of ids, using the SAME numbering as
    the 3D scene (invariant 7). ``label`` is a human tag when one exists. When
    ``site_based`` is True the ids are canonical coordination-site ids (donor k
    binds site ``assignment[lig][k]``) and the build routes through
    :func:`mecobi.assembly.build_from_sites`; otherwise they are topology vertex
    ids for :func:`mecobi.assembly.build`. The serialised topology-string form is
    DEFERRED; this is the in-memory seam.
    """

    geometry: Geometry
    label: str | None
    assignment: dict[int, tuple[int, ...]]
    site_based: bool = False


def _ligand_key(lig: Ligand) -> tuple:
    """Identity of a ligand for isomer dedup (identical ligands share a key)."""
    return (lig.smiles, tuple(lig.effective_donors or ()))


def _vertex_automorphisms(positions, denticities, tol: float = 0.15) -> list[tuple[int, ...]]:
    """Permutations of vertices that preserve denticity and all pairwise distances."""
    import numpy as np

    n = len(positions)
    dist = [[float(np.linalg.norm(positions[i] - positions[j])) for j in range(n)] for i in range(n)]

    classes = list(defaultdict(list, _group_indices(denticities)).values())
    autos: list[tuple[int, ...]] = []
    for combo in product(*[permutations(cls) for cls in classes]):
        p = [0] * n
        for cls, perm in zip(classes, combo):
            for orig, new in zip(cls, perm):
                p[orig] = new
        if all(
            abs(dist[i][j] - dist[p[i]][p[j]]) <= tol
            for i in range(n) for j in range(i + 1, n)
        ):
            autos.append(tuple(p))
    return autos


def _group_indices(values) -> dict:
    groups: dict = defaultdict(list)
    for i, v in enumerate(values):
        groups[v].append(i)
    return groups


def enumerate_isomers(
    complex: Complex, geometry: Geometry, *, max_isomers: int = 64
) -> list[IsomerSpec]:
    """Enumerate distinct geometric isomers for a complex/geometry.

    Assigns ligands to vertices within matching denticity classes, then
    deduplicates up to the vertex symmetry group and identical ligands.
    """
    from .assembly import registry  # lazy: avoids import cycle with assembly

    denticities = [l.denticity for l in complex.ligands]
    try:
        entry = registry.lookup(geometry, denticities)
    except KeyError:
        # No FIXED vertex topology for this (geometry, partition). Most geometries
        # live in the site model (assembly.default_isomer / enumerate_site_isomers),
        # not the small fixed registry, so raise a typed, actionable error instead
        # of leaking a raw (geometry, partition) KeyError tuple to callers.
        raise UnsupportedTopology(
            f"No fixed vertex topology for {geometry.value} with denticities "
            f"{registry.partition(denticities)}; use the site model "
            f"(enumerate_site_isomers / assembly.default_isomer)."
        ) from None
    vdent = entry.vertex_denticities
    autos = _vertex_automorphisms(registry.vertex_positions(entry), vdent)

    ligs_by_d = _group_indices(denticities)
    verts_by_d = _group_indices(vdent)

    # For each denticity class, every bijection of its ligands onto its vertices.
    class_options = []
    for d, verts in verts_by_d.items():
        ligs = ligs_by_d[d]
        class_options.append([list(zip(verts, perm)) for perm in permutations(ligs)])

    keys = [_ligand_key(l) for l in complex.ligands]
    seen: set = set()
    results: list[IsomerSpec] = []
    for combo in product(*class_options):
        vertex_to_lig = {}
        for pairs in combo:
            vertex_to_lig.update(pairs)
        idtuple = tuple(keys[vertex_to_lig[v]] for v in range(len(vdent)))
        canon = min(
            tuple(idtuple[p.index(k)] for k in range(len(vdent))) for p in autos
        )
        if canon in seen:
            continue
        seen.add(canon)
        lig_to_verts: dict = defaultdict(list)
        for v, lig in vertex_to_lig.items():
            lig_to_verts[lig].append(v)
        assignment = {lig: tuple(sorted(vs)) for lig, vs in lig_to_verts.items()}
        results.append(IsomerSpec(geometry=geometry, label=None, assignment=assignment))
        if len(results) >= max_isomers:
            break
    return results


class UnsupportedTopology(RuntimeError):
    """No fixed vertex topology exists for a (geometry, denticity-partition).

    Raised by :func:`enumerate_isomers` (the fixed-registry enumerator). The site
    model — :func:`enumerate_site_isomers` / :func:`mecobi.assembly.default_isomer`
    — covers these geometries, so callers should fall back to it.
    """


class StereoNotSupported(RuntimeError):
    """Raised when the site-based stereo enumeration can't express a complex.

    Callers (pipeline) should fall back to the coarse vertex enumeration.
    """


def _ligand_type_key(smiles: str) -> str:
    """Canonical identity of a ligand type (identical ligands share a key)."""
    from rdkit import Chem

    m = Chem.MolFromSmiles(smiles)
    return Chem.MolToSmiles(m) if m is not None else smiles


def _all_site_assignments(geometry, denticities, *, ordered, facial_ligs=frozenset()):
    """Every {lig -> site tuple} that fills all sites.

    Bidentates take a cis pair — as an ordered pair (both donor directions) when
    ``ordered``, else a single canonical order. Monodentates take one site. A
    tridentate takes a facial triple (three mutually-cis sites) when it is an
    arene/Cp cap (``facial_ligs``), else a meridional triple (a central site cis
    to two mutually-trans ends) as a planar tridentate such as terpyridine.
    """
    from .assembly import sites

    n_sites = len(sites.SITE_VECTORS[geometry])
    cis = sites.cis_pairs(geometry)
    is_cis = {(min(a, b), max(a, b)) for a, b in cis}
    # fac triples: one site per axis => three mutually orthogonal (cis) sites.
    pos = sites.site_positions(geometry)
    facial_triples = [
        (i, j, k)
        for i in range(n_sites) for j in range(i + 1, n_sites) for k in range(j + 1, n_sites)
        if abs(float(pos[i] @ pos[j])) < 1e-6
        and abs(float(pos[i] @ pos[k])) < 1e-6
        and abs(float(pos[j] @ pos[k])) < 1e-6
    ]
    # mer triples: a centre cis to two ends that are themselves trans (not cis),
    # ordered (centre in the middle) so the tuple encodes donor -> site placement.
    meridional_triples: list[tuple[int, int, int]] = []
    for b in range(n_sites):
        ends = [s for s in range(n_sites) if s != b and (min(b, s), max(b, s)) in is_cis]
        for a in ends:
            for c in ends:
                if a == c or (min(a, c), max(a, c)) in is_cis:
                    continue
                if ordered or a < c:  # both donor directions when ordered
                    meridional_triples.append((a, b, c))
    order = sorted(range(len(denticities)), key=lambda i: denticities[i], reverse=True)
    out: list[dict] = []
    free = set(range(n_sites))
    asg: dict[int, tuple[int, ...]] = {}

    def place(k: int) -> None:
        if k == len(order):
            if not free:
                out.append(dict(asg))
            return
        lig = order[k]
        d = denticities[lig]
        if d == 1:
            for s in sorted(free):
                asg[lig] = (s,)
                free.discard(s)
                place(k + 1)
                free.add(s)
                asg.pop(lig)
        elif d == 2:
            for a, b in cis:
                if a in free and b in free:
                    for pr in (((a, b), (b, a)) if ordered else ((a, b),)):
                        asg[lig] = pr
                        free.difference_update((a, b))
                        place(k + 1)
                        free.update((a, b))
                        asg.pop(lig)
        elif d == 3:
            # Arene/Cp caps take a symmetric facial triad; planar tridentates
            # (terpy) take a meridional triple with the central donor in the middle.
            cand = facial_triples if lig in facial_ligs else meridional_triples
            for tri in cand:
                if all(s in free for s in tri):
                    asg[lig] = tri
                    free.difference_update(tri)
                    place(k + 1)
                    free.update(tri)
                    asg.pop(lig)
        else:
            raise StereoNotSupported(f"site enumeration supports denticity 1-3, got {d}")

    place(0)
    return out


def _mirror_assignment(assignment, geometry):
    """Reflect an assignment through a mirror plane (an improper site permutation).

    Uses any one improper operation of the geometry's point group, which maps the
    site framework onto itself for ANY geometry (the earlier hard-coded negate-x
    reflection only mapped sites to sites for octahedral/square-planar, and
    collapsed to the identity — silently disabling Delta/Lambda — everywhere else).
    """
    from .assembly import sites

    improper = sites.improper_site_perms(geometry)
    if not improper:  # framework has no mirror symmetry: mirror == identity
        return dict(assignment)
    refl = improper[0]
    return {lig: tuple(refl[s] for s in sitetup) for lig, sitetup in assignment.items()}


def enumerate_site_isomers(
    complex: Complex, geometry: Geometry, *, stereo: bool = True, max_isomers: int = 64
) -> list[IsomerSpec]:
    """Enumerate stereoisomers via the coordination-site model.

    Unlike :func:`enumerate_isomers` (coarse, vertex-level), this deduplicates
    ordered donor->site assignments up to the geometry's **proper** rotation
    group, so it distinguishes Delta/Lambda enantiomers and the donor-direction
    of asymmetric chelates, while collapsing donor swaps of symmetric chelates
    (via :func:`mecobi.assembly._chem.donor_symmetry_classes`). With
    ``stereo=False`` it deduplicates over the full point group (merging
    enantiomers) and ignores donor direction — reproducing the coarse count.

    Raises :class:`StereoNotSupported` if a ligand denticity is outside 1-3.
    """
    from .assembly import _chem, sites

    dents = [l.denticity for l in complex.ligands]
    if any(d is None for d in dents):
        raise StereoNotSupported("perceive ligands (denticities) before enumerating isomers")
    if geometry not in sites.SITE_VECTORS:
        raise StereoNotSupported(f"no site model for geometry {geometry.value!r}")
    n_sites = len(sites.SITE_VECTORS[geometry])
    if sum(dents) != n_sites:
        raise StereoNotSupported(
            f"denticities sum to {sum(dents)} but {geometry.value} has {n_sites} sites"
        )
    if any((d or 0) > 3 for d in dents):
        raise StereoNotSupported("site model supports denticity 1-3")

    lig_keys, lig_classes = [], []
    for l in complex.ligands:
        donors = list(l.effective_donors or [])
        lig_keys.append(_ligand_type_key(l.smiles))
        if l.is_arene:
            # facial cap: donors are a symmetric triad — direction is irrelevant.
            lig_classes.append([0] * l.denticity)
        else:
            lig_classes.append(_chem.donor_symmetry_classes(l.smiles, donors) if donors else [])

    group = (
        sites.proper_rotation_site_perms(geometry)
        if stereo
        else sites.full_symmetry_site_perms(geometry)
    )
    from .assembly import is_tripodal  # lazy: assembly imports this module

    # Arene caps AND tripodal σ-tridentates (tacn, Tp, triphos, a bis(pyridyl)methyl tripod)
    # take facial triples; a tripod cannot span the trans pair of a meridional triple.
    facial_ligs = frozenset(
        i for i, l in enumerate(complex.ligands) if l.is_arene or is_tripodal(l))
    raw = _all_site_assignments(geometry, dents, ordered=stereo, facial_ligs=facial_ligs)

    def canonical(asg):
        return _canonicalize(_blocks(asg, lig_keys, lig_classes, stereo), group)

    seen: dict = {}
    reps: list[tuple] = []
    for asg in raw:
        c = canonical(asg)
        if c in seen:
            continue
        seen[c] = asg
        reps.append((c, asg))
        if len(reps) >= max_isomers:
            break

    return _label_isomers(complex, geometry, reps, lig_keys, lig_classes, stereo)


def _blocks(asg, lig_keys, lig_classes, stereo):
    """Assignment as labeled ligand-blocks: (lig_key, sorted (site, donor_class)).

    Grouping donors into blocks encodes chelate connectivity (which sites share a
    ligand); the donor_class encodes donor direction (kept for asymmetric
    chelates, collapsed to 0 for symmetric ones / non-stereo).
    """
    bl = []
    for lig, sitetup in asg.items():
        classes = lig_classes[lig]
        items = tuple(
            sorted((s, (classes[k] if (stereo and classes) else 0)) for k, s in enumerate(sitetup))
        )
        bl.append((lig_keys[lig], items))
    return bl


def _canonicalize(blocks, group):
    """Canonical form of labeled blocks, minimised over the site-permutation group."""
    best = None
    for p in group:
        mapped = tuple(
            sorted((key, tuple(sorted((p[s], c) for (s, c) in items))) for (key, items) in blocks)
        )
        if best is None or mapped < best:
            best = mapped
    return best


def _label_isomers(complex, geometry, reps, lig_keys, lig_classes, stereo) -> list[IsomerSpec]:
    """Attach Delta/Lambda + cis/trans labels (uniquified) to enumerated isomers.

    An isomer is chiral iff its mirror image is a *different* enumerated isomer
    (their canonical forms differ under the proper rotation group). Within such an
    enantiomer pair the member with the lexicographically smaller canonical form
    is tagged ``Delta`` and its partner ``Lambda`` — a deterministic convention
    that always gives the two hands opposite tags (not a claim of absolute IUPAC
    configuration).
    """
    from .assembly import sites

    proper = sites.proper_rotation_site_perms(geometry)
    canon_set = {c for c, _ in reps}
    pos = sites.site_positions(geometry)

    raw_labels: list[str | None] = []
    for canon, asg in reps:
        parts: list[str] = []
        if stereo:
            mirror = _mirror_assignment(asg, geometry)
            mcanon = _canonicalize(_blocks(mirror, lig_keys, lig_classes, stereo), proper)
            if mcanon in canon_set and mcanon != canon:
                parts.append("Delta" if canon < mcanon else "Lambda")
        tag = _positional_tag(asg, complex, geometry, pos)
        if tag:
            parts.append(tag)
        raw_labels.append("_".join(parts) if parts else None)

    labels = _uniquify_labels(raw_labels)
    return [
        IsomerSpec(geometry=geometry, label=labels[i], assignment=dict(asg), site_based=True)
        for i, (_c, asg) in enumerate(reps)
    ]


def _uniquify_labels(labels: list[str | None]) -> list[str | None]:
    """Disambiguate repeated/None labels so each maps to a distinct filename stem."""
    from collections import Counter

    counts = Counter(l for l in labels if l is not None)
    seen: Counter = Counter()
    out: list[str | None] = []
    for i, l in enumerate(labels, start=1):
        if l is None:
            out.append(f"iso{i:02d}")
        elif counts[l] > 1:
            seen[l] += 1
            out.append(f"{l}{seen[l]}")
        else:
            out.append(l)
    return out


def _site_weights(asg, lig_keys, lig_classes, rank, geometry, stereo):
    from .assembly import sites

    n_sites = len(sites.SITE_VECTORS[geometry])
    weights = [0.0] * n_sites
    for lig, sitetup in asg.items():
        classes = lig_classes[lig]
        for k, s in enumerate(sitetup):
            dc = classes[k] if (stereo and classes) else 0
            weights[s] = float(rank.get((lig_keys[lig], dc), 0))
    return weights


def _positional_tag(asg, complex, geometry, pos):
    """cis/trans for a pair of identical monodentates, when unambiguous."""
    import numpy as np
    from collections import defaultdict

    by_key = defaultdict(list)
    for lig, sitetup in asg.items():
        if complex.ligands[lig].denticity == 1:
            by_key[_ligand_type_key(complex.ligands[lig].smiles)].append(sitetup[0])
    for _key, ss in by_key.items():
        if len(ss) == 2:
            va, vb = pos[ss[0]], pos[ss[1]]
            cos = float(va @ vb) / (np.linalg.norm(va) * np.linalg.norm(vb))
            return "trans" if cos < -0.5 else "cis"
    return ""


class IsomerNotationError(ValueError):
    """Raised when a donor-index isomer notation string is malformed."""


@dataclass(frozen=True)
class IsomerNotation:
    """Parsed donor-index isomer notation ("mode 3").

    The non-visual equivalent of the 3D site-assigner: a compact text string that
    pins, per ligand, *which SMILES atoms coordinate* and/or *which coordination
    site each donor occupies*. It is the analog of the CIF ``metalbondatoms``
    column — atom indices are 0-based RDKit heavy-atom indices of that ligand's
    own SMILES; site ids use the canonical site numbering (invariant 7, shared
    with the 3D scene, :data:`mecobi.assembly.sites.SITE_VECTORS`).

    Attributes:
        geometry: Optional geometry override (from a ``geometry|`` prefix).
        donors: ligand index -> donor atom indices (empty when unspecified).
        sites: ligand index -> site ids in donor order (empty when unspecified);
            when present the pipeline builds exactly that isomer via the site model.
    """

    geometry: Geometry | None = None
    donors: dict[int, tuple[int, ...]] = field(default_factory=dict)
    sites: dict[int, tuple[int, ...]] = field(default_factory=dict)


# One block:  ligIdx  [ (donorAtoms) ]  [ :siteList ]  — whitespace is ignored.
_BLOCK_RE = re.compile(
    r"^\s*(?P<lig>\d+)\s*(?:\(\s*(?P<donors>[\d,\s]*)\)\s*)?(?::\s*(?P<sites>[\d,\s]*))?\s*$"
)


def _int_list(text: str | None) -> tuple[int, ...]:
    if not text or not text.strip():
        return ()
    return tuple(int(x) for x in text.split(",") if x.strip() != "")


def parse_isomer_notation(spec: str) -> IsomerNotation:
    """Parse a donor-index isomer notation string into an :class:`IsomerNotation`.

    Grammar (whitespace-insensitive)::

        spec  := [ geometry '|' ] block ( ';' block )*
        block := ligIdx [ '(' atom (',' atom)* ')' ] [ ':' site (',' site)* ]

    Examples::

        "0(3);1(3)"                 # pin donor atom 3 of ligands 0 and 1
        "0:0,2;1:1,3;2:4;3:5"       # cis bis-chelate octahedral isomer
        "octahedral| 0(0,1):0,2; 2:4; 3:5"   # geometry + donors + sites

    A block must specify donors, sites, or both. Raises
    :class:`IsomerNotationError` on any malformed input (duplicate ligand,
    unknown geometry, non-integer index).
    """
    text = spec.strip()
    if not text:
        raise IsomerNotationError("empty isomer notation")
    geometry: Geometry | None = None
    if "|" in text:
        gpart, text = text.split("|", 1)
        gpart = gpart.strip()
        if gpart:
            try:
                geometry = Geometry(gpart)
            except ValueError as exc:
                raise IsomerNotationError(f"unknown geometry {gpart!r}") from exc

    donors: dict[int, tuple[int, ...]] = {}
    sites: dict[int, tuple[int, ...]] = {}
    for raw in text.split(";"):
        if not raw.strip():
            continue
        m = _BLOCK_RE.match(raw)
        if m is None:
            raise IsomerNotationError(f"malformed block {raw.strip()!r}")
        lig = int(m.group("lig"))
        if lig in donors or lig in sites:
            raise IsomerNotationError(f"ligand {lig} specified more than once")
        d = _int_list(m.group("donors"))
        s = _int_list(m.group("sites"))
        if not d and not s:
            raise IsomerNotationError(
                f"block {raw.strip()!r} pins neither donor atoms nor sites"
            )
        if d:
            donors[lig] = d
        if s:
            sites[lig] = s
    if not donors and not sites:
        raise IsomerNotationError("isomer notation specifies nothing")
    return IsomerNotation(geometry=geometry, donors=donors, sites=sites)


def format_isomer_spec(
    spec: IsomerSpec, donors: dict[int, tuple[int, ...]] | None = None
) -> str:
    """Serialise a site-based :class:`IsomerSpec` to a donor-index notation string.

    The inverse of :func:`parse_isomer_notation` for the site (isomer) part; pass
    ``donors`` to also emit the coordinating-atom indices. Site order within a
    ligand is preserved (it encodes donor direction), so the round-trip is exact.
    """
    if not spec.site_based:
        raise IsomerNotationError("only site-based IsomerSpecs have a notation form")
    parts: list[str] = []
    for lig in sorted(spec.assignment):
        block = str(lig)
        if donors and lig in donors:
            block += "(" + ",".join(str(a) for a in donors[lig]) + ")"
        block += ":" + ",".join(str(s) for s in spec.assignment[lig])
        parts.append(block)
    return ";".join(parts)


def parse_topology_spec(spec: str, geometry: Geometry) -> IsomerSpec:
    """Mode 3: parse a donor-index isomer notation string into a site-based
    :class:`IsomerSpec`.

    Requires the notation to assign sites (``ligIdx:site,...``); a donors-only
    string does not name an isomer. The geometry comes from a ``geometry|`` prefix
    if present, else the ``geometry`` argument. Denticity/cis validity is checked
    downstream by :func:`mecobi.assembly.sites.validate_assignment` at build time.
    """
    notation = parse_isomer_notation(spec)
    geom = notation.geometry or geometry
    if not notation.sites:
        raise IsomerNotationError(
            "topology spec must assign sites (e.g. '0:0,2;1:1,3;2:4;3:5')"
        )
    return IsomerSpec(
        geometry=geom, label="custom", assignment=dict(notation.sites), site_based=True
    )
