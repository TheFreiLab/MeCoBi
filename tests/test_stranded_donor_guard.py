"""The donor-dissociation guard must not discard an INCOMPLETE inward pull.

The guard reverts to the assembled geometry when a restrained donor ends beyond the
dissociation threshold. That is right when xtb pushed the donor OFF a bonded start, but
wrong when the ASSEMBLY had already stranded it: a bulky pincer seated well beyond the
M-P reference is over the threshold before xtb runs, so a relax that drags it inward --
a real improvement -- was being thrown away and the worse assembled geometry returned
with no energy.

Thresholds are DERIVED from the same helpers the guard uses (Re-P lands on the
reference-scaled 1.4x threshold, Re-O on the fixed 3.1 A floor), so these tests do not
silently change meaning if the mined M-L table is updated.

xtb is faked at the subprocess boundary (not by replacing relax_with_xtb) so the real
guard code runs against a controlled relaxed geometry.
"""

import subprocess
from pathlib import Path

import pytest

from mecobi import optimize


def _threshold(donor: str) -> float:
    ref = optimize._restraint_reference(2.5, "Re", donor, ox=5, cn=6)
    return max(optimize.DISSOCIATION_THRESHOLD_A,
               ref * optimize.DISSOCIATION_REFERENCE_FACTOR)


def _write_xyz(path: Path, donor: str, distance: float) -> None:
    """Re at the origin with one donor on +x at the requested distance."""
    path.write_text(
        f"2\n\nRe 0.000000 0.000000 0.000000\n{donor} {distance:.6f} 0.000000 0.000000\n",
        encoding="utf-8",
    )


@pytest.fixture
def relax(tmp_path, monkeypatch):
    """Run the real guard against a chosen (assembled -> relaxed) donor distance pair."""
    def _run(donor: str, assembled: float, relaxed: float):
        def fake_run(cmd, cwd=None, **kwargs):
            _write_xyz(Path(cwd) / "xtbopt.xyz", donor, relaxed)
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        monkeypatch.setattr(optimize.subprocess, "run", fake_run)

        xyz = tmp_path / "c.xyz"
        _write_xyz(xyz, donor, assembled)
        warnings: list[str] = []
        energy_out: dict = {}
        optimize.relax_with_xtb(
            xyz, charge=0, uhf=0, restrain_donors=True,
            metal_index=0, donor_indices=[1], metal_symbol="Re",
            coordination_number=6, oxidation_state=5,
            warnings=warnings, energy_out=energy_out,
        )
        kept = float(xyz.read_text(encoding="utf-8").splitlines()[3].split()[1])
        return kept, warnings, energy_out
    return _run


def test_stranded_donor_pulled_inward_keeps_the_relaxed_geometry(relax):
    # Stranded by the ASSEMBLY, pulled inward but not all the way to a bond: still over
    # the threshold, yet strictly better than the assembly -- keep it, don't revert.
    thr = _threshold("P")
    kept, warnings, energy_out = relax("P", thr + 0.5, thr + 0.2)
    assert kept == pytest.approx(thr + 0.2), "the improved relaxed geometry must be kept"
    assert not any("dissociated a donor" in w for w in warnings)
    assert any("still long after relaxation" in w for w in warnings)
    # Not a bonded distance, so its energy must stay out of isomer ranking.
    assert energy_out.get("dissociated") is True


def test_donor_pushed_off_a_bonded_start_still_reverts(relax):
    # Bonded in the assembly and ejected by xtb: a genuine dissociation. This is the
    # Re(V) dioxo bis-PNP oxo case (O bonded at ~1.9 A, ejected past the 3.1 A floor);
    # it must keep reverting -- the relaxed geometry really is the worse one.
    thr = _threshold("O")
    kept, warnings, energy_out = relax("O", 1.9, thr + 1.5)
    assert kept == pytest.approx(1.9), "the assembled geometry must be restored"
    assert any("dissociated a donor" in w for w in warnings)
    assert energy_out.get("dissociated") is True


def test_stranded_donor_pushed_further_out_reverts(relax):
    # Stranded by the assembly AND made worse by xtb: reverting is still right.
    thr = _threshold("P")
    kept, warnings, energy_out = relax("P", thr + 0.5, thr + 1.0)
    assert kept == pytest.approx(thr + 0.5), "the assembled geometry must be restored"
    assert any("dissociated a donor" in w for w in warnings)
    assert energy_out.get("dissociated") is True


def test_intact_donor_is_untouched(relax):
    # An ordinary relax that keeps the donor bonded: no warning, geometry kept, energy usable.
    kept, warnings, energy_out = relax("P", 2.6, 2.44)
    assert kept == pytest.approx(2.44)
    assert warnings == []
    assert "dissociated" not in energy_out


def test_drift_just_past_the_assembled_distance_is_not_an_improvement(relax):
    # A donor that ends marginally FURTHER out than the assembly left it is not an
    # "incomplete pull" -- beyond the small numerical tolerance it reverts.
    thr = _threshold("P")
    was = thr + 0.5
    kept, warnings, _ = relax("P", was, was + optimize.DISSOCIATION_WORSENED_A + 0.05)
    assert kept == pytest.approx(was), "the assembled geometry must be restored"
    assert any("dissociated a donor" in w for w in warnings)
