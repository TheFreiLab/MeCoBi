"""GFN2 isomer energy ranking.

Fast unit tests for the energy parsing and the ranking helper (no xtb needed);
the end-to-end xtb ranking is exercised by the slow build tests.
"""

from mecobi import optimize, pipeline
from mecobi.model import BuildResult, Complex, Metal


def _result(energy, connectivity_ok=True, label="x"):
    return BuildResult(
        complex=Complex(metal=Metal("Ir", 3), ligands=[]),
        isomer_label=label, xyz_path="x.xyz", total_energy=energy,
        connectivity_ok=connectivity_ok,
    )


def test_parse_energy_from_comment_line():
    comment = " energy: -28.1234567 gnorm: 0.0009 xtb: 6.6.1"
    assert optimize._parse_energy(comment, "") == -28.1234567


def test_parse_energy_falls_back_to_stdout():
    stdout = "          | TOTAL ENERGY              -42.5000000 Eh   |"
    assert optimize._parse_energy("no energy here", stdout) == -42.5


def test_parse_energy_none_when_absent():
    assert optimize._parse_energy("", "") is None


def test_rank_orders_and_fills_relative_energies():
    # -1.0 Eh is lowest; +0.5 Eh above is 1.0*627.509/2 ... just check magnitude.
    results = [_result(-1.00), _result(-1.02), _result(-1.01)]
    pipeline._rank_by_energy(results)
    assert [r.total_energy for r in results] == [-1.02, -1.01, -1.00]  # sorted asc
    assert results[0].is_lowest_energy
    assert results[0].relative_energy_kcal == 0.0
    # 0.01 Eh above the minimum -> ~6.275 kcal/mol.
    assert abs(results[1].relative_energy_kcal - 0.01 * optimize.HARTREE_TO_KCAL) < 1e-6
    assert not results[1].is_lowest_energy


def test_rank_noop_for_single_or_missing_energy():
    one = [_result(-1.0)]
    pipeline._rank_by_energy(one)
    assert one[0].relative_energy_kcal is None and not one[0].is_lowest_energy

    mixed = [_result(-1.0), _result(None)]
    pipeline._rank_by_energy(mixed)  # only one comparable energy -> no ranking
    assert all(r.relative_energy_kcal is None for r in mixed)


def test_rank_pushes_unscored_results_last():
    results = [_result(None), _result(-2.0), _result(-1.0)]
    pipeline._rank_by_energy(results)
    assert results[-1].total_energy is None
    assert results[0].total_energy == -2.0


def test_broken_connectivity_never_wins_even_when_numerically_lowest():
    # The fused isomer has the lowest number but is a different molecule.
    results = [_result(-1.00, label="a"), _result(-1.50, connectivity_ok=False, label="fused"),
               _result(-1.02, label="b")]
    pipeline._rank_by_energy(results)
    assert [r.isomer_label for r in results] == ["b", "a", "fused"]
    assert results[0].is_lowest_energy and results[0].relative_energy_kcal == 0.0
    assert abs(results[1].relative_energy_kcal - 0.02 * optimize.HARTREE_TO_KCAL) < 1e-6
    fused = results[2]
    assert not fused.is_lowest_energy
    assert fused.relative_energy_kcal is None
    assert fused.total_energy == -1.50  # kept for diagnosis


def test_broken_results_go_after_valid_unscored_ones_in_build_order():
    results = [_result(-3.0, connectivity_ok=False, label="bad1"), _result(None, label="noE"),
               _result(-1.0, label="a"), _result(None, connectivity_ok=False, label="bad2"),
               _result(-2.0, label="b")]
    pipeline._rank_by_energy(results)
    assert [r.isomer_label for r in results] == ["b", "a", "noE", "bad1", "bad2"]
    assert [r.is_lowest_energy for r in results] == [True, False, False, False, False]


def test_one_valid_energy_plus_broken_ones_is_not_ranked_but_valid_comes_first():
    results = [_result(-5.0, connectivity_ok=False, label="bad"), _result(-1.0, label="ok")]
    pipeline._rank_by_energy(results)
    assert [r.isomer_label for r in results] == ["ok", "bad"]
    assert all(r.relative_energy_kcal is None and not r.is_lowest_energy for r in results)


def test_only_broken_results_have_no_lowest():
    results = [_result(-1.0, connectivity_ok=False), _result(-2.0, connectivity_ok=False)]
    pipeline._rank_by_energy(results)
    assert not any(r.is_lowest_energy for r in results)
    assert all(r.relative_energy_kcal is None for r in results)
