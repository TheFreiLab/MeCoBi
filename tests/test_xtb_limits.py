"""Per-process resource caps on the xtb child.

The unit tests pin the wrapper command; the POSIX tests run a stand-in child through the
real wrapper and check each cap actually fires (these only run on Linux CI, the dev box is
Windows)."""
import os
import subprocess
import sys

import pytest

from mecobi import optimize
from mecobi.optimize import _limited_command

posix_only = pytest.mark.skipif(os.name != "posix", reason="rlimits are POSIX only")


@pytest.fixture
def posix(monkeypatch):
    monkeypatch.setattr(optimize.os, "name", "posix")
    for k in ("MECOBI_XTB_LIMITS", "MECOBI_XTB_MAX_FILE_MB", "MECOBI_XTB_OOM_SCORE_ADJ"):
        monkeypatch.delenv(k, raising=False)


def test_wrapper_applies_every_cap_then_execs_xtb(posix):
    cmd = ["xtb", "in.xyz", "--opt"]
    out = _limited_command(cmd, timeout_s=300, threads=4)
    assert out[:2] == ["/bin/sh", "-c"] and out[3:] == ["xtb", *cmd]
    script = out[2]
    assert "ulimit -c 0" in script
    assert f"ulimit -f {1024 * 2048}" in script          # 1 GB in 512-byte blocks
    assert f"ulimit -t {300 * 4 + 60}" in script         # CPU s across all threads
    assert "echo 1000 > /proc/self/oom_score_adj" in script
    assert script.endswith('exec "$@"')


def test_no_cpu_cap_without_a_timeout(posix):
    assert "ulimit -t" not in _limited_command(["xtb"], timeout_s=None, threads=1)[2]


def test_env_overrides_and_kill_switch(posix, monkeypatch):
    monkeypatch.setenv("MECOBI_XTB_MAX_FILE_MB", "0")
    monkeypatch.setenv("MECOBI_XTB_OOM_SCORE_ADJ", "0")
    script = _limited_command(["xtb"], timeout_s=10, threads=1)[2]
    assert "ulimit -f" not in script and "oom_score_adj" not in script
    monkeypatch.setenv("MECOBI_XTB_LIMITS", "0")
    assert _limited_command(["xtb", "a"], timeout_s=10, threads=1) == ["xtb", "a"]


def test_missing_binary_still_raises_xtb_not_found(tmp_path, monkeypatch):
    """Behind sh a missing xtb is exit 127, not FileNotFoundError; it must stay XtbNotFound
    (on Windows, unwrapped, it is the FileNotFoundError path)."""
    monkeypatch.delenv("MECOBI_XTB_LIMITS", raising=False)
    xyz = tmp_path / "h2.xyz"
    xyz.write_text("2\n\nH 0 0 0\nH 0 0 0.74\n")
    with pytest.raises(optimize.XtbNotFound):
        optimize.relax_with_xtb(xyz, charge=0, uhf=0, xtb_bin="no-such-xtb-binary", timeout_s=30)


def test_windows_is_untouched(monkeypatch):
    monkeypatch.setattr(optimize.os, "name", "nt")
    assert _limited_command(["xtb", "a"], timeout_s=10, threads=1) == ["xtb", "a"]


# --- real caps, via the real wrapper, on a python stand-in for xtb -------------------------

def _run(code, monkeypatch, **env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    cmd = _limited_command([sys.executable, "-c", code], timeout_s=1, threads=1)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


@posix_only
def test_file_size_cap_kills_a_runaway_writer(tmp_path, monkeypatch):
    code = (f"f = open({str(tmp_path / 'big')!r}, 'wb')\n"
            "while True: f.write(b'x' * (1 << 20)); f.flush()")
    proc = _run(code, monkeypatch, MECOBI_XTB_MAX_FILE_MB="2")
    # xtb (Fortran, default signal handling) is killed by SIGXFSZ; this python stand-in
    # ignores SIGXFSZ (CPython does at startup) and gets EFBIG instead. Either way it stops.
    assert proc.returncode == -25 or "File too large" in proc.stderr, proc
    assert (tmp_path / "big").stat().st_size <= 2 * 1024 * 1024


@posix_only
def test_cpu_cap_kills_a_spinning_child(monkeypatch):
    monkeypatch.setattr(optimize, "XTB_CPU_MARGIN_S", 0)
    proc = _run("while True: pass", monkeypatch)   # cap = 1 s x 1 thread
    assert proc.returncode in (-24, -9), proc      # SIGXCPU (SIGKILL at the hard limit)


@posix_only
def test_child_sees_core_off_and_oom_preference(monkeypatch):
    code = ("import resource; print(resource.getrlimit(resource.RLIMIT_CORE)[0]);"
            "print(open('/proc/self/oom_score_adj').read().strip())")
    proc = _run(code, monkeypatch)
    assert proc.returncode == 0, proc
    core, oom = proc.stdout.split()
    assert core == "0" and oom == "1000"


@posix_only
def test_caps_never_leak_into_the_parent():
    import resource
    before = resource.getrlimit(resource.RLIMIT_FSIZE)
    cmd = _limited_command([sys.executable, "-c", "pass"], timeout_s=1, threads=1)
    subprocess.run(cmd, check=True, timeout=60)
    assert resource.getrlimit(resource.RLIMIT_FSIZE) == before


def test_limit_signals_read_as_plain_english():
    assert "out-of-memory" in optimize._LIMIT_SIGNALS[-9]
    assert "SIGXFSZ" in optimize._LIMIT_SIGNALS[-25]
