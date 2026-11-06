"""Per-refcode input corrections for the benchmark -- confirmed oxidation-state / charge /
donor-atom errors in the FROZEN bundle, applied by enrich_bundle_geometry.py and run.py so the
bundle itself stays immutable. Only spot-fix errors verified in review (the pilot found HIFZEF
+ ECORUM); never mass-edit. Fields in benchmark_overrides.json mirror the bundle record
(``ox``, ``cn``, ``ligands``, ``charges``, ``donor_elements``) plus ``donors`` (a donor-index
override, same shape as benchmark_donors[refcode]); any ``note`` is ignored.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
_FIELDS = ("ox", "cn", "ligands", "charges", "donor_elements")


def load(path: str = "benchmark_overrides.json") -> dict:
    p = Path(path) if Path(path).is_absolute() else HERE / path
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def record(r: dict, overrides: dict) -> dict:
    """Bundle record with any override applied (copy; original untouched)."""
    ov = overrides.get(r["refcode"])
    if not ov:
        return r
    out = dict(r)
    for k in _FIELDS:
        if k in ov:
            out[k] = ov[k]
    return out


def donors(rc: str, donors_row, overrides: dict):
    """Donor-index list for ``rc``, replaced by the override's ``donors`` when present."""
    ov = overrides.get(rc)
    return ov["donors"] if (ov and "donors" in ov) else donors_row
