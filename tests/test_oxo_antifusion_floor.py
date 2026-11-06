"""Pre-emptive anti-fusion floor for terminal oxo/nitrido donors (C4b).

The fast tests (no torch / no xtb) unit-test the floor geometry and the two-block xtb constraint
file. The slow test at the bottom locks in the end-to-end xtb evidence: the Re(V) dioxo
bis-PNP, run as the singlet it is,
relaxes INTACT with default options (Re=O ~1.70 A); its old P-O ~1.49 A fusion was a triplet artefact.
"""
import math

import pytest

from mecobi import optimize, pipeline
from mecobi.model import Complex, Ligand, Metal


def _read_xyz(path):
    lines = open(path).read().splitlines()
    n = int(lines[0].split()[0])
    syms, coords = [], []
    for ln in lines[2:2 + n]:
        s = ln.split()
        syms.append(s[0]); coords.append((float(s[1]), float(s[2]), float(s[3])))
    return syms, coords


def test_preemptive_oxo_floors_holds_terminal_oxo_off_a_nearby_donor():
    # metal(0) at origin; terminal oxo O(1) at 2 A; phosphine P(2) on a DIFFERENT ligand ~2.83 A away.
    pre = [("Re", (0.0, 0.0, 0.0)), ("O", (2.0, 0.0, 0.0)), ("P", (0.0, 2.0, 0.0))]
    comp = [-1, 0, 1]  # metal excluded; oxo its own component; P a different ligand
    floors = pipeline._preemptive_oxo_floors(pre, oxo_donors={1}, comp=comp, metal_index=0)

    assert len(floors) == 1
    i, j, target = floors[0]
    assert {i, j} == {1, 2}
    d = math.dist(pre[1][1], pre[2][1])
    nonbonded = (optimize._cov_radius("O") + optimize._cov_radius("P")) * 1.5
    # floor never pulls a pair CLOSER than it already is: target = max(current, non-bonded).
    assert target == max(d, nonbonded)


def test_preemptive_oxo_floors_also_guards_a_nearby_non_donor_carbon():
    # The oxo can also fuse onto a backbone/carbonyl CARBON (not a donor). The floor must catch it.
    pre = [("Re", (0.0, 0.0, 0.0)), ("O", (2.0, 0.0, 0.0)), ("C", (0.6, 2.0, 0.0))]
    comp = [-1, 0, 1]  # C is on a different ligand and is NOT a donor
    floors = pipeline._preemptive_oxo_floors(pre, oxo_donors={1}, comp=comp, metal_index=0)
    assert len(floors) == 1 and {floors[0][0], floors[0][1]} == {1, 2}


def test_preemptive_oxo_floors_skips_same_ligand_metal_and_distant_atoms():
    # C(2) shares the oxo's... no: O(1) alone is a component; C(2) same-ligand pair skipped;
    # N(3) beyond 4 A capture; metal(0) skipped.
    pre = [("Re", (0.0, 0.0, 0.0)), ("O", (2.0, 0.0, 0.0)),
           ("C", (2.6, 0.0, 0.0)), ("N", (0.0, 0.0, 9.0))]
    comp = [-1, 0, 0, 1]  # O(1) and C(2) in the SAME ligand component -> skipped
    floors = pipeline._preemptive_oxo_floors(pre, oxo_donors={1}, comp=comp, metal_index=0)
    assert floors == []  # same-ligand C skipped; distant N skipped; metal skipped


def test_oxo_fusions_flags_oxo_to_carbon_on_another_ligand():
    # xtb forged O(1)-C(3): oxo(1) is terminal, C(3) is on a DIFFERENT ligand -> a deoxygenation
    # fusion the donor-only detector misses (C is not a donor). new_bonds are (i, j, dist) triples.
    new_bonds = [(1, 3, 1.4)]
    comp = [-1, 0, 0, 1]  # oxo(1) in comp 0; C(3) in comp 1
    assert pipeline._oxo_fusions(new_bonds, comp, oxo_donors={1}) == [(1, 3)]


def test_oxo_fusions_ignores_same_ligand_and_non_oxo_new_bonds():
    new_bonds = [(2, 3, 1.5), (1, 2, 1.5)]  # (2,3) has no oxo; (1,2) is oxo but same ligand
    comp = [-1, 0, 0, 1]
    assert pipeline._oxo_fusions(new_bonds, comp, oxo_donors={1}) == []


def test_constraint_file_emits_two_blocks_with_independent_force_constants(tmp_path):
    f = tmp_path / "constrain.inp"
    optimize._write_constraint_file(
        f, [(0, 1, 2.0)], 0.5,
        strong_constraints=[(2, 3, 3.5)], strong_force_constant=5.0,
    )
    text = f.read_text()
    assert text.count("$constrain") == 2
    assert "force constant=0.5" in text
    assert "force constant=5.0" in text
    assert "distance: 1, 2, 2.000" in text  # normal block, 1-based indices
    assert "distance: 3, 4, 3.500" in text  # strong block


def test_constraint_file_omits_strong_block_when_no_strong_constraints(tmp_path):
    f = tmp_path / "constrain.inp"
    optimize._write_constraint_file(f, [(0, 1, 2.0)], 0.5)
    assert f.read_text().count("$constrain") == 1


# The motivating case's PNP arm: N donor + two -CH2-PPh2 phosphines; the -CCC[P+](Ph)3 arm is a
# non-coordinating phosphonium. donor_override picks the two phosphine P (atoms 24, 38); the pincer
# is built as an effective bidentate P,P.
_RE_PNP = ("N(CCC[P+](C1=CC=CC=C1)(C2=CC=CC=C2)C3=CC=CC=C3)(CP(C4=CC=CC=C4)C5=CC=CC=C5)"
           "CP(C6=CC=CC=C6)C7=CC=CC=C7")


@pytest.mark.slow
def test_re_dioxo_bis_pnp_relaxes_intact_as_singlet_with_defaults(tmp_path):
    """End-to-end regression for the motivating C4 case (NOTES.md, 2026-09-23 addendum).

    The GFN2 deoxygenation (spurious P-O ~1.49 A) was a spin-state error: the d2 Re(V) centre was
    run as a triplet, populating the Re=O pi*. As the closed-shell singlet it is, the 195-atom
    Re(V) dioxo bis-PNP relaxes INTACT with default options: no oxo->P fusion, Re-P at the CSD
    reference (~2.44 A), and two genuine Re=O multiple bonds (~1.70 A). The old opt-in path
    (floors + reposition) only checked "oxo retained" and hid a 1.92/2.35 A Re-O.
    """
    ligs = [Ligand(_RE_PNP, donor_override=[24, 38]), Ligand(_RE_PNP, donor_override=[24, 38]),
            Ligand("[O-2]", donor_override=[0]), Ligand("[O-2]", donor_override=[0])]
    cx = Complex(metal=Metal("Re", 5), name="re_dioxo_bis_pnp", ligands=ligs)

    res = pipeline.build_complex(cx, tmp_path, relax=True, xtb_timeout_s=1200)[0]
    # Surface the pipeline's own diagnosis (xtb tier failures, fallbacks) in any failure below.
    print("build warnings:", *res.warnings, sep="\n  ")
    assert res.uhf == 0, f"d2 Re(V) dioxo must relax as a singlet, got uhf={res.uhf}"
    assert res.connectivity_ok, "xtb rearranged the assembled connectivity"

    syms, P = _read_xyz(res.xyz_path)
    assert len(syms) == 195, f"unexpected atom count {len(syms)}"
    m = P[res.metal_index]
    Ps = [i for i, s in enumerate(syms) if s == "P"]
    Os = [i for i, s in enumerate(syms) if s == "O"]
    assert len(Ps) == 6 and len(Os) == 2

    # No deoxygenation: a P-O bond is ~1.5 A; the intact cis P...O contact is ~2.8 A.
    min_po = min(math.dist(P[p], P[o]) for p in Ps for o in Os)
    assert min_po > 2.5, f"terminal oxo fused onto a phosphine (min P-O {min_po:.2f} A)"

    # The four coordinating phosphines sit at the CSD Re-P reference (~2.44 A); the two phosphonium
    # P are non-donors that must stay well off the metal.
    re_p = sorted(math.dist(m, P[i]) for i in Ps)
    donors = re_p[:4]
    assert all(2.3 < d < 2.7 for d in donors),         f"Re-P donors off the reference: {[round(d, 2) for d in donors]}"
    assert re_p[4] > 4.0, "a non-donor phosphonium P drifted onto the metal"

    # Two real Re=O multiple bonds (exp. ~1.77 A; GFN2 ~1.70 A), not merely "retained" oxo.
    re_o = sorted(math.dist(m, P[i]) for i in Os)
    assert all(1.6 < d < 1.85 for d in re_o), f"Re=O not a multiple bond: {[round(d, 2) for d in re_o]}"
