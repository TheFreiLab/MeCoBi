"""MetalloGen m-SMILES export (reverse direction): site table, shape fit, string assembly."""

from pathlib import Path

import numpy as np
import pytest
from rdkit import Chem

from mecobi import msmiles, reverse


def _ammine(n_pos, out):
    """NH3 on the metal at ``n_pos`` (an axis direction scaled to 2.05 A), Hs pointing away."""
    n = np.asarray(n_pos, float)
    u = n / np.linalg.norm(n)
    a = np.cross(u, [0.0, 0.0, 1.0] if abs(u[2]) < 0.9 else [1.0, 0.0, 0.0])
    a /= np.linalg.norm(a)
    b = np.cross(u, a)
    out.append(("N", n))
    for k in range(3):
        t = 2 * np.pi * k / 3
        out.append(("H", n + 0.34 * u + 0.95 * (np.cos(t) * a + np.sin(t) * b)))


def _xyz(atoms):
    body = "\n".join(f"{el} {x:.4f} {y:.4f} {z:.4f}" for el, (x, y, z) in atoms)
    return f"{len(atoms)}\n\n{body}\n"


def _pt_diammine_dichloride(cis: bool) -> str:
    atoms = [("Pt", (0.0, 0.0, 0.0))]
    _ammine((2.05, 0, 0), atoms)
    _ammine((0, 2.05, 0) if cis else (-2.05, 0, 0), atoms)
    for pos in ([(0, -2.3, 0), (-2.3, 0, 0)] if cis else [(0, 2.3, 0), (0, -2.3, 0)]):
        atoms.append(("Cl", pos))
    return _xyz(atoms)


def _ferrocene() -> str:
    atoms = [("Fe", (0.0, 0.0, 0.0))]
    for z, phase in ((1.65, 0.0), (-1.65, np.pi / 5)):
        for k in range(5):
            t = 2 * np.pi * k / 5 + phase
            atoms.append(("C", (1.21 * np.cos(t), 1.21 * np.sin(t), z)))
            atoms.append(("H", (2.29 * np.cos(t), 2.29 * np.sin(t), z * 1.03)))
    return _xyz(atoms)


def _sites(ms: str) -> tuple[str, str, dict[int, list[str]]]:
    """(metal token, geometry, {site number: donor symbols}) of an m-SMILES string."""
    parts = ms.split("|")
    sites: dict[int, list[str]] = {}
    for smi in parts[1:-1]:
        mol = Chem.MolFromSmiles(smi)
        assert mol is not None, smi
        for atom in mol.GetAtoms():
            if atom.GetAtomMapNum():
                sites.setdefault(atom.GetAtomMapNum(), []).append(atom.GetSymbol())
    return parts[0], parts[-1], sites


def _trans(geometry: str, a: int, b: int) -> bool:
    v = msmiles._unit(msmiles.GEOMETRY_VECTORS[geometry])
    return float(v[a - 1] @ v[b - 1]) < -0.99


def test_usable_geometries_skip_invalid_upstream_entries():
    # Upstream lists 9 vectors for a CN-8 shape and repeats one in a CN-7 shape.
    assert "8_bicapped_trigonal_prismatic" not in msmiles.usable_geometries(8)
    assert "7_capped_octahedral" not in msmiles.usable_geometries(7)
    assert "6_octahedral" in msmiles.usable_geometries(6)
    assert msmiles.usable_geometries(11) == ()


def test_match_shape_recovers_rotated_octahedron_site_by_site():
    ideal = msmiles._unit(msmiles.GEOMETRY_VECTORS["6_octahedral"])
    q, _ = np.linalg.qr(np.random.default_rng(1).standard_normal((3, 3)))
    if np.linalg.det(q) < 0:
        q[:, 0] = -q[:, 0]
    geometry, site_of, rmsd = msmiles.match_shape(ideal @ q.T)
    assert geometry == "6_octahedral" and rmsd < 1e-6
    # Each direction lands on its own site or on one related by the polyhedron's symmetry,
    # so trans pairs (0/1, 2/3, 4/5 in the upstream order) must stay trans.
    for a, b in ((0, 1), (2, 3), (4, 5)):
        assert _trans(geometry, site_of[a] + 1, site_of[b] + 1)


def test_match_shape_rejects_cn_without_metallogen_geometry():
    with pytest.raises(ValueError, match="coordination number 11"):
        msmiles.match_shape(np.random.default_rng(0).standard_normal((11, 3)))


@pytest.mark.parametrize("cis", [True, False])
def test_msmiles_encodes_cis_trans_isomer(cis):
    ms = reverse.to_msmiles(_pt_diammine_dichloride(cis), overall_charge=0)
    metal, geometry, sites = _sites(ms)
    assert metal == "[Pt+2]" and geometry == "4_square_planar"
    cl = [s for s, els in sites.items() if els == ["Cl"]]
    n = [s for s, els in sites.items() if els == ["N"]]
    assert sorted(sites) == [1, 2, 3, 4] and len(cl) == 2 and len(n) == 2
    assert _trans(geometry, *cl) is (not cis)
    assert _trans(geometry, *n) is (not cis)


def test_msmiles_haptic_ring_shares_one_site():
    ms = reverse.to_msmiles(_ferrocene(), overall_charge=0)
    metal, geometry, sites = _sites(ms)
    assert metal == "[Fe+2]" and geometry == "2_linear"
    assert sorted(sites) == [1, 2]
    assert all(els == ["C"] * 5 for els in sites.values())


def test_msmiles_metal_charge_follows_overall_charge():
    ms = reverse.to_msmiles(_pt_diammine_dichloride(True), overall_charge=2)
    assert ms.startswith("[Pt+4]|")


def test_msmiles_needs_charge_and_a_bound_sphere():
    with pytest.raises(reverse.ReverseError, match="overall_charge"):
        reverse.to_msmiles(_ferrocene(), overall_charge=None)
    lattice_water = _xyz([("Zn", (0, 0, 0)), ("Cl", (2.2, 0, 0)), ("Cl", (-2.2, 0, 0)),
                          ("O", (0, 6.0, 0)), ("H", (0.76, 6.6, 0)), ("H", (-0.76, 6.6, 0))])
    with pytest.raises(reverse.ReverseError, match="not bound to the metal"):
        reverse.to_msmiles(lattice_water, overall_charge=0)


def test_msmiles_is_a_registered_representation():
    keys = [r["key"] for r in reverse.available_representations()]
    assert "msmiles" in keys  # built in: present without the reverse-tm extra
    ms = reverse.render_representation(_pt_diammine_dichloride(False), "msmiles", 0)
    assert ms.endswith("|4_square_planar")


@pytest.mark.slow
def test_msmiles_roundtrip_mecobi_build_keeps_isomer(tmp_path):
    # The use case: a structure MeCoBi built. Each Cl-M-Cl relationship in the m-SMILES
    # must match the built geometry (trans <=> ~180 degrees between the two chlorides).
    from mecobi import pipeline
    from mecobi.model import Complex, Geometry, Ligand, Metal

    bipy = "c1ccc(-c2ccccn2)nc1"
    cx = Complex(metal=Metal("Ir", 3), geometry=Geometry.OCTAHEDRAL,
                 ligands=[Ligand(bipy), Ligand(bipy), Ligand("[Cl-]"), Ligand("[Cl-]")])
    for res in pipeline.build_complex(cx, tmp_path, relax=False):
        text = Path(res.xyz_path).read_text()
        atoms = reverse._read_xyz_atoms(text)
        ir = np.array(next(p for el, p in atoms if el == "Ir"))
        cl = [np.array(p) - ir for el, p in atoms if el == "Cl"]
        built_trans = bool(cl[0] @ cl[1] / (np.linalg.norm(cl[0]) * np.linalg.norm(cl[1])) < -0.9)

        metal, geometry, sites = _sites(reverse.to_msmiles(text, overall_charge=1))
        assert metal == "[Ir+3]" and geometry == "6_octahedral"
        assert sorted(sites) == [1, 2, 3, 4, 5, 6]
        cl_sites = [s for s, els in sites.items() if els == ["Cl"]]
        assert _trans(geometry, *cl_sites) is built_trans
