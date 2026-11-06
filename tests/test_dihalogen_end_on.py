"""η1-dihalogen ligands (PIDRIE: van Koten's Pt(NCN)(I)(I2)) bind end-on and collinear.

Three gaps: pydentate perceives no donor in a bare X-X molecule; the linearity restraint only
knew C/N end-on donors (CO, CN-, NO); and an UNRESTRAINED relax (the σ-aryl policy, which the
NCN pincer triggers) dropped every angle restraint, so M-C≡O / M-I-I were free to bend there.
"""

import math

import pytest

from mecobi import optimize, perception, pipeline
from mecobi.model import Ligand


@pytest.mark.parametrize("smiles,donor", [("II", 0), ("BrBr", 0), ("ICl", 0), ("ClI", 1)])
def test_dihalogen_binds_through_one_heavier_halogen(smiles, donor):
    lig = Ligand(smiles)
    perception.perceive(lig)
    assert lig.coord_atoms == [donor]
    assert lig.denticity == 1


def test_iodide_and_hypervalent_anions_untouched():
    lig = Ligand("[I-]")
    perception.perceive(lig)
    assert lig.coord_atoms == [0]


def test_linear_restraint_covers_end_on_dihalogen(tmp_path):
    xyz = tmp_path / "m.xyz"
    xyz.write_text("3\n\nPt 0 0 0\nI 2.6 0 0\nI 4.8 1.2 0\n")   # bent M-I-I
    assert pipeline._linear_donor_angles(xyz, [(0, 1), (1, 2)], 0, [1]) == [(0, 1, 2, 180.0)]


def test_unrestrained_relax_still_writes_angle_restraints(tmp_path, monkeypatch):
    xyz = tmp_path / "m.xyz"
    xyz.write_text("3\n\nPt 0 0 0\nI 2.6 0 0\nI 4.8 1.2 0\n")
    seen = {}

    def fake_run(cmd, *a, **k):
        if "--input" in cmd:
            seen["input"] = (tmp_path / "run" / "constrain.inp").exists() or \
                any(p.endswith("constrain.inp") for p in cmd)
            path = cmd[cmd.index("--input") + 1]
            seen["text"] = open(path).read()
        raise optimize.XtbError("stop after writing the input")

    monkeypatch.setattr(optimize.subprocess, "run", fake_run)
    with pytest.raises(optimize.XtbError):
        optimize.relax_with_xtb(xyz, charge=0, uhf=0, workdir=tmp_path, restrain_donors=False,
                                angle_constraints=[(0, 1, 2, 180.0)])
    assert "angle: 1, 2, 3, 180.00" in seen["text"]
    assert "distance" not in seen["text"]


@pytest.mark.slow
def test_pidrie_pt_i_i_stays_linear(tmp_path):
    from mecobi.model import Complex, Metal

    cx = Complex(metal=Metal("Pt", 2), ligands=[
        Ligand("[I-]"), Ligand("II"),
        Ligand("CN(C)Cc1[c-]c(CN(C)C)cc(C(=O)ON2C(=O)CCC2=O)c1")])
    (res,) = pipeline.build_complex(cx, tmp_path, relax=True)
    lines = open(res.xyz_path).read().splitlines()[2:]
    at = [(ln.split()[0], [float(v) for v in ln.split()[1:4]]) for ln in lines if ln.strip()]
    m = at[res.metal_index][1]
    iodines = [i for i, (e, _) in enumerate(at) if e == "I"]
    pair = next((a, b) for a in iodines for b in iodines
                if a < b and math.dist(at[a][1], at[b][1]) < 3.4)   # the I-I molecule
    bound, far = sorted(pair, key=lambda i: math.dist(at[i][1], m))
    v1 = [a - b for a, b in zip(m, at[bound][1])]
    v2 = [a - b for a, b in zip(at[far][1], at[bound][1])]
    ang = math.degrees(math.acos(sum(p * q for p, q in zip(v1, v2))
                                 / (math.hypot(*v1) * math.hypot(*v2))))
    assert ang > 170, ang
