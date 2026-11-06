import importlib
import json
import threading
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from mecobi.web import jobs


def test_retention_starts_at_completion_and_preserves_active(tmp_path, monkeypatch):
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)
    monkeypatch.setattr(jobs, '_now', lambda: now)
    store = jobs.JobStore(tmp_path / 'jobs.db', tmp_path / 'results')
    running = store.create({'complexes': [{}]}, 'ip', start_running=True)
    queued = store.create({'complexes': [{}]}, 'ip')
    done = store.create({'complexes': [{}]}, 'ip', start_running=True)
    now += timedelta(days=3)
    store.finish(done, [])
    assert store.cleanup() == 0
    now += timedelta(hours=25)
    assert store.cleanup() == 1
    assert store.get(running)['status'] == 'running'
    assert store.get(queued)['status'] == 'queued'


def test_restart_preserves_partial_results_and_queued_jobs(tmp_path):
    store = jobs.JobStore(tmp_path / 'jobs.db', tmp_path / 'results')
    running = store.create({'complexes': [{}, {}]}, 'ip', start_running=True)
    queued = store.create({'complexes': [{}]}, 'ip')
    store.set_partial_results(running, [{'name': 'completed.xyz'}], [])
    reopened = jobs.JobStore(store.db_path, store.results_dir)
    assert reopened.recover_interrupted() == 1
    row = reopened.get(running)
    assert row['status'] == 'failed' and 'restart' in row['error']
    assert json.loads(row['results']) == [{'name': 'completed.xyz'}]
    assert row['finished_at']
    assert reopened.claim_next()['id'] == queued


def test_shutdown_finishes_current_complex_only(tmp_path, monkeypatch):
    store = jobs.JobStore(tmp_path / 'jobs.db', tmp_path / 'results')
    jid = store.create({'complexes': [{'name': 'first'}, {'name': 'second'}]}, 'ip')
    next_job = store.create({'complexes': [{'name': 'next job'}]}, 'ip')
    entered, release = threading.Event(), threading.Event()
    built = []
    def build(spec, *args):
        built.append(spec['name'])
        entered.set()
        assert release.wait(5)
        return [{'name': 'first.xyz'}]
    monkeypatch.setattr(jobs, '_build_one', build)
    worker = jobs.Worker(store)
    worker.start()
    try:
        assert entered.wait(5)
        worker.stop()
        release.set()
        worker.join(5)
        assert not worker.is_alive()
        assert built == ['first']
        row = store.get(jid)
        assert row['status'] == 'failed' and 'shutdown' in row['error']
        assert json.loads(row['results']) == [{'name': 'first.xyz'}]
        assert store.get(next_job)['status'] == 'queued'
        assert not jobs.BUILD_SLOT.locked()
    finally:
        release.set()
        worker.stop(join_timeout=5)


def test_cleaner_runs_while_build_slot_busy_and_retries(tmp_path, monkeypatch):
    store = jobs.JobStore(tmp_path / 'jobs.db', tmp_path / 'results')
    cleaned = threading.Event()
    attempts = []
    def cleanup():
        attempts.append(True)
        if len(attempts) == 1:
            raise OSError('temporarily locked')
        cleaned.set()
    monkeypatch.setattr(store, 'cleanup', cleanup)
    cleaner = jobs.Cleaner(store, interval_s=0.01)
    with jobs.BUILD_SLOT:
        cleaner.start()
        try:
            assert cleaned.wait(5)
        finally:
            cleaner.stop()
    assert len(attempts) >= 2
    assert not cleaner.is_alive()


@pytest.mark.parametrize('fail', [False, True])
def test_individual_build_outputs_are_tracked_and_expire(tmp_path, monkeypatch, fail):
    mod = importlib.import_module('mecobi.web.app')
    monkeypatch.setattr(mod, '_DATA', tmp_path)
    monkeypatch.setattr(mod, '_RESULTS', tmp_path / 'results')
    dirs = []
    def build(req, directory):
        dirs.append(directory)
        directory.mkdir()
        (directory / 'test.xyz').write_text('1\n\nH 0 0 0\n')
        if fail:
            raise HTTPException(422, 'test failure')
        return [mod.BuiltFile(name='test.xyz', token=f'{directory.name}/test.xyz',
                              total_charge=0, uhf=0)]
    monkeypatch.setattr(mod, '_build_one_sync', build)
    with TestClient(mod.create_app()) as client:
        response = client.post('/api/build', json={
            'metal': 'Pt', 'oxidation_state': 2, 'geometry': 'square_planar',
            'ligands': [{'smiles': 'N'}] * 4, 'relax': False})
        assert response.status_code == (422 if fail else 200)
        store = client.app.state.store
        row = store.get(dirs[0].name)
        assert row['status'] == ('failed' if fail else 'done')
        assert row['finished_at']
        assert store.cleanup() == 0
        assert store.cleanup(ttl=timedelta(seconds=-1)) == 1
        assert not dirs[0].exists()


def test_legacy_outputs_get_one_grace_period(tmp_path, monkeypatch):
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)
    monkeypatch.setattr(jobs, '_now', lambda: now)
    store = jobs.JobStore(tmp_path / 'jobs.db', tmp_path / 'results')
    legacy = store.results_dir / 'abcdef123456'
    legacy.mkdir()
    unrelated = store.results_dir / 'notes'
    unrelated.mkdir()
    assert store.track_legacy_outputs() == 1
    assert store.cleanup() == 0
    now += timedelta(hours=25)
    assert store.track_legacy_outputs() == 0
    assert store.cleanup() == 1
    assert not legacy.exists()
    assert unrelated.exists()


def test_cleanup_retries_failed_deletion(tmp_path, monkeypatch):
    store = jobs.JobStore(tmp_path / 'jobs.db', tmp_path / 'results')
    jid = store.create({'complexes': [{}]}, 'ip')
    store.finish(jid, [])
    real_remove = jobs._rmtree
    def locked(path):
        raise PermissionError('file in use')
    monkeypatch.setattr(jobs, '_rmtree', locked)
    assert store.cleanup(ttl=timedelta(seconds=-1)) == 0
    assert store.get(jid) is not None
    monkeypatch.setattr(jobs, '_rmtree', real_remove)
    assert store.cleanup(ttl=timedelta(seconds=-1)) == 1


def test_old_database_migrates_terminal_completion_time(tmp_path):
    store = jobs.JobStore(tmp_path / 'jobs.db', tmp_path / 'results')
    done = store.create({'complexes': [{}]}, 'ip')
    store.finish(done, [])
    queued = store.create({'complexes': [{}]}, 'ip')
    with store._conn() as c:
        c.execute('ALTER TABLE jobs DROP COLUMN finished_at')
    reopened = jobs.JobStore(store.db_path, store.results_dir)
    assert reopened.get(done)['finished_at'] == reopened.get(done)['updated_at']
    assert reopened.get(queued)['finished_at'] is None


def test_stop_during_final_complex_still_completes_job(tmp_path, monkeypatch):
    store = jobs.JobStore(tmp_path / 'jobs.db', tmp_path / 'results')
    jid = store.create({'complexes': [{}]}, 'ip')
    worker = jobs.Worker(store)
    def build(*args):
        worker.stop()
        return [{'name': 'last.xyz'}]
    monkeypatch.setattr(jobs, '_build_one', build)
    worker.start()
    worker.join(5)
    assert not worker.is_alive()
    assert store.get(jid)['status'] == 'done'
