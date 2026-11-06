"""η-cap centroid model (donor-override path): a selected carbocyclic ring is ONE
coordination site at its centroid (denticity 1), so metallocenes are linear and
multi-Cp / mixed cap+σ ligands (ansa-metallocenes, Cp+pyridine) build. Auto-perception
is unchanged. See feat/eta-cap-centroid-prototype."""
import tempfile

import pytest
from rdkit import Chem

from mecobi import perception, pipeline
from mecobi.model import Complex, Ligand, Metal

CP = [0, 1, 2, 3, 4]


def _cap_donors(smi):
    """Carbocyclic 5-/6-ring carbons + aromatic-ring N — a donor override for a cap ligand."""
    m = Chem.MolFromSmiles(smi)
    ov = []
    for ring in m.GetRingInfo().AtomRings():
        if len(ring) in (5, 6) and all(m.GetAtomWithIdx(i).GetAtomicNum() == 6 for i in ring):
            ov += list(ring)
    for a in m.GetAtoms():
        if a.GetIsAromatic() and a.GetAtomicNum() == 7:
            ov.append(a.GetIdx())
    return sorted(set(ov))


def _lig(smi, donors):
    """donors: explicit list (override), None (auto-detect cap ring(s)), or "auto"
    (let pydentate perceive, e.g. a bidentate bpy in a piano-stool)."""
    if donors == "auto":
        return Ligand(smi)
    return Ligand(smi, donor_override=(donors if donors is not None else _cap_donors(smi)))


def _cx(metal, ox, ligspec):
    return Complex(metal=Metal(metal, ox), ligands=[_lig(s, o) for s, o in ligspec])


CO = ("[C-]#[O+]", [0])   # carbonyl, C-donor
CL = ("[Cl-]", [0])
CPX = "CC1=C(C)C(C)=C(C)[C-]1C"  # Cp*  (5 ring carbons -> one centroid cap)
BPY = ("c1ccc(-c2ccccn2)nc1", "auto")


def test_cap_reaction_factory_registers_caps_without_touching_stk_global():
    # The metal(1)-cap(N) dative bond is handled by a GenericReactionFactory subclass
    # (CapReactionFactory), NOT by mutating stk's process-global reaction registry.
    # This also guards the private stk internals it relies on: importing the module
    # fails at collection if stk renames _one_two_reaction / _get_reaction_key.
    from stk._internal.reaction_factories import generic_reaction_factory as grf

    from mecobi.assembly.topologies.metal_complex import _CAP_REACTIONS

    assert {tuple(sorted(k)) for k in _CAP_REACTIONS} == {(1, 3), (1, 4), (1, 5), (1, 6)}
    # stk's own registry stays pristine (only its built-in {1}, {1,2}, {2} keys).
    assert not any(len(k) == 2 and 1 in k and max(k) >= 3 for k in grf._reactions)


def test_metallocene_is_cn2_linear():
    cx = _cx("Fe", 2, [("[cH-]1cccc1", CP), ("[cH-]1cccc1", CP)])
    perception.perceive_complex(cx)
    assert [l.denticity for l in cx.ligands] == [1, 1]
    assert cx.coordination_number == 2          # each Cp is one centroid site, not 3


def test_bis_cp_pyridine_is_cn5():
    # one ligand = 2 Cp caps + a pyridine N; + 2 Cl -> CN5 (matches MetalloGen)
    smi = "C1(CC2=NC(CC3=CC=C[CH-]3)=CC=C2)=C[CH-]C=C1"
    cx = _cx("Zr", 4, [(smi, None), ("[Cl-]", [0]), ("[Cl-]", [0])])
    perception.perceive_complex(cx)
    assert cx.ligands[0].denticity == 3         # 2 caps + 1 N
    assert len(cx.ligands[0].pi_sites) == 2     # two centroid caps
    assert cx.coordination_number == 5


@pytest.mark.parametrize("name,metal,ox,ligspec", [
    ("ferrocene", "Fe", 2, [("[cH-]1cccc1", CP), ("[cH-]1cccc1", CP)]),
    ("cobaltocene", "Co", 2, [("[cH-]1cccc1", CP), ("[cH-]1cccc1", CP)]),
    ("Cp2TiCl2", "Ti", 4, [("[cH-]1cccc1", CP), ("[cH-]1cccc1", CP), CL, CL]),
    ("bis-benzene-Cr", "Cr", 0, [("c1ccccc1", None), ("c1ccccc1", None)]),
    ("decamethylferrocene", "Fe", 2, [(CPX, None), (CPX, None)]),
    ("mixed-sandwich-CpFe-arene", "Fe", 2, [("[cH-]1cccc1", CP), ("c1ccccc1", None)]),
    ("cymantrene-CpMn(CO)3", "Mn", 1, [("[cH-]1cccc1", CP), CO, CO, CO]),
    ("benzene-Cr(CO)3", "Cr", 0, [("c1ccccc1", None), CO, CO, CO]),
    ("CpFe(CO)2Cl", "Fe", 2, [("[cH-]1cccc1", CP), CO, CO, CL]),
    ("Cp*Ir(bpy)Cl-piano", "Ir", 3, [(CPX, None), BPY, CL]),
    ("ansa-ferrocenophane", "Fe", 2, [("C1(CCCC2=CC=C[CH-]2)=C[CH-]C=C1", None)]),
    ("Zr-bisCp-pyridine", "Zr", 4, [("C1(CC2=NC(CC3=CC=C[CH-]3)=CC=C2)=C[CH-]C=C1", None), CL, CL]),
])
def test_cap_complexes_assemble(name, metal, ox, ligspec):
    cx = _cx(metal, ox, ligspec)
    with tempfile.TemporaryDirectory() as d:
        res = pipeline.build_complex(cx, d, relax=False)
    assert len(res) >= 1
    # every ring carbon of the caps ends up bonded to the metal
    assert res[0].donor_indices


def test_bent_metallocene_routing_and_assignment():
    """A two-cap fragment with ancillary ligands routes to METALLOCENE_BENT, with the
    caps on the two cap sites (0,1) and the ancillary ligands in the wedge (2..)."""
    from mecobi import geometry
    from mecobi.assembly import default_isomer

    cx = _cx("Ti", 4, [("[cH-]1cccc1", CP), ("[cH-]1cccc1", CP), CL, CL])   # Cp2TiCl2
    perception.perceive_complex(cx)
    cap_sites = sum(1 for l in cx.ligands for s in (l.pi_sites or []) if len(s) >= 3)
    assert cap_sites == 2
    spec = default_isomer(cx, geometry.Geometry.METALLOCENE_BENT)
    assert spec.geometry is geometry.Geometry.METALLOCENE_BENT and spec.site_based
    caps = {s for lig in (0, 1) for s in spec.assignment[lig]}
    ancillary = {s for lig in (2, 3) for s in spec.assignment[lig]}
    assert caps == {0, 1} and ancillary == {2, 3}       # caps up, Cl in the wedge


@pytest.mark.slow
def test_cp2ticl2_bent_relaxes_clean():
    """Bent metallocene end to end: two intact η5 Cp rings + two Cl, no clash."""
    import numpy as np
    cx = _cx("Ti", 4, [("[cH-]1cccc1", CP), ("[cH-]1cccc1", CP), CL, CL])
    with tempfile.TemporaryDirectory() as d:
        r = pipeline.build_complex(cx, d, relax=True, xtb_timeout_s=180)[0]
        lines = open(r.xyz_path).read().splitlines()
    n = int(lines[0])
    syms = [ln.split()[0] for ln in lines[2:2 + n]]
    P = np.array([[float(x) for x in ln.split()[1:4]] for ln in lines[2:2 + n]])
    M = P[syms.index("Ti")]
    ti_c = sorted(float(np.linalg.norm(P[i] - M)) for i in range(len(syms)) if syms[i] == "C")
    assert len(ti_c) == 10 and all(2.0 < d < 2.7 for d in ti_c)   # both Cp η5, none slipped
    mind = min(float(np.linalg.norm(P[i] - P[j]))
               for i in range(n) for j in range(i + 1, n))
    assert mind > 0.95                                             # no atom overlap/clash


@pytest.mark.slow
def test_ferrocene_relaxes_to_bonded_eta5():
    import numpy as np
    cx = _cx("Fe", 2, [("[cH-]1cccc1", CP), ("[cH-]1cccc1", CP)])
    with tempfile.TemporaryDirectory() as d:
        r = pipeline.build_complex(cx, d, relax=True, xtb_timeout_s=150)[0]
        lines = open(r.xyz_path).read().splitlines()
        n = int(lines[0])
        syms = [ln.split()[0] for ln in lines[2:2 + n]]
        P = np.array([[float(x) for x in ln.split()[1:4]] for ln in lines[2:2 + n]])
        M = P[syms.index("Fe")]
        fe_c = sorted(float(np.linalg.norm(P[i] - M)) for i in range(len(syms)) if syms[i] == "C")
        assert len(fe_c) == 10                       # both Cp fully bonded
        assert all(1.9 < d < 2.7 for d in fe_c)      # η5, no dissociation, no crush
