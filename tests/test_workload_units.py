"""Queue workload is counted in structures, not input rows.

One "all isomers" row can build up to MECOBI_MAX_ISOMERS structures (64), or
MECOBI_MAX_ISOMERS_HIGH_CN above CN 6 (16). Admission, the pending budget, the
time estimate and progress all use the same unit (jobs.workload_units).
"""

import importlib

import pytest
from fastapi.testclient import TestClient

from mecobi.web import jobs
from mecobi.web.jobs import JobStore, QueueFull


def _mono(smiles):
    return {"smiles": smiles, "coord_atoms": [0]}


def _row(metal, os_, geometry, ligands, all_isomers=True, **extra):
    return {"metal": metal, "oxidation_state": os_, "geometry": geometry,
            "ligands": ligands, "all_isomers": all_isomers, **extra}


CISPLATIN = _row("Pt", 2, "square_planar", [_mono(s) for s in ["N", "N", "[Cl-]", "[Cl-]"]])
# Eight different monodentates on a square antiprism: hundreds of isomers.
CN8_MIXED = _row("Zr", 4, "square_antiprism",
                 [_mono(s) for s in ["N", "O", "[Cl-]", "[Br-]", "[I-]", "[F-]", "S", "P"]])
# Six different monodentates on an octahedron: 30 stereoisomers.
OCT_MIXED = _row("Co", 3, "octahedral",
                 [_mono(s) for s in ["N", "O", "[Cl-]", "[Br-]", "[I-]", "[F-]"]])


# --------------------------------------------------------------------------- #
# workload_units
# --------------------------------------------------------------------------- #

def test_one_structure_without_all_isomers():
    assert jobs.workload_units({**CISPLATIN, "all_isomers": False}) == 1


def test_an_explicit_isomer_is_one_structure_even_with_all_isomers():
    assert jobs.workload_units({**CISPLATIN, "assignment": {"0": [0]}}) == 1
    assert jobs.workload_units({**CISPLATIN, "site_assignment": {"0": [0]}}) == 1


def test_all_isomers_costs_the_enumerated_count():
    assert jobs.workload_units(CISPLATIN) == 2  # cis + trans


def test_all_isomers_respects_the_cap(monkeypatch):
    assert jobs.workload_units(OCT_MIXED) == 30
    monkeypatch.setenv("MECOBI_MAX_ISOMERS", "10")
    assert jobs.workload_units(OCT_MIXED) == 10


def test_all_isomers_above_cn6_uses_the_high_cn_cap(monkeypatch):
    assert jobs.workload_units(CN8_MIXED) == 16
    monkeypatch.setenv("MECOBI_MAX_ISOMERS_HIGH_CN", "5")
    assert jobs.workload_units(CN8_MIXED) == 5


def test_uncostable_rows_are_charged_the_full_cap():
    no_donors = {**CISPLATIN, "ligands": [{"smiles": "N"}] * 4}  # would need ML perception
    assert jobs.workload_units(no_donors) == 64
    assert jobs.workload_units({**CISPLATIN, "geometry": "no_such_geometry"}) == 64
    assert jobs.workload_units(CISPLATIN, enumerate_isomers=False) == 64


def test_batch_costing_memoises_and_falls_back_to_the_cap_past_the_budget():
    assert jobs.workload_units_for([CISPLATIN, CISPLATIN, OCT_MIXED]) == [2, 2, 30]
    assert jobs.workload_units_for([CISPLATIN, {**CISPLATIN, "all_isomers": False}],
                                   budget_s=0) == [64, 1]


# --------------------------------------------------------------------------- #
# job store: admission, estimate, workload, progress
# --------------------------------------------------------------------------- #

def test_a_small_row_count_cannot_bypass_the_pending_budget(tmp_path):
    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    with pytest.raises(QueueFull, match="this job needs 1100"):
        store.create({"complexes": [{}, {}], "workload_units": [600, 500]}, "a", max_pending=1000)
    store.create({"complexes": [{}], "workload_units": [64]}, "a", max_pending=100)
    with pytest.raises(QueueFull):
        store.create({"complexes": [{}], "workload_units": [40]}, "b", max_pending=100)
    store.create({"complexes": [{}], "workload_units": [36]}, "b", max_pending=100)  # exactly full


def test_estimate_and_workload_count_structures(tmp_path):
    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    jid = store.create({"complexes": [{}, {}], "workload_units": [1, 30], "relax": True}, "a")
    job = store.get(jid)
    assert job["n_complexes"] == 2 and job["n_units"] == 31
    assert job["estimate_s"] == jobs.estimate_seconds(31, relax=True)
    summary = store.workload()
    assert summary["pending_complexes"] == 2 and summary["pending_structures"] == 31


def test_spec_without_units_counts_one_per_complex(tmp_path):
    # Jobs stored before the unit existed (and malformed unit lists) read as one per row.
    assert jobs.spec_units({"complexes": [{}, {}, {}]}) == 3
    assert jobs.spec_units({"complexes": [{}, {}], "workload_units": [5]}) == 2


def test_progress_is_weighted_by_structures(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, "_build_one", lambda *a, **k: [])
    seen = []
    spec = {"relax": False, "complexes": [{"name": "big"}, {"name": "small"}],
            "workload_units": [9, 1]}
    jobs.run_build(spec, tmp_path, on_progress=lambda f, stage: seen.append(f))
    assert seen == [0.0, 0.9]


# --------------------------------------------------------------------------- #
# HTTP: same units in admission, responses and limits
# --------------------------------------------------------------------------- #

@pytest.fixture
def client(tmp_path, monkeypatch):
    mod = importlib.import_module("mecobi.web.app")
    monkeypatch.setattr(mod, "_DATA", tmp_path)
    monkeypatch.setattr(mod, "_RESULTS", tmp_path / "results")
    app = mod.create_app()
    with TestClient(app) as client:
        app.state.worker.stop(join_timeout=2)  # keep submitted jobs queued
        yield client


def test_submitted_job_reports_its_size_in_structures(client):
    r = client.post("/api/jobs", json={"complexes": [CISPLATIN, {**CISPLATIN, "all_isomers": False}],
                                       "relax": False})
    assert r.status_code == 202, r.text
    job = r.json()
    assert job["n_complexes"] == 2 and job["n_structures"] == 3
    assert job["estimate_s"] == jobs.estimate_seconds(3, relax=False)
    summary = client.get("/api/workload").json()
    assert summary["pending_structures"] == 3 and summary["pending_complexes"] == 2
    assert "max_pending_structures" in summary and "max_pending_complexes" not in summary


def test_job_larger_than_the_budget_is_rejected_outright(client, monkeypatch):
    mod = importlib.import_module("mecobi.web.app")
    monkeypatch.setattr(mod, "MAX_PENDING_STRUCTURES", 20)
    r = client.post("/api/jobs", json={"complexes": [OCT_MIXED], "relax": False})
    assert r.status_code == 400
    assert "30 structures" in r.json()["detail"]


def test_all_isomers_rows_fill_the_queue_before_their_row_count_does(client, monkeypatch):
    mod = importlib.import_module("mecobi.web.app")
    monkeypatch.setattr(mod, "MAX_PENDING_STRUCTURES", 40)
    assert client.post("/api/jobs", json={"complexes": [OCT_MIXED], "relax": False}).status_code == 202
    r = client.post("/api/jobs", json={"complexes": [CISPLATIN] * 6, "relax": False})  # 12 more
    assert r.status_code == 429
    assert "unfinished structures" in r.json()["detail"]
