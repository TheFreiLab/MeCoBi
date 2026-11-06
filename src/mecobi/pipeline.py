"""End-to-end orchestration — the single code path (invariant 2).

Local runs and web runs both call into here; the web layer only wraps this in a
job queue, status tracking and storage. No chemistry lives above this module.

Full chain:
    SMILES -> perceive donors/denticity -> CN -> propose/confirm geometry ->
    resolve isomer(s) -> stk assemble -> MCHammer -> xtb -> write .xyz.

As of Stage 2 the chain runs through stk assembly + MCHammer (the construction
optimizer). xtb relaxation (Stage 3) is opt-in via ``relax=True`` until wired by
default; multi-isomer enumeration is a follow-up, so the default builds one
canonical isomer.
"""

from __future__ import annotations

import math
import shutil
import time
from pathlib import Path
from typing import Callable

from . import assembly, geometry, isomers, joint_embed, naming, optimize, spin
from ._text import noun
from ._text import plural as _plural
from .model import BuildResult, Complex, Geometry, Spin


def _report(progress: "Callable[[str], None] | None", message: str) -> None:
    """Emit a human-readable progress message if a callback was supplied."""
    if progress is not None:
        progress(message)


def resolve_perception(complex: Complex) -> Complex:
    """Fill donor atoms / denticity for every ligand, applying arene + trim rules."""
    from . import perception

    return perception.perceive_complex(complex)


def _metal_bonded_donors(constructed, metal_symbol: str) -> tuple[int, list[int]]:
    """(metal atom index, donor atom indices) from the assembled stk topology's
    metal bonds. Atom order matches the written .xyz and survives xtb, so these
    are the true donors to restrain during relaxation -- unlike a nearest-heavy
    guess, they don't mistake a bulky ligand's backbone atom for a donor."""
    atoms = list(constructed.get_atoms())
    elems = [a.__class__.__name__ for a in atoms]
    mi = elems.index(metal_symbol)
    metal_id = atoms[mi].get_id()
    donors: list[int] = []
    for bond in constructed.get_bonds():
        a1, a2 = bond.get_atom1().get_id(), bond.get_atom2().get_id()
        if a1 == metal_id:
            donors.append(a2)
        elif a2 == metal_id:
            donors.append(a1)
    return mi, sorted(donors)


def _eta_cap_ring_atoms(constructed, donor_indices: list[int]) -> list[int]:
    """All carbon atoms of the η-cap ring(s), given the metal-bonded facial-triad
    donors.

    An η5/η6 cap binds through its whole ring, but the topology only bonds three
    facial-triad carbons to the metal (:func:`assembly._assembly_donors`). For a
    symmetric relaxation restraint every ring carbon must be held to the metal, or
    the two un-pinned carbons let the ring slip/tilt off-axis. Rings are perceived
    from the assembled connectivity (no sanitisation, so the metal's odd valences
    don't matter); a carbocyclic 5- or 6-ring containing any triad carbon is a cap.
    Returns the union of such ring carbons (``.xyz``-aligned indices), or the
    original donors if ring perception finds nothing to expand.
    """
    from rdkit import Chem

    atoms = list(constructed.get_atoms())
    rw = Chem.RWMol()
    for a in atoms:
        rw.AddAtom(Chem.Atom(a.get_atomic_number()))
    for bond in constructed.get_bonds():
        rw.AddBond(bond.get_atom1().get_id(), bond.get_atom2().get_id(), Chem.BondType.SINGLE)
    mol = rw.GetMol()
    Chem.FastFindRings(mol)  # ring perception only; no valence/aromaticity checks
    donor_set = set(donor_indices)
    ring_atoms: set[int] = set()
    for ring in mol.GetRingInfo().AtomRings():
        if (len(ring) in (5, 6)
                and any(i in donor_set for i in ring)
                and all(atoms[i].get_atomic_number() == 6 for i in ring)):
            ring_atoms.update(ring)
    return sorted(ring_atoms) if len(ring_atoms) >= len(donor_indices) else sorted(donor_set)


def _terminal_oxo_donors(constructed, metal_index: int, donor_indices: list[int]) -> set[int]:
    """Donor indices that are a terminal oxo / nitrido: an O or N bonded ONLY to the
    metal (no other neighbour). Such a ligand forms a short M=O / M≡N multiple bond,
    far shorter than the covalent single-bond restraint target, so it must relax
    free of the coordination restraint. A halide (Cl⁻) is terminal too but not O/N;
    hydroxide/aqua O carry an H neighbour, so they are (correctly) not matched."""
    atoms = list(constructed.get_atoms())
    elems = [a.__class__.__name__ for a in atoms]
    nonmetal_neighbours = {i: 0 for i in donor_indices}
    for bond in constructed.get_bonds():
        a1, a2 = bond.get_atom1().get_id(), bond.get_atom2().get_id()
        for x, y in ((a1, a2), (a2, a1)):
            if x in nonmetal_neighbours and y != metal_index:
                nonmetal_neighbours[x] += 1
    return {i for i in donor_indices
            if elems[i] in ("O", "N") and nonmetal_neighbours[i] == 0}


def _topology_bonds(constructed) -> list[tuple[int, int]]:
    """All bonds of the assembled topology as (i, j) atom-index pairs.

    stk atom ids equal their position in the written .xyz, so these pairs index
    the relaxation geometry directly -- used to hold every covalent bond near its
    assembled length so xtb cannot pull a ligand apart."""
    return [
        (bond.get_atom1().get_id(), bond.get_atom2().get_id())
        for bond in constructed.get_bonds()
    ]


def _new_or_broken_bonds(intended_bonds, xyz_path, metal_index, tol: float = 1.2):
    """Heavy-atom connectivity change after relaxation, vs the assembled topology.

    Returns ``(new, broken)`` lists of ``(i, j, "El-El")``. ``new`` = a covalent
    heavy-heavy contact that formed during xtb but was NOT assembled -- a ligand-ligand
    fusion or a collapse (the failure the M-L bond restraint can't stop, since it only
    holds *existing* bonds). ``broken`` = an assembled heavy-heavy bond that stretched
    past bonding (fragmentation). The metal is excluded (its donor bonds are governed
    by the dissociation guard); H is excluded (crystallographic/relaxed H is noisy).
    A pair counts as bonded when ``d <= (rcov_i + rcov_j) * tol`` -- tol 1.2 cleanly
    separates a real new bond (~1.5 A for C-C) from a 1,3 contact (~2.4 A)."""
    atoms = optimize._read_xyz(Path(xyz_path))

    def _heavy(i):
        return i != metal_index and atoms[i][0] != "H"

    heavy = [i for i in range(len(atoms)) if _heavy(i)]
    intended = {frozenset((a, b)) for a, b in intended_bonds if _heavy(a) and _heavy(b)}
    perceived = set()
    for a in range(len(heavy)):
        for b in range(a + 1, len(heavy)):
            i, j = heavy[a], heavy[b]
            ri, rj = optimize._cov_radius(atoms[i][0]), optimize._cov_radius(atoms[j][0])
            if ri is None or rj is None:
                continue
            if math.dist(atoms[i][1], atoms[j][1]) <= (ri + rj) * tol:
                perceived.add(frozenset((i, j)))

    def _label(pair):
        i, j = sorted(pair)
        return (i, j, f"{atoms[i][0]}-{atoms[j][0]}")

    return ([_label(p) for p in perceived - intended],
            [_label(p) for p in intended - perceived])


def _nondonor_on_metal(xyz_path, metal_index, donor_indices, thresh: float = 1.4) -> bool:
    """True if a non-donor heavy atom collapsed onto the metal (closer than ``thresh``).

    The bond-connectivity guard (:func:`_new_or_broken_bonds`) excludes the metal, so a ligand
    atom that xtb pulls INTO the metal (a phenyl folding onto Pd -- DIBWAM: a C at 0.76 Å) slips
    through it. This catches that: any non-metal, non-H atom that is not a coordinating donor and
    sits nearer than ``thresh`` (well inside a real ~2.0 Å M-L bond) is a collapse onto the centre.
    Donors are excluded — they and any η-cap ring carbons legitimately sit in the sphere."""
    if metal_index is None:
        return False
    atoms = optimize._read_xyz(Path(xyz_path))
    if metal_index >= len(atoms):
        return False
    mp = atoms[metal_index][1]
    donors = set(donor_indices or [])
    for i, (el, p) in enumerate(atoms):
        if i == metal_index or el == "H" or i in donors:
            continue
        if math.dist(mp, p) < thresh:
            return True
    return False


def _unbound_donors(xyz_path, metal_index, donor_indices, metal_symbol, oxidation_state,
                    coordination_number) -> "list[tuple[int, str, float, float]]":
    """Donors sitting beyond ``_CO_LIGAND_DRIFT`` x their M-L reference: ``(index, element,
    distance, reference)``. A donor that far out is not bonded, however the structure got there.

    The xtb dissociation guard only fires past max(3.1 A, 1.4 x reference) and lets a donor the
    assembly had already stranded through, so a complex can leave relax with several donors off
    and nothing flagged: LAYFID (Y) kept its diamide/amidinate N and THF O at 2.9-3.3 A
    (Y-N CSD 2.42 A) while backbone carbons took the sphere."""
    if metal_index is None:
        return []
    atoms = optimize._read_xyz(Path(xyz_path))
    if metal_index >= len(atoms):
        return []
    mp = atoms[metal_index][1]
    out = []
    for d in donor_indices or []:
        if d == metal_index or d >= len(atoms):
            continue
        r = math.dist(atoms[d][1], mp)
        ref = optimize._restraint_reference(
            r, metal_symbol, optimize._donor_key(atoms, d, metal_index, donor_indices),
            ox=oxidation_state, cn=coordination_number)
        if r > _CO_LIGAND_DRIFT * ref:
            out.append((d, atoms[d][0], r, ref))
    return out


def _mch_env(name: str, default: float) -> float:
    import os
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return float(default)


def _angular_rms_deviation(donor_dirs, site_vecs) -> float:
    """RMS angle (deg) between donor directions and ideal site vectors, minimised over rotations
    and donor-to-site matchings, so it measures polyhedron SHAPE only.

    The ideal vectors live in the site model's fixed frame, but a fixed registry topology builds in
    its own frame (``square_2bi`` puts donors on the diagonals, 45 deg off the site axes). Scoring in
    the fixed frame then charges both the raw and the MCHammer placement a large bogus deviation
    (one donor ~130 deg "off"), and the fallback compared noise: it discarded a correct MCHammer
    Au(ppy)(dithiolate) for the raw placement with every M-L at 2.9 A. Each rotation candidate maps
    an ordered site pair onto donor 0 and the first donor not collinear with it, takes the optimal
    assignment, then refines the rotation once by Kabsch on that assignment and re-scores."""
    import itertools

    import numpy as np
    from scipy.optimize import linear_sum_assignment

    def frame(a, b):
        a = a / (np.linalg.norm(a) or 1.0)
        b = b - (b @ a) * a
        nb = np.linalg.norm(b)
        if nb < 1e-6:
            return None
        b = b / nb
        return np.stack([a, b, np.cross(a, b)])

    def unit(X):
        n = np.linalg.norm(X, axis=1)
        return X / np.where(n > 0, n, 1.0)[:, None]

    def score(rot):
        cost = np.degrees(np.arccos(np.clip(D @ rot.T, -1.0, 1.0))) ** 2
        r, c = linear_sum_assignment(cost)
        return float(cost[r, c].mean()) ** 0.5, r, c

    D, S = unit(np.asarray(donor_dirs, float)), unit(np.asarray(site_vecs, float))
    b = next((k for k in range(1, len(D)) if abs(float(D[0] @ D[k])) < 0.95), None)
    fd = frame(D[0], D[b]) if b is not None else None
    best = score(S)[0]
    if fd is None:                        # all donors collinear (CN2): align one axis only
        for i in range(len(S)):
            v, c = np.cross(S[i], D[0]), float(S[i] @ D[0])
            if np.linalg.norm(v) < 1e-9:
                rot = np.eye(3) if c > 0 else -np.eye(3)
            else:                          # Rodrigues: the rotation taking S[i] onto D[0]
                k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
                rot = np.eye(3) + k + k @ k / (1.0 + c)
            best = min(best, score(S @ rot.T)[0])
        return best
    for i, j in itertools.permutations(range(len(S)), 2):
        fs = frame(S[i], S[j])
        if fs is None:
            continue
        rms, r, c = score(S @ (fd.T @ fs).T)  # site frame -> donor frame
        u, _, vt = np.linalg.svd(S[c].T @ D[r])  # Kabsch: best rotation for this matching
        rot = (u @ np.diag([1.0, 1.0, np.sign(np.linalg.det(u @ vt))]) @ vt).T
        best = min(best, rms, score(S @ rot.T)[0])
    return best


def _stranded_donors(constructed, metal_symbol: str, metal_ox=None) -> int:
    """Sigma donors the assembly left beyond ``_CO_LIGAND_DRIFT`` x their M-L reference: the same
    "not bonded" rule :func:`_unbound_donors` applies after relaxation, here on the assembled
    structure. The fixed ``_ML_MAX`` (3.3 A) of :func:`_geom_badness` is blind to them: MCHammer
    pushed the iminopyridine N of [Cp*Ir(N^N)Cl]+ to 2.6-3.3 A (Ir-N CSD 2.06 A) while the raw stk
    placement had both at 2.0 A, and the stranded N stayed off the metal through xtb.

    Hapto carbons (Cp / arene / alkene) are skipped: the raw placement seats a cap ring by its
    facial triad and xtb moves the ring onto the metal, so their pre-relax distance says nothing.
    The reference is the CSD-mined M-L average, else the covalent-radius sum."""
    mi, donors = _metal_bonded_donors(constructed, metal_symbol)
    if mi is None or not donors:
        return 0
    atoms = [(a.__class__.__name__, tuple(map(float, p)))
             for a, p in zip(constructed.get_atoms(), constructed.get_position_matrix())]
    cn = len(donors)
    n = 0
    for d in donors:
        key = optimize._donor_key(atoms, d, mi, donors)
        if key == optimize.ETA_CARBON:
            continue
        ref = optimize._ml_target(metal_symbol, metal_ox, key, cn)
        if ref is None:
            r_m = optimize._cov_radius(metal_symbol)
            r_d = optimize._cov_radius("C" if key == optimize.SP_CARBON else key)
            if r_m is None or r_d is None:
                continue
            ref = r_m + r_d
        if math.dist(atoms[d][1], atoms[mi][1]) > _CO_LIGAND_DRIFT * ref:
            n += 1
    return n


_STRANDED_DONOR_PENALTY = 5.0   # per stranded sigma donor; well above _MCH_BADNESS_TOL


def _geom_badness(constructed, metal_symbol: str, geom, metal_ox=None) -> float:
    """A geometry-quality penalty for an assembled structure (0 = clean; higher = worse), used to
    decide whether MCHammer collapsed the raw stk placement. Sums five unambiguous defects, each
    tunable via env:
      * a non-donor heavy atom collapsed onto the metal / into the M-donor region (``_METAL_CLASH``);
      * two heavy atoms of DIFFERENT ligands fused (``_FUSE``);
      * a donor at a physically impossible M-L distance (outside ``_ML_MIN``..``_ML_MAX``);
      * a sigma donor stranded beyond ``_CO_LIGAND_DRIFT`` x its M-L reference
        (:func:`_stranded_donors`; ``MECOBI_MCH_STRANDED``, 0 switches it off);
      * the RMS angular deviation of the donor directions from the coordination geometry's ideal
        site vectors (over ``_ANGLE`` degrees), after the best rotation + donor-to-site matching
        (:func:`_angular_rms_deviation`; a scale- and frame-free polyhedron check)."""
    import numpy as np

    from .assembly import sites
    mi, donors = _metal_bonded_donors(constructed, metal_symbol)
    if mi is None:
        return 0.0
    P = np.asarray(constructed.get_position_matrix(), float)
    m = P[mi]
    atoms = list(constructed.get_atoms())
    zn = [a.get_atomic_number() for a in atoms]
    bonds = [(b.get_atom1().get_id(), b.get_atom2().get_id()) for b in constructed.get_bonds()]
    comp = optimize._components_excluding(bonds, len(P), mi)
    dset = set(donors)
    clash = _mch_env("MECOBI_MCH_METAL_CLASH", 1.7)
    fuse = _mch_env("MECOBI_MCH_FUSE", 1.35)
    ml_min, ml_max = _mch_env("MECOBI_MCH_ML_MIN", 1.3), _mch_env("MECOBI_MCH_ML_MAX", 3.3)
    pen = 0.0
    for i in range(len(P)):                       # non-donor heavy atom on/near the metal
        if i == mi or i in dset or zn[i] == 1:
            continue
        if float(np.linalg.norm(P[i] - m)) < clash:
            pen += 10.0
    for d in donors:                              # donor at a wrong M-L distance
        r = float(np.linalg.norm(P[d] - m))
        if r > ml_max:
            pen += (r - ml_max) * 2.0
        elif r < ml_min:
            pen += (ml_min - r) * 4.0
    pen += _mch_env("MECOBI_MCH_STRANDED", _STRANDED_DONOR_PENALTY) * _stranded_donors(
        constructed, metal_symbol, metal_ox)
    for i in range(len(P)):                        # inter-ligand fusion
        if zn[i] == 1 or comp[i] < 0:
            continue
        for j in range(i + 1, len(P)):
            if zn[j] == 1 or comp[j] < 0 or comp[j] == comp[i]:
                continue
            if float(np.linalg.norm(P[i] - P[j])) < fuse:
                pen += 8.0
    # Donor-donor collapse: two donors of DIFFERENT ligands squeezed together (MCHammer pulling
    # small monodentate halides into a fused clump -- NISYAS's 3 iodides at 60 deg / 2.1 A, YIVLEX's
    # 2 iodides at 37 deg / 1.45 A). The generic inter-ligand `fuse` term (fixed 1.35 A) misses it
    # because big donors like I fuse well above 1.35 A, and the angular term stays under threshold.
    # Size/geometry-free criterion: for two different-ligand donors at radii r_i, r_j, their cis
    # separation is 2*r*sin(theta/2); flagging sep < dfuse*(r_i+r_j) ~ flags theta below ~67 deg,
    # well inside a real cis (>=72 deg even for a pentagonal-bipyramid equator), a clear collapse.
    dfuse = _mch_env("MECOBI_MCH_DONOR_FUSE", 0.55)
    for a in range(len(donors)):
        for b in range(a + 1, len(donors)):
            di, dj = donors[a], donors[b]
            if comp[di] == comp[dj]:               # same ligand (a chelate bite) -> legitimate
                continue
            ri, rj = float(np.linalg.norm(P[di] - m)), float(np.linalg.norm(P[dj] - m))
            if ri > 1e-6 and rj > 1e-6 and float(np.linalg.norm(P[di] - P[dj])) < dfuse * (ri + rj):
                pen += 8.0
    try:                                           # angular deviation from the ideal polyhedron
        sv = sites.site_positions(geom, len(donors))
        if sv and len(sv) == len(donors) and len(donors) >= 2:
            dv = [(P[d] - m) / (np.linalg.norm(P[d] - m) or 1.0) for d in donors]
            rms = _angular_rms_deviation(dv, sv)
            ang = _mch_env("MECOBI_MCH_ANGLE", 40.0)
            if rms > ang:
                pen += (rms - ang) * 0.1
    except Exception:  # noqa: BLE001  (no site model for this geometry -> skip the angular term)
        pass
    return pen


_MCH_BADNESS_TOL = 1.0  # geometry penalty below which MCHammer is fine; above -> try the raw placement

# User-facing build notes for the MCHammer fallback, in the words the web UI uses for the
# option ("Force-field pre-placement"); they used to read like a debug log and named xtb
# even when relaxation was off (UI audit W8). Tests key on MCH_WORSE_MSG.
MCH_WORSE_MSG = ("Force-field pre-placement made the geometry worse, so the ideal placement "
                 "was used instead")
MCH_OFF_MSG = "Force-field pre-placement is off, so the ideal placement was used."


def _mch_worse(bad_mch: float, bad_raw: float) -> str:
    return f"{MCH_WORSE_MSG} (geometry penalty {bad_mch:.1f} vs {bad_raw:.1f})."


def _build_with_fallback(make, metal_symbol, geom, mchammer_fallback, mchammer=True, metal_ox=None):
    """Assemble via ``make(mchammer=True)`` (MCHammer); if MCHammer collapsed the sphere, re-build
    ``make(mchammer=False)`` (the raw stk vertex placement) and keep whichever is cleaner. So an
    already-good MCHammer result is untouched, and a case MCHammer *worsens* (a collapsed geometry,
    a wrong M-L distance, a big angular deviation -- see :func:`_geom_badness`) is handed to xtb as
    the raw placement instead of the collapsed one. Returns (constructed, label, note-or-None).

    ``mchammer=False`` turns MCHammer OFF entirely: skip it and hand xtb the raw stk placement
    (donors on the ideal site vectors) directly, never running the optimiser at all."""
    if not mchammer:
        constructed, label = make(False)
        return constructed, label, MCH_OFF_MSG
    constructed, label = make(True)
    if not mchammer_fallback:
        return constructed, label, None
    bad = _geom_badness(constructed, metal_symbol, geom, metal_ox)
    import os
    if os.environ.get("MECOBI_DECLASH", "1") != "0":
        return _pick_with_chelate_repair(make, constructed, label, bad, metal_symbol, geom, metal_ox)
    if bad <= _mch_env("MECOBI_MCH_BADNESS_TOL", _MCH_BADNESS_TOL):
        return constructed, label, None
    raw, _ = make(False)
    bad_raw = _geom_badness(raw, metal_symbol, geom, metal_ox)
    if bad_raw < bad - 1e-6 and not _raw_intrudes_more(raw, constructed, metal_symbol):
        return raw, label, _mch_worse(bad, bad_raw)
    return constructed, label, None


def _assemble(make, complex, geom, mchammer_fallback, mchammer, reembed_crowded=True):
    """:func:`_build_with_fallback`, then (``reembed_crowded``) the joint re-embedding of a
    collapsed sphere of monodentates/chelates (:mod:`joint_embed`: bulky ligands seated one by
    one thread through each other -- Pt(PPh3)4, Pt(BINAP)2). Returns (constructed, label,
    note-or-None)."""
    constructed, label, note = _build_with_fallback(
        make, complex.metal.symbol, geom, mchammer_fallback, mchammer=mchammer,
        metal_ox=complex.metal.oxidation_state)
    if not reembed_crowded:
        return constructed, label, note
    constructed, jnote = joint_embed.joint_embed(
        make, constructed, complex.metal.symbol, metal_ox=complex.metal.oxidation_state,
        cn=complex.coordination_number)
    if jnote:
        note = f"{note} {jnote}" if note else jnote
    return constructed, label, note


_NEAR_METAL_A = 2.2   # a non-donor heavy atom this close to the metal: an assembly defect


def _pick_with_chelate_repair(make, mch, label, bad_mch, metal_symbol, geom, metal_ox=None):
    """Default fallback (``MECOBI_DECLASH=0`` switches it off): MCHammer vs raw vs raw + chelate repair.

    Runs when MCHammer fails the quality check OR leaves a 5-membered chelate ring inside-out
    (:func:`chelate_fix.n_inside_out`). Candidates are ranked by fused/collapsed atoms
    (:func:`_hard_overlaps`), then inside-out rings, then the geometry penalty, so a repair is
    only taken when it is cleaner. The repair (:func:`chelate_fix.repair_chelates`) flattens and
    exo-corrects gated 5-ring chelates and de-clashes substituent torsions; no donor moves.

    A raw placement with a non-donor heavy atom inside ``_NEAR_METAL_A`` of the metal is broken
    too, and is repaired before it can replace a rejected MCHammer assembly: once the stranded-donor
    term rejected MCHammer for [Cp*Ir(N^N)Cl]+, the raw placement it fell back to sometimes had the
    iminopyridine folded onto the metal (imine C 1.8-1.9 A from Ir, both N at 2.0 A). That is
    above the 1.7 A of :func:`_hard_overlaps`, so the repair never ran, and xtb fused the Cp* into
    the Schiff base or dissociated a donor; the repair rotates the ring out (nearest atom 2.6 A)."""
    from . import chelate_fix

    io_mch = chelate_fix.n_inside_out(mch, metal_symbol)
    if bad_mch <= _mch_env("MECOBI_MCH_BADNESS_TOL", _MCH_BADNESS_TOL) and not io_mch:
        return mch, label, None
    raw, _ = make(False)
    cands = [("MCHammer", mch, bad_mch),
             ("raw", raw, _geom_badness(raw, metal_symbol, geom, metal_ox))]

    def broken(c):
        # an atom on the metal or an inside-out 5-ring: what the repair exists for. A crowded
        # periphery alone is not: xtb relaxed VIWCEL's raw placement (4 fused pairs) cleanly but
        # failed on the "clean" repaired one, and QAQRAB likewise.
        return (_hard_overlaps(c, metal_symbol)[1] > 0
                or chelate_fix.n_inside_out(c, metal_symbol) > 0 or near(c))

    def near(c):
        return _closest_intrusion(c, metal_symbol) < _mch_env("MECOBI_NEAR_METAL", _NEAR_METAL_A)

    tol = _mch_env("MECOBI_MCH_BADNESS_TOL", _MCH_BADNESS_TOL)
    if all(broken(c[1]) for c in cands) or (bad_mch > tol and near(raw)):
        repaired, rep = chelate_fix.repair_chelates(raw, metal_symbol, metal_ox=metal_ox)
    else:
        rep = {"changed": False}
    if rep.get("changed") and _hard_overlaps(repaired, metal_symbol)[1] > 0:
        # The repair must clear the first shell completely. It only moves 5-ring chelates, so an
        # atom it cannot reach stays on the metal: QEMTOR's TMS-amido tripod put an Si 0.68 A
        # from Ti in the raw placement it starts from (0.99 A in MCHammer's, which xtb untangles).
        rep = {"changed": False}
    if not (rep.get("changed") and (rep.get("rings_fixed") or rep.get("exo_fixed"))):
        # No repair in play: exactly the default fallback (raw only if its penalty is lower).
        bad_raw = cands[1][2]
        if (bad_mch > tol and bad_raw < bad_mch - 1e-6 and not near(raw)
                and not _raw_intrudes_more(raw, mch, metal_symbol)):
            return raw, label, _mch_worse(bad_mch, bad_raw)
        return mch, label, None
    # Only a repair that actually fixed a 5-membered chelate (ring or endo substituent) competes: a torsion-only
    # outer-sphere de-clash with no ring to fix sent VIBQON (Rh, Cl/CO/2 monodentate P) to
    # Rh-Cl 1.74 A under xtb.
    if rep.get("changed") and (rep.get("rings_fixed") or rep.get("exo_fixed")):
        cands.append(("repaired", repaired, _geom_badness(repaired, metal_symbol, geom, metal_ox)))

    def key(c):
        return (sum(_hard_overlaps(c[1], metal_symbol)),
                chelate_fix.n_inside_out(c[1], metal_symbol), near(c[1]), c[2])

    name, chosen, bad = min(cands, key=key)
    if name == "raw" and _raw_intrudes_more(raw, mch, metal_symbol):
        name = "MCHammer"
    if name == "MCHammer":
        return mch, label, None
    if name == "raw":
        return raw, label, _mch_worse(bad_mch, bad)
    return repaired, label, (
        f"Force-field pre-placement left {_plural(io_mch, 'chelate ring')} inside out "
        f"(geometry penalty {bad_mch:.1f}), so the ideal placement was used and repaired: "
        f"{_plural(rep['rings_fixed'], '5-membered chelate ring')} flattened, "
        f"{_plural(rep['exo_fixed'], 'donor substituent')} turned outward and "
        f"{_plural(rep['torsions'], 'substituent torsion')} adjusted (penalty {bad:.1f}).")


def _closest_intrusion(constructed, metal_symbol) -> float:
    """Distance (A) from the metal to the nearest non-donor heavy atom (inf if none)."""
    import numpy as np

    mi, donors = _metal_bonded_donors(constructed, metal_symbol)
    if mi is None:
        return float("inf")
    P = np.asarray(constructed.get_position_matrix(), float)
    dset = set(donors)
    d = [float(np.linalg.norm(P[i] - P[mi])) for i, a in enumerate(constructed.get_atoms())
         if a.get_atomic_number() != 1 and i != mi and i not in dset]
    return min(d, default=float("inf"))


def _raw_intrudes_more(raw, mch, metal_symbol) -> bool:
    """True when the raw stk placement puts a non-donor atom on the metal (< 1.7 A) closer than
    MCHammer's assembly does. A lower geometry penalty then does not make raw the better start:
    on the Linux VM QEMTOR's raw placement (penalty 20.2 vs 24.2) had the tripod's SiMe3 arm on Ti
    and xtb collapsed, while from MCHammer's (Si 0.99 A) xtb recovers. The penalty scores donor
    angles and distances only, so it cannot see the intrusion."""
    r = _closest_intrusion(raw, metal_symbol)
    return r < 1.7 and r < _closest_intrusion(mch, metal_symbol)


def _hard_overlaps(constructed, metal_symbol) -> "tuple[int, int]":
    """Unrecoverable contacts as ``(fused, on_metal)``: heavy-atom pairs of different ligands
    closer than 1.35 A, and non-donor heavy atoms closer than 1.7 A to the metal."""
    import numpy as np

    mi, donors = _metal_bonded_donors(constructed, metal_symbol)
    if mi is None:
        return 0, 0
    P = np.asarray(constructed.get_position_matrix(), float)
    Z = np.array([a.get_atomic_number() for a in constructed.get_atoms()])
    bonds = [(b.get_atom1().get_id(), b.get_atom2().get_id()) for b in constructed.get_bonds()]
    comp = np.array(optimize._components_excluding(bonds, len(P), mi))
    heavy = np.where((Z != 1) & (comp >= 0))[0]
    H = P[heavy]
    dd = np.linalg.norm(H[:, None, :] - H[None, :, :], axis=-1)
    other = np.triu(comp[heavy][:, None] != comp[heavy][None, :], 1)
    dset = set(donors)
    near_metal = sum(1 for i in heavy if i not in dset and np.linalg.norm(P[i] - P[mi]) < 1.7)
    return int((dd[other] < 1.35).sum()), int(near_metal)


def _proper_rotation_rmsd(a, b) -> float:
    """Atom-order-preserving Kabsch RMSD using proper rotations only."""
    import numpy as np

    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape or a.ndim != 2 or a.shape[1] != 3:
        return math.inf
    ac = a - a.mean(axis=0)
    bc = b - b.mean(axis=0)
    u, _s, vt = np.linalg.svd(ac.T @ bc)
    det = float(np.linalg.det(vt.T @ u.T))
    rotation = vt.T @ np.diag([1.0, 1.0, 1.0 if det >= 0 else -1.0]) @ u.T
    return float(np.sqrt(np.mean(np.sum((bc - ac @ rotation.T) ** 2, axis=1))))


def _restore_collapsed_enantiomers(builds: list[tuple], tol: float = 1e-4) -> list[tuple]:
    """Reflect a Delta assembly when its Lambda partner collapsed onto the same hand.

    The octahedral site enumerator distinguishes the two hands correctly, but stk's
    placement of three *identical symmetric* chelates can canonicalise both site maps
    to the same Cartesian structure.  Heteroleptic cases such as TLD1433 do not do
    this. Detect the failure on the assembled coordinates and repair only the
    duplicate Lambda member by reflecting its matching Delta structure.  Reflection
    preserves all distances and the topology while guaranteeing the opposite hand;
    the normal xTB path can then refine that geometry.
    """
    import numpy as np

    deltas = [
        constructed
        for constructed, _topology, iso_label, _note in builds
        if iso_label and iso_label.startswith("Delta")
    ]
    if not deltas:
        return builds

    repaired = []
    for constructed, topology, iso_label, note in builds:
        if not (iso_label and iso_label.startswith("Lambda")):
            repaired.append((constructed, topology, iso_label, note))
            continue
        coords = constructed.get_position_matrix()
        duplicate = next(
            (delta for delta in deltas
             if _proper_rotation_rmsd(delta.get_position_matrix(), coords) < tol),
            None,
        )
        if duplicate is None:
            repaired.append((constructed, topology, iso_label, note))
            continue
        mirrored = np.asarray(duplicate.get_position_matrix(), dtype=float).copy()
        centre = mirrored.mean(axis=0)
        mirrored[:, 0] = 2.0 * centre[0] - mirrored[:, 0]
        constructed = constructed.with_position_matrix(mirrored)
        repair_note = (
            "site placement collapsed this Lambda assembly onto its Delta partner; "
            "reflected the duplicate assembled geometry to preserve the opposite hand."
        )
        note = f"{note} {repair_note}" if note else repair_note
        repaired.append((constructed, topology, iso_label, note))
    return repaired


def _linear_donor_angles(xyz_path, bond_pairs, metal_index, donor_indices):
    """Linearity restraints for end-on linear donors, as ``(metal, donor, partner, 180.0)``.

    A cyanide/carbonyl/isocyanide/nitrosyl/nitrile-type donor binds end-on through a MULTIPLE
    bond and must stay collinear with it (M–C≡N ~180°); so does an end-on η1-dihalogen (M–I–I). Match strictly: a C or N donor whose
    only heavy neighbour besides the metal (i) is C, N or O and (ii) sits within 1.3 Å — a
    triple/double bond (C≡N ~1.16, C≡O ~1.13, N=O ~1.2 Å), not a single bond (~1.4-1.5 Å). The
    distance gate is what keeps a single-bonded terminal (a −CH₂⁻, an −OR arm) from being forced
    linear — over-matching there bent/fused ligands. Left free, a true end-on donor bends inward
    and clashes (ZIVCUF). Graph + geometry only; the angle (vertex = the donor) goes to
    ``$constrain``. Ring/chelate donors have ≥2 heavy neighbours and never match."""
    if not bond_pairs or metal_index is None:
        return []
    atoms = optimize._read_xyz(Path(xyz_path))
    adj: dict[int, set] = {}
    for a, b in bond_pairs:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    out = []
    halogens = ("F", "Cl", "Br", "I")
    for d in donor_indices or []:
        if d == metal_index or d >= len(atoms) or atoms[d][0] not in ("C", "N") + halogens:
            continue
        heavy = [n for n in adj.get(d, ()) if n != metal_index and atoms[n][0] != "H"]
        if len(heavy) != 1:
            continue
        p = heavy[0]
        if atoms[d][0] in halogens:
            # End-on η1-dihalogen (M-I-I, PIDRIE): a σ-donor X-X binds collinear, M-X-X ~180 deg.
            # Left free, GFN2 folds the distal halogen over onto the metal.
            if atoms[p][0] in halogens and len(adj.get(p, ())) == 1:
                out.append((metal_index, d, p, 180.0))
            continue
        if atoms[p][0] not in ("C", "N", "O"):
            continue
        if math.dist(atoms[d][1], atoms[p][1]) > 1.3:  # single bond -> not an end-on multiple bond
            continue
        out.append((metal_index, d, p, 180.0))
    return out


def _haptic_aryl_pins(xyz_path, bond_pairs, metal_index, donor_indices):
    """Stop a σ aryl-carbon donor slipping to η-arene during xtb, as (metal, ortho, distance) pins.

    An aryl carbanion is an excellent arene, so GFN2 rocks the whole ring onto the metal — UMIZOG's
    mesityl (a σ C-donor at assembly) relaxes to η⁶, the ring's six carbons all ~2.1 Å from the Cr.
    Pin the metal-to-ORTHO-carbon distances at their assembled (σ) values: with the M–Cipso bond
    restraint already holding the ipso carbon, these fixed M–C distances lock the ring plane's tilt
    so it cannot rock into η. Fires only for a σ CARBON donor whose two neighbours are BOTH carbons
    that are themselves in the ring (an aromatic/conjugated ipso) — an alkyl (0 C neighbours), a
    carbene (N/O neighbours), or a π-site carbon (η already, ≥2-atom donor group) never matches.
    Graph + geometry only; harmonic distance goes to the same ``$constrain`` block as the M–L bonds.
    """
    if not bond_pairs or metal_index is None:
        return []
    atoms = optimize._read_xyz(Path(xyz_path))
    dset = set(donor_indices or [])
    adj: dict[int, set] = {}
    for a, b in bond_pairs:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    out = []
    for d in donor_indices or []:
        if d == metal_index or d >= len(atoms) or atoms[d][0] != "C":
            continue
        ortho = [n for n in adj.get(d, ()) if n != metal_index and atoms[n][0] == "C"]
        # An eta-cap (Cp / arene) has MANY ring carbons in the donor set, each bonded to another
        # donor carbon -- that is a legitimate pi-donor, NOT a sigma-aryl to hold down, so skip any
        # donor whose ring neighbour is itself a donor. A sigma aryl-carbon (one ring carbon in the
        # donor set) never has a donor neighbour.
        if any(n in dset for n in ortho):
            continue
        # aromatic/conjugated ipso: two carbon neighbours, each with a further carbon neighbour in
        # the ring (so a vinyl/allyl terminus or an isolated sp3 chain-carbon does not match).
        if len(ortho) < 2 or not all(
                any(k not in (d, n) and atoms[k][0] == "C" for k in adj.get(n, ())) for n in ortho):
            continue
        for n in ortho:
            out.append((metal_index, n, math.dist(atoms[metal_index][1], atoms[n][1])))
    return out


_CO_LIGAND_DRIFT = 1.3     # donor counts as drifted off beyond this x its M-L reference
_DONOR_SQUEEZE = 0.85      # ... or as crushed below this x (a genuine short M=O is exempt: see
                           # optimize._restraint_reference, which then returns the distance itself)
_CO_LIGAND_INTRUDE = 1.15  # a non-donor heavy atom this close (x rcov sum) has taken a site


def _cyclometalated_split(bond_pairs, n_atoms, metal_index, donor_indices, sigma_aryl):
    """``(cyclometalated ligand atoms, co-ligand donors)`` for an unrestrained σ-aryl relax.

    The cyclometalated ligand(s) are the metal-excluded connected components holding a σ aryl
    donor; every other donor belongs to a co-ligand that the σ-aryl policy freed only as a
    side effect."""
    comp = optimize._components_excluding(bond_pairs, n_atoms, metal_index)
    cyclo = {comp[d] for d in sigma_aryl}
    cyclo_atoms = {i for i in range(n_atoms) if comp[i] in cyclo}
    return cyclo_atoms, [d for d in donor_indices if comp[d] not in cyclo]


def _co_ligand_drift(xyz_path, metal_index, co_donors, cyclo_atoms, donor_indices,
                     metal_symbol, oxidation_state, coordination_number):
    """How an unrestrained σ-aryl relax damaged the CO-ligands: ``(drifted, intruders)``.

    ``drifted`` = donors now beyond ``_CO_LIGAND_DRIFT`` x their M-L reference (a floppy arm that
    wandered off: Ru(tpa)(ppy)'s CH2-pyridine at 5.3 A) or crushed below ``_DONOR_SQUEEZE`` x it
    (an over-constrained pincer aryl: MOHWOX's Ir-C at 1.77 A vs 2.18). ``intruders`` =
    co-ligand non-donor heavy atoms within ``_CO_LIGAND_INTRUDE`` x the covalent sum of the metal
    (the atom that moved into the vacated site: a tpa carbon at 2.06 A). Atoms of the
    cyclometalated ligand are ignored -- its own sphere is what the free relax is for."""
    atoms = optimize._read_xyz(Path(xyz_path))
    mp = atoms[metal_index][1]
    r_m = optimize._cov_radius(atoms[metal_index][0]) or 1.4
    drifted = []
    for d in co_donors:
        r = math.dist(atoms[d][1], mp)
        ref = optimize._restraint_reference(
            r, metal_symbol, optimize._donor_key(atoms, d, metal_index, co_donors),
            ox=oxidation_state, cn=coordination_number,
            multiple_bond_ok=optimize._can_multiple_bond(atoms, d, metal_index))
        if r > _CO_LIGAND_DRIFT * ref or r < _DONOR_SQUEEZE * ref:
            drifted.append(d)
    dset = set(donor_indices)
    intruders = [
        i for i, (el, p) in enumerate(atoms)
        if i != metal_index and el != "H" and i not in dset and i not in cyclo_atoms
        and math.dist(p, mp) < _CO_LIGAND_INTRUDE * (r_m + (optimize._cov_radius(el) or 0.8))
    ]
    return drifted, intruders


def _sigma_ortho_pins(xyz_path, bond_pairs, metal_index, sigma_aryl, metal_symbol,
                      oxidation_state, coordination_number):
    """(metal, ortho C, distance) pins holding each σ aryl donor's ring in the IDEAL σ pose.

    Like :func:`_haptic_aryl_pins`, but the target is the M...C(ortho) distance of a σ aryl at its
    M-C reference length with a 120 deg M-C(ipso)-C(ortho) angle, not the assembled distance: a
    stranded assembly (ppy's ring ~4 A out) would otherwise hold the σ carbon long (Ru-C 2.30 A)."""
    atoms = optimize._read_xyz(Path(xyz_path))
    mp = atoms[metal_index][1]
    out = []
    for d in sorted(sigma_aryl):
        r = optimize._restraint_reference(math.dist(atoms[d][1], mp), metal_symbol, "C",
                                          ox=oxidation_state, cn=coordination_number)
        for a, b in bond_pairs:
            o = b if a == d else a if b == d else None
            if o is None or o == metal_index or atoms[o][0] != "C":
                continue
            cc = math.dist(atoms[d][1], atoms[o][1])
            out.append((metal_index, o, math.sqrt(r * r + cc * cc + r * cc)))  # cos 120 = -1/2
    return out


def _sigma_aryl_slipped(xyz_path, bond_pairs, metal_index, sigma_aryl) -> bool:
    """True if a σ aryl donor's ring slipped toward η: an ORTHO carbon of any σ-aryl donor now
    within ``_CO_LIGAND_INTRUDE`` x the M-C covalent sum (a σ aryl keeps its ortho C ~2.9-3.1 A
    from the metal; an η2+ ring brings them to ~2.1-2.4 A)."""
    atoms = optimize._read_xyz(Path(xyz_path))
    mp = atoms[metal_index][1]
    cut = _CO_LIGAND_INTRUDE * ((optimize._cov_radius(atoms[metal_index][0]) or 1.4)
                                + (optimize._cov_radius("C") or 0.76))
    for d in sigma_aryl:
        for a, b in bond_pairs:
            o = b if a == d else a if b == d else None
            if o is None or o == metal_index or atoms[o][0] != "C":
                continue
            if math.dist(atoms[o][1], mp) < cut:
                return True
    return False


def _sigma_aryl_donors(xyz_path, bond_pairs, metal_index, donor_indices) -> set:
    """Donor indices that are a cyclometalated σ aryl-carbon (same criterion as
    :func:`_haptic_aryl_pins`): a carbon donor whose two neighbours are BOTH ring carbons
    (an aromatic ipso), none of them itself a donor -- so a carbene (N/O neighbours) or an
    η-cap π-donor (ring carbons are donors) never matches.

    When any is present, :func:`build_complex` relaxes the whole complex UNRESTRAINED. The M–L
    restraint pulls such a ring toward the metal (from a long assembled M–Cipso ~2.4 Å to the
    covalent target ~2.05 Å) and that contraction kicks it out of the σ basin into η — the
    Ru/Ir(2-phenylpyridine) piano-stool slip. Freeing only the σ-C from the restraint is not
    enough (the arene/N restraints still slip it); dropping all M–L restraints lets GFN2 settle σ
    exactly as a plain ``xtb --opt`` does (verified on keisan: restrained -> η, unrestrained -> σ).
    A σ M–C bond is strong enough not to dissociate unrestrained."""
    if not bond_pairs or metal_index is None:
        return set()
    atoms = optimize._read_xyz(Path(xyz_path))
    dset = set(donor_indices or [])
    adj: dict[int, set] = {}
    for a, b in bond_pairs:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    out = set()
    for d in donor_indices or []:
        if d == metal_index or d >= len(atoms) or atoms[d][0] != "C":
            continue
        ortho = [n for n in adj.get(d, ()) if n != metal_index and atoms[n][0] == "C"]
        if any(n in dset for n in ortho):
            continue
        if len(ortho) < 2 or not all(
                any(k not in (d, n) and atoms[k][0] == "C" for k in adj.get(n, ())) for n in ortho):
            continue
        out.add(d)
    return out


# A metal-excluded pre-relax step may not tip a monodentate sp2 N donor further out of plane than this.
_PLANAR_TILT_MAX = 25.0


def _planar_donor_dihedrals(xyz_path, bond_pairs, metal_index, donor_indices, snap=True):
    """Keep an sp² donor's metal IN the ring plane, as (metal, D, A, B, target_deg) dihedrals.

    A pyridine N (or an sp²/aromatic O) coordinates in-plane through its in-plane lone pair, so the
    metal, N and the ring are coplanar. xtb, left free, bends the metal OUT of that plane — the N
    starts acting pseudo-sp³ (HUJCAR: M–N 57° out of plane, MOFGEU 16°). Pin the M–D–A–B torsion so
    the metal can't leave the plane: D is the donor, A a heavy neighbour of D, B a heavy neighbour
    of A other than D — three atoms that define the donor's plane.

    The target for an sp² **N** is the IN-PLANE value itself (0° or 180°, whichever the assembly is
    nearer), not the assembled torsion: a pre-relax step can leave the ring tilted (HUJCAR: the
    metal-excluded UFF de-clash tipped the pyridine 50° to clear the cis iodides), and pinning that
    assembled value froze the tilt in instead of removing it. An sp² **O** keeps its assembled
    torsion — an aryloxide/carbonyl M–O–C–C is not confined to the plane the way a pyridine's is.
    ``snap=False`` returns the assembled torsion for every donor (used to MEASURE a tilt).

    Applied to MONODENTATE donors only (the caller passes the monodentate donor subset). A donor that
    shares its ligand with other donors (a chelate arm, a tripodal tris(2-pyridyl)) is left out: the
    chelate bite already fixes its orientation, so forcing its torsion would fight the bite.

    Fires only for an sp² donor: an AROMATIC N/O donor, or one double-bonded to its neighbour (a
    carbonyl/imine O/N), whose neighbour A is itself planar (≥2 heavy neighbours). A σ amine/alkoxide
    (sp³, freely rotating) is left alone. Graph + geometry only; goes to ``$constrain``."""
    if not bond_pairs or metal_index is None:
        return []
    atoms = optimize._read_xyz(Path(xyz_path))
    adj: dict[int, set] = {}
    for a, b in bond_pairs:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)

    out = []
    for d in donor_indices or []:
        if d == metal_index or d >= len(atoms) or atoms[d][0] not in ("N", "O"):
            continue
        heavy = [n for n in adj.get(d, ()) if n != metal_index and atoms[n][0] != "H"]
        # sp²/aromatic donor: a heavy neighbour A reached by a SHORT bond (< 1.40 A: pyridine C–N
        # ~1.34, phenol/carbonyl C–O ~1.22-1.37) that is ITSELF sp² (<= 3 substituents). The short-
        # bond test alone would also catch a FLUORINATED alkoxide -- induction from the CF₃ groups
        # shortens its C–O to ~1.37 -- so require A to be sp²: that alkoxide's central C is sp³
        # (O + H + 2 C = 4 substituents) and is excluded, leaving a real alkoxide free to rotate.
        # (A plain sp³ amine/alkoxide C–O/C–N ~1.43-1.47 never even passes the distance gate.)
        a_cands = [a for a in heavy
                   if math.dist(atoms[d][1], atoms[a][1]) < 1.40
                   and len([k for k in adj.get(a, ()) if k != metal_index]) <= 3]
        # pick A (a short-bonded sp² neighbour of the donor) and B (a further heavy neighbour of A)
        # that, with D, span the donor's plane; skip if the ligand is too small to define one.
        chosen = None
        for a in a_cands:
            for b in adj.get(a, ()):
                if b not in (d, metal_index) and atoms[b][0] != "H":
                    chosen = (a, b)
                    break
            if chosen:
                break
        if not chosen:
            continue
        a, b = chosen
        deg = _dihedral(atoms[metal_index][1], atoms[d][1], atoms[a][1], atoms[b][1])
        if snap and atoms[d][0] == "N":
            deg = 0.0 if abs(deg) < 90.0 else 180.0
        out.append((metal_index, d, a, b, deg))
    return out


def _sp2_n_tilt(xyz_path, bond_pairs, metal_index, donor_indices) -> float:
    """Largest out-of-plane torsion (degrees from 0/180) among the monodentate sp² N donors."""
    atoms = optimize._read_xyz(Path(xyz_path))
    return max((min(abs(deg), 180.0 - abs(deg))
                for _, d, _, _, deg in _planar_donor_dihedrals(xyz_path, bond_pairs, metal_index,
                                                               donor_indices, snap=False)
                if atoms[d][0] == "N"), default=0.0)


def _dihedral(p0, p1, p2, p3) -> float:
    """Signed M–D–A–B torsion in degrees (the four points as (x,y,z) tuples)."""
    import numpy as np
    b0 = np.asarray(p0, float) - np.asarray(p1, float)
    b1 = np.asarray(p2, float) - np.asarray(p1, float)
    b2 = np.asarray(p3, float) - np.asarray(p2, float)
    b1n = b1 / (np.linalg.norm(b1) or 1.0)
    v = b0 - (b0 @ b1n) * b1n
    w = b2 - (b2 @ b1n) * b1n
    x = float(v @ w)
    y = float(np.cross(b1n, v) @ w)
    return math.degrees(math.atan2(y, x))


def _chelate_donor_pairs(constructed, metal_index: int, donor_indices: list[int]) -> set:
    """Donor-atom pairs (as ``frozenset({i, j})``) that belong to the SAME ligand.

    Two metal-bound donors are on the same ligand iff they are connected through
    the ligand backbone -- i.e. reachable via bonds that don't pass through the
    metal. Such pairs are chelate bite angles (set by the ligand, not the
    coordination polyhedron), so the angle restraint leaves them free rather than
    forcing them to the idealised inter-site angle. Uses union-find over all bonds
    except those touching the metal."""
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for bond in constructed.get_bonds():
        a, b = bond.get_atom1().get_id(), bond.get_atom2().get_id()
        if a == metal_index or b == metal_index:
            continue
        parent[find(a)] = find(b)

    from itertools import combinations
    return {frozenset((di, dj)) for di, dj in combinations(donor_indices, 2)
            if find(di) == find(dj)}


def _monodentate_donors(constructed, metal_index: int, donor_indices: list[int]) -> list[int]:
    """The donor atoms that are the SOLE donor of their ligand (monodentate).

    A donor shares a ligand with another donor iff they are connected through the backbone (bonds
    not through the metal) -- :func:`_chelate_donor_pairs`. A donor in no such pair is the only donor
    of its ligand, i.e. a monodentate ligand. Used to scope the sp² planarity guard: a lone
    pyridine/imine assembles in-plane and only needs holding, whereas a chelate/tripodal arm has its
    orientation set by the bite and can assemble off-plane (so pinning it would freeze a bad seat)."""
    chelated = set()
    for pair in _chelate_donor_pairs(constructed, metal_index, donor_indices):
        chelated |= set(pair)
    return [d for d in donor_indices if d not in chelated]


def _angle_constraints_for(geom: Geometry, constructed, metal_index: int,
                           donor_indices: list[int]) -> "list | None":
    """Ideal donor-M-donor angle restraints for this build, or None if the geometry
    has no site model (e.g. metallocene) -- see :func:`optimize.build_angle_constraints`."""
    from .assembly.sites import site_positions, SiteAssignmentError

    try:
        site_dirs = site_positions(geom)
    except SiteAssignmentError:
        return None
    coords = constructed.get_position_matrix()
    chelate = _chelate_donor_pairs(constructed, metal_index, donor_indices)
    return optimize.build_angle_constraints(
        site_dirs, metal_index, donor_indices, coords, chelate_pairs=chelate
    ) or None


def _donor_electron_pairs(complex: Complex) -> int:
    """Electron PAIRS the ligands donate, counting an ηⁿ cap by its true hapticity, not as one site.

    The 18-electron / missing-hydride check needs the electrons donated, but the centroid model
    makes each Cp/arene ONE site (denticity 1), so the naive ``2·CN`` counts a cap as a 2e donor and
    a ferrocene as 10e -> a bogus "4 missing hydrides". Count each π-site by its ionic donation
    (η⁵-Cp = 6e, η⁶-arene = 6e, η⁴-diene = 4e, η³-allyl = 4e, η²-alkene = 2e; even n → n electrons,
    odd n → n+1) plus 2e per σ donor. For a cap-free complex this equals CN, so behaviour is
    unchanged there; ferrocene becomes d6 + 2·(3+3) = 18e and stops crying wolf."""
    pairs = 0
    for lig in complex.ligands:
        sites = lig.pi_sites or []
        pi_atoms = {a for s in sites for a in s}
        for s in sites:
            k = len(s)
            pairs += (k if k % 2 == 0 else k + 1) // 2      # π-site electron pairs (ionic count)
        pairs += sum(1 for a in (lig.coord_atoms or []) if a not in pi_atoms)  # σ donors: 1 pair each
    return pairs


def _n_terminal_oxo_nitrido_ligands(complex: Complex) -> int:
    """Ligands that are a bare O or N with no H ([O-2], [O], [N-3]): a terminal oxo /
    nitrido forming an M=O / M≡N multiple bond. Aqua/hydroxide/amide carry H and are
    not counted — the ligand-level twin of ``_terminal_oxo_donors``, needed before
    assembly because the spin state is fixed up front."""
    from rdkit import Chem

    n = 0
    for lig in complex.ligands:
        mol = Chem.MolFromSmiles(lig.smiles)
        if (mol is not None and mol.GetNumAtoms() == 1
                and mol.GetAtomWithIdx(0).GetSymbol() in ("O", "N")
                and mol.GetAtomWithIdx(0).GetTotalNumHs() == 0):
            n += 1
    return n


def _uhf_for(complex: Complex, geometry_: Geometry, warnings: list[str]) -> int:
    """Unpaired electrons for xtb --uhf from the spin model; 0 (with a warning) if
    the d-count can't be determined so the caller can override spin."""
    from . import spin

    n_multiple = _n_terminal_oxo_nitrido_ligands(complex)
    try:
        uhf = spin.unpaired_electrons(
            complex.metal.symbol, complex.metal.oxidation_state, geometry_, complex.spin,
            n_terminal_multiple=n_multiple,
        )
        if n_multiple and uhf == 0 and complex.spin is Spin.LOW and spin.d_count_or_none(
                complex.metal.symbol, complex.metal.oxidation_state) == 2:
            warnings.append(
                f"spin: d2 {complex.metal.symbol}({complex.metal.oxidation_state}) with a "
                f"terminal oxo/nitrido treated as a closed-shell singlet (uhf=0; both d "
                f"electrons paired in dxy). Choose high spin to force the triplet.")
        return uhf
    except spin.SpinError as exc:
        warnings.append(f"spin model fell back to uhf=0: {exc}")
        return 0


def _drop_meridional_tripods(complex, geom, specs):
    """Drop enumerated isomers that put a tripodal tridentate (tacn, Tp, a bis(pyridyl)methyl
    tripod; :func:`assembly.is_tripodal`) on a non-facial triple: it cannot span a trans pair,
    so those "isomers" only fuse under xtb. Keeps the list unchanged if nothing facial is left
    (e.g. square planar, where every triple has a trans pair)."""
    import itertools

    from .assembly import sites

    tripods = [i for i, l in enumerate(complex.ligands) if assembly.is_tripodal(l)]
    if not tripods or geom not in sites.SITE_VECTORS:
        return specs
    adj = sites._adjacency(geom, complex.coordination_number)

    def facial(spec):
        if not getattr(spec, "site_based", False):
            return True
        return all(b in adj[a] for i in tripods
                   for a, b in itertools.combinations(spec.assignment.get(i, ()), 2))

    kept = [s for s in specs if facial(s)]
    return kept or specs


def build_complex(
    complex: Complex,
    output_dir: str | Path,
    *,
    all_isomers: bool = False,
    stereo: bool = True,
    isomers_override: "list | None" = None,
    site_assignment: "dict | None" = None,
    relax: bool = False,
    angle_restraint: bool = False,
    linear_restraint: bool = True,
    orient_bulky: bool = True,  # de-clash bulky ligands (phosphines, pincer arms) via guarded UFF
    reposition_donors: bool = True,  # slide stranded monodentates in to their CSD M-L reference
    reposition_polydentates: bool = False,  # OPT-IN: slide stranded chelates/pincers (washes out post-xtb; can regress)
    clear_metal_region: bool = True,  # rotate a monodentate whose backbone folded into the M-donor region
    declash_torsion: bool = True,  # spin crowded bulky monodentates about their M-donor axis to mesh arms
    haptic_guard: bool = True,  # pin sigma aryl-carbon donors so xtb can't slip them to eta-arene
    planar_guard: bool = True,  # pin sp2 N/O donors coplanar with the metal (no pseudo-sp3 bend)
    mchammer: bool = True,  # off: never run MCHammer, hand xtb the raw stk placement (ideal site vectors)
    mchammer_fallback: bool = True,  # skip MCHammer when it collapses the raw stk placement
    reembed_crowded: bool = True,  # re-embed a collapsed sphere jointly (Pt(PPh3)4, Pt(BINAP)2)
    antifusion_guard: bool = True,  # re-relax with floors ONLY if xtb fused two inter-ligand donors
    oxo_antifusion_floors: bool = False,  # OPT-IN: pre-floor terminal oxo/nitrido (blanket; over-constrains)
    oxo_floor_fc: float = 5.0,  # force constant for the anti-fusion floors (reactive path + opt-in preemptive)
    metal_surrogate: bool = False,  # opt-in: relax Y as Sc (xtb-friendly), restore Y after
    uff_fallback: bool = False,  # opt-in: UFF relax when every xtb tier fails (Y/Sc)
    two_stage_relax: bool = True,
    revert_on_bond_change: bool = False,  # off: let xtb re-form bonds to fix bad initial placement
    registry_for_sites: bool = False,
    formats: "tuple[str, ...] | list[str]" = ("xyz",),  # also emit .mol/.pdb beside each .xyz
    xtb_bin: str = "xtb",
    xtb_timeout_s: int = 600,
    max_isomers: int | None = None,
    max_isomers_high_cn: int | None = None,  # tighter cap for CN > 6 (each isomer is slow)
    progress: "Callable[[str], None] | None" = None,
) -> list[BuildResult]:
    """Run the pipeline for one complex; return one result per isomer built.

    ``site_assignment`` ({ligand index -> ordered site ids}) builds one exact
    isomer via the dynamic site model (cis/trans, asymmetric chelates). Otherwise
    ``isomers_override`` (IsomerSpec list) builds those, ``all_isomers`` enumerates
    distinct isomers, and the default builds one canonical isomer.

    With ``all_isomers`` and ``stereo`` (default), enumeration runs through the
    site model (:func:`isomers.enumerate_site_isomers`) so Delta/Lambda
    enantiomers and asymmetric-chelate donor directions split out; it falls back
    to the coarse vertex enumeration where the site model can't express the
    complex (e.g. facial arene caps). ``stereo=False`` gives the coarse count.
    ``relax`` runs the xtb GFN step (invariant 4: correct charge and --uhf).

    When ``relax`` builds more than one isomer, the returned results are ordered
    lowest-GFN2-energy first, with :attr:`BuildResult.relative_energy_kcal` and
    :attr:`BuildResult.is_lowest_energy` filled in (see :func:`_rank_by_energy`).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    from . import export

    formats = export.normalize_formats(formats)  # validate up front; always includes "xyz"

    # Donor-index isomer notation ("mode 3") from the input. Its donor
    # atoms must be pinned BEFORE perception (they set each ligand's denticity);
    # its site assignment becomes the isomer to build, once the geometry is known.
    # An explicit site_assignment / isomers_override argument takes precedence.
    notation = None
    if (
        complex.isomer_spec
        and site_assignment is None
        and isomers_override is None
    ):
        notation = isomers.parse_isomer_notation(complex.isomer_spec)
        for lig_idx, atoms in notation.donors.items():
            if not 0 <= lig_idx < len(complex.ligands):
                raise ValueError(
                    f"isomer notation refers to ligand {lig_idx} but the complex "
                    f"has {_plural(len(complex.ligands), 'ligand')}."
                )
            complex.ligands[lig_idx].donor_override = list(atoms)

    _report(progress, "perceiving ligands")
    resolve_perception(complex)
    # A ligand with no perceived donors cannot be placed on any site; name it here
    # with an actionable message instead of surfacing a cryptic downstream
    # SiteAssignmentError ("Denticities [...,0] cannot fill N sites").
    no_donors = [l.smiles for l in complex.ligands if not l.effective_donors]
    if no_donors:
        from . import perception

        raise perception.PerceptionError(
            f"No coordinating atoms perceived for {noun(len(no_donors), 'ligand')}: "
            + ", ".join(no_donors)
            + ". Specify donor atoms for these ligands (donor override / isomer "
            "notation), or remove them if they are non-coordinating."
        )
    # Metallocenes route by their two eta-caps, not by summed CN (which would be 6
    # or 8 and mislabel/​unsupport them). Only when no geometry was set explicitly.
    geom = complex.geometry
    if geom is None:
        geom = geometry.detect_metallocene(
            [l.denticity for l in complex.ligands],
            [any(len(s) >= 3 for s in l.pi_sites) for l in complex.ligands],
        ) or geometry.propose_geometry(
            complex.coordination_number,
            spin.d_count_or_none(complex.metal.symbol, complex.metal.oxidation_state),
            denticities=[l.denticity for l in complex.ligands],
            lone_pair=spin.has_stereo_active_lone_pair(
                complex.metal.symbol, complex.metal.oxidation_state
            ),
        )
    if notation is not None and notation.geometry is not None:
        geom = notation.geometry
    # Centroid η-caps (Cp/arene ring caps, one site each at the ring centroid). A
    # two-cap metallocene fragment is LINEAR when bare, or a BENT metallocene (Cp2MXn
    # — caps up and apart, ancillary ligands in the equatorial wedge) when it carries
    # ancillary donors. Neither is a flat CN geometry, so coerce onto the right one;
    # the site model then seats each cap η5/η6 with the ancillary ligands in the wedge.
    #
    # A single cap can arrive from the web UI with a stale geometry: parse-time
    # auto-perception represents Cp/arene as a three-site facial ligand, while the
    # build request's explicit ring atoms use the one-site centroid convention.
    # Re-propose only when that geometry no longer belongs to the post-perception CN.
    # This preserves a compatible explicit user choice while preventing, for example,
    # CpMn(CO)3 from trying to put four centroid sites into an octahedron.
    # (is_arene facial caps have no pi_sites, so they are untouched and keep the fixed
    # facial-triad metallocene topology.)
    cap_sites = sum(1 for l in complex.ligands for s in (l.pi_sites or []) if len(s) >= 3)
    if cap_sites == 2:
        geom = (Geometry.LINEAR if complex.coordination_number == 2
                else Geometry.METALLOCENE_BENT)
    elif cap_sites:
        cn_geometries = geometry.geometries_for_cn(complex.coordination_number)
        if geom not in cn_geometries:
            geom = geometry.propose_geometry(
                complex.coordination_number,
                spin.d_count_or_none(
                    complex.metal.symbol, complex.metal.oxidation_state
                ),
                denticities=[l.denticity for l in complex.ligands],
                lone_pair=spin.has_stereo_active_lone_pair(
                    complex.metal.symbol, complex.metal.oxidation_state
                ),
            )
    if notation is not None and notation.sites:
        isomers_override = [
            isomers.IsomerSpec(
                geometry=geom, label="custom",
                assignment=dict(notation.sites), site_based=True,
            )
        ]

    # builds: list of (constructed molecule, topology label, isomer label, assembly note)
    builds: list[tuple] = []
    isomer_cap_note = None
    if site_assignment is not None:
        constructed, label, note = _assemble(
            lambda mch: assembly.build_from_sites(
                complex, geom, site_assignment, prefer_registry=registry_for_sites, mchammer=mch),
            complex, geom, mchammer_fallback, mchammer, reembed_crowded)
        builds.append((constructed, label, "custom", note))
    else:
        # Enumerate one past the cap so an overflow is detectable, and never more than the
        # enumerators' own default (64): a many-monodentate CN8/9 complex has thousands.
        # CN > 6 gets its own, tighter cap: a CN8/9 sphere of mixed monodentates enumerates
        # hundreds of isomers at ~12 s of assembly each. At CN <= 6 the 64 cap never bites (six
        # different monodentates give 30 stereoisomers).
        if max_isomers_high_cn is not None and complex.coordination_number > 6:
            max_isomers = (max_isomers_high_cn if max_isomers is None
                           else min(max_isomers, max_isomers_high_cn))
        enum_cap = 64 if max_isomers is None else min(64, max_isomers + 1)
        if isomers_override is not None:
            specs = isomers_override
        elif all_isomers:
            try:
                specs = isomers.enumerate_site_isomers(
                    complex, geom, stereo=stereo, max_isomers=enum_cap)
            except isomers.StereoNotSupported:
                # Site enumerator can't stereo-enumerate this (e.g. denticity >= 4).
                # Try the fixed-registry enumerator; if that geometry/partition has
                # no fixed topology either, fall back to the single canonical isomer
                # (default_isomer routes through the site model) rather than crash.
                try:
                    specs = isomers.enumerate_isomers(complex, geom, max_isomers=enum_cap)
                except isomers.UnsupportedTopology:
                    specs = [assembly.default_isomer(complex, geom)]
        else:
            specs = [assembly.default_isomer(complex, geom)]
        if all_isomers and isomers_override is None:
            specs = _drop_meridional_tripods(complex, geom, specs)
        # Cap BEFORE assembly: each spec costs two stk/MCHammer builds (and later an xtb run),
        # so trimming only the finished builds let one "all isomers" click on a CN8 complex
        # with 8 mixed monodentates spend 20+ min assembling 64 isomers to keep a handful.
        if max_isomers is not None and len(specs) > max_isomers:
            isomer_cap_note = (
                f"more than {max_isomers} isomers enumerated; built the first "
                f"{max_isomers} (limit).")
            specs = specs[:max_isomers]
        for spec in specs:
            if getattr(spec, "site_based", False):
                make = (lambda mch, sp=spec: assembly.build_from_sites(
                    complex, sp.geometry, dict(sp.assignment),
                    prefer_registry=registry_for_sites, mchammer=mch))
            else:
                make = (lambda mch, sp=spec: assembly.build(complex, sp, mchammer=mch))
            constructed, label, note = _assemble(
                make, complex, spec.geometry, mchammer_fallback, mchammer, reembed_crowded)
            builds.append((constructed, label, spec.label, note))

    if all_isomers and stereo and len(builds) > 1:
        builds = _restore_collapsed_enantiomers(builds)

    charge = complex.total_charge
    warnings: list[str] = []
    from . import inputs

    for lig in complex.ligands:
        w = inputs.radical_warning(lig.smiles)
        if w:
            warnings.append(w)
    # Possible missing hydride(s): X-ray CIFs rarely locate M-H, so a hydrido complex mines with
    # its CN too low. Flag the 18-electron shortfall so the user knows the sphere may be incomplete.
    n_h = spin.possible_missing_hydrides(
        complex.metal.symbol, complex.metal.oxidation_state, _donor_electron_pairs(complex))
    if n_h:
        warnings.append(
            f"possible {_plural(n_h, 'missing hydride ligand')}: {complex.metal.symbol}"
            f"({complex.metal.oxidation_state}) with {complex.coordination_number} donors is "
            f"{2 * n_h}e short of the 18e (16e for d8) count — X-ray CIFs seldom locate M-H, so a "
            f"hydrido complex mines with too few donors. Verify the coordination sphere/charge.")
    # A centroid η-cap is ONE site for placement but donates a facial triad to the d-orbital
    # field, so the CN-derived geometry splits the d electrons on the wrong pattern — for a
    # bare sandwich (placed LINEAR) and equally for a one-cap piano stool (placed tetrahedral
    # at CN 4). Resolve the splitting geometry separately; placement (geom) is unchanged.
    cap_ring_sizes = [len(s) for l in complex.ligands
                      for s in (l.pi_sites or []) if len(s) >= 3]
    spin_geom = geometry.spin_geometry(geom, cap_ring_sizes, complex.coordination_number)
    uhf = _uhf_for(complex, spin_geom, warnings)
    # xtb (GFN2/GFN-FF) does not reliably treat f-block metals; skip relaxation
    # for them and return the assembled geometry, flagged with a warning.
    skip_xtb_fblock = relax and inputs.is_f_block(complex.metal.symbol)
    if skip_xtb_fblock:
        warnings.append(
            f"{complex.metal.symbol} is an f-block element (lanthanide/actinide); "
            f"xtb cannot reliably relax it, so the assembled (pre-relax) geometry is "
            f"returned without xtb relaxation."
        )
    do_relax = relax and not skip_xtb_fblock
    # The isomer cap was applied before assembly (above), so neither assembly nor the
    # relax loop can be asked for unbounded work.
    if isomer_cap_note:
        warnings.append(isomer_cap_note)
    multi = len(builds) > 1
    results: list[BuildResult] = []
    for i, (constructed, label, iso_label, assembly_note) in enumerate(builds, start=1):
        base = complex.name or label
        stem = naming.make_stem(
            base, charge,
            isomer_index=(i if multi else None),
            isomer_label=iso_label,
        )
        iso_warnings = list(warnings)
        if assembly_note:
            iso_warnings.append(assembly_note)
        # Collision-free and contained within output_dir (sanitized stem + a
        # numeric suffix if the name already exists), so repeated/adversarial
        # names never escape the directory or silently overwrite a prior result.
        xyz = naming.unique_output_path(output_dir, stem)
        constructed.write(str(xyz))
        n = len(builds)
        _report(progress, f"relaxing isomer {i}/{n} (xtb)" if do_relax
                else f"writing isomer {i}/{n}")
        # The true metal + donor indices from the topology: used to restrain the
        # coordination sphere during relaxation AND to draw exact metal-donor bonds
        # in the 3D viewer (both need the .xyz-aligned indices).
        metal_index, donor_indices = _metal_bonded_donors(constructed, complex.metal.symbol)
        if reposition_donors:
            # The site model seats donors on a generic 2.5 A shell and MCHammer pushes a bulky
            # monodentate out to ~3 A (OGOLAX terphenyl-phenoxide). Slide each stranded monodentate
            # rigidly in to its CSD M-L reference so xtb starts from a physically correct sphere.
            optimize.reposition_stranded_monodentates(
                xyz, constructed, metal_index, donor_indices,
                metal_symbol=complex.metal.symbol,
                oxidation_state=complex.metal.oxidation_state,
                coordination_number=complex.coordination_number)
            if reposition_polydentates:
                # A chelate/pincer's donors are coupled by the backbone, so the monodentate slide
                # above skips them and they stay at stk's generic ~3 A placement -- xtb then drags
                # them ~0.7 A inward through the sphere and can fuse a donor onto a neighbour. Slide
                # the whole chelate in to its CSD reference (bite-preserving, clash-guarded).
                optimize.reposition_stranded_polydentates(
                    xyz, constructed, metal_index, donor_indices,
                    metal_symbol=complex.metal.symbol,
                    oxidation_state=complex.metal.oxidation_state,
                    coordination_number=complex.coordination_number)
        if clear_metal_region:
            # Backbone in the metal-donor region: rotate a monodentate whose body was folded onto
            # the metal so it points outward again (bonder stays on its site). Log how many moved.
            nfix = optimize.orient_monodentate_body_outward(xyz, constructed, metal_index, donor_indices)
            if nfix:
                iso_warnings.append(f"cleared the metal-donor region: re-oriented "
                                    f"{_plural(nfix, 'monodentate ligand')} whose backbone was "
                                    f"folded toward the metal.")
        if declash_torsion:
            # Crowded bulky monodentates that seat their cones outward yet still interpenetrate a
            # neighbour (VOFRAJ: a phenoxide + two tribenzylphosphines on a trigonal Ni, arms fused
            # at <1 A). Spin each about its M-donor axis -- rigid (no bond breaks, unlike the UFF
            # de-clash that mangles a P-C here) and cone-preserving -- to mesh the arms instead of
            # colliding. Kept only if the inter-ligand overlap drops.
            ntor = optimize.declash_monodentate_torsion(xyz, constructed, metal_index, donor_indices)
            if ntor:
                iso_warnings.append(f"de-clashed {_plural(ntor, 'bulky monodentate')} by axial rotation "
                                    f"(meshed interpenetrating substituent arms).")
        if orient_bulky:
            # Bulky-ligand de-clash: when a ligand's substituents ram into a neighbour -- a
            # phosphine cone (IFASOA: three PPh3 whose phenyls collide) OR a multidentate's arm
            # crowding a small co-ligand (a PCP pincer's isopropyl jammed against a carbonyl) --
            # relax the ligand shell with the metal-excluded UFF so the bodies splay, but keep it
            # only if it reduces the inter-ligand overlap, so a sphere it would worsen is reverted.
            # That UFF excludes the metal, so nothing in it holds a pyridine's metal in the ring
            # plane: it can "de-clash" by tipping the ring (HUJCAR: 50 deg, to clear cis iodides).
            # Revert when it tilts a monodentate sp2 N donor out of plane.
            _bonds = _topology_bonds(constructed)
            _mono = _monodentate_donors(constructed, metal_index, donor_indices)
            _before_txt = Path(xyz).read_text(encoding="utf-8")
            _tilt0 = _sp2_n_tilt(xyz, _bonds, metal_index, _mono)
            optimize.declash_bulky_ligands(
                xyz, constructed, metal_index, donor_indices,
                oxidation_state=complex.metal.oxidation_state,
                coordination_number=complex.coordination_number)
            _tilt1 = _sp2_n_tilt(xyz, _bonds, metal_index, _mono)
            if _tilt1 > _PLANAR_TILT_MAX and _tilt1 > _tilt0 + 10.0:
                Path(xyz).write_text(_before_txt, encoding="utf-8")
                iso_warnings.append(
                    f"bulky-ligand de-clash reverted: it tilted an sp2 N donor {_tilt1:.0f} deg "
                    f"out of its ring plane.")
        energy = None
        connectivity_ok = True
        if do_relax:
            # A metallocene binds each Cp through a 3-carbon facial triad, but the
            # ring binds η5/η6. Restraining only the triad slips the ring; dropping
            # the restraint entirely lets an *asymmetric* cap (a substituted Cp with
            # a heavy sidechain, e.g. ferroquine) tilt off-axis under free xtb. So
            # restrain EVERY ring carbon of each cap to the metal — that holds the
            # ring symmetric and centred while xtb still relaxes conformation.
            # A centroid η-cap (denticity-1 ring, from a donor override) binds the
            # metal to every ring carbon; like a metallocene it must relax with the
            # metal FREE (ligand-internal bonds only) so xtb settles symmetric η5,
            # rather than pinning all N metal-carbon bonds (which crushes the ring).
            has_ring_cap = any(
                l.pi_sites and any(len(s) >= 3 for s in l.pi_sites) for l in complex.ligands
            )
            eta_sandwich = geom in (Geometry.METALLOCENE, Geometry.METALLOCENE_BENT)
            relax_bonds = _topology_bonds(constructed)
            angle_cons = None
            if has_ring_cap:
                # Each centroid η-cap is bonded to EVERY ring carbon. Hold all of
                # them to the metal (not just the σ legs) so the metal stays centred
                # over the ring and cannot slide to the ring edge under xtb in a busy
                # sphere — the "ring slip" seen on cymene/Cp piano-stools (RUHDOQ,
                # LIBFOU). Equal M–C targets force the metal onto the ring axis at the
                # centroid, pinning slip AND tilt, exactly like the legacy facial-triad
                # path below. (An earlier version freed the ring to let xtb settle a
                # symmetric η5/η6, but with the ring bonded symmetrically at assembly
                # that freedom only let the metal drift off-axis in crowded spheres.)
                restraint_donors = sorted(
                    set(donor_indices) | set(_eta_cap_ring_atoms(constructed, donor_indices))
                )
            elif eta_sandwich:
                # Legacy facial-triad metallocene: hold every ring carbon to the metal.
                restraint_donors = _eta_cap_ring_atoms(constructed, donor_indices)
            else:
                restraint_donors = donor_indices
                # Ideal donor-M-donor angle restraints (OFF by default; net wash on a
                # 95-complex CSD set — real angles scatter +/-8-17 deg around ideal).
                angle_cons = (
                    None if not angle_restraint
                    else _angle_constraints_for(geom, constructed, metal_index, donor_indices)
                )
            # Linear-donor linearity restraint (Phase 3): CN-/CO/isocyanide/azide/nitrosyl
            # donors bind end-on and must stay linear (M-C≡N ~180°), else xtb lets them bend
            # inward and clash (ZIVCUF). Detected from the assembled graph, added to $constrain.
            if linear_restraint:
                lin = _linear_donor_angles(xyz, relax_bonds, metal_index, donor_indices)
                if lin:
                    angle_cons = (angle_cons or []) + lin
            # Planarity guard (Phase 3): keep an sp2 donor's metal in the ring plane so xtb can't
            # bend the pyridine/phenol out of plane (pseudo-sp3 N -- HUJCAR 57 deg, MOFGEU 16 deg).
            # Planarity guard scoped to MONODENTATE sp2 donors: a lone pyridine/imine assembles in
            # its plane along the lone pair and only needs holding there (HUJCAR, MOFGEU). A chelate
            # or tripodal arm has its orientation set by the bite -- excluded, since its assembled
            # dihedral can be off-plane and pinning it would freeze a bad seat (GERYUY's tripodal
            # tris(2-pyridyl)).
            dihedral_cons = (
                _planar_donor_dihedrals(
                    xyz, relax_bonds, metal_index,
                    _monodentate_donors(constructed, metal_index, donor_indices))
                if planar_guard else None
            )
            if dihedral_cons:
                iso_warnings.append(
                    f"planarity guard: pinned {_plural(len(dihedral_cons), 'M-donor torsion')} to "
                    f"keep monodentate sp2 N/O {noun(len(dihedral_cons), 'donor')} coplanar with the "
                    f"metal (no pseudo-sp3 bend).")
            # Metal surrogate: a metal whose GFN2 diverges (Y) is relaxed as an xtb-friendly
            # stand-in of the same charge/d-count (Sc(III) for Y(III)), then the real symbol is
            # restored. xtb sees Sc and converges; the M-L restraints then use Sc's reference
            # bond lengths, so the geometry is Sc's — a physically sensible Y proxy.
            surrogate = optimize.xtb_surrogate(complex.metal.symbol) if metal_surrogate else None
            if surrogate:
                iso_warnings.append(
                    f"relaxed with {surrogate} as an xtb surrogate for {complex.metal.symbol} "
                    f"(same charge/d-count), then restored {complex.metal.symbol}.")
            # Cyclometalated σ aryl-carbon donors: relax UNRESTRAINED. The M–L bond restraint pulls
            # such a ring toward the metal and nucleates an η slip (Ru/Ir(2-phenylpyridine) piano-
            # stools -> η-phenyl), while a plain `xtb --opt` with the same charge/uhf keeps σ. Freeing
            # only the σ-C is not enough -- the arene/N restraints still slip it -- so when one is
            # present we drop ALL M–L restraints for this relaxation and let xtb settle σ, exactly as
            # the plain optimiser does (verified on keisan: restrained -> η, unrestrained -> σ).
            # CYCLOMETALATED only: a σ-aryl whose ligand carries another donor (ppy's C^N). A
            # MONODENTATE aryl (Ph, tolyl; σ since the σ-aryl perception fix) relaxed free let the
            # aryl and its neighbours drift off (XUVZOE Pt(BIAN)(Ph)(MeCN): Ph 3.66 A, MeCN 2.96 A,
            # BIAN ring C fused into the sites), so it keeps the restrained relax plus the ortho pins
            # of the hapticity guard below, the path built for a monodentate mesityl (UMIZOG).
            sigma_aryl = _sigma_aryl_donors(xyz, relax_bonds, metal_index, donor_indices)
            if sigma_aryl:
                _comp = optimize._components_excluding(
                    relax_bonds, len(optimize._read_xyz(Path(xyz))), metal_index)
                sigma_aryl = {d for d in sigma_aryl
                              if any(_comp[o] == _comp[d] for o in donor_indices if o != d)}
            restrain_this = not bool(sigma_aryl)
            # Hapticity guard: pin a σ aryl-carbon donor's ortho carbons so xtb can't rock the ring
            # into η-arene (UMIZOG's mesityl -> η6). Moot when unrestrained (no restraint to fight).
            extra = None
            if haptic_guard and restrain_this:
                pins = _haptic_aryl_pins(xyz, relax_bonds, metal_index, donor_indices)
                if pins:
                    extra = pins
                    iso_warnings.append(
                        f"hapticity guard: pinned {_plural(len(pins), 'ortho M–C distance')} to "
                        f"keep the σ aryl-carbon {noun(len(sigma_aryl), 'donor')} from slipping to "
                        f"η-arene during xtb.")
            free_donors = _terminal_oxo_donors(constructed, metal_index, donor_indices)
            oxo_floors = None
            if oxo_antifusion_floors and free_donors and restrain_this:
                _pre = optimize._read_xyz(Path(xyz))
                _comp = optimize._components_excluding(relax_bonds, len(_pre), metal_index)
                oxo_floors = _preemptive_oxo_floors(_pre, free_donors, _comp, metal_index) or None
                if oxo_floors:
                    iso_warnings.append(
                        f"anti-fusion: pre-floored {_plural(len(oxo_floors), 'terminal-oxo/donor pair')} "
                        f"at fc={oxo_floor_fc} to block deoxygenation during xtb. These are "
                        f"two-sided restraints holding each oxo at its PRE-RELAX separations, so "
                        f"a poorly seated oxo stays long (check the M=O length); leave this off "
                        f"unless the default build fuses.")
            if not restrain_this:
                iso_warnings.append(
                    f"{_plural(len(sigma_aryl), 'cyclometalated σ aryl-carbon donor')} present: relaxed "
                    f"UNRESTRAINED -- the M–L restraint slips the aryl to η; plain xtb keeps σ.")

            def _relax(target_xyz, extra_distances, strong=None, restrain=None, donors=None):
                """One xtb relaxation of ``target_xyz`` (handles the Y->surrogate metal swap).

                ``strong`` overrides the high-FC floor set for this call (the reactive anti-fusion
                re-relax passes the fused pairs); otherwise the opt-in preemptive ``oxo_floors``.
                ``restrain``/``donors`` override the M-L restraint switch and the restrained donor
                set (the σ-aryl co-ligand re-relax restrains only the co-ligands' donors)."""
                if surrogate:
                    optimize.swap_metal_symbol(target_xyz, metal_index, surrogate)
                out_xyz, out_e = _relax_tiered(
                    target_xyz, charge=charge, uhf=uhf, output_dir=output_dir, xtb_bin=xtb_bin,
                    metal_symbol=surrogate or complex.metal.symbol,
                    coordination_number=complex.coordination_number,
                    oxidation_state=complex.metal.oxidation_state,
                    metal_index=metal_index,
                    donor_indices=restraint_donors if donors is None else donors,
                    free_donors=free_donors,
                    angle_constraints=angle_cons, dihedral_constraints=dihedral_cons,
                    bond_pairs=relax_bonds, warnings=iso_warnings, timeout_s=xtb_timeout_s,
                    restrain=restrain_this if restrain is None else restrain,
                    two_stage=two_stage_relax,
                    revert_on_bond_change=revert_on_bond_change, constructed=constructed,
                    uff_fallback=uff_fallback, extra_distances=extra_distances,
                    strong_distances=strong if strong is not None else oxo_floors,
                    strong_fc=oxo_floor_fc,
                    reference_metal=complex.metal.symbol if surrogate else None)
                if surrogate:
                    optimize.swap_metal_symbol(out_xyz, metal_index, complex.metal.symbol)  # restore Y
                return out_xyz, out_e

            pre_relax = Path(xyz).read_text(encoding="utf-8") if antifusion_guard else None
            assembled_text = Path(xyz).read_text(encoding="utf-8") if sigma_aryl else None
            xyz, energy = _relax(xyz, extra)
            # Connectivity guard: the M-L restraint holds *existing* bonds near their assembled
            # length, but nothing stops xtb forging a NEW bond between clashing atoms (ligand-ligand
            # fusion) or an outright collapse.
            new_bonds, broken_bonds = _new_or_broken_bonds(relax_bonds, xyz, metal_index)
            # Anti-fusion re-relax (detect-then-fix): if xtb forged a NEW bond between two donors --
            # of DIFFERENT ligands (cis carbonyls -> C-C, an oxo onto a thiolate, an iodide onto an
            # amide), or of the SAME ligand but far apart in the backbone (a chelating diyl whose bite
            # collapsed, CPFPRH's 1,4-bis-carbanion metallacycle folding shut) -- a fusion the plain
            # relax can't undo -- re-relax ONCE from the assembled geometry with a distance floor
            # holding exactly those pairs at their assembled separation, keeping it only if it cleared
            # the fusion. A second xtb runs ONLY for the few % that actually fuse (self-selecting via
            # the connectivity guard), and a sphere that relaxed clean is never touched -- so it can't
            # distort a good geometry the way a blanket floor did (REYMUD's chlorides, TELLEF's
            # cyanides).
            if antifusion_guard and new_bonds and pre_relax is not None:
                comp = optimize._components_excluding(
                    relax_bonds, len(optimize._read_xyz(Path(xyz))), metal_index)
                dset = set(donor_indices)

                def _fusions(nb):
                    pairs = (_interligand_donor_fusions(nb, comp, dset)
                             + _intraligand_diyl_fusions(nb, comp, relax_bonds, dset, metal_index)
                             + _oxo_fusions(nb, comp, free_donors))
                    return sorted({(min(a, b), max(a, b)) for a, b in pairs})

                fused = _fusions(new_bonds)
                if fused:
                    # Reactive strong-floor re-relax: hold exactly the fused pairs apart in a STIFF
                    # (oxo_floor_fc) $constrain block -- the soft global FC can't resist a deoxygenation
                    # drive, which is why the old soft floor cleared only some -- restarting from the
                    # assembly and iterating until no new fusion remains (a floored pair can shove the
                    # fusion onto a neighbour, so we add survivors and retry). Self-selecting: only a
                    # sphere that ACTUALLY fused is touched, so a clean geometry is never distorted.
                    n0 = len(fused)
                    best_text = Path(xyz).read_text(encoding="utf-8")   # first relax = the fallback
                    best_energy, best_new, best_broken, best_n = energy, new_bonds, broken_bonds, n0
                    Path(xyz).write_text(pre_relax, encoding="utf-8")  # assembly geometry
                    pre_atoms = optimize._read_xyz(Path(xyz))          # floor targets from the assembly
                    floor_pairs = set(fused)
                    # Iterate: a floored pair can shove the fusion onto a DIFFERENT acceptor (an oxo
                    # with several cis phosphines), so keep flooring newly-fused pairs -- not just when
                    # the count drops -- until none remain or the survivors are all already floored
                    # (a floored pair that re-fuses means the floor cannot hold it; stop).
                    for _ in range(5):
                        Path(xyz).write_text(pre_relax, encoding="utf-8")
                        floors = _fusion_floors(pre_atoms, sorted(floor_pairs))
                        xyz, r_energy = _relax(xyz, extra, strong=floors)
                        r_new, r_broken = _new_or_broken_bonds(relax_bonds, xyz, metal_index)
                        r_fused = set(_fusions(r_new))
                        if len(r_fused) < best_n:          # record the best (fewest-fusion) result
                            best_text = Path(xyz).read_text(encoding="utf-8")
                            best_energy, best_new, best_broken, best_n = (
                                r_energy, r_new, r_broken, len(r_fused))
                        if not r_fused:
                            break                          # fully cleared
                        new_pairs = r_fused - floor_pairs
                        if not new_pairs:
                            break                          # survivors already floored -> can't hold
                        floor_pairs |= new_pairs           # relocated fusion -> floor it too, retry
                    Path(xyz).write_text(best_text, encoding="utf-8")
                    energy, new_bonds, broken_bonds = best_energy, best_new, best_broken
                    iso_warnings.append(
                        f"anti-fusion: xtb fused {_plural(n0, 'pair')}; re-relaxed with strong distance "
                        f"floors ({best_n} remaining).")
            if sigma_aryl:
                # Runs AFTER the anti-fusion step (whose re-relax is unrestrained here and would
                # undo this). The σ-aryl policy frees EVERY M-L restraint, co-ligands included, so a floppy
                # co-ligand arm can wander off and a backbone atom take its site (Ru(tpa)(ppy): a
                # CH2-pyridine at 5.3 A, a tpa carbon at 2.06 A). Detect-then-fix: only if that
                # happened, re-relax ONCE from the assembly with the co-ligands' donors restrained
                # and the cyclometalated ligand still free (so its aryl keeps the σ basin), and
                # keep it only if it clears the drift without slipping the aryl. A co-ligand that
                # relaxed fine is never touched.
                n_at = len(optimize._read_xyz(Path(xyz)))
                cyclo_atoms, co_donors = _cyclometalated_split(
                    relax_bonds, n_at, metal_index, donor_indices, sigma_aryl)
                # Every donor is checked: a pincer's own P arm (MOHWOX, NEVNIO) or a C^N ligand's N
                # (DUYTAU) wanders off the same way as a co-ligand arm.
                all_args = (metal_index, list(donor_indices), cyclo_atoms, donor_indices,
                            complex.metal.symbol, complex.metal.oxidation_state,
                            complex.coordination_number)
                drifted, intruders = _co_ligand_drift(xyz, *all_args)
                if drifted or intruders:
                    first_text, first_energy = Path(xyz).read_text(encoding="utf-8"), energy
                    # Restraining the co-ligands alone still rocks the free aryl into η (Ru(tpa)(ppy):
                    # ortho CH 2.38 A), so pin each σ aryl's ORTHO carbons at their assembled σ
                    # distances (the hapticity guard) in every attempt. Attempts, cheapest first:
                    # co-ligand donors only (the σ aryl ligand free), then every donor. Accept the
                    # first where EVERY donor is bound (the co-ligand restraint can instead shove the
                    # σ carbon off: Ru-C 3.29 A), no atom took a site and no aryl slipped.
                    Path(xyz).write_text(assembled_text, encoding="utf-8")
                    pins = _sigma_ortho_pins(xyz, relax_bonds, metal_index, sigma_aryl,
                                             complex.metal.symbol, complex.metal.oxidation_state,
                                             complex.coordination_number)
                    fixed = None
                    # A rigid pincer can't meet the ideal-σ ortho pins AND its P/N restraints (MOHWOX:
                    # Ir-C crushed to 1.77 A), so the last attempt drops the pins.
                    attempts = ([("the co-ligand donors", co_donors, pins)] if co_donors else []) + [
                        ("every donor", list(restraint_donors), pins),
                        ("every donor (no ortho pins)", list(restraint_donors), [])]
                    for label, donors, att_pins in attempts:
                        Path(xyz).write_text(assembled_text, encoding="utf-8")
                        try:
                            xyz, r_energy = _relax(xyz, (extra or []) + att_pins, restrain=True,
                                                   donors=donors)
                        except optimize.XtbNotFound:
                            raise
                        except optimize.XtbError:
                            continue
                        r_drifted, r_intruders = _co_ligand_drift(xyz, *all_args)
                        if not (r_drifted or r_intruders or _sigma_aryl_slipped(
                                xyz, relax_bonds, metal_index, sigma_aryl)):
                            fixed = (label, r_energy)
                            break
                    if fixed:
                        energy = fixed[1]
                        new_bonds, broken_bonds = _new_or_broken_bonds(relax_bonds, xyz, metal_index)
                        iso_warnings.append(
                            f"donor drift: the unrestrained σ-aryl relax let "
                            f"{_plural(len(drifted), 'donor')} drift off / "
                            f"{_plural(len(intruders), 'atom')} take a site; "
                            f"re-relaxed with {fixed[0]} restrained (every donor bound, aryl σ).")
                    else:
                        Path(xyz).write_text(first_text, encoding="utf-8")
                        energy = first_energy
                        iso_warnings.append(
                            f"donor drift: {_plural(len(drifted), 'donor')} drifted off / "
                            f"{_plural(len(intruders), 'atom')} took a site in the unrestrained σ-aryl "
                            f"relax; restrained re-relaxes did not fix it (flagged).")
            if _nondonor_on_metal(xyz, metal_index, donor_indices):
                connectivity_ok = False
                iso_warnings.append(
                    "xtb relaxation collapsed a ligand atom onto the metal centre (flagged).")
            unbound = _unbound_donors(xyz, metal_index, donor_indices, complex.metal.symbol,
                                      complex.metal.oxidation_state, complex.coordination_number)
            if unbound:
                connectivity_ok = False
                if not any(w.startswith("donor drift") for w in iso_warnings):
                    shown = ", ".join(f"{el}{d} {r:.2f} Å (ref {ref:.2f})"
                                      for d, el, r, ref in unbound[:4])
                    iso_warnings.append(
                        f"{_plural(len(unbound), 'donor')} not bonded to the metal after relaxation "
                        f"({shown}{', ...' if len(unbound) > 4 else ''}; > {_CO_LIGAND_DRIFT}x "
                        f"the M–L reference) (flagged).")
            if new_bonds or broken_bonds:
                connectivity_ok = False
                parts = []
                if new_bonds:
                    shown = ", ".join(lbl for *_, lbl in new_bonds[:4])
                    parts.append(f"{_plural(len(new_bonds), 'new bond')} formed ({shown}"
                                 f"{', ...' if len(new_bonds) > 4 else ''})")
                if broken_bonds:
                    shown = ", ".join(lbl for *_, lbl in broken_bonds[:4])
                    parts.append(f"{_plural(len(broken_bonds), 'assembled bond')} broke ({shown}"
                                 f"{', ...' if len(broken_bonds) > 4 else ''})")
                iso_warnings.append(
                    "xtb relaxation changed the molecular connectivity vs the assembled "
                    "graph: " + "; ".join(parts)
                    + " (flagged; likely a ligand fusion or collapse)."
                )
        # Extra formats (.mol/.pdb) from the assembled bonds + the final (relaxed) coordinates.
        # xyz is already on disk; this is a no-op unless more formats were requested.
        extra_paths = [str(p) for p in export.write_formats(constructed, xyz, formats)]
        results.append(BuildResult(
            complex, iso_label, str(xyz), extra_paths, charge, uhf, iso_warnings,
            total_energy=energy, metal_index=metal_index, donor_indices=donor_indices,
            connectivity_ok=connectivity_ok,
        ))
    _rank_by_energy(results)
    return results


def _interligand_donor_fusions(new_bonds, comp, donor_set):
    """From :func:`_new_or_broken_bonds`'s ``new`` list, keep only the FUSIONS worth undoing: a bond
    xtb forged between two DONOR atoms of DIFFERENT ligands -- two cis carbonyls making a C-C bond
    (BOLCIP, REPPIL), an oxo dropping onto a thiolate (HODJUF), an iodide onto an amide N (YIVLEX).
    A new bond inside one ligand, or one touching a non-donor (BATKOX's backbone alkyne-into-phenyl),
    is not an anti-fusion target -- it stays with the plain connectivity flag. Returns ``[(i, j)]``.

    Detecting a fusion from the RESULT (a real new bond) instead of guessing pre-xtb is what makes
    the re-relax self-selecting: it fires only where a fusion actually happened, whatever the donor
    type or how far apart the pair started, and never on a sphere that relaxed clean."""
    out = []
    for i, j, _ in new_bonds:
        if (i in donor_set and j in donor_set and 0 <= comp[i] and comp[j] >= 0
                and comp[i] != comp[j]):
            out.append((i, j))
    return out


def _oxo_fusions(new_bonds, comp, oxo_donors):
    """From :func:`_new_or_broken_bonds`'s ``new`` list, bonds where a terminal oxo/nitrido bonded to
    an atom on ANOTHER ligand -- GFN2 deoxygenation of a metal oxo: oxo -> phosphine/thiolate (a
    donor), OR oxo -> a backbone/carbonyl CARBON, which :func:`_interligand_donor_fusions` misses
    because the carbon is not a donor (seen on DAJWIX/JOTYUM). ``oxo_donors`` is the terminal
    oxo/nitrido set. Returns ``[(i, j)]`` for the same strong-floor re-relax."""
    out = []
    for i, j, _ in new_bonds:
        if ((i in oxo_donors or j in oxo_donors)
                and comp[i] >= 0 and comp[j] >= 0 and comp[i] != comp[j]):
            out.append((i, j))
    return out


def _intraligand_diyl_fusions(new_bonds, comp, intended_bonds, donor_set, metal_index):
    """From :func:`_new_or_broken_bonds`'s ``new`` list, the INTRA-ligand fusions worth undoing: a
    bond xtb forged between two DONOR atoms of the SAME ligand that were >= 3 bonds apart in the
    assembled graph -- a chelating diyl whose bite collapsed. CPFPRH's perfluoro 1,4-bis-carbanion is
    a metallacyclopentadiene (Rh + C=C-C=C, the two carbanions 2.6 A apart, bite ~78 deg); with the
    M-C restraint pulling both termini toward ~2.1 A but nothing holding the bite open, xtb folds the
    two carbanions together (2.6 -> 1.5 A, bite 40 deg) into a spurious C-C bond. :func:`_interligand_
    donor_fusions` misses it (same ligand, comp[i] == comp[j]); this is its intra-ligand counterpart.

    The >= 3-bond guard is what keeps it targeted: two donors that START bonded (an eta2 alkene, a
    centroid cap's ring carbons) never appear here (their bond is assembled, not new), and a geminal
    1,2 pair (2 bonds apart) is left to the plain connectivity flag -- so a genuine small chelate ring
    is never pried open. Returns ``[(i, j)]``, fed to the same floor re-relax as inter-ligand fusions.
    """
    adj: dict[int, set[int]] = {}
    for a, b in intended_bonds:
        if a == metal_index or b == metal_index:
            continue
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)

    def far(i: int, j: int, cutoff: int = 3) -> bool:
        """True if the assembled-graph distance between i and j is >= cutoff (or disconnected)."""
        seen, frontier = {i}, {i}
        for _ in range(cutoff - 1):
            nxt = set().union(*(adj.get(x, set()) for x in frontier)) - seen if frontier else set()
            if j in nxt:
                return False
            seen |= nxt
            frontier = nxt
        return True

    return [(i, j) for i, j, _ in new_bonds
            if i in donor_set and j in donor_set and comp[i] >= 0
            and comp[i] == comp[j] and far(i, j)]


def _preemptive_oxo_floors(pre_atoms, oxo_donors, comp, metal_index, capture: float = 4.0):
    """Distance floors ``[(i, j, target)]`` keeping each terminal oxo/nitrido donor off every nearby
    heavy atom on ANOTHER ligand, applied from the FIRST relax (with a stiff force constant) so xtb
    never forges a deoxygenation bond. GFN2 favours phosphine/thiolate deoxygenation of a metal oxo
    AND migration of the oxo onto a backbone/carbonyl **carbon** (an oxo->C fusion seen on DAJWIX/
    JOTYUM), so the floor targets all cross-ligand heavy atoms, not just donors. The reactive
    anti-fusion path only fires AFTER a fusion and shares the soft global FC, which the deoxygenation
    drive can overpower; flooring pre-emptively at high FC prevents it. Target = the non-bonded
    covalent-radii distance (or the current separation if already larger, so a legitimate close
    contact is never pulled tighter). Only atoms within ``capture`` A on a DIFFERENT ligand component
    are floored, so distant atoms add no spurious restraint."""
    out = []
    for i in oxo_donors:
        ci = comp[i]
        for j in range(len(pre_atoms)):
            if j == metal_index or j == i or pre_atoms[j][0] == "H":
                continue
            cj = comp[j]
            if cj < 0 or cj == ci:  # skip the metal (comp -1) and the oxo's own ligand
                continue
            d = math.dist(pre_atoms[i][1], pre_atoms[j][1])
            if d <= capture:
                ri = optimize._cov_radius(pre_atoms[i][0]) or 0.7
                rj = optimize._cov_radius(pre_atoms[j][0]) or 0.7
                out.append((i, j, max(d, (ri + rj) * 1.5)))
    return out


def _fusion_floors(pre_atoms, fused_pairs):
    """Distance floors ``[(i, j, target)]`` holding each fused donor pair at its ASSEMBLED separation
    (or a clearly non-bonded covalent-radii distance, whichever is larger), so a re-relax keeps the
    pair apart instead of forging the bond again. ``pre_atoms`` is the assembled (pre-relax) xyz."""
    out = []
    for i, j in fused_pairs:
        ri = optimize._cov_radius(pre_atoms[i][0]) or 0.7
        rj = optimize._cov_radius(pre_atoms[j][0]) or 0.7
        out.append((i, j, max(math.dist(pre_atoms[i][1], pre_atoms[j][1]), (ri + rj) * 1.5)))
    return out


def _uff_relax_fallback(xyz, base, constructed, metal_index, donor_indices,
                        oxidation_state, coordination_number, warnings) -> bool:
    """Last-resort relaxation when every xtb tier failed: a metal-excluded UFF force-field
    relax (donors held at their CSD-reference M-L bond lengths, ligand shell relaxed and
    de-clashed) via :func:`optimize.ff_declash`. This is MetalloGen's robust force-field path —
    UFF is parameterised across the whole periodic table, so it produces a physically sensible
    geometry for the metals xtb's GFN2 SCF / ANC optimiser diverges on (Y, Sc, lanthanides),
    where the only alternative is shipping the raw assembly. Starts from ``base`` (the assembled
    geometry, whose connectivity matches ``constructed``) and overwrites ``xyz``. Returns True
    if a UFF geometry was produced, False if it could not run (no topology)."""
    if constructed is None:
        return False
    shutil.copyfile(base, xyz)
    optimize.ff_declash(  # never raises; leaves the geometry untouched if UFF can't run
        xyz, constructed, metal_index, donor_indices,
        oxidation_state=oxidation_state, coordination_number=coordination_number,
    )
    warnings.append("xtb relaxation failed on this metal; fell back to a UFF force-field "
                    "relaxation (donors held at CSD M-L bond lengths, ligand shell de-clashed).")
    return True


# Smallest slice of the per-structure budget worth handing to another xtb tier: below
# this a stage cannot do useful work, so it is skipped rather than started to die.
_MIN_STAGE_S = 5

# Appended to a fallback warning when the FALLBACK was caused by the time budget running
# out (not an xtb crash). The web app caps the budget, so a large/crowded complex can be
# handed back a pre-relax geometry that simply needed more time; point the user at the
# local build, which accepts a longer limit.
_TIMEOUT_LOCAL_HINT = (
    " Large or crowded complexes can need more time to converge than the web app allows; "
    "for a fully xtb-optimised geometry, run MeCoBi locally (the command-line / Python "
    "build accepts a longer optimisation time limit)."
)


def _relax_tiered(
    xyz, *, charge, uhf, output_dir, xtb_bin, metal_symbol,
    coordination_number, metal_index, donor_indices, warnings, bond_pairs=None,
    free_donors=None, angle_constraints=None, dihedral_constraints=None, oxidation_state=None,
    timeout_s: int = 600, restrain: bool = True, two_stage: bool = True,
    preopt_level: str = "loose", revert_on_bond_change: bool = False,
    constructed=None, uff_fallback: bool = True, extra_distances=None,
    strong_distances=None, strong_fc: float = 5.0, reference_metal=None,
) -> "tuple[Path, float | None]":
    """Relax with xtb, degrading gracefully so a hard case never fails the build.

    Two-stage relaxation (``two_stage=True``, default), mirroring Architector's
    UFF→xtb: a **GFN-FF pre-relax** first relieves inter-/intra-ligand clashes gently
    (GFN-FF's energy is steric-dominated, so it de-clashes without the SCF fragility of
    GFN2 or its tendency to fuse two atoms that start close), then **GFN2** refines from
    that clash-free start.

    xtb is deliberately left FREE to change the connectivity: a bad initial placement (a
    donor seated too far, a mis-oriented bulky ligand) is often only repaired by xtb
    re-forming the correct bonds, so we ship GFN2's result rather than reverting to the
    assembled geometry. Any connectivity change is still detected and flagged by the
    caller (``connectivity_ok``). ``revert_on_bond_change=True`` restores the old guard —
    revert a new/broken bond (or a ligand atom collapsed onto the metal) to the last
    topology-correct structure — kept only for A/B measurement, off by default.

    ``timeout_s`` is a wall-clock budget for the whole structure, shared by every tier
    (the legacy single path included), not a fresh allowance per xtb call: a tier that
    would start with less than ``_MIN_STAGE_S`` left is skipped instead.

    ``two_stage=False`` restores the legacy single path (GFN2, GFN-FF only as a crash
    fallback). The coordination sphere is restrained either way so labile donors can't
    drift off (invariant 4 charge/uhf still apply). A missing xtb executable is re-raised
    (a setup problem). Returns ``(xyz_path, energy_or_None)`` — energy is None only for a
    dissociated/failed GFN2 (so a wreck never wins isomer ranking).
    """
    xyz = Path(xyz)
    # ``timeout_s`` is the budget for THIS STRUCTURE, not for each xtb invocation. The
    # tiered path calls xtb up to three times (GFN-FF pre-relax, GFN2, GFN2 retry), so a
    # per-call timeout let one structure spend 3x the caller's allowance -- a 300 s budget
    # spent 609 s on a 195-atom Re complex, and behind a reverse proxy a synchronous build
    # 502s long before that returns. Every stage now gets only what is LEFT.
    deadline = time.monotonic() + timeout_s if timeout_s else None

    def _budget_left() -> "int | None":
        return None if deadline is None else int(deadline - time.monotonic())

    # η-sandwiches relax free of the metal-donor restraint; keep only the ligand-internal
    # bonds (drop any bond touching the metal) so the cap can settle to symmetric η5.
    relax_bonds = bond_pairs
    if not restrain and bond_pairs is not None:
        relax_bonds = [(a, b) for a, b in bond_pairs if a != metal_index and b != metal_index]

    def _run(gfn, level, energy_out):
        left = _budget_left()
        if left is not None and left < _MIN_STAGE_S:
            raise optimize.XtbTimeout(
                f"xtb budget of {timeout_s}s exhausted before the GFN{gfn} stage on {xyz.name}")
        return optimize.relax_with_xtb(
            xyz, charge=charge, uhf=uhf, workdir=output_dir, xtb_bin=xtb_bin, gfn=gfn,
            opt_level=level, timeout_s=left, restrain_donors=restrain,
            metal_symbol=metal_symbol, coordination_number=coordination_number,
            metal_index=metal_index, donor_indices=donor_indices, free_donors=free_donors,
            angle_constraints=angle_constraints, dihedral_constraints=dihedral_constraints,
            extra_distances=extra_distances,
            strong_distances=strong_distances, strong_fc=strong_fc,
            oxidation_state=oxidation_state,
            bond_pairs=relax_bonds, warnings=warnings, energy_out=energy_out,
            reference_metal=reference_metal,
        )

    def _topology_ok() -> bool:
        if _nondonor_on_metal(xyz, metal_index, donor_indices):
            return False  # a ligand atom collapsed onto the metal (bond guard misses this)
        if not bond_pairs:
            return True  # nothing else to check against (no assembled graph)
        new, broken = _new_or_broken_bonds(bond_pairs, xyz, metal_index)
        return not (new or broken)

    if not two_stage:  # legacy single-path behaviour
        last_err = None
        for gfn in (2, "ff"):
            energy_out: dict = {}
            try:
                out = _run(gfn, "normal", energy_out)
            except optimize.XtbNotFound:
                raise
            except optimize.XtbError as exc:
                last_err = exc
                continue
            if gfn != 2:
                warnings.append("GFN2 relaxation failed; used the more robust GFN-FF instead.")
                return out, None
            return out, (None if energy_out.get("dissociated") else energy_out.get("energy_eh"))
        head = str(last_err).splitlines()[0] if last_err else "unknown error"
        if uff_fallback and _uff_relax_fallback(
                xyz, xyz, constructed, metal_index, donor_indices,
                oxidation_state, coordination_number, warnings):
            return xyz, None
        warnings.append(f"xtb relaxation failed ({head}); kept the assembled geometry.")
        return xyz, None

    # --- two-stage: GFN-FF pre-relax -> GFN2 ---
    assembled = xyz.with_name(xyz.stem + "_assembled.xyz")  # crash-only fallback
    shutil.copyfile(xyz, assembled)
    ff_snap = None

    def _cleanup():
        for p in (assembled, ff_snap):
            if p is not None:
                Path(p).unlink(missing_ok=True)

    try:  # Stage 1 -- GFN-FF de-clash (relax_with_xtb overwrites xyz in place)
        _run("ff", preopt_level, {})
        ff_snap = xyz.with_name(xyz.stem + "_gfnff.xyz")
        shutil.copyfile(xyz, ff_snap)
        ff_ok = _topology_ok()
    except optimize.XtbNotFound:
        _cleanup(); raise
    except optimize.XtbError:
        shutil.copyfile(assembled, xyz)  # FF failed -> GFN2 starts from the assembled geometry
        ff_ok = False

    energy_out = {}
    try:  # Stage 2 -- GFN2 refine from the (clash-relieved) geometry
        _run(2, "normal", energy_out)
    except optimize.XtbNotFound:
        _cleanup(); raise
    except optimize.XtbError as exc:
        # The GFN-FF pre-relax can push a crowded complex into a geometry where GFN2's SCF
        # won't converge, even though GFN2 converges fine from the clean assembly (seen on a
        # Y CN9 cage: GFN2-on-assembled converges in 67 SCC iters, GFN2-on-GFN-FF aborts).
        # Retry GFN2 once from the assembled geometry before giving up on relaxation.
        # A TIMEOUT is not that failure: the retry would restart the same slow system on an
        # already-spent budget and time out again, which is exactly how a 300 s allowance
        # became 609 s of wall clock and still returned the assembled geometry. Skip it.
        timed_out = isinstance(exc, optimize.XtbTimeout)
        retried = False
        if not timed_out:
            shutil.copyfile(assembled, xyz)
            energy_out = {}
            try:
                _run(2, "normal", energy_out)
                warnings.append("GFN2 did not converge from the GFN-FF pre-relax; re-relaxed "
                                "from the assembled geometry instead.")
                retried = True
            except optimize.XtbError:
                retried = False
        if not retried:
            if ff_snap is not None and ff_ok:
                shutil.copyfile(ff_snap, xyz)
                if timed_out:
                    warnings.append(
                        f"xtb (GFN2) did not finish within the {timeout_s}s time limit; kept the "
                        "GFN-FF pre-relaxed structure, which is a force-field geometry rather than "
                        "a fully xtb-optimised one." + _TIMEOUT_LOCAL_HINT)
                else:
                    warnings.append(
                        "GFN2 relaxation failed; kept the GFN-FF pre-relaxed structure.")
            elif uff_fallback and _uff_relax_fallback(
                    xyz, assembled, constructed, metal_index, donor_indices,
                    oxidation_state, coordination_number, warnings):
                pass  # UFF force-field fallback (warning added inside)
            elif timed_out:
                shutil.copyfile(assembled, xyz)
                warnings.append(
                    f"xtb did not finish within the {timeout_s}s time limit; kept the assembled "
                    "(pre-relax) geometry." + _TIMEOUT_LOCAL_HINT)
            else:
                shutil.copyfile(assembled, xyz)
                warnings.append(f"xtb relaxation failed ({str(exc).splitlines()[0]}); "
                                "kept the assembled geometry.")
            _cleanup()
            return xyz, None

    # Default: keep GFN2's geometry even if the connectivity changed -- that change is
    # often the repair of a bad initial placement, and it is flagged (not reverted) by the
    # caller. energy is withheld for a dissociated result so it can't win isomer ranking.
    if not revert_on_bond_change or _topology_ok():
        energy = None if energy_out.get("dissociated") else energy_out.get("energy_eh")
        _cleanup()
        return xyz, energy
    # Opt-in guard (A/B only): GFN2 fused/collapsed -> revert to the last topology-correct structure.
    if ff_snap is not None and ff_ok:
        shutil.copyfile(ff_snap, xyz)
        warnings.append("GFN2 relaxation changed the molecular connectivity (clash/collapse); "
                        "reverted to the GFN-FF pre-relaxed structure.")
    else:
        shutil.copyfile(assembled, xyz)
        warnings.append("both GFN-FF and GFN2 changed the connectivity; reverted to the "
                        "assembled (pre-relax) geometry.")
    _cleanup()
    return xyz, None


def _rank_by_energy(results: "list[BuildResult]") -> None:
    """Order isomers lowest-energy first and fill relative energies (in place).

    Only isomers with a comparable GFN energy participate: a numeric
    ``total_energy`` and ``connectivity_ok``. A structure whose relaxation fused,
    fragmented, collapsed or unbound something is a different molecule, so its
    energy is not on the same surface: it never sets the baseline, is never
    ``is_lowest_energy`` and keeps ``relative_energy_kcal=None`` (its raw
    ``total_energy`` stays, for diagnosis).

    Order: comparable isomers by energy, then valid isomers without an energy
    (relaxation off, energy unreadable), then the flagged ones; build order is
    kept within the last two groups. Relative energies are only filled when at
    least two isomers are comparable.
    """
    def comparable(r):
        return r.connectivity_ok and r.total_energy is not None

    results.sort(key=lambda r: (0, r.total_energy) if comparable(r)
                 else (1 if r.connectivity_ok else 2, 0.0))
    scored = [r for r in results if comparable(r)]
    if len(scored) < 2:
        return
    lowest = scored[0].total_energy
    for r in scored:
        r.relative_energy_kcal = (r.total_energy - lowest) * optimize.HARTREE_TO_KCAL
        r.is_lowest_energy = r.total_energy == lowest
