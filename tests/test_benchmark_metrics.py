"""Self-consistency of the benchmark scorers (experiments/benchmark): a structure compared with
itself -- rotated, mirrored, atoms shuffled -- must score 0, and the shape measure must find the
TRUE minimum. Guards the fixes from the 2 Oct 2026 metrics review: c-kmRMSD used to depend on the
build's orientation (crystal core vs itself rotated: 1.4-2.1 A), the 6-start CShM missed the
minimum for ~15% of spheres, and the distance-matrix pairing heuristic over-reported."""
import gzip
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial.distance import cdist
from scipy.spatial.transform import Rotation

BENCH = Path(__file__).resolve().parents[1] / "experiments" / "benchmark"
sys.path.insert(0, str(BENCH))
import metrics as M
from ckmrmsd import ckmrmsd, core_size

# crystal cores/spheres named in the review (orientation-sensitive c-kmRMSD, mislabelled CShM,
# over-reported dmat) plus a spread of CNs
REFCODES = ["IWOWEY", "NAGDOO", "VALGOF", "VEQGEH", "XUPJEY", "KUQCIK", "AYUBON", "WEWNUH"]


# The crystal cores/spheres are CSD coordinates: they stay in the private working copy and are not
# distributed, so these tests skip where the files are absent (anyone with the CSD can regenerate
# them with experiments/benchmark/extract_cores.py and dataprep/extract_spheres.py).
CSD_DATA_MISSING = "CSD crystal coordinates are not distributed with MeCoBi"


def _load(name):
    if not (BENCH / name).exists():
        pytest.skip(f"{name}: {CSD_DATA_MISSING}")
    with gzip.open(BENCH / name, "rt", encoding="utf-8") as fh:
        d = json.load(fh)
    return d if isinstance(d, dict) else {r["refcode"]: r for r in d}


# the frozen crystal data take a few seconds to read -> those tests are in the full suite only
data = pytest.mark.slow


@pytest.fixture(scope="module")
def cores():
    d = _load("benchmark_cores.json.gz")
    return {k: d[k] for k in REFCODES if k in d}


@pytest.fixture(scope="module")
def spheres():
    d = _load("benchmark_spheres.json.gz")
    return {k: d[k] for k in REFCODES if k in d}


def _transform(core, Rm, rng):
    """The core rotated about its metal by Rm (proper or improper), donor and depth-2 lists
    shuffled."""
    m = np.asarray(core["metal"]["xyz"], float)

    def mv(a):
        return {"el": a["el"], "xyz": ((np.asarray(a["xyz"], float) - m) @ Rm.T + m).tolist()}

    donors, depth2 = [mv(a) for a in core["donors"]], [mv(a) for a in core["depth2"]]
    rng.shuffle(donors)
    rng.shuffle(depth2)
    return {"metal": core["metal"], "donors": donors, "depth2": depth2}


def _brute_cshm(Q, P0):
    """Reference CShM: every permutation, Kabsch + scale fit each (proper rotations)."""
    Q = Q - Q.mean(0)
    P0 = P0 - P0.mean(0)
    best = math.inf
    for perm in itertools.permutations(range(len(Q))):
        P = P0[list(perm)]
        Pr = P @ M._kabsch(P, Q).T
        s = (Q * Pr).sum() / (Pr * Pr).sum()
        best = min(best, 100 * ((Q - s * Pr) ** 2).sum() / (Q * Q).sum())
    return best


def _dirs(s):
    D = np.asarray(s["donors"], float) - np.asarray(s["metal_xyz"], float)
    return D / np.linalg.norm(D, axis=1, keepdims=True)


# --------------------------------------------------------------------------- c-kmRMSD
def _octahedral_core():
    """A symmetric synthetic depth-2 core, Pt(NC2)6: the case a single-start optimiser gets wrong
    (many near-equivalent wrong pairings)."""
    axes = np.vstack([np.eye(3), -np.eye(3)])
    donors, depth2 = [], []
    for k, a in enumerate(axes):
        n = 2.05 * a
        perp = np.roll(a, 1) if k % 2 == 0 else np.roll(a, 2)
        donors.append({"el": "N", "xyz": n.tolist()})
        depth2 += [{"el": "C", "xyz": (n + 1.47 * (0.6 * a + 0.8 * s * perp)).tolist()}
                   for s in (1, -1)]
    return {"metal": {"el": "Pt", "xyz": [0.0, 0.0, 0.0]}, "donors": donors, "depth2": depth2}


def test_ckmrmsd_is_orientation_independent_on_a_symmetric_core():
    core, rng = _octahedral_core(), np.random.default_rng(2)
    for k in range(5):
        Rm = Rotation.random(random_state=k).as_matrix()
        val, nm = ckmrmsd(core, _transform(core, Rm, rng))
        assert val < 1e-3, f"rotation {k}: {val:.3f} A"
        assert nm == core_size(core) == 19


@data
def test_ckmrmsd_of_a_core_with_itself_rotated_is_zero(cores):
    assert cores, "none of the review refcodes are in benchmark_cores.json.gz"
    rng = np.random.default_rng(3)
    for rc, core in cores.items():
        for k in range(3):
            Rm = Rotation.random(random_state=100 + k).as_matrix()
            val, nm = ckmrmsd(core, _transform(core, Rm, rng))
            assert val < 1e-3, f"{rc}: rotated self-comparison gave {val:.3f} A"
            assert nm == core_size(core)


@data
def test_ckmrmsd_matches_a_mirror_image(cores):
    rng = np.random.default_rng(4)
    core = next(iter(cores.values()))
    mirror = np.diag([-1.0, 1.0, 1.0]) @ Rotation.random(random_state=7).as_matrix()
    assert ckmrmsd(core, _transform(core, mirror, rng))[0] < 1e-3


@data
def test_ckmrmsd_reports_missing_atoms(cores):
    core = next(iter(cores.values()))
    short = dict(core, depth2=core["depth2"][:-1])
    _, nm = ckmrmsd(core, short)
    assert nm == core_size(core) - 1


# --------------------------------------------------------------------------- CShM
@pytest.mark.parametrize("cn,name", [(cn, n) for cn, d in M._IDEAL.items() for n in d])
def test_ideal_shape_scores_zero_against_itself_rotated(cn, name):
    vecs = M._IDEAL[cn][name]
    Rm = Rotation.random(random_state=cn).as_matrix()
    q = (vecs @ Rm.T)[np.random.default_rng(cn).permutation(cn)]
    assert M.continuous_shape_measure(q, vecs) < 1e-6
    assert M.best_shape(q, cn)[0] == name


def test_shape_ideals_follow_shape():
    spy = M._IDEAL[5]["square_pyramidal"]
    apex = np.argmax(spy[:, 2])
    angles = [math.degrees(math.acos(spy[apex] @ v)) for i, v in enumerate(spy) if i != apex]
    assert np.allclose(angles, 104.48, atol=0.01)      # SHAPE SPY-5, not the vacant octahedron
    sapr = M._IDEAL[8]["square_antiprism"]
    edges = np.sort(cdist(sapr, sapr), axis=1)[:, 1:5]  # each vertex has 4 edges (2 in its own
    assert np.allclose(edges, edges.min(), atol=1e-6)   # square, 2 to the other) of ONE length


@data
def test_cshm_finds_the_true_minimum_on_crystal_spheres(spheres):
    checked = 0
    for rc, s in spheres.items():
        q = _dirs(s)
        if not 4 <= len(q) <= 6:
            continue
        for name, vecs in M._IDEAL[len(q)].items():
            assert abs(M.continuous_shape_measure(q, vecs) - _brute_cshm(q, vecs)) < 1e-6, \
                (rc, name)
        checked += 1
    assert checked


@data
def test_poly_cshm_of_a_sphere_with_itself_is_zero(spheres):
    rng = np.random.default_rng(5)
    for rc, s in spheres.items():
        q = _dirs(s)
        for Rm in (Rotation.random(random_state=1).as_matrix(),
                   np.diag([-1.0, 1.0, 1.0])):            # reflections allowed, as in SHAPE
            b = (q @ Rm.T)[rng.permutation(len(q))]
            assert M.shape_deviation(b, q) < 1e-6, rc


@pytest.mark.slow     # run.py imports the MeCoBi pipeline (stk)
def test_shape_match_is_none_without_an_ideal_shape():
    import run as R

    # CN10: no ideal shape at this CN -> '' on both sides must not count as a match
    dirs = Rotation.random(10, random_state=0).apply([0.0, 0.0, 1.0])
    exp = {"metal_xyz": [0.0, 0.0, 0.0], "donors": (2.4 * dirs).tolist(),
           "donor_elements": ["O"] * 10}
    xyz = "11\n\nLa 0 0 0\n" + "".join(f"O {x:.4f} {y:.4f} {z:.4f}\n" for x, y, z in 2.4 * dirs)
    assert R.score(xyz, "La", 10, exp)["shape_match"] is None


# --------------------------------------------------------------------------- distance matrix
@data
def test_dmat_rmsd_is_the_optimal_pairing(spheres):
    rng = np.random.default_rng(6)
    for rc, s in spheres.items():
        E = np.asarray(s["donors"], float) - np.asarray(s["metal_xyz"], float)
        if len(E) > 7:
            continue
        assert M.local_distance_matrix_rmsd(E, E[rng.permutation(len(E))]) < 1e-9
        B = (E + rng.normal(0, 0.25, E.shape))[rng.permutation(len(E))]
        DE, DB = cdist(E, E), cdist(B, B)
        iu = np.triu_indices(len(E), 1)
        opt = min(np.sqrt(np.mean((DE[iu] - DB[np.ix_(p, p)][iu]) ** 2))
                  for p in map(list, itertools.permutations(range(len(E)))))
        assert abs(M.local_distance_matrix_rmsd(E, B) - opt) < 1e-9, rc


@pytest.mark.parametrize("angle, name", [(62, "bent"), (84, "bent"), (120, "bent"),
                                         (145, "linear"), (170, "linear"), (180, "linear")])
def test_cn2_shape_reads_the_donor_metal_donor_angle(angle, name):
    # Two donors alone are always "a segment"; the metal vertex makes linear vs bent visible.
    t = math.radians(angle)
    q = np.array([[1.0, 0.0, 0.0], [math.cos(t), math.sin(t), 0.0]])
    assert M.best_shape(q, 2)[0] == name
    assert M.shape_deviation(q, q) < 1e-6
    assert M.shape_deviation(M._IDEAL[2]["linear"], M._IDEAL[2]["bent"]) > 20
