import asyncio
import importlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from mecobi.web.jobs import BUILD_SLOT, JobStore, QueueFull
from mecobi.web.limits import BodySizeLimit


def test_chunked_body_rejected_before_application():
    called = []
    sent = []
    chunks = iter([b'123', b'456'])
    async def receive():
        return {'type': 'http.request', 'body': next(chunks), 'more_body': True}
    async def send(message):
        sent.append(message)
    async def app(scope, receive, send):
        called.append(True)
    asyncio.run(BodySizeLimit(app, lambda: 5)(
        {'type': 'http', 'headers': []}, receive, send))
    assert not called
    assert sent[0]['status'] == 413


def test_admission_is_atomic_across_connections(tmp_path):
    stores = [JobStore(tmp_path / 'jobs.db', tmp_path / 'results') for _ in range(2)]
    def submit(store):
        try:
            return store.create({'complexes': [{}] * 600}, 'private', max_pending=1000)
        except QueueFull:
            return None
    with ThreadPoolExecutor(2) as pool:
        ids = list(pool.map(submit, stores))
    assert sum(x is not None for x in ids) == 1
    store = stores[0]
    jid = next(x for x in ids if x)
    store.claim_next()
    store.set_progress(jid, 0.5, 'private molecule')
    summary = store.workload()
    assert summary['pending_complexes'] == 600
    assert summary['running_jobs'] == 1
    assert summary['estimated_wait_s'] == 9000
    assert 'private' not in str(summary)
    store.create({'complexes': [{}] * 400}, 'other', max_pending=1000)
    with pytest.raises(QueueFull):
        store.create({'complexes': [{}]}, 'other', max_pending=1000)
    store.finish(jid, [])
    store.create({'complexes': [{}] * 600}, 'other', max_pending=1000)


@pytest.fixture
def client(tmp_path, monkeypatch):
    mod = importlib.import_module('mecobi.web.app')
    monkeypatch.setattr(mod, '_DATA', tmp_path)
    monkeypatch.setattr(mod, '_RESULTS', tmp_path / 'results')
    app = mod.create_app()
    with TestClient(app) as client:
        app.state.worker.stop(join_timeout=2)
        yield client


def test_queue_full_and_busy_build(client, monkeypatch):
    mod = importlib.import_module('mecobi.web.app')
    monkeypatch.setattr(mod, 'BUILD_SLOT_TIMEOUT_S', 0.1)  # don't wait out the real slot timeout
    client.app.state.store.create({'complexes': [{}] * 1000}, 'secret')
    summary = client.get('/api/workload').json()
    assert summary['busy']
    assert summary['pending_complexes'] == 1000
    spec = {'metal': 'Pt', 'oxidation_state': 2, 'geometry': 'square_planar',
            'ligands': [{'smiles': 'N'}] * 4}
    assert client.post('/api/jobs', json={'complexes': [spec]}).status_code == 429
    assert client.post('/api/build', json=spec).status_code == 503
    assert not BUILD_SLOT.locked()
    with BUILD_SLOT:
        assert client.post('/api/build', json=spec).status_code == 503


def test_invalid_request_is_rejected_whatever_the_slot_is_doing(client):
    # A malformed request must not depend on server load: with the build slot
    # held it still 400s on the bad geometry rather than 503ing on the slot.
    spec = {'metal': 'Pt', 'oxidation_state': 2, 'geometry': 'cubic',
            'ligands': [{'smiles': '[Cl-]'}]}
    with BUILD_SLOT:
        assert client.post('/api/build', json=spec).status_code == 400


def test_build_waits_out_a_transient_slot_holder(client, monkeypatch):
    # The queue worker grabs the shared slot on every poll (0.4 s) just to look
    # for work, so a non-blocking acquire 503s an idle server at random. The
    # request must wait that momentary hold out instead.
    mod = importlib.import_module('mecobi.web.app')
    monkeypatch.setattr(mod, '_build_one_sync', lambda req, job_dir: [])
    spec = {'metal': 'Pt', 'oxidation_state': 2, 'geometry': 'square_planar',
            'ligands': [{'smiles': '[Cl-]'}] * 4}
    BUILD_SLOT.acquire()
    releaser = threading.Timer(0.3, BUILD_SLOT.release)
    releaser.start()
    try:
        assert client.post('/api/build', json=spec).status_code == 200
    finally:
        releaser.join(5)
    assert not BUILD_SLOT.locked()


def test_workload_is_not_busy_while_the_idle_worker_holds_the_slot(client):
    with BUILD_SLOT:
        assert client.get('/api/workload').json()['busy'] is False
    client.app.state.store.create({'complexes': [{}]}, 'someone')
    assert client.get('/api/workload').json()['busy'] is True


@pytest.mark.parametrize('endpoint', ['perceive', 'isomers'])
def test_preview_rejects_oversized_ligand(client, endpoint):
    response = client.post('/api/' + endpoint, json={
        'metal': 'Pt', 'oxidation_state': 2, 'geometry': 'square_planar',
        'ligands': [{'smiles': 'C' * 401}]})
    assert response.status_code == 400


def test_preview_burst_queues_instead_of_rejecting(client):
    # The donor panel fires one /api/depict per ligand at once, so a normal
    # complex bursts more previews than the concurrency cap. With every slot held
    # the request must QUEUE and then succeed once a slot frees — the old
    # non-blocking guard 503'd it instantly, so a >cap-ligand panel lost previews.
    mod = importlib.import_module('mecobi.web.app')

    slots = client.app.state.preview_slots
    held = [slots.acquire() for _ in range(mod.PREVIEW_CONCURRENCY)]
    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(client.get, '/api/depict', params={'smiles': 'c1ccccc1N'})
            time.sleep(0.3)
            assert not fut.done()          # waiting on a slot, not rejected
            slots.release()
            held.pop()
            resp = fut.result(timeout=5)
    finally:
        for _ in held:
            slots.release()
    assert resp.status_code == 200
    assert resp.json()['atoms']


def test_preview_rejects_only_after_queue_timeout(client, monkeypatch):
    # A genuine sustained overload (every slot held past the wait) still 503s.
    mod = importlib.import_module('mecobi.web.app')

    monkeypatch.setattr(mod, 'PREVIEW_SLOT_TIMEOUT_S', 0.1)
    slots = client.app.state.preview_slots
    held = [slots.acquire() for _ in range(mod.PREVIEW_CONCURRENCY)]
    try:
        resp = client.get('/api/depict', params={'smiles': 'N'})
    finally:
        for _ in held:
            slots.release()
    assert resp.status_code == 503
