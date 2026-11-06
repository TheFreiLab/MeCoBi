"""Anti-fusion detect-then-fix (pipeline._interligand_donor_fusions + _fusion_floors).

If xtb forges a NEW bond between two DONORS of DIFFERENT ligands (cis carbonyls -> C-C,
an oxo onto a thiolate, an iodide onto an amide), that fusion is re-relaxed with a distance
floor on exactly those pairs. These two helpers pick the fusion pairs out of the connectivity
guard's new-bond list and build the floors. Pure geometry, no xtb.
"""


from mecobi import pipeline


def test_interligand_donor_fusions_picks_donor_pairs_across_ligands():
    # comp: ligand membership per atom (metal excluded -> -1). donors {1,2,3}.
    #   1 & 2 on DIFFERENT ligands (0 vs 1) -> a fusion; 3 & 4 -> 4 is not a donor; 1 & 5 -> same ligand.
    comp = {1: 0, 2: 1, 3: 1, 4: 1, 5: 0}
    donor_set = {1, 2, 3, 5}
    new_bonds = [(1, 2, "C-C"),   # inter-ligand donor pair -> KEEP
                 (3, 4, "O-C"),   # 4 not a donor -> drop
                 (1, 5, "C-C")]   # same ligand (0) -> drop
    assert pipeline._interligand_donor_fusions(new_bonds, comp, donor_set) == [(1, 2)]


def test_interligand_donor_fusions_ignores_backbone_fusion():
    # BATKOX-style: a new bond between two NON-donor backbone carbons is not an anti-fusion target.
    comp = {1: 0, 2: 1}
    assert pipeline._interligand_donor_fusions([(1, 2, "C-C")], comp, donor_set=set()) == []


def test_intraligand_diyl_fusion_fires_on_collapsed_bite():
    # CPFPRH: a chelating 1,4-bis-carbanion (metallacyclopentadiene). Donors 1 & 4 sit on one ligand,
    # 3 bonds apart (1-2-3-4); xtb folds them into a direct bond. Same ligand so the inter-ligand
    # detector misses it -- the diyl detector catches it (>= 3 bonds apart in the assembled graph).
    intended = [(0, 1), (0, 4), (1, 2), (2, 3), (3, 4)]   # metal=0; backbone 1-2-3-4
    comp = {1: 0, 2: 0, 3: 0, 4: 0}
    got = pipeline._intraligand_diyl_fusions(
        [(1, 4, "C-C")], comp, intended, donor_set={1, 4}, metal_index=0)
    assert got == [(1, 4)]
    # and the inter-ligand detector does NOT (same component)
    assert pipeline._interligand_donor_fusions([(1, 4, "C-C")], comp, {1, 4}) == []


def test_intraligand_diyl_fusion_ignores_geminal_and_nondonor():
    intended = [(0, 1), (0, 3), (1, 2), (2, 3)]           # donors 1 & 3, only 2 bonds apart (geminal)
    comp = {1: 0, 2: 0, 3: 0}
    # geminal (2 bonds) -> not a diyl collapse, left to the plain connectivity flag
    assert pipeline._intraligand_diyl_fusions(
        [(1, 3, "C-C")], comp, intended, donor_set={1, 3}, metal_index=0) == []
    # a new bond touching a non-donor backbone atom -> never a target
    assert pipeline._intraligand_diyl_fusions(
        [(2, 3, "C-C")], comp, intended, donor_set={1, 3}, metal_index=0) == []


def test_fusion_floors_target_is_the_assembled_separation():
    # two carbonyl carbons 2.8 A apart in the assembly -> floor holds them at 2.8 (their separation)
    pre_atoms = [("Fe", (0.0, 0.0, 0.0)),
                 ("C", (1.9, 0.0, 0.0)),
                 ("C", (1.9, 2.8, 0.0))]
    floors = pipeline._fusion_floors(pre_atoms, [(1, 2)])
    assert len(floors) == 1
    i, j, target = floors[0]
    assert (i, j) == (1, 2)
    assert abs(target - 2.8) < 1e-6            # the assembled C-C separation


def test_fusion_floors_never_below_a_non_bonded_distance():
    # if the assembled pair is somehow close, the floor is at least ~1.5x the covalent-radii sum
    pre_atoms = [("Fe", (0.0, 0.0, 0.0)), ("C", (1.9, 0.0, 0.0)), ("C", (1.9, 0.5, 0.0))]
    _, _, target = pipeline._fusion_floors(pre_atoms, [(1, 2)])[0]
    assert target > 2.0                        # 1.5 * (0.76 + 0.76) = 2.28, not the 0.5 A gap
