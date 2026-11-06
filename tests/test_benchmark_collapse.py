"""hapticity_collapsed_sphere collapses eta-rings AND eta2/eta3 pi-bonds to one
site each, but leaves sigma-donors (incl. a crammed sigma-carbon) and chelate
donors distinct. Guards the DILZED eta2-alkyne scoring fix."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "benchmark"))
import metrics  # noqa: E402


def _xyz(atoms):
    lines = [str(len(atoms)), ""]
    for s, x, y, z in atoms:
        lines.append(f"{s} {x:.4f} {y:.4f} {z:.4f}")
    return "\n".join(lines) + "\n"


def test_eta2_alkene_collapses_to_one_site():
    # Pt + eta2-C=C (2 C, 1.34 A apart, each ~2.16 A from metal) + 3 Cl.
    atoms = [
        ("Pt", 0, 0, 0),
        ("C", 2.05, 0.67, 0), ("C", 2.05, -0.67, 0),   # eta2 alkene (C-C = 1.34)
        ("Cl", -2.3, 0, 0), ("Cl", 0, 2.3, 0), ("Cl", 0, -2.3, 0),
    ]
    m, donors, syms = metrics.hapticity_collapsed_sphere(_xyz(atoms), "Pt", cn=5)
    assert syms.count("X") == 1, f"eta2 not collapsed: {syms}"
    assert len(donors) == 4, f"expected 4 sites (1 pi + 3 Cl), got {len(donors)}: {syms}"
    assert sorted(s for s in syms if s != "X") == ["Cl", "Cl", "Cl"]


def test_crammed_sigma_carbon_stays_separate():
    # a CO-like sigma-C jammed 1.60 A from a ring carbon must NOT merge into the ring.
    ring = [("C", 2.10, 0.0, 0.7), ("C", 2.10, 0.67, -0.35), ("C", 2.10, -0.67, -0.35)]
    atoms = [("Ir", 0, 0, 0), *ring,
             ("C", 2.10, 0.0, -1.9),   # sigma-C at ~1.6 A from the nearest ring C
             ("P", -2.3, 0, 0)]
    m, donors, syms = metrics.hapticity_collapsed_sphere(_xyz(atoms), "Ir", cn=5)
    # ring (3 C here) -> 1 X; the crammed sigma-C stays its own 'C'; P separate
    assert syms.count("X") == 1 and syms.count("C") == 1 and "P" in syms, syms


def test_chelate_donors_not_collapsed():
    # ethylenediamine-like: 2 N ~2.7 A apart (backbone-separated) stay 2 sites.
    atoms = [("Ni", 0, 0, 0), ("N", 2.0, 1.0, 0), ("N", 2.0, -1.0, 0),
             ("Cl", -2.3, 0, 0), ("Cl", 0, 0, 2.3)]
    m, donors, syms = metrics.hapticity_collapsed_sphere(_xyz(atoms), "Ni", cn=4)
    assert "X" not in syms and syms.count("N") == 2, syms
