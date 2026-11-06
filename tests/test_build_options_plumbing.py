"""Advanced build options must actually REACH build_complex on both routes.

`reposition_polydentates` and `oxo_antifusion_floors` are opt-in escalations for a hard,
crowded sphere. They were defined only as
build_complex kwargs and were never referenced by the web layer, so no GUI or API caller
could reach them. These tests pin the wiring, and the job-level vs per-complex precedence.
(The Re(V) dioxo bis-PNP case that motivated them turned out to be a spin-state error and
now builds cleanly with default options.)
"""

import json

from fastapi.testclient import TestClient

from mecobi import pipeline
# `mecobi.web.app` is rebound to the FastAPI instance by the package __init__, so the
# app object and the module's names are imported separately (see tests/test_web.py).
from mecobi.web import app as fastapi_app
from mecobi.web import jobs
from mecobi.web.app import BuildOptions

OPT_IN_KEYS = ("reposition_polydentates", "oxo_antifusion_floors")


def test_opt_in_flags_are_exposed_and_default_off():
    opts = BuildOptions()
    for k in OPT_IN_KEYS:
        assert hasattr(opts, k), f"{k} is not exposed on BuildOptions"
        assert getattr(opts, k) is False, f"{k} must default OFF (it costs accuracy elsewhere)"


def test_opt_in_flags_are_in_the_queue_allowlist():
    for k in OPT_IN_KEYS:
        assert k in jobs.BUILD_OPTION_KEYS


def test_build_options_defaults_match_build_complex_defaults():
    """A default BuildOptions must reproduce the standard build exactly -- otherwise the
    GUI silently changes chemistry for every user who never opens Advanced options."""
    import inspect

    sig = inspect.signature(pipeline.build_complex).parameters
    for k, v in BuildOptions().model_dump().items():
        assert k in sig, f"BuildOptions.{k} has no build_complex parameter"
        assert sig[k].default == v, (
            f"BuildOptions.{k} defaults to {v} but build_complex defaults to {sig[k].default}")


def test_queue_route_forwards_the_opt_in_flags(monkeypatch):
    """_build_options is what the queue worker hands to build_complex."""
    spec = {"options": {k: True for k in OPT_IN_KEYS}}
    forwarded = jobs._build_options(spec)
    for k in OPT_IN_KEYS:
        assert forwarded[k] is True


def test_sync_route_forwards_the_opt_in_flags(monkeypatch):
    """/api/build is assembly-only in the GUI, but the pre-xtb placement guards still
    change the ASSEMBLED geometry, so they must be honoured there too."""
    seen = {}

    def fake_build_complex(cx, out_dir, **kwargs):
        seen.update(kwargs)
        return []

    monkeypatch.setattr(pipeline, "build_complex", fake_build_complex)
    with TestClient(fastapi_app) as c:
        r = c.post("/api/build", json={
            "metal": "Pt", "oxidation_state": 2,
            "ligands": [{"smiles": "[Cl-]"} for _ in range(4)],
            "geometry": "square_planar", "relax": False,
            "options": {k: True for k in OPT_IN_KEYS},
        })
    assert r.status_code == 200, r.text
    for k in OPT_IN_KEYS:
        assert seen.get(k) is True, f"{k} never reached build_complex on the sync route"


def test_sync_route_without_options_is_the_standard_build(monkeypatch):
    seen = {}

    def fake_build_complex(cx, out_dir, **kwargs):
        seen.update(kwargs)
        return []

    monkeypatch.setattr(pipeline, "build_complex", fake_build_complex)
    with TestClient(fastapi_app) as c:
        r = c.post("/api/build", json={
            "metal": "Pt", "oxidation_state": 2,
            "ligands": [{"smiles": "[Cl-]"} for _ in range(4)],
            "geometry": "square_planar", "relax": False,
        })
    assert r.status_code == 200, r.text
    for k in OPT_IN_KEYS:
        assert seen.get(k) is False


def _capture_run_build(monkeypatch, spec, tmp_path):
    seen = []

    def fake_build_complex(cx, out_dir, **kwargs):
        seen.append(kwargs)
        return []

    monkeypatch.setattr(pipeline, "build_complex", fake_build_complex)
    _, errors = jobs.run_build(spec, tmp_path)
    assert not errors, errors
    return seen


def _cspec(**extra):
    return {"metal": "Pt", "oxidation_state": 2, "geometry": "square_planar",
            "ligands": [{"smiles": "[Cl-]"} for _ in range(4)], **extra}


def test_job_level_options_reach_every_complex(monkeypatch, tmp_path):
    spec = {"relax": False, "options": {"oxo_antifusion_floors": True},
            "complexes": [_cspec(), _cspec(options={})]}
    seen = _capture_run_build(monkeypatch, spec, tmp_path)
    assert [k["oxo_antifusion_floors"] for k in seen] == [True, True]


def test_per_complex_options_override_job_level_key_by_key(monkeypatch, tmp_path):
    spec = {"relax": False,
            "options": {"oxo_antifusion_floors": True, "reposition_polydentates": True},
            "complexes": [_cspec(options={"oxo_antifusion_floors": False})]}
    (kw,) = _capture_run_build(monkeypatch, spec, tmp_path)
    assert kw["oxo_antifusion_floors"] is False     # overridden per complex
    assert kw["reposition_polydentates"] is True    # untouched key keeps the job-level value


def test_submit_job_stores_only_explicit_per_complex_options():
    """A complex that sets no options must not store defaults that would then read as
    per-complex choices (the stored False beside a job-level True that looked ignored)."""
    with TestClient(fastapi_app) as c:
        r = c.post("/api/jobs", json={
            "relax": False, "options": {"oxo_antifusion_floors": True},
            "complexes": [
                {"metal": "Pt", "oxidation_state": 2, "geometry": "square_planar",
                 "ligands": [{"smiles": "[Cl-]"} for _ in range(4)]},
                {"metal": "Pt", "oxidation_state": 2, "geometry": "square_planar",
                 "ligands": [{"smiles": "[Cl-]"} for _ in range(4)],
                 "options": {"planar_guard": False}},
            ]})
        assert r.status_code == 202, r.text
        spec = json.loads(fastapi_app.state.store.get(r.json()["job_id"])["spec"])
    assert spec["complexes"][0]["options"] == {}
    assert spec["complexes"][1]["options"] == {"planar_guard": False}
    assert spec["options"]["oxo_antifusion_floors"] is True
