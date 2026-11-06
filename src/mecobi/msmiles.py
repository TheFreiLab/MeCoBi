"""MetalloGen m-SMILES: coordination-site table and shape fit for the reverse direction.

m-SMILES (Lee, Park, Park & Kim, "MetalloGen: Automated 3D Conformer Generation for Diverse
Coordination Complexes", J. Chem. Inf. Model. 2025, 65, 11878-11891) writes a mononuclear complex
as ``[M+q]|ligand|ligand|...|<CN>_<geometry>``. Each donor atom carries an atom-map number naming
the 1-based coordination site it occupies in the geometry's ideal site-vector set; all atoms of a
haptic group share one number. That makes it an isomer-exact string: :func:`match_shape` recovers
the geometry and the donor -> site numbering from 3D donor directions, the way MetalloGen's own
``utils/shape.py::assign_shape`` does for a structure input (centroid direction per binding site,
best rotation over seeded site permutations, one site per binding site). Two refinements over that
reference: site vectors are normalised before fitting (several upstream entries are not unit
length, which would bias the choice between geometries of one CN), and the assignment is a
Kuhn-Munkres bijection rather than per-vector argmax.

``GEOMETRY_VECTORS`` / ``CN_GEOMETRIES`` are copied verbatim from MetalloGen's
``MetalloGen/globalvars.py`` (``known_geometries_vector_dict`` / ``CN_known_geometries_dict``,
commit fa26e2a; keys keep upstream spellings such as ``8_squre_antiprismatic``, because those
strings ARE the m-SMILES geometry tokens). Two upstream entries are not a valid site set and are
skipped by :func:`usable_geometries`: ``7_capped_octahedral`` repeats a vector and
``8_bicapped_trigonal_prismatic`` lists nine.

The table is redistributed under MetalloGen's licence:

    BSD 3-Clause License

    Copyright (c) 2025, KyunghoonLee

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, this
       list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright notice,
       this list of conditions and the following disclaimer in the documentation
       and/or other materials provided with the distribution.

    3. Neither the name of the copyright holder nor the names of its
       contributors may be used to endorse or promote products derived from
       this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from __future__ import annotations

from functools import cache
from itertools import permutations

import numpy as np

_PI = np.pi

# fmt: off
GEOMETRY_VECTORS: dict[str, list[list[float]]] = {
    # CN 2
    "2_linear": [[0, 0, 1], [0, 0, -1]],
    "2_bent_135": [[0, 0, 1], [0, 1 / np.sqrt(2), -1 / np.sqrt(2)]],
    "2_bent_90": [[0, 0, 1], [0, 1, 0]],
    # CN 3
    "3_trigonal_planar": (np.array([[2, 0, 0], [-1, np.sqrt(3), 0], [-1, -np.sqrt(3), 0]]) / 2).tolist(),
    "3_trigonal_pyramidal": (np.array([[1, -1, -1], [-1, 1, -1], [-1, -1, 1]]) / np.sqrt(3)).tolist(),
    "3_t_shaped": [[0, 0, 1], [0, 1, 0], [0, 0, -1]],
    # CN 4
    "4_tetrahedral": (np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]]) / np.sqrt(3)).tolist(),
    "4_square_planar": [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0]],
    "4_seesaw": [[0, 0, 1], [0, 0, -1], [1, 0, 0], [0, 1, 0]],
    # CN 5
    "5_trigonal_bipyramidal": (np.array([[0, 0, 2], [0, 0, -2], [2, 0, 0], [-1, np.sqrt(3), 0],
                                         [-1, -np.sqrt(3), 0]]) / 2).tolist(),
    "5_square_pyramidal": [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1]],
    "5_pentagonal_planar": [[np.cos(2 * _PI * k / 5), np.sin(2 * _PI * k / 5), 0] for k in range(5)],
    # CN 6
    "6_octahedral": [[0, 0, 1], [0, 0, -1], [0, 1, 0], [0, -1, 0], [1, 0, 0], [-1, 0, 0]],
    "6_pentagonal_pyramidal": [[0, 0, 1]] + [[np.cos(2 * _PI * k / 5), np.sin(2 * _PI * k / 5), 0]
                                             for k in range(5)],
    "6_trigonal_prismatic": (np.array([[1.511, 0.0, 1.31], [-0.756, 1.309, 1.309],
                                       [-0.756, -1.309, 1.309], [1.511, 0.0, -1.31],
                                       [-0.756, 1.309, -1.309], [-0.756, -1.309, -1.309]]) / 2).tolist(),
    "6_hexagonal_planar": [[np.cos(2 * _PI * k / 6), np.sin(2 * _PI * k / 6), 0] for k in range(6)],
    # CN 7
    "7_pentagonal_bipyramidal": [[0, 0, 1], [0, 0, -1]] + [[np.cos(2 * _PI * k / 5),
                                                            np.sin(2 * _PI * k / 5), 0]
                                                           for k in range(5)],
    "7_capped_trigonal_prismatic": (np.array([[1.511, 0.0, 1.31], [-0.756, 1.309, 1.309],
                                              [-0.756, -1.309, 1.309], [1.511, 0.0, -1.31],
                                              [-0.756, 1.309, -1.309], [-0.756, -1.309, -1.309],
                                              [-2.0, 0.0, 0.0]]) / 2).tolist(),
    "7_capped_octahedral": (np.array([[0, 0, 2], [0, 0, 2], [0, 2, 0], [0, -2, 0], [2, 0, 0],
                                      [-2, 0, 0], [1.155, 1.155, 1.155]]) / 2).tolist(),
    "7_hexagonal_pyramidal": [[0, 0, 1]] + [[np.cos(2 * _PI * k / 6), np.sin(2 * _PI * k / 6), 0]
                                            for k in range(6)],
    # CN 8
    "8_squre_antiprismatic": (np.array([[-1, 1, 1], [1, 1, 1], [-1, -1, 1], [1, -1, 1],
                                        [-1.41, 0, -1], [0, -1.41, -1], [1.41, 0, -1],
                                        [0, 1.41, -1]]) / np.sqrt(3)).tolist(),
    "8_sqaure_prismatic": (np.array([[-1, 1, 1], [1, 1, 1], [-1, -1, 1], [1, -1, 1], [-1, 1, -1],
                                     [-1, -1, -1], [1, -1, -1], [1, 1, -1]]) / np.sqrt(3)).tolist(),
    "8_bicapped_trigonal_prismatic": (np.array([[1.511, 0.0, 1.31], [-0.756, 1.309, 1.309],
                                                [-0.756, -1.309, 1.309], [1.511, 0.0, -1.31],
                                                [-0.756, 1.309, -1.309], [-0.756, -1.309, -1.309],
                                                [-2.0, 0.0, 0.0], [1.16, -1.62, 0],
                                                [1.16, 1.62, 0]]) / 2).tolist(),
    "8_hexagonal_bipyramidal": [[0, 0, 1], [0, 0, -1]] + [[np.cos(2 * _PI * k / 6),
                                                           np.sin(2 * _PI * k / 6), 0]
                                                          for k in range(6)],
    "8_dodecahedral": [[1.289, 0.411, 0], [-1.289, 0.411, 0], [0, -0.411, 1.289],
                       [0, -0.411, -1.289], [1, -1.568, 0], [-1, -1.568, 0], [0, 1.568, 1],
                       [0, 1.568, -1]],
    "8_axial_bicapped_trigonal_prismatic": (np.array([
        [-0.77660752, 0.7455247, 1.68554848], [0.84666207, -0.75727505, -1.64611599],
        [-1.89364682, 0.64292567, -0.02735548], [-1.1421033, -0.44716888, -1.57975949],
        [-0.05187737, -1.12955356, 1.64967193], [1.08122157, -1.67863101, 0.11470761],
        [0.73916493, 1.67714792, 0.80050613], [1.25857889, 1.12625782, -1.07122477],
    ]) / 2).tolist(),
    # CN 9
    "9_capped_square_antiprismatic": [[-1, 1, 1], [1, 1, 1], [-1, -1, 1], [1, -1, 1],
                                      [-1.41, 0, -1], [0, -1.41, -1], [1.41, 0, -1],
                                      [0, 1.41, -1], [0, 0, 1.73]],
    "9_tricapped_trigonal_prismatic": [[1.511, 0.0, 1.31], [-0.756, 1.309, 1.309],
                                       [-0.756, -1.309, 1.309], [1.511, 0.0, -1.31],
                                       [-0.756, 1.309, -1.309], [-0.756, -1.309, -1.309],
                                       [-2.0, 0.0, 0.0], [1.16, -1.62, 0], [1.16, 1.62, 0]],
    "9_tri_tri_mer_capped": [
        [-0.32238184, 0.16659695, -1.96680335], [1.82278439, -0.47604810, 0.67144270],
        [-1.55384060, 0.32203597, 1.21732174], [-1.56677590, -0.94884186, -0.80306439],
        [1.26907643, 1.11747728, -1.06803068], [0.88550201, -1.62631150, -0.75564351],
        [0.83666247, 1.16758890, 1.39166521], [-0.41252724, -1.36401551, 1.40331143],
        [-0.99299587, 1.73068560, -0.13669874],
    ],
    # CN 10
    "10_axial_bicapped_hexagonal_planar": [
        [-1.86281576, 0.06020958, -0.72546002], [1.86281576, 0.06020958, 0.72546002],
        [-0.65427417, -1.79359695, -0.59576447], [-1.23433283, 1.57281414, -0.05175061],
        [-0.00766799, 0.70251884, 1.87254065], [-1.23148994, -0.52774663, 1.48489596],
        [0.65420987, -1.79364224, 0.59569870], [1.23433412, 1.57281579, 0.05166980],
        [0.00758642, 0.70251895, -1.87254094], [1.23140247, -0.52774392, -1.48496947],
    ],
    # CN 12
    "12_penta_bi_capped_pyramidal": [
        [1.94669217, -0.00263606, 0.45867487], [-1.94669638, -0.00263596, -0.45865703],
        [0.80732904, -1.82239409, -0.16461956], [1.04605529, -0.25227919, -1.68585988],
        [-0.41002572, -0.89431687, -1.74128580], [-0.42780953, 1.32200287, -1.43850100],
        [0.97354769, 1.61530666, -0.66557439], [-0.80732904, -1.82239409, 0.16461956],
        [-1.04614067, -0.25228214, 1.68580646], [0.41002572, -0.89431687, 1.74128580],
        [0.42774741, 1.32205074, 1.43847627], [-0.97360413, 1.61527759, 0.66556241],
    ],
}

CN_GEOMETRIES: dict[int, list[str]] = {
    2: ["2_linear", "2_bent_135", "2_bent_90"],
    3: ["3_trigonal_planar", "3_trigonal_pyramidal", "3_t_shaped"],
    4: ["4_tetrahedral", "4_seesaw", "4_square_planar"],
    5: ["5_trigonal_bipyramidal", "5_square_pyramidal", "5_pentagonal_planar"],
    6: ["6_octahedral", "6_trigonal_prismatic", "6_pentagonal_pyramidal", "6_hexagonal_planar"],
    7: ["7_pentagonal_bipyramidal", "7_hexagonal_pyramidal", "7_capped_trigonal_prismatic",
        "7_capped_octahedral"],
    8: ["8_squre_antiprismatic", "8_sqaure_prismatic", "8_bicapped_trigonal_prismatic",
        "8_hexagonal_bipyramidal", "8_dodecahedral"],
    9: ["9_capped_square_antiprismatic", "9_tricapped_trigonal_prismatic", "9_tri_tri_mer_capped"],
    10: ["10_axial_bicapped_hexagonal_planar"],
    11: [],
    12: ["12_penta_bi_capped_pyramidal"],
}
# fmt: on

# Number of binding vectors used to seed each candidate rotation (MetalloGen uses k=5). Four
# non-coplanar-enough directions fix a rotation; the Kuhn-Munkres refit below uses all of them.
_SEED = 4


def _unit(v) -> np.ndarray:
    v = np.asarray(v, float)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


@cache
def usable_geometries(cn: int) -> tuple[str, ...]:
    """MetalloGen geometry names for ``cn`` whose site set is valid (``cn`` distinct vectors)."""
    out = []
    for name in CN_GEOMETRIES.get(cn, []):
        vecs = np.asarray(GEOMETRY_VECTORS[name], float)
        if len(vecs) != cn:
            continue
        u = _unit(vecs)
        if np.any(np.triu(u @ u.T, k=1) > 1 - 1e-6):  # two identical directions
            continue
        out.append(name)
    return tuple(out)


def _kabsch(P: np.ndarray, Q: np.ndarray) -> np.ndarray:
    """Proper rotation R minimising |P R^T - Q| (rows matched)."""
    U, _, Vt = np.linalg.svd(P.T @ Q)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    return Vt.T @ np.diag([1.0, 1.0, d]) @ U.T


def _fit(B: np.ndarray, D: np.ndarray) -> tuple[float, list[int]]:
    """Best proper-rotation fit of binding directions ``B`` onto site directions ``D``.

    Returns (rmsd, site_of) with ``site_of[i]`` the 0-based site of binding direction ``i``.
    Seeds a rotation from every ordered choice of sites for the first few binding directions
    (MetalloGen's scheme), assigns all directions by Kuhn-Munkres, refits on the full
    assignment and keeps the lowest RMSD.
    """
    from scipy.optimize import linear_sum_assignment

    n = len(B)
    k = min(_SEED, n)
    best_rmsd, best_site_of = float("inf"), None
    seen: set[tuple[int, ...]] = set()
    for perm in permutations(range(n), k):
        R = _kabsch(B[:k], D[list(perm)])
        _, col = linear_sum_assignment(-(B @ R.T) @ D.T)
        key = tuple(int(c) for c in col)
        if key in seen:
            continue
        seen.add(key)
        R = _kabsch(B, D[col])
        rmsd = float(np.sqrt(np.mean(np.sum((B @ R.T - D[col]) ** 2, axis=1))))
        if rmsd < best_rmsd - 1e-9:
            best_rmsd, best_site_of = rmsd, list(key)
    return best_rmsd, best_site_of


def match_shape(directions) -> tuple[str, list[int], float]:
    """Closest MetalloGen geometry to metal->binding-site ``directions`` (one row per site).

    Returns ``(geometry, site_of, rmsd)``: the m-SMILES geometry token, the 0-based MetalloGen
    site index of each direction (add 1 for the atom-map number) and the fit RMSD on unit
    vectors. Raises ``ValueError`` when MetalloGen has no geometry for that coordination number.
    """
    B = _unit(directions)
    names = usable_geometries(len(B))
    if not names:
        raise ValueError(f"MetalloGen has no geometry for coordination number {len(B)}")
    best = None
    for name in names:
        rmsd, site_of = _fit(B, _unit(GEOMETRY_VECTORS[name]))
        if best is None or rmsd < best[2] - 1e-9:
            best = (name, site_of, rmsd)
    return best


def metal_token(metal: str, charge: int) -> str:
    """Bracketed m-SMILES metal head, e.g. ``[Ru+2]``, ``[Ni]``, ``[Co-1]``."""
    return f"[{metal}{charge:+d}]" if charge else f"[{metal}]"
