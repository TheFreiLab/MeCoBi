"""The coordination sphere of a built structure from its MOLECULAR GRAPH, not from distance alone.

The scorers used to take "the cn nearest non-H atoms" as the build's donors. That always yields
cn donors, so a build whose sphere is wrong (a donor pushed off, a phenyl carbon or a ligand
backbone atom sitting where a donor should be) is still scored as having the target CN, and its
angular metrics are computed on the wrong atoms. Here:

  * :func:`donor_indices` finds the atoms that SHOULD be the donors: the build is cut into
    ligand fragments (heavy-atom bonds by covalent radius, metal excluded), each fragment is
    matched to one input ligand SMILES by element-labelled graph isomorphism, and the ligand's
    known donor atoms (``benchmark_donors.json``, RDKit indices) are read through that mapping.
    Tool-agnostic: it needs only the .xyz, so MeCoBi, MetalloGen, molSimplify and Architector
    builds are treated identically. ``None`` when a ligand cannot be matched (a broken build).
  * :func:`detected_cn` counts the atoms that ARE bonded to the metal (Cordero covalent radii
    + 0.4 A, the CSD convention, lengthened per metal-donor pair to the crystal reference's own
    99th-percentile distance -- benchmark_ml_cutoffs.json), leaving out chelate bridgeheads and
    donor substituents that are inside the cut-off by geometry, so the CN is measured, not assumed.

Hydride ligands ([H-]) have no heavy atoms and are skipped here; hydrides.build_hydrides finds
them in the build as before.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from extract_cores import _TOL, rcov

# Cordero et al. (2008) covalent radii (A) for metals; low-spin values for Mn/Fe/Co (as in
# mecobi.optimize). Non-metals come from extract_cores.RCOV.
RCOV_METAL = {
    "Li": 1.28, "Be": 0.96, "Na": 1.66, "Mg": 1.41, "Al": 1.21, "K": 2.03, "Ca": 1.76,
    "Sc": 1.70, "Ti": 1.60, "V": 1.53, "Cr": 1.39, "Mn": 1.39, "Fe": 1.32, "Co": 1.26,
    "Ni": 1.24, "Cu": 1.32, "Zn": 1.22, "Ga": 1.22, "Rb": 2.20, "Sr": 1.95, "Y": 1.90,
    "Zr": 1.75, "Nb": 1.64, "Mo": 1.54, "Tc": 1.47, "Ru": 1.46, "Rh": 1.42, "Pd": 1.39,
    "Ag": 1.45, "Cd": 1.44, "In": 1.42, "Sn": 1.39, "Cs": 2.44, "Ba": 2.15, "La": 2.07,
    "Ce": 2.04, "Pr": 2.03, "Nd": 2.01, "Pm": 1.99, "Sm": 1.98, "Eu": 1.98, "Gd": 1.96,
    "Tb": 1.94, "Dy": 1.92, "Ho": 1.92, "Er": 1.89, "Tm": 1.90, "Yb": 1.87, "Lu": 1.87,
    "Hf": 1.75, "Ta": 1.70, "W": 1.62, "Re": 1.51, "Os": 1.44, "Ir": 1.41, "Pt": 1.36,
    "Au": 1.36, "Hg": 1.32, "Tl": 1.45, "Pb": 1.46, "Bi": 1.48, "Th": 2.06, "Pa": 2.00,
    "U": 1.96, "Np": 1.90, "Pu": 1.87, "Am": 1.80,
}
ML_SLACK = 0.4          # A: bonded if d <= r(M) + r(X) + 0.4 (CSD default bond criterion)
_BRIDGEHEAD_GAP = 0.2   # A: a chelate bridgehead sits this much farther than both its donors
_ALPHA_GAP = 0.5        # A: a donor's substituent sits this much farther than the donor itself
_MAX_ISO = 200         # isomorphisms tried per fragment (symmetric ligands have many)


def _r(el: str) -> float:
    return RCOV_METAL.get(el) or rcov(el)


_CUTOFFS: dict | None = None


def _cutoffs() -> dict:
    """(metal|donor) -> crystal-calibrated cut-off (dataprep/build_ml_cutoffs.py), loaded once."""
    global _CUTOFFS
    if _CUTOFFS is None:
        p = Path(__file__).with_name("benchmark_ml_cutoffs.json")
        _CUTOFFS = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _CUTOFFS


def ml_bonded(metal: str, el: str, d: float) -> bool:
    """Bonded if d <= r(M) + r(X) + 0.4 A, or within the 99th percentile of that pair's crystal
    M-X distances when longer (long weak bonds the reference CN counts: Pb-O, Hg-N, Cu-O axial)."""
    return d <= max(_r(metal) + _r(el) + ML_SLACK, _cutoffs().get(f"{metal}|{el}", 0.0))


def detected_cn(syms, P, mi, count_h: bool = True) -> int:
    """Atoms bonded to the metal: heavy atoms within the M-X bond criterion, plus (``count_h``)
    metal-only H (hydrides: an H with no other bonding partner). Pass ``count_h=False`` when the
    reference sphere carries no hydride, so a build made from hydride-corrected inputs is not
    read as over-coordinated against a hydride-less crystal sphere.

    Two kinds of atom are inside the cut-off by geometry, not by bonding, and are not counted:

      * the BRIDGEHEAD of a small chelate ring: an atom covalently bonded to two metal-bonded
        atoms that both sit clearly nearer the metal (the C of a kappa2-carboxylate at ~2.4 A,
        the N of a kappa2-nitrate);
      * the SUBSTITUENT of a donor: an atom covalently bonded to one metal-bonded atom that sits
        more than 0.5 A nearer the metal (the C of an alkoxide or amide on a large metal with
        short bonds: Zr-O 2.0 A, Zr...C 2.7 A, cut-off 2.91 A). On the crystals themselves this
        takes the agreement with the declared CN from 95.4% to 97.4% (Zr/Hf/Ti/Sc/Y: 83% to 95%).

    The carbons of an eta-ring, or the two atoms of a side-on ligand, are at about one distance,
    so they stay counted."""
    from hydrides import build_hydrides

    P = np.asarray(P, float)
    d = np.linalg.norm(P - P[mi], axis=1)
    near = [j for j, e in enumerate(syms)
            if j != mi and e != "H" and ml_bonded(syms[mi], e, d[j])]
    heavy = 0
    for j in near:
        nbrs = [k for k in near if k != j
                and np.linalg.norm(P[j] - P[k]) <= (rcov(syms[j]) + rcov(syms[k])) * _TOL]
        bridgehead = sum(d[k] < d[j] - _BRIDGEHEAD_GAP for k in nbrs) >= 2
        substituent = any(d[k] < d[j] - _ALPHA_GAP for k in nbrs)
        heavy += not (bridgehead or substituent)
    return heavy + (len(build_hydrides(list(syms), P, mi, 99)) if count_h else 0)


def _fragments(syms, P, mi):
    """Heavy-atom ligand fragments of the build (metal excluded) as networkx graphs."""
    import networkx as nx

    idx = [j for j, e in enumerate(syms) if j != mi and e != "H"]
    G = nx.Graph()
    for j in idx:
        G.add_node(j, el=syms[j])
    Q = P[idx]
    D = np.linalg.norm(Q[:, None] - Q[None], axis=-1)
    rad = np.array([rcov(syms[j]) for j in idx])
    lim = (rad[:, None] + rad[None]) * _TOL
    a, b = np.where(np.triu((D > 0.4) & (D <= lim), 1))
    G.add_edges_from((idx[i], idx[k]) for i, k in zip(a, b))
    return [G.subgraph(c).copy() for c in nx.connected_components(G)]


def _ligand_graph(smiles: str):
    import networkx as nx
    from rdkit import Chem

    mol = Chem.MolFromSmiles(smiles, sanitize=False)
    if mol is None:
        return None
    G = nx.Graph()
    for a in mol.GetAtoms():
        if a.GetSymbol() != "H":
            G.add_node(a.GetIdx(), el=a.GetSymbol())
    for bd in mol.GetBonds():
        i, k = bd.GetBeginAtomIdx(), bd.GetEndAtomIdx()
        if i in G and k in G:
            G.add_edge(i, k)
    return G


def _signature(G):
    return (G.number_of_nodes(), G.number_of_edges(),
            tuple(sorted(d["el"] for _, d in G.nodes(data=True))))


def donor_indices(syms, P, mi, ligands, donor_spec):
    """Indices (into the build) of the heavy donor atoms named by ``donor_spec`` (one list of
    RDKit atom indices per ligand SMILES), or None when a ligand cannot be found in the build.

    Each ligand is matched to an unused build fragment with the same heavy-atom graph; among the
    graph isomorphisms (a symmetric ligand has several, e.g. which of two equivalent N binds) the
    one placing the donors nearest the metal is kept."""
    from networkx.algorithms.isomorphism import GraphMatcher

    if not ligands or not donor_spec or len(donor_spec) < len(ligands):
        return None
    P = np.asarray(P, float)
    dm = np.linalg.norm(P - P[mi], axis=1)
    frags = _fragments(syms, P, mi)
    used, out = set(), []
    for smi, dons in zip(ligands, donor_spec):
        L = _ligand_graph(smi)
        if L is None:
            return None
        if L.number_of_nodes() == 0:          # [H-]: found by hydrides.build_hydrides
            continue
        if any(d not in L for d in dons):
            return None
        sig, best = _signature(L), None
        for fi, F in enumerate(frags):
            if fi in used or _signature(F) != sig:
                continue
            gm = GraphMatcher(L, F, node_match=lambda a, b: a["el"] == b["el"])
            for n, iso in enumerate(gm.isomorphisms_iter()):   # ligand atom -> build atom
                cost = sum(dm[iso[d]] for d in dons)
                if best is None or cost < best[0]:
                    best = (cost, fi, [iso[d] for d in dons])
                if n + 1 >= _MAX_ISO:
                    break
            if best is not None and best[1] == fi:
                break                          # identical ligands: the first fit is as good
        if best is None:
            return None
        used.add(best[1])
        out.extend(best[2])
    return out


def from_xyz(text: str, metal: str, ligands, donor_spec):
    """:func:`donor_indices` straight from .xyz text; None on any failure (never raises)."""
    from metrics import parse_xyz

    try:
        syms, P = parse_xyz(text)
        if metal not in syms:
            return None
        return donor_indices(syms, P, syms.index(metal), ligands, donor_spec)
    except Exception:  # noqa: BLE001 -- scoring falls back to the nearest atoms
        return None
