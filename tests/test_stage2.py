"""Stage 2 tests: topology registry + assembly (fast) and full build (slow)."""

from pathlib import Path

import pytest

from mecobi import assembly, geometry, inputs, pipeline
from mecobi.assembly import registry
from mecobi.model import Complex, Geometry, Ligand, Metal

REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_CSV = Path(__file__).resolve().parent / "fixtures" / "test_compounds.csv"


# --------------------------------------------------------------------------- #
# registry + default isomer — fast, no model/stk build
# --------------------------------------------------------------------------- #

def test_registry_lookup_by_partition():
    e = registry.lookup(Geometry.OCTAHEDRAL, [1, 2, 1, 2])  # unsorted -> (2,2,1,1)
    assert e.label == "octa_2bi2mono"
    assert e.n_sites == 6
    assert e.vertex_denticities == (2, 2, 1, 1)


def test_registry_unregistered_partition_raises():
    with pytest.raises(KeyError):
        registry.lookup(Geometry.OCTAHEDRAL, [1, 1, 1])  # CN 3 not supported


def test_cn4_geometry_default_by_d_count():
    # d8 (Pt/Pd/Ni-II) -> square-planar; d10/main-group & unknown -> tetrahedral.
    assert geometry.propose_geometry(4, 8) is Geometry.SQUARE_PLANAR
    assert geometry.propose_geometry(4, 10) is Geometry.TETRAHEDRAL
    assert geometry.propose_geometry(4) is Geometry.TETRAHEDRAL
    # square-planar 4-monodentate has a fixed topology; tetrahedral builds via the
    # generic site model (no fixed registry class — that's by design).
    assert registry.lookup(Geometry.SQUARE_PLANAR, [1, 1, 1, 1]).label == "square_4mono"


def test_cn4_default_uses_metal_d_count():
    from mecobi import spin

    # d8 centres -> square-planar (Pt/Pd/Ni-II); d10 & main-group -> tetrahedral.
    assert spin.d_count_or_none("Pt", 2) == 8
    assert geometry.propose_geometry(4, spin.d_count_or_none("Pt", 2)) is Geometry.SQUARE_PLANAR
    assert spin.d_count_or_none("Zn", 2) == 10
    assert geometry.propose_geometry(4, spin.d_count_or_none("Zn", 2)) is Geometry.TETRAHEDRAL
    # [GaCl4]- : Ga is main-group (no group-number entry) -> d-count None -> tetrahedral
    # (previously defaulted to square-planar, which the CIF validation flagged).
    assert spin.d_count_or_none("Ga", 3) is None
    assert geometry.propose_geometry(4, spin.d_count_or_none("Ga", 3)) is Geometry.TETRAHEDRAL


def test_gacl4_builds_tetrahedral_not_square_planar(tmp_path):
    # End-to-end: [GaCl4]- (Ga d10, main-group) must now build tetrahedral, not the
    # old square-planar default. [Cl-] perception is trivial, so this stays fast.
    import numpy as np

    cx = Complex(metal=Metal("Ga", 3), ligands=[Ligand("[Cl-]") for _ in range(4)])
    res = pipeline.build_complex(cx, tmp_path, relax=False)[0]
    lines = Path(res.xyz_path).read_text().splitlines()
    at = [(l.split()[0], np.array(list(map(float, l.split()[1:4]))))
          for l in lines[2:2 + int(lines[0])]]
    mp = next(p for e, p in at if e == "Ga")
    vs = [p - mp for e, p in at if e == "Cl"]
    angs = [float(np.degrees(np.arccos(np.clip(
                np.dot(a, b) / np.linalg.norm(a) / np.linalg.norm(b), -1, 1))))
            for i, a in enumerate(vs) for b in vs[i + 1:]]
    # tetrahedral: all six angles near 109.5; square-planar has two ~180 trans angles.
    assert max(angs) < 150, f"looks square-planar (has a ~180 trans angle): {sorted(angs)}"
    assert 95 < float(np.mean(angs)) < 125


def test_tridentate_donors_preorganized_to_chelate():
    # Regression for the V(V)-oxo bug: a linear tri-/tetradentate ligand's
    # backbone-adjacent donors must be pre-organised into cis-chelate range so the
    # ligand wraps the metal instead of binding backbone-first (which stranded the
    # donors and crushed a backbone C-H onto the metal). dien = N-C-C-N-C-C-N.
    import numpy as np
    from rdkit import Chem

    from mecobi.assembly._chem import _donor_chain_order, ligand_building_block

    donors = [0, 3, 6]
    bb = ligand_building_block("NCCNCCN", donors)
    pos = bb.get_position_matrix()
    chain = _donor_chain_order(Chem.AddHs(Chem.MolFromSmiles("NCCNCCN")), donors)
    for a, b in zip(chain, chain[1:]):
        d = float(np.linalg.norm(pos[a] - pos[b]))
        assert d < 3.3, f"adjacent donors {a},{b} at {d:.2f} A — not pre-organised to chelate"


def test_terminal_oxo_donor_detection():
    # A terminal oxo (O bonded only to the metal) is detected so it can relax to a
    # short M=O; halides (also terminal, but Cl) are not, so they stay restrained.
    from mecobi.pipeline import (
        _metal_bonded_donors,
        _terminal_oxo_donors,
        resolve_perception,
    )

    cx = Complex(Metal("W", 6), [Ligand("[O-2]")] + [Ligand("[Cl-]") for _ in range(5)])
    resolve_perception(cx)
    spec = assembly.default_isomer(cx, geometry.propose_geometry(cx.coordination_number))
    constructed, _ = (
        assembly.build_from_sites(cx, spec.geometry, dict(spec.assignment))
        if getattr(spec, "site_based", False) else assembly.build(cx, spec)
    )
    mi, donors = _metal_bonded_donors(constructed, "W")
    oxo = _terminal_oxo_donors(constructed, mi, donors)
    elems = [a.__class__.__name__ for a in constructed.get_atoms()]
    assert len(oxo) == 1 and all(elems[i] == "O" for i in oxo)  # the oxo only
    assert not any(elems[i] == "Cl" for i in oxo)               # halides stay restrained


@pytest.mark.slow
def test_vanadium_oxo_builds_clean(tmp_path):
    # Regression for VanadiumComplexIssue: V(V)-oxo + tridentate ONO ligand +
    # hydroxamate must build with a short V=O, no stranded donors, and no backbone
    # atom crushed onto the metal.
    import numpy as np
    import pandas as pd

    row = {"Name": "V", "Metal": "V", "Charge": 5,
           "L1": "[O-]C1=CC=CC=C1/C=N/N=C([O-])/C2=CC=CC=C2",
           "L2": "O=C(N[O-])C1=CC=CC=C1", "L3": "[O-2]"}
    cx = inputs.parse_dataframe(pd.DataFrame([row]))[0]
    res = pipeline.build_complex(cx, tmp_path, relax=True, xtb_timeout_s=200)[0]
    lines = open(res.xyz_path).read().splitlines()
    at = [(l.split()[0], np.array(list(map(float, l.split()[1:4]))))
          for l in lines[2:2 + int(lines[0])]]
    mp = at[res.metal_index][1]
    dists = sorted(float(np.linalg.norm(at[i][1] - mp)) for i in res.donor_indices)
    assert dists[0] < 1.75, f"no short V=O (shortest donor {dists[0]:.2f} A)"
    assert dists[-1] < 3.0, f"a donor is stranded at {dists[-1]:.2f} A"
    non_donor_closest = min(
        float(np.linalg.norm(p - mp)) for i, (e, p) in enumerate(at)
        if i != res.metal_index and i not in res.donor_indices
    )
    assert non_donor_closest > 1.8, f"a backbone atom is crushed at {non_donor_closest:.2f} A"


def test_default_isomer_orders_ligands_high_denticity_first():
    cx = Complex(
        Metal("Ir", 3),
        [Ligand("a", denticity=1), Ligand("b", denticity=2),
         Ligand("c", denticity=1), Ligand("d", denticity=2)],
    )
    spec = assembly.default_isomer(cx, Geometry.OCTAHEDRAL)
    # bidentate ligands (idx 1,3) take vertices 0,1; monodentate (0,2) take 2,3.
    assert spec.assignment == {1: (0,), 3: (1,), 0: (2,), 2: (3,)}
    assert spec.geometry is Geometry.OCTAHEDRAL


# --------------------------------------------------------------------------- #
# full pipeline build — slow (perception + stk + MCHammer)
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_pipeline_builds_square_2bi(tmp_path):
    cx = next(c for c in inputs.parse_csv(PROTOTYPE_CSV) if c.name == "Sq2b_Pt_1")
    results = pipeline.build_complex(cx, tmp_path)
    assert len(results) == 1
    r = results[0]
    assert r.total_charge == 2  # Pt(II) + two neutral bipyridines
    xyz = Path(r.xyz_path)
    assert xyz.exists()
    assert int(xyz.read_text().splitlines()[0]) == 41  # atom count


@pytest.mark.slow
def test_pipeline_builds_octahedral_2bi2mono(tmp_path):
    cx = next(c for c in inputs.parse_csv(PROTOTYPE_CSV) if c.name == "Oct2b_Ir_1")
    results = pipeline.build_complex(cx, tmp_path)
    assert len(results) == 1
    assert Path(results[0].xyz_path).exists()
