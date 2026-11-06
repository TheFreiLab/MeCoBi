"""`mecobi build` batch reporting: paths on stdout, failures on stderr, exit status.

The build itself is mocked (no xtb, no RDKit assembly); these tests pin the
CLI contract, documented in :mod:`mecobi.cli`.
"""

from pathlib import Path

import pytest

from mecobi import cli, inputs, pipeline
from mecobi.model import BuildResult, Complex, Metal


def _complexes(*names):
    return [Complex(metal=Metal("Pt", 2), ligands=[], name=n) for n in names]


def _run(monkeypatch, capsys, tmp_path, names, failing=()):
    """Run `mecobi build` over complexes `names`; those in `failing` raise in the build."""
    monkeypatch.setattr(inputs, "parse_csv", lambda path: _complexes(*names))

    def fake_build(cx, output_dir, **kwargs):
        if cx.name in failing:
            raise RuntimeError(f"cannot build {cx.name}")
        xyz = Path(output_dir) / f"{cx.name}.xyz"
        return [BuildResult(cx, "x", str(xyz), warnings=[f"note on {cx.name}"])]

    monkeypatch.setattr(pipeline, "build_complex", fake_build)
    code = cli.main(["build", "in.csv", "--output-dir", str(tmp_path), "--no-relax"])
    out, err = capsys.readouterr()
    return code, out.splitlines(), err


def test_all_success_exits_zero_with_only_paths_on_stdout(monkeypatch, capsys, tmp_path):
    code, out, err = _run(monkeypatch, capsys, tmp_path, ["a", "b"])
    assert code == cli.EXIT_OK == 0
    assert out == [str(tmp_path / "a.xyz"), str(tmp_path / "b.xyz")]
    assert "FAILED" not in err and "note on a" in err  # warnings stay on stderr


def test_partial_failure_keeps_going_and_exits_one(monkeypatch, capsys, tmp_path):
    code, out, err = _run(monkeypatch, capsys, tmp_path, ["a", "bad", "c"], failing={"bad"})
    assert code == cli.EXIT_BUILD_FAILED == 1
    assert out == [str(tmp_path / "a.xyz"), str(tmp_path / "c.xyz")]  # survivors still built
    assert "# FAILED bad: cannot build bad" in err
    assert "1 of 3 complexes failed: bad" in err


def test_all_failure_exits_one_with_empty_stdout(monkeypatch, capsys, tmp_path):
    code, out, err = _run(monkeypatch, capsys, tmp_path, ["x", "y"], failing={"x", "y"})
    assert code == cli.EXIT_BUILD_FAILED
    assert out == []
    assert err.count("# FAILED") == 2 and "2 of 2 complexes failed: x, y" in err


def test_unreadable_input_is_a_usage_error(capsys, tmp_path):
    code = cli.main(["build", str(tmp_path / "missing.csv"), "--output-dir", str(tmp_path)])
    out, err = capsys.readouterr()
    assert code == cli.EXIT_USAGE == 2
    assert out == "" and "could not read" in err


def test_bad_format_is_a_usage_error(capsys, tmp_path):
    code = cli.main(["build", "in.csv", "--format", "xyz,docx", "--output-dir", str(tmp_path)])
    out, err = capsys.readouterr()
    assert code == cli.EXIT_USAGE and out == "" and err


def test_help_documents_the_exit_status(capsys):
    with pytest.raises(SystemExit):
        cli.main(["build", "--help"])
    help_text = " ".join(capsys.readouterr().out.split())  # argparse re-wraps the epilog
    assert "Exit status: 0 all complexes built, 1 one or more failed" in help_text
