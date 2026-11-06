"""D-MAE_k: MetalloGen's distance-matrix mean absolute error over the atoms within k bonds of the
metal (Lee et al., J. Chem. Inf. Model. 2025, 65, 11878, eq. 2; k = 3 in the paper's results).

    D-MAE_k(D, D') = 1 / (|N_k| (|N_k| - 1)) * sum_{i,j in N_k} | D_ij - D'_ij |

with N_k the atoms within k graph neighbours of the metal -- i.e. the mean |delta d| over every
pair of those atoms. Unlike an RMSD it needs no superposition, and unlike MeCoBi's donor-only
dmat RMSD it sees the ligand backbone out to three bonds.

Differences from the paper's set-up (its scoring code is not in the public repository):
  * the paper's reference is the CSD structure RE-OPTIMISED with GFN2-xTB, compared with the
    xtb-optimised MetalloGen conformer (the closest in energy of up to ten); here the reference
    is the raw crystal geometry, so values are not numerically comparable with the paper's
    (0.399 A average there);
  * the paper includes H (all atoms of N_k; xtb-placed on both sides); here heavy atoms only,
    since X-ray H positions are systematically short (hydrides excluded on both sides);
  * the shells are found on the molecular graph by covalent radius (extract_cores._TOL), from the
    donors: the build's graph-identified donors (donor_map) and the crystal's cn nearest atoms;
  * the atom correspondence is the element-wise one that minimises the core RMSD
    (ckmrmsd.best_match: 300 random starts + mirror). The paper builds each conformer from the
    CSD molecular graph, so its correspondence is given; a geometric one equals it whenever the
    build's atoms sit nearest their own crystal counterparts, and otherwise can only LOWER the
    error.
  * pairs are counted over matched atoms only; ``n_matched`` vs the crystal core size flags a
    build whose depth-k core has missing or extra atoms.

Crystal depth-k cores come from the CIFs (dataprep/extract_cores_dk.py ->
benchmark_cores_d3*.json.gz): the isolated complex (ckm_depth3.crystal_core, disorder merged).
"""
from __future__ import annotations

import numpy as np
from scipy.spatial.distance import cdist

from ckmrmsd import best_match
from extract_cores import _TOL, rcov
from metrics import _heavy_donors, parse_xyz

DEPTH = 3


def shells(elems, P, mi, donor_idx, depth: int = DEPTH):
    """Heavy-atom indices within ``depth`` bonds of the metal, BFS from ``donor_idx`` over
    covalent-radius bonds (H and the metal never enter a shell). Donors first."""
    order, seen, frontier = list(donor_idx), set(donor_idx), list(donor_idx)
    metal = elems[mi]
    for _ in range(depth - 1):
        nxt = []
        for a in frontier:
            da = np.linalg.norm(P - P[a], axis=1)
            for j in np.where(da <= (rcov(elems[a]) + 2.0) * _TOL)[0]:
                j = int(j)
                if (j in seen or j == mi or elems[j] in ("H", metal)
                        or not 0.4 < da[j] <= (rcov(elems[j]) + rcov(elems[a])) * _TOL):
                    continue
                seen.add(j); nxt.append(j); order.append(j)
        frontier = nxt
    return order


def core_from_xyz(text: str, metal: str, n_heavy: int, depth: int = DEPTH, donor_idx=None):
    """Depth-k heavy core of a built .xyz: ``{"metal", "atoms"}`` (atoms = [{"el", "xyz"}],
    donors first), or None. ``n_heavy`` heavy donors: ``donor_idx`` when given, else nearest."""
    syms, P = parse_xyz(text)
    if metal not in syms:
        return None
    mi = syms.index(metal)
    don = _heavy_donors(syms, P, mi, n_heavy, donor_idx)
    if len(don) < n_heavy:
        return None
    idx = shells(syms, P, mi, don, depth)
    return {"metal": {"el": metal, "xyz": P[mi].tolist()},
            "atoms": [{"el": syms[j], "xyz": P[j].tolist()} for j in idx]}


def core_size(core) -> int:
    return 1 + len(core["atoms"])


def _arrays(core):
    atoms = [core["metal"]] + core["atoms"]
    return ([a["el"] for a in atoms],
            np.asarray([a["xyz"] for a in atoms], float) - np.asarray(core["metal"]["xyz"], float))


def dmae(crystal_core, build_core):
    """(D-MAE in A, n_matched atoms) between two depth-k cores; (nan, 0) if nothing matches."""
    ce, CP = _arrays(crystal_core)
    be, BP = _arrays(build_core)
    res = best_match(ce, CP, be, BP)
    if res is None or len(res[1]) < 2:
        return float("nan"), 0
    _, cm, bm = res
    DC, DB = cdist(CP[cm], CP[cm]), cdist(BP[bm], BP[bm])
    iu = np.triu_indices(len(cm), k=1)
    return float(np.mean(np.abs(DC[iu] - DB[iu]))), len(cm)
