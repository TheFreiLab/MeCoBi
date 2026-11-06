"""Extra output formats (.mol, .pdb) for a built complex.

The forward pipeline writes .xyz by default. Because MeCoBi *assembles* the complex it
already holds exact connectivity (the stk topology's bonds), so a molfile / PDB is written
straight from that graph — never re-perceived from geometry, which is unreliable for the
dative metal-ligand contacts of a coordination sphere (the very problem that forces
:mod:`mecobi.reverse` to strip the metal before perceiving). Coordinates come from the
finished .xyz (post-relax if relaxation ran); bonds and bond orders come from the assembled
molecule, aligned by atom index (stk writes atoms in id order, and xtb preserves that order).

Caveats, by design:
* A metal-ligand bond is written as a single (order-1) bond — a V2000 molfile has no dative
  bond type, and keeping M-L as an ordinary bond leaves the metal in one connected molecule so
  the PDB CONECT records and the mol connectivity are complete.
* No sanitisation runs (a coordination centre routinely breaks RDKit's valence model), so the
  files carry connectivity + geometry, not a rigorous bond-order/charge perception.
"""

from __future__ import annotations

from pathlib import Path

from ._text import noun

# Formats the exporter can emit. "xyz" is the pipeline's native output (already on disk); the
# others are derived from the assembled graph. Kept as the single source of truth for the CLI
# --format validation and the web build.
SUPPORTED_FORMATS = ("xyz", "mol", "pdb")
DEFAULT_FORMATS = ("xyz",)


def normalize_formats(formats) -> tuple[str, ...]:
    """Validate/dedupe a format list, preserving order and always keeping ``xyz`` first.

    Raises ``ValueError`` naming the unsupported token(s), so a CLI ``--format`` typo fails
    with an actionable message instead of silently writing nothing.
    """
    seen: list[str] = []
    bad: list[str] = []
    for f in formats:
        f = f.strip().lower()
        if not f:
            continue
        if f not in SUPPORTED_FORMATS:
            bad.append(f)
        elif f not in seen:
            seen.append(f)
    if bad:
        raise ValueError(
            f"unsupported output {noun(len(bad), 'format')}: {', '.join(bad)}. "
            f"Choose from: {', '.join(SUPPORTED_FORMATS)}."
        )
    # xyz is the native output and the connectivity is derived from it; keep it first/always.
    if "xyz" not in seen:
        seen.insert(0, "xyz")
    else:
        seen.remove("xyz")
        seen.insert(0, "xyz")
    return tuple(seen)


def _rdkit_mol_from_topology(constructed, coords):
    """An RDKit ``Mol`` with the assembled bonds/orders and the supplied coordinates.

    ``coords`` is ``[(x, y, z), ...]`` in atom-index order (i.e. the .xyz order, which matches
    ``constructed.get_atoms()``). No sanitisation — the metal's valence would trip it — but ring
    info and property caches are populated (best-effort) so the writers don't choke.
    """
    from rdkit import Chem
    from rdkit.Geometry import Point3D

    _ORDER = {1: Chem.BondType.SINGLE, 2: Chem.BondType.DOUBLE, 3: Chem.BondType.TRIPLE}
    rw = Chem.RWMol()
    for a in constructed.get_atoms():
        atom = Chem.Atom(a.get_atomic_number())
        # Best-effort formal charge from stk (captures e.g. an anionic chloride/alkoxide donor);
        # not guaranteed to sum to the complex charge, and irrelevant to the geometry we emit.
        try:
            atom.SetFormalCharge(int(a.get_charge()))
        except Exception:  # noqa: BLE001  (stk API/charge missing -> leave neutral)
            pass
        rw.AddAtom(atom)
    for b in constructed.get_bonds():
        rw.AddBond(b.get_atom1().get_id(), b.get_atom2().get_id(),
                   _ORDER.get(b.get_order(), Chem.BondType.SINGLE))
    mol = rw.GetMol()
    conf = Chem.Conformer(mol.GetNumAtoms())
    for i, (x, y, z) in enumerate(coords):
        conf.SetAtomPosition(i, Point3D(float(x), float(y), float(z)))
    mol.AddConformer(conf, assignId=True)
    mol.UpdatePropertyCache(strict=False)  # implicit valences without enforcing them (metal!)
    Chem.FastFindRings(mol)                 # ring perception only; no aromaticity/valence checks
    return mol


def write_formats(constructed, xyz_path, formats) -> list[Path]:
    """Write the requested ``formats`` for one built complex; return the paths written.

    ``xyz_path`` is the .xyz the pipeline already wrote (post-relax geometry); ``.mol`` / ``.pdb``
    are written beside it with the same stem. ``xyz`` is a no-op (already on disk) but is included
    in the returned list so callers get the full set. Bonds come from ``constructed``; coordinates
    are re-read from ``xyz_path`` so the relaxed geometry is what lands in every format.
    """
    from . import optimize

    xyz_path = Path(xyz_path)
    fmts = normalize_formats(formats)
    written: list[Path] = [xyz_path]
    if fmts == ("xyz",):
        return written

    from rdkit import Chem

    coords = [p for _el, p in optimize._read_xyz(xyz_path)]
    mol = _rdkit_mol_from_topology(constructed, coords)
    if "mol" in fmts:
        p = xyz_path.with_suffix(".mol")
        Chem.MolToMolFile(mol, str(p), kekulize=False)
        written.append(p)
    if "pdb" in fmts:
        p = xyz_path.with_suffix(".pdb")
        # flavor=4 -> CONECT records in both directions, so every M-L bond is recorded and viewers
        # (PyMOL/VMD) draw the coordination sphere instead of leaving the metal an isolated dot.
        Chem.MolToPDBFile(mol, str(p), flavor=4)
        written.append(p)
    return written
