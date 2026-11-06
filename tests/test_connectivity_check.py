"""Pilot-100 fixes: (1) group-3 spin d-count (Sc/Y no longer fall back to uhf=0),
(2) the post-relaxation connectivity guard that flags ligand-ligand fusion /
fragmentation / collapse (pipeline._new_or_broken_bonds)."""
from mecobi import pipeline
from mecobi.spin import d_electron_count


def test_group3_metals_resolve_d_count():
    # Was: SpinError "No group number for metal 'Y'" -> uhf=0 fallback (JORXUM).
    assert d_electron_count("Y", 3) == 0   # Y(III) d0
    assert d_electron_count("Sc", 3) == 0   # Sc(III) d0
    assert d_electron_count("La", 3) == 0


def _xyz(tmp_path, atoms):
    lines = [str(len(atoms)), ""]
    for el, x, y, z in atoms:
        lines.append(f"{el} {x} {y} {z}")
    p = tmp_path / "s.xyz"
    p.write_text("\n".join(lines) + "\n")
    return p


def test_connectivity_flags_ligand_fusion(tmp_path):
    # Fe + two carbons that end up 1.4 A apart -> a NEW C-C bond that was not assembled
    # (the WIMCEA/CBFMOP-style fusion the M-L restraint cannot prevent).
    xyz = _xyz(tmp_path, [("Fe", 0, 0, 0), ("C", 2.0, 0, 0), ("C", 2.0, 1.4, 0)])
    new, broken = pipeline._new_or_broken_bonds([(0, 1), (0, 2)], xyz, metal_index=0)
    assert [lbl for *_, lbl in new] == ["C-C"]
    assert not broken


def test_connectivity_flags_fragmentation(tmp_path):
    # An assembled C-C bond stretched to 3.0 A -> fragmentation (LAFQUE-style).
    xyz = _xyz(tmp_path, [("Fe", 0, 0, 0), ("C", 2.0, 0, 0), ("C", 2.0, 3.0, 0)])
    new, broken = pipeline._new_or_broken_bonds([(0, 1), (0, 2), (1, 2)], xyz, metal_index=0)
    assert [lbl for *_, lbl in broken] == ["C-C"]
    assert not new


def test_connectivity_ok_when_graph_preserved(tmp_path):
    # Fe-C0 (metal bond, ignored) + C0-C1 assembled at 1.4 A (bonded) -> no change.
    xyz = _xyz(tmp_path, [("Fe", 0, 0, 0), ("C", 2.0, 0, 0), ("C", 3.4, 0, 0)])
    new, broken = pipeline._new_or_broken_bonds([(0, 1), (1, 2)], xyz, metal_index=0)
    assert not new and not broken


def test_connectivity_ignores_metal_and_hydrogen(tmp_path):
    # A donor at a long M-L distance (2.9 A, would look 'unbonded') and an H near the
    # metal must NOT be reported -- the metal's bonds are the dissociation guard's job,
    # and H is excluded as noisy.
    xyz = _xyz(tmp_path, [("Fe", 0, 0, 0), ("N", 2.9, 0, 0), ("H", 1.0, 0, 0)])
    new, broken = pipeline._new_or_broken_bonds([(0, 1)], xyz, metal_index=0)
    assert not new and not broken
