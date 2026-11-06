"""Core kmRMSD (c-kmRMSD) -- Architector's structure-comparison metric: RMSD over the region
within two graph hops of the metal, with the two atom sets matched by a Kuhn-Munkres (Hungarian)
assignment *within each element* and superposed by Kabsch.

Two pieces:
  * build_core_from_xyz(xyz, metal, cn) -> the depth-2 core of a *built* structure (metal +
    cn nearest non-H donors + heavy donor-neighbours), same definition extract_cores.py uses on
    the crystal, so build and crystal cores are directly comparable.
  * ckmrmsd(crystal_core, build_core) -> (rmsd_A, n_matched): element-wise Hungarian matching
    (handles small count mismatches by matching min per element) iterated with Kabsch about the
    shared metal origin, restarted from 300 random rotations (and their mirror images) as in
    Architector so the result does not depend on how the build happens to be oriented.

Differences from Architector's definition that remain: H are dropped (except located hydrides),
the core is found from interatomic distances rather than the molecular graph, and a composition
mismatch is matched partially (report ``n_matched`` vs ``core_size``) instead of returning 1000.

Reference cores come from benchmark_cores.json.gz (extract_cores.py). numpy + scipy only.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

from extract_cores import rcov, _TOL
from hydrides import build_hydrides, n_in_core, strip_core
from metrics import parse_xyz


def build_core_like(crystal_core, text: str, metal_sym: str, donor_idx=None):
    """``(crystal core, build core)`` ready for :func:`ckmrmsd`, hydride-aware: when the crystal
    core carries hydrides and the build has them too, both keep them; a build without hydrides
    (made from the uncorrected inputs) is compared on the heavy donors alone. ``donor_idx``: the
    build's graph-identified heavy donors (donor_map.donor_indices), else the nearest atoms."""
    n_h = n_in_core(crystal_core)
    cn = len(crystal_core["donors"])
    bc = build_core_from_xyz(text, metal_sym, cn, n_h, donor_idx)
    if n_h and (bc is None or n_in_core(bc) < n_h):
        crystal_core = strip_core(crystal_core)
        bc = build_core_from_xyz(text, metal_sym, cn - n_h, donor_idx=donor_idx)
    return crystal_core, bc


def build_core_from_xyz(text: str, metal_sym: str, cn: int, n_h: int = 0, donor_idx=None):
    """metal + cn donors + heavy donor-neighbours (depth 2) of a built .xyz.

    The heavy donors are ``donor_idx`` when given and of the right size (graph-identified, see
    donor_map.py), else the nearest non-H atoms. With ``n_h`` (hydride-corrected complex, see
    hydrides.py) ``cn`` counts the hydrides: the ``cn - n_h`` heavy donors plus the build's
    metal-only H, appended to the donor shell (a build without hydrides just gets the heavy
    donors)."""
    syms, P = parse_xyz(text)
    if metal_sym not in syms:
        return None
    mi = syms.index(metal_sym)
    mc = P[mi]
    d = np.linalg.norm(P - mc, axis=1)
    cand = sorted((float(d[j]), j) for j in range(len(syms))
                  if j != mi and syms[j] not in ("H", metal_sym))
    if len(cand) < cn - n_h:
        return None
    heavy = (list(donor_idx) if donor_idx is not None and len(donor_idx) == cn - n_h
             else [j for _, j in cand[:cn - n_h]])
    donor_idx = heavy + build_hydrides(syms, P, mi, n_h)
    dset = set(donor_idx)
    added, depth2 = set(), []
    for dj in donor_idx:
        dp, de = P[dj], syms[dj]
        dd = np.linalg.norm(P - dp, axis=1)
        for j in range(len(syms)):
            ej = syms[j]
            if ej == "H" or j == mi or j in dset or j in added:
                continue
            if de != "H" and 0.4 < dd[j] <= (rcov(ej) + rcov(de)) * _TOL:
                added.add(j)
                depth2.append({"el": ej, "xyz": P[j].tolist()})
    return {
        "metal": {"el": metal_sym, "xyz": mc.tolist()},
        "donors": [{"el": syms[j], "xyz": P[j].tolist()} for j in donor_idx],
        "depth2": depth2,
    }


def _atoms(core):
    """(elements, positions metal-centred) for metal + donors + depth2."""
    atoms = [core["metal"]] + core["donors"] + core["depth2"]
    els = [a["el"] for a in atoms]
    P = np.asarray([a["xyz"] for a in atoms], float) - np.asarray(core["metal"]["xyz"], float)
    return els, P


def _kabsch(P, Q):
    """R minimising |Q - P R^T| (both metal-centred, matched order)."""
    U, _, Vt = np.linalg.svd(P.T @ Q)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    return Vt.T @ np.diag([1.0, 1.0, d]) @ U.T


def core_size(core) -> int:
    """Atoms in a core (metal + donors + depth-2): compare with ``n_matched`` from :func:`ckmrmsd`
    -- fewer matched atoms than the crystal core means the build's core is missing atoms or has
    the wrong composition, which the RMSD over the matched atoms alone does not see."""
    return 1 + len(core["donors"]) + len(core["depth2"])


_N_STARTS = 300                     # random starting rotations (Architector: 300)
_MIRROR = np.diag([-1.0, 1.0, 1.0])  # each start also tried on the mirrored build (x -> -x)


def _refine(CP, BP, groups, R, iters):
    """Hungarian-per-element <-> Kabsch from rotation ``R`` until the matching stops changing.
    Returns (rmsd, crystal indices, build indices) of the matched pairs."""
    prev = None
    for _ in range(iters):
        BR = BP @ R.T
        cpairs, bpairs = [], []
        for cidx, bidx in groups:
            row, col = linear_sum_assignment(cdist(CP[cidx], BR[bidx]))
            cpairs.extend(cidx[row]); bpairs.extend(bidx[col])
        cm, bm = np.array(cpairs), np.array(bpairs)
        R = _kabsch(BP[bm], CP[cm])
        if prev is not None and np.array_equal(bm, prev):
            break
        prev = bm
    resid = CP[cm] - BP[bm] @ R.T
    return float(np.sqrt(np.mean(np.sum(resid ** 2, axis=1)))), cm, bm


def best_match(ce, CP, be, BP, iters: int = 10, n_starts: int = _N_STARTS, mirror: bool = True):
    """``(rmsd, crystal idx, build idx)``: the element-wise atom correspondence of minimum RMSD
    over ``n_starts`` random starting rotations (each also on the mirrored build). Positions are
    metal-centred; ``None`` when no element is shared."""
    from scipy.spatial.transform import Rotation

    ci, bi = defaultdict(list), defaultdict(list)
    for i, e in enumerate(ce):
        ci[e].append(i)
    for i, e in enumerate(be):
        bi[e].append(i)
    groups = [(np.array(ci[e]), np.array(bi[e])) for e in ci if e in bi]
    if not groups:
        return None
    starts = [np.eye(3)]
    if n_starts > 1:
        starts += list(Rotation.random(n_starts - 1, random_state=0).as_matrix())
    best = None
    for M in ([np.eye(3), _MIRROR] if mirror else [np.eye(3)]):
        BPm = BP @ M.T
        for R0 in starts:
            res = _refine(CP, BPm, groups, R0, iters)
            if best is None or res[0] < best[0]:
                best = res
            if best[0] < 1e-6:
                return best
    return best


def ckmrmsd(crystal_core, build_core, iters: int = 10, n_starts: int = _N_STARTS,
            mirror: bool = True):
    """(c-kmRMSD in A, n_matched atoms). Element-wise Hungarian assignment (min count per
    element) iterated with Kabsch about the metal. nan if nothing matches.

    The assignment <-> Kabsch iteration is a LOCAL optimiser: started from one orientation it
    sticks in a wrong-permutation basin whenever the two cores are related by a large rotation
    (a crystal core scored against itself rotated gave 1.4-2.1 A instead of 0). As Architector
    does, it is therefore restarted from ``n_starts`` random rotations (fixed seed: deterministic),
    each also on the mirrored build (``mirror``), and the minimum is kept. ``n_matched`` counts
    the matched atoms; compare it with :func:`core_size` of the crystal core (Architector instead
    returns a sentinel when the compositions differ)."""
    ce, CP = _atoms(crystal_core)
    be, BP = _atoms(build_core)
    res = best_match(ce, CP, be, BP, iters, n_starts, mirror)
    if res is None:
        return float("nan"), 0
    return res[0], len(res[1])
