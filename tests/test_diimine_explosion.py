"""Regression: a bulky N-aryl α-diimine chelate must not explode during assembly.

The bidentate pre-organisation snaps the N=C–C=N dihedral to s-cis to fold the bite
toward the metal. On a diimine bearing an aryl on each donor nitrogen that snap slams
the two phenyls into overlap, and the subsequent UFF minimisation used to DIVERGE and
blow the ligand apart (aromatic C–C stretched past 2.5 Å) — so xtb then re-formed a
scrambled graph. The pre-organisation now reverts an exploded conformer and refolds
with the distance restraint alone. Pure RDKit/stk, no xtb (fast).
"""

import math

from mecobi import inputs, perception, pipeline
from mecobi.assembly import _chem

# glyoxal-bis(phenylimine): Ph-N=CH-CH=N-Ph, a classic α-diimine N,N-chelate.
DIIMINE = r"C1(/N=C\C=N/C2=CC=CC=C2)=CC=CC=C1"


def _worst_heavy_bond(bb) -> float:
    P = bb.get_position_matrix()
    atoms = list(bb.get_atoms())
    worst = 0.0
    for b in bb.get_bonds():
        i, j = b.get_atom1().get_id(), b.get_atom2().get_id()
        if atoms[i].__class__.__name__ == "H" or atoms[j].__class__.__name__ == "H":
            continue
        worst = max(worst, math.dist(P[i], P[j]))
    return worst


def test_diimine_building_block_conformer_is_not_exploded():
    # donors are the two imine nitrogens (RDKit indices 1 and 4, no explicit Hs).
    bb = _chem.ligand_building_block(DIIMINE, [1, 4])
    worst = _worst_heavy_bond(bb)
    assert worst < 1.8, f"diimine conformer exploded: longest heavy–heavy bond {worst:.2f} Å"


def _isolated_heavy_atoms(xyz_path) -> list:
    with open(xyz_path) as fh:
        lines = fh.read().splitlines()
    n = int(lines[0])
    atoms = [(p[0], float(p[1]), float(p[2]), float(p[3]))
             for p in (ln.split() for ln in lines[2:2 + n])]
    out = []
    for i, a in enumerate(atoms):
        if a[0] == "H":
            continue
        nn = min((math.dist(a[1:], b[1:]) for j, b in enumerate(atoms)
                  if j != i and b[0] != "H"), default=99.0)
        if nn > 2.0 and a[0] not in ("Ni", "Br"):
            out.append((i, a[0], round(nn, 2)))
    return out


def test_diimine_complex_assembles_with_every_atom_bonded(tmp_path):
    # Ni(II) diimine dibromide — the reported case. relax off (no xtb) keeps this fast;
    # the bug showed up already in the pre-xtb assembly, so this is enough to catch it.
    cx = perception.perceive_complex(
        inputs.parse_row(["Ni", "2", "[Br-]", "[Br-]", DIIMINE]))
    results = pipeline.build_complex(cx, tmp_path, all_isomers=False, relax=False)
    assert results
    for r in results:
        stranded = _isolated_heavy_atoms(r.xyz_path)
        assert not stranded, f"assembly stranded heavy atoms (broken bonds): {stranded}"
