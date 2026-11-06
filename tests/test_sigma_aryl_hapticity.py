"""Regression: a cyclometalated sigma aryl-carbon donor must stay sigma through the xtb
relaxation and not slip to eta.

The fix (main #51, ``fix/sigma-aryl-unrestrained``) relaxes cyclometalated sigma-aryl complexes
UNRESTRAINED. This locks in the reference case verified on the command line: (p-cymene)Ru(C^N)Cl
with a bromo-2-phenylpyridine C^N chelate. The relaxed geometry was independently checked stable
in raw GFN2 at BOTH ``--uhf 0`` and ``--uhf 2``; MeCoBi now relaxes it at the corrected uhf = 0
(d6 Ru(II) piano stool splits pseudo-octahedral, main #52).
"""
import math

import pytest

from mecobi import pipeline
from mecobi.model import Complex, Ligand, Metal

# (p-cymene)Ru(bromo-2-phenylpyridine)Cl -- the exact reference complex (Ru, OS 2).
BROMO_PPY = "Brc1c[c-]c(-c2ccccn2)cc1"   # cyclometalated C^N: sigma aryl-C + pyridine N
CYMENE = "Cc1ccc(C(C)C)cc1"              # p-cymene, eta6 arene cap


def _read_xyz(path):
    lines = open(path).read().splitlines()
    n = int(lines[0].split()[0])
    syms, P = [], []
    for ln in lines[2:2 + n]:
        s = ln.split()
        syms.append(s[0]); P.append((float(s[1]), float(s[2]), float(s[3])))
    return syms, P


def _dist(a, b):
    return math.dist(a, b)


def _heavy_graph(syms, P, metal_index, cutoff=1.95):
    """Heavy-atom bond graph (metal + H excluded) by distance cutoff."""
    heavy = [i for i, s in enumerate(syms) if s != "H" and i != metal_index]
    adj = {i: set() for i in heavy}
    for a in range(len(heavy)):
        for b in range(a + 1, len(heavy)):
            i, j = heavy[a], heavy[b]
            if _dist(P[i], P[j]) < cutoff:
                adj[i].add(j); adj[j].add(i)
    return adj


def _ring_through(start, adj, size):
    """A cycle of exactly ``size`` atoms passing through ``start`` (or None)."""
    stack = [(start, [start])]
    while stack:
        node, path = stack.pop()
        if len(path) == size:
            if start in adj[node]:
                return set(path)
            continue
        for nb in adj[node]:
            if nb not in path:
                stack.append((nb, path + [nb]))
    return None


@pytest.mark.slow
def test_cyclometalated_sigma_aryl_stays_sigma(tmp_path):
    ligs = [Ligand(smiles=s) for s in (BROMO_PPY, CYMENE, "[Cl-]")]
    cx = Complex(metal=Metal("Ru", 2), name="ru_cymene_bromoppy_cl", ligands=ligs)

    res = pipeline.build_complex(cx, tmp_path, relax=True, xtb_timeout_s=300)[0]
    assert res.connectivity_ok, "xtb rearranged the assembled connectivity"
    assert res.uhf == 0, f"expected diamagnetic d6 Ru(II) piano stool (uhf 0), got {res.uhf}"

    syms, P = _read_xyz(res.xyz_path)
    M = P[res.metal_index]
    adj = _heavy_graph(syms, P, res.metal_index)

    # The sigma-aryl ring is the carbocycle bearing the Br (the cymene cap has none).
    br = syms.index("Br")
    ring_c = next(iter(adj[br]))
    ring = _ring_through(ring_c, adj, 6)
    assert ring is not None, "could not locate the bromo-aryl ring in the relaxed structure"

    # Sigma coordination = ONE ring carbon on the metal, the rest clearly farther (a large gap:
    # ipso ~2.8 A vs the next ring C ~3.5 A). An eta-slip clusters 2-3 ring carbons at similar
    # short distances, so count carbons within 0.6 A of the closest -- run-robust vs an absolute
    # cutoff. The closest must actually be bonded (< 3.1 A), i.e. the sigma-C did not detach.
    ring_c = sorted(_dist(P[i], M) for i in ring if syms[i] == "C")
    closest = ring_c[0]
    on_metal = sum(1 for d in ring_c if d < closest + 0.6)
    assert closest < 3.1, f"sigma aryl-C detached from the metal (closest ring C at {closest:.2f} A)"
    assert on_metal == 1, (
        f"sigma-aryl donor slipped to eta: {on_metal} ring carbons cluster on the metal "
        f"(ring C-Ru distances: {[round(d, 2) for d in ring_c]})"
    )


@pytest.mark.slow
def test_monodentate_sigma_aryl_relaxes_restrained_and_stays_sigma(tmp_path):
    """A MONODENTATE σ-aryl (Ph, σ since the σ-aryl perception fix) must not take the unrestrained
    relax meant for cyclometalated C^N chelates: relaxed free, XUVZOE's Ph and MeCN drifted off.
    Pt(bpy)Ph2 keeps the restrained relax + ortho pins: both Pt-C bound, each ring still σ."""
    from pathlib import Path

    from mecobi import optimize

    cx = Complex(metal=Metal("Pt", 2), ligands=[
        Ligand(smiles="c1ccc(-c2ccccn2)nc1"), Ligand(smiles="[c-]1ccccc1"),
        Ligand(smiles="[c-]1ccccc1")])
    (res,) = pipeline.build_complex(cx, tmp_path, relax=True)
    assert not any("UNRESTRAINED" in w for w in res.warnings)
    at = optimize._read_xyz(Path(res.xyz_path))
    m = at[res.metal_index][1]
    for d in res.donor_indices:
        assert math.dist(at[d][1], m) < 2.3
        if at[d][0] == "C":   # its two ring neighbours stay ~3 A away (σ), not ~2.2 A (η)
            ring = sorted((math.dist(at[d][1], at[k][1]), k) for k in range(len(at))
                          if k != d and at[k][0] == "C")[:2]
            assert all(math.dist(at[k][1], m) > 2.6 for _, k in ring)
