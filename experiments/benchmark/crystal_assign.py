"""Deterministic geometry + isomer (site-map) assignment straight from a crystal CIF.

Replaces the enumerate-and-select "oracle" (RMSD / c-kmRMSD trial and error) with a
direct read of the crystal:

  1. GEOMETRY  -- continuous shape measure (metrics.best_shape / CShM) of the crystal's
     donor directions against MeCoBi's *buildable* ideal polyhedra; assign the closest
     one (nearest-buildable v1: a real trigonal-prismatic CN6 maps to octahedral, flagged
     via ``geom_ambiguous`` / the runner-up CShM).
  2. SITE MAP  -- align the geometry's canonical SITE_VECTORS (invariant 7, the numbering
     shared with the 3D scene) to the crystal donor directions (Kabsch + Kuhn-Munkres),
     giving donor -> site id. Group donors into ligands by crystal connectivity
     (flood-fill, never crossing the metal) and match each ligand component to a bundle
     ligand index by (denticity, donor-element multiset). The result is the mode-3 isomer
     notation string ``"0:1;1:0,2,3,4,5"`` that ``isomers.parse_topology_spec`` +
     ``pipeline.build_complex(isomers_override=[spec])`` build directly -- no enumeration.

Ligands of denticity >=4 are outside the site model (``StereoNotSupported``); those
complexes get ``site_map=None`` + ``status="geometry_only"`` (build with the geometry's
default isomer). numpy + scipy + the local cif_geometry/extract_cores parsers; the site
model is imported from mecobi (no xtb, no pydentate).
"""
from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np
from rdkit import Chem
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

from cif_geometry import _cell_and_atoms
from extract_cores import _TOL, rcov

_GRAPH_RCUT = 10.0  # A: expand crystal atoms within this of the metal (chelate backbones)


def _unit(V):
    n = np.linalg.norm(V, axis=1, keepdims=True)
    return V / np.where(n == 0, 1.0, n)


def _kabsch(P, Q):
    """R minimising |Q - P R^T| (both centred / metal-origin, matched order)."""
    U, _, Vt = np.linalg.svd(P.T @ Q)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    return Vt.T @ np.diag([1.0, 1.0, d]) @ U.T


# ---------------------------------------------------------------------------
# 1. geometry
# ---------------------------------------------------------------------------
def assign_geometry(donor_dirs, cn: int, ambiguous_tol: float = 2.5, lone_pair: bool = False):
    """Closest buildable ideal polyhedron to the crystal donor directions.

    Returns ``{geometry, cshm, runner_up, geom_ambiguous, lone_pair, all}`` or ``None`` if the
    CN is unsupported / the donor count is wrong. ``geom_ambiguous`` marks a near-degenerate
    call (runner-up CShM within ``ambiguous_tol`` -- the CN5 tbp<->spy, CN8 antiprism<->dodeca
    ties).

    ``lone_pair`` (a stereo-active ns² main-group lone pair, e.g. Bi(III)/Sn(II)/Pb(II) at
    CN5) overrides the pure-CShM pick to **square_pyramidal**: the lone pair occupies the 6th
    octahedral vertex, so the 5 real donors are square-pyramidal even though their bare
    positions read closer to trigonal-bipyramidal by shape measure alone (the CShM cannot see
    the lone pair). EPAQOE/MOFGEU are exactly this case.
    """
    from metrics import _IDEAL, continuous_shape_measure

    cands = _IDEAL.get(cn)
    if not cands or len(donor_dirs) != cn:
        return None
    scored = sorted(((name, continuous_shape_measure(donor_dirs, vecs))
                     for name, vecs in cands.items()), key=lambda t: t[1])
    best_name, best_cshm = scored[0]
    lp_applied = False
    if lone_pair and cn == 5 and "square_pyramidal" in cands and best_name != "square_pyramidal":
        best_name = "square_pyramidal"
        best_cshm = dict(scored)["square_pyramidal"]
        lp_applied = True
    runner = next((v for n, v in scored if n != best_name), None)
    return {
        "geometry": best_name,
        "cshm": None if np.isnan(best_cshm) else round(float(best_cshm), 3),
        "runner_up": None if runner is None or np.isnan(runner) else round(float(runner), 3),
        "geom_ambiguous": bool(not lp_applied and runner is not None and not np.isnan(runner)
                               and (runner - best_cshm) < ambiguous_tol),
        "lone_pair": lp_applied,
        "all": {n: (None if np.isnan(v) else round(float(v), 3)) for n, v in scored},
    }


# ---------------------------------------------------------------------------
# 2. donor -> site id
# ---------------------------------------------------------------------------
def _random_rotation(rng):
    """Uniformly-random proper rotation (QR of a Gaussian matrix, det forced +1)."""
    Q, R = np.linalg.qr(rng.standard_normal((3, 3)))
    Q *= np.sign(np.diag(R))
    if np.linalg.det(Q) < 0:
        Q[:, 0] = -Q[:, 0]
    return Q


def map_donors_to_sites(donor_dirs, geometry, iters: int = 30, restarts: int = 10):
    """Assign each crystal donor to a canonical site id of ``geometry`` (invariant 7).

    Aligns the geometry's numbered site directions to the crystal donor directions by iterated
    Kuhn-Munkres <-> Kabsch, then reads off the optimal donor->site bijection. The alignment is
    restarted from several random initial rotations and the lowest-residual one is kept: a
    single identity-seeded run can converge to a rotated basin that mis-pairs donors and
    SCRAMBLES the crystal's trans relationships (e.g. an amine that is trans to a chloride in
    the crystal landing on a cis site). The global-best alignment preserves those
    donor-donor angular relationships -- which is what fixes which ligand is trans to which
    (HOVWUL, GERYUY). Returns ``site_of[i]`` (site id for donor ``i``), or ``None`` if the
    site count does not match the donor count.
    """
    from mecobi.assembly import sites as _sites
    from mecobi.model import Geometry

    geom = geometry if isinstance(geometry, Geometry) else Geometry(geometry)
    site_pos = np.asarray(_sites.site_positions(geom), float)
    if len(site_pos) != len(donor_dirs):
        return None
    S = _unit(site_pos)
    Q = _unit(np.asarray(donor_dirs, float))
    rng = np.random.default_rng(0)  # fixed seed: deterministic
    best_cost, best_site_of = float("inf"), None
    for attempt in range(max(1, restarts)):
        R = np.eye(3) if attempt == 0 else _random_rotation(rng)
        for _ in range(iters):
            row, col = linear_sum_assignment(cdist(Q, S @ R.T))
            R = _kabsch(S[col], Q[row])
        cost_mat = cdist(Q, S @ R.T)
        row, col = linear_sum_assignment(cost_mat)
        cost = float(cost_mat[row, col].sum())
        if cost < best_cost:
            site_of = [0] * len(Q)
            for r, c in zip(row, col):
                site_of[r] = int(c)
            best_cost, best_site_of = cost, site_of
    return best_site_of


# ---------------------------------------------------------------------------
# crystal graph: donors + which ligand (component) each belongs to
# ---------------------------------------------------------------------------
def crystal_donor_graph(cif_text, metal_sym, target_cn, h_rel=None, donor_elements=None):
    """Extract the crystal coordination sphere donor ATOMS grouped by ligand.

    Returns ``{"metal": xyz, "donors": [ {pos, elem, component}, ... ]}`` or ``None``
    (unparseable / fewer than ``target_cn`` neighbours). ``target_cn`` is the ATOM-space CN
    (bundle CN); the ``target_cn`` nearest non-H, non-same-metal atoms are taken (symmetry-
    expanded, deduped). ``component`` is a ligand id: two donors share it iff joined by a
    covalent-bond path through heavy ligand atoms that never passes through the metal (a
    chelate's donors share a component, trans monodentates do not). Haptic collapse (Cp ->
    1 site, each C=C -> 1) is NOT done here -- build_site_map collapses each ligand's donors
    into exactly the site count MeCoBi's structure perception gives (so the two never
    disagree), placing each site at the crystal centroid of its atoms.

    ``h_rel`` (hydride-corrected complex, see hydrides.py): the located hydrides' M->H vectors.
    ``target_cn`` then counts them -- the ``target_cn - len(h_rel)`` nearest heavy atoms are
    taken and each hydride is appended as a donor of element ``H`` in a component of its own.

    ``donor_elements`` (the bundle's declared donor atoms): instead of the nearest heavy atoms
    whatever their element, take for each declared heavy element that many nearest atoms of it,
    so a lost I/Cl donor is not replaced by a nearer backbone C (ICIHAF: N 2.11 A in place of
    Cl 2.64 A -> no site map). Declared H donors are left to ``h_rel``.
    """
    M, atoms, symops = _cell_and_atoms(cif_text)
    if M is None:
        return None
    elems, fracs = atoms
    metal_idx = [i for i, e in enumerate(elems) if e == metal_sym]
    if not metal_idx:
        return None
    mc = fracs[metal_idx[0]] @ M.T
    trans = [np.array([i, j, k]) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)]
    xyz_all, el_all = [], []
    for R, t in symops:
        g = fracs @ R.T + t
        for tr in trans:
            xyz_all.append((g + tr) @ M.T)
            el_all.extend(elems)
    IMG = np.vstack(xyz_all)
    IE = np.array(el_all)
    d = np.linalg.norm(IMG - mc, axis=1)
    loc = d <= _GRAPH_RCUT
    IMG, IE, d = IMG[loc], IE[loc], d[loc]
    # dedup symmetry-image duplicates by rounded position
    seen, keep = set(), []
    for j in range(len(IMG)):
        k = tuple(np.round(IMG[j], 1))
        if k not in seen:
            seen.add(k)
            keep.append(j)
    IMG, IE, d = IMG[keep], IE[keep], d[keep]

    cand = sorted((float(d[j]), j) for j in range(len(IMG))
                  if d[j] > 0.5 and IE[j] not in ("H", metal_sym))
    h_rel = [np.asarray(v, float) for v in (h_rel or [])]
    n_heavy = target_cn - len(h_rel)
    if donor_elements:
        heavy_decl = Counter(e for e in donor_elements if e != "H")
        donor_idx = []
        for el, n in heavy_decl.items():
            pick = [j for _, j in cand if IE[j] == el][:n]
            if len(pick) < n:
                return None
            donor_idx += pick
        donor_idx.sort(key=lambda j: d[j])
    else:
        if len(cand) < n_heavy:
            return None
        donor_idx = [j for _, j in cand[:n_heavy]]

    # heavy ligand-atom graph (metal + H excluded): union-find over covalent contacts
    heavy = [j for j in range(len(IMG)) if IE[j] not in ("H", metal_sym)]
    parent = {j: j for j in heavy}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a in range(len(heavy)):
        ia = heavy[a]
        for b in range(a + 1, len(heavy)):
            ib = heavy[b]
            if np.linalg.norm(IMG[ia] - IMG[ib]) <= (rcov(IE[ia]) + rcov(IE[ib])) * _TOL:
                parent[find(ia)] = find(ib)

    roots = {find(j) for j in donor_idx}
    root_to_comp = {r: c for c, r in enumerate(sorted(roots))}
    donors = [{"pos": IMG[j], "elem": str(IE[j]), "component": root_to_comp[find(j)], "atom": int(j)}
              for j in donor_idx]

    # Per-ligand heavy-atom FRAGMENT (every heavy atom sharing a donor's component) + its
    # bonds -- the graph matched against the SMILES for the exact crystal<->SMILES atom map.
    frags: dict[int, dict] = {c: {"gidx": [], "elems": [], "pos": []}
                              for c in root_to_comp.values()}
    for j in heavy:
        r = find(j)
        if r in root_to_comp:
            f = frags[root_to_comp[r]]
            f["gidx"].append(int(j)); f["elems"].append(str(IE[j])); f["pos"].append(IMG[j])
    for f in frags.values():
        gl = f["gidx"]
        f["bonds"] = [(a, b) for a in range(len(gl)) for b in range(a + 1, len(gl))
                      if np.linalg.norm(IMG[gl[a]] - IMG[gl[b]])
                      <= (rcov(IE[gl[a]]) + rcov(IE[gl[b]])) * _TOL]
    for k, v in enumerate(h_rel):          # located hydrides: one single-atom ligand each
        comp = len(root_to_comp) + k
        donors.append({"pos": mc + v, "elem": "H", "component": comp, "atom": -(k + 1)})
        frags[comp] = {"gidx": [], "elems": [], "pos": [], "bonds": []}
    return {"metal": mc, "donors": donors, "fragments": frags}


# ---------------------------------------------------------------------------
# 3. full site map
# ---------------------------------------------------------------------------
def _collapse_to_k(P, k):
    """Merge ``len(P)`` donor positions into exactly ``k`` site centroids (agglomerative:
    fuse the two closest clusters until ``k`` remain). An eta-ring's carbons fuse into one
    cap centroid, a diene's two C=C into two -- matching the ``k`` MeCoBi's structure
    perception assigns, but placed at the CRYSTAL centroids. Returns ``(centroids, groups)``
    where ``groups[i]`` are the atom indices (into ``P``) fused into centroid ``i``."""
    groups = [[i] for i in range(len(P))]
    cents = [P[i].astype(float) for i in range(len(P))]
    while len(groups) > k:
        best = (float("inf"), 0, 1)
        for a in range(len(groups)):
            for b in range(a + 1, len(groups)):
                d = float(np.linalg.norm(cents[a] - cents[b]))
                if d < best[0]:
                    best = (d, a, b)
        _, a, b = best
        groups[a] += groups[b]
        cents[a] = P[groups[a]].mean(axis=0)
        del groups[b], cents[b]
    return [np.asarray(c, float) for c in cents], groups


def _rank_ascending(vals):
    """Dense rank (0 = smallest) of each value, ties share the sorted position."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0] * len(vals)
    for pos, i in enumerate(order):
        r[i] = pos
    return r


def _order_ligand_sites(smiles, donor_idx, site_elems, site_vecs, site_ids):
    """Order ``site_ids`` so ``tuple[k]`` is the site of the ligand's k-th SMILES donor
    (``effective_donors`` order) -- ``donor k -> site tuple[k]``, the convention the site
    model builds by. Each crystal site (one donor atom each, non-haptic) is matched to a
    SMILES donor by ELEMENT plus a CENTRALITY signature: topological (sum of bond distances
    to the ligand's other donors) on the SMILES side, angular (largest metal-donor-donor
    angle to another donor of the same ligand; a meridional centre is ~cis to both ends so
    its max angle is small, an end is ~trans to the other end so its max angle is ~180) on
    the crystal side. This pins an asymmetric chelate's donor directions and a meridional
    tridentate's central donor. Falls back to sorted order if the SMILES won't parse."""
    n = len(site_ids)
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None or len(donor_idx) != n:
        return tuple(sorted(site_ids))
    dm = Chem.GetDistanceMatrix(mol)
    s_el = [mol.GetAtomWithIdx(a).GetSymbol() for a in donor_idx]
    s_cent = [sum(dm[a][b] for b in donor_idx if b != a) for a in donor_idx]

    def ang(u, w):
        c = float(np.dot(u, w)) / (np.linalg.norm(u) * np.linalg.norm(w) + 1e-9)
        return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))

    c_cent = [max((ang(site_vecs[j], site_vecs[k]) for k in range(n) if k != j), default=0.0)
              for j in range(n)]
    sr, cr = _rank_ascending(s_cent), _rank_ascending(c_cent)
    cost = np.array([[(0 if s_el[i] == site_elems[j] else 10) + abs(sr[i] - cr[j])
                      for j in range(n)] for i in range(n)], float)
    row, col = linear_sum_assignment(cost)
    order = [0] * n
    for i, j in zip(row, col):
        order[i] = site_ids[j]
    return tuple(order)


def _fragment_to_mol(frag):
    """RDKit mol (single bonds, no sanitize) from a crystal ligand fragment's heavy atoms."""
    from rdkit.Chem import Atom, BondType, RWMol

    m = RWMol()
    for el in frag["elems"]:
        m.AddAtom(Atom(el))
    for i, j in frag["bonds"]:
        m.AddBond(i, j, BondType.SINGLE)
    return m.GetMol()


def _skeleton(mol):
    """Connectivity-only copy: every bond SINGLE, aromaticity cleared -- so a single-bond
    crystal fragment matches an aromatic/multiple-bond SMILES by graph + elements alone."""
    rw = Chem.RWMol(mol)
    for b in rw.GetBonds():
        b.SetBondType(Chem.BondType.SINGLE)
        b.SetIsAromatic(False)
    for a in rw.GetAtoms():
        a.SetIsAromatic(False)
    return rw.GetMol()


def _substructure_donor_order(frag, smiles, donor_idx, atom_to_site):
    """Site tuple in SMILES-donor order via an EXACT crystal-atom <-> SMILES-atom match, or
    ``None`` if it fails. Builds the crystal fragment as a graph and finds it inside the
    SMILES skeleton (``GetSubstructMatch``), giving each crystal atom its SMILES index; then
    reads each SMILES donor's site from ``atom_to_site`` (global crystal atom idx -> site id).
    Robust to a truncated fragment (crystal is a sub-pattern of the SMILES)."""
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return None
    try:
        cq = _fragment_to_mol(frag)
        match = _skeleton(mol).GetSubstructMatch(cq)  # crystal-local -> SMILES atom idx
    except Exception:  # noqa: BLE001
        return None
    if not match or len(match) != len(frag["gidx"]):
        return None
    smiles_to_g = {match[i]: frag["gidx"][i] for i in range(len(match))}
    order = []
    for d in donor_idx:  # effective_donors order -> donor k
        g = smiles_to_g.get(d)
        if g is None or g not in atom_to_site:
            return None
        order.append(atom_to_site[g])
    return tuple(order)


def _canonicalize_equiv_sites(order, smiles, donor_idx):
    """Give canonically-equivalent donors a deterministic site order (their sites sorted
    ascending), leaving distinct donors where the match put them. Symmetric donors (e.g. the
    two ends of a terpyridine, both N,O arms of a salen) are interchangeable, so pinning them
    by an arbitrary substructure permutation only adds build noise; distinct donors (a
    terpy's central N, an asymmetric chelate's two arms) keep their matched placement."""
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return order
    ranks = list(Chem.CanonicalRankAtoms(mol, breakTies=False))
    groups: dict = defaultdict(list)
    for k, a in enumerate(donor_idx):
        groups[ranks[a]].append(k)
    final = list(order)
    for ks in groups.values():
        if len(ks) > 1:
            for k, s in zip(sorted(ks), sorted(final[k] for k in ks)):
                final[k] = s
    return tuple(final)


def _match_components_to_ligands(comp_elems, lig_specs):
    """Map each crystal component to a bundle ligand index by its raw donor-atom element
    multiset (crystal-derived; identical ligands are interchangeable). ``comp_elems``: list
    of sorted element tuples, one per component. ``lig_specs``: per bundle ligand
    ``(site_count, raw-elements, smiles, donor_idx)``. Returns ``{comp_index: lig_index}``
    or ``None``."""
    if len(comp_elems) != len(lig_specs):
        return None
    used = [False] * len(lig_specs)
    out: dict[int, int] = {}
    for ci, ce in enumerate(comp_elems):
        hit = next((l for l, sp in enumerate(lig_specs) if not used[l] and sp[1] == ce), None)
        if hit is None:  # relax to atom-count only (crystal vs SMILES element read can differ)
            hit = next((l for l, sp in enumerate(lig_specs)   # ... but never hydride <-> heavy
                        if not used[l] and len(sp[1]) == len(ce)
                        and (sp[1] == ("H",)) == (ce == ("H",))), None)
        if hit is None:
            return None
        used[hit] = True
        out[ci] = hit
    return out


def build_site_map(cif_text, metal_sym, atom_cn, lig_specs, lone_pair: bool = False,
                   h_rel=None, donor_elements=None):
    """Crystal CIF -> ``{geometry, site_cn, site_map, cshm, geom_ambiguous, status}``.

    ``lone_pair`` (stereo-active ns² cation) forces square-pyramidal at CN5 -- see
    :func:`assign_geometry`. ``h_rel``: located hydrides, see :func:`crystal_donor_graph`
    (``atom_cn`` and ``lig_specs`` must then include them).

    ``atom_cn`` : the bundle (atom-space) CN. ``lig_specs`` : per bundle ligand
    ``(site_count, sorted-raw-donor-element-tuple)`` in bundle order. ``site_count`` is how
    many coordination SITES the ligand occupies -- MeCoBi's structure-perceived denticity
    (Cp -> 1, diene -> 2), NOT pydentate; ``raw-elements`` are its donor ATOM elements
    (Cp -> 5x'C'). Each ligand's crystal donors are collapsed to exactly ``site_count`` sites
    (crystal centroids), so the SITE count always equals what the builder assembles -- no
    perception/crystal disagreement, no fallback. Geometry is read on the collapsed sites.

    ``site_map`` is the mode-3 notation string (or ``None``). ``status`` is ``ok`` for a
    valid buildable map, else ``geometry_only`` (components unmatched / chelate lands trans /
    unsupported site count), ``no_sphere``, ``no_geometry``.
    """
    ex = crystal_donor_graph(cif_text, metal_sym, atom_cn, h_rel, donor_elements)
    if ex is None:
        return {"status": "no_sphere"}
    mc = np.asarray(ex["metal"], float)
    donors = ex["donors"]
    comp_atoms: dict[int, list[int]] = defaultdict(list)
    for i, d in enumerate(donors):
        comp_atoms[d["component"]].append(i)
    comp_items = sorted(comp_atoms.items())  # (component id, [donor-list indices])
    comp_elems = [tuple(sorted(donors[i]["elem"] for i in idxs)) for _, idxs in comp_items]
    match = _match_components_to_ligands(comp_elems, lig_specs)

    # Collapse each component to k = its ligand's site count (crystal centroids). Track each
    # site's component + donor atom + element so a non-haptic ligand (one atom per site) can be
    # donor-ordered. Without a match we can't know k -> one site per atom (geometry read only).
    sites = []  # {"pos", "lig", "comp_id", "single", "elem", "atom"}
    for ci, (comp_id, idxs) in enumerate(comp_items):
        P = np.array([donors[i]["pos"] for i in idxs], float)
        lig = match[ci] if match is not None else None
        k = lig_specs[lig][0] if lig is not None else len(P)
        if k >= len(P):
            cents, groups = list(P), [[j] for j in range(len(P))]
        else:
            cents, groups = _collapse_to_k(P, k)
        for c, grp in zip(cents, groups):
            single = len(grp) == 1
            sites.append({"pos": np.asarray(c, float), "lig": lig, "comp_id": comp_id,
                          "single": single, "pts": P[grp],
                          "elem": donors[idxs[grp[0]]]["elem"] if single else "X",
                          "atom": donors[idxs[grp[0]]]["atom"] if single else None})

    dirs = _unit(np.array([s["pos"] for s in sites], float) - mc)
    site_cn = len(sites)
    g = assign_geometry(dirs, site_cn, lone_pair=lone_pair)
    if g is None:
        return {"status": "no_geometry", "site_cn": site_cn}
    out = {"geometry": g["geometry"], "cshm": g["cshm"], "runner_up": g["runner_up"],
           "geom_ambiguous": g["geom_ambiguous"], "lone_pair": g.get("lone_pair", False),
           "site_cn": site_cn, "site_map": None, "status": "geometry_only"}
    if match is None:
        return out
    site_of = map_donors_to_sites(dirs, g["geometry"])
    if site_of is None:
        return out
    # Per ligand, order its site tuple so donor k -> tuple[k] (site model convention). For a
    # non-haptic polydentate, pin the order with an EXACT crystal<->SMILES atom match
    # (substructure); fall back to the element+centrality heuristic if it fails, and to sorted
    # for haptic/monodentate ligands (where the order is symmetric or trivial).
    lig_site_idx: dict[int, list[int]] = defaultdict(list)
    for si, s in enumerate(sites):
        lig_site_idx[s["lig"]].append(si)
    assignment: dict[int, tuple[int, ...]] = {}
    for lig, sidx in lig_site_idx.items():
        ids = [site_of[si] for si in sidx]
        _k, _elems, smiles, donor_idx = lig_specs[lig]
        if len(sidx) >= 2 and all(sites[si]["single"] for si in sidx):
            frag = ex["fragments"].get(sites[sidx[0]]["comp_id"])
            atom_to_site = {sites[si]["atom"]: site_of[si] for si in sidx}
            ordered = (_substructure_donor_order(frag, smiles, donor_idx, atom_to_site)
                       if frag else None)
            if ordered is None:
                ordered = _order_ligand_sites(
                    smiles, donor_idx, [sites[si]["elem"] for si in sidx],
                    [sites[si]["pos"] - mc for si in sidx], ids)
            assignment[lig] = _canonicalize_equiv_sites(ordered, smiles, donor_idx)
        else:
            assignment[lig] = tuple(sorted(ids))

    # Only accept a map the site model validates (fills every site, chelate donors cis, no
    # collision). The enricher additionally build-checks it (relax=False) before keeping.
    try:
        from mecobi.assembly import sites as _sites
        from mecobi.model import Geometry
        _sites.validate_assignment(Geometry(g["geometry"]), [sp[0] for sp in lig_specs], assignment)
    except Exception:  # noqa: BLE001 -- any validation failure -> geometry-only fallback
        return out

    assignment = _orient_eta2_numbering(g["geometry"], sites, site_of, dirs, lig_site_idx,
                                        lig_specs, assignment)
    out["site_map"] = ";".join(
        f"{lig}:{','.join(str(s) for s in assignment[lig])}" for lig in sorted(assignment))
    out["status"] = "ok"
    return out


def _orient_eta2_numbering(geometry, sites, site_of, dirs, lig_site_idx, lig_specs, assignment):
    """Among the equivalent site numberings of this isomer (the geometry's proper rotations),
    pick the one in which MeCoBi's eta2 rule reproduces the crystal: a side-on alkene/alkyne is
    built with its C=C / C#C bond along ``sites.eta2_axis(geometry, its site)``, so the numbering
    decides whether the bond lies along one axis or stands 90 deg off (DILZED: lying along the
    OC-Mo-NCMe axis in the crystal, built standing). The isomer itself is unchanged -- only the
    labels move. Returns the assignment relabelled, or as given when there is no lone eta2
    ligand or no numbering does better."""
    try:
        from mecobi.assembly import sites as _sites
        from mecobi.model import Geometry

        geom = Geometry(geometry)
        eta2 = []                               # (site index, crystal bond unit vector)
        for lig, sidx in lig_site_idx.items():
            if len(sidx) != 1 or lig is None or lig_specs[lig][0] != 1:
                continue
            pts = np.asarray(sites[sidx[0]]["pts"], float)
            if len(pts) != 2:
                continue
            cc = pts[1] - pts[0]
            n = float(np.linalg.norm(cc))
            if n > 1e-6:
                eta2.append((sidx[0], cc / n))
        if not eta2:
            return assignment
        ideal = _unit(np.array(_sites.site_positions(geom, len(sites)), float))
        ids = [int(site_of[si]) for si in range(len(sites))]

        def score(perm):
            new_ids = [perm[i] for i in ids]
            R = _kabsch(ideal[new_ids], dirs)     # ideal frame -> crystal frame
            tot = 0.0
            for si, cc in eta2:
                want = _sites.eta2_axis(geom, new_ids[si], len(sites))
                if want is None:
                    return None
                tot += abs(float((R @ want) @ cc))
            return tot / len(eta2)

        best_perm, best = None, score(tuple(range(len(sites))))
        if best is None:
            return assignment
        for perm in _sites.proper_rotation_site_perms(geom):
            sc = score(perm)
            if sc is not None and sc > best + 0.05:
                best_perm, best = perm, sc
        if best_perm is None:
            return assignment
        # donor k of a ligand keeps its order: only the site labels are permuted
        relabelled = {lig: tuple(best_perm[t] for t in tup) for lig, tup in assignment.items()}
        _sites.validate_assignment(geom, [sp[0] for sp in lig_specs], relabelled)
        return relabelled
    except Exception:  # noqa: BLE001 -- keep the validated map on any failure
        return assignment
