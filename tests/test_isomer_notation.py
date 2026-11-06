"""Donor-index isomer notation ("mode 3").

Parsing, serialisation round-trip, and end-to-end build of one pinned isomer
from a CSV ``isomer`` column.
"""

import numpy as np
import pytest

from mecobi import inputs, isomers
from mecobi.isomers import IsomerNotationError, parse_isomer_notation
from mecobi.model import Complex, Geometry, Ligand, Metal

O = Geometry.OCTAHEDRAL


# --------------------------------------------------------------------------- #
# fast: parse + format
# --------------------------------------------------------------------------- #

def test_parse_donors_only():
    n = parse_isomer_notation("0(3);1(3)")
    assert n.donors == {0: (3,), 1: (3,)}
    assert n.sites == {}
    assert n.geometry is None


def test_parse_sites_only():
    n = parse_isomer_notation("0:0,2;1:1,3;2:4;3:5")
    assert n.sites == {0: (0, 2), 1: (1, 3), 2: (4,), 3: (5,)}
    assert n.donors == {}


def test_parse_geometry_prefix_and_both():
    n = parse_isomer_notation("octahedral| 0(0,1):0,2; 2:4; 3:5")
    assert n.geometry is O
    assert n.donors == {0: (0, 1)}
    assert n.sites == {0: (0, 2), 2: (4,), 3: (5,)}


def test_site_order_is_preserved():
    # donor direction matters — sites must NOT be sorted within a ligand.
    assert parse_isomer_notation("0:2,0").sites == {0: (2, 0)}


@pytest.mark.parametrize("bad", ["", "0", "()", "0:", "x:1", "0:1;0:2", "bogus| 0:1"])
def test_malformed_notation_raises(bad):
    with pytest.raises(IsomerNotationError):
        parse_isomer_notation(bad)


def test_format_round_trips_enumerated_isomers():
    # Enumerate octahedral bis-bipyridine dichlorido isomers, serialise each to a
    # notation string, parse back, and confirm the site assignment is identical.
    cx = Complex(
        metal=Metal("Ir", 3),
        ligands=[Ligand("c1ccc(-c2ccccn2)nc1", coord_atoms=[6, 11], denticity=2),
                 Ligand("c1ccc(-c2ccccn2)nc1", coord_atoms=[6, 11], denticity=2),
                 Ligand("[Cl-]", coord_atoms=[0], denticity=1),
                 Ligand("[Cl-]", coord_atoms=[0], denticity=1)],
    )
    specs = isomers.enumerate_site_isomers(cx, O)
    assert len(specs) >= 2  # cis + trans at least
    for spec in specs:
        text = isomers.format_isomer_spec(spec)
        back = isomers.parse_topology_spec(text, O)
        assert back.assignment == spec.assignment
        assert back.site_based


def test_inputs_reads_isomer_column():
    import pandas as pd

    df = pd.DataFrame(
        {"Metal": ["Ir"], "Charge": [3],
         "L1": ["[Cl-]"], "L2": ["[Cl-]"], "L3": ["[Cl-]"],
         "L4": ["[Cl-]"], "L5": ["[Cl-]"], "L6": ["[Cl-]"],
         "isomer": ["0:0;1:1;2:2;3:3;4:4;5:5"]},
    )
    cx = inputs.parse_dataframe(df)[0]
    assert cx.isomer_spec == "0:0;1:1;2:2;3:3;4:4;5:5"


# --------------------------------------------------------------------------- #
# slow: build one pinned isomer end to end
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_build_cis_from_isomer_spec(tmp_path):
    from mecobi import pipeline

    def cl_angle(spec_text):
        cx = Complex(
            metal=Metal("Ir", 3), geometry=O, isomer_spec=spec_text,
            ligands=[Ligand("c1ccc(-c2ccccn2)nc1"), Ligand("c1ccc(-c2ccccn2)nc1"),
                     Ligand("[Cl-]"), Ligand("[Cl-]")],
        )
        res = pipeline.build_complex(cx, tmp_path, relax=False)
        assert len(res) == 1
        from pathlib import Path

        lines = Path(res[0].xyz_path).read_text().splitlines()
        n = int(lines[0])
        syms, X = [], []
        for ln in lines[2:2 + n]:
            q = ln.split(); syms.append(q[0]); X.append([float(x) for x in q[1:4]])
        X = np.array(X); mi = syms.index("Ir")
        d = np.linalg.norm(X - X[mi], axis=1)
        cl = [i for i in np.argsort(d) if syms[i] == "Cl"][:2]
        va, vb = X[cl[0]] - X[mi], X[cl[1]] - X[mi]
        return np.degrees(np.arccos(np.clip(va @ vb / (np.linalg.norm(va) * np.linalg.norm(vb)), -1, 1)))

    # sites 1 and 4 are cis (90 deg); the bis-chelate takes cis pairs (0,2),(3,5).
    assert cl_angle("0:0,2;1:3,5;2:1;3:4") < 110
    assert cl_angle("0:0,2;1:1,3;2:4;3:5") > 150  # Cl on trans 4/5
