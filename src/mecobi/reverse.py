"""Reverse direction: an .xyz geometry -> metal + ligand SMILES.

The inverse of the build pipeline. Reads a mononuclear metal-complex geometry and
recovers, per ligand, its SMILES and which atoms coordinate the metal -- i.e. the
same information the forward pipeline consumes, so a reversed structure can be fed
straight back in (optionally via the donor-index isomer notation).

Perception backends
-------------------
Plain xyz->mol perception (RDKit's integrated xyz2mol, ``rdDetermineBonds``) does
not handle a transition-metal centre: the many metal-ligand contacts confuse the
valence model. The default ``"builtin"`` backend therefore strips the metal, splits
the remaining atoms into connected fragments (one per ligand), and perceives each
organic fragment on its own.

Two dedicated, metal-aware third-party tools can be selected instead for tougher
cases (both optional, both MIT-licensed -- installed via the ``reverse-tm`` extra,
not vendored):

* ``"xyz2mol_tm"`` -- the Jensen group's structure->SMILES converter for transition
  metal complexes. Yields a single, whole-complex RDKit-parsable SMILES (with the
  metal and dative bonds) which we attach as :attr:`ReversedComplex.complex_smiles`
  alongside the builtin per-ligand decomposition.
  Repo: https://github.com/jensengroup/xyz2mol_tm (MIT).
  Cite: "SMILES all around: structure to SMILES conversion for transition metal
  complexes", J. Cheminform. 2025, doi:10.1186/s13321-025-01008-1.

T-REX notation
--------------
Separately from SMILES, a complex can be rendered as a **T-REX** string -- a
canonical, geometry-aware language for transition metal complexes -- via
:func:`to_trex`. This wraps the ``trex`` package:
  Repo: https://github.com/iliak14/trex (MIT).
  Cite: Kevlishvili, "Taming T-REX: A Canonical Language for Geometry-Aware
  Generative Design of Transition Metal Complexes", ChemRxiv 2025,
  doi:10.26434/chemrxiv-2025-7s3gx.

m-SMILES
--------
:func:`to_msmiles` renders MetalloGen's isomer-exact m-SMILES input string
(Lee et al., J. Chem. Inf. Model. 2025, 65, 11878). It needs no optional package:
the site table lives in :mod:`mecobi.msmiles`, so it is always available.

All three optional tools are imported lazily and only when their backend/notation is
requested, so the core install keeps zero extra dependencies and the default
``"builtin"`` path never changes.
"""

from __future__ import annotations

import importlib.util
import math
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import rdDetermineBonds

from .optimize import _COV_RADIUS

# Non-metal / metalloid elements that appear as ligand atoms; everything else with
# Z > 2 is treated as the coordinating metal centre.
_NONMETAL = frozenset({
    "H", "He", "B", "C", "N", "O", "F", "Ne", "Si", "P", "S", "Cl", "Ar",
    "As", "Se", "Br", "Kr", "Te", "I", "Xe", "At", "Rn",
})
# Charges tried (in order) when perceiving a fragment's bond orders.
_TRIAL_CHARGES = (0, -1, 1, -2, 2, -3, 3)
# A non-metal atom within this multiple of the covalent bond length to the metal
# is counted as a donor.
_DONOR_TOLERANCE = 1.3


class ReverseError(RuntimeError):
    """Raised when an .xyz cannot be decomposed into a metal + ligands."""


@dataclass
class ReversedLigand:
    smiles: str
    donor_atoms: list[int] = field(default_factory=list)  # 0-based, in this SMILES
    charge: int = 0


@dataclass
class ReversedComplex:
    metal: str
    ligands: list[ReversedLigand]
    backend: str = "builtin"
    # Whole-complex SMILES (metal + dative bonds), populated by metal-aware
    # backends such as ``xyz2mol_tm``; None for the builtin per-ligand backend.
    complex_smiles: str | None = None
    # T-REX notation string, populated on demand by :func:`to_trex`.
    trex: str | None = None

    @property
    def coordination_number(self) -> int:
        return sum(len(l.donor_atoms) for l in self.ligands)

    def to_isomer_notation(self) -> str:
        """Donor-index notation for the recovered donors (see :mod:`mecobi.isomers`)."""
        return ";".join(
            f"{i}({','.join(str(a) for a in l.donor_atoms)})"
            for i, l in enumerate(self.ligands) if l.donor_atoms
        )

    def to_trex(self) -> str | None:
        """The T-REX notation, if it has been computed (see :func:`to_trex`)."""
        return self.trex


# --------------------------------------------------------------------------- #
# Perception backends. Each takes the raw .xyz text and returns a
# ReversedComplex. Selected by name so callers just pass a string.
# --------------------------------------------------------------------------- #

def available_backends() -> list[str]:
    """Perception backend names whose optional deps import cleanly.

    ``"builtin"`` (pure RDKit, always a dependency) is always present; metal-aware
    third-party backends appear only when their package is installed.
    """
    names = ["builtin"]
    if importlib.util.find_spec("xyz2mol_tm") is not None:
        names.append("xyz2mol_tm")
    return names


def available_notations() -> list[str]:
    """Complex-notation names available. ``"isomer"`` is always present; ``"trex"``
    appears only when the ``trex`` package is installed."""
    names = ["isomer"]
    if importlib.util.find_spec("trex") is not None:
        names.append("trex")
    return names


def reverse_xyz(
    source: str | Path,
    backend: str = "builtin",
    overall_charge: int | None = None,
) -> ReversedComplex:
    """Decompose a mononuclear metal-complex .xyz into metal + ligand SMILES.

    ``source`` is an .xyz file path or the raw text. ``backend`` selects the
    perception engine (see :func:`available_backends`). ``overall_charge`` (the
    complex's total charge) is required by the ``"xyz2mol_tm"`` backend and ignored
    by ``"builtin"``. Raises :class:`ReverseError` on failure.
    """
    text = _read_source(source)
    if backend == "builtin":
        return _reverse_builtin(text)
    if backend == "xyz2mol_tm":
        return _reverse_xyz2mol_tm(text, overall_charge)
    raise ReverseError(
        f"unknown backend {backend!r}; available: {available_backends()}"
    )


def _reverse_builtin(text: str) -> ReversedComplex:
    metal_el, _metal_pos, frags = _decompose(text)
    ligands = [
        ReversedLigand(smiles=Chem.MolToSmiles(mol), donor_atoms=sorted(donors), charge=charge)
        for mol, charge, donors, _groups in frags
    ]
    ligands.sort(key=lambda l: (l.smiles, tuple(l.donor_atoms)))
    return ReversedComplex(metal=metal_el, ligands=ligands, backend="builtin")


def _decompose(text: str):
    """Split an .xyz into its metal and perceived ligand fragments.

    Returns ``(metal, metal_pos, frags)`` with one ``(mol, charge, donors, groups)`` per
    fragment: ``mol`` the perceived heavy-atom molecule, ``donors`` its metal-bound atom
    indices and ``groups`` those donors split into binding sites (atoms bonded to each other,
    i.e. a haptic group, share a site), each site as ``(atom indices, centroid position)``.
    """
    atoms = _read_xyz_atoms(text)

    metal_idxs = [i for i, (el, _) in enumerate(atoms) if el not in _NONMETAL]
    if len(metal_idxs) != 1:
        raise ReverseError(
            f"expected exactly one metal atom, found {len(metal_idxs)} "
            f"({[atoms[i][0] for i in metal_idxs]}). Only mononuclear complexes are supported."
        )
    mi = metal_idxs[0]
    metal_el, metal_pos = atoms[mi]

    ligand_atoms = [(i, atoms[i]) for i in range(len(atoms)) if i != mi]
    if not ligand_atoms:
        raise ReverseError("no ligand atoms around the metal.")

    # Connectivity among the metal-free atoms -> one fragment per ligand.
    block = _xyz_block([a for _i, a in ligand_atoms])
    mol = Chem.MolFromXYZBlock(block)
    if mol is None:
        raise ReverseError("RDKit could not read the ligand geometry.")
    rdDetermineBonds.DetermineConnectivity(mol)

    # Two cis monodentate donors (e.g. cis halides) can sit close enough that the
    # covalent-distance rule wrongly bonds them into one fragment. Cut a direct
    # bond between two metal-donors when one is a terminal (monatomic) donor; this
    # splits them without touching chelate backbones or eta-bonded rings (whose
    # donor atoms have ring degree > 1).
    donor_block_idxs = {
        b for b, (_i, (el, pos)) in enumerate(ligand_atoms)
        if _is_bonded(metal_el, metal_pos, el, pos)
    }
    edit = Chem.RWMol(mol)
    to_cut = [
        (bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())
        for bond in mol.GetBonds()
        if bond.GetBeginAtomIdx() in donor_block_idxs
        and bond.GetEndAtomIdx() in donor_block_idxs
        and (mol.GetAtomWithIdx(bond.GetBeginAtomIdx()).GetDegree() == 1
             or mol.GetAtomWithIdx(bond.GetEndAtomIdx()).GetDegree() == 1)
    ]
    for a, b in to_cut:
        edit.RemoveBond(a, b)
    mol = edit.GetMol()

    frags = Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)
    frag_members = Chem.GetMolFrags(mol, asMols=False)

    out = []
    for frag, members in zip(frags, frag_members):
        mol, charge = _perceive_fragment_mol(frag)
        # Donor atoms: fragment atoms bonded to the metal by distance. `members`
        # maps this fragment's local atom order to the metal-free block index,
        # which (block order == ligand_atoms order) maps back to original atoms.
        donors_local = []
        for local, blk_idx in enumerate(members):
            orig_el, orig_pos = ligand_atoms[blk_idx][1]
            if _is_bonded(metal_el, metal_pos, orig_el, orig_pos):
                donors_local.append(local)
        heavy = _heavy_index_map(frag)
        groups = []
        for site in _bonded_groups(frag, donors_local):
            pos = [ligand_atoms[members[i]][1][1] for i in site]
            centroid = tuple(sum(c) / len(pos) for c in zip(*pos))
            groups.append((sorted(heavy[i] for i in site if i in heavy), centroid))
        donors = [heavy[i] for i in donors_local if i in heavy]
        out.append((mol, charge, donors, groups))
    return metal_el, metal_pos, out


def _reverse_xyz2mol_tm(text: str, overall_charge: int | None) -> ReversedComplex:
    """xyz -> whole-complex SMILES via the Jensen group's xyz2mol_tm (MIT).

    Reuses the builtin decomposition for the per-ligand SMILES + donor atoms, and
    attaches xyz2mol_tm's metal-aware whole-complex SMILES as ``complex_smiles``.
    """
    if overall_charge is None:
        raise ReverseError(
            "the 'xyz2mol_tm' backend needs overall_charge (the complex's total "
            "formal charge); it cannot be inferred from geometry alone."
        )
    get_tmc_mol = _import_xyz2mol_tm()
    rc = _reverse_builtin(text)
    rc.backend = "xyz2mol_tm"
    with _temp_xyz(_normalized_xyz(text)) as path:
        mol = get_tmc_mol(str(path), int(overall_charge), with_stereo=False)
    if mol is None:
        raise ReverseError("xyz2mol_tm could not perceive the complex.")
    # Round-trip through SMILES to canonicalise, mirroring the tool's own CLI.
    rc.complex_smiles = Chem.MolToSmiles(Chem.MolFromSmiles(Chem.MolToSmiles(mol)))
    return rc


def to_trex(source: str | Path, overall_charge: int) -> str:
    """Render a complex .xyz as a canonical T-REX notation string.

    Wraps the ``trex`` package (Kevlishvili, MIT; doi:10.26434/chemrxiv-2025-7s3gx).
    ``source`` is an .xyz path or raw text; ``overall_charge`` is the complex's total
    formal charge (required by trex, and not inferable from geometry). Raises
    :class:`ReverseError` if the package is not installed or perception fails.
    """
    if overall_charge is None:
        raise ReverseError(
            "T-REX notation needs overall_charge (the complex's total formal "
            "charge); it cannot be inferred from geometry alone."
        )
    xyz_to_trex, canonicalize = _import_trex()
    text = _read_source(source)
    with _temp_xyz(_normalized_xyz(text)) as path:
        try:
            # trex canonicalises internally when handed the canonicalise fn.
            raw = xyz_to_trex(str(path), int(overall_charge), canonicalize_fn=canonicalize)
        except Exception as exc:  # noqa: BLE001 - surface any trex failure uniformly
            raise ReverseError(f"trex could not convert the structure: {exc}") from exc
    if not raw:
        raise ReverseError("trex returned an empty notation.")
    return raw


def to_msmiles(source: str | Path, overall_charge: int) -> str:
    """Render a complex .xyz as a MetalloGen m-SMILES string (see :mod:`mecobi.msmiles`).

    Built-in (no optional dependency): the builtin decomposition gives the ligands and
    their metal-bound atoms; each binding site (one donor, or one haptic group) is
    matched to MetalloGen's closest ideal geometry and its atoms are labelled with the
    1-based site number, so the string fixes the isomer as well as the connectivity.
    The metal charge is ``overall_charge`` minus the perceived ligand charges.
    """
    from . import msmiles

    if overall_charge is None:
        raise ReverseError(
            "m-SMILES needs overall_charge (the complex's total formal charge) to "
            "assign the metal's charge; it cannot be inferred from geometry alone."
        )
    metal, metal_pos, frags = _decompose(_read_source(source))
    unbound = [Chem.MolToSmiles(mol) for mol, _q, donors, _g in frags if not donors]
    if unbound:
        raise ReverseError(
            f"fragment(s) {unbound} are not bound to the metal; m-SMILES describes only "
            "the coordination sphere (remove counter-ions or solvent from the .xyz)."
        )
    sites = [(fi, atoms, pos) for fi, (_m, _q, _d, groups) in enumerate(frags)
             for atoms, pos in groups]
    directions = [tuple(p - m for p, m in zip(pos, metal_pos)) for _fi, _a, pos in sites]
    try:
        geometry, site_of, _rmsd = msmiles.match_shape(directions)
    except ValueError as exc:
        raise ReverseError(str(exc)) from exc
    mols = [Chem.Mol(mol) for mol, *_ in frags]
    for (fi, atoms, _pos), site in zip(sites, site_of):
        for a in atoms:
            mols[fi].GetAtomWithIdx(a).SetAtomMapNum(site + 1)
    metal_charge = int(overall_charge) - sum(q for _m, q, _d, _g in frags)
    ligands = sorted(Chem.MolToSmiles(m) for m in mols)
    return "|".join([msmiles.metal_token(metal, metal_charge), *ligands, geometry])


# --------------------------------------------------------------------------- #
# Optional-dependency imports. Lazy, with actionable install + citation messages.
# --------------------------------------------------------------------------- #

def _import_xyz2mol_tm():
    try:
        from xyz2mol_tm.huckel_to_smiles.xyz2mol_tmc import get_tmc_mol
    except Exception as exc:  # noqa: BLE001 - any import failure -> guidance
        raise ReverseError(
            "backend 'xyz2mol_tm' requires the xyz2mol_tm package (MIT, Jensen "
            "group). Install with: pip install 'mecobi[reverse-tm]'  (or: pip "
            "install git+https://github.com/jensengroup/xyz2mol_tm). Cite: 'SMILES "
            "all around', J. Cheminform. 2025, doi:10.1186/s13321-025-01008-1."
        ) from exc
    return get_tmc_mol


def _import_trex():
    try:
        from trex.xyz_to_trex import xyz_to_trex
    except Exception as exc:  # noqa: BLE001
        raise ReverseError(
            "T-REX notation requires the trex package (MIT, Kevlishvili). Install "
            "with: pip install 'mecobi[reverse-tm]'  (or: pip install "
            "git+https://github.com/iliak14/trex). Cite: 'Taming T-REX', ChemRxiv "
            "2025, doi:10.26434/chemrxiv-2025-7s3gx."
        ) from exc
    try:
        from trex.parse_full import canonicalize_trex_full_string as canonicalize
    except Exception:  # noqa: BLE001 - canonicalisation is optional
        canonicalize = None
    return xyz_to_trex, canonicalize


@contextmanager
def _temp_xyz(text: str):
    """Write xyz text to a temp file (the third-party tools take file paths).

    Uses close-then-reopen so it works on Windows, and always unlinks.
    """
    fd, name = tempfile.mkstemp(suffix=".xyz")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        yield Path(name)
    finally:
        try:
            os.unlink(name)
        except OSError:
            pass


# --------------------------------------------------------------------------- #
# Shared helpers (unchanged behaviour).
# --------------------------------------------------------------------------- #

def _read_source(source: str | Path) -> str:
    return Path(source).read_text() if _looks_like_path(source) else str(source)


def _normalized_xyz(text: str) -> str:
    """Re-emit an .xyz as clean ``element x y z`` lines with an empty comment.

    The third-party tools unpack each atom line into exactly four fields, so any
    extra columns (e.g. an xtb gradient/force triple) or a token-heavy comment line
    make them raise "too many values to unpack". Our own reader keeps only the first
    four fields, so round-tripping through it guarantees a format they accept.
    """
    return _xyz_block(_read_xyz_atoms(text))


# --------------------------------------------------------------------------- #
# Representation registry. One entry per notation the reverse command can emit;
# drives the CSV export and the web menu, so a newly published notation is added
# here in one place (name + how to render it) and appears everywhere.
# --------------------------------------------------------------------------- #

def available_representations() -> list[dict]:
    """Installed complex-level representations, as ``{key, label, ref, cite}`` dicts,
    in a stable display order. ``ref`` is a short author tag shown in the UI, ``cite``
    the full citation (hover text). Each requires the ``overall_charge`` to render."""
    reps: list[dict] = []
    if importlib.util.find_spec("xyz2mol_tm") is not None:
        reps.append({
            "key": "complex_smiles", "label": "Complex SMILES",
            "ref": "Jensen et al.",
            "cite": "SMILES all around, J. Cheminform. 2025, doi:10.1186/s13321-025-01008-1",
        })
    if importlib.util.find_spec("trex") is not None:
        reps.append({
            "key": "trex", "label": "T-REX notation",
            "ref": "Kevlishvili et al.",
            "cite": "Taming T-REX, ChemRxiv 2025, doi:10.26434/chemrxiv-2025-7s3gx",
        })
    reps.append({
        "key": "msmiles", "label": "m-SMILES (MetalloGen)",
        "ref": "Lee et al.",
        "cite": "MetalloGen: Automated 3D Conformer Generation for Diverse Coordination "
                "Complexes, J. Chem. Inf. Model. 2025, 65, 11878-11891",
    })
    return reps


def render_representation(source: str | Path, key: str, overall_charge: int) -> str:
    """Render one representation of a structure by its registry ``key``."""
    if key == "complex_smiles":
        rc = reverse_xyz(source, backend="xyz2mol_tm", overall_charge=overall_charge)
        return rc.complex_smiles or ""
    if key == "trex":
        return to_trex(source, overall_charge)
    if key == "msmiles":
        return to_msmiles(source, overall_charge)
    raise ReverseError(
        f"unknown representation {key!r}; available: "
        f"{[r['key'] for r in available_representations()]}"
    )


def _read_xyz_atoms(text: str) -> list[tuple[str, tuple[float, float, float]]]:
    lines = text.splitlines()
    n = int(lines[0].strip())
    atoms = []
    for line in lines[2:2 + n]:
        p = line.split()
        atoms.append((p[0], (float(p[1]), float(p[2]), float(p[3]))))
    if len(atoms) != n:
        raise ReverseError(f"xyz declares {n} atoms but has {len(atoms)}.")
    return atoms


def _xyz_block(atoms: list[tuple[str, tuple[float, float, float]]]) -> str:
    body = "\n".join(f"{el} {x:.6f} {y:.6f} {z:.6f}" for el, (x, y, z) in atoms)
    return f"{len(atoms)}\n\n{body}\n"


def _perceive_fragment_mol(frag: Chem.Mol) -> tuple[Chem.Mol, int]:
    """Heavy-atom molecule + total charge of one ligand fragment, trying candidate charges.

    Returns the first charge whose bond-order perception yields a sanitisable
    molecule; falls back to the connectivity-only structure if none do. Hydrogen
    removal keeps the heavy atoms in fragment order (see :func:`_heavy_index_map`).
    """
    # A lone halogen atom is a halide anion, not a neutral radical (which charge 0
    # would otherwise "successfully" perceive) -- matches the forward pipeline's
    # bare-halide normalisation.
    heavy = [a for a in frag.GetAtoms() if a.GetAtomicNum() > 1]
    if len(heavy) == 1 and heavy[0].GetSymbol() in ("F", "Cl", "Br", "I"):
        return Chem.MolFromSmiles(f"[{heavy[0].GetSymbol()}-]"), -1
    for charge in _TRIAL_CHARGES:
        trial = Chem.Mol(frag)
        try:
            rdDetermineBonds.DetermineBonds(trial, charge=charge)
            Chem.SanitizeMol(trial)
        except (ValueError, RuntimeError, Chem.KekulizeException):
            continue
        return Chem.RemoveHs(trial), charge
    # No charge worked: return the connectivity-only structure (single bonds).
    return Chem.RemoveHs(frag), 0


def _is_bonded(m_el, m_pos, a_el, a_pos) -> bool:
    r_m = _COV_RADIUS.get(m_el, 1.5)
    r_a = _COV_RADIUS.get(a_el, 0.77)
    return math.dist(m_pos, a_pos) <= _DONOR_TOLERANCE * (r_m + r_a)


def _heavy_index_map(frag: Chem.Mol) -> dict[int, int]:
    """Fragment atom index (with H) -> index in the perceived heavy-atom molecule.

    That molecule comes from ``RemoveHs``, which keeps heavy atoms in order; a donor
    is always a heavy atom, so its index is its position among the non-H atoms.
    """
    heavy_order = [a.GetIdx() for a in frag.GetAtoms() if a.GetAtomicNum() > 1]
    return {idx: rank for rank, idx in enumerate(heavy_order)}


def _bonded_groups(frag: Chem.Mol, idxs: list[int]) -> list[list[int]]:
    """Split ``idxs`` into groups connected by bonds among themselves (haptic sites)."""
    todo, groups = set(idxs), []
    while todo:
        stack, group = [min(todo)], []
        todo.discard(stack[0])
        while stack:
            i = stack.pop()
            group.append(i)
            for nb in frag.GetAtomWithIdx(i).GetNeighbors():
                if nb.GetIdx() in todo:
                    todo.discard(nb.GetIdx())
                    stack.append(nb.GetIdx())
        groups.append(sorted(group))
    return sorted(groups)


def _looks_like_path(source: str | Path) -> bool:
    if isinstance(source, Path):
        return True
    return "\n" not in source and len(source) < 260 and source.strip().lower().endswith(".xyz")
