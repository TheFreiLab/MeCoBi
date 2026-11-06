"""Graph-identified donors, measured CN (donor_map) and D-MAE3 (dmae) in the benchmark scorers.

The scorers used to take "the cn nearest non-H atoms" as a build's donors, so a wrong sphere was
still scored at the target CN. Here a non-donor atom sitting closer to the metal than a real
donor must NOT be taken as a donor, and it must show up as an extra bonded atom (CN mismatch).
D-MAE3 of a structure against itself, rotated and with atoms shuffled, must be 0.
"""
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

BENCH = Path(__file__).resolve().parents[1] / "experiments" / "benchmark"
sys.path.insert(0, str(BENCH))
import dmae
import donor_map
import metrics as M

# Pt + Cl- + 2-aminoethanol bound through N only (donor spec [3]), with its O swung in to
# 1.94 A -- closer than the N (2.20 A) and the Cl (2.30 A). Heavy atoms only.
ATOMS = [("Pt", 0.0, 0.0, 0.0),
         ("Cl", 2.30, 0.0, 0.0),
         ("N", -2.20, 0.0, 0.0), ("C", -2.60, 1.40, 0.0), ("C", -1.60, 2.40, 0.0),
         ("O", -0.40, 1.90, 0.0)]
LIGANDS, SPEC = ["[Cl-]", "OCCN"], [[0], [3]]


def _xyz(atoms):
    return f"{len(atoms)}\n\n" + "".join(f"{s} {x:.4f} {y:.4f} {z:.4f}\n" for s, x, y, z in atoms)


def _arrays(atoms):
    return [a[0] for a in atoms], np.array([a[1:] for a in atoms], float)


def test_graph_donors_skip_a_nearer_non_donor():
    syms, P = _arrays(ATOMS)
    didx = donor_map.donor_indices(syms, P, 0, LIGANDS, SPEC)
    assert sorted(syms[j] for j in didx) == ["Cl", "N"]
    # nearest-atom selection would have taken O and N and dropped the Cl
    assert sorted(M.coordination_sphere(_xyz(ATOMS), "Pt", 2)[2]) == ["N", "O"]
    assert sorted(M.coordination_sphere(_xyz(ATOMS), "Pt", 2, donor_idx=didx)[2]) == ["Cl", "N"]


def test_detected_cn_counts_the_extra_bonded_atom():
    syms, P = _arrays(ATOMS)
    assert donor_map.detected_cn(syms, P, 0) == 3        # Cl, N and the stray O
    far = [a if a[0] != "O" else ("O", -0.40, 3.20, 0.0) for a in ATOMS]
    far = [a if a[0] != "C" or a[2] != 2.40 else ("C", -1.80, 2.70, 0.0) for a in far]
    s2, P2 = _arrays(far)
    assert donor_map.detected_cn(s2, P2, 0) == 2


def test_hydrides_count_only_against_a_hydride_reference():
    atoms = ATOMS + [("H", 0.0, -1.60, 0.0)]                # a metal-only H (hydride)
    syms, P = _arrays(atoms)
    assert donor_map.detected_cn(syms, P, 0) == 4
    assert donor_map.detected_cn(syms, P, 0, count_h=False) == 3


def test_chelate_bridgehead_is_not_counted_as_bonded():
    # kappa2-carboxylate: both O at 2.0 A are bonded; the C between them sits at ~2.4 A, inside
    # the Mn-C cut-off by geometry alone (UQUBEO read as CN 7 instead of 6)
    atoms = [("Mn", 0, 0, 0), ("O", 1.70, 1.08, 0), ("O", 1.70, -1.08, 0), ("C", 2.38, 0, 0),
             ("C", 3.88, 0, 0)]
    syms, P = _arrays(atoms)
    assert donor_map.detected_cn(syms, P, 0) == 2
    # an eta2 pair (both carbons at one distance, bonded to each other) stays counted
    eta = [("Mn", 0, 0, 0), ("C", 2.05, 0.67, 0), ("C", 2.05, -0.67, 0)]
    s2, P2 = _arrays(eta)
    assert donor_map.detected_cn(s2, P2, 0) == 2


def test_donor_substituent_is_not_counted_as_bonded():
    # a bent Zr alkoxide: O at 2.00 A is bonded; its carbon sits at ~2.7 A, inside the 2.91 A
    # Zr-C cut-off by geometry alone (DEVFOA read as CN 8 instead of 6)
    atoms = [("Zr", 0, 0, 0), ("O", 2.00, 0, 0), ("C", 2.40, 1.36, 0), ("C", 3.90, 1.50, 0)]
    syms, P = _arrays(atoms)
    assert 2.7 < float(np.linalg.norm(P[2])) < 2.91
    assert donor_map.detected_cn(syms, P, 0) == 1
    # a carbon that close to the metal with NO nearer bonded neighbour is still an extra atom
    stray = [("Zr", 0, 0, 0), ("O", 2.00, 0, 0), ("C", 0, 2.70, 0)]
    s2, P2 = _arrays(stray)
    assert donor_map.detected_cn(s2, P2, 0) == 2
    # side-on N-N (2.10 / 2.30 A): the farther atom is a donor, not a substituent
    eta = [("Zr", 0, 0, 0), ("N", 2.10, 0, 0), ("N", 1.90, 1.30, 0)]
    s3, P3 = _arrays(eta)
    assert donor_map.detected_cn(s3, P3, 0) == 2


def test_symmetric_ligand_maps_to_the_bound_end():
    # ethylenediamine bound through ONE N: whichever RDKit index the spec names, the bound N wins
    atoms = [("Pt", 0, 0, 0), ("Cl", 2.3, 0, 0),
             ("N", -2.05, 0, 0), ("C", -2.6, 1.35, 0), ("C", -4.1, 1.35, 0), ("N", -4.65, 2.7, 0)]
    syms, P = _arrays(atoms)
    for spec in ([[0], [0]], [[0], [3]]):
        didx = donor_map.donor_indices(syms, P, 0, ["[Cl-]", "NCCN"], spec)
        assert 2 in didx and 5 not in didx


def test_unmatched_ligand_gives_none():
    syms, P = _arrays(ATOMS)
    assert donor_map.donor_indices(syms, P, 0, LIGANDS, None) is None
    assert donor_map.donor_indices(syms, P, 0, ["[Cl-]", "OCCCN"], [[0], [4]]) is None


def test_hydride_ligand_is_skipped():
    syms, P = _arrays(ATOMS)
    didx = donor_map.donor_indices(syms, P, 0, LIGANDS + ["[H-]"], SPEC + [[0]])
    assert sorted(syms[j] for j in didx) == ["Cl", "N"]


def test_dmae_of_a_structure_with_itself_rotated_is_zero():
    syms, P = _arrays(ATOMS)
    didx = donor_map.donor_indices(syms, P, 0, LIGANDS, SPEC)
    c = dmae.core_from_xyz(_xyz(ATOMS), "Pt", 2, donor_idx=didx)
    assert dmae.core_size(c) == 5     # Pt, Cl, N, C, C: the O is 4 bonds out (Pt-N-C-C-O)
    rng = np.random.default_rng(0)
    perm = np.r_[0, 1 + rng.permutation(len(ATOMS) - 1)]
    Q = (P @ Rotation.random(random_state=3).as_matrix().T)[perm]
    moved = [(syms[k], *Q[i]) for i, k in enumerate(perm)]
    d2 = donor_map.donor_indices([a[0] for a in moved], Q, 0, LIGANDS, SPEC)
    c2 = dmae.core_from_xyz(_xyz(moved), "Pt", 2, donor_idx=d2)
    v, n = dmae.dmae(c, c2)
    assert v < 1e-3 and n == 5                          # .xyz text keeps 4 decimals
    stretched = [a if a[0] != "Cl" else ("Cl", 2.60, 0.0, 0.0) for a in ATOMS]
    c3 = dmae.core_from_xyz(_xyz(stretched), "Pt", 2, donor_idx=didx)
    assert dmae.dmae(c, c3)[0] > 0.05


@pytest.mark.slow
def test_crystal_depth3_cores_score_zero_against_themselves():
    path = BENCH / "benchmark_cores_d3_pilot.json.gz"
    if not path.exists():  # CSD crystal coordinates: kept private, not distributed
        pytest.skip("CSD crystal coordinates are not distributed with MeCoBi")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        cores = json.load(fh)
    rng = np.random.default_rng(1)
    for rc in list(cores)[:8]:
        c = cores[rc]
        m = np.asarray(c["metal"]["xyz"], float)
        Rm = Rotation.random(random_state=len(rc)).as_matrix()
        atoms = [{"el": a["el"], "xyz": ((np.asarray(a["xyz"]) - m) @ Rm.T + m).tolist()}
                 for a in c["atoms"]]
        rng.shuffle(atoms)
        v, n = dmae.dmae(c, {"metal": c["metal"], "atoms": atoms})
        assert v < 1e-6 and n == dmae.core_size(c), rc


@pytest.mark.slow     # run.py imports the MeCoBi pipeline (stk)
def test_score_reports_cn_mismatch():
    import run as R

    syms, P = _arrays(ATOMS)
    didx = donor_map.donor_indices(syms, P, 0, LIGANDS, SPEC)
    exp = {"metal_xyz": [0.0, 0.0, 0.0], "donors": [[2.3, 0.0, 0.0], [-2.1, 0.0, 0.0]],
           "donor_elements": ["Cl", "N"]}
    sc = R.score(_xyz(ATOMS), "Pt", 2, exp, didx)
    assert sc["donor_source"] == "graph"
    assert sc["cn_detected"] == 3 and sc["cn_match"] is False
    assert sc["bond_rmsd"] < 0.15                         # scored on Cl + N, not on the stray O
