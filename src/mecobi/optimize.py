"""Structure optimisation: MCHammer -> xtb.

1. MCHammer runs as the stk construction optimizer during assembly (see
   :mod:`mecobi.assembly`).
2. xtb — a quick GFN-xtb geometry relaxation. The core **calls xtb itself**; it
   is never a manual step. xtb MUST be invoked with the correct total charge and
   ``--uhf`` derived from spin (invariant 4).

xtb is a compiled binary; every run happens in an **isolated working directory**
with a **timeout**. Heavier sandboxing (CPU/memory
caps) is added by the web layer, but the same code path serves local and web
(invariant 2) — hence the ``workdir`` / ``timeout_s`` parameters here.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path


def _resolve_xtb_threads(threads: int | None) -> int:
    """Number of OpenMP threads to give one xtb run.

    Explicit ``threads`` wins; otherwise ``MECOBI_XTB_THREADS`` (so a deployment
    can request e.g. 8 cores per optimisation without any code change); else 1
    (xtb's own default is all cores, which oversubscribes when several jobs run
    at once — an explicit 1 keeps a serial batch predictable)."""
    if threads is None:
        try:
            threads = int(os.environ.get("MECOBI_XTB_THREADS", "0"))
        except ValueError:
            threads = 0
    return max(1, threads) if threads and threads > 0 else 1

# 1 Hartree in kcal/mol, for reporting relative isomer energies.
HARTREE_TO_KCAL = 627.5094740631

# A metal-donor bond longer than this (Angstrom) is treated as a dissociated
# donor rather than a real (if weak) coordinate bond. Set above the longest real
# M-donor bonds (weak M-N/M-halide on large metals reach ~2.7-2.9 A) so a merely
# long-but-present bond in a strained isomer (e.g. a crowded cis) keeps its
# relaxed geometry instead of falling back to the raw assembled one; a genuine
# dissociation runs well past 3.5 A.
DISSOCIATION_THRESHOLD_A = 3.1
# A donor counts as dissociated only when its bond exceeds BOTH the fixed floor above AND
# this multiple of the metal-donor REFERENCE length. Large electropositive metals (Y, the
# lanthanides) have genuinely long M-L bonds (~2.4-2.6 A) that xtb stretches past the 3.1 A
# floor without the donor actually leaving; scaling by the reference (Y-L ref ~2.4 ->
# threshold ~3.4) stops those false reverts, while small metals (ref ~2.0 -> 2.8 < 3.1) keep
# the 3.1 A floor unchanged.
DISSOCIATION_REFERENCE_FACTOR = 1.4
# How far OUTWARD (Angstrom) a donor must move during the relax, relative to where the
# ASSEMBLY put it, before the move counts as xtb pushing it off. A donor the assembly
# already stranded beyond the threshold (a bulky pincer seated at ~3.9 A against a ~2.44 A
# reference) that xtb pulled INWARD has not dissociated -- the inward pull merely did not
# finish inside the budget, and the relaxed geometry is strictly better than the assembled
# one, so reverting would throw the improvement away. The tolerance keeps sub-0.05 A
# numerical drift from reading as "pushed out".
DISSOCIATION_WORSENED_A = 0.05

# Cordero covalent radii (Angstrom), for a chemically sensible metal-donor
# restraint target = r(metal) + r(donor). Restraining to the *assembled* distance
# alone locks in the occasional gross MCHammer mis-placement of a bulky donor
# (e.g. a PCy3 phosphorus stranded at 3.4 A); a covalent target pulls such a donor
# back to a real bond length while leaving well-placed donors untouched.
_COV_RADIUS = {
    "H": 0.31, "C": 0.76, "N": 0.71, "O": 0.66, "F": 0.57, "P": 1.07, "S": 1.05,
    "Cl": 1.02, "As": 1.19, "Se": 1.20, "Br": 1.20, "I": 1.39, "B": 0.84,
    # metals we build
    "Au": 1.36, "Cu": 1.32, "Pt": 1.36, "Ru": 1.46, "Ir": 1.41, "Mo": 1.54,
    "Ag": 1.45, "Pd": 1.39, "Ni": 1.24, "Fe": 1.32, "Zn": 1.22, "Co": 1.26,
    "W": 1.62, "Zr": 1.75, "Mn": 1.39, "Cr": 1.39, "V": 1.53, "Ti": 1.60,
    "Re": 1.51, "Os": 1.44, "Rh": 1.42, "Cd": 1.44, "Hg": 1.32,
}
# Assembled distances up to this multiple of the covalent target are trusted as-is
# (real bonds vary); beyond it the assembly is assumed to have mis-placed the donor
# and the covalent target is restrained instead.
_TRUST_ASSEMBLED_FACTOR = 1.3
# The default 1.3x is calibrated for the weak, long dative bonds of large late/heavy
# metals (a Ru-N or Pt-N reaching 2.7-2.9 A is real). Small, high-oxidation-state
# early transition metals form SHORT M-L bonds with little stretch, so 1.3x trusts
# absurdly long assembled distances there (V-O target 2.19 A -> 2.85 A ceiling, vs a
# real V-O of ~1.6-2.0 A), pinning a mis-placed donor at its stranded distance
# instead of pulling it to a bond. Tighten the factor for those metals; every other
# metal keeps the calibrated 1.3x (so the validated late/heavy-metal batch is
# unchanged).
_TRUST_FACTOR_BY_METAL = {
    "V": 1.12, "Ti": 1.12,
    "Cr": 1.15, "Mn": 1.15,
    "Mo": 1.15, "W": 1.15, "Re": 1.15,
}


def _trust_factor(metal_el: str) -> float:
    """Trust multiplier for ``metal_el``: a tightened value for short-bond early
    transition metals, else the default :data:`_TRUST_ASSEMBLED_FACTOR`."""
    return _TRUST_FACTOR_BY_METAL.get(metal_el, _TRUST_ASSEMBLED_FACTOR)


def _cov_radius(el: str) -> float | None:
    """Covalent radius (A): the local Cordero table first, else RDKit's periodic
    table. The RDKit fallback matters for the broader periodic table (Hf, Ta, Nb,
    In, Ga, Sn, lanthanides, ...): without it these metals fell through to "trust
    the assembly", which left weak donors that MCHammer stranded on a large centre
    (e.g. a thioether S 6 A off a Hf(IV)) un-restrained and free for xtb to eject."""
    if el in _COV_RADIUS:
        return _COV_RADIUS[el]
    from rdkit.Chem import GetPeriodicTable

    try:
        r = GetPeriodicTable().GetRcovalent(el)
        return r if r and r > 0 else None
    except Exception:
        return None


# --- CSD-mined metal-donor bond-length reference -----------------------------
# A table of experimental M-L averages mined from the CSD (see
# experiments/benchmark and tmp_cifreview_fixed/mine_bond_lengths.py), keyed
# hierarchically (metal|OS|donor|CN -> metal|OS|donor -> metal|donor). Restraining
# to these removes the ~0.13 A systematic elongation the covalent-radius target
# leaves (validated A/B: median M-L RMSD 0.21 -> 0.09 A). Shipped as package data;
# MECOBI_ML_REFERENCE overrides the path (e.g. a freshly mined table).
_ML_TABLE = None
_ML_LOADED = False
_ML_NMIN = 8  # min samples in a bin before its mean is trusted


def _ml_reference_path() -> Path:
    override = os.environ.get("MECOBI_ML_REFERENCE")
    return Path(override) if override else Path(__file__).parent / "data" / "ml_reference.json"


def _load_ml_table():
    global _ML_TABLE, _ML_LOADED
    if not _ML_LOADED:
        _ML_LOADED = True
        p = _ml_reference_path()
        try:
            _ML_TABLE = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        except (OSError, ValueError):
            _ML_TABLE = None
    return _ML_TABLE


SP_CARBON = "C_sp"   # donor class of a carbonyl / cyanide / isocyanide carbon (see _donor_key)
ETA_CARBON = "C_eta"  # donor class of a hapto carbon: Cp / arene / alkene / allyl (see _donor_key)


def _ml_target(metal_el: str, ox, donor_el: str, cn) -> float | None:
    """Most specific CSD M-L average with >= _ML_NMIN samples, else None. ``donor_el`` may be the
    ``C_sp`` or ``C_eta`` class; where that has no usable bin the plain ``C`` bins are consulted
    (a table mined before the class existed keeps those carbons under ``C``)."""
    tab = _load_ml_table()
    if not tab:
        return None
    oxs = "" if ox is None else str(ox)
    for el in ((donor_el, "C") if donor_el in (SP_CARBON, ETA_CARBON) else (donor_el,)):
        for sub, key in (("metal_os_donor_cn", f"{metal_el}|{oxs}|{el}|{cn}"),
                         ("metal_os_donor", f"{metal_el}|{oxs}|{el}"),
                         ("metal_donor", f"{metal_el}|{el}")):
            v = tab.get(sub, {}).get(key)
            if v and v.get("n", 0) >= _ML_NMIN and v.get("mean") is not None:
                return float(v["mean"])
    return None


_SP_PARTNER_MAX = 1.30   # A: C#O 1.13-1.16, C#N 1.15-1.18; a C=O / C=N double bond is >= 1.20
                         # but its carbon has a second neighbour, so it never qualifies
_SP_ANGLE_MIN = 135.0    # deg: M-C-X of an sp donor is near linear, but a crowded pre-relax
                         # sphere bends it to ~140 (IYOQES); an acyl / iminoacyl is 120-130


def _donor_key(atoms, donor_index: int, metal_index: int, donors=None) -> str:
    """The donor's key in the M-L reference: its element, ``C_eta`` for a hapto carbon, or
    ``C_sp`` for an sp carbon.

    A HAPTO carbon is a carbon donor covalently bonded to a fellow donor (``donors``: the
    complex's donor atom indices; without them no carbon is classed as hapto): the ring carbons
    of a Cp or an arene, the two carbons of a side-on alkene or alkyne, an allyl. They sit
    0.15-0.3 A farther from the metal than a sigma carbon of the same metal and oxidation state
    (Ti(IV): Cp 2.37 A, alkyl 2.1 A), so each kind needs its own reference.

    An sp carbon is a C
    whose ONLY substituent is an N or O within 1.30 A, with M-C-X near linear (carbonyl, cyanide,
    isocyanide). The table's ``C`` bins average those with Cp / arene / alkyl / aryl carbons
    (Fe(0) CN5: 2.03 A, against a real Fe-CO of 1.78 A), which held every M-CO ~0.13 A too long.

    Atoms that are themselves bonded to the metal are never counted as the carbon's substituents:
    in a crowded or still-crushed pre-relax sphere a cis donor sits at bonding distance from the
    carbonyl carbon (DILZED, Mo CN7: an iodide 2.11 A away -- a real C-I bond is 2.14 A), so no
    distance threshold separates the two. The linearity test keeps out the one case that rule
    could let in, a metallacyclic acyl whose other substituent is a donor.
    ``atoms`` is ``[(element, (x, y, z)), ...]``; neighbours are geometric."""
    el, p = atoms[donor_index]
    if el != "C":
        return el
    for j in donors or ():
        if j not in (donor_index, metal_index) and j < len(atoms):
            e, q = atoms[j]
            if math.dist(p, q) < 1.15 * (0.76 + (_cov_radius(e) or 0.75)):
                return ETA_CARBON
    m_el, mp = atoms[metal_index]
    r_m = _cov_radius(m_el) or 1.4
    partners = []
    for i, (e, q) in enumerate(atoms):
        if i in (donor_index, metal_index):
            continue
        r_e = _cov_radius(e) or 0.75
        d = math.dist(p, q)
        if d >= 1.15 * (0.76 + r_e):
            continue                      # not bonded to the carbon
        sp_partner = e in ("N", "O") and d < _SP_PARTNER_MAX
        if not sp_partner and math.dist(q, mp) < 1.15 * (r_m + r_e):
            continue                      # a donor of the metal, not a substituent
        # (the triple-bond partner itself is kept even when a compressed M-C-O puts its O inside
        # that radius; an eta2-acyl, whose O really is bonded, fails the linearity test below)
        partners.append((e, d, q))
    if len(partners) != 1 or partners[0][0] not in ("N", "O") or partners[0][1] >= _SP_PARTNER_MAX:
        return el
    q = partners[0][2]
    u = [mp[k] - p[k] for k in range(3)]
    v = [q[k] - p[k] for k in range(3)]
    nu, nv = math.sqrt(sum(c * c for c in u)), math.sqrt(sum(c * c for c in v))
    if nu < 1e-6 or nv < 1e-6:
        return el
    cos = max(-1.0, min(1.0, sum(a * b for a, b in zip(u, v)) / (nu * nv)))
    return SP_CARBON if math.degrees(math.acos(cos)) >= _SP_ANGLE_MIN else el


_SHORT_BOND_RATIO = 0.80  # below this x the reference, a donor is a short multiple bond or squeezed
# Donor elements that form genuine short M=X / M#X bonds (oxo, nitrido, imido, sulfido,
# alkylidene/alkylidyne, phosphinidene). Halides never do.
_MULTIPLE_BOND_DONORS = frozenset({"O", "N", "S", "Se", "Te", "C", "P"})


def _can_multiple_bond(atoms, donor_index: int, metal_index: int) -> bool:
    """True when a donor could carry a short M=X / M#X bond, so a short assembled M-X distance
    may be real: an O/N/S/Se/Te/C/P donor with at most one heavy-atom neighbour besides the
    metal (oxo, nitrido, imido N-R, sulfido, alkylidyne). An amido/amine/phosphine with two or
    more heavy neighbours, or any halide, at a short distance is a squeezed assembly, not a
    multiple bond: QEMTOR's Ti-N(SiMe3)C amido sat at 1.57 A (CSD 2.07) and was held there.
    ``atoms`` is ``[(element, (x, y, z)), ...]``; neighbours are geometric (1.15 x rcov sum)."""
    el, p = atoms[donor_index]
    if el not in _MULTIPLE_BOND_DONORS:
        return False
    r_d = _cov_radius(el) or 0.75
    heavy = 0
    for i, (e, q) in enumerate(atoms):
        if i in (donor_index, metal_index) or e == "H":
            continue
        if math.dist(p, q) < 1.15 * (r_d + (_cov_radius(e) or 0.75)):
            heavy += 1
            if heavy > 1:
                return False
    return True


def _restraint_reference(assembled_dist: float, metal_el: str, donor_el: str,
                         ox=None, cn=None, multiple_bond_ok: bool = True) -> float:
    """Distance to restrain a metal-donor pair to: the CSD-mined experimental
    average when available for this (metal, OS, donor, CN); else the assembled
    distance when chemically reasonable; else the covalent-radius target (pulls a
    grossly mis-placed / stranded donor back to a real bond length).

    A distance far below the reference is kept only when ``multiple_bond_ok`` (see
    :func:`_can_multiple_bond`); otherwise it is a squeezed donor and gets the reference."""
    csd = _ml_target(metal_el, ox, donor_el, cn)
    if csd is not None:
        # keep a genuine short multiple bond (terminal oxo/nitrido M=O, M#N) rather
        # than stretching it up to a dative single-bond average
        if multiple_bond_ok and assembled_dist < _SHORT_BOND_RATIO * csd:
            return assembled_dist
        return csd
    r_m = _cov_radius(metal_el)
    r_d = _cov_radius("C" if donor_el == SP_CARBON else donor_el)
    if r_m is None or r_d is None:
        return assembled_dist  # truly unknown element -> trust the assembly
    target = r_m + r_d
    if not multiple_bond_ok and assembled_dist < _SHORT_BOND_RATIO * target:
        return target
    return assembled_dist if assembled_dist <= _trust_factor(metal_el) * target else target


class XtbError(RuntimeError):
    """Raised when xtb fails, times out, or produces no optimised structure."""


class XtbNotFound(XtbError):
    """Raised specifically when the xtb executable is missing — a setup problem,
    distinct from xtb failing on a hard structure (so callers can propagate the
    'install xtb' signal instead of silently falling back)."""


class XtbTimeout(XtbError):
    """Raised when xtb exceeded its wall-clock budget, as distinct from failing.

    A convergence failure is worth retrying from a different starting geometry; a
    timeout is not -- the same system on the same budget simply times out again,
    spending the caller's whole allowance twice for nothing. Callers branch on this
    to skip a retry that cannot finish (see :func:`pipeline._relax_structure`)."""


def spin_to_uhf(n_unpaired: int) -> int:
    """xtb ``--uhf`` is the number of unpaired electrons (pass-through for clarity)."""
    return n_unpaired


def _read_xyz(path: Path) -> list[tuple[str, tuple[float, float, float]]]:
    """Minimal .xyz reader -> [(element, (x, y, z)), ...]."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    n = int(lines[0].strip())
    atoms = []
    for line in lines[2:2 + n]:
        p = line.split()
        atoms.append((p[0], (float(p[1]), float(p[2]), float(p[3]))))
    return atoms


# xtb writes the final energy on the .xyz comment line (" energy: -28.1 ...") and
# as "TOTAL ENERGY  -28.1 Eh" in stdout; try the comment first, fall back to stdout.
_XYZ_ENERGY_RE = re.compile(r"energy:\s*(-?\d+\.\d+)")
_TOTAL_ENERGY_RE = re.compile(r"TOTAL ENERGY\s+(-?\d+\.\d+)")


def _write_xyz(path: Path, atoms: list, comment: str = "") -> None:
    """Write ``[(element, (x, y, z)), ...]`` back to an .xyz."""
    lines = [str(len(atoms)), comment]
    lines += [f"{el} {x:.6f} {y:.6f} {z:.6f}" for el, (x, y, z) in atoms]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


# Metals whose GFN2 SCF / ANC optimiser diverges are RELAXED as an xtb-friendly surrogate of the
# SAME oxidation state's d-count, so --chrg/--uhf carry over unchanged, then the real symbol is
# restored. Y(III) d0 -> Sc(III) d0 by default. Env MECOBI_XTB_SURROGATE="Y:Sc,La:Sc" overrides.
_XTB_SURROGATE_DEFAULT = {"Y": "Sc"}


def xtb_surrogate(metal_symbol: "str | None") -> "str | None":
    """The xtb-optimisation surrogate for a metal whose GFN2 diverges (Y -> Sc by default), or
    None to relax the metal as itself. The surrogate MUST share the oxidation state's d-count so
    the complex's charge and unpaired-electron count are unchanged (Y³⁺ and Sc³⁺ are both d0)."""
    if not metal_symbol:
        return None
    table = dict(_XTB_SURROGATE_DEFAULT)
    raw = os.environ.get("MECOBI_XTB_SURROGATE", "").strip()
    if raw:
        try:
            table = {k.strip(): v.strip() for k, v in (p.split(":") for p in raw.split(","))}
        except ValueError:
            pass
    sur = table.get(metal_symbol)
    return sur if sur and sur != metal_symbol else None


def swap_metal_symbol(xyz_path, metal_index: int, new_symbol: str) -> None:
    """Rewrite the element of the atom at ``metal_index`` in an .xyz (coordinates untouched)."""
    atoms = _read_xyz(Path(xyz_path))
    if metal_index is None or metal_index >= len(atoms):
        return
    atoms[metal_index] = (new_symbol, atoms[metal_index][1])
    _write_xyz(Path(xyz_path), atoms)


def _components_excluding(bonds, n: int, metal_index: int) -> list[int]:
    """Connected-component id per atom over the covalent graph with the metal removed.

    Atoms in the same component belong to the same ligand; the metal gets its own id. Used to
    tell an *inter-ligand* contact (two ligands overlapping — the clash we relieve) from an
    intra-ligand one (a real bond)."""
    adj: dict[int, set] = {i: set() for i in range(n)}
    for u, v in bonds:
        if u == metal_index or v == metal_index:
            continue
        adj[u].add(v)
        adj[v].add(u)
    comp = [-1] * n
    c = 0
    for i in range(n):
        if i == metal_index or comp[i] != -1:
            continue
        stack, comp[i] = [i], c
        while stack:
            x = stack.pop()
            for y in adj[x]:
                if comp[y] == -1:
                    comp[y] = c
                    stack.append(y)
        c += 1
    return comp


def ff_declash(xyz_path, constructed, metal_index: int, donor_indices: list[int],
               oxidation_state: "int | None" = None, coordination_number: "int | None" = None,
               max_iters: int = 400, collapse_ratio: float = 0.55,
               fuse_ratio: float = 1.15, metal_clear: float = 1.8) -> Path:
    """Force-field de-clash of the ligand shell before xtb, so the QM step starts clash-free.

    Independent MeCoBi implementation of the metal-excluded ligand force-field cleanup used by
    MetalloGen (Lee et al.) and molSimplify (Ioannidis et al.) — same principle, own code:

      * build ONE RDKit molecule of every non-metal atom (bonds + orders from the stk topology)
        and UFF-minimise it with the **metal excluded**, so the field sees only ligand-internal
        and ligand-ligand forces — the inter-ligand van der Waals repulsion pushes overlapping
        ligands apart (a bulky phosphine's aryl swings off the metal; two stacked rings separate);
      * ``ignoreInterfragInteractions=False`` is essential — RDKit's default IGNORES forces
        between disconnected fragments, i.e. between different ligands, which is exactly the
        clash we need relieved;
      * **donor repositioning**: assembly with bulky ligands can push a donor out of bonding range
        (DIBWAM: three P donors stranded at ~3 A while a phosphine phenyl takes the coordination
        site). Each donor is first pulled along the metal→donor direction to a real M-L bond length
        — the same CSD/covalent reference the xtb restraint uses (:func:`_restraint_reference`), so
        a well-placed donor is left alone and a stranded one is corrected — then held there;
      * the **donor atoms are held fixed** (``AddFixedPoint``) so the coordination sphere set by
        assembly does not move and a labile donor (a phosphine, a halide) cannot drift off and
        dissociate — a soft tether let those escape;
      * **metal-centre clearance** (``metal_clear``): the excluded metal means nothing in the FF
        pushes a non-donor atom that sits ON the metal (a phosphine aryl folded over the centre —
        DIBWAM). AFTER minimising (nudging before is pointless — the metal-blind UFF folds it right
        back), any non-donor atom closer than ``metal_clear`` to the metal is pushed radially out
        to that distance as the final placement; xtb refines from there. Donors are untouched;
      * UFF cannot break or form covalent bonds, and the result is **accepted only if it did not
        push two ligands into contact** (an inter-ligand pair closer than ``collapse_ratio`` ×
        Σr_cov = collapse, or newly within ``fuse_ratio`` × Σr_cov = fusion); otherwise the
        assembled geometry is kept. This is the topology guard, done geometrically.

    Robust by construction: ``UpdatePropertyCache(strict=False)`` + ring perception replace a full
    sanitise (coordinated carbanions/odd valences no longer abort it). Overwrites ``xyz_path`` and
    returns it; never raises — any failure leaves the assembly untouched.
    """
    def _dbg(msg):
        if os.environ.get("MECOBI_FF_DEBUG"):
            print(f"[ff_declash] {Path(xyz_path).name}: {msg}", flush=True)

    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
        from rdkit.Geometry import Point3D
    except ImportError:
        _dbg("rdkit import failed"); return Path(xyz_path)
    xyz_path = Path(xyz_path)
    try:
        atoms = _read_xyz(xyz_path)
        n = len(atoms)
        stk_atoms = {a.get_id(): a for a in constructed.get_atoms()}
        bonds = [(b.get_atom1().get_id(), b.get_atom2().get_id()) for b in constructed.get_bonds()]
        comp = _components_excluding(bonds, n, metal_index)
        ids = [i for i in range(n) if i != metal_index]
        if len(ids) < 2:
            _dbg(f"only {len(ids)} non-metal atom(s), nothing to relax"); return xyz_path
        donor_set = {d for d in (donor_indices or []) if 0 <= d < n and d != metal_index}
        if len(ids) - len(donor_set) <= 0:
            # every non-metal atom is a fixed donor (all-monodentate single-atom ligands, e.g.
            # halides) -> no free DOF for UFF; skip (BFGS would flag a fully-constrained system).
            _dbg("all non-metal atoms are fixed donors; nothing to relax"); return xyz_path

        rank = {gid: k for k, gid in enumerate(ids)}
        rw = Chem.RWMol()
        for gid in ids:
            a = Chem.Atom(int(stk_atoms[gid].get_atomic_number()))
            try:
                a.SetFormalCharge(int(stk_atoms[gid].get_charge()))
            except Exception:  # noqa: BLE001  (stk atom without a charge -> neutral)
                pass
            rw.AddAtom(a)
        bt = {1: Chem.BondType.SINGLE, 2: Chem.BondType.DOUBLE,
              3: Chem.BondType.TRIPLE, 4: Chem.BondType.QUADRUPLE}
        for b in constructed.get_bonds():
            u, v = b.get_atom1().get_id(), b.get_atom2().get_id()
            if u == metal_index or v == metal_index:
                continue
            rw.AddBond(rank[u], rank[v], bt.get(int(b.get_order()), Chem.BondType.SINGLE))
        mol = rw.GetMol()
        # Robust typing without a full sanitise (which aborts on coordinated carbanions / odd
        # valences): compute valences non-strictly, then assign only what UFF needs -- rings,
        # aromaticity, hybridisation -- skipping the valence-property and kekulise checks.
        mol.UpdatePropertyCache(strict=False)
        Chem.SanitizeMol(mol, sanitizeOps=(Chem.SanitizeFlags.SANITIZE_SYMMRINGS
                                           | Chem.SanitizeFlags.SANITIZE_SETAROMATICITY
                                           | Chem.SanitizeFlags.SANITIZE_SETCONJUGATION
                                           | Chem.SanitizeFlags.SANITIZE_SETHYBRIDIZATION),
                         catchErrors=True)
        mx, my, mz = atoms[metal_index][1]
        m_el = atoms[metal_index][0]
        start = [list(atoms[i][1]) for i in range(n)]

        # #3 donor repositioning: pull a stranded donor (bulky-ligand assembly leaves P/N pushed
        # out while a ring takes the site -- DIBWAM) to a real M-L bond length before fixing it.
        repositioned = 0
        for d in donor_set:
            vx, vy, vz = start[d][0] - mx, start[d][1] - my, start[d][2] - mz
            dist = math.sqrt(vx * vx + vy * vy + vz * vz)
            if dist < 1e-6:
                continue
            target = _restraint_reference(dist, m_el,
                                          _donor_key(atoms, d, metal_index, donor_set),
                                          ox=oxidation_state, cn=coordination_number,
                                          multiple_bond_ok=_can_multiple_bond(atoms, d, metal_index))
            if abs(target - dist) > 0.15:  # mis-placed -> move to the reference bond length
                repositioned += 1
                s = target / dist
                start[d] = [mx + vx * s, my + vy * s, mz + vz * s]

        conf = Chem.Conformer(mol.GetNumAtoms())
        for gid in ids:
            x, y, z = start[gid]
            conf.SetAtomPosition(rank[gid], Point3D(x, y, z))
        mol.AddConformer(conf, assignId=True)

        # inter-ligand contact score at a set of positions: (collapsed pairs, fused-close pairs)
        def _contacts(pos):
            collapse = fuse = 0
            for a in range(len(ids)):
                ia = ids[a]
                ra = _cov_radius(atoms[ia][0])
                if ra is None:
                    continue
                for b_ in range(a + 1, len(ids)):
                    ib = ids[b_]
                    if comp[ia] == comp[ib]:
                        continue  # same ligand -> a real bond/1,3 contact, not a clash
                    rb = _cov_radius(atoms[ib][0])
                    if rb is None:
                        continue
                    d = math.dist(pos[ia], pos[ib])
                    s = ra + rb
                    if d < collapse_ratio * s:
                        collapse += 1
                    elif d < fuse_ratio * s:
                        fuse += 1
            return collapse, fuse

        pos0 = [atoms[i][1] for i in range(n)]
        col0, fus0 = _contacts(pos0)

        ff = AllChem.UFFGetMoleculeForceField(mol, ignoreInterfragInteractions=False)
        if ff is None:
            _dbg("UFF returned None (unparameterised element/type)"); return xyz_path
        for d in donor_set:
            ff.AddFixedPoint(rank[d])  # hold donors at their coordination sites (no dissociation)
        ff.Initialize()
        ff.Minimize(maxIts=max_iters)

        relaxed = mol.GetConformer()
        newpos = list(pos0)
        for gid in ids:
            p = relaxed.GetAtomPosition(rank[gid])
            newpos[gid] = (p.x, p.y, p.z)

        # #2 metal-centre clearance -- AFTER UFF: the metal is excluded from the field, so nudging
        # before minimising is pointless (UFF, blind to the metal, folds a phenyl right back onto
        # the centre -- DIBWAM's C at 0.76 A). Push any non-donor atom within metal_clear of the
        # metal radially out as the final placement; xtb refines from there.
        nudged = 0
        for gid in ids:
            if gid in donor_set:
                continue
            vx, vy, vz = newpos[gid][0] - mx, newpos[gid][1] - my, newpos[gid][2] - mz
            d = math.sqrt(vx * vx + vy * vy + vz * vz)
            if d < metal_clear:
                nudged += 1
                if d > 1e-6:
                    s = metal_clear / d
                    newpos[gid] = (mx + vx * s, my + vy * s, mz + vz * s)
                else:
                    newpos[gid] = (mx + metal_clear, my, mz)
        moved = max(math.dist(atoms[gid][1], newpos[gid]) for gid in ids)
        col1, fus1 = _contacts(newpos)

        if col1 > col0 or fus1 > fus0:  # FF pushed ligands together -> keep the assembly
            _dbg(f"REVERT -- FF worsened inter-ligand contacts "
                 f"(collapse {col0}->{col1}, fuse {fus0}->{fus1})")
            return xyz_path
        for gid in ids:
            atoms[gid] = (atoms[gid][0], newpos[gid])
        _write_xyz(xyz_path, atoms, comment="ligand FF de-clash")
        _dbg(f"OK -- {len({comp[i] for i in ids})} ligands, max move {moved:.2f} A, "
             f"{repositioned} donor reposition(s), {nudged} off-metal nudge(s), "
             f"inter-ligand collapse {col0}->{col1} fuse {fus0}->{fus1}")
    except Exception as exc:  # noqa: BLE001  (never fail the build on a pre-opt; keep the assembly)
        _dbg(f"BAILED -- {type(exc).__name__}: {exc}")
        return Path(xyz_path)
    return xyz_path


def _rot_about(axis, theta):
    """Rodrigues rotation matrix for angle ``theta`` about a unit ``axis`` (numpy 3x3)."""
    import numpy as np

    x, y, z = axis
    c, s, C = math.cos(theta), math.sin(theta), 1.0 - math.cos(theta)
    return np.array([
        [c + x * x * C, x * y * C - z * s, x * z * C + y * s],
        [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
        [z * x * C - y * s, z * y * C + x * s, c + z * z * C],
    ])


def orient_monodentate_body_outward(xyz_path, constructed, metal_index: int, donor_indices: list[int],
                                    clearance: float = 0.15, min_body: int = 2) -> Path:
    """Keep the bonder atoms the CLOSEST atoms of each ligand to the metal. After assembly a ligand
    can fold so a BACKBONE atom (a bulky phosphine aryl, a chelate spacer) sits between the metal and
    its own bonder -- i.e. a non-donor atom ends up closer to the metal than the donor that is meant
    to coordinate. We measure the initial geometry and, for every ligand where a non-donor heavy
    atom is nearer the metal than the ligand's closest bonder (minus ``clearance``), rigidly rotate
    the ligand to swing its body away from the metal WITHOUT moving the bonders off their sites:

    * monodentate (1 donor): pivot on the donor and rotate the body centroid to point outward;
    * bidentate  (2 donors): rotate about the donor-donor axis (both donors lie on it, so they are
      fixed) so the body centroid swings to the far side of the metal.

    3+ donors are skipped: no rigid rotation keeps every donor on its site, and a translation would
    pull the bonders off the polyhedron. The move is kept only if it actually increases the closest
    non-donor distance AND does not swing the body into another ligand (more interpenetrating
    inter-ligand pairs, :func:`joint_embed.collapse_count`), else reverted, so it can never make a
    sphere worse: rotated about their P-P axes, ZIHHUT's two BINAPs went from 0 to 19 such pairs.
    The metal and all other ligands are untouched. Returns the count of ligands re-oriented;
    overwrites the xyz in place."""
    from collections import defaultdict

    import numpy as np

    from .joint_embed import collapse_count

    reoriented = 0
    try:
        atoms = _read_xyz(Path(xyz_path))
        n = len(atoms)
        if metal_index is None or not donor_indices or metal_index >= n:
            return 0
        bonds = [(b.get_atom1().get_id(), b.get_atom2().get_id()) for b in constructed.get_bonds()]
        comp = _components_excluding(bonds, n, metal_index)
        nbr: dict[int, set[int]] = defaultdict(set)
        for a, b in bonds:
            nbr[a].add(b)
            nbr[b].add(a)
        members: dict[int, list[int]] = defaultdict(list)
        for i in range(n):
            if comp[i] >= 0:
                members[comp[i]].append(i)
        P = np.array([a[1] for a in atoms], float)
        m = P[metal_index]
        dset = set(donor_indices)
        elems = [a[0] for a in atoms]
        comp_arr = np.array(comp)

        def _worst_nondonor(mem, ds):
            """(closest bonder distance, closest non-donor heavy-atom distance) for a ligand."""
            dref = min(float(np.linalg.norm(P[i] - m)) for i in ds)
            nd = [float(np.linalg.norm(P[i] - m)) for i in mem
                  if i not in dset and atoms[i][0] != "H"]
            return dref, (min(nd) if nd else float("inf"))

        for mem in members.values():
            ds = [i for i in mem if i in dset]
            if not ds or len(ds) > 2:
                continue                          # 3+ donors: no safe rigid move (see docstring)
            body = [i for i in mem if i not in dset and atoms[i][0] != "H"]
            if len(body) < min_body:
                continue
            dref, worst = _worst_nondonor(mem, ds)
            if worst >= dref - clearance:
                continue                          # bonders already the closest atoms -- nothing to do

            before = worst
            R = None
            pivot = None
            if len(ds) == 1:                      # pivot on the donor, seat its substituent cone out
                d = ds[0]
                pivot = P[d].copy()
                out = P[d] - m
                no = float(np.linalg.norm(out))
                if no < 1e-6:
                    continue
                out /= no
                # Seat the donor's substituents in the far hemisphere by rotating about the donor.
                # A single rigid rotation can only fix the collapse if there is a reference direction
                # of the donor that, aligned with `out`, carries every substituent away from the
                # metal. We generate the physically meaningful candidates and keep whichever rotation
                # maximises the closest body-atom distance:
                #   * the cone axis (sum of donor->alpha bonds) -- correct for a pyramidal donor
                #     seated slightly off the lone pair (VOFRAJ's phosphine);
                #   * +/- the alpha-shell plane normal (the lone-pair axis) -- correct when the metal
                #     is edge-on to a flattened donor and the cone vectors cancel (IFASOA, where one
                #     P-C bond points straight at the metal);
                #   * the body centroid -- the last resort for a single-substituent donor.
                # A rigid rotation can't fix a case where no candidate separates all substituents
                # (a truly mis-pyramidalised donor); then none improves the min and we leave it.
                alpha = [a for a in nbr[d] if a != metal_index and atoms[a][0] != "H"]
                cands = []
                if len(alpha) >= 2:
                    cs = np.zeros(3)
                    for a in alpha:
                        v = P[a] - P[d]
                        nv = float(np.linalg.norm(v))
                        if nv > 1e-6:
                            cs += v / nv
                    if float(np.linalg.norm(cs)) > 0.3:
                        cands.append(cs / float(np.linalg.norm(cs)))
                if len(alpha) >= 3:
                    A = np.array([P[a] - P[d] for a in alpha], float)
                    A = A - A.mean(0)
                    nrm = np.linalg.svd(A)[2][2]
                    cands.append(nrm)
                    cands.append(-nrm)
                bd = P[body].mean(0) - P[d]
                if float(np.linalg.norm(bd)) > 1e-6:
                    cands.append(bd / float(np.linalg.norm(bd)))
                R, best_min = None, before
                for ref in cands:
                    axis = np.cross(ref, out)
                    na = float(np.linalg.norm(axis))
                    if na < 1e-6:
                        continue                  # candidate already on the M-donor axis
                    Rc = _rot_about(axis / na, math.acos(max(-1.0, min(1.0, float(ref @ out)))))
                    mnd = min(float(np.linalg.norm(pivot + Rc @ (P[i] - pivot) - m)) for i in body)
                    if mnd > best_min + 1e-3:
                        R, best_min = Rc, mnd
                if R is None:
                    continue                      # no rigid rotation seats the substituents out
            else:                                 # bidentate: rotate about the donor-donor axis
                d1, d2 = ds
                pivot = P[d1].copy()
                u = P[d2] - P[d1]
                nu = float(np.linalg.norm(u))
                if nu < 1e-6:
                    continue
                u /= nu
                c = P[body].mean(0)
                cp = (c - pivot) - float((c - pivot) @ u) * u   # body perp component
                mp = (m - pivot) - float((m - pivot) @ u) * u   # metal perp component
                ncp, nmp = float(np.linalg.norm(cp)), float(np.linalg.norm(mp))
                if ncp < 1e-6 or nmp < 1e-6:
                    continue
                cp /= ncp
                target = -mp / nmp                # want body on the opposite side of the metal
                ang = math.acos(max(-1.0, min(1.0, float(cp @ target))))
                if float(np.cross(cp, target) @ u) < 0:
                    ang = -ang
                R = _rot_about(u, ang)

            Pnew = P.copy()
            for i in mem:
                if i not in ds:                   # donors stay fixed (on the pivot / axis)
                    Pnew[i] = pivot + R @ (P[i] - pivot)
            # keep only if the closest non-donor atom genuinely moved away from the metal, and the
            # body did not land in a neighbouring ligand
            nd = [float(np.linalg.norm(Pnew[i] - m)) for i in body]
            if nd and min(nd) > before + 1e-3 and (
                    collapse_count(Pnew, elems, comp_arr) <= collapse_count(P, elems, comp_arr)):
                P = Pnew
                reoriented += 1

        if reoriented:
            _write_xyz(Path(xyz_path),
                       [(atoms[i][0], tuple(P[i])) for i in range(n)],
                       comment="ligand bodies oriented so bonders are closest to the metal")
    except Exception:  # noqa: BLE001  (never fail the build on a pre-opt tweak)
        return 0
    return reoriented


def declash_monodentate_torsion(xyz_path, constructed, metal_index: int, donor_indices: list[int],
                                min_bulk: int = 3, steps: int = 24, passes: int = 2,
                                clash_ratio: float = 1.15) -> int:
    """Interleave crowded bulky MONODENTATES by spinning each about its own M-donor axis. Three
    bulky ligands on a trigonal centre (VOFRAJ: a phenoxide + two tribenzylphosphines at 120 deg)
    seat their cones correctly outward yet still ram each other -- the substituent arms of adjacent
    ligands interpenetrate (carbons of different ligands at <1 A). The metal-excluded UFF de-clash
    can't help here: with atoms that overlapped it mangles a ligand's own P-C bond and the
    bond-integrity guard reverts it. A rotation about the M-donor axis, though, is RIGID (no bond
    can change) and preserves both the bonder position and the cone's outward tilt (every atom keeps
    its distance from that axis) -- it only re-aims the arms azimuthally, which is exactly the free
    coordinate that lets neighbouring cones mesh instead of collide.

    For each bulky monodentate, coarse-search the rotation angle that minimises the total inter-
    ligand overlap (:func:`_inter_ligand_overlap`), a few passes so ligands settle against each
    other. Kept only if the overall overlap drops. Returns the number of ligands rotated."""
    from collections import defaultdict

    import numpy as np

    rotated = 0
    try:
        atoms = _read_xyz(Path(xyz_path))
        n = len(atoms)
        if metal_index is None or not donor_indices or metal_index >= n:
            return 0
        bonds = [(b.get_atom1().get_id(), b.get_atom2().get_id()) for b in constructed.get_bonds()]
        comp = _components_excluding(bonds, n, metal_index)
        dset = set(donor_indices)
        members: dict[int, list[int]] = defaultdict(list)
        for i in range(n):
            if comp[i] >= 0:
                members[comp[i]].append(i)
        targets = []                                   # (donor_index, member_list) per bulky monodentate
        for mem in members.values():
            ds = [i for i in mem if i in dset]
            if len(ds) == 1 and sum(1 for i in mem if i not in dset and atoms[i][0] != "H") >= min_bulk:
                targets.append((ds[0], mem))
        if len(targets) < 2:                           # a lone bulky ligand has nothing to mesh with
            return 0
        P = np.array([a[1] for a in atoms], float)
        m = P[metal_index]
        rad = np.array([_cov_radius(a[0]) or 0.0 for a in atoms], float)
        heavy = np.array([a[0] != "H" and (_cov_radius(a[0]) is not None) for a in atoms])

        def _overlap():
            return _inter_ligand_overlap([(atoms[i][0], tuple(P[i])) for i in range(n)],
                                         comp, clash_ratio)

        before = _overlap()
        if before <= 1e-6:
            return 0
        for _ in range(passes):
            for d, mem in targets:
                axis = P[d] - m
                na = float(np.linalg.norm(axis))
                if na < 1e-6:
                    continue
                axis /= na
                # Only pairs between this ligand and the OTHER ligands change as it spins, so score
                # just those (vectorised): minimising this ligand's cross-ligand overlap minimises
                # the total. `mi_h` = this ligand's heavy atoms; `oth` = heavy atoms elsewhere.
                mem_h = [i for i in mem if heavy[i]]
                oth = [j for j in range(n) if heavy[j] and comp[j] >= 0 and comp[j] != comp[mem[0]]]
                if not mem_h or not oth:
                    continue
                Po = P[oth]
                ro = rad[oth]
                base = P[[*mem]].copy()
                base_h = P[mem_h].copy()

                def _cross(Ph):
                    diff = Ph[:, None, :] - Po[None, :, :]
                    dist = np.sqrt((diff * diff).sum(-1))
                    over = clash_ratio * (rad[mem_h][:, None] + ro[None, :]) - dist
                    return float(np.clip(over, 0.0, None).sum())

                best_ang, best_ov = 0.0, _cross(base_h)
                for k in range(1, steps):
                    R = _rot_about(axis, 2.0 * math.pi * k / steps)
                    ov = _cross((base_h - m) @ R.T + m)
                    if ov < best_ov - 1e-6:
                        best_ov, best_ang = ov, 2.0 * math.pi * k / steps
                if abs(best_ang) > 1e-9:
                    R = _rot_about(axis, best_ang)     # commit the best angle onto all ligand atoms
                    P[[*mem]] = (base - m) @ R.T + m
                    rotated += 1
        after = _overlap()
        if rotated and after < before - 1e-6:
            _write_xyz(Path(xyz_path),
                       [(atoms[i][0], tuple(P[i])) for i in range(n)],
                       comment="bulky monodentates de-clashed by axial rotation")
        else:
            rotated = 0                                # no net improvement -> leave the assembly
    except Exception:  # noqa: BLE001  (never fail the build on a pre-opt tweak)
        return 0
    return rotated


def reposition_stranded_monodentates(xyz_path, constructed, metal_index: int,
                                     donor_indices: list[int], metal_symbol: "str | None" = None,
                                     oxidation_state: "int | None" = None,
                                     coordination_number: "int | None" = None,
                                     slack: float = 0.3) -> Path:
    """Slide each MONODENTATE ligand rigidly along its metal-donor axis so the donor sits at its
    CSD/covalent reference bond length, when the assembly left it stranded far out.

    The site model seats every donor on a generic 2.5 A shell and MCHammer then trades the M-L
    spring against ligand-ligand sterics, so a bulky monodentate (OGOLAX's terphenyl-phenoxide) is
    pushed out to ~3 A -- a bad, far starting point for xtb even though xtb usually recovers the
    ~1.95 A bond. Translate the WHOLE ligand (rigid body, no internal distortion) inward so the
    donor lands on the reference distance; only stranded donors (current > reference + ``slack``)
    are moved, and only monodentates (a rigid slide can't seat every donor of a chelate). The
    metal, other ligands and every internal bond are untouched. Overwrites ``xyz_path``; never
    raises."""
    from collections import defaultdict

    try:
        atoms = _read_xyz(Path(xyz_path))
        n = len(atoms)
        if metal_index is None or not donor_indices or metal_index >= n:
            return Path(xyz_path)
        bonds = [(b.get_atom1().get_id(), b.get_atom2().get_id()) for b in constructed.get_bonds()]
        comp = _components_excluding(bonds, n, metal_index)
        donor_set = set(donor_indices)
        members_of: dict[int, list[int]] = defaultdict(list)
        for i in range(n):
            if comp[i] >= 0:
                members_of[comp[i]].append(i)
        m = atoms[metal_index][1]
        moved = False
        for members in members_of.values():
            ds = [i for i in members if i in donor_set]
            if len(ds) != 1:
                continue                          # monodentate ligands only
            d = ds[0]
            v = [atoms[d][1][k] - m[k] for k in range(3)]
            dist = math.sqrt(sum(c * c for c in v))
            if dist < 1e-6:
                continue
            ref = _restraint_reference(dist, metal_symbol or atoms[metal_index][0],
                                       _donor_key(atoms, d, metal_index),
                                       ox=oxidation_state, cn=coordination_number)
            if dist - ref <= slack:
                continue                          # already at/inside the reference -> leave it
            shift = [(v[k] / dist) * (ref - dist) for k in range(3)]   # inward along M-donor axis
            for i in members:
                atoms[i] = (atoms[i][0], tuple(atoms[i][1][k] + shift[k] for k in range(3)))
            moved = True
        if moved:
            _write_xyz(Path(xyz_path), atoms, comment="stranded monodentates repositioned")
    except Exception:  # noqa: BLE001  (never fail the build on a pre-opt tweak)
        return Path(xyz_path)
    return Path(xyz_path)


def reposition_stranded_polydentates(xyz_path, constructed, metal_index: int,
                                     donor_indices: list[int], metal_symbol: "str | None" = None,
                                     oxidation_state: "int | None" = None,
                                     coordination_number: "int | None" = None,
                                     slack: float = 0.3, clash_ratio: float = 1.15) -> Path:
    """Slide each stranded POLYDENTATE (chelate/pincer) ligand rigidly along its metal->donor-
    centroid axis so its donors approach their CSD reference bond length, backing off as needed to
    keep inter-ligand overlap from rising.

    Unlike :func:`reposition_stranded_monodentates` (a lone donor slides exactly onto its
    reference along the single M-donor axis), a chelate's donors are coupled through the backbone,
    so one rigid slide cannot seat every donor exactly; instead the WHOLE ligand slides along its
    metal->donor-centroid axis by the least-squares delta that best fits the per-donor references.
    A bulky chelate in a crowded, high-CN sphere may have no room to come in, so the inward move is
    then binary-searched back down until it no longer raises the inter-ligand overlap. Rigid => no
    internal ligand distortion; the metal, other ligands and every internal bond are untouched.
    Overwrites ``xyz_path``; never raises."""
    from collections import defaultdict

    try:
        atoms = _read_xyz(Path(xyz_path))
        n = len(atoms)
        if metal_index is None or not donor_indices or metal_index >= n:
            return Path(xyz_path)
        bonds = [(b.get_atom1().get_id(), b.get_atom2().get_id()) for b in constructed.get_bonds()]
        comp = _components_excluding(bonds, n, metal_index)
        donor_set = set(donor_indices)
        members_of: dict[int, list[int]] = defaultdict(list)
        for i in range(n):
            if comp[i] >= 0:
                members_of[comp[i]].append(i)
        m = atoms[metal_index][1]
        metal_el = metal_symbol or atoms[metal_index][0]
        moved = False
        for members in members_of.values():
            ds = [i for i in members if i in donor_set]
            if len(ds) < 2:
                continue  # polydentate only; monodentates handled above
            dists = [math.dist(m, atoms[i][1]) for i in ds]
            refs = [_restraint_reference(dists[k], metal_el,
                                         _donor_key(atoms, ds[k], metal_index, ds),
                                         ox=oxidation_state, cn=coordination_number)
                    for k in range(len(ds))]
            if (sum(dists) / len(dists)) - (sum(refs) / len(refs)) <= slack:
                continue                          # centroid already at/inside the reference
            centroid = [sum(atoms[i][1][k] for i in ds) / len(ds) for k in range(3)]
            v = [centroid[k] - m[k] for k in range(3)]
            axis_len = math.sqrt(sum(c * c for c in v))
            if axis_len < 1e-6:
                continue
            u = [c / axis_len for c in v]

            def _pt(i, dd):  # donor/atom i shifted inward along the axis by dd
                return [atoms[i][1][t] - dd * u[t] for t in range(3)]

            # Best inward delta: least-squares fit of the donors to their refs along the axis.
            hi = max(0.0, (sum(dists) / len(dists)) - min(refs))
            best, best_sse = 0.0, None
            for s in range(101):
                delta = hi * s / 100
                sse = sum((math.dist(m, _pt(i, delta)) - refs[k]) ** 2
                          for k, i in enumerate(ds))
                if best_sse is None or sse < best_sse:
                    best_sse, best = sse, delta
            if best <= 1e-6:
                continue

            def _translated(frac):
                a2 = list(atoms)
                for i in members:
                    a2[i] = (atoms[i][0], tuple(_pt(i, frac * best)))
                return a2

            # Clash guard: take the full slide only if it does not raise inter-ligand overlap;
            # otherwise binary-search the largest inward fraction that stays clash-neutral.
            base_ov = _inter_ligand_overlap(atoms, comp, clash_ratio)
            if _inter_ligand_overlap(_translated(1.0), comp, clash_ratio) <= base_ov + 1e-6:
                frac = 1.0
            else:
                lo, high = 0.0, 1.0
                for _ in range(12):
                    mid = (lo + high) / 2
                    if _inter_ligand_overlap(_translated(mid), comp, clash_ratio) <= base_ov + 1e-6:
                        lo = mid
                    else:
                        high = mid
                frac = lo
            if frac <= 1e-3:
                continue
            for i in members:
                atoms[i] = (atoms[i][0], tuple(_pt(i, frac * best)))
            moved = True
        if moved:
            _write_xyz(Path(xyz_path), atoms, comment="stranded polydentates repositioned")
    except Exception:  # noqa: BLE001  (never fail the build on a pre-opt tweak)
        return Path(xyz_path)
    return Path(xyz_path)


def _inter_ligand_overlap(atoms, comp, clash_ratio: float = 1.15) -> float:
    """Soft, depth-weighted sum of inter-ligand heavy-atom overlaps: Σ max(0, r_cov·ratio − d)
    over every heavy pair on DIFFERENT ligands (different component). Bigger = more clash."""
    import numpy as np

    P = np.array([a[1] for a in atoms], float)
    radii = [_cov_radius(a[0]) for a in atoms]
    n = len(atoms)
    s = 0.0
    for i in range(n):
        ri = radii[i]
        if ri is None or atoms[i][0] == "H" or comp[i] < 0:
            continue
        for j in range(i + 1, n):
            rj = radii[j]
            if rj is None or atoms[j][0] == "H" or comp[j] < 0 or comp[j] == comp[i]:
                continue
            over = clash_ratio * (ri + rj) - float(np.linalg.norm(P[i] - P[j]))
            if over > 0:
                s += over
    return s


def declash_bulky_ligands(xyz_path, constructed, metal_index: int, donor_indices: list[int],
                          oxidation_state: "int | None" = None,
                          coordination_number: "int | None" = None,
                          min_bulk: int = 3, clash_ratio: float = 1.15) -> Path:
    """When the sphere carries a bulky ligand whose substituents clash with a neighbour, relax the
    ligand shell with the metal-excluded UFF (:func:`ff_declash`) so the bodies splay apart — the
    JOINT relax that a rigid azimuthal rotation can't do for a ~symmetric PPh₃ cone (rotating a
    3-fold cone barely changes its clash profile; the phenyls have to flex).

    The bulk can belong to a ligand of ANY denticity, not just a monodentate. Three PPh₃ on a
    trigonal Ag whose phenyls collide (IFASOA) was the original monodentate target, but a small
    co-ligand rammed by a MULTIDENTATE's substituent needs the same relax: on a Mn(III) hydrido-
    carbonyl PCP pincer the carbonyl carbon sits ~1.6 Å from an isopropyl methyl of the pincer in
    the raw placement, which xtb then "resolves" by forging a spurious C–C bond and bending the CO.
    Restricting the trigger to 1-donor ligands meant the bulky pincer never fired this de-clash.

    Guarded so it is never a net loss: it runs only when a bulky ligand is present AND the sphere
    already has inter-ligand overlap, then keeps the UFF result ONLY if that overlap DECREASES — a
    sphere ff_declash would otherwise worsen (it can, on some geometries: ROSJIU, SOQZIK) is
    reverted to the assembly. Overwrites ``xyz_path``; never raises."""
    from collections import defaultdict

    try:
        atoms = _read_xyz(Path(xyz_path))
        n = len(atoms)
        if metal_index is None or not donor_indices or metal_index >= n:
            return Path(xyz_path)
        bonds = [(b.get_atom1().get_id(), b.get_atom2().get_id()) for b in constructed.get_bonds()]
        comp = _components_excluding(bonds, n, metal_index)
        donor_set = set(donor_indices)
        members_of: dict[int, list[int]] = defaultdict(list)
        for i in range(n):
            if comp[i] >= 0:
                members_of[comp[i]].append(i)
        # A bulky BODY (>= min_bulk non-donor heavy atoms) on a ligand of ANY denticity: a
        # multidentate pincer's isopropyl arms crowd a neighbouring cis site just as a bulky
        # monodentate's cone does. (Previously required exactly one donor, so a bulky chelate or
        # pincer never triggered the de-clash and its clash was handed straight to xtb.)
        bulky = any(
            sum(1 for i in mem if i not in donor_set and atoms[i][0] != "H") >= min_bulk
            for mem in members_of.values()
        )
        if not bulky:
            return Path(xyz_path)
        before = _inter_ligand_overlap(atoms, comp, clash_ratio)
        if before <= 1e-6:
            return Path(xyz_path)                 # nothing clashing -> leave the assembly alone
        snapshot = Path(xyz_path).read_text(encoding="utf-8")
        ff_declash(xyz_path, constructed, metal_index, donor_indices,
                   oxidation_state=oxidation_state, coordination_number=coordination_number)
        after_atoms = _read_xyz(Path(xyz_path))
        after = _inter_ligand_overlap(after_atoms, comp, clash_ratio)
        # Bond-integrity guard: the metal-excluded UFF can mangle a ligand's OWN geometry (VOFRAJ:
        # a tribenzylphosphine came back with P-C at 1.2 A), which the inter-ligand overlap check
        # can't see. Revert if any topology bond's length moved more than 0.3 A -- a real bond
        # never should during a de-clash.
        def _worst_bond_shift() -> float:
            worst = 0.0
            for a, b_ in bonds:
                if a == metal_index or b_ == metal_index or a >= n or b_ >= n:
                    continue
                d0 = math.dist(atoms[a][1], atoms[b_][1])
                d1 = math.dist(after_atoms[a][1], after_atoms[b_][1])
                worst = max(worst, abs(d1 - d0))
            return worst

        if after > before - 1e-6 or _worst_bond_shift() > 0.3:  # no net de-clash OR a bond broke
            Path(xyz_path).write_text(snapshot, encoding="utf-8")
    except Exception:  # noqa: BLE001  (never fail the build on a pre-opt tweak)
        return Path(xyz_path)
    return Path(xyz_path)


def _read_xyz_comment(path: Path) -> str:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[1] if len(lines) > 1 else ""


def _parse_energy(comment: str, stdout: str) -> float | None:
    """GFN total energy (Hartree) from the xtbopt comment line or xtb stdout."""
    m = _XYZ_ENERGY_RE.search(comment)
    if m:
        return float(m.group(1))
    m = _TOTAL_ENERGY_RE.search(stdout)
    return float(m.group(1)) if m else None


def _metal_donors(
    atoms: list[tuple[str, tuple[float, float, float]]], metal_symbol: str, n_donors: int
) -> tuple[int, list[tuple[int, float]]]:
    """Locate the (unique) metal and its ``n_donors`` nearest **heavy** atoms.

    Fallback donor identification when explicit indices aren't supplied. No bond
    graph exists in an .xyz, so proximity is the signal; H is excluded because a
    bare hydrogen is never a real donor. For bulky multi-heteroatom ligands the
    nearest heavy atom can be a backbone atom rather than the true donor -- prefer
    passing explicit ``donor_indices`` (from the assembled topology) when known.
    Returns ``(metal_index, [(donor_index, distance), ...])`` (0-based indices).
    """
    metal_idxs = [i for i, (el, _) in enumerate(atoms) if el == metal_symbol]
    if len(metal_idxs) != 1:
        raise XtbError(
            f"Expected exactly one {metal_symbol} atom for restraint, found {len(metal_idxs)}"
        )
    mi = metal_idxs[0]
    mx, my, mz = atoms[mi][1]
    dists = [
        (i, math.dist(atoms[i][1], (mx, my, mz)))
        for i, (el, _) in enumerate(atoms)
        if i != mi and el != "H"
    ]
    dists.sort(key=lambda t: t[1])
    return mi, dists[:n_donors]


def _resolve_donors(
    atoms: list[tuple[str, tuple[float, float, float]]],
    metal_index: int | None,
    donor_indices: list[int] | None,
    metal_symbol: str | None,
    coordination_number: int | None,
) -> tuple[int, list[tuple[int, float]]]:
    """Return ``(metal_index, [(donor_index, distance), ...])``, preferring the
    explicit topological donor indices (correct even for bulky ligands) and
    falling back to the nearest-heavy-atom heuristic."""
    if metal_index is not None and donor_indices:
        mp = atoms[metal_index][1]
        return metal_index, [(di, math.dist(atoms[di][1], mp)) for di in donor_indices]
    if metal_symbol is not None and coordination_number is not None:
        return _metal_donors(atoms, metal_symbol, coordination_number)
    raise XtbError(
        "restrain_donors requires either (metal_index + donor_indices) or "
        "(metal_symbol + coordination_number)."
    )


def _write_constraint_file(
    path: Path,
    constraints: list[tuple[int, int, float]],
    force_constant: float,
    angle_constraints: "list[tuple[int, int, int, float]] | None" = None,
    dihedral_constraints: "list[tuple[int, int, int, int, float]] | None" = None,
    strong_constraints: "list[tuple[int, int, float]] | None" = None,
    strong_force_constant: float = 5.0,
) -> None:
    """Write an xtb ``$constrain`` block holding each ``(i, j, distance)`` pair, each
    ``(a, vertex, b, degrees)`` angle near the given value, and each
    ``(i, j, k, l, degrees)`` dihedral (atom indices are 1-based in xtb input files;
    ``angle: a,b,c`` fixes the a-b-c angle at vertex b, ``dihedral: i,j,k,l`` the i-j-k-l torsion).

    ``strong_constraints`` go in a SECOND ``$constrain`` block at ``strong_force_constant`` -- xtb
    applies a block's force constant to that block's entries, so a stiff anti-fusion floor can be
    held without stiffening the ordinary M-L / intra-ligand restraints."""
    lines = ["$constrain", f"  force constant={force_constant}"]
    for i, j, dist in constraints:
        lines.append(f"  distance: {i + 1}, {j + 1}, {dist:.3f}")
    for a, v, b, deg in (angle_constraints or []):
        lines.append(f"  angle: {a + 1}, {v + 1}, {b + 1}, {deg:.2f}")
    for i, j, k, l, deg in (dihedral_constraints or []):
        lines.append(f"  dihedral: {i + 1}, {j + 1}, {k + 1}, {l + 1}, {deg:.2f}")
    lines.append("$end")
    if strong_constraints:
        lines.append("$constrain")
        lines.append(f"  force constant={strong_force_constant}")
        for i, j, dist in strong_constraints:
            lines.append(f"  distance: {i + 1}, {j + 1}, {dist:.3f}")
        lines.append("$end")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_angle_constraints(
    site_dirs: "list",
    metal_index: int,
    donor_indices: list[int],
    coords: "list",
    chelate_pairs: "set | None" = None,
    bite_target=None,
) -> list[tuple[int, int, int, float]]:
    """Ideal donor-metal-donor angle constraints from the coordination geometry.

    Each donor is matched to one of the geometry's ``site_dirs`` (idealised unit
    site vectors) by an optimal angular assignment, so the ideal L-M-L angle of any
    donor pair is the angle between their matched site vectors -- e.g. 90 deg / 180
    deg for octahedral. This restrains xtb toward the correct coordination polyhedron
    without needing the explicit site assignment threaded through (it is recovered
    from the assembled geometry), and the *global* matching is robust to the ~20 deg
    slop the assembly leaves in individual donors.

    Inter-ligand pairs are restrained to the ideal inter-site angle. Same-ligand
    (chelate bite) pairs in ``chelate_pairs`` (a set of ``frozenset({i, j})`` donor
    atom indices) are left free unless ``bite_target(i, j)`` returns a value (the
    future CSD-mined bite angle) -- their angle is set by the ligand backbone, not
    the polyhedron. Returns ``[(donor_i, metal_index, donor_j, target_deg), ...]``;
    empty if donor and site counts differ (an over/under-coordinated build), so a
    malformed sphere is never over-constrained.
    """
    import numpy as np

    try:
        from scipy.optimize import linear_sum_assignment
    except Exception:
        return []
    if len(donor_indices) != len(site_dirs) or len(donor_indices) < 2:
        return []
    m = np.asarray(coords[metal_index], dtype=float)
    dvecs = []
    for di in donor_indices:
        v = np.asarray(coords[di], dtype=float) - m
        nv = np.linalg.norm(v)
        if nv < 1e-6:
            return []
        dvecs.append(v / nv)
    D = np.asarray(dvecs)
    S = np.asarray([np.asarray(s, dtype=float) / np.linalg.norm(s) for s in site_dirs])
    cost = np.arccos(np.clip(D @ S.T, -1.0, 1.0))
    row, col = linear_sum_assignment(cost)
    site_of = {donor_indices[r]: int(c) for r, c in zip(row, col)}
    chelate_pairs = chelate_pairs or set()
    out: list[tuple[int, int, int, float]] = []
    idx = list(donor_indices)
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            di, dj = idx[a], idx[b]
            sa, sb = site_of[di], site_of[dj]
            ideal = float(np.degrees(np.arccos(np.clip(S[sa] @ S[sb], -1.0, 1.0))))
            if frozenset((di, dj)) in chelate_pairs:
                t = bite_target(di, dj) if bite_target else None
                if t is not None:
                    out.append((di, metal_index, dj, t))
                continue
            out.append((di, metal_index, dj, ideal))
    return out


_CORETYPE_CACHE: "str | None" = None


def _openblas_coretype(cpuinfo_path: str = "/proc/cpuinfo") -> str:
    """The OpenBLAS kernel xtb should use on this CPU.

    Haswell (AVX2) by default. On AMD CPUs with AVX-512, i.e. Zen4/Zen5 (EPYC 9V74, 9V45), the
    Haswell kernel of conda-forge's OpenBLAS 0.3.34 makes xtb GFN2 segfault (rc=-11, reproduced on
    every such CI runner, single- or multi-threaded, whatever the stack), which silently returned
    the unrelaxed geometry; the SandyBridge (AVX) kernel is clean there. Intel (AVX-512 or not) and
    Zen3 (EPYC 7763) are clean on Haswell and keep it. Non-Linux / unreadable cpuinfo -> Haswell."""
    global _CORETYPE_CACHE
    if _CORETYPE_CACHE is not None and cpuinfo_path == "/proc/cpuinfo":
        return _CORETYPE_CACHE
    core = "Haswell"
    try:
        with open(cpuinfo_path, encoding="utf-8", errors="replace") as fh:
            head = fh.read(64_000)   # the first core's block is enough
        vendor = next((ln.split(":", 1)[1].strip() for ln in head.splitlines()
                       if ln.startswith("vendor_id")), "")
        flags = next((ln.split(":", 1)[1].split() for ln in head.splitlines()
                      if ln.startswith("flags")), [])
        if vendor == "AuthenticAMD" and "avx512f" in flags:
            core = "SandyBridge"
    except OSError:
        pass
    if cpuinfo_path == "/proc/cpuinfo":
        _CORETYPE_CACHE = core
    return core


def _raise_stack_limit() -> None:
    """Raise this process's soft stack limit to its hard limit (POSIX only), so the xtb child
    inherits it. OMP_STACKSIZE only sizes the OpenMP worker threads; xtb's MAIN thread still gets
    ``ulimit -s`` (8 MB in a stock container), and on a large complex (the 195-atom Re(V) dioxo
    bis-PNP) xtb then segfaults (rc=-11, no output) and the build silently keeps the assembled
    geometry. xtb's docs prescribe ``ulimit -s unlimited``. Done in the parent rather than via
    ``preexec_fn``, which is unsafe with the web worker's threads. Idempotent; never raises."""
    try:
        import resource
    except ImportError:  # Windows: the stack size is fixed in the executable
        return
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
        if soft != hard and (hard == resource.RLIM_INFINITY or soft < hard):
            resource.setrlimit(resource.RLIMIT_STACK, (hard, hard))
    except (ValueError, OSError):
        pass


# Per-process caps on the xtb child: the container bounds MeCoBi as a whole, but
# xtb shares that box with the web server, so a runaway run must hit its OWN limits first.
# Defaults are generous for real work (a 200-atom GFN2 opt writes tens of MB) and are
# env-overridable; MECOBI_XTB_LIMITS=0 turns the whole wrapper off.
XTB_MAX_FILE_MB = 1024      # RLIMIT_FSIZE per file: guards the shared root disk (15 Sep outage)
XTB_OOM_SCORE_ADJ = 1000    # make xtb the container OOM killer's first victim, not uvicorn
XTB_CPU_MARGIN_S = 60       # RLIMIT_CPU = budget x threads + margin (backstop to the wall clock)
# Signals the caps deliver, for a readable XtbError instead of a bare rc.
_LIMIT_SIGNALS = {
    -9: "killed (SIGKILL), most likely by the out-of-memory killer",
    -24: "hit its CPU-time limit (SIGXCPU)",
    -25: "hit its maximum output file size (SIGXFSZ)",
}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _limited_command(cmd: list[str], *, timeout_s: int | None, threads: int) -> list[str]:
    """Wrap ``cmd`` so the xtb child alone runs under resource caps (POSIX only).

    A ``/bin/sh`` prologue lowers the child's own rlimits and raises its ``oom_score_adj``
    (both allowed unprivileged), then ``exec``s xtb, so the caps are in place before xtb
    starts and the timeout still kills xtb itself. Done this way because ``preexec_fn`` is
    unsafe with the web worker's threads, and setting limits in the parent would cap the
    whole server. Each step is independent and silenced: a limit that cannot be applied
    never blocks the run. Units: ``ulimit -f`` counts 512-byte blocks (POSIX sh; dash, and
    bash invoked as sh), ``-t`` is CPU seconds (all threads combined)."""
    if os.name != "posix" or os.environ.get("MECOBI_XTB_LIMITS", "1") == "0":
        return cmd
    steps = ["ulimit -c 0 2>/dev/null"]  # no multi-GB cores from a segfault with a 4 GB stack
    file_mb = _env_int("MECOBI_XTB_MAX_FILE_MB", XTB_MAX_FILE_MB)
    if file_mb > 0:
        steps.append(f"ulimit -f {file_mb * 2048} 2>/dev/null")
    if timeout_s:
        steps.append(f"ulimit -t {int(timeout_s) * max(1, threads) + XTB_CPU_MARGIN_S} 2>/dev/null")
    oom = _env_int("MECOBI_XTB_OOM_SCORE_ADJ", XTB_OOM_SCORE_ADJ)
    if oom:
        steps.append(f"echo {oom} > /proc/self/oom_score_adj 2>/dev/null")
    script = "; ".join(steps) + '; exec "$@"'
    return ["/bin/sh", "-c", script, "xtb", *cmd]


def relax_with_xtb(
    xyz_in: str | Path,
    *,
    charge: int,
    uhf: int,
    workdir: str | Path | None = None,
    timeout_s: int | None = 600,
    xtb_bin: str = "xtb",
    gfn: int = 2,
    opt_level: str = "normal",
    threads: int | None = None,
    restrain_donors: bool = False,
    metal_symbol: str | None = None,
    coordination_number: int | None = None,
    oxidation_state: int | None = None,
    metal_index: int | None = None,
    donor_indices: list[int] | None = None,
    free_donors: "set[int] | None" = None,
    bond_pairs: list[tuple[int, int]] | None = None,
    angle_constraints: "list[tuple[int, int, int, float]] | None" = None,
    dihedral_constraints: "list[tuple[int, int, int, int, float]] | None" = None,
    extra_distances: "list[tuple[int, int, float]] | None" = None,
    restraint_fc: float = 0.5,
    strong_distances: "list[tuple[int, int, float]] | None" = None,
    strong_fc: float = 5.0,
    warnings: list[str] | None = None,
    energy_out: dict | None = None,
    reference_metal: str | None = None,
) -> Path:
    """Run an xtb GFN geometry optimisation; overwrite ``xyz_in`` with the result.

    ``reference_metal``: the element whose M-L reference distances restrain the donors, when it
    is not the metal written in the file -- a complex relaxed as an xtb surrogate (Y as Sc) must
    still be held at the REAL metal's bond lengths (Y-N 2.47 A, not Sc-N 2.35 A).

    Always passes ``--chrg {charge}`` and ``--uhf {uhf}`` (invariant 4). Runs in an
    isolated subdirectory so xtb's scratch files never collide between jobs.
    Returns the path to the optimised ``.xyz`` (same as ``xyz_in``).

    Coordination restraint (``restrain_donors=True``): in gas phase, with no crystal
    packing / counterion / solvent, labile donors (halides, weak N/O) can drift off
    the metal during optimisation. When enabled, the metal-donor distances in the
    *input* (assembled) geometry are harmonically restrained (force constant
    ``restraint_fc``) so relaxation optimises ligand conformation and angles without
    letting donors run away. Donors are identified from the explicit
    ``metal_index`` + ``donor_indices`` (the true donors from the assembled
    topology; correct even for bulky ligands) when given, else from the nearest
    ``coordination_number`` heavy atoms to ``metal_symbol``. If a restrained donor
    ends beyond :data:`DISSOCIATION_THRESHOLD_A` *and* xtb pushed it further out than
    the assembly had it, the input (pre-relax) geometry is kept instead of the
    dissociated result. A donor the ASSEMBLY already stranded past the threshold that
    xtb pulled inward (an incomplete pull, not a dissociation) keeps its relaxed
    geometry -- that geometry is strictly closer to a real complex than the assembled
    one -- but is still excluded from energy ranking. Either way a message is appended
    to ``warnings`` (if provided). With ``restrain_donors=False`` the behaviour is
    unchanged.
    """
    xyz_in = Path(xyz_in).resolve()
    base = Path(workdir) if workdir else xyz_in.parent
    run_dir = base / f".xtb_{xyz_in.stem}"
    if run_dir.exists():
        shutil.rmtree(run_dir, ignore_errors=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    # ``gfn='ff'`` selects the GFN-FF force field (``--gfnff``), which is far more
    # robust than the semi-empirical GFN Hamiltonians on hard cases (high charge,
    # f-elements, large systems) where the SCF diverges.
    gfn_flag = ["--gfnff"] if str(gfn).lower() in ("ff", "gfnff") else ["--gfn", str(gfn)]
    n_threads = _resolve_xtb_threads(threads)
    cmd = [
        xtb_bin, str(xyz_in), "--opt", opt_level,
        "--chrg", str(charge), "--uhf", str(uhf), *gfn_flag,
        "--parallel", str(n_threads),
    ]
    # xtb parallelises via OpenMP; set the thread count in the child env too (some
    # xtb builds honour OMP_NUM_THREADS over --parallel). A larger stack avoids the
    # segfaults xtb hits on big systems -- but the unit MUST be one libgomp accepts:
    # "4G" is REJECTED ("libgomp: Invalid value for OMP_STACKSIZE: 4G") on common Linux
    # builds, silently leaving the default (small) stack in place, so xtb segfaults on
    # larger complexes and the build falls back to the un-relaxed geometry. Use megabytes.
    xtb_env = {**os.environ, "OMP_NUM_THREADS": str(n_threads),
               "MKL_NUM_THREADS": str(n_threads)}
    xtb_env.setdefault("OMP_STACKSIZE", "4000M")
    # OpenBLAS runtime CPU detection can pick a BROKEN kernel when the CPU model is hidden
    # (e.g. under WSL2, where lscpu shows "-"), or misdetect some AMD Zen parts -- xtb then
    # gets NaN gradients from the linear algebra and every molecule "explodes" during opt.
    # Pin a known-good kernel so xtb is numerically sound regardless (see _openblas_coretype:
    # Haswell, or SandyBridge on AMD Zen4/Zen5 where the Haswell kernel segfaults); a user who
    # wants another kernel can still override OPENBLAS_CORETYPE in the environment.
    xtb_env.setdefault("OPENBLAS_CORETYPE", _openblas_coretype())
    _raise_stack_limit()

    if restrain_donors:
        pre_atoms = _read_xyz(xyz_in)
        metal_idx, donors = _resolve_donors(
            pre_atoms, metal_index, donor_indices, metal_symbol, coordination_number
        )
        metal_el = reference_metal or pre_atoms[metal_idx][0]
        # Metal-donor bonds: restrain to a covalent-radius target (pulls a stranded
        # bulky donor back to a real bond length). ``free_donors`` are left
        # unrestrained — a terminal oxo/nitrido (V=O, M≡N) whose real multiple bond
        # is far shorter than the covalent single-bond target, so it must relax
        # freely (it is a strong bond and won't dissociate).
        free = free_donors or set()
        donor_ids = [di for di, _ in donors]
        constraints = [
            (metal_idx, di, _restraint_reference(
                dist, metal_el, _donor_key(pre_atoms, di, metal_idx, donor_ids),
                ox=oxidation_state, cn=coordination_number,
                multiple_bond_ok=_can_multiple_bond(pre_atoms, di, metal_idx)))
            for di, dist in donors
            if di not in free
        ]
        # Intramolecular ligand bonds: hold each covalent bond near its assembled
        # length so xtb cannot pull a ligand apart (the assembled connectivity comes
        # from the stk topology, and its bond lengths are from RDKit embedding, so
        # they are already sane). Metal bonds are skipped -- handled above.
        if bond_pairs:
            for a, b in bond_pairs:
                if a == metal_idx or b == metal_idx:
                    continue
                constraints.append((a, b, math.dist(pre_atoms[a][1], pre_atoms[b][1])))
        # Anti-fusion floors between donors on different ligands (computed once from the assembly,
        # passed in): stops xtb forging a bond between two adjacent donors (cis carbonyls, oxo onto
        # a chelate O). Pure distance -- no angle, so it can't flip cis<->trans.
        if extra_distances:
            constraints.extend(extra_distances)
        con_file = run_dir / "constrain.inp"
        _write_constraint_file(con_file, constraints, restraint_fc, angle_constraints,
                               dihedral_constraints, strong_constraints=strong_distances,
                               strong_force_constant=strong_fc)
        cmd += ["--input", str(con_file)]
    elif angle_constraints:
        # An UNRESTRAINED relax (the σ-aryl policy) still honours angle restraints: they are the
        # end-on linearity holds (M-C≡O, M-C≡N, M-I-I), which the free relax silently dropped,
        # letting PIDRIE's η1-I2 fold over. No M-L distances, no dihedrals: the σ-aryl basin is
        # what the free relax is for.
        con_file = run_dir / "constrain.inp"
        _write_constraint_file(con_file, [], restraint_fc, angle_constraints, None)
        cmd += ["--input", str(con_file)]

    try:
        proc = subprocess.run(
            _limited_command(cmd, timeout_s=timeout_s, threads=n_threads),
            cwd=run_dir, capture_output=True, text=True,
            encoding="utf-8", errors="replace",  # xtb emits non-cp1252 chars on Windows
            timeout=timeout_s, env=xtb_env,
        )
    except subprocess.TimeoutExpired as exc:
        raise XtbTimeout(f"xtb timed out after {timeout_s}s on {xyz_in.name}") from exc
    except FileNotFoundError as exc:
        raise XtbNotFound(f"xtb executable {xtb_bin!r} not found on PATH.") from exc

    # Behind the limits wrapper a missing binary is sh's "exit 127: not found", not the
    # FileNotFoundError above; keep reporting it as XtbNotFound.
    if proc.returncode == 127 and "not found" in (proc.stderr or ""):
        raise XtbNotFound(f"xtb executable {xtb_bin!r} not found on PATH.")
    opt = run_dir / "xtbopt.xyz"
    if proc.returncode != 0 or not opt.exists():
        tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-15:])
        why = _LIMIT_SIGNALS.get(proc.returncode)
        why = f"; xtb {why}" if why else ""
        raise XtbError(f"xtb failed on {xyz_in.name} (rc={proc.returncode}{why}):\n{tail}")

    # GFN total energy of the relaxed structure (Hartree), for isomer ranking.
    if energy_out is not None:
        e = _parse_energy(_read_xyz_comment(opt), proc.stdout)
        if e is not None:
            energy_out["energy_eh"] = e

    if restrain_donors:
        # Fallback: if a (true) donor still dissociated despite the restraint, the
        # relaxed geometry is worse than the assembled one -- keep the pre-relax
        # structure. Uses the SAME donor set that was restrained, so a backbone
        # atom folding in can't mask a real donor leaving.
        opt_atoms = _read_xyz(opt)
        _mi, opt_donors = _resolve_donors(
            opt_atoms, metal_index, donor_indices, metal_symbol, coordination_number
        )
        m_el = reference_metal or (opt_atoms[_mi][0] if _mi is not None else (metal_symbol or ""))
        # Pre-relax M-L distances for the SAME donor set, to tell a donor xtb pushed off
        # from one the ASSEMBLY had already stranded (see DISSOCIATION_WORSENED_A). With
        # explicit donor_indices both resolutions return the same indices in the same
        # order; the nearest-heavy-atom fallback may not, and an unmatched donor is
        # treated as a genuine dissociation (the conservative reading).
        pre_by_index = {di: d for di, d in donors}
        # Per-donor threshold from the M-L reference: floor at DISSOCIATION_THRESHOLD_A, but
        # allow longer for metals whose reference bond is long (Y, lanthanides) so a genuinely
        # long-but-present bond is not misread as a dissociation.
        worst = None     # (bond, threshold): xtb pushed this donor out -> revert
        stranded = None  # (bond, threshold, pre-relax bond): assembly stranded it, xtb did not worsen it
        for di, dist in opt_donors:
            ref = _restraint_reference(dist, m_el,
                                       _donor_key(opt_atoms, di, _mi, [d for d, _ in opt_donors]),
                                       ox=oxidation_state, cn=coordination_number)
            thr = max(DISSOCIATION_THRESHOLD_A, ref * DISSOCIATION_REFERENCE_FACTOR)
            if dist <= thr:
                continue
            was = pre_by_index.get(di)
            if was is not None and was > thr and dist <= was + DISSOCIATION_WORSENED_A:
                # Long before the relax AND not pushed further out: incomplete inward
                # pull, not a dissociation. Keep the (better) relaxed geometry.
                if stranded is None or dist - thr > stranded[0] - stranded[1]:
                    stranded = (dist, thr, was)
                continue
            if worst is None or dist - thr > worst[0] - worst[1]:
                worst = (dist, thr)
        if worst is not None:
            max_bond, thr = worst
            # The parsed energy belongs to the discarded (dissociated) geometry, so
            # it should not be trusted for ranking against intact isomers.
            if energy_out is not None:
                energy_out["dissociated"] = True
            if warnings is not None:
                label = metal_symbol or "metal"
                warnings.append(
                    f"xtb relaxation dissociated a donor (M-{label} bond "
                    f"{max_bond:.2f} A > {thr:.2f} A); kept the "
                    f"pre-relax (assembled) geometry."
                )
            return xyz_in  # leave the assembled geometry in place, do not overwrite
        if stranded is not None:
            max_bond, thr, was = stranded
            # Geometry is kept (it is closer to a real complex than the assembly), but the
            # donor is still not bonded, so the energy is NOT comparable to intact isomers.
            if energy_out is not None:
                energy_out["dissociated"] = True
            if warnings is not None:
                label = metal_symbol or "metal"
                warnings.append(
                    f"a donor is still long after relaxation (M-{label} bond "
                    f"{max_bond:.2f} A > {thr:.2f} A; the assembly placed it at "
                    f"{was:.2f} A). xtb pulled it in but did not reach a bonded "
                    f"distance, so the relaxed geometry is kept but its energy is "
                    f"not ranked."
                )

    shutil.copyfile(opt, xyz_in)
    return xyz_in
