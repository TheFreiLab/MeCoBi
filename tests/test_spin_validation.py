"""`spin` is scientific input: exactly "low" or "high", never silently coerced.

It sets xtb's --uhf, so a typo ("High", "hgih") used to build a low-spin
structure without a word. The request model now uses the Spin enum (422 on
anything else) and the queued job's reconstruction keeps the same contract.
"""

import importlib
import json

import pytest
from fastapi.testclient import TestClient

from mecobi.model import Spin
from mecobi.web import jobs

BAD_SPINS = ["High", "HIGH", "Low", "hgih", "", "intermediate", 2]


def _row(**extra):
    return {"metal": "Fe", "oxidation_state": 2, "geometry": "octahedral",
            "ligands": [{"smiles": "N", "coord_atoms": [0]}] * 6, "relax": False, **extra}


@pytest.fixture
def client(tmp_path, monkeypatch):
    mod = importlib.import_module("mecobi.web.app")
    monkeypatch.setattr(mod, "_DATA", tmp_path)
    monkeypatch.setattr(mod, "_RESULTS", tmp_path / "results")
    app = mod.create_app()
    with TestClient(app) as client:
        app.state.worker.stop(join_timeout=2)  # keep submitted jobs queued for inspection
        yield client


@pytest.mark.parametrize("spin", BAD_SPINS)
def test_sync_build_rejects_an_unknown_spin(client, spin):
    r = client.post("/api/build", json=_row(spin=spin))
    assert r.status_code == 422
    assert any(e["loc"][-1] == "spin" for e in r.json()["detail"])


@pytest.mark.parametrize("spin", BAD_SPINS)
def test_queued_job_rejects_an_unknown_spin(client, spin):
    r = client.post("/api/jobs", json={"complexes": [_row(), _row(spin=spin)], "relax": False})
    assert r.status_code == 422


@pytest.mark.parametrize("spin, expected", [("low", Spin.LOW), ("high", Spin.HIGH), (None, Spin.LOW)])
def test_valid_spin_round_trips_through_the_queue(client, spin, expected):
    row = _row() if spin is None else _row(spin=spin)
    r = client.post("/api/jobs", json={"complexes": [row], "relax": False})
    assert r.status_code == 202, r.text
    stored = json.loads(client.app.state.store.get(r.json()["job_id"])["spec"])["complexes"][0]
    assert stored["spin"] == expected.value  # serialised as the plain enum value
    assert jobs._reconstruct(stored).spin is expected


def test_reconstruction_refuses_a_stored_unknown_spin():
    with pytest.raises(ValueError):
        jobs._reconstruct({**_row(), "spin": "High"})
    assert jobs._reconstruct({k: v for k, v in _row().items()}).spin is Spin.LOW  # absent = low
