"""stk assembly.

Calls the custom topology graph for the chosen geometry/partition with ligand
building blocks and their donor atoms, and returns a constructed molecule. The
graphs own isomer generation incl. Delta/Lambda enantiomers; this
layer routes to them and places ligands on vertices — it does not re-derive
isomer chemistry.

Building blocks and the metal centre come from :mod:`mecobi.assembly._chem`;
routing from :mod:`mecobi.assembly.registry`. The MCHammer pre-optimisation
runs here as the stk construction optimizer; xtb relaxation
is the separate :mod:`mecobi.optimize` step.
"""

from __future__ import annotations

import stk

from ..isomers import IsomerSpec
from ..model import Complex, Geometry
from . import _chem, registry


# MCHammer's default target_bond_length (1.2 Å) is an organic-bond value that
# collapses metal-donor bonds — small monodentate ligands get crushed onto the
# metal (~1.5 Å) and later ejected by xtb. Use a metal-ligand-appropriate target
# so assembly starts clash-free at sane distances; xtb refines from there.
_MCHAMMER_TARGET_BOND_LENGTH = 2.1


class AssemblyError(RuntimeError):
    """Raised when a complex cannot be assembled (bad mapping, denticity, ...)."""


def is_tripodal(lig) -> bool:
    """True for a σ tridentate that can only bind FACIALLY (tacn, Tp, triphos, a
    bis(2-pyridyl)methyl-aryl): no donor lies on the shortest bond path between the other
    two, so all three hang off a common bridgehead/ring and none can span a trans pair.
    A linear tridentate (terpy, a pincer, dien) has its central donor on the path between
    the ends and stays meridional-capable. Forcing a tripod meridional wrenched it through
    its neighbours under xtb (DECLUU: pyridine N-N and C-C fusions)."""
    from rdkit import Chem

    if (lig.denticity != 3 or lig.is_arene
            or (lig.pi_sites and any(len(s) >= 2 for s in lig.pi_sites))):
        return False
    donors = list(lig.effective_donors or [])
    if len(donors) != 3:
        return False
    mol = Chem.MolFromSmiles(lig.smiles)
    if mol is None:
        return False
    for k in range(3):
        a, b = (donors[j] for j in range(3) if j != k)
        if donors[k] in Chem.GetShortestPath(mol, a, b):
            return False
    return True


def _meridionalize_assignment(
    complex: Complex, geometry: Geometry, assignment: dict[int, tuple[int, ...]]
) -> dict[int, tuple[int, ...]]:
    """Reorder each non-arene tridentate's site tuple for meridional binding.

    A linear tridentate (ONO Schiff base, terpy, a pincer) binds meridionally:
    its two END donors span a trans pair and its CENTRAL donor sits on the site
    cis to both. The site model assigns a meridional triple, but donor ``k`` binds
    site ``k`` in tuple order, so with the raw (sorted) tuple the central donor can
    land on an end site and the ligand folds. Reorder the tuple so the central
    backbone donor maps to the cis-to-both site. Facial triples (arene caps, a
    genuinely facial tridentate) have no trans pair and are left untouched.
    """
    from rdkit import Chem

    from . import sites as sites_mod

    adj = sites_mod._adjacency(geometry, sum(l.denticity for l in complex.ligands))
    out = dict(assignment)
    for lig_idx, site_ids in assignment.items():
        lig = complex.ligands[lig_idx]
        # Skip arene caps and centroid-cap ligands (a Cp+pyridine tridentate is not a
        # meridional σ-chelate; its caps have many anchor atoms, not one donor each).
        if (lig.is_arene or lig.denticity != 3 or len(site_ids) != 3
                or (lig.pi_sites and any(len(s) >= 3 for s in lig.pi_sites))):
            continue
        s = list(site_ids)
        centre_site = end_sites = None
        for i in range(3):
            others = [s[j] for j in range(3) if j != i]
            # centre = cis to both others, which are themselves trans (not cis)
            if all(o in adj[s[i]] for o in others) and others[1] not in adj[others[0]]:
                centre_site, end_sites = s[i], others
                break
        if centre_site is None:
            continue  # facial clique -> not meridional, leave as assigned
        donors = [a for grp in _assembly_donor_groups(lig) for a in grp]  # flat donor order
        mol = Chem.AddHs(Chem.MolFromSmiles(lig.smiles))
        if mol is None:
            continue
        chain = _chem._donor_chain_order(mol, list(donors))  # [end, centre, end]
        centre_k = list(donors).index(chain[len(chain) // 2])
        ordered: list[int | None] = [None, None, None]
        ordered[centre_k] = centre_site
        ends = [j for j in range(3) if j != centre_k]
        ordered[ends[0]], ordered[ends[1]] = end_sites
        out[lig_idx] = tuple(ordered)  # type: ignore[arg-type]
    return out


def default_isomer(complex: Complex, geometry: Geometry) -> IsomerSpec:
    """A single canonical isomer for a complex.

    Prefers a fixed topology class (vertex-based spec, ordered high-denticity
    first). When no fixed class exists but the geometry has a coordination-site
    model (CN 3/5/7/9 and the generic path), falls back to a site-based spec via
    :func:`mecobi.assembly.sites.default_assignment`. Raises KeyError only when
    neither is available (invariant 3, surfaced by the caller).

    A non-arene tridentate whose partition matches the facial piano-stool cap
    (e.g. octahedral (3,2,1)/(3,1,1,1)) is routed to the site model with a
    meridional assignment instead: an ONO/terpy/pincer ligand binds across the
    meridian, not folded onto the cap's facial triad (which stranded its donors).
    """
    from . import sites

    denticities = [l.denticity for l in complex.ligands]

    def _site_based() -> IsomerSpec:
        arene_ligands = {i for i, l in enumerate(complex.ligands) if l.is_arene}
        cap_counts = {i: sum(1 for s in l.pi_sites if len(s) >= 3)
                      for i, l in enumerate(complex.ligands)}
        cap = {i for i, n in cap_counts.items() if n}
        # Tripodal tridentates take a facial (mutually cis) triple, like an arene cap; if the
        # geometry has none (square planar), fall back to the ordinary connected placement.
        tripods = {i for i, l in enumerate(complex.ligands) if is_tripodal(l)}
        try:
            assignment = sites.default_assignment(
                geometry, denticities, arene_ligands=arene_ligands | tripods, cap_ligands=cap,
                cap_site_counts=cap_counts)
        except sites.SiteAssignmentError:
            if not tripods:
                raise
            assignment = sites.default_assignment(
                geometry, denticities, arene_ligands=arene_ligands, cap_ligands=cap,
                cap_site_counts=cap_counts)
        assignment = _meridionalize_assignment(complex, geometry, assignment)
        return IsomerSpec(geometry=geometry, label=None, assignment=assignment, site_based=True)

    # A centroid η-cap needs its perpendicular-ring vertex, which only the site model
    # provides (CentroidCap / CapMulti) — route cap complexes there, not the fixed
    # registry. The bent metallocene is a site-model geometry too (dynamic vectors).
    if any(l.pi_sites and any(len(s) >= 3 for s in l.pi_sites) for l in complex.ligands) \
            and (geometry in sites.SITE_VECTORS or geometry == Geometry.METALLOCENE_BENT):
        return _site_based()

    try:
        entry = registry.lookup(geometry, denticities)
    except KeyError:
        if geometry in sites.SITE_VECTORS:
            return _site_based()
        raise

    # Route two classes of non-arene tridentate to the meridional site model instead
    # of the fixed registry topology:
    #  - piano-stool (3,2,1)/(3,1,1,1): the fixed class caps one face with a facial
    #    triad — wrong for a meridional ONO/terpy/pincer; and
    #  - bis-tridentate ([3,3] etc.): the fixed octa_2tri overlaps two bulky planar
    #    tridentates (bis-terpy interpenetrates); the site model seats them on
    #    perpendicular meridional planes (PlanarTriDentate) and relaxes clean.
    has_nonarene_tridentate = any(
        l.denticity == 3 and not l.is_arene for l in complex.ligands
    )
    if (has_nonarene_tridentate and geometry in sites.SITE_VECTORS
            and (entry.topology_class.__module__.endswith("piano_stool")
                 or denticities.count(3) >= 2)):
        return _site_based()

    order = sorted(range(len(complex.ligands)), key=lambda i: denticities[i] or 0, reverse=True)
    assignment = {lig_idx: (vertex_id,) for vertex_id, lig_idx in enumerate(order)}
    return IsomerSpec(geometry=geometry, label=None, assignment=assignment)


def _assembly_donor_groups(lig) -> list:
    """Donor groups to expose as functional groups — one entry per coordination SITE.

    A σ-donor is a 1-atom group; an η²-alkene/alkyne π-site is a 2-atom group (both
    carbons bond one vertex at the midpoint); an η-arene binds through its whole ring
    but exposes three fac sites, so trim to a facial triad. ``len(groups) == denticity``.
    """
    donors = lig.effective_donors
    if not donors:
        raise AssemblyError(f"Ligand {lig.smiles!r} has no donor atoms (perceive first).")
    if lig.is_arene and len(donors) > 3:
        return [(c,) for c in _chem.facial_triad(lig.smiles, list(donors))]
    if lig.pi_sites:
        pi_atoms = {a for s in lig.pi_sites for a in s}
        groups: list = [tuple(s) for s in lig.pi_sites]
        groups += [(a,) for a in donors if a not in pi_atoms]
        return groups
    return [(c,) for c in donors]


def _stk_optimizer(mchammer: bool):
    """The topology optimiser: MCHammer (default -- relieves clashes, pulls donors to the target
    M-L length) or NullOptimizer (the raw vertex placement, for the MCHammer-collapse fallback)."""
    return (stk.MCHammer(target_bond_length=_MCHAMMER_TARGET_BOND_LENGTH)
            if mchammer else stk.NullOptimizer())


def build(complex: Complex, isomer: IsomerSpec, mchammer: bool = True) -> tuple[stk.ConstructedMolecule, str]:
    """Assemble one isomer with stk; return (constructed molecule, topology label).

    The label is the class name used in output filenames (e.g. ``octa_2bi2mono``).
    ``mchammer=False`` skips the MCHammer pre-optimisation (raw vertex placement).
    """
    denticities = [l.denticity for l in complex.ligands]
    try:
        entry = registry.lookup(isomer.geometry, denticities)
    except KeyError as exc:
        raise AssemblyError(
            f"No topology for geometry {isomer.geometry.value} with denticities "
            f"{registry.partition(denticities)}."
        ) from exc

    metal = _chem.metal_building_block(
        complex.metal.symbol, complex.metal.oxidation_state, entry.n_sites
    )

    ligands_map: dict[stk.BuildingBlock, tuple[int, ...]] = {}
    for lig_idx, vertex_ids in isomer.assignment.items():
        lig = complex.ligands[lig_idx]
        bb = _chem.ligand_building_block(lig.smiles, _assembly_donor_groups(lig))
        ligands_map[bb] = tuple(vertex_ids)

    topology = entry.topology_class(
        metals=metal, ligands=ligands_map, optimizer=_stk_optimizer(mchammer),
    )
    constructed = stk.ConstructedMolecule(topology_graph=topology)
    from . import sites
    try:
        site_pos = sites.site_positions(isomer.geometry, entry.n_sites)
    except Exception:  # noqa: BLE001 -- a geometry without numbered sites: leave the twist alone
        return constructed, entry.label
    return (_orient_eta2_ligands(constructed, complex.metal.symbol, isomer.geometry, site_pos),
            entry.label)


def _has_lone_eta2(complex: Complex) -> bool:
    """True if a ligand binds side-on through ONE 2-atom pi-site and nothing else (an eta2
    alkene/alkyne). Its twist about the metal-midpoint axis is set by the site it sits on
    (:func:`sites.eta2_axis`), so the site numbering of an explicit assignment carries
    information even when the isomer itself is unique -- the fixed-topology shortcut, which
    ignores the numbering, must not be taken."""
    return any(l.pi_sites and len(l.pi_sites) == 1 and len(l.pi_sites[0]) == 2
               and l.denticity == 1 for l in complex.ligands)


def _has_unsymmetric_chelate(complex: Complex) -> bool:
    """True if any multidentate ligand binds through INEQUIVALENT donor atoms (an unsymmetric
    chelate). Its cis/trans (or fac/mer) placement is then a distinct diastereomer: the site-map
    dynamic path honours the exact donor->site order the crystal specifies, but the fixed-topology
    shortcut can't tell the donors apart and may seat the wrong one at each site (ONENIG's
    unsymmetric dithiolene came out cis where the crystal is trans). Skip the shortcut for these.

    Symmetric chelates (equivalent donors -- ethylenediamine, a symmetric dithiolene) are
    unaffected: their donors are interchangeable so the shortcut's canonical isomer is correct."""
    from rdkit import Chem

    for lig in complex.ligands:
        donors = list(getattr(lig, "effective_donors", None) or ())
        if len(donors) < 2:
            continue
        m = Chem.MolFromSmiles(lig.smiles)
        if m is None:
            continue
        ranks = list(Chem.CanonicalRankAtoms(m, breakTies=False))
        if len({ranks[d] for d in donors if d < len(ranks)}) > 1:
            return True
    return False


def _unique_isomer(complex: Complex, geometry: Geometry) -> bool:
    """True when this geometry + ligand set admits a SINGLE diastereomer.

    Then the registry's canonical isomer is necessarily the crystal's, so routing a site_map
    build through the hand-tuned fixed topology is safe (it builds the same complex). Counted via
    the site-model enumerator (stereo off — Δ/Λ enantiomers don't change which sites the ligands
    occupy). Any failure (denticity >= 4, unperceived ligands, no site model) -> False, i.e. fall
    back to the dynamic path that honours the exact site_map."""
    from .. import isomers

    try:
        return len(isomers.enumerate_site_isomers(complex, geometry, stereo=False)) == 1
    except Exception:  # noqa: BLE001  (StereoNotSupported / perception / unsupported geometry)
        return False


def build_from_sites(
    complex: Complex, geometry: Geometry, site_assignment: dict[int, tuple[int, ...]],
    prefer_registry: bool = False, mchammer: bool = True,
) -> tuple[stk.ConstructedMolecule, str]:
    """Assemble one explicit isomer from a coordination-site assignment (§7.2).

    ``site_assignment`` maps ligand index -> ordered site ids (donor k binds
    site k). Builds a topology dynamically via :mod:`mecobi.assembly.sites`, so
    cis/trans and asymmetric-chelate orientation are exactly as specified —
    unlike the fixed topology classes.

    Routes to the hand-tuned fixed topology (the GUI/heuristic path — its ``BiDentateLigandVertex``
    orients a bulky chelate better than the dynamic ``ChelateVertex``) when doing so is SAFE, i.e.
    when the geometry + ligand set has a UNIQUE isomer: then the registry's canonical isomer *is*
    the crystal's, so the site_map path and the tool build the identical complex through the
    identical routine (resolves the DIBWAM class). ``_unique_isomer`` decides this automatically via
    the diastereomer count; ``prefer_registry=True`` forces the registry even for a multi-isomer
    partition (its canonical isomer may then differ from the crystal — for testing only).
    """
    from . import sites

    denticities = [l.denticity for l in complex.ligands]

    if (prefer_registry
            or (_unique_isomer(complex, geometry) and not _has_unsymmetric_chelate(complex)
                and not _has_lone_eta2(complex))) \
            and all(d is not None for d in denticities):
        try:
            registry.lookup(geometry, denticities)
        except KeyError:
            pass
        else:
            spec = default_isomer(complex, geometry)
            if not getattr(spec, "site_based", False):  # a real fixed topology, not a site fallback
                return build(complex, spec, mchammer=mchammer)
    planar = {i for i, l in enumerate(complex.ligands) if l.is_arene}
    cap = {i for i, l in enumerate(complex.ligands)
           if l.pi_sites and any(len(s) >= 3 for s in l.pi_sites)}
    topo_class = sites.topology_from_sites(
        geometry, denticities, site_assignment, planar_ligands=planar, cap_ligands=cap
    )
    metal = _chem.metal_building_block(
        complex.metal.symbol, complex.metal.oxidation_state, sum(denticities)
    )
    # Target coordination-site directions (unit vectors), so a σ-chelate's donors are
    # pre-organised toward the EXACT sites it will bind (cis/trans, fac/mer), not just
    # gathered near the metal — donor k of ligand `lig_idx` binds site `sites_of[k]`.
    import numpy as np

    site_pos = sites.site_positions(geometry, sum(denticities))
    ligands_map: dict[stk.BuildingBlock, tuple[int, ...]] = {}
    for proto_idx, lig_idx in enumerate(sorted(site_assignment)):
        lig = complex.ligands[lig_idx]
        dirs = [np.asarray(site_pos[s]) / (np.linalg.norm(site_pos[s]) or 1.0)
                for s in site_assignment[lig_idx]]
        bb = _chem.ligand_building_block(lig.smiles, _assembly_donor_groups(lig), site_dirs=dirs)
        ligands_map[bb] = (proto_idx,)
    topology = topo_class(
        metals=metal, ligands=ligands_map,
        optimizer=_stk_optimizer(mchammer),
    )
    constructed = stk.ConstructedMolecule(topology_graph=topology)
    return _orient_eta2_ligands(constructed, complex.metal.symbol, geometry, site_pos), "custom"


def _orient_eta2_ligands(constructed, metal_symbol: str, geometry: Geometry, site_pos):
    """Twist every MONODENTATE eta2 ligand (a side-on alkene/alkyne: exactly two metal-bonded
    atoms, bonded to each other, and no other donor) about its metal-midpoint axis so its C=C /
    C#C bond lies along the direction the site model prescribes (:func:`sites.eta2_axis`). A rigid
    rotation about that axis: the midpoint stays on its site and no bond changes. The ligand's
    site is read off the placement (the site vector nearest its midpoint). Never raises."""
    import numpy as np

    from .. import optimize
    from . import sites

    try:
        atoms = list(constructed.get_atoms())
        elems = [a.__class__.__name__ for a in atoms]
        if metal_symbol not in elems:
            return constructed
        mi = elems.index(metal_symbol)
        bonds = [(b.get_atom1().get_id(), b.get_atom2().get_id()) for b in constructed.get_bonds()]
        bonded = {(min(a, b), max(a, b)) for a, b in bonds}
        donors = sorted({b if a == mi else a for a, b in bonds if mi in (a, b)})
        comp = np.array(optimize._components_excluding(bonds, len(atoms), mi))
        P = np.array(constructed.get_position_matrix(), float)
        unit = [np.asarray(v, float) / (np.linalg.norm(v) or 1.0) for v in site_pos]
        moved = False
        for c in sorted(set(comp[comp >= 0].tolist())):
            ds = [d for d in donors if comp[d] == c]
            if len(ds) != 2 or (min(ds), max(ds)) not in bonded:
                continue                      # not a lone eta2 pi-site
            mid = (P[ds[0]] + P[ds[1]]) / 2.0 - P[mi]
            n_mid = float(np.linalg.norm(mid))
            if n_mid < 1e-6:
                continue
            axis = mid / n_mid
            site = int(np.argmax([float(u @ axis) for u in unit]))
            want = sites.eta2_axis(geometry, site, len(unit))
            if want is None:
                continue
            cc = P[ds[1]] - P[ds[0]]
            cc_p = cc - float(cc @ axis) * axis
            t_p = want - float(want @ axis) * axis
            if np.linalg.norm(cc_p) < 1e-6 or np.linalg.norm(t_p) < 1e-6:
                continue
            cc_p /= np.linalg.norm(cc_p)
            t_p /= np.linalg.norm(t_p)
            if float(cc_p @ t_p) < 0:         # the bond has no direction: take the short way
                t_p = -t_p
            theta = float(np.arctan2(float(np.cross(cc_p, t_p) @ axis), float(cc_p @ t_p)))
            if abs(theta) < 1e-3:
                continue
            K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
            R = np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * (K @ K)
            mem = np.where(comp == c)[0]
            P[mem] = (P[mem] - P[mi]) @ R.T + P[mi]
            moved = True
        return constructed.with_position_matrix(P) if moved else constructed
    except Exception:  # noqa: BLE001 -- an orientation nicety must never fail the build
        return constructed
