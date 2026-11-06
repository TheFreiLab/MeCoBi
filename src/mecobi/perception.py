"""Ligand perception — pydentate wrapper.

Sole entry point to pydentate for the core (mirrors the prototype invariant: no
build code calls pydentate directly). Fills donor atoms / denticity / arene flag
/ formal charge onto a :class:`~mecobi.model.Ligand`.

Rules:
    - Over-prediction: pydentate may return more donors than the true denticity.
      When an ``expected_denticity`` is known, deterministically **trim to the
      top-N donors by probability**. Automatic, not a user choice.
    - Cp / arene ligands: pydentate does NOT handle eta-bonding. When a ligand is
      flagged/declared as an arene, denticity is **hardcoded to 3**. Tier-1
      auto-detection covers *standalone* all-carbon caps — aromatic arenes
      (benzene/cymene) and Cp/Cp* in both anionic-aromatic and neutral-diene
      forms (see ``_carbocyclic_arene_atoms``). Fully robust classification of an
      eta-cap embedded in a larger functionalised ligand stays DEFERRED (a free
      SMILES can't always tell an eta-cap from a spectator aromatic ring); those
      are honoured via a caller ``is_arene`` flag or a donor override.
    - KNOWN LIMITATION — eta2-alkene chelating dienes (e.g. 1,5-cyclooctadiene /
      COD, ``C1=C\\CC/C=C\\CC/1``): pydentate returns all four alkene carbons as
      separate sigma donors, so COD is perceived as a **tetradentate (4 x C)**
      rather than a bidentate diene (two eta2-alkene sites). ``Pt(COD)Cl2`` then
      comes out CN6/octahedral instead of CN4/square-planar. Collapsing each
      coordinating C=C to one eta2 site would need both a perception rule AND
      assembly support for placing an alkene midpoint on a site (the arene cap
      uses 3 real ring atoms, not a midpoint) — DEFERRED. The 3D assigner surfaces
      it honestly (the donors read as ``C -> site``), so it is visible, not silent.
    - Single-atom ligands (e.g. ``[Cl-]``): trivially monodentate; pydentate is
      skipped (the GNN is not meaningful for a lone atom).

pydentate (Kulik Group, MIT) is vendored at :mod:`mecobi._pydentate` so the core
is a standalone package; see that module for licence and citation.
"""

from __future__ import annotations

import os

from rdkit import Chem

from .model import Complex, Ligand

ARENE_DENTICITY = 3


class PerceptionError(RuntimeError):
    """Raised when pydentate perception fails for a ligand."""


class SmilesParseError(PerceptionError):
    """Raised when RDKit cannot read a ligand SMILES (message is user-facing as is)."""


# --------------------------------------------------------------------------- #
# Perception
# --------------------------------------------------------------------------- #

def formal_charge(smiles: str) -> int:
    """Formal charge of a SMILES (0 if it fails to parse)."""
    mol = Chem.MolFromSmiles(smiles)
    return Chem.GetFormalCharge(mol) if mol is not None else 0


# Cache by the exact input SMILES: donor indices and per-atom probabilities refer
# to that string's atom order. Equivalent SMILES can number atoms differently,
# so sharing a canonical key would silently attach predictions to the wrong atoms.
# Repeated identical inputs still reuse inference in both lookup and prewarming.
_PYDENTATE_CACHE: dict[str, tuple] = {}


def _compute_pydentate(smiles: str):
    """Run pydentate on one SMILES; return (coord_num, coord_atoms, atom_probs).

    The heavy call (torch). No caching here — callers cache by exact input SMILES.
    """
    from ._pydentate.pydentate_lite import pydentate_lite  # lazy: heavy torch import

    try:
        result = pydentate_lite(smiles)
    except Exception as exc:  # pydentate raises bare exceptions on odd inputs
        raise PerceptionError(f"pydentate failed for {smiles!r}: {exc}") from exc

    coord_num, coord_atoms = int(result[0]), list(result[1])
    summary = result[8]
    atom_probs = list(summary["coordinating_atoms_probabilities"].iloc[0])
    return coord_num, coord_atoms, atom_probs


def _run_pydentate(smiles: str):
    """pydentate for one SMILES, cached without changing its atom order."""
    hit = _PYDENTATE_CACHE.get(smiles)
    if hit is not None:
        return hit
    result = _compute_pydentate(smiles)
    _PYDENTATE_CACHE[smiles] = result
    return result


def _pydentate_worker(smiles: str):
    """Process-pool entry point: compute one ligand, swallowing failures (they are
    re-raised properly later if the ligand is actually perceived)."""
    try:
        return _compute_pydentate(smiles)
    except Exception:
        return None


def _resolve_perception_workers(workers: int | None, n: int) -> int:
    """How many worker processes to use for a batch prewarm.

    ``workers`` (or ``MECOBI_PERCEPTION_WORKERS``) opts in; default 1 (serial).
    Only honoured where ``fork`` is available (Linux): with ``spawn`` (Windows/
    macOS) each worker re-imports torch, so the startup cost outweighs the win.
    """
    import multiprocessing as mp

    if workers is None:
        try:
            workers = int(os.environ.get("MECOBI_PERCEPTION_WORKERS", "0"))
        except ValueError:
            workers = 0
    if workers is None or workers <= 1:
        return 1
    if "fork" not in mp.get_all_start_methods():
        return 1
    return max(1, min(workers, n, os.cpu_count() or 1))


def prewarm_pydentate(smiles_iter, workers: int | None = None) -> None:
    """Fill the pydentate cache for many ligands ahead of a batch parse.

    With workers > 1 on a fork platform, the unique input strings are inferred in
    parallel across processes (the GIL makes threads useless here — the work is
    RDKit/Python featurisation). Serial and side-effect-free everywhere else, so
    this is always safe to call; it only ever speeds a repeated/large batch.
    """
    uniq: list[str] = []
    seen: set[str] = set()
    for s in smiles_iter:
        if s in seen or s in _PYDENTATE_CACHE:
            continue
        seen.add(s)
        uniq.append(s)
    if not uniq:
        return

    n = _resolve_perception_workers(workers, len(uniq))
    if n <= 1:
        for s in uniq:
            try:
                _PYDENTATE_CACHE[s] = _compute_pydentate(s)
            except Exception:
                pass
        return

    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor

    ctx = mp.get_context("fork")
    with ProcessPoolExecutor(max_workers=n, mp_context=ctx) as ex:
        for s, res in zip(uniq, ex.map(_pydentate_worker, uniq, chunksize=4)):
            if res is not None:
                _PYDENTATE_CACHE[s] = res


def _trim_to_top_n(coord_atoms: list[int], atom_probs: list[float], n: int) -> list[int]:
    """Keep the ``n`` donors with the highest per-atom probability."""
    ranked = sorted(coord_atoms, key=lambda idx: atom_probs[idx], reverse=True)
    return sorted(ranked[:n])


# A neutral cyclopentadiene ring (Cp/Cp* as users commonly draw it: one sp3
# vertex, two ring C=C). RDKit does NOT flag this as aromatic, so the aromatic
# pass below misses it; this SMARTS catches the eta5 carbocyclic cap directly.
_CP_DIENE = Chem.MolFromSmarts("[#6]1=[#6][#6]=[#6][#6]1")


def _carbocyclic_arene_atoms(mol: Chem.Mol) -> list[int] | None:
    """Return the ring-atom indices of a standalone all-carbon eta-cap, else None.

    Fires for a pure-hydrocarbon molecule whose coordinating ring is either:
      (a) an aromatic carbocycle — benzene / alkyl-arene (cymene) eta6, or an
          anionic ``[c-]`` cyclopentadienyl (Cp/Cp*) eta5; or
      (b) a neutral cyclopentadiene ring (Cp/Cp* drawn as a diene, which RDKit
          does not treat as aromatic).

    Conservative on purpose: it only fires when the *whole molecule* is C/H, so
    any heteroatom that could sigma-donate (or any functional group) defers to a
    manual ``Ligand.is_arene`` / donor override. This is a fundamental limit — a
    free-ligand SMILES cannot always distinguish an eta-cap from a spectator
    aromatic ring inside a larger, functionalised ligand.
    """
    if any(a.GetAtomicNum() not in (1, 6) for a in mol.GetAtoms()):
        return None
    ring_info = mol.GetRingInfo()
    # (a) aromatic carbocycle: benzene/cymene (eta6), anionic [c-] Cp (eta5).
    for ring in ring_info.AtomRings():
        if 5 <= len(ring) <= 6 and all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring):
            return sorted(ring)
    # (b) neutral cyclopentadiene ring (eta5 Cp/Cp* drawn as a diene).
    match = mol.GetSubstructMatch(_CP_DIENE)
    if match:
        return sorted(match)
    return None


def _sigma_aryl_carbanions(mol: Chem.Mol) -> list[int]:
    """Anionic, H-free, ring-only-bonded carbons of aromatic 6-membered carbocycles.

    ``[c-]1ccccc1`` (phenyl) and ``Cc1cc[c-]cc1`` (tolyl) are sigma-aryl carbanions (M-Ph), not
    eta6 arenes: the negative carbon lost its H to the metal. An eta6 arene is neutral, and the
    CSD's mislabelled eta-arene "false carbanion" keeps its H (``[cH-]``), so neither matches.
    Only 6-rings: a 5-ring ``[c-]`` is a Cp anion (Cp* carries its charge on a methylated C)."""
    hits: list[int] = []
    for ring in mol.GetRingInfo().AtomRings():
        if len(ring) != 6:
            continue
        atoms = [mol.GetAtomWithIdx(i) for i in ring]
        if any(a.GetAtomicNum() != 6 or not a.GetIsAromatic() for a in atoms):
            continue
        hits += [a.GetIdx() for a in atoms if a.GetFormalCharge() == -1
                 and a.GetTotalNumHs() == 0 and a.GetDegree() == 2 and a.GetIdx() not in hits]
    return sorted(hits)


def _embedded_cyclopentadienyl(mol: Chem.Mol) -> list[int] | None:
    """Ring atoms of a cyclopentadienyl (Cp) anion, even inside a larger ligand.

    A 5-membered all-carbon ring bearing a negative formal charge on a ring atom
    (the ``[CH-]`` of ``C1=C[CH-]C=C1``) — or an aromatic ``[c-]`` ring — is a
    cyclopentadienyl anion, which is essentially always an η5 cap. Unlike
    :func:`_carbocyclic_arene_atoms` (whole-molecule hydrocarbons only) this fires
    for a *substituted / functionalised* Cp (ferrocenes like ferroquine), where
    pydentate mis-assigns the ring as several σ donors or picks a pendant donor.
    """
    for ring in mol.GetRingInfo().AtomRings():
        if len(ring) != 5:
            continue
        atoms = [mol.GetAtomWithIdx(i) for i in ring]
        if any(a.GetAtomicNum() != 6 for a in atoms):
            continue
        if any(a.GetFormalCharge() < 0 for a in atoms) or all(a.GetIsAromatic() for a in atoms):
            return sorted(ring)
    return None


def _selected_carbocyclic_ring(mol: Chem.Mol, atoms: list[int]) -> bool:
    """True if ``atoms`` are exactly the members of one all-carbon 5- or 6-ring.

    Lets a user select the five carbons of a cyclopentadienyl (or six of an
    arene) by clicking the ring and have it treated as an eta5/eta6 cap
    (denticity 3) instead of 5/6 separate sigma donors — even when the ring is
    embedded in a larger, functionalised ligand where auto-detection defers.
    """
    if len(atoms) not in (5, 6):
        return False
    if any(mol.GetAtomWithIdx(i).GetAtomicNum() != 6 for i in atoms):
        return False
    aset = set(atoms)
    return any(set(ring) == aset for ring in mol.GetRingInfo().AtomRings())


def _pi_sites(mol: Chem.Mol, coord_atoms: list[int]) -> list[list[int]]:
    """Contiguous η-bonded π regions among the donor CARBONS, each collapsed to ONE coordination
    site at its centroid — the single, uniform representation for every hapticity ηⁿ:

      * a pair joined by C=C / C#C is an **η²** alkene/alkyne;
      * an aromatic ring is **η⁵/η⁶/η⁷/η⁸** (Cp, arene, tropylium, cyclooctatetraene);
      * a conjugated open chain is **η³/η⁴** (allyl, butadiene).

    Two donor carbons belong to the SAME site iff joined by an aromatic, double, triple, or
    conjugated bond, so two ISOLATED alkenes on one ligand (COD) stay two η² sites, but a conjugated
    diene collapses to one η⁴ site. Heteroatom donors and lone sp³ carbons are σ sites (one atom
    each), left to the caller. Returns one sorted atom list per π-site (a site of ≥ 2 atoms).
    """
    pi_bond = (Chem.BondType.DOUBLE, Chem.BondType.TRIPLE)
    adj: dict[int, set[int]] = {a: set() for a in coord_atoms
                                if mol.GetAtomWithIdx(a).GetAtomicNum() == 6}
    for b in mol.GetBonds():
        i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
        if i in adj and j in adj and (
                b.GetIsAromatic() or b.GetBondType() in pi_bond or b.GetIsConjugated()):
            adj[i].add(j)
            adj[j].add(i)
    seen: set[int] = set()
    sites: list[list[int]] = []
    for start in adj:
        if start in seen or not adj[start]:
            continue
        comp, stack = [], [start]
        seen.add(start)
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        if len(comp) >= 2:
            sites.append(sorted(comp))
    return sites


def _in_nonaromatic_cc(mol: Chem.Mol, idx: int) -> bool:
    """Is atom ``idx`` a carbon that is part of a non-aromatic C=C double bond (an alkene)?"""
    a = mol.GetAtomWithIdx(idx)
    if a.GetAtomicNum() != 6:
        return False
    for b in a.GetBonds():
        if (b.GetBondType() == Chem.BondType.DOUBLE and not b.GetIsAromatic()
                and b.GetOtherAtom(a).GetAtomicNum() == 6):
            return True
    return False


def _snap_diene_donors(mol: Chem.Mol, coord_atoms: list[int]) -> list[int]:
    """Recover the η²-alkene sites of a chelating diene whose donor atoms were given as the
    saturated (allylic CH₂) carbons instead of the alkene carbons — the classic COD index
    mismatch (donors indexed against one SMILES traversal, ``C1CC=CCCC=C1`` → [2,3,6,7], but
    stored against another, ``C1=CCCC=CCC1`` where those are CH₂). Each such carbon is remapped
    to its adjacent non-aromatic alkene carbon so :func:`_pi_sites` can pair them into η² sites.

    Fires ONLY for the unambiguous diene signature: at least four carbon donors that form no π-site
    as given, each bonded to exactly one alkene carbon, and where the remap yields ≥2 clean η²
    sites. A single sp3 σ-carbon donor (an alkyl, a cyclometalated benzyl — whose neighbour is an
    AROMATIC ring, excluded here) never matches, so genuine σ-carbon donors are untouched."""
    covered = {a for s in _pi_sites(mol, coord_atoms) for a in s}
    orphans = [a for a in coord_atoms
               if a not in covered and mol.GetAtomWithIdx(a).GetAtomicNum() == 6]
    if len(orphans) < 4:                       # < 2 sites' worth -> not a diene, leave alone
        return coord_atoms
    remap = {}
    for a in orphans:
        alkene_nb = [nb.GetIdx() for nb in mol.GetAtomWithIdx(a).GetNeighbors()
                     if _in_nonaromatic_cc(mol, nb.GetIdx())]
        if len(alkene_nb) != 1:                # ambiguous / no alkene neighbour -> bail (whole lig)
            return coord_atoms
        remap[a] = alkene_nb[0]
    snapped = sorted((set(coord_atoms) - set(orphans)) | set(remap.values()))
    return snapped if len(_pi_sites(mol, snapped)) >= 2 else coord_atoms


def _reprotonate_eta2_terminal_alkynes(ligand: Ligand, mol: Chem.Mol, sites: list[list[int]]) -> None:
    """Restore the terminal C–H of an η²-coordinated alkyne mis-mined as an acetylide.

    A neutral terminal alkyne HC≡C–R binding side-on (η²) is often mined with its terminal H
    stripped, i.e. drawn as the acetylide anion ``[C-]#C–R`` (BATKOX: the built structure then has
    no CH where the crystal has one, and the ligand carries a spurious −1). When a π-site is a C≡C
    whose carbon is a TERMINAL carbanion (degree 1, charge −1), re-protonate it to the neutral
    alkyne: set the charge to 0 (RDKit fills the implicit H), rewrite the SMILES with atom order
    preserved (so coord_atoms/pi_sites indices still hold), and recompute the ligand's formal
    charge. A σ-acetylide (only the terminal C is a donor, denticity 1, NOT a 2-atom π-site) is left
    alone — there the carbanion is real. Fires on the eta2 diene/alkyne path only."""
    changed = False
    rw = Chem.RWMol(mol)
    pi_atoms = {a for s in sites for a in s}
    for a in list(pi_atoms):
        at = rw.GetAtomWithIdx(a)
        if (at.GetAtomicNum() == 6 and at.GetFormalCharge() == -1 and at.GetDegree() == 1
                and any(b.GetBondType() == Chem.BondType.TRIPLE for b in at.GetBonds())):
            at.SetFormalCharge(0)
            at.SetNoImplicit(False)
            changed = True
    if not changed:
        return
    try:
        m2 = rw.GetMol()
        Chem.SanitizeMol(m2)
        ligand.smiles = Chem.MolToSmiles(m2, canonical=False)  # keep the heavy-atom order
        ligand.formal_charge = sum(a.GetFormalCharge() for a in m2.GetAtoms())
    except Exception:  # noqa: BLE001  (re-protonation failed -> keep the acetylide as given)
        pass


def _set_denticity(ligand: Ligand, mol: Chem.Mol) -> None:
    """Set denticity from coord_atoms, collapsing each η²-alkene/alkyne π-bond to a
    single coordination site (denticity counts π-sites once, not per carbon)."""
    snapped = _snap_diene_donors(mol, ligand.coord_atoms)
    if snapped != ligand.coord_atoms:          # diene given as CH₂ carbons -> use the alkene carbons
        ligand.coord_atoms = snapped
        if ligand.donor_override is not None:  # keep effective_donors (assembly) consistent
            ligand.donor_override = snapped
    sites = _pi_sites(mol, ligand.coord_atoms)
    ligand.pi_sites = sites
    pi_atoms = {a for s in sites for a in s}
    n_sigma = sum(1 for a in ligand.coord_atoms if a not in pi_atoms)
    ligand.denticity = n_sigma + len(sites)
    _reprotonate_eta2_terminal_alkynes(ligand, mol, sites)


def _set_eta_cap(ligand: Ligand, ring: list[int]) -> None:
    """Represent a perceived η-cap (a whole Cp/arene ring) as ONE centroid coordination site
    (denticity 1) — the SAME model an explicit donor override uses. This is the standardisation:
    an ηⁿ ligand is one site at the centroid of its coordinating region whatever path found it, so
    a metallocene is CN2 / linear in auto-perception too (it used to be CN6 via a facial triad,
    while an override gave CN2 — the same ferrocene had two answers). The whole ring is the π-site;
    ``is_arene`` is cleared so the assembly builds a centroid vertex, not a facial-triad. Unlike the
    generic :func:`_pi_sites` grouping, the detector's full ring is trusted as one site (a neutral
    cyclopentadiene's sp³-broken conjugation would otherwise split it into two η² fragments)."""
    ligand.coord_atoms = sorted(ring)
    ligand.pi_sites = [sorted(ring)]
    ligand.denticity = 1
    ligand.is_arene = False


def _covered_cap_rings(mol: Chem.Mol, atoms: list[int], min_cover: int = 3) -> list[list[int]]:
    """All-carbon 5-/6-rings that the selected donor atoms substantially cover.

    Each such ring is an η-cap that occupies ONE coordination site at its centroid
    (denticity 1), built via a multi-bonder functional group like an η²-alkene.
    Returns the FULL ring-atom list per cap (one per cap; a bis-Cp ligand yields two).

    A crystal donor list names only the ring carbons inside the M–C cutoff — often a
    SUBSET of a genuine η5/η6 cap (an indenyl whose crystal contacts are 4 of its 5
    Cp carbons, a tilted η6 arene down to its 3 closest). When ``min_cover`` or more
    of an all-carbon ring's atoms are selected, the WHOLE ring is one centroid cap;
    without this the leftover carbons are mis-read as separate σ donors / partial
    η²-alkenes and the ring wraps the metal. Rings are taken greedily by coverage so
    a fused system (indenyl: Cp + benzo) picks the best-covered ring and never
    double-counts a shared atom. ``min_cover=3`` — three coordinating carbons of one
    carbocycle is an unambiguous face cap (η3+), never a σ set.
    """
    aset = set(atoms)
    candidates = []
    for ring in mol.GetRingInfo().AtomRings():
        if len(ring) not in (5, 6):
            continue
        if not all(mol.GetAtomWithIdx(i).GetAtomicNum() == 6 for i in ring):
            continue
        cover = len(aset & set(ring))
        if cover >= min_cover:
            candidates.append((cover, sorted(ring)))
    candidates.sort(key=lambda c: -c[0])  # most-covered ring wins a shared atom
    chosen: list[list[int]] = []
    claimed: set[int] = set()
    for _cover, ring in candidates:
        if claimed & set(ring):
            continue
        chosen.append(ring)
        claimed.update(ring)
    return chosen


def cyclopentadienyl_cap_rings(smiles: str) -> list[list[int]]:
    """Cyclopentadienyl (Cp) η-cap rings in a ligand: 5-membered all-carbon rings
    that are aromatic or carbanionic.

    Auto-perception marks at most ONE ring per ligand as an η-cap, so a ligand
    carrying TWO of these (an ansa-metallocene, a Cp+pyridine ligand) is silently
    under-coordinated — the web layer uses this to warn that both rings must be set
    as centroid caps before a batch build. Restricted to 5-membered Cp rings on
    purpose: a neutral 6-membered aromatic (a pendant phenyl / a fused benzo, as in
    ferroquine's quinoline) is almost always a non-coordinating substituent, so
    counting it would wrongly flag ordinary metallocenes.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return []
    rings = []
    for ring in mol.GetRingInfo().AtomRings():
        atoms = [mol.GetAtomWithIdx(i) for i in ring]
        if len(ring) != 5 or not all(a.GetAtomicNum() == 6 for a in atoms):
            continue
        if all(a.GetIsAromatic() for a in atoms) or any(a.GetFormalCharge() < 0 for a in atoms):
            rings.append(sorted(ring))
    return rings


def perceive(ligand: Ligand, *, expected_denticity: int | None = None) -> Ligand:
    """Populate donor atoms / denticity / arene flag / formal charge in place.

    Precedence: explicit donor override > declared arene > single-atom ligand >
    conservative arene detection > pydentate (with optional top-N trim).
    """
    smiles = ligand.smiles
    ligand.formal_charge = formal_charge(smiles)
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise SmilesParseError(f"Can't read SMILES {smiles!r}.")

    # 1. Caller pinned the donors (e.g. from the 2D donor-correction panel).
    if ligand.donor_override is not None:
        ligand.coord_atoms = sorted(ligand.donor_override)
        # Each carbocyclic 5-/6-ring that the donors substantially cover is an η-cap
        # occupying ONE coordination site at its centroid (denticity 1, built as a
        # multi-bonder centroid group). So a metallocene is a linear 2-coordinate build,
        # multi-Cp / mixed cap+σ ligands (ansa-metallocenes, Cp+pyridine) work, and a
        # crystal donor list that names only some of a cap's ring carbons still collapses
        # to the whole ring (not partial σ/η² fragments). Auto-perception is unchanged;
        # this centroid convention applies only to explicit donor overrides.
        rings = _covered_cap_rings(mol, ligand.coord_atoms)
        if rings:
            ring_atoms = {a for r in rings for a in r}
            # Absorb the full ring into the donor set so the centroid FG uses every ring
            # carbon even when the crystal named only a subset within the M–C cutoff.
            ligand.coord_atoms = sorted(set(ligand.coord_atoms) | ring_atoms)
            sigma = [a for a in ligand.coord_atoms if a not in ring_atoms]
            ligand.pi_sites = [list(r) for r in rings]
            ligand.denticity = len(rings) + len(sigma)
            ligand.is_arene = False
        elif ligand.is_arene:
            _set_eta_cap(ligand, ligand.coord_atoms)   # declared cap, no covered ring -> centroid
        else:
            _set_denticity(ligand, mol)
        return ligand

    # 2. Caller declared this an eta-arene / Cp -> one centroid site.
    if ligand.is_arene:
        ring = _carbocyclic_arene_atoms(mol)
        _set_eta_cap(ligand, ring if ring is not None else (ligand.coord_atoms or []))
        return ligand

    # 3. Single-atom ligand (halide, etc.) -> trivially monodentate.
    if mol.GetNumAtoms() == 1:
        ligand.coord_atoms = [0]
        ligand.denticity = 1
        ligand.is_arene = False
        return ligand

    # 3b. Neutral dihalogen (I2, Br2, Cl2, ICl, IBr) -> end-on σ through ONE halogen (van Koten's
    # Pt(NCN)(I)(eta1-I2), PIDRIE). pydentate finds no donor in a bare X-X molecule. For an
    # interhalogen the heavier, softer, less electronegative atom binds (I of ICl).
    if (mol.GetNumAtoms() == 2 and all(a.GetAtomicNum() in (9, 17, 35, 53) for a in mol.GetAtoms())
            and all(a.GetFormalCharge() == 0 for a in mol.GetAtoms())):
        ligand.coord_atoms = [max(range(2), key=lambda i: mol.GetAtomWithIdx(i).GetAtomicNum())]
        ligand.denticity = 1
        ligand.is_arene = False
        return ligand

    # 4. Cyclopentadienyl anion (even substituted / embedded) -> eta5 cap (one centroid site). A Cp
    # anion is an unambiguous eta5 signal, so this fires before pydentate — which otherwise
    # mis-perceives a substituted Cp (ferroquine) as sigma donors.
    cp = _embedded_cyclopentadienyl(mol)
    if cp is not None:
        _set_eta_cap(ligand, cp)
        return ligand

    # 5. Conservative pure-hydrocarbon aromatic ring -> eta-arene, one centroid site. A sigma-aryl
    # carbanion (phenyl/tolyl/biphenyl-diyl) is a hydrocarbon aromatic too, but binds through its
    # anionic carbon(s): take those as sigma donors instead (Pb/Sn/Bi aryls were built as eta6 caps).
    sigma_aryl = (_sigma_aryl_carbanions(mol)
                  if all(a.GetAtomicNum() in (1, 6) for a in mol.GetAtoms()) else [])
    if sigma_aryl:
        ligand.coord_atoms = sigma_aryl
        ligand.is_arene = False
        _set_denticity(ligand, mol)
        return ligand
    ring = _carbocyclic_arene_atoms(mol)
    if ring is not None:
        _set_eta_cap(ligand, ring)
        return ligand

    # 5. Normal path: pydentate, with optional trim to expected denticity.
    coord_num, coord_atoms, atom_probs = _run_pydentate(smiles)
    # An embedded Cp/arene cap (e.g. the substituted cyclopentadienyl of
    # ferroquine): pydentate returns the whole ring as separate sigma donors.
    # If they are exactly an all-carbon 5-/6-ring, it is an eta5/eta6 cap
    # (one centroid site) — collapse it before any top-N trim.
    if _selected_carbocyclic_ring(mol, sorted(coord_atoms)):
        _set_eta_cap(ligand, sorted(coord_atoms))
        return ligand
    target = expected_denticity if expected_denticity is not None else coord_num
    if target and len(coord_atoms) > target:
        coord_atoms = _trim_to_top_n(coord_atoms, atom_probs, target)
    ligand.coord_atoms = sorted(coord_atoms)
    ligand.is_arene = False
    _set_denticity(ligand, mol)
    return ligand


def perceive_complex(complex: Complex) -> Complex:
    """Perceive every ligand of a complex in place; returns it."""
    for lig in complex.ligands:
        perceive(lig)
    return complex
