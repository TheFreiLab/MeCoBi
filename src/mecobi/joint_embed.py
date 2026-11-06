"""Joint re-embedding of a crowded sphere of monodentates and chelates (on by default;
``MECOBI_JOINT_EMBED=0`` turns it off).

The site model embeds every ligand ALONE and then seats it rigidly on its site, so the bodies of
neighbouring ligands never see each other. For small ligands that is fine; for a sphere of bulky
monodentates it is not: Pt(PPh3)4 comes out of the raw stk placement with 78 inter-ligand atom
pairs closer than 1.6 A (phenyls threaded through one another, worst contact 0.24 A). MCHammer
then scatters the phosphines (P-Pt-P 79-135 deg), and no rigid rotation or metal-excluded UFF
untangles rings that pass through each other -- xtb is handed an unrelaxable geometry.

The repair is the one MetalloGen uses for every complex: embed the WHOLE complex in one distance-
geometry run (RDKit ``EmbedMolecule`` with a coordinate map), pinning only the metal and each
donor atom on its site. Every ligand atom then sits in the same bounds matrix, so the van der
Waals lower bounds between atoms of DIFFERENT ligands are honoured and the bulky groups come out
meshed instead of interpenetrating (Pt(PPh3)4: 0 pairs under 1.6 A, nearest contact 2.3 A, <1 s).

A CN2 complex of a single chelate is always re-embedded this way (no collapse needed): one
rigid conformer seated on two sites rarely reaches both, least of all a trans-spanning
diphosphine or macrocycle on a d10 metal (donors left 8-9 A out, or squeezed to 1.5 A).

Kept deliberately narrow:

* sigma ligands only: monodentates, and chelates of up to four donors (two interpenetrating
  BINAPs on Pt(0), ZIHHUT). A haptic cap (donor atoms bonded to each other) has its own
  placement and is never re-drawn, nor is a ligand of five or more donors or of more than
  ``_MAX_LIGAND_HEAVY`` heavy atoms (the embedding fails slowly on those);
* only when the assembly is actually collapsed (:func:`collapse_count`). A monodentate is judged
  where the pre-relax donor reposition will seat it; a chelate is judged where it IS -- chelates
  are not repositioned by default, and sliding one once per donor invents collapses that are
  not there;
* the donors are pinned along their RAW stk placement directions at their reference M-L
  distance, so the isomer and the site numbering are untouched. For a monodentate that direction
  IS the ideal site vector; a chelate's donors are pinned where its rigid placement put them (a
  rigid conformer does not reach every site exactly), not snapped to the ideal sites;
* the result replaces the assembly only if it is collapse-free, kept every bond length, did not
  fold a ligand onto itself, and preserved every ligand stereocentre, double-bond geometry and
  biaryl axis (:func:`_stereo_signature`).
"""
from __future__ import annotations

import os

import numpy as np

from . import optimize
from ._text import plural

_HARD_ANY = 1.0       # A: any two atoms of different ligands closer than this are interpenetrating
_HARD_HEAVY = 1.5     # A: ... or two heavy atoms closer than this
_MIN_BULK = 3         # non-donor heavy atoms that make a ligand "bulky"
_SEEDS = (7, 11, 23, 42)
_BOND_TOL = 0.25      # A: a topology bond may not change length by more than this
_MAX_DENTICITY = 4    # a ligand with more donors than this is never re-embedded
_MAX_LIGAND_HEAVY = 80
_SELF_CLASH = 2.2     # A: two heavy atoms of ONE ligand, >= 4 bonds apart, closer than this
_EMBED_TIMEOUT_S = 10  # per seed (RDKit >= 2024.03); a big pinned system can grind for a minute
_CHELATE_SEEDS = 2    # a sphere with chelates that will not embed fails slowly: try fewer seeds


def enabled() -> bool:
    return os.environ.get("MECOBI_JOINT_EMBED", "1") != "0"


def _topology(constructed, metal_symbol):
    atoms = list(constructed.get_atoms())
    elems = [a.__class__.__name__ for a in atoms]
    if metal_symbol not in elems:
        return None
    mi = elems.index(metal_symbol)
    bonds = [(b.get_atom1().get_id(), b.get_atom2().get_id()) for b in constructed.get_bonds()]
    donors = sorted({b if a == mi else a for a, b in bonds if mi in (a, b)})
    comp = np.array(optimize._components_excluding(bonds, len(atoms), mi))
    return elems, mi, bonds, donors, comp


def collapse_count(positions, elems, comp) -> int:
    """Interpenetrating atom pairs between DIFFERENT ligands: any pair closer than 1.0 A, or two
    heavy atoms closer than 1.5 A. Zero for any sane assembly (a bonded heavy pair is ~1.4-1.5 A,
    a non-bonded contact >= 2 A), so a non-zero count means ligand bodies pass through each
    other."""
    P = np.asarray(positions, float)
    lig = np.where(comp >= 0)[0]
    if len(lig) < 2:
        return 0
    d = np.linalg.norm(P[lig][:, None, :] - P[lig][None, :, :], axis=-1)
    other = np.triu(comp[lig][:, None] != comp[lig][None, :], 1)
    heavy = np.array([elems[i] != "H" for i in lig])
    hh = heavy[:, None] & heavy[None, :]
    return int((other & ((d < _HARD_ANY) | (hh & (d < _HARD_HEAVY)))).sum())


def _eligible(elems, donors, comp, bonds, single_chelate=False) -> bool:
    """Sigma ligands only (no haptic cap), none above ``_MAX_DENTICITY`` donors or
    ``_MAX_LIGAND_HEAVY`` heavy atoms. An all-monodentate sphere needs >= 3 ligands with >= 2 bulky
    (as before); a sphere with a chelate needs >= 2 ligands with >= 1 bulky."""
    donor_set = set(donors)
    ligs = sorted(set(comp[comp >= 0].tolist()))
    bonded = {(min(a, b), max(a, b)) for a, b in bonds}
    bulky, chelate = 0, False
    for c in ligs:
        members = np.where(comp == c)[0]
        dons = [int(i) for i in members if i in donor_set]
        if not dons or len(dons) > _MAX_DENTICITY:
            return False                      # stray fragment / too many donors to pin
        if any((min(a, b), max(a, b)) in bonded for k, a in enumerate(dons) for b in dons[k + 1:]):
            return False                      # haptic: its donor atoms are bonded to each other
        heavy = sum(1 for i in members if elems[i] != "H")
        if heavy > _MAX_LIGAND_HEAVY:
            return False
        chelate = chelate or len(dons) > 1
        if heavy - len(dons) >= _MIN_BULK:
            bulky += 1
    if single_chelate:
        return True                           # CN2: one chelate, fitted around the metal
    if chelate:
        return len(ligs) >= 2 and bulky >= 1
    return len(ligs) >= 3 and bulky >= 2


def _self_clashes(positions, elems, comp, bonds, mi) -> int:
    """Heavy-atom pairs of ONE ligand that are >= 4 bonds apart yet closer than ``_SELF_CLASH``:
    a ligand folded onto itself. :func:`collapse_count` only sees pairs of different ligands."""
    P = np.asarray(positions, float)
    n = len(elems)
    nbr = [[] for _ in range(n)]
    for a, b in bonds:
        if mi not in (a, b):
            nbr[a].append(b)
            nbr[b].append(a)
    heavy = [i for i in range(n) if comp[i] >= 0 and elems[i] != "H"]
    count = 0
    for i in heavy:
        near, frontier = {i}, [i]
        for _ in range(3):                    # atoms within 3 bonds are bonded/1,3/1,4 contacts
            frontier = [k for j in frontier for k in nbr[j] if k not in near]
            near.update(frontier)
        for j in heavy:
            if j > i and comp[j] == comp[i] and j not in near \
                    and np.linalg.norm(P[i] - P[j]) < _SELF_CLASH:
                count += 1
    return count


def _embed(raw, coord_map, seed):
    """One whole-complex distance-geometry embedding with ``coord_map`` pinned; positions or None."""
    from rdkit import Chem
    from rdkit.Chem import AllChem, rdDistGeom
    from rdkit.Geometry import Point3D

    mol = raw.to_rdkit_mol()
    try:
        Chem.SanitizeMol(mol)
    except Exception:  # noqa: BLE001 -- a metal's valence can fail strict sanitisation
        mol.UpdatePropertyCache(strict=False)
        Chem.SanitizeMol(mol, Chem.SANITIZE_ALL ^ Chem.SANITIZE_PROPERTIES, catchErrors=True)
    # ligand stereocentres are read off the assembled coordinates so the embedding keeps them
    Chem.AssignStereochemistryFrom3D(mol)
    params = rdDistGeom.EmbedParameters()
    params.useRandomCoords = True          # required for a big, pinned system to converge
    params.maxIterations = 200
    params.ignoreSmoothingFailures = True
    params.useBasicKnowledge = True        # keeps aromatic rings flat
    params.randomSeed = seed
    if hasattr(params, "timeout"):
        params.timeout = _EMBED_TIMEOUT_S
    params.SetCoordMap({i: Point3D(*map(float, p)) for i, p in coord_map.items()})
    try:
        if AllChem.EmbedMolecule(mol, params) != 0:
            return None, mol
    except Exception:  # noqa: BLE001
        return None, mol
    return np.asarray(mol.GetConformer().GetPositions(), float), mol


def _stereo_signature(raw, positions):
    """What the embedding must not change, read off the 3D coordinates: tetrahedral centres,
    double-bond E/Z, and the sense of every biaryl axis (a single bond joining two rings, as in
    BINAP -- atropisomers have no stereocentre for RDKit to label)."""
    from rdkit import Chem
    from rdkit.Chem import rdMolTransforms

    mol = raw.to_rdkit_mol()
    conf = mol.GetConformer()
    for i, p in enumerate(positions):
        conf.SetAtomPosition(i, tuple(map(float, p)))
    try:
        mol.UpdatePropertyCache(strict=False)
        Chem.FastFindRings(mol)
        Chem.AssignStereochemistryFrom3D(mol)
        centres = sorted(Chem.FindMolChiralCenters(mol, includeUnassigned=False,
                                                   useLegacyImplementation=False))
        double = sorted((b.GetBeginAtomIdx(), b.GetEndAtomIdx(), str(b.GetStereo()))
                        for b in mol.GetBonds()
                        if b.GetStereo() not in (Chem.BondStereo.STEREONONE,
                                                 Chem.BondStereo.STEREOANY))
        axes = []
        for b in mol.GetBonds():
            a1, a2 = b.GetBeginAtom(), b.GetEndAtom()
            if b.IsInRing() or not (a1.IsInRing() and a2.IsInRing()):
                continue
            n1 = sorted(x.GetIdx() for x in a1.GetNeighbors() if x.GetIdx() != a2.GetIdx())
            n2 = sorted(x.GetIdx() for x in a2.GetNeighbors() if x.GetIdx() != a1.GetIdx())
            if len(n1) < 2 or len(n2) < 2:
                continue
            dih = rdMolTransforms.GetDihedralDeg(conf, n1[0], a1.GetIdx(), a2.GetIdx(), n2[0])
            if 30.0 < abs(dih) < 150.0:        # a twisted axis has a sense; a flat one has none
                axes.append((a1.GetIdx(), a2.GetIdx(), dih > 0))
        return centres, double, sorted(axes)
    except Exception:  # noqa: BLE001
        return None


def _same_stereo(before, after) -> bool:
    """Centres and E/Z identical; every biaryl axis twisted in BOTH keeps its sense."""
    if before is None or after is None:
        return before is None
    if before[0] != after[0] or before[1] != after[1]:
        return False
    sense = {(a, b): s for a, b, s in after[2]}
    return all(sense.get((a, b), s) == s for a, b, s in before[2])


def joint_embed(make, constructed, metal_symbol, metal_ox=None, cn=None):
    """``(constructed, note)``: the assembly re-embedded jointly when it is a collapsed sphere
    of monodentates/chelates, else the input unchanged with ``note=None``.

    ``make(mchammer: bool)`` rebuilds the assembly (as :func:`pipeline._build_with_fallback`
    takes it); the raw stk placement it returns for ``False`` supplies the ideal site positions
    the donors are pinned on. Never raises."""
    if not enabled():
        return constructed, None
    try:
        topo = _topology(constructed, metal_symbol)
        if topo is None:
            return constructed, None
        elems, mi, bonds, donors, comp = topo
        # A CN2 complex of ONE chelate: its rigid conformer, seated on the two sites, rarely puts
        # both donors at bonding distance on them (a trans-spanning diphosphine on Pd(0), a
        # macrocycle on Ag(I): donors 8-9 A out, or squeezed to 1.5 A). Always fit the ligand
        # around the metal instead, donors pinned on their sites at the reference M-L distance.
        single = (cn == 2 and len(donors) == 2 and len(set(comp[comp >= 0].tolist())) == 1)
        if not _eligible(elems, donors, comp, bonds, single_chelate=single):
            return constructed, None
        # The sphere the pre-relax steps will make of this assembly: a MONODENTATE stranded beyond
        # its reference M-L distance is slid rigidly in to it (same rule and slack as
        # optimize.reposition_stranded_monodentates), so a collapse that only appears once
        # MCHammer's pushed-out ligands are pulled back in (RhCl(PPh3)3) is seen. One seated SHORT
        # of it is judged at the reference too: the site model leaves a halide on a ~1.25 A shell
        # until ff_declash seats it, and judged there it "collapses" onto any chelate atom near
        # the metal (Pd(dppe)Cl2 under RDKit 2026.03: a dppe H at 0.64 A from Pd, 0.89 A from Cl).
        # A chelate is judged where it is: it is not repositioned by default, and sliding it once
        # per donor (along 2-4 different vectors) fabricates contacts.
        Pa = np.array(constructed.get_position_matrix(), float)
        n_don = {c: sum(1 for x in donors if comp[x] == c) for c in set(comp[donors].tolist())}
        atoms = [(e, tuple(p)) for e, p in zip(elems, Pa.tolist())]
        target = {}
        for d in donors:
            v = Pa[d] - Pa[mi]
            dist = float(np.linalg.norm(v))
            if dist < 1e-6:
                return constructed, None
            ref = optimize._restraint_reference(dist, metal_symbol, elems[d], ox=metal_ox, cn=cn,
                                                multiple_bond_ok=not single)
            target[d] = ref if (single or dist - ref > 0.3) else dist
            if n_don[comp[d]] == 1:
                seat = target[d]
                if not optimize._can_multiple_bond(atoms, d, mi):   # a squeezed halide/amine
                    seat = optimize._restraint_reference(
                        dist, metal_symbol, elems[d], ox=metal_ox, cn=cn, multiple_bond_ok=False)
                    seat = seat if abs(dist - seat) > 0.3 else dist
                Pa[comp == comp[d]] += v / dist * (seat - dist)
        before = collapse_count(Pa, elems, comp)
        if before == 0 and not single:
            return constructed, None

        raw, _ = make(False)                              # donors on the ideal site vectors
        P0 = np.asarray(raw.get_position_matrix(), float)
        if len(P0) != len(elems):
            return constructed, None
        coord_map = {mi: P0[mi]}
        for d in donors:                                  # ideal direction, seated distance
            v = P0[d] - P0[mi]
            dist = float(np.linalg.norm(v))
            if dist < 1e-6:
                return constructed, None
            coord_map[d] = P0[mi] + v / dist * target[d]

        lig_bonds = [(a, b) for a, b in bonds if mi not in (a, b)]
        d0 = np.array([np.linalg.norm(P0[a] - P0[b]) for a, b in lig_bonds])
        stereo0 = _stereo_signature(raw, P0)
        self0 = _self_clashes(P0, elems, comp, bonds, mi)
        best = None
        seeds = _SEEDS[:_CHELATE_SEEDS] if (max(n_don.values()) > 1 and not single) else _SEEDS
        for seed in seeds:
            P, _mol = _embed(raw, coord_map, seed)
            if P is None:
                continue
            d1 = np.array([np.linalg.norm(P[a] - P[b]) for a, b in lig_bonds])
            if len(d0) and float(np.max(np.abs(d1 - d0))) > _BOND_TOL:
                continue                                  # a bond was stretched/crushed
            if not _same_stereo(stereo0, _stereo_signature(raw, P)):
                continue                      # a stereocentre, double bond or biaryl axis flipped
            if _self_clashes(P, elems, comp, bonds, mi) > self0:
                continue                                  # a ligand folded onto itself
            n = collapse_count(P, elems, comp)
            if best is None or n < best[0]:
                best = (n, P)
            if n == 0:
                break
        if best is None or best[0] != 0:
            return constructed, None                      # no clean embedding -> keep the assembly
        if single:
            return raw.with_position_matrix(best[1]), (
                "CN2 chelate: ligand re-embedded around the metal (distance geometry, both donors "
                "pinned on their sites at the reference M-L distance).")
        note = (f"crowded sphere: {plural(before, 'interpenetrating inter-ligand atom pair')} "
                f"in the assembly; re-embedded the whole complex jointly (distance geometry, metal "
                f"and donors pinned on their sites) so the ligand bodies mesh.")
        return raw.with_position_matrix(best[1]), note
    except Exception:  # noqa: BLE001 -- an assembly-time repair must never fail the build
        return constructed, None
