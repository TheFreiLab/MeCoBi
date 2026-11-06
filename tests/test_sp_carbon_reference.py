"""M-L reference for sp-carbon donors (carbonyl, cyanide, isocyanide): optimize._donor_key.

The CSD table is keyed by donor element, so its ``C`` bins average carbonyl carbons with Cp /
arene / alkyl / aryl carbons (Fe(0) CN5: 2.03 A, against a real Fe-CO of ~1.78 A). The xtb
distance restraint then held every M-CO too long (pilot-100: +0.13 A on average, CBFMOP +0.25 A).
An sp carbon is now looked up under its own ``C_sp`` class. Pure geometry + table; no xtb.
"""
from mecobi import optimize

FE = ("Fe", (0.0, 0.0, 0.0))


def test_carbonyl_and_cyanide_carbons_are_sp():
    co = [FE, ("C", (1.78, 0.0, 0.0)), ("O", (2.93, 0.0, 0.0))]
    cn = [FE, ("C", (1.92, 0.0, 0.0)), ("N", (3.08, 0.0, 0.0))]
    iso = [FE, ("C", (1.85, 0.0, 0.0)), ("N", (3.01, 0.0, 0.0)), ("C", (4.44, 0.0, 0.0))]
    for atoms in (co, cn, iso):
        assert optimize._donor_key(atoms, 1, 0) == optimize.SP_CARBON


def test_a_cis_donor_in_a_crowded_sphere_is_not_a_substituent():
    # DILZED (Mo, CN7): in the still-crushed pre-relax sphere a cis iodide sat 2.11 A from the
    # carbonyl carbon -- a real C-I bond length -- but it is the metal's donor, not a substituent
    atoms = [("Mo", (0.0, 0.0, 0.0)), ("C", (2.2, 0.0, 0.0)), ("O", (3.33, 0.0, 0.0)),
             ("I", (1.35, 1.93, 0.0))]
    assert optimize._donor_key(atoms, 1, 0) == optimize.SP_CARBON


def test_compressed_carbonyl_is_still_sp():
    # a squeezed pre-relax W-CO (W-C 1.75 A): the O is inside the radius used to spot the
    # metal's own donors, but it is the carbon's triple-bond partner
    atoms = [("W", (0.0, 0.0, 0.0)), ("C", (1.75, 0.0, 0.0)), ("O", (2.88, 0.0, 0.0))]
    assert optimize._donor_key(atoms, 1, 0) == optimize.SP_CARBON
    # eta2-acyl: the O is bonded to the metal too, M-C-O is far from linear
    eta2 = [FE, ("C", (1.85, 0.0, 0.0)), ("O", (1.60, 1.20, 0.0)), ("C", (3.10, -0.85, 0.0))]
    assert optimize._donor_key(eta2, 1, 0) == "C"


def test_bent_metallacyclic_acyl_is_not_sp():
    # C(=O) whose other substituent is itself a donor (kappa2-C,S): one free O partner, but
    # M-C-O ~125 deg, not linear
    atoms = [FE, ("C", (1.90, 0.0, 0.0)), ("O", (2.55, 1.00, 0.0)), ("S", (1.20, -1.60, 0.0))]
    assert optimize._donor_key(atoms, 1, 0) == "C"


def test_other_carbon_donors_keep_the_element_key():
    # acyl: C=O but a second (carbon) neighbour; aryl/alkyl: no N/O partner; carbene: two N
    acyl = [FE, ("C", (1.95, 0.0, 0.0)), ("O", (2.60, 1.03, 0.0)), ("C", (2.70, -1.30, 0.0))]
    alkyl = [FE, ("C", (2.05, 0.0, 0.0)), ("C", (2.60, 1.42, 0.0))]
    nhc = [FE, ("C", (1.95, 0.0, 0.0)), ("N", (2.70, 1.10, 0.0)), ("N", (2.70, -1.10, 0.0))]
    for atoms in (acyl, alkyl, nhc):
        assert optimize._donor_key(atoms, 1, 0) == "C"
    assert optimize._donor_key([FE, ("N", (2.0, 0.0, 0.0)), ("C", (3.15, 0.0, 0.0))], 1, 0) == "N"


def test_sp_carbon_reference_is_shorter_than_the_mixed_carbon_bin():
    sp = optimize._restraint_reference(1.80, "Fe", optimize.SP_CARBON, ox=0, cn=5)
    mixed = optimize._restraint_reference(2.00, "Fe", "C", ox=0, cn=5)
    assert 1.70 < sp < 1.85                      # Fe(0)-CO in the CSD
    assert mixed - sp > 0.15


def test_sp_carbon_falls_back_to_the_carbon_bin_without_data(monkeypatch):
    table = {"metal_os_donor_cn": {}, "metal_os_donor": {},
             "metal_donor": {"Xx|C": {"mean": 2.10, "n": 50}}}
    monkeypatch.setattr(optimize, "_ML_TABLE", table)
    monkeypatch.setattr(optimize, "_ML_LOADED", True)
    assert optimize._ml_target("Xx", 2, optimize.SP_CARBON, 6) == 2.10
    table["metal_donor"]["Xx|C_sp"] = {"mean": 1.90, "n": 50}
    assert optimize._ml_target("Xx", 2, optimize.SP_CARBON, 6) == 1.90
    table["metal_donor"]["Xx|C_sp"] = {"mean": 1.90, "n": 3}        # too few samples -> C bin
    assert optimize._ml_target("Xx", 2, optimize.SP_CARBON, 6) == 2.10
