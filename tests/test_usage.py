"""Usage counter: anonymous daily totals behind the public "structures built" number."""

import importlib
import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from mecobi.web import app
from mecobi.web import usage
from mecobi.web.jobs import JobStatus, JobStore

DAY1 = datetime(2026, 11, 7, 10, tzinfo=timezone.utc)
DAY2 = DAY1 + timedelta(days=1)


def _db(tmp_path) -> sqlite3.Connection:
    c = sqlite3.connect(tmp_path / "u.db")
    usage.ensure_schema(c)
    return c


def _results(n):
    return [{"name": f"s{i}.xyz"} for i in range(n)]


def test_record_adds_up_and_counts_distinct_users_per_day(tmp_path):
    c = _db(tmp_path)
    usage.record(c, submitter="1.2.3.4", complexes=2, structures=5, now=DAY1)
    usage.record(c, submitter="1.2.3.4", complexes=1, structures=1, complex_errors=1,
                 failed=True, now=DAY1)
    usage.record(c, submitter="5.6.7.8", complexes=1, structures=3, now=DAY1)
    usage.record(c, submitter="1.2.3.4", complexes=1, structures=2, now=DAY2)
    rows = usage.daily(c)
    assert rows == [
        {"day": "2026-11-07", "requests": 3, "complexes": 4, "structures": 9,
         "complex_errors": 1, "failed_requests": 1, "users": 2},
        {"day": "2026-11-08", "requests": 1, "complexes": 1, "structures": 2,
         "complex_errors": 0, "failed_requests": 0, "users": 1},
    ]
    assert usage.totals(c) == {"structures_built": 11, "since": "2026-11-07"}


def test_no_address_is_stored_and_old_hashes_are_dropped(tmp_path):
    c = _db(tmp_path)
    usage.record(c, submitter="203.0.113.9", complexes=1, structures=1, now=DAY1)
    usage.record(c, submitter="203.0.113.9", complexes=1, structures=1, now=DAY2)
    c.commit()
    dump = "\n".join(c.iterdump())
    assert "203.0.113.9" not in dump
    # Only the current day's salted hashes remain.
    assert [r[0] for r in c.execute("SELECT day FROM usage_users")] == ["2026-11-08"]


def test_empty_totals(tmp_path):
    assert usage.totals(_db(tmp_path)) == {"structures_built": 0, "since": None}


def test_finished_job_counts_once_and_survives_cleanup(tmp_path):
    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    jid = store.create({"complexes": [{}, {}], "relax": False}, "1.2.3.4", start_running=True)
    store.finish(jid, _results(3), [{"complex": "b", "error": "x"}])
    store.finish(jid, _results(3))          # a repeat call must not count again
    store.fail(jid, "late failure")         # nor a terminal-to-terminal transition
    assert store.usage_totals()["structures_built"] == 3
    store.cleanup(ttl=timedelta(seconds=-1))   # job rows and files expire...
    assert store.get(jid) is None
    assert store.usage_totals()["structures_built"] == 3   # ...the totals do not


def test_failed_or_interrupted_jobs_count_what_they_finished(tmp_path):
    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    cancelled = store.create({"complexes": [{}] * 3}, "a", start_running=True)
    store.set_partial_results(cancelled, _results(2), [])
    store.fail(cancelled, "Cancelled by user.")
    interrupted = store.create({"complexes": [{}] * 3}, "b", start_running=True)
    store.set_partial_results(interrupted, _results(1), [])
    assert store.recover_interrupted() == 1
    store.recover_interrupted()             # nothing left running: no second count
    assert store.usage_totals()["structures_built"] == 3
    with sqlite3.connect(tmp_path / "jobs.db") as c:
        assert c.execute("SELECT requests, failed_requests FROM usage_daily").fetchone() == (2, 2)


def test_cancelling_a_queued_job_counts_nothing(tmp_path):
    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    jid = store.create({"complexes": [{}]}, "a")
    assert store.request_cancel(jid) == JobStatus.QUEUED.value
    assert store.usage_totals() == {"structures_built": 0, "since": None}


def test_export_writes_csv(tmp_path, capsys):
    store = JobStore(tmp_path / "jobs.db", tmp_path / "results")
    jid = store.create({"complexes": [{}]}, "a", start_running=True)
    store.finish(jid, _results(2))
    assert usage.main(["--db", str(tmp_path / "jobs.db")]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == ",".join(usage.COLUMNS)
    assert lines[1].split(",")[1:4] == ["1", "1", "2"]


def test_default_db_matches_the_app():
    # `mecobi.web.app` the attribute is the FastAPI instance; fetch the module itself.
    appmod = importlib.import_module("mecobi.web.app")
    assert usage.DEFAULT_DB == appmod._DATA / "jobs.db"


def test_stats_endpoint_counts_a_gui_build():
    req = {
        "metal": "Pt", "oxidation_state": 2, "geometry": "square_planar", "relax": False,
        "ligands": [{"smiles": "N", "coord_atoms": [0]}, {"smiles": "N", "coord_atoms": [0]},
                    {"smiles": "[Cl-]", "coord_atoms": [0]},
                    {"smiles": "[Cl-]", "coord_atoms": [0]}],
    }
    with TestClient(app) as c:
        before = c.get("/api/stats").json()
        r = c.post("/api/build", json=req)
        assert r.status_code == 200, r.text
        after = c.get("/api/stats").json()
    assert set(after) == {"structures_built", "since"}
    assert after["structures_built"] - before["structures_built"] == len(r.json()["results"]) >= 1
    assert after["since"] is not None
