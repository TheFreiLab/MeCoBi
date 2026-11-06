"""stk building-block construction for assembly (ported from the prototype ``common.py``).

Builds the metal centre and the ligand building blocks (with GenericFunctionalGroup
markers on the donor atoms) that the custom topology graphs consume. The 3D
conformer + backbone-geometry fixing for bidentate ligands is carried over
verbatim from the proven prototype so assembled geometries match.
"""

from __future__ import annotations

import numpy as np
import stk
from rdkit import Chem
from rdkit.Chem import AllChem

# NOTE: bonding a 1-bonder metal FG to an N-bonder centroid η-cap FG (a KeyError in
# stk's built-in reaction registry) is handled by CapReactionFactory in
# topologies/metal_complex.py — a GenericReactionFactory subclass wired into the
# topology's factory, rather than mutating stk's process-global _reactions dict.

def _n_conformers() -> int:
    """Conformer ensemble size for σ-chelates (denticity >= 2), from
    ``MECOBI_N_CONFORMERS`` (default 1 = the proven single deterministic embed).

    ``> 1`` turns on the coordination-directed path: embed N conformers, pre-organise each
    toward the exact target site directions (see ``site_dirs`` in ligand_building_block),
    and keep the least-strained. A same-platform pre-opt A/B was a wash, and a controlled
    relaxed A/B (P2a on vs off, same xtb) came out net-NEGATIVE on the cases checked (one
    0.2 -> 27 poly-CShM), so it is OFF by default pending a clean full-pilot A/B on a
    known-good xtb build. Set ``MECOBI_N_CONFORMERS=10`` to A/B it. The fixed embed seed
    keeps any ensemble reproducible (per platform — RDKit ETKDG differs across OSes).
    """
    import os

    try:
        return max(1, int(os.environ.get("MECOBI_N_CONFORMERS", "1")))
    except ValueError:
        return 1


def _flex_threshold() -> int:
    """Backbone-flexibility cutoff (rotatable bonds on the donor-to-donor paths) at or above
    which a denticity>=3 ligand is treated as a flexible WRAPPER and given a conformer
    ensemble. Env-tunable ``MECOBI_FLEX_ROTB`` (default 3). Rigid macrocyclic/planar donor
    cores (phthalocyanines, salen-type, cyclam) sit at 0-1 backbone-rotatable bonds, so 3
    clears them with margin; flexible arms (salicylaldimine tripods, aminocarboxylate cages)
    sit at 3-9."""
    import os

    try:
        return max(1, int(os.environ.get("MECOBI_FLEX_ROTB", "3")))
    except ValueError:
        return 3


def _coord_map_enabled() -> bool:
    """Whether the coordinate-map embed (MetalloGen-style: pin a flexible high-denticity ligand's
    donors to their target sites and let distance geometry fold the backbone around them) is on.
    Default ON; ``MECOBI_COORD_MAP=0`` disables it for an A/B against the free-embed placement."""
    import os

    return os.environ.get("MECOBI_COORD_MAP", "1").strip() not in ("0", "false", "no", "")


def _auto_ensemble_size() -> int:
    """Ensemble size used AUTOMATICALLY for a flexible high-denticity wrapper (see
    ``_backbone_rotatable``), independent of the manual ``MECOBI_N_CONFORMERS`` override.
    Env-tunable ``MECOBI_AUTO_CONFORMERS`` (default 1 = OFF).

    Rationale for default OFF: on a same-platform pilot A/B the flexibility-gated, geometric-
    fitness ensemble (rigid cores provably untouched — see the gate) was net-positive by TOTAL
    poly-CShM (~-10 over 18 flexible wrappers: MUTSAX 14->2, TIZJUI 32->20, QUSGAN 24->14) but
    a WASH by count (9 better / 7 worse, e.g. UQUBEO 20->33, HEZXES 17->27). The per-ligand
    ensemble can't see the multi-ligand + MCHammer interactions that decide the final geometry,
    so which conformer assembles best isn't fully predictable per-ligand. RDKit ETKDG embeds
    differ across OSes, so this local A/B can't be the decider — set MECOBI_AUTO_CONFORMERS=8
    and A/B on the target xtb platform (Keisan) before flipping the default."""
    import os

    try:
        return max(1, int(os.environ.get("MECOBI_AUTO_CONFORMERS", "1")))
    except ValueError:
        return 1


def _backbone_rotatable(rdkit_mol, coord_atoms: list[int]) -> int:
    """Count rotatable bonds lying on the union of shortest donor-to-donor paths — the
    ligand's *coordinating skeleton*, ignoring peripheral chains (a phthalocyanine with six
    dangling hexyls reads as rigid, which its rigid macrocyclic donor core is). A bond counts
    if it is a single, non-ring bond between two atoms that each have another heavy neighbour.
    Drives the flexible-wrapper gate: high count -> the donors need a different backbone
    rotamer to reach every site, so an ensemble pays off; ~0 -> one embed is definitive."""
    import itertools

    bond_set: set[tuple[int, int]] = set()
    for a, c in itertools.combinations(coord_atoms, 2):
        path = Chem.GetShortestPath(rdkit_mol, int(a), int(c))
        bond_set.update(tuple(sorted((u, v))) for u, v in zip(path, path[1:]))
    n = 0
    for u, v in bond_set:
        bd = rdkit_mol.GetBondBetweenAtoms(u, v)
        if bd is None or bd.GetBondType() != Chem.BondType.SINGLE or bd.IsInRing():
            continue
        au, av = rdkit_mol.GetAtomWithIdx(u), rdkit_mol.GetAtomWithIdx(v)
        if _heavy_degree(au) > 1 and _heavy_degree(av) > 1:
            n += 1
    return n


def _heavy_degree(atom) -> int:
    return sum(1 for nb in atom.GetNeighbors() if nb.GetAtomicNum() > 1)


def _donor_target_rmsd(donor_xyz: np.ndarray, target_xyz: np.ndarray) -> float:
    """RMSD after optimal rigid superposition (Kabsch) of the ligand's donor atoms onto the
    target coordination-site positions. This is exactly what stk's vertex does when it seats
    the building block — a Kabsch fit of the bonder centroids onto the edge positions — so
    minimising this over an ensemble picks the conformer whose donor set will actually sit on
    the target polyhedron, rather than the one with the lowest (assembly-blind) UFF strain."""
    P = np.asarray(donor_xyz, dtype=float)
    Q = np.asarray(target_xyz, dtype=float)
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    H = Pc.T @ Qc
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    diff = (R @ Pc.T).T - Qc
    return float(np.sqrt((diff * diff).sum() / len(P)))


def metal_building_block(symbol: str, charge: int, n_sites: int) -> stk.BuildingBlock:
    """A single-atom metal centre with ``n_sites`` SingleAtom functional groups.

    ``n_sites`` is the coordination number (one binding site per donor atom).
    """
    metal_class = getattr(stk, symbol, None)
    if metal_class is None:
        raise ValueError(f"stk has no metal atom class for element {symbol!r}.")
    metal_atom = metal_class(0, charge=charge)
    return stk.BuildingBlock(
        smiles=f"[{symbol}{charge:+d}]",   # "+2", "+0", "-1": "[Fe+-1]" is not valid SMILES
        functional_groups=[stk.SingleAtom(metal_atom) for _ in range(n_sites)],
        position_matrix=[[0.0, 0.0, 0.0]],
    )


def _apply_geom_info(conf, geom_info) -> None:
    from rdkit.Chem import rdMolTransforms

    if "type" not in geom_info:
        return
    if geom_info["type"] == "angle":
        i, j, k = geom_info["indices"]
        rdMolTransforms.SetAngleDeg(conf, i, j, k, geom_info["value_deg"])
    elif geom_info["type"] == "dihedral":
        i, j, k, l = geom_info["indices"]
        rdMolTransforms.SetDihedralDeg(conf, i, j, k, l, geom_info["value_deg"])
    elif geom_info["type"] == "double_dihedral":
        i1, i2, i3, i4, i5 = geom_info["indices"]
        d1, d2 = geom_info["values_deg"]
        rdMolTransforms.SetDihedralDeg(conf, i1, i2, i3, i4, d1)
        rdMolTransforms.SetDihedralDeg(conf, i2, i3, i4, i5, d2)


def _worst_heavy_bond(rdkit_mol, cid: int) -> float:
    """Longest heavy-atom–heavy-atom bond (Å) in conformer ``cid``.

    A pre-organisation force-field minimisation started from an atom overlap — a
    hard dihedral snap can slam two donor-borne aryls together (an N-aryl
    α-diimine folded to s-cis) — can DIVERGE and blow bonds apart. A normal
    organic ligand has every heavy–heavy bond well under 1.8 Å, so a large value
    here flags an exploded conformer that must be reverted rather than assembled.
    """
    conf = rdkit_mol.GetConformer(cid)
    worst = 0.0
    for b in rdkit_mol.GetBonds():
        a1, a2 = b.GetBeginAtom(), b.GetEndAtom()
        if a1.GetAtomicNum() == 1 or a2.GetAtomicNum() == 1:
            continue
        p1, p2 = conf.GetAtomPosition(a1.GetIdx()), conf.GetAtomPosition(a2.GetIdx())
        worst = max(worst, ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2 + (p1.z - p2.z) ** 2) ** 0.5)
    return worst


def _set_conformer_positions(conf, positions) -> None:
    """Restore ``conf`` to a saved (N, 3) coordinate array (revert a bad pre-org)."""
    from rdkit.Geometry import Point3D

    for i, (x, y, z) in enumerate(positions):
        conf.SetAtomPosition(i, Point3D(float(x), float(y), float(z)))


def facial_triad(smiles: str, ring_atoms: list[int]) -> list[int]:
    """Pick three mutually-spread ring carbons to represent an eta-arene face.

    A facial arene binds through its whole ring, but the topology graph exposes
    three fac binding sites; three carbons at ~120 deg around the ring (for a
    regular ring, the maximally-separated triple) approximate the face cap and
    let ``PlanarTriDentateLigandVertex`` orient the plane. xtb relaxes to eta6.
    """
    ring = sorted(set(ring_atoms))
    if len(ring) <= 3:
        return ring
    rdkit_mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    params = AllChem.ETKDGv3()
    params.randomSeed = 0xF00D
    if AllChem.EmbedMolecule(rdkit_mol, params=params) != 0:
        # fall back to evenly-spaced indices if embedding fails
        step = len(ring) / 3.0
        return sorted(ring[int(round(k * step)) % len(ring)] for k in range(3))
    conf = rdkit_mol.GetConformer()
    pos = {i: np.array(conf.GetAtomPosition(i)) for i in ring}
    # greedy max-spread triple: farthest pair, then the atom maximising min dist
    best = max(((i, j) for i in ring for j in ring if i < j),
               key=lambda p: np.linalg.norm(pos[p[0]] - pos[p[1]]))
    a, b = best
    c = max((k for k in ring if k not in (a, b)),
            key=lambda k: min(np.linalg.norm(pos[k] - pos[a]),
                              np.linalg.norm(pos[k] - pos[b])))
    return sorted([a, b, c])


def donor_symmetry_classes(smiles: str, donors: list[int]) -> list[int]:
    """Symmetry class of each donor atom (canonical rank ignoring tie-breaking).

    Two donors sharing a class are related by a molecular symmetry, so swapping
    which one binds where yields no new isomer. This collapses donor-direction
    permutations for symmetric chelates (bpy, en — both donors equivalent) while
    keeping them for asymmetric ones (N^O Schiff bases — distinct classes).

    ``donors`` are 0-based atom indices into the SMILES without explicit Hs, the
    same convention as :attr:`mecobi.model.Ligand.coord_atoms`.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    ranks = list(Chem.CanonicalRankAtoms(mol, breakTies=False))
    return [ranks[i] for i in donors]


def _donor_chain_order(rdkit_mol, donors: list[int]) -> list[int]:
    """Order donors along the backbone for a chelating multidentate ligand.

    Endpoints are the donor pair joined by the longest bond-graph path; the rest
    are inserted between them, sorted by graph distance from one endpoint. Adjacent
    entries in the returned list are then the natural chelate-adjacent donor pairs
    (e.g. for an ONO/ONNO ligand: O–N, N–O), which the pre-organisation restrains
    to cis-chelate range so the donor set curls toward one face.
    """
    import itertools

    pair_path: dict[tuple[int, int], int] = {}
    for a, b in itertools.combinations(donors, 2):
        d = len(Chem.GetShortestPath(rdkit_mol, a, b))
        pair_path[(a, b)] = pair_path[(b, a)] = d
    e1, e2 = max(itertools.combinations(donors, 2), key=lambda p: pair_path[p])
    middle = sorted((d for d in donors if d not in (e1, e2)), key=lambda d: pair_path[(e1, d)])
    return [e1, *middle, e2]


def _stk_skeleton(smiles: str) -> stk.BuildingBlock:
    """The atoms + bonds of ``stk.BuildingBlock(smiles=smiles)``, WITHOUT its 3D embed.

    stk's SMILES constructor embeds with its own fixed ETKDGv2 (seed 4) and raises
    "Embedding with seed value of 4 failed." when that fails -- which it does for large,
    flexible ligands (C16-chain BIP, terphenyl tripods, silyl-ether phthalocyanines: ~260
    CSD benchmark structures). Those coordinates were only ever a placeholder (the caller
    overwrites them with its own embed), so build the same molecule stk would -- AddHs on the
    parsed SMILES, Kekulized so bond orders stay 1/2/3, not aromatic 1.5 -- on a zero
    conformer instead. Atom order matches ``Chem.AddHs(Chem.MolFromSmiles(smiles))``.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    mol = Chem.AddHs(mol)
    Chem.Kekulize(mol)
    mol.AddConformer(Chem.Conformer(mol.GetNumAtoms()), assignId=True)
    return stk.BuildingBlock.init_from_rdkit_mol(mol)


def _embed(rdkit_mol, params) -> bool:
    """``EmbedMolecule`` with a random-coordinates retry; True on success.

    The default distance-geometry start (eigen-decomposition of the sampled distance matrix)
    fails on large, flexible ligands (~150+ atoms), whose sampled distances are far from any
    3D arrangement. Starting from random coordinates instead is the RDKit-recommended remedy
    and is still seeded, so deterministic. Only used as a FALLBACK: a ligand that embeds today
    keeps its exact conformer.
    """
    if AllChem.EmbedMolecule(rdkit_mol, params=params) == 0:
        return True
    params.useRandomCoords = True
    try:
        return AllChem.EmbedMolecule(rdkit_mol, params=params) == 0
    finally:
        params.useRandomCoords = False


def ligand_building_block(
    smiles: str, donor_groups: list, site_dirs: "list | None" = None,
) -> stk.BuildingBlock:
    """Build an stk ligand BuildingBlock with a 3D conformer and donor markers.

    ``donor_groups`` is one entry per coordination SITE: a bare int (or 1-tuple)
    for a σ-donor, or a multi-atom tuple for an η-bonded π-site (an η²-alkene/alkyne
    ``(C, C)`` pair). Each group becomes ONE GenericFunctionalGroup whose bonders are
    all its atoms — so stk aligns the bonder centroid to the vertex, seating the
    metal over a σ-donor or over a π-bond midpoint. #functional-groups == denticity.

    ``site_dirs`` (one UNIT direction per donor group, in the same order — the target
    coordination-site directions the ligand's donors will bind) turns the pre-organisation
    coordination-DIRECTED for a σ-chelate: each donor PAIR is pulled to the distance the
    target site geometry implies (``|R·dir_i − R·dir_j|`` at a realistic M–L radius, the
    molSimplify bounds idea), so the donors adopt the exact target polyhedron — cis vs
    trans, fac vs mer — instead of merely gathering near the metal. Omitted (or for π/cap
    ligands) → the generic backbone pre-organisation, unchanged.
    """
    groups = [(g,) if isinstance(g, int) else tuple(g) for g in donor_groups]
    coord_atoms = [grp[0] for grp in groups]  # one representative atom per site
    mol = _stk_skeleton(smiles)
    atoms_list = list(mol.get_atoms())
    functional_groups = [
        stk.GenericFunctionalGroup(
            atoms=tuple(atoms_list[i] for i in grp),
            bonders=tuple(atoms_list[i] for i in grp),
            deleters=(),
        )
        for grp in groups
    ]
    mol = stk.BuildingBlock.init_from_molecule(mol, functional_groups=tuple(functional_groups))

    rdkit_mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    if rdkit_mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    params = AllChem.ETKDGv3()
    params.randomSeed = 0xF00D
    ring_groups = [grp for grp in groups if len(grp) >= 5]

    def _preorganise(cid: int) -> float:
        """Pre-organise conformer ``cid`` in place (donor-arrangement fixing, per
        denticity) and return a fitness: the restrained-UFF energy after the pull.

        That energy is LOW when the donors reach a coordinating cluster with little
        backbone strain, and HIGH when the backbone resists (donors can't close, so the
        distance restraints stay violated). Comparing it across conformers of the same
        ligand therefore picks the rotamer that seats all donors best — the point of the
        ensemble. Returns 0.0 for cases with no pre-organisation (monodentate), where any
        conformer is equivalent.
        """
        conf = rdkit_mol.GetConformer(cid)
        # Multi-cap ligand (ansa-metallocene, Cp+donor CGC): the free-ligand embed splays
        # the anionic cap rings ~7 A apart with their normals ~70 deg off the ring-ring
        # axis, and the rigid placement inherits that — so the rings get crushed onto the
        # metal and a substituted ring (Cp*) buckles on its own methyls. Fold the caps into
        # a metallocene conformer first: pull every cross-ring atom pair into stacking range
        # so the rings end ~3.5 A apart and facing (normals along the ring-ring axis); the
        # metal then seats between them and xtb finishes the eta5/eta6. (Handled here, ahead
        # of the sigma-chelate pre-organisation, which only pulls one atom per ring together
        # and leaves the rings edge-on.)
        if len(ring_groups) >= 2:
            try:
                AllChem.UFFOptimizeMolecule(rdkit_mol, maxIters=50, confId=cid)
            except Exception:
                pass
            # Terminal ring substituents (Cp* methyls): keep those of different caps apart
            # so the minimiser settles on a STAGGERED sandwich rather than eclipsed — else
            # the ten methyls clash H-on-H and, coupled through the bridge, xtb can't
            # rotate out of it. (No-op for unsubstituted Cp, which has no such carbons.)
            ring_atom_set = {a for grp in ring_groups for a in grp}

            def _terminal_subs(ring):
                out = []
                for a in ring:
                    for nb in rdkit_mol.GetAtomWithIdx(a).GetNeighbors():
                        j = nb.GetIdx()
                        if nb.GetAtomicNum() == 6 and j not in ring_atom_set \
                                and len([x for x in nb.GetNeighbors() if x.GetAtomicNum() > 1]) == 1:
                            out.append(j)
                return out

            try:
                ff = AllChem.UFFGetMoleculeForceField(rdkit_mol, confId=cid)
                if ff is not None:
                    for gi in range(len(ring_groups)):
                        for gj in range(gi + 1, len(ring_groups)):
                            for a in ring_groups[gi]:
                                for b in ring_groups[gj]:
                                    ff.UFFAddDistanceConstraint(a, b, False, 2.5, 4.2, 50.0)
                            subs_i, subs_j = _terminal_subs(ring_groups[gi]), _terminal_subs(ring_groups[gj])
                            for a in subs_i:
                                for b in subs_j:
                                    ff.UFFAddDistanceConstraint(a, b, False, 3.6, 99.0, 25.0)
                    ff.Minimize(maxIts=2000)
                    return ff.CalcEnergy()
            except Exception:
                pass
            return 0.0
        # Coordination-directed pre-organisation (molSimplify-style) when the target site
        # directions are known and every donor is a single σ atom: pull each donor PAIR to
        # the distance the sites imply, so the donors take the exact target arrangement
        # (cis/trans, fac/mer) rather than an unbiased cluster. The returned restrained
        # energy is then coordination-relevant — a meaningful conformer fitness.
        #
        # EXPERIMENTAL, gated with the ensemble (MECOBI_N_CONFORMERS > 1): on a pilot A/B
        # this NET-regressed the assembled geometry, for two structural reasons a per-ligand
        # HARD restraint can't dodge — (1) it imposes the ideal polyhedron bite angle even on
        # a rigid chelate whose natural bite differs (a tetrahedral 109° forced onto an ~80°
        # 5-ring chelate), and (2) it trusts the site_map's donor->site order, so a meridional
        # tridentate listed out of backbone order gets an end-pair forced trans and tears.
        # molSimplify avoids both by smoothing SOFT distance bounds over the WHOLE complex
        # (the ligand's rigidity wins), which our per-ligand embed + vertex placement can't
        # replicate. Kept behind the flag for A/B, not shipped on.
        if (site_dirs is not None and _n_conformers() > 1
                and len(coord_atoms) >= 2 and all(len(g) == 1 for g in groups)):
            import itertools

            try:
                AllChem.UFFOptimizeMolecule(rdkit_mol, maxIters=50, confId=cid)
            except Exception:
                pass
            try:
                ml = 2.0  # reference M–L: the directions set the angles; ml sets a realistic bite
                sd = [np.asarray(d, dtype=float) for d in site_dirs]
                ff = AllChem.UFFGetMoleculeForceField(rdkit_mol, confId=cid)
                if ff is not None:
                    for a, b in itertools.combinations(range(len(coord_atoms)), 2):
                        d = float(np.linalg.norm(ml * sd[a] - ml * sd[b]))
                        ff.UFFAddDistanceConstraint(
                            coord_atoms[a], coord_atoms[b], False, d * 0.9, d * 1.1, 200.0)
                    ff.Minimize(maxIts=1000)
                    return ff.CalcEnergy()
            except Exception:
                pass
            return 0.0
        if len(coord_atoms) == 2:
            i1, i4 = coord_atoms
            try:
                AllChem.UFFOptimizeMolecule(rdkit_mol, maxIters=50, confId=cid)
            except Exception:
                pass
            path = Chem.GetShortestPath(rdkit_mol, i1, i4)
            geom_info: dict = {}
            if len(path) == 3:
                geom_info = {"type": "angle", "indices": (i1, path[1], i4), "value_deg": 120.0}
            elif len(path) == 4:
                geom_info = {"type": "dihedral", "indices": (i1, path[1], path[2], i4), "value_deg": 0.0}
            elif len(path) == 5:
                geom_info = {
                    "type": "double_dihedral",
                    "indices": (i1, path[1], path[2], path[3], i4),
                    "values_deg": (60, -60),
                }
            # Snapshot the intact, clash-free conformer. A hard dihedral/angle snap
            # folds the chelate to s-cis, but on a ligand carrying bulky substituents
            # on its donors (an N-aryl α-diimine) it slams the two aryls into overlap;
            # a UFF minimisation from that clash then DIVERGES and blows the ligand
            # apart (aromatic bonds stretched past 2.5 Å). If that happens we revert
            # to this snapshot and fold with the distance restraint ALONE, which pulls
            # the bite together without the clash that triggers the blow-up.
            clean = np.array(
                [list(conf.GetAtomPosition(i)) for i in range(rdkit_mol.GetNumAtoms())])
            explode_limit = _worst_heavy_bond(rdkit_mol, cid) + 0.4
            if geom_info:
                try:
                    _apply_geom_info(conf, geom_info)
                except (ValueError, RuntimeError):
                    pass

            # The dihedral fixes above cannot touch ring bonds (SetDihedralDeg
            # refuses them), so chelates whose donor path runs through a ring —
            # salicylaldimines, cyclometalating aryls — keep the embed's anti
            # rotamer and can never close onto the metal. A UFF minimisation with
            # a donor-donor distance restraint pulls the bite to chelating range
            # whatever bonds have to rotate.
            def _restrained_min() -> "float | None":
                try:
                    ff = AllChem.UFFGetMoleculeForceField(rdkit_mol, confId=cid)
                    if ff is None:
                        return None
                    ff.UFFAddDistanceConstraint(i1, i4, False, 2.3, 3.0, 200.0)
                    ff.Minimize(maxIts=500)
                    return ff.CalcEnergy()
                except Exception:
                    return None

            energy = _restrained_min()
            if energy is not None and _worst_heavy_bond(rdkit_mol, cid) <= explode_limit:
                return energy
            # Exploded (or the FF failed): revert to the intact snapshot and refold
            # from the clash-free geometry, skipping the dihedral snap that caused it.
            _set_conformer_positions(conf, clean)
            energy = _restrained_min()
            if energy is not None and _worst_heavy_bond(rdkit_mol, cid) <= explode_limit:
                return energy
            _set_conformer_positions(conf, clean)
            return 0.0
        if len(coord_atoms) >= 3:
            # Tridentate and higher: the raw ETKDGv3 embed leaves the donors splayed,
            # so stk binds the ligand backbone-first — donors stranded far from the
            # metal and a backbone atom crushed onto it (seen on a V(V)-oxo ONO azine
            # ligand, and on an EDTA hexadentate cage). Pre-organise the donors:
            #  - backbone-adjacent pairs (from the donor chain order) into cis-chelate
            #    range, so a linear multidentate curls toward one face; and
            #  - EVERY donor pair into a coordination shell (2.5–4.6 A ~ cis..trans of
            #    ~2.4 A M–L bonds), so a branched cage (EDTA) gathers around the metal
            #    instead of extending. xtb relaxes the exact geometry afterwards.
            try:
                AllChem.UFFOptimizeMolecule(rdkit_mol, maxIters=50, confId=cid)
            except Exception:
                pass
            try:
                import itertools

                chain = _donor_chain_order(rdkit_mol, list(coord_atoms))
                adjacent = set(zip(chain, chain[1:]))
                ff = AllChem.UFFGetMoleculeForceField(rdkit_mol, confId=cid)
                if ff is not None:
                    for a, b in itertools.combinations(coord_atoms, 2):
                        if (a, b) in adjacent or (b, a) in adjacent:
                            ff.UFFAddDistanceConstraint(a, b, False, 2.4, 2.9, 200.0)
                        else:
                            ff.UFFAddDistanceConstraint(a, b, False, 2.5, 4.6, 80.0)
                    ff.Minimize(maxIts=1000)
                    # Ensemble fitness: when the target site directions are known, score the
                    # pre-organised conformer by how well its donors can be Kabsch-seated onto
                    # the target polyhedron (what stk does at placement) — a direct predictor
                    # of assembled-geometry quality. UFF strain (used when directions are
                    # unknown) is assembly-blind and picks worse conformers for the flexible
                    # wrappers this ensemble targets.
                    if site_dirs is not None and len(site_dirs) == len(coord_atoms):
                        conf = rdkit_mol.GetConformer(cid)
                        donor_xyz = np.array([list(conf.GetAtomPosition(a)) for a in coord_atoms])
                        target = 2.0 * np.asarray(site_dirs, dtype=float)
                        return _donor_target_rmsd(donor_xyz, target)
                    return ff.CalcEnergy()
            except Exception:
                pass
            return 0.0
        return 0.0  # monodentate: no backbone pre-organisation, any conformer is equivalent

    # Coordinate-map embed (MetalloGen-style) for a flexible HIGH-DENTICITY wrapper that must fold
    # to reach every site (JORXUM's meridional ONO, TIZJUI's salicylaldimine tripod). Instead of
    # embedding the ligand FREE — which clumps the donors, so a rigid Kabsch placement can never
    # seat them on the polyhedron (the #3 failure) — PIN each donor to its target site position
    # (site_dir × M-L radius) and let RDKit distance geometry generate the backbone AROUND those
    # pins. The conformer then already has every donor on its coordination site, so stk's placement
    # is a near-identity fit. Gated to flexible denticity>=3 σ-wrappers with known site directions
    # (a rigid pincer or a monodentate never needs it); on an infeasible pin set the embed fails
    # and we fall through to the free embed + pre-organisation below.
    #
    # The SAME pin also fixes a chelating-diene conformation problem (COD, norbornadiene): a free
    # 1,5-cyclooctadiene embed relaxes to its gas-phase twist conformer, whose two C=C bonds do NOT
    # both face one side, so MCHammer -- which nudges bond lengths, it does not flip a ring pucker --
    # cannot fold it into the bound "tub" (boat-like) form the metal needs. Pinning one carbon of
    # each eta2 alkene to its cis coordination site forces the ring to fold both double bonds toward
    # the metal, i.e. the boat conformer, before stk ever seats it. Detected generically as a
    # bidentate whose two donor groups are both eta2 (2-atom) pi-sites -- never hard-coded to COD.
    eta2_diene = (len(groups) == 2 and all(len(g) == 2 for g in groups) and len(ring_groups) == 0)
    flex_wrapper = (len(coord_atoms) >= 3 and len(ring_groups) < 2
                    and all(len(g) == 1 for g in groups)
                    and _backbone_rotatable(rdkit_mol, coord_atoms) >= _flex_threshold())
    if (_coord_map_enabled() and site_dirs is not None and len(site_dirs) == len(coord_atoms)
            and (flex_wrapper or eta2_diene)):
        import os

        from rdkit.Geometry import Point3D

        if eta2_diene and os.environ.get("MECOBI_COORD_MAP_DEBUG"):
            print(f"[coord-map] eta2-diene chelate {smiles!r}: pinning alkenes to cis sites "
                  f"(boat/tub conformation)")
        ml = 2.1  # generic M-L radius; MCHammer/xtb refine the exact bond length
        coord_map = {
            coord_atoms[i]: Point3D(*(ml * np.asarray(site_dirs[i], dtype=float)))
            for i in range(len(coord_atoms))
        }
        cparams = AllChem.ETKDGv3()
        cparams.randomSeed = 0xF00D
        cparams.SetCoordMap(coord_map)
        try:
            ok = AllChem.EmbedMolecule(rdkit_mol, params=cparams) == 0
        except Exception:  # infeasible pin set / RDKit internal -> fall through to free embed
            ok = False
        if ok:
            conf = rdkit_mol.GetConformer()
            pos_matrix = np.array(
                [list(conf.GetAtomPosition(i)) for i in range(rdkit_mol.GetNumAtoms())])
            return mol.with_position_matrix(pos_matrix)
        rdkit_mol.RemoveAllConformers()  # a partial/failed embed must not leak into the free path

    # Conformer ensemble for σ-chelates (denticity >= 2): the donor pre-organisation can
    # only curl ONE embed toward the metal, but a flexible multidentate often needs a
    # different backbone rotamer to seat every donor. Embed several, pre-organise each, and
    # keep the one whose donors reach a coordinating arrangement with least strain.
    #
    # Two triggers set the ensemble size (max wins):
    #  - AUTOMATIC (opt-in, default OFF — see _auto_ensemble_size): a denticity>=3 wrapper
    #    whose donor-to-donor skeleton is flexible (>= _flex_threshold rotatable bonds) gets
    #    _auto_ensemble_size() embeds when MECOBI_AUTO_CONFORMERS>1 is set. A
    #    rigid macrocyclic/planar core (backbone-rotatable ~0 — phthalocyanine, salen, cyclam)
    #    stays on the single deterministic embed, so its output is byte-identical to before:
    #    the ensemble only ever touches ligands that can actually re-fold, which is where the
    #    earlier blanket-ensemble regressions came from (rigid cores picked a distorted embed).
    #  - MANUAL: MECOBI_N_CONFORMERS > 1 forces an ensemble on EVERY σ-chelate (also arms the
    #    experimental site-directed pre-org above) — for A/B sweeps, applies regardless of
    #    flexibility.
    # Monodentates and the metallocene fold path always keep the single deterministic embed.
    auto_n = _auto_ensemble_size()
    auto = (
        auto_n if (
            auto_n > 1 and len(coord_atoms) >= 3 and len(ring_groups) < 2
            and _backbone_rotatable(rdkit_mol, coord_atoms) >= _flex_threshold()
        ) else 1
    )
    n_conf = max(_n_conformers(), auto)
    single = len(coord_atoms) < 2 or len(ring_groups) >= 2 or n_conf <= 1
    if single:
        if not _embed(rdkit_mol, params):
            raise RuntimeError(f"Failed to generate conformer for {smiles}")
        conf_ids = [rdkit_mol.GetConformer().GetId()]
    else:
        conf_ids = list(AllChem.EmbedMultipleConfs(rdkit_mol, numConfs=n_conf, params=params))
        if not conf_ids:  # embedding all failed -> the single deterministic embed
            if not _embed(rdkit_mol, params):
                raise RuntimeError(f"Failed to generate conformer for {smiles}")
            conf_ids = [rdkit_mol.GetConformer().GetId()]

    best_cid, best_score = conf_ids[0], None
    for cid in conf_ids:
        score = _preorganise(cid)
        if best_score is None or score < best_score:
            best_cid, best_score = cid, score

    conf = rdkit_mol.GetConformer(best_cid)
    pos_matrix = np.array(
        [list(conf.GetAtomPosition(i)) for i in range(rdkit_mol.GetNumAtoms())]
    )
    return mol.with_position_matrix(pos_matrix)
