"""OpenBLAS kernel choice for xtb: SandyBridge on AMD Zen4/Zen5 (AVX-512), else Haswell.

The Haswell kernel of conda-forge OpenBLAS 0.3.34 makes xtb GFN2 segfault on AMD EPYC 9V74 /
9V45 (the intermittent CI failure of the Re dioxo bis-PNP regression: GitHub's runner pool
mixes CPUs). Intel with AVX-512 and Zen3 are fine on Haswell and must keep it.
"""

import pytest

from mecobi import optimize


def _cpuinfo(tmp_path, vendor, flags):
    p = tmp_path / "cpuinfo"
    p.write_text(f"processor\t: 0\nvendor_id\t: {vendor}\nmodel name\t: x\nflags\t\t: {flags}\n")
    return str(p)


@pytest.mark.parametrize("vendor,flags,core", [
    ("AuthenticAMD", "fpu sse2 avx avx2 avx512f avx512bw", "SandyBridge"),  # Zen4/Zen5
    ("AuthenticAMD", "fpu sse2 avx avx2", "Haswell"),                        # Zen3 (EPYC 7763)
    ("GenuineIntel", "fpu sse2 avx avx2 avx512f", "Haswell"),                # Xeon, York VM
    ("GenuineIntel", "fpu sse2 avx avx2", "Haswell"),
])
def test_coretype_by_cpu(tmp_path, vendor, flags, core):
    assert optimize._openblas_coretype(_cpuinfo(tmp_path, vendor, flags)) == core


def test_unreadable_cpuinfo_defaults_to_haswell(tmp_path):
    assert optimize._openblas_coretype(str(tmp_path / "missing")) == "Haswell"
