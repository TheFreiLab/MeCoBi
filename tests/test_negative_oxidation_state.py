"""A metal in a NEGATIVE oxidation state must assemble (carbonylates: [Fe(CO)4]2-, [Co(CO)4]-).

The metal building block was written as ``[Fe+-1]`` -- not valid SMILES -- so every such complex
(300 in the 36k benchmark bundle) failed in assembly before any chemistry ran.
"""
import pytest

from mecobi import pipeline
from mecobi.assembly import _chem
from mecobi.model import Complex, Ligand, Metal


@pytest.mark.parametrize("charge", [-2, -1, 0, 2])
def test_metal_building_block_accepts_any_charge(charge):
    bb = _chem.metal_building_block("Fe", charge, 4)
    assert bb.get_num_atoms() == 1
    assert next(bb.get_atoms()).get_charge() == charge


def test_tetracarbonylferrate_assembles(tmp_path):
    ligs = [Ligand("[C-]#[O+]") for _ in range(4)]
    for lig in ligs:
        lig.donor_override = [0]
    cx = Complex(metal=Metal("Fe", -2), name="t", ligands=ligs)
    res = pipeline.build_complex(cx, tmp_path, all_isomers=False, relax=False)
    assert res and open(res[0].xyz_path).read().count("\n") >= 11      # Fe + 4 CO
