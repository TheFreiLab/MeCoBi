"""/api/download/<job>: bounded, file-backed, cached "Download all" archives."""

import importlib
import io
import os
import zipfile

import pytest
from fastapi.testclient import TestClient

from mecobi.web.jobs import JobStatus


@pytest.fixture
def env(tmp_path, monkeypatch):
    mod = importlib.import_module("mecobi.web.app")
    monkeypatch.setattr(mod, "_DATA", tmp_path)
    monkeypatch.setattr(mod, "_RESULTS", tmp_path / "results")
    app = mod.create_app()
    with TestClient(app) as client:
        app.state.worker.stop(join_timeout=2)
        yield mod, app, client, tmp_path / "results"


def _job(app, results, files, status=JobStatus.DONE):
    """A job row plus its directory holding ``files`` ({name: text})."""
    store = app.state.store
    jid = store.create({"complexes": [{}]}, "me")
    if status is JobStatus.DONE:
        store.claim_next()
        store.finish(jid, [])
    job_dir = results / jid
    job_dir.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (job_dir / name).write_text(text, encoding="utf-8")
    return jid, job_dir


def _names(resp):
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        return sorted(zf.namelist())


def test_finished_job_archive_is_built_once_and_reused(env):
    mod, app, client, results = env
    jid, job_dir = _job(app, results, {"a.xyz": "1\n\nPt 0 0 0\n", "a.mol": "m", "a.pdb": "p",
                                       "notes.txt": "not a structure"})
    r = client.get(f"/api/download/{jid}")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    assert f'filename="mecobi_{jid}.zip"' in r.headers["content-disposition"]
    assert _names(r) == ["a.mol", "a.pdb", "a.xyz"]
    cached = job_dir / mod._ARCHIVE_NAME
    assert cached.is_file()
    assert not list(job_dir.glob(".download-*"))  # no temp file left behind
    mtime = cached.stat().st_mtime_ns
    # Repeat downloads are served from the cached archive, even with archive building blocked.
    for _ in range(3):
        app.state.zip_slots.acquire()
        try:
            r2 = client.get(f"/api/download/{jid}")
        finally:
            app.state.zip_slots.release()
        assert r2.status_code == 200 and _names(r2) == ["a.mol", "a.pdb", "a.xyz"]
    assert cached.stat().st_mtime_ns == mtime


def test_unfinished_job_archive_is_temporary(env):
    mod, app, client, results = env
    jid, job_dir = _job(app, results, {"a.xyz": "x"}, status=JobStatus.QUEUED)
    r = client.get(f"/api/download/{jid}")
    assert r.status_code == 200 and _names(r) == ["a.xyz"]
    assert not (job_dir / mod._ARCHIVE_NAME).exists()  # partial job: never cached
    assert not list(job_dir.glob(".download-*"))       # temp archive removed after sending


def test_empty_and_missing_jobs(env):
    mod, app, client, results = env
    jid, _ = _job(app, results, {"readme.txt": "no structures"})
    assert client.get(f"/api/download/{jid}").status_code == 404
    assert client.get("/api/download/nosuchjob").status_code == 404
    for bad in ["..", "a.b", "a%2F..%2Fb", "x'y"]:
        assert client.get(f"/api/download/{bad}").status_code in (400, 404)


def test_limits_are_checked_before_compressing(env, monkeypatch):
    mod, app, client, results = env
    jid, job_dir = _job(app, results, {f"s{i}.xyz": "x" * 100 for i in range(5)})
    monkeypatch.setattr(mod, "MAX_ZIP_FILES", 4)
    r = client.get(f"/api/download/{jid}")
    assert r.status_code == 413 and "5 files" in r.json()["detail"]
    monkeypatch.setattr(mod, "MAX_ZIP_FILES", 100)
    monkeypatch.setattr(mod, "MAX_ZIP_BYTES", 400)
    assert client.get(f"/api/download/{jid}").status_code == 413
    assert not list(job_dir.glob(".download-*")) and not (job_dir / mod._ARCHIVE_NAME).exists()


def test_symlinks_are_never_archived(env, tmp_path):
    mod, app, client, results = env
    secret = tmp_path / "secret.xyz"
    secret.write_text("outside the job", encoding="utf-8")
    jid, job_dir = _job(app, results, {"real.xyz": "x"})
    try:
        os.symlink(secret, job_dir / "link.xyz")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not permitted on this platform/account")
    r = client.get(f"/api/download/{jid}")
    assert r.status_code == 200 and _names(r) == ["real.xyz"]


def test_concurrent_archive_builds_are_bounded(env):
    mod, app, client, results = env
    jid, _ = _job(app, results, {"a.xyz": "x"}, status=JobStatus.QUEUED)
    held = [app.state.zip_slots.acquire(timeout=0) for _ in range(mod.ZIP_CONCURRENCY)]
    try:
        r = client.get(f"/api/download/{jid}")
        assert r.status_code == 503 and r.headers["retry-after"]
    finally:
        for ok in held:
            if ok:
                app.state.zip_slots.release()
    assert client.get(f"/api/download/{jid}").status_code == 200


def test_archive_building_is_rate_limited(env):
    mod, app, client, results = env
    jid, _ = _job(app, results, {"a.xyz": "x"}, status=JobStatus.QUEUED)  # never cached
    codes = [client.get(f"/api/download/{jid}").status_code for _ in range(35)]
    assert codes[:30] == [200] * 30 and codes[30:] == [429] * 5
