"""Depth-N c-kmRMSD ("N-hop"): extend Architector's core-kmRMSD one graph hop further.

The shipped c-kmRMSD (ckmrmsd.py) scores the depth-2 core (metal + donors + donor-neighbours).
This computes the SAME Kuhn-Munkres-matched Kabsch RMSD over a deeper core -- default depth 3
(adds the neighbours-of-neighbours) -- for a built .xyz against the crystal core extracted from
the CIF, reusing extract_cores' CIF machinery so the two sides are perceived identically.

    python ckm_depth3.py                       # JOMNAD + PIPHIJ, all four builders, depth 2 & 3
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import os

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

from extract_cores import _RCUT, _cell_and_atoms, full_complex, rcov, _TOL  # noqa: F401
from metrics import parse_xyz

HERE = Path(__file__).parent
CIF_ROOT = Path(os.environ.get("MECOBI_CIF_ROOT", "CCDC"))  # CSD CIFs, one folder per metal


def _dedupe(P, E, dp=1):
    """Drop coincident symmetry images by rounded position (special-position metals stack copies)."""
    seen, keep = set(), []
    for j in range(len(P)):
        k = tuple(np.round(P[j], dp))
        if k not in seen:
            seen.add(k); keep.append(j)
    return P[keep], E[keep]


def _merge_disorder(els, P, thresh=1.2):
    """Collapse crystallographic disorder: same-element atoms sitting closer than ``thresh`` are
    alternate positions of one physical atom (a flexible ethyl modelled over two sites), not two
    real atoms -- no bond is that short (C-C >= 1.4 A). JOMNAD's ethyls are disordered with no
    occupancy column to filter on, so a plain extractor double-counts them (each PEt3's P shows 6
    bonded C, 9-atom 'arms'); merging same-element atoms within thresh keeps one per cluster."""
    keep, taken = [], np.zeros(len(P), bool)
    for i in range(len(P)):
        if taken[i]:
            continue
        keep.append(i); taken[i] = True
        for j in range(i + 1, len(P)):
            if not taken[j] and els[j] == els[i] and np.linalg.norm(P[j] - P[i]) < thresh:
                taken[j] = True
    return [els[i] for i in keep], P[np.array(keep)]


def _core(elems, P, mc, metal_sym, cn, depth, donor_elements=None):
    """metal + donors (cn nearest non-H, non-metal) + BFS bond-shells out to ``depth``.

    Returns (element list, positions) INCLUDING the metal at index 0, or (None, None). Bonds are
    covalent-radius contacts; H and the metal are excluded from every shell -- identical rule to
    extract_cores.depth2_core / ckmrmsd.build_core_from_xyz, just iterated ``depth-1`` times."""
    d = np.linalg.norm(P - mc, axis=1)
    if donor_elements:      # each declared donor element: that many nearest atoms of it
        from collections import Counter

        donor_idx = []
        for el, n in Counter(e for e in donor_elements if e != "H").items():
            pick = [j for _, j in sorted((float(d[j]), j) for j in range(len(elems))
                                         if d[j] > 0.5 and elems[j] == el)][:n]
            if len(pick) < n:
                return None, None
            donor_idx += pick
        donor_idx.sort(key=lambda j: d[j])
    else:
        cand = sorted((float(d[j]), j) for j in range(len(elems))
                      if d[j] > 0.5 and elems[j] not in ("H", metal_sym))
        if len(cand) < cn:
            return None, None
        donor_idx = [j for _, j in cand[:cn]]
    in_core = set(donor_idx)
    order = list(donor_idx)
    frontier = list(donor_idx)
    for _ in range(depth - 1):
        nxt = []
        for a in frontier:
            da = np.linalg.norm(P - P[a], axis=1)
            for j in range(len(elems)):
                if elems[j] in ("H", metal_sym) or j in in_core:
                    continue
                if 0.4 < da[j] <= (rcov(elems[j]) + rcov(elems[a])) * _TOL:
                    in_core.add(j); nxt.append(j); order.append(j)
        frontier = nxt
    els = [metal_sym] + [elems[j] for j in order]
    pos = np.vstack([mc] + [P[j] for j in order])
    return els, pos


def crystal_core(cif_path, metal_sym, cn, depth, donor_elements=None):
    """Depth-N core of the ISOLATED crystal complex. full_complex flood-fills the molecular graph
    from the metal (never crossing another metal), so the depth-N BFS stays inside one molecule --
    a plain radius-contact expansion instead bleeds packing neighbours into depth 3 (JOMNAD's
    crystal picked up ~9 C from an adjacent molecule, 28 vs the 19 real). Extracting the core from
    the isolated-complex .xyz -- the same extractor the builds use -- keeps both sides comparable."""
    text = Path(cif_path).read_text(encoding="utf-8", errors="ignore")
    iso = full_complex(text, metal_sym, cn)
    if iso is None:
        return None, None
    syms, P = parse_xyz(iso)
    els, Pm = _merge_disorder(list(syms), np.asarray(P, float))   # collapse disordered alt-sites
    mc = Pm[els.index(metal_sym)]
    return _core(els, Pm, mc, metal_sym, cn, depth, donor_elements)


def build_core(xyz_text, metal_sym, cn, depth):
    syms, P = parse_xyz(xyz_text)
    if metal_sym not in syms:
        return None, None
    mc = P[syms.index(metal_sym)]
    return _core(list(syms), np.asarray(P, float), mc, metal_sym, cn, depth)


def _kabsch(P, Q):
    U, _, Vt = np.linalg.svd(P.T @ Q)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    return Vt.T @ np.diag([1.0, 1.0, d]) @ U.T


def ckm(els_a, Pa, els_b, Pb, iters=60):
    """(RMSD, n_matched): element-wise Hungarian assignment iterated with Kabsch about the metal."""
    if els_a is None or els_b is None:
        return None, 0
    A = np.asarray(Pa, float) - Pa[0]
    B = np.asarray(Pb, float) - Pb[0]
    ci, bi = defaultdict(list), defaultdict(list)
    for i, e in enumerate(els_a):
        ci[e].append(i)
    for i, e in enumerate(els_b):
        bi[e].append(i)
    elems = [e for e in ci if e in bi]
    if not elems:
        return None, 0
    R = np.eye(3)
    cm = bm = None
    for _ in range(iters):
        BR = B @ R.T
        cp, bp = [], []
        for e in elems:
            cidx, bidx = np.array(ci[e]), np.array(bi[e])
            row, col = linear_sum_assignment(cdist(A[cidx], BR[bidx]))
            cp.extend(cidx[row]); bp.extend(bidx[col])
        cm, bm = np.array(cp), np.array(bp)
        R = _kabsch(B[bm], A[cm])
    resid = A[cm] - B[bm] @ R.T
    return float(np.sqrt(np.mean(np.sum(resid ** 2, axis=1)))), len(cm)


TARGETS = {
    "JOMNAD": (CIF_ROOT / "Nickel" / "JOMNAD.Ni.cif", "Ni", 3),
    "PIPHIJ": (CIF_ROOT / "Copper" / "PIPHIJ.Cu.cif", "Cu", 6),
}
BUILDERS = {
    "MeCoBi":      HERE / "mecobi_det" / "old_30" / "structures",
    "MolSimplify": HERE.parent.parent / "arch_comparison" / "molsimplify" / "molsim_structures",
    "MetalloGen":  HERE.parent.parent / "arch_comparison" / "metallogen" / "metallogen_structures",
    "Architector": HERE.parent.parent / "arch_comparison" / "architector",
}


def main():
    for rc, (cif, metal, cn) in TARGETS.items():
        print(f"\n=== {rc}  ({metal}, CN{cn}) ===")
        cores = {dep: crystal_core(cif, metal, cn, dep) for dep in (2, 3)}
        for dep in (2, 3):
            ce, cp = cores[dep]
            n = 0 if ce is None else len(ce)
            print(f"  crystal depth-{dep} core: {n} atoms")
        print(f"  {'builder':<12} {'ckm_d2':>8} {'ckm_d3':>8}  {'nmatch_d3':>9}")
        for name, sdir in BUILDERS.items():
            xyz = sdir / f"{rc}.xyz"
            if not xyz.exists():
                print(f"  {name:<12} {'--':>8} {'--':>8}  (no .xyz)")
                continue
            txt = xyz.read_text(encoding="utf-8")
            row = []
            nm3 = 0
            for dep in (2, 3):
                ce, cp = cores[dep]
                be, bp = build_core(txt, metal, cn, dep)
                r, nm = ckm(ce, cp, be, bp)
                row.append(r)
                if dep == 3:
                    nm3 = nm
            d2 = f"{row[0]:.3f}" if row[0] is not None else "nan"
            d3 = f"{row[1]:.3f}" if row[1] is not None else "nan"
            print(f"  {name:<12} {d2:>8} {d3:>8}  {nm3:>9}")


if __name__ == "__main__":
    main()
