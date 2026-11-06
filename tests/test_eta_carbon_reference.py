"""M-L reference for hapto carbons (Cp, arene, alkene, allyl): optimize._donor_key.

The re-mined table keeps sigma carbons in the ``C`` bins, so a Cp carbon looked up as ``C`` was
restrained to the sigma distance (Ti(IV): 2.1 A against a real Ti-Cp of 2.37 A; the pilot A/B had
haptic complexes 22 better / 40 worse). A carbon donor bonded to a fellow donor is now looked up
under its own ``C_eta`` class. Pure geometry + table; no xtb.
"""
import math

import pytest

from mecobi import optimize

TI = ("Ti", (0.0, 0.0, 0.0))


def _cp(height=2.05, r=1.21):
    """Five ring carbons of an eta5-Cp above the metal (M-C about 2.38 A)."""
    return [("C", (r * math.cos(2 * math.pi * k / 5), r * math.sin(2 * math.pi * k / 5), height))
            for k in range(5)]


def test_cp_carbons_are_hapto_and_a_sigma_carbon_is_not():
    atoms = [TI, *_cp(), ("C", (2.10, 0.0, -0.6)), ("C", (2.80, 1.2, -1.0))]   # Cp + an ethyl
    donors = [1, 2, 3, 4, 5, 6]
    for d in range(1, 6):
        assert optimize._donor_key(atoms, d, 0, donors) == optimize.ETA_CARBON
    assert optimize._donor_key(atoms, 6, 0, donors) == "C"       # its neighbour is no donor
    assert optimize._donor_key(atoms, 1, 0) == "C"               # no donor list: never hapto


def test_side_on_alkene_is_hapto_and_a_carbonyl_stays_sp():
    atoms = [TI, ("C", (2.05, 0.68, 0.0)), ("C", (2.05, -0.68, 0.0)),
             ("C", (0.0, 0.0, 1.95)), ("O", (0.0, 0.0, 3.10))]
    donors = [1, 2, 3]
    assert optimize._donor_key(atoms, 1, 0, donors) == optimize.ETA_CARBON
    assert optimize._donor_key(atoms, 3, 0, donors) == optimize.SP_CARBON


@pytest.fixture
def table(monkeypatch):
    tab = {"metal_os_donor_cn": {}, "metal_os_donor": {"Xx|4|C": {"mean": 2.10, "n": 50}},
           "metal_donor": {"Xx|C_eta": {"mean": 2.38, "n": 50}}}
    monkeypatch.setattr(optimize, "_ML_TABLE", tab)
    monkeypatch.setattr(optimize, "_ML_LOADED", True)
    return tab


def test_hapto_carbon_gets_its_own_reference(table):
    assert optimize._ml_target("Xx", 4, "C", 8) == 2.10
    assert optimize._ml_target("Xx", 4, optimize.ETA_CARBON, 8) == 2.38


def test_hapto_carbon_falls_back_to_plain_carbon_in_an_older_table(table):
    del table["metal_donor"]["Xx|C_eta"]      # a table mined before the class existed
    assert optimize._ml_target("Xx", 4, optimize.ETA_CARBON, 8) == 2.10
