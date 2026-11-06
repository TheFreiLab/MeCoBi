"""Output-filename safety: sanitization, path containment, collision suffixes."""

import pytest

from mecobi import naming
from mecobi.model import Complex, Geometry, Ligand, Metal


# --------------------------------------------------------------------------- #
# sanitize_component
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw, expected", [
    ("Cisplatin", "Cisplatin"),
    ("BOLD-100", "BOLD-100"),
    ("trans_AC", "trans_AC"),
    ("../../etc/passwd", "passwd"),
    (r"..\..\windows\system32", "system32"),
    (r"C:\Windows\System32\evil", "evil"),
    (r"\\server\share\x", "x"),
    ("a/b/c", "c"),
])
def test_sanitize_strips_path_parts(raw, expected):
    assert naming.sanitize_component(raw) == expected


@pytest.mark.parametrize("raw", ["CON", "con", "NUL", "com1", "LPT1", "nul.xyz"])
def test_sanitize_guards_windows_reserved(raw):
    out = naming.sanitize_component(raw)
    assert out.upper().split(".", 1)[0] not in naming._WINDOWS_RESERVED


@pytest.mark.parametrize("raw", ["", "   ", "..", " . ", "///"])
def test_sanitize_empty_or_dangerous_falls_back(raw):
    assert naming.sanitize_component(raw) == "complex"


def test_sanitize_control_only_is_safe_nonempty():
    out = naming.sanitize_component("\x00\x01")
    assert out and not any(ord(c) < 32 or c in '<>:"/\\|?*' for c in out)


def test_sanitize_replaces_illegal_chars_but_keeps_brackets():
    assert naming.sanitize_component('a<>:"|?*b') == "a_______b"
    assert naming.sanitize_component("[Cp]Ir") == "[Cp]Ir"  # brackets legal on Windows


# --------------------------------------------------------------------------- #
# unique_output_path: containment + collisions
# --------------------------------------------------------------------------- #

def test_unique_output_path_contained_and_deduped(tmp_path):
    p1 = naming.unique_output_path(tmp_path, "X")
    p1.write_text("1")
    p2 = naming.unique_output_path(tmp_path, "X")
    p2.write_text("2")
    p3 = naming.unique_output_path(tmp_path, "X")
    assert [p.name for p in (p1, p2, p3)] == ["X.xyz", "X_2.xyz", "X_3.xyz"]
    assert all(p.resolve().parent == tmp_path.resolve() for p in (p1, p2, p3))


def test_unique_output_path_rejects_escaping_stem(tmp_path):
    # Defence in depth: even if a separator slipped past sanitization, the
    # containment check must refuse it rather than write outside output_dir.
    with pytest.raises(ValueError):
        naming.unique_output_path(tmp_path, "../evil")


def test_make_stem_sanitizes_base():
    stem = naming.make_stem("../../evil", 2)
    assert "/" not in stem and ".." not in stem
    assert stem == "evil_c2"


# --------------------------------------------------------------------------- #
# End-to-end: a malicious complex name cannot escape or overwrite (no xtb).
# --------------------------------------------------------------------------- #

def test_build_with_traversal_name_stays_contained(tmp_path):
    from mecobi import pipeline

    def build(name):
        cx = Complex(metal=Metal("Pt", 2), geometry=Geometry.SQUARE_PLANAR, name=name,
                     ligands=[Ligand("N"), Ligand("N"), Ligand("[Cl-]"), Ligand("[Cl-]")])
        return pipeline.build_complex(cx, tmp_path, relax=False)[0]

    r1 = build("../../pwned")
    r2 = build("../../pwned")  # identical name again -> must not overwrite
    from pathlib import Path
    p1, p2 = Path(r1.xyz_path), Path(r2.xyz_path)
    assert p1.resolve().parent == tmp_path.resolve()
    assert p2.resolve().parent == tmp_path.resolve()
    assert p1.name != p2.name and p1.exists() and p2.exists()
    assert ".." not in p1.name and "/" not in p1.name
