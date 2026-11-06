"""User-facing count wording: "1 donor" / "2 donors", never "donor(s)" (UI audit W13)."""

from mecobi._text import noun, plural


def test_plural_and_noun():
    assert plural(1, "donor") == "1 donor"
    assert plural(0, "donor") == "0 donors"
    assert plural(3, "new bond") == "3 new bonds"
    assert plural(2, "torsion", "torsions") == "2 torsions"
    assert noun(1, "format") == "format" and noun(2, "format") == "formats"
