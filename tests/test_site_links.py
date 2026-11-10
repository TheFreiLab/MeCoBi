"""The web GUI links to the preprint and the source code, and those links match CITATION.cff.

The links live in the React source and in the committed production bundle FastAPI serves, so
the test reads the bundle: a rebuild that drops them, or a citation change that the site misses,
fails here.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src" / "mecobi" / "web" / "static"


def _cff(pattern):
    # CITATION.cff is YAML; a regex keeps the test free of a PyYAML dependency.
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    assert m, f"CITATION.cff: no match for {pattern!r}"
    return m.group(1)


def _bundle_js():
    files = sorted((STATIC / "assets").glob("index-*.js"))
    assert files, "no committed frontend bundle under src/mecobi/web/static/assets"
    return "\n".join(f.read_text(encoding="utf-8") for f in files)


def test_gui_links_to_preprint_from_citation():
    preprint = _cff(r'^preferred-citation:.*?^  url: "([^"]+)"')
    assert preprint.startswith("https://doi.org/10.26434/chemrxiv.")
    assert preprint in _bundle_js()


def test_gui_links_to_public_repository_from_citation():
    repo = _cff(r'^repository-code: "([^"]+)"')
    assert repo == "https://github.com/TheFreiLab/MeCoBi"
    assert repo in _bundle_js()


def test_bundle_has_no_private_repository_link():
    # The site must point at the public copy, never the private development repository.
    assert "MeCoBi-dev" not in _bundle_js()
