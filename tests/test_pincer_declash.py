"""Regression: a bulky multidentate must not jam a small co-ligand into a clash.

A Mn(III) hydrido-carbonyl PCP pincer seats the carbonyl at a cis site flanked by
the pincer's isopropyl arms. The raw placement put the CO carbon ~1.6 Å from an
isopropyl methyl (and ~0.8 Å from one of its hydrogens); xtb then "resolved" the
overlap by forging a spurious C–C bond and bending the carbonyl to ~68°.

The metal-excluded UFF de-clash (optimize.declash_bulky_ligands) used to fire only
for bulky MONODENTATES, so the tridentate pincer's bulk never triggered it. It now
fires for a bulky ligand of any denticity, splaying the isopropyl arm off the CO.
This is checked pre-xtb (relax off, fast): the de-clash runs before relaxation.
"""

import math

from mecobi import inputs, perception, pipeline

PINCER = "CC(C)P(C(C)C)CC1=[C-]C(CP(C(C)C)C(C)C)=CC=C1"
CELLS = ["Mn", "3", PINCER, "[C-]#[O+]", "[H-]", "[Br-]"]


def _read_xyz(path):
    with open(path) as fh:
        lines = fh.read().splitlines()
    n = int(lines[0])
    return [(p[0], float(p[1]), float(p[2]), float(p[3]))
            for p in (ln.split() for ln in lines[2:2 + n])]


def test_pincer_isopropyl_does_not_jam_the_carbonyl(tmp_path):
    cx = perception.perceive_complex(inputs.parse_row(CELLS))
    results = pipeline.build_complex(cx, tmp_path, all_isomers=False, relax=False)
    assert results
    atoms = _read_xyz(results[0].xyz_path)

    # the carbonyl carbon = the C bonded to the (single) O
    oi = next(i for i, a in enumerate(atoms) if a[0] == "O")
    ci = min((i for i, a in enumerate(atoms) if a[0] == "C"),
             key=lambda i: math.dist(atoms[i][1:], atoms[oi][1:]))
    assert math.dist(atoms[ci][1:], atoms[oi][1:]) < 1.4  # sanity: it really is the C≡O

    # nearest non-CO heavy atom and nearest H to the carbonyl carbon
    heavy = min(math.dist(atoms[ci][1:], atoms[j][1:]) for j, a in enumerate(atoms)
                if j not in (ci, oi) and a[0] not in ("H", "Mn"))
    hydro = min(math.dist(atoms[ci][1:], atoms[j][1:]) for j, a in enumerate(atoms)
                if a[0] == "H")
    # de-clashed: heavy contact ~2.6 Å (a normal cis neighbour), H ~2.3 Å. The old
    # jammed placement gave ~1.6 Å / ~0.8 Å (a fusion waiting to happen in xtb).
    assert heavy > 2.2, f"carbonyl carbon still clashing a heavy atom at {heavy:.2f} Å"
    assert hydro > 1.5, f"carbonyl carbon still clashing an H at {hydro:.2f} Å"
