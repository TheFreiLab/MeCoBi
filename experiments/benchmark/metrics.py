"""Structure-fidelity metrics for the MeCoBi CSD benchmark (Phase 2).

Coordination-geometry quality is reported the way the field does it -- robustly --
rather than via raw donor-metal-donor angle RMSD (which the mined 21k-angle CSD
distribution shows is dominated by intrinsic +/-8-17 deg scatter):

  * continuous_shape_measure (CShM) -- an ANGULAR variant of the SHAPE/Alvarez measure
    (metal-donor unit vectors, metal not a vertex): how far the coordination polyhedron is
    from an ideal shape (0 = perfect). Reported vs the best-matching ideal for the CN.
    Values are not numerically SHAPE's.
  * local_distance_matrix_rmsd -- RMSD of the donor-donor distance matrix; folds angular +
    radial error into one number (a donor-donor distance encodes the L-M-L angle given the
    bonds). MeCoBi's own metric, not MetalloGen's D-MAE3.

Plus the direct radial metric (metal-donor bond RMSD over SORTED bond lengths -- a lower
bound, since it ignores which donor is which). No gemmi/ase (not installed); numpy/scipy.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

from hydrides import build_hydrides


# ---------------------------------------------------------------------------
# ideal coordination polyhedra (unit vectors), one or more candidate shapes / CN
# ---------------------------------------------------------------------------
def _pentagon(z=0.0):
    return [(math.cos(2 * math.pi * k / 5), math.sin(2 * math.pi * k / 5), z)
            for k in range(5)]


def _ideal_shapes() -> dict[int, dict[str, np.ndarray]]:
    t = 1 / math.sqrt(3)
    tA, tB = math.radians(36.9), math.radians(69.5)  # dodecahedron polar angles
    # SHAPE SPY-5 (spherical square pyramid, C4v): basal donors at arccos(-1/4) = 104.48 deg from
    # the apex about the metal -- not 90 deg, which is the vacant octahedron (SHAPE's vOC-5).
    zb, rb = -0.25, math.sqrt(1 - 0.25 ** 2)
    # SHAPE SAPR-8 (regular square antiprism, all edges equal): tan^2(polar) = 2*sqrt(2), so the
    # polar angle is 59.26 deg (cosymlib ideal_structures_center.yaml), not 67.5 deg.
    ta = math.atan(math.sqrt(2 * math.sqrt(2)))
    sa, ca = math.sin(ta), math.cos(ta)
    shapes = {
        # CN2: linear, or bent at 90 deg (SHAPE vOC-2; MeCoBi's bent site model): a single chelate
        # on a main-group or d8 centre is bent, so linear alone made every CN2 shape "match".
        2: {"linear": [(0, 0, 1), (0, 0, -1)], "bent": [(1, 0, 0), (0, 1, 0)]},
        3: {"trigonal_planar": [(1, 0, 0), (-0.5, 0.8660, 0), (-0.5, -0.8660, 0)]},
        4: {
            "tetrahedral": [(t, t, t), (t, -t, -t), (-t, t, -t), (-t, -t, t)],
            "square_planar": [(1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0)],
        },
        5: {
            "trigonal_bipyramidal":
                [(0, 0, 1), (0, 0, -1), (1, 0, 0), (-0.5, 0.8660, 0), (-0.5, -0.8660, 0)],
            "square_pyramidal":
                [(0, 0, 1), (rb, 0, zb), (0, rb, zb), (-rb, 0, zb), (0, -rb, zb)],
        },
        6: {"octahedral": [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]},
        7: {"pentagonal_bipyramidal": [(0, 0, 1), (0, 0, -1)] + _pentagon()},
        8: {"square_antiprism":
            [(math.cos(a) * sa, math.sin(a) * sa, ca) for a in
             np.deg2rad([0, 90, 180, 270])] +
            [(math.cos(a) * sa, math.sin(a) * sa, -ca) for a in
             np.deg2rad([45, 135, 225, 315])],
            # D2d triangular dodecahedron (bisdisphenoid): two disphenoids rotated
            # 90 deg, with Hoard-Silverton ideal polar angles ~36.9/69.5 deg. The
            # other common CN8 shape; without it every CN8 sphere trivially
            # classifies as antiprism. (bicapped trigonal prism omitted: it lies
            # between these two and the iterative CShM solver can't resolve a third
            # near-degenerate CN8 candidate reliably.)
            "dodecahedral":
            [(0.0,  math.sin(tA),  math.cos(tA)), (0.0, -math.sin(tA),  math.cos(tA)),
             (math.sin(tA), 0.0, -math.cos(tA)), (-math.sin(tA), 0.0, -math.cos(tA)),
             (math.sin(tB), 0.0,  math.cos(tB)), (-math.sin(tB), 0.0,  math.cos(tB)),
             (0.0,  math.sin(tB), -math.cos(tB)), (0.0, -math.sin(tB), -math.cos(tB))]},
        9: {"tricapped_trigonal_prism":
            [(math.cos(a), math.sin(a), 0.5) for a in np.deg2rad([90, 210, 330])] +
            [(math.cos(a), math.sin(a), -0.5) for a in np.deg2rad([90, 210, 330])] +
            [(math.cos(a), math.sin(a), 0.0) for a in np.deg2rad([30, 150, 270])]},
    }
    return {cn: {n: _unit(np.array(v, float)) for n, v in d.items()}
            for cn, d in shapes.items()}


def _unit(P: np.ndarray) -> np.ndarray:
    return P / np.linalg.norm(P, axis=1, keepdims=True)


_IDEAL = _ideal_shapes()


# ---------------------------------------------------------------------------
def _kabsch(P: np.ndarray, Q: np.ndarray) -> np.ndarray:
    """Rotation R minimising |Q - P R^T| (both centred, same order)."""
    H = P.T @ Q
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    return Vt.T @ np.diag([1.0, 1.0, d]) @ U.T


def _random_rotation(rng) -> np.ndarray:
    """A uniformly-random proper rotation matrix (QR of a Gaussian matrix, det forced +1)."""
    Q, R = np.linalg.qr(rng.standard_normal((3, 3)))
    Q *= np.sign(np.diag(R))
    if np.linalg.det(Q) < 0:
        Q[:, 0] = -Q[:, 0]
    return Q


_EXACT_MAX = 8          # CN up to which every vertex permutation is tried (8! = 40320)
_PERMS: dict[int, np.ndarray] = {}


def _permutations(n: int) -> np.ndarray:
    """All permutations of range(n) as an (n!, n) int array (cached)."""
    if n not in _PERMS:
        _PERMS[n] = np.array(list(itertools.permutations(range(n))), dtype=np.int8)
    return _PERMS[n]


def _cshm_exact(Q: np.ndarray, P0: np.ndarray, reflect: bool) -> float:
    """Exact CShM over every vertex permutation (both arrays centred). For a fixed pairing the
    best rotation + scale has a closed form: with H = P^T Q and singular values s1>=s2>=s3,
    min resid = |Q|^2 - (s1 + s2 + d*s3)^2 / |P|^2, where d = sign(det H) for a proper rotation
    (d = 1 when reflections are allowed). Vectorised over all n! pairings."""
    perms = _permutations(len(Q))
    H = np.einsum("mni,nj->mij", P0[perms], Q)
    sv = np.linalg.svd(H, compute_uv=False)
    if not reflect:
        sv[:, 2] *= np.sign(np.linalg.det(H))
    tr = sv.sum(axis=1).max()
    ratio = tr * tr / (float(np.sum(P0 * P0)) * float(np.sum(Q * Q)))
    return max(0.0, 100.0 * (1.0 - ratio))


def continuous_shape_measure(donor_dirs, shape_vecs, iters: int = 25, restarts: int = 50,
                             reflect: bool = False) -> float:
    """CShM of a coordination sphere vs one ideal shape (0 = perfect, up to 100).

    S = 100 * min_{rotation, permutation, scale} sum|q_i - s R p_j|^2 / sum|q_i - q0|^2.

    Angular variant: the inputs are metal-donor UNIT vectors and the metal itself is not a
    vertex, so bond-length distortions do not count and the values are not numerically SHAPE's
    (whose literature thresholds therefore do not apply).

    For CN <= 8 the minimum is EXACT: every vertex permutation is tried with its closed-form
    best rotation (:func:`_cshm_exact`). The earlier Hungarian <-> Kabsch iteration from 6
    random starts missed the true minimum for ~15% of crystal CN4-6 spheres and gave the wrong
    best-shape label for ~7%. Above CN8 the iteration is still used, from ``restarts`` random
    starting rotations. ``reflect`` also allows improper rotations (mirror images).

    Two donors alone always form the same shape (a segment), so at CN2 the metal (the origin)
    is added as a third vertex: the metal-donor triangle tells linear from bent."""
    if len(donor_dirs) == 2 and len(shape_vecs) == 2:
        donor_dirs = np.vstack([np.asarray(donor_dirs, float), np.zeros(3)])
        shape_vecs = np.vstack([np.asarray(shape_vecs, float), np.zeros(3)])
    Q = np.asarray(donor_dirs, float)
    Q = Q - Q.mean(0)
    denom = float(np.sum(Q * Q))
    if denom < 1e-9 or len(Q) != len(shape_vecs):
        return float("nan")
    P0 = np.asarray(shape_vecs, float)
    P0 = P0 - P0.mean(0)
    if len(Q) <= _EXACT_MAX:
        return _cshm_exact(Q, P0, reflect)
    rng = np.random.default_rng(0)  # fixed seed: deterministic result
    best = float("inf")
    for M in ([np.eye(3), np.diag([-1.0, 1.0, 1.0])] if reflect else [np.eye(3)]):
        Pm = P0 @ M.T
        for attempt in range(max(1, restarts)):
            R = np.eye(3) if attempt == 0 else _random_rotation(rng)
            perm = np.arange(len(Q))
            for _ in range(iters):
                row, col = linear_sum_assignment(cdist(Q, Pm @ R.T))
                perm = col
                R = _kabsch(Pm[perm], Q)
            Prot = Pm[perm] @ R.T
            s = float(np.sum(Q * Prot) / np.sum(Prot * Prot))
            resid = float(np.sum((Q - s * Prot) ** 2))
            best = min(best, 100.0 * resid / denom)
    return best


def best_shape(donor_dirs, cn: int) -> "tuple[str, float]":
    """(shape name, CShM) for the closest ideal shape at this CN; ('', nan) if unknown."""
    cands = _IDEAL.get(cn)
    if not cands or len(donor_dirs) != cn:
        return "", float("nan")
    scored = [(name, continuous_shape_measure(donor_dirs, vecs))
              for name, vecs in cands.items()]
    return min(scored, key=lambda t: t[1])


def shape_deviation(build_dirs, exp_dirs) -> float:
    """CShM of the build coordination polyhedron measured directly against the
    *crystal* polyhedron (not an ideal shape). Label-free: for coordination numbers
    whose ideal-shape label is ambiguous (CN5 tbp<->square-pyramidal by Berry
    pseudorotation, CN8 antiprism<->dodecahedron), a binary best-shape match unfairly
    penalises a build that in fact reproduces the crystal geometry. This scores that
    reproduction fidelity regardless of which ideal either sphere is nearest to
    (0 = build angular geometry matches the crystal). Requires equal donor counts.
    Reflections are allowed (as in SHAPE): a mirror-image polyhedron scores 0."""
    Q = np.asarray(exp_dirs, float)
    P = np.asarray(build_dirs, float)
    if len(Q) != len(P) or len(Q) < 2:
        return float("nan")
    return continuous_shape_measure(P, Q, reflect=True)


def local_distance_matrix_rmsd(exp_donors, build_donors) -> float:
    """RMSD (A) between the two donor-donor distance matrices (metal-centred donor positions),
    over the donor pairing that minimises it. Order- and labelling-invariant; requires equal
    donor counts. MeCoBi's own site metric (not MetalloGen's D-MAE3, which is a mean ABSOLUTE
    error over every atom within three bonds of the metal).

    For CN <= 8 the pairing is exact (every permutation, vectorised). Above that it falls back
    to matching rows of sorted distances, a heuristic that can over-report the error."""
    E = np.asarray(exp_donors, float)
    B = np.asarray(build_donors, float)
    if len(E) != len(B) or len(E) < 2:
        return float("nan")
    DE = cdist(E, E)
    DB = cdist(B, B)
    iu = np.triu_indices(len(E), k=1)
    if len(E) <= _EXACT_MAX:
        perms = _permutations(len(E))
        diff = DB[perms[:, iu[0]], perms[:, iu[1]]] - DE[iu]
        return float(np.sqrt(np.min(np.mean(diff ** 2, axis=1))))
    # match build donors to exp donors: cost = row-sorted distance-vector diff
    cost = cdist(np.sort(DE, axis=1), np.sort(DB, axis=1))
    row, col = linear_sum_assignment(cost)
    DBm = DB[np.ix_(col, col)]
    return float(np.sqrt(np.mean((DE[iu] - DBm[iu]) ** 2)))


# ---------------------------------------------------------------------------
# coordination-sphere extraction + radial metrics
# ---------------------------------------------------------------------------
def parse_xyz(text: str):
    lines = text.splitlines()
    n = int(lines[0])
    syms, P = [], []
    for ln in lines[2:2 + n]:
        p = ln.split()
        syms.append(p[0]); P.append((float(p[1]), float(p[2]), float(p[3])))
    return syms, np.array(P)


def _heavy_donors(syms, P, mi, n_heavy: int, donor_idx=None):
    """The build's heavy donor atoms: ``donor_idx`` (from the molecular graph, see donor_map.py)
    when given and of the right size, else the ``n_heavy`` nearest non-H atoms."""
    if donor_idx is not None and len(donor_idx) == n_heavy:
        return list(donor_idx)
    cand = sorted(((float(np.linalg.norm(P[j] - P[mi])), j)
                   for j in range(len(syms)) if j != mi and syms[j] != "H"),
                  key=lambda t: t[0])[:n_heavy]
    return [j for _, j in cand]


def coordination_sphere(text: str, metal_sym: str, cn: int, n_h: int = 0, donor_idx=None):
    """Return (metal_xyz, donor_xyz[cn,3], donor_syms) for the build's cn donors.

    The heavy donors are ``donor_idx`` when given (graph-identified, donor_map.donor_indices),
    else the cn nearest non-H atoms. With ``n_h`` (a hydride-corrected complex, see hydrides.py)
    ``cn`` counts the hydrides too: the ``cn - n_h`` heavy donors plus the build's ``n_h``
    metal-only H, appended last. Returns fewer than ``cn`` donors when the build carries no
    hydride."""
    syms, P = parse_xyz(text)
    if metal_sym not in syms:
        return None
    mi = syms.index(metal_sym)
    idx = _heavy_donors(syms, P, mi, cn - n_h, donor_idx) + build_hydrides(syms, P, mi, n_h)
    return P[mi], P[idx], [syms[j] for j in idx]


# Covalent radii (A) for cap-ring detection; metals get a generous default.
_RCOV = {"H": 0.31, "C": 0.76, "N": 0.71, "O": 0.66, "P": 1.07, "S": 1.05,
         "Cl": 1.02, "Br": 1.20, "I": 1.39, "Si": 1.11}


# Max C-C distance (A) treated as one haptic pi-unit. Genuine haptic carbons
# (arene/Cp ~1.40, allyl ~1.40, alkene ~1.34, alkyne ~1.20) are all <=~1.45; a
# sigma-carbon donor (CO, carbene, alkyl) sits >=1.5 A from a neighbouring donor in
# a sane sphere, so this cleanly separates a pi-cluster from a crammed sigma-carbon.
_HAPTIC_CC_MAX = 1.5


def _haptic_clusters(syms, P, idx):
    """Partition the selected donor atoms ``idx`` into coordination SITES: a cluster
    of mutually bonded metal-bound CARBONS is ONE site (an eta 5/6-ring cap, or an
    eta2/eta3 pi-bond), an isolated donor is its own site.

    Only carbon-carbon pairs within :data:`_HAPTIC_CC_MAX` are merged -- that is
    exactly the haptic pi-carbon case. A normal chelate's donors are backbone-
    separated (>2 A apart) and stay distinct; a sigma-carbon donor crammed near a
    ring (a clashed build) is >1.5 A away and also stays distinct. Returns a list of
    atom-index lists."""
    parent = {i: i for i in idx}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    ids = list(idx)
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            i, j = ids[a], ids[b]
            if (syms[i] == "C" and syms[j] == "C"
                    and np.linalg.norm(P[i] - P[j]) <= _HAPTIC_CC_MAX):
                parent[find(i)] = find(j)
    clusters: dict = {}
    for i in idx:
        clusters.setdefault(find(i), []).append(i)
    return list(clusters.values())


def hapticity_collapsed_sphere(text: str, metal_sym: str, cn: int, n_h: int = 0,
                               donor_idx=None):
    """Like :func:`coordination_sphere`, but each metal-bound haptic cluster (an
    eta 5/6-ring cap OR an eta2/eta3 pi-bond) is replaced by ONE centroid vertex --
    matching MeCoBi's site model, where a cap or pi-site occupies a single site.

    Rationale (C1): a crystallographic CN counts every M-X contact, so an eta6-arene
    is 6 near-coplanar "donors" and an eta2-alkyne is 2; scoring those as independent
    polyhedron vertices inflates the shape measure (a piano-stool read as a 9-vertex
    solid; DILZED's eta2-alkyne CShM 11.2 vs 2.6 collapsed). Collapsing each haptic
    cluster to its centroid on BOTH crystal and build compares the coordination
    *sites* like-for-like. Chelate donors are backbone-separated (not directly bonded)
    so they remain distinct. Returns (metal_xyz, donor_xyz, donor_syms) with pseudo-
    element ``'X'`` marking a collapsed cluster; ``None`` if no metal. ``n_h`` as in
    :func:`coordination_sphere` (hydrides are their own sites, never collapsed), as is
    ``donor_idx``."""
    syms, P = parse_xyz(text)
    if metal_sym not in syms:
        return None
    mi = syms.index(metal_sym)
    idx = _heavy_donors(syms, P, mi, cn - n_h, donor_idx) + build_hydrides(syms, P, mi, n_h)
    donors, dsyms = [], []
    for cl in _haptic_clusters(syms, P, idx):
        if len(cl) >= 2:
            donors.append(P[cl].mean(axis=0)); dsyms.append("X")   # collapsed site
        else:
            donors.append(P[cl[0]]); dsyms.append(syms[cl[0]])
    return P[mi], np.array(donors), dsyms


def collapse_crystal_sphere(exp: dict):
    """Collapse haptic clusters in a CRYSTAL coordination sphere to centroid vertices,
    mirroring :func:`hapticity_collapsed_sphere` for the build side so the two are scored
    like-for-like (an eta5/6 cap is ONE site on both). Needs ``donor_elements``; merges only
    mutually bonded C-C (<= :data:`_HAPTIC_CC_MAX`), leaving backbone-separated chelate donors
    distinct. Returns ``(metal_xyz, donor_xyz)`` with each cap replaced by its centroid."""
    m = np.asarray(exp["metal_xyz"], dtype=float)
    D = np.asarray(exp["donors"], dtype=float)
    E = exp.get("donor_elements") or ["?"] * len(D)
    n = len(D)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if E[i] == "C" and E[j] == "C" and np.linalg.norm(D[i] - D[j]) <= _HAPTIC_CC_MAX:
                parent[find(i)] = find(j)
    clusters: dict = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(i)
    out = [D[c].mean(axis=0) if len(c) >= 2 else D[c[0]] for c in clusters.values()]
    return m, np.array(out)


def bond_rmsd(exp_donors, m_exp, build_donors, m_build) -> "tuple[float, float]":
    """(M-L bond RMSD, mean signed offset) over sorted bond lengths (A)."""
    be = sorted(float(np.linalg.norm(d - m_exp)) for d in exp_donors)
    bb = sorted(float(np.linalg.norm(d - m_build)) for d in build_donors)
    if len(be) != len(bb) or not be:
        return float("nan"), float("nan")
    diff = np.array(bb) - np.array(be)
    return float(np.sqrt(np.mean(diff ** 2))), float(np.mean(diff))
