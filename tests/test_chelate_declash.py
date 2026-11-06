"""Chelate repair (on by default, MECOBI_DECLASH=0 turns it off): gate 5-membered chelate rings by the
ring-centroid test, flatten inside-out conjugated rings, turn donor substituents exo and
de-clash substituent torsions, WITHOUT moving any donor (HOLMEC, XUVZOE)."""

import numpy as np

from mecobi import chelate_fix, pipeline
from mecobi.model import Complex, Geometry, Ligand, Metal

DAD = "CC(C)c1cccc(C(C)C)c1[N-]C=C[N-]c1c(C(C)C)cccc1C(C)C"   # HOLMEC ene-diamide


def _raw(cx, geom):
    from mecobi import assembly
    from mecobi.pipeline import resolve_perception

    resolve_perception(cx)
    spec = assembly.default_isomer(cx, geom)
    if spec.site_based:
        return assembly.build_from_sites(cx, geom, dict(spec.assignment), mchammer=False)[0]
    return assembly.build(cx, spec, mchammer=False)[0]


def _holmec_raw():
    cx = Complex(metal=Metal("Ti", 4), ligands=[
        Ligand(DAD, donor_override=[13, 16], denticity=2),
        Ligand(DAD, donor_override=[13, 16], denticity=2)])
    return _raw(cx, Geometry.TETRAHEDRAL)


def test_repair_never_moves_a_donor_and_turns_rings_right_way_round():
    raw = _holmec_raw()
    mi, don = pipeline._metal_bonded_donors(raw, "Ti")
    out, rep = chelate_fix.repair_chelates(raw, "Ti")
    before = np.asarray(raw.get_position_matrix(), float)
    after = np.asarray(out.get_position_matrix(), float)
    assert np.allclose(before[don], after[don]) and np.allclose(before[mi], after[mi])
    if rep["changed"]:
        assert all(off > 0.3 for off in chelate_fix.ring_offsets(out, "Ti"))
        assert sum(pipeline._hard_overlaps(out, "Ti")) == 0


def test_correct_rings_are_left_alone():
    acac = "CC(=O)/C=C(/[O-])C"   # 6-membered ring: never gated
    cx = Complex(metal=Metal("Ni", 2), ligands=[Ligand(acac, donor_override=[2, 5], denticity=2),
                                                Ligand(acac, donor_override=[2, 5], denticity=2)])
    raw = _raw(cx, Geometry.SQUARE_PLANAR)
    assert chelate_fix.ring_offsets(raw, "Ni") == []
    out, rep = chelate_fix.repair_chelates(raw, "Ni")
    assert rep["rings_fixed"] == 0 and rep["exo_fixed"] == 0


def test_repair_can_be_switched_off(monkeypatch):
    monkeypatch.setenv("MECOBI_DECLASH", "0")
    called = []
    monkeypatch.setattr(chelate_fix, "repair_chelates",
                        lambda c, s, **k: called.append(1) or (c, {"changed": False}))
    raw = _holmec_raw()
    pipeline._build_with_fallback(lambda m: (raw, "x"), "Ti", Geometry.TETRAHEDRAL, True)
    assert not called
