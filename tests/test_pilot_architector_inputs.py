"""pilot100/architector/arch_run.py: the crystal geometry and isomer reach Architector's input.

Run at its defaults, Architector searched every core of the coordination number and kept the
lowest energy, while MeCoBi and MetalloGen were given the crystal geometry and isomer: the
comparison was not like for like. ``--targets`` passes the geometry, ``--pin-sites`` the isomer.
"""
import json
import sys
import types
from pathlib import Path

import numpy as np
import pytest

ARCH = Path(__file__).resolve().parents[1] / "experiments" / "benchmark" / "pilot100" / "architector"
sys.modules.setdefault("architector", types.SimpleNamespace(build_complex=None))  # not installed
sys.path.insert(0, str(ARCH))
import arch_run

VECTORS = json.loads((ARCH / "mecobi_site_vectors.json").read_text(encoding="utf-8"))
REC = {"refcode": "X", "metal": "Zr", "ox": 4, "cn": 6, "donor_elements": ["Cl", "Cl"] + ["N"] * 4,
       "ligands": ["[Cl-]", "[Cl-]", "NCCNCCNCCN"]}
DONORS = [[0], [0], [0, 3, 6, 9]]
TARGET = {"geometry": "octahedral", "site_cn": 6, "site_map": "0:3;1:0;2:2,1,4,5"}


def test_site_vectors_file_is_mecobis():
    from mecobi.assembly.sites import SITE_VECTORS
    assert set(VECTORS) == {getattr(g, "value", g) for g in SITE_VECTORS}
    for g, v in SITE_VECTORS.items():
        v = np.asarray(v, float)
        assert np.allclose(VECTORS[getattr(g, "value", g)],
                           v / np.linalg.norm(v, axis=1)[:, None], atol=1e-5)


def test_levels_most_specific_first():
    assert arch_run.input_levels(None, DONORS, True, VECTORS) == (["default"], False)
    assert arch_run.input_levels(TARGET, DONORS, False, VECTORS) == (["geometry", "default"], False)
    assert arch_run.input_levels(TARGET, DONORS, True, VECTORS) == (
        ["isomer", "geometry", "default"], False)


def test_haptic_complex_keeps_the_default():
    # eight donor atoms on four sites: Architector has no input for that
    donors = [[0], [0], [0], [0, 1, 2, 3, 4]]
    tg = {"geometry": "tetrahedral", "site_cn": 4, "site_map": "0:0;1:2;2:3;3:1"}
    assert arch_run.input_levels(tg, donors, True, VECTORS) == (["default"], True)


def test_geometry_level_passes_the_core_type_alone():
    inp, err = arch_run.build_input(REC, DONORS, "geometry", TARGET, VECTORS)
    assert err is None
    # a coreCN next to coreType would add every core of that CN back
    assert inp["core"] == {"metal": "Zr", "coreType": ["octahedral"]}
    assert [lig["coordList"] for lig in inp["ligands"]] == DONORS


def test_isomer_level_ties_each_donor_to_its_crystal_site():
    inp, err = arch_run.build_input(REC, DONORS, "isomer", TARGET, VECTORS)
    assert err is None
    assert np.allclose(inp["core"]["coordList"],
                       arch_run.CORE_RADIUS * np.array(VECTORS["octahedral"]))
    assert "coreCN" not in inp["core"] and "coreType" not in inp["core"]
    assert [lig["coordList"] for lig in inp["ligands"]] == [
        [[0, 3]], [[0, 0]], [[0, 2], [3, 1], [6, 4], [9, 5]]]


@pytest.mark.parametrize("site_map", ["0:3;1:0", "0:3;1:3;2:2,1,4,5", "0:3;1:0;2:2,1,4"])
def test_incomplete_site_map_is_not_pinned(site_map):
    tg = dict(TARGET, site_map=site_map)   # ligand missing / site used twice / donor without site
    assert arch_run.input_levels(tg, DONORS, True, VECTORS)[0] == ["geometry", "default"]


def test_default_level_is_the_old_input():
    inp, _ = arch_run.build_input(REC, DONORS)
    assert inp["core"] == {"metal": "Zr", "coreCN": 6}


def test_every_mecobi_geometry_has_a_core_type():
    assert set(arch_run.CORE_TYPE) == set(VECTORS)
