"""The all-isomers cap bounds ASSEMBLY, not just the relax loop.

Regression: build_complex enumerated (up to 64) isomers, assembled every one (two stk/MCHammer
builds each) and only then trimmed to ``max_isomers``. One "all isomers" click on a CN8 complex
with eight mixed monodentates spent 20+ minutes assembling isomers it then threw away.
"""

from mecobi import pipeline
from mecobi.model import Complex, Ligand, Metal

# cis/trans-rich MA2B2C2 octahedron: well over two stereoisomers
MA2B2C2 = ["[Cl-]", "[Cl-]", "[Br-]", "[Br-]", "N", "N"]


def _count_assemblies(monkeypatch):
    calls = []
    real = pipeline._build_with_fallback

    def counting(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(pipeline, "_build_with_fallback", counting)
    return calls


def test_isomer_cap_applies_before_assembly(tmp_path, monkeypatch):
    calls = _count_assemblies(monkeypatch)
    cx = Complex(metal=Metal("Ru", 2), ligands=[Ligand(s) for s in MA2B2C2])
    res = pipeline.build_complex(cx, tmp_path, all_isomers=True, max_isomers=2)
    assert len(res) == 2
    assert len(calls) == 2
    assert any("built the first 2 (limit)" in w for w in res[0].warnings)


def test_no_cap_note_when_under_the_limit(tmp_path, monkeypatch):
    calls = _count_assemblies(monkeypatch)
    cx = Complex(metal=Metal("Ru", 2), ligands=[Ligand(s) for s in MA2B2C2])
    res = pipeline.build_complex(cx, tmp_path, all_isomers=True, max_isomers=64)
    assert len(res) == len(calls) > 2
    assert not any("(limit)" in w for w in res[0].warnings)


def test_high_cn_cap_only_applies_above_cn6(tmp_path, monkeypatch):
    from mecobi.model import Geometry

    calls = _count_assemblies(monkeypatch)
    cn8 = Complex(metal=Metal("Zr", 4), geometry=Geometry.SQUARE_ANTIPRISM,
                  ligands=[Ligand(s) for s in ["[Cl-]"] * 4 + ["[Br-]"] * 4])
    res = pipeline.build_complex(tmp_path / "cn8", cn8, all_isomers=True,
                                 max_isomers=64, max_isomers_high_cn=2) \
        if False else pipeline.build_complex(cn8, tmp_path / "cn8", all_isomers=True,
                                             max_isomers=64, max_isomers_high_cn=2)
    assert len(res) == len(calls) == 2

    calls.clear()
    cn6 = Complex(metal=Metal("Ru", 2), ligands=[Ligand(s) for s in MA2B2C2])
    res = pipeline.build_complex(cn6, tmp_path / "cn6", all_isomers=True,
                                 max_isomers=64, max_isomers_high_cn=2)
    assert len(res) == len(calls) > 2
