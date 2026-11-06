"""Extra output formats (.mol / .pdb) from the assembled graph — mecobi.export.

Bonds come from the assembled topology (never perceived from geometry), coordinates from the
built .xyz. The unit tests drive a duck-typed stand-in for the stk molecule (the same tiny API the
real path uses: ``get_atoms`` / ``get_bonds`` / ``get_atomic_number`` / ``get_id`` / ``get_charge``
/ ``get_order`` / ``get_atom1`` / ``get_atom2``), so they need no stk/xtb/perception and stay fast.
"""
import pytest

from mecobi import export


class _Atom:
    def __init__(self, z, idx, charge=0):
        self._z, self._id, self._c = z, idx, charge

    def get_atomic_number(self):
        return self._z

    def get_id(self):
        return self._id

    def get_charge(self):
        return self._c


class _Bond:
    def __init__(self, a, b, order=1):
        self._a, self._b, self._o = a, b, order

    def get_atom1(self):
        return self._a

    def get_atom2(self):
        return self._b

    def get_order(self):
        return self._o


class _Mol:
    def __init__(self, atoms, bonds):
        self._atoms, self._bonds = atoms, bonds

    def get_atoms(self):
        return list(self._atoms)

    def get_bonds(self):
        return list(self._bonds)


def _cisplatin_core():
    """A square-planar Pt(NH3-N)2Cl2 core: metal + 2 anionic Cl + 2 N, all M-L single bonds."""
    a = [_Atom(78, 0), _Atom(17, 1, charge=-1), _Atom(17, 2, charge=-1), _Atom(7, 3), _Atom(7, 4)]
    bonds = [_Bond(a[0], a[1]), _Bond(a[0], a[2]), _Bond(a[0], a[3]), _Bond(a[0], a[4])]
    coords = [(0.0, 0.0, 0.0), (2.3, 0.0, 0.0), (-2.3, 0.0, 0.0),
              (0.0, 2.0, 0.0), (0.0, -2.0, 0.0)]
    return _Mol(a, bonds), coords


def _write_xyz(path, symbols, coords):
    lines = [str(len(symbols)), "test"]
    lines += [f"{s} {x:.4f} {y:.4f} {z:.4f}" for s, (x, y, z) in zip(symbols, coords)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# normalize_formats
# --------------------------------------------------------------------------- #

def test_normalize_dedupes_and_keeps_xyz_first():
    assert export.normalize_formats(["pdb", "mol", "pdb"]) == ("xyz", "pdb", "mol")


def test_normalize_always_includes_xyz():
    assert export.normalize_formats(["mol"]) == ("xyz", "mol")
    assert export.normalize_formats([]) == ("xyz",)


def test_normalize_is_case_and_space_insensitive():
    assert export.normalize_formats([" MOL ", "XYZ"]) == ("xyz", "mol")


def test_normalize_rejects_unknown_format():
    with pytest.raises(ValueError, match="sdf"):
        export.normalize_formats(["xyz", "sdf"])


# --------------------------------------------------------------------------- #
# write_formats
# --------------------------------------------------------------------------- #

def test_xyz_only_writes_nothing_extra(tmp_path):
    mol, coords = _cisplatin_core()
    xyz = tmp_path / "cis.xyz"
    _write_xyz(xyz, ["Pt", "Cl", "Cl", "N", "N"], coords)
    written = export.write_formats(mol, xyz, ["xyz"])
    assert written == [xyz]
    assert not (tmp_path / "cis.mol").exists()
    assert not (tmp_path / "cis.pdb").exists()


def test_writes_mol_with_assembled_connectivity(tmp_path):
    from rdkit import Chem

    mol, coords = _cisplatin_core()
    xyz = tmp_path / "cis.xyz"
    _write_xyz(xyz, ["Pt", "Cl", "Cl", "N", "N"], coords)
    written = export.write_formats(mol, xyz, ["xyz", "mol"])
    molfile = tmp_path / "cis.mol"
    assert molfile in written and molfile.exists()
    # Bonds are the assembled M-L bonds, not re-perceived from geometry.
    rd = Chem.MolFromMolFile(str(molfile), sanitize=False)
    assert rd is not None
    assert rd.GetNumAtoms() == 5
    assert rd.GetNumBonds() == 4
    assert rd.GetAtomWithIdx(0).GetSymbol() == "Pt"
    # Coordinates round-trip from the .xyz.
    pos = rd.GetConformer().GetAtomPosition(1)
    assert abs(pos.x - 2.3) < 1e-3


def test_writes_pdb_with_conect_for_metal_bonds(tmp_path):
    mol, coords = _cisplatin_core()
    xyz = tmp_path / "cis.xyz"
    _write_xyz(xyz, ["Pt", "Cl", "Cl", "N", "N"], coords)
    written = export.write_formats(mol, xyz, ["pdb"])
    pdb = tmp_path / "cis.pdb"
    assert pdb in written and pdb.exists()
    text = pdb.read_text()
    # The metal must carry CONECT records, or a viewer shows it as an isolated dot.
    assert "CONECT" in text
    assert text.count("HETATM") == 5
    assert "PT" in text.upper()
