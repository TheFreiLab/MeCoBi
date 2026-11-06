"""Async job layer: store / rate-limit / cleanup (fast) + submit-poll (slow)."""

import sqlite3
import time
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mecobi.web import app as mecobi_app  # the FastAPI instance
from mecobi.web.jobs import JobStatus, JobStore, RateLimiter, estimate_seconds, run_build

REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_CSV = Path(__file__).resolve().parent / "fixtures" / "test_compounds.csv"


# --------------------------------------------------------------------------- #
# fast unit tests
# --------------------------------------------------------------------------- #

def test_rate_limiter_blocks_after_max():
    rl = RateLimiter(max_per_window=3, window_s=60)
    assert [rl.allow("ip") for _ in range(4)] == [True, True, True, False]
    assert rl.allow("other-ip") is True  # per-key


def test_worker_stops_and_joins_cleanly(tmp_path):
    """An idle worker must stop and join without error (regression: the old
    `self._stop` shadowed threading.Thread._stop and could break join())."""
    from mecobi.web.jobs import Worker

    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    worker = Worker(store)
    worker.start()
    assert worker.is_alive()
    worker.stop(join_timeout=5.0)
    assert not worker.is_alive()


def test_worker_survives_a_failing_store(tmp_path):
    """A store error must not kill the only queue thread.

    Regression for a production outage (2026-09-15): `claim_next` hit a transient
    sqlite `OperationalError: unable to open database file` when the VM's disk
    filled during a package download. The exception propagated straight out of
    `Worker.run`, the single queue thread died, and every job submitted over the
    next four days sat queued forever while `/api/health` still returned ok.
    """
    from mecobi.web.jobs import Worker

    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    real_claim, calls = store.claim_next, []

    def flaky_claim():
        calls.append(1)
        if len(calls) <= 3:
            raise sqlite3.OperationalError("unable to open database file")
        return real_claim()

    store.claim_next = flaky_claim
    worker = Worker(store)
    worker.start()
    try:
        deadline = time.time() + 10
        while len(calls) < 5 and time.time() < deadline:
            time.sleep(0.05)
        assert worker.is_alive(), "a store error killed the queue worker"
        assert len(calls) >= 5, "worker stopped polling after the failures"
    finally:
        worker.stop(join_timeout=5.0)


def test_estimate_scales_with_relax():
    assert estimate_seconds(2, relax=False) < estimate_seconds(2, relax=True)


def test_run_build_fault_isolation(tmp_path):
    """One bad complex must not discard the whole batch's results (assembly-only)."""
    spec = {
        "relax": False,
        "complexes": [
            {"name": "good_cisplatin", "metal": "Pt", "oxidation_state": 2,
             "geometry": "square_planar",
             "ligands": [{"smiles": s} for s in ["N", "N", "[Cl-]", "[Cl-]"]]},
            {"name": "bad_metal", "metal": "Xx", "oxidation_state": 2,
             "geometry": "linear",
             "ligands": [{"smiles": "N"}, {"smiles": "N"}]},
            {"name": "good_diammine", "metal": "Pt", "oxidation_state": 2,
             "geometry": "linear",
             "ligands": [{"smiles": "N"}, {"smiles": "N"}]},
        ],
    }
    results, errors = run_build(spec, tmp_path)
    built = {r["complex"] for r in results}
    assert "good_cisplatin" in built and "good_diammine" in built  # survivors kept
    assert [e["complex"] for e in errors] == ["bad_metal"]         # only the bad one failed
    assert errors[0]["error"]  # non-empty, human-readable


def test_job_store_lifecycle(tmp_path):
    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    jid = store.create({"complexes": [{"name": "x"}], "relax": False}, submitter="1.2.3.4")
    assert store.get(jid)["status"] == JobStatus.QUEUED.value

    claimed = store.claim_next()
    assert claimed["id"] == jid
    assert store.get(jid)["status"] == JobStatus.RUNNING.value
    assert store.claim_next() is None  # nothing left queued

    store.finish(jid, [{"name": "x_c0.xyz", "token": f"{jid}/x_c0.xyz",
                        "total_charge": 0, "uhf": 0, "warnings": []}])
    assert store.get(jid)["status"] == JobStatus.DONE.value


def test_cancel_queued_job_fails_it_immediately(tmp_path):
    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    jid = store.create({"complexes": [{"name": "x"}], "relax": False}, submitter="1.2.3.4")
    prev = store.request_cancel(jid)
    assert prev == JobStatus.QUEUED.value
    # A cancelled queued job never runs: it is terminal, and claim_next skips it.
    assert store.get(jid)["status"] == JobStatus.FAILED.value
    assert store.claim_next() is None
    assert not store.is_cancel_requested(jid)  # no running-flag for a queued cancel


def test_cancel_running_job_sets_a_cooperative_flag(tmp_path):
    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    jid = store.create({"complexes": [{"name": "x"}], "relax": False}, submitter="1.2.3.4")
    store.claim_next()  # -> RUNNING
    prev = store.request_cancel(jid)
    assert prev == JobStatus.RUNNING.value
    # The worker checks this between complexes (xtb is never killed mid-structure).
    assert store.is_cancel_requested(jid) is True
    store.clear_cancel(jid)
    assert store.is_cancel_requested(jid) is False


def test_cancel_finished_or_unknown_job_is_a_noop(tmp_path):
    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    assert store.request_cancel("does-not-exist") is None
    jid = store.create({"complexes": [], "relax": False}, submitter="ip")
    store.claim_next()
    store.finish(jid, [])
    assert store.request_cancel(jid) is None  # already terminal
    assert store.get(jid)["status"] == JobStatus.DONE.value


def test_job_store_progress_tracking(tmp_path):
    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    jid = store.create({"complexes": [{"name": "a"}, {"name": "b"}], "relax": False}, "1.2.3.4")
    assert store.get(jid)["progress"] == 0.0

    store.set_progress(jid, 0.5, "building 1/2: a")
    row = store.get(jid)
    assert row["progress"] == 0.5 and row["stage"] == "building 1/2: a"

    store.set_progress(jid, 5.0, "clamped")  # out-of-range fraction is clamped
    assert store.get(jid)["progress"] == 1.0

    store.finish(jid, [])
    done = store.get(jid)
    assert done["progress"] == 1.0 and done["stage"] == "done"


def test_job_store_cleanup_removes_old(tmp_path):
    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    jid = store.create({"complexes": [], "relax": False}, submitter="ip")
    job_dir = (tmp_path / "results" / jid)
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "f.xyz").write_text("1\n\nH 0 0 0\n")

    assert store.cleanup(ttl=timedelta(hours=24)) == 0  # too new
    store.finish(jid, [])
    removed = store.cleanup(ttl=timedelta(seconds=-1))  # completed results are "old"
    assert removed == 1
    assert store.get(jid) is None
    assert not job_dir.exists()


# --------------------------------------------------------------------------- #
# slow integration: submit -> worker -> poll -> fetch
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_submit_poll_fetch(tmp_path):
    with TestClient(mecobi_app) as client:
        parsed = client.post("/api/parse", json={"csv": PROTOTYPE_CSV.read_text()}).json()
        row = next(x for x in parsed if x["name"] == "Sq2b_Pt_1")
        req = {
            "complexes": [{
                "name": "Sq2b_Pt_1", "metal": row["metal"],
                "oxidation_state": row["oxidation_state"],
                "ligands": [{"smiles": l["smiles"], "coord_atoms": l["coord_atoms"],
                             "is_arene": l["is_arene"]} for l in row["ligands"]],
                "geometry": row["proposed_geometry"], "spin": "low",
            }],
            "relax": False,
        }
        sub = client.post("/api/jobs", json=req)
        assert sub.status_code == 202
        job_id = sub.json()["job_id"]
        assert sub.json()["status"] == JobStatus.QUEUED.value

        deadline = time.time() + 90
        status = None
        while time.time() < deadline:
            job = client.get(f"/api/jobs/{job_id}").json()
            status = job["status"]
            if status in (JobStatus.DONE.value, JobStatus.FAILED.value):
                break
            time.sleep(0.5)

        assert status == JobStatus.DONE.value, job
        assert len(job["results"]) == 1
        token = job["results"][0]["token"]
        rf = client.get(f"/api/file/{token}")
        assert rf.status_code == 200 and int(rf.text.splitlines()[0]) == 41


def test_get_unknown_job_404():
    with TestClient(mecobi_app) as client:
        assert client.get("/api/jobs/deadbeef").status_code == 404


def test_submit_empty_rejected():
    with TestClient(mecobi_app) as client:
        assert client.post("/api/jobs", json={"complexes": [], "relax": False}).status_code == 400
