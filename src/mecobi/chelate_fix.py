"""Assembly-time repair of conjugated 5-membered chelate rings (on by default; ``MECOBI_DECLASH=0`` turns it off).

A rigid ligand conformer placed on two sites can come out *inside-out*: HOLMEC's ene-diamide
had its C=C backbone 1.4 A from Ti, and one N-aryl of each ligand pointed where the N lone pair
belongs, so the Dipp groups of the two ligands interpenetrated and xtb failed. The repair works
on the raw stk placement, never moves a donor, and only touches rings that need it:

1. **Gate** (:func:`ring_offsets`): for each bidentate whose donors are joined by a two-atom
   backbone (M-D-X-X-D, a 5-membered ring), compare the centroid of D, X, X, D with the donor
   midpoint. A correct ring opens away from the metal (centroid ~0.5 A farther from M than the
   midpoint); a ring within ``gate`` of flat or inside-out is repaired.
2. **Ring plane**: rotate the ligand about its donor-donor axis so the backbone lies in the
   M-D-D plane on the far side of the metal (only for conjugated backbones, which are flat).
3. **Exo substituents**: at each sp2 donor of EVERY 5-ring chelate (bonded to M, a ring atom and
   one other heavy substituent), turn an endo substituent into the exo position, opposite the M
   and ring bonds (a ring can pass the gate yet carry an endo N-aryl: XUVZOE).
4. **Outer sphere**: rotate substituents about acyclic single bonds (ring atoms fixed) to clear
   inter- and intra-ligand clashes.
"""
from __future__ import annotations

from collections import deque

import numpy as np

GATE = 0.3            # A; ring centroid must sit this much farther from M than the donor midpoint
_STEP = 30            # deg grid for substituent torsions


def _graph(constructed, mi):
    adj: dict[int, set] = {}
    order: dict[frozenset, float] = {}
    for b in constructed.get_bonds():
        a1, a2 = b.get_atom1().get_id(), b.get_atom2().get_id()
        if mi in (a1, a2):
            continue
        adj.setdefault(a1, set()).add(a2)
        adj.setdefault(a2, set()).add(a1)
        order[frozenset((a1, a2))] = b.get_order()
    return adj, order


def _path(adj, a, b):
    prev = {a: None}
    q = deque([a])
    while q:
        u = q.popleft()
        if u == b:
            break
        for v in adj.get(u, ()):
            if v not in prev:
                prev[v] = u
                q.append(v)
    if b not in prev:
        return None
    p = [b]
    while prev[p[-1]] is not None:
        p.append(prev[p[-1]])
    return p[::-1]


def _side(adj, a, b):
    """Atoms reached from ``b`` without crossing back over the a-b bond."""
    seen = {b}
    q = deque([b])
    while q:
        u = q.popleft()
        for w in adj.get(u, ()):
            if w != a and w not in seen:
                seen.add(w)
                q.append(w)
    return seen


def _rot(Q, idx, origin, axis, deg):
    axis = axis / (np.linalg.norm(axis) or 1.0)
    t = np.radians(deg)
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    R = np.eye(3) + np.sin(t) * k + (1 - np.cos(t)) * (k @ k)
    out = Q.copy()
    out[idx] = (Q[idx] - origin) @ R.T + origin
    return out


def _context(constructed, metal_symbol):
    from . import optimize, pipeline

    mi, donors = pipeline._metal_bonded_donors(constructed, metal_symbol)
    if mi is None or not donors:
        return None
    P = np.asarray(constructed.get_position_matrix(), float)
    Z = np.array([a.get_atomic_number() for a in constructed.get_atoms()])
    bonds = [(b.get_atom1().get_id(), b.get_atom2().get_id()) for b in constructed.get_bonds()]
    comp = np.array(optimize._components_excluding(bonds, len(P), mi))
    adj, order = _graph(constructed, mi)
    by_lig: dict[int, list] = {}
    for d in donors:
        by_lig.setdefault(int(comp[d]), []).append(d)
    return mi, donors, P, Z, comp, adj, order, by_lig


def _five_rings(P, mi, adj, order, by_lig, Z=None):
    """[(ligand, donors, path, offset, conjugated)] for each 5-membered chelate ring."""
    out = []
    for lig, ds in by_lig.items():
        if len(ds) != 2:
            continue
        p = _path(adj, ds[0], ds[1])
        if not p or len(p) != 4:
            continue
        if Z is not None and any(Z[i] not in (6, 7) for i in p[1:3]):
            # backbone must be C/N (ene-diamide, alpha-diimine, BIAN, iminopyridine, oxime...):
            # VIWCEL's Se=P-N-P=Se "ring" ran through P and flattening it broke xtb.
            continue
        cen = P[p].mean(axis=0)
        mid = (P[ds[0]] + P[ds[1]]) / 2
        off = float(np.linalg.norm(cen - P[mi]) - np.linalg.norm(mid - P[mi]))
        conj = any(order.get(frozenset((p[i], p[i + 1])), 1) != 1 for i in range(3))
        out.append((lig, ds, p, off, conj))
    return out


def ring_offsets(constructed, metal_symbol) -> list:
    """Centroid-minus-midpoint offset (A) of each 5-membered chelate ring; < 0 = inside-out."""
    ctx = _context(constructed, metal_symbol)
    if ctx is None:
        return []
    mi, donors, P, Z, comp, adj, order, by_lig = ctx
    return [round(r[3], 2) for r in _five_rings(P, mi, adj, order, by_lig, Z)]


def n_inside_out(constructed, metal_symbol) -> int:
    return sum(1 for off in ring_offsets(constructed, metal_symbol) if off < 0)


def repair_chelates(constructed, metal_symbol, gate: float = GATE, passes: int = 3,
                    metal_ox: "int | None" = None):
    """Gate, flatten and exo-correct 5-ring chelates, then de-clash substituent torsions.

    Returns ``(constructed_or_copy, report)``; ``report["changed"]`` is False when nothing moved.
    Donors and the metal never move."""
    ctx = _context(constructed, metal_symbol)
    if ctx is None:
        return constructed, {"changed": False}
    mi, donors, P, Z, comp, adj, order, by_lig = ctx
    dset = set(donors)
    report = {"changed": False, "rings_fixed": 0, "exo_fixed": 0, "torsions": 0}
    fixed_rings: set = set()

    for lig, ds, p, off, conj in _five_rings(P, mi, adj, order, by_lig, Z):
        if off < gate and conj:
            a, b = P[ds[0]], P[ds[1]]
            axis = (b - a) / np.linalg.norm(b - a)
            mid = (P[p[1]] + P[p[2]]) / 2
            u = (mid - a) - ((mid - a) @ axis) * axis
            v = -((P[mi] - a) - ((P[mi] - a) @ axis) * axis)
            if np.linalg.norm(u) > 1e-6 and np.linalg.norm(v) > 1e-6:
                u, v = u / np.linalg.norm(u), v / np.linalg.norm(v)
                ang = float(np.degrees(np.arctan2(np.cross(u, v) @ axis, u @ v)))
                P = _rot(P, np.where(comp == lig)[0], a, axis, ang)
                fixed_rings.update(p)
                report["rings_fixed"] += 1
        # Exo check at EVERY 5-ring chelate donor, not only repaired rings: XUVZOE's BIAN ring is
        # the right way round (passes the centroid gate) but one N-mesityl sat endo, folded onto Pt.
        for d, ring_nb in ((p[0], p[1]), (p[-1], p[-2])):
            subs = [n for n in adj.get(d, ()) if n != ring_nb and Z[n] != 1]
            if len(subs) != 1:
                continue
            sub = subs[0]
            uM = (P[mi] - P[d]) / np.linalg.norm(P[mi] - P[d])
            uR = (P[ring_nb] - P[d]) / np.linalg.norm(P[ring_nb] - P[d])
            want = -(uM + uR)
            if np.linalg.norm(want) < 1e-6:
                continue
            want /= np.linalg.norm(want)
            cur = (P[sub] - P[d]) / np.linalg.norm(P[sub] - P[d])
            if cur @ want > 0.9:                  # already exo (within ~25 deg)
                continue
            ax = np.cross(cur, want)
            if np.linalg.norm(ax) < 1e-6:
                continue
            deg = float(np.degrees(np.arctan2(np.linalg.norm(ax), cur @ want)))
            P = _rot(P, np.array(sorted(_side(adj, d, sub)), dtype=int), P[d], ax, deg)
            fixed_rings.update(p)
            report["exo_fixed"] += 1

    # outer-sphere torsions
    heavy = [int(i) for i in np.where((Z != 1) & (comp >= 0))[0]]
    near: dict[int, set] = {}
    for i in heavy:                                   # atoms within 3 bonds (excluded from intra)
        dist = {i: 0}
        q = deque([i])
        while q:
            x = q.popleft()
            if dist[x] >= 3:
                continue
            for w in adj.get(x, ()):
                if w not in dist:
                    dist[w] = dist[x] + 1
                    q.append(w)
        near[i] = set(dist)
    inter, intra = [], []
    for k, i in enumerate(heavy):
        for j in heavy[k + 1:]:
            if comp[i] != comp[j]:
                inter.append((i, j))
            elif j not in near[i]:
                intra.append((i, j))
    pe = np.array(inter, dtype=int).reshape(-1, 2)
    pa = np.array(intra, dtype=int).reshape(-1, 2)
    nondonor = np.array([i for i in heavy if i not in dset], dtype=int)

    def score(Q):
        s = 0.0
        if len(pe):
            s += (np.clip(3.2 - np.linalg.norm(Q[pe[:, 0]] - Q[pe[:, 1]], axis=1), 0, None) ** 2).sum()
        if len(pa):
            s += (np.clip(2.9 - np.linalg.norm(Q[pa[:, 0]] - Q[pa[:, 1]], axis=1), 0, None) ** 2).sum()
        if len(nondonor):
            r = np.linalg.norm(Q[nondonor] - Q[mi], axis=1)
            s += 25.0 * (np.clip(2.6 - r, 0, None) ** 2).sum()
        return float(s)

    rot_bonds = []
    for fb, o in order.items():
        a, b = tuple(fb)
        if o != 1 or Z[a] == 1 or Z[b] == 1:
            continue
        sb, sa = _side(adj, a, b), _side(adj, b, a)
        if a in sb:                                   # ring bond
            continue
        for nr, far, fs in ((a, b, sb), (b, a, sa)):
            if fs & dset or fs & fixed_rings or nr == mi:
                continue
            if not any(Z[k] != 1 for k in fs if k != far):
                continue
            rot_bonds.append((nr, far, np.array(sorted(fs), dtype=int)))
    best = start = score(P)
    for _ in range(passes):
        improved = False
        for nr, far, idx in rot_bonds:
            cand = [(score(Q), Q) for deg in range(_STEP, 360, _STEP)
                    for Q in (_rot(P, idx, P[far], P[far] - P[nr], deg),)]
            sc, Q = min(cand, key=lambda c: c[0])
            if sc < best - 1e-6:
                best, P, improved = sc, Q, True
                report["torsions"] += 1
        if not improved:
            break
    report["changed"] = bool(report["rings_fixed"] or report["exo_fixed"] or best < start - 1e-6)
    if not report["changed"]:
        return constructed, report
    # The raw placement seats single-atom ligands far too close (a halide at 1.25 A); the restraint
    # then reads that as a genuine short multiple bond and holds it (ALAREK Ni-Br, EBANUS Ir-Cl,
    # IGOTIH Pd-Br ended ~1.8 A). Push each squeezed monodentate out along its M-D line to the
    # reference length; a terminal oxo/nitrido (O/N with no other neighbour) is really short.
    from . import optimize

    atoms = list(constructed.get_atoms())
    msym = atoms[mi].__class__.__name__
    for lig, ds in by_lig.items():
        if len(ds) != 1:
            continue
        d = ds[0]
        el = atoms[d].__class__.__name__
        if el in ("O", "N") and not [n for n in adj.get(d, ()) if Z[n] != 1]:
            continue
        ref = optimize._ml_target(msym, metal_ox, el, len(donors)) if metal_ox is not None else None
        if ref is None:
            rm, rd = optimize._cov_radius(msym), optimize._cov_radius(el)
            ref = (rm + rd) if rm and rd else None
        r = float(np.linalg.norm(P[d] - P[mi]))
        if ref is None or r >= 0.85 * ref or r < 1e-6:
            continue
        shift = (P[d] - P[mi]) / r * (ref - r)
        idx = np.where(comp == lig)[0]
        P[idx] = P[idx] + shift
        report["unsqueezed"] = report.get("unsqueezed", 0) + 1
    return constructed.with_position_matrix(P), report
