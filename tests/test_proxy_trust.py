"""Exercise the actual uvicorn trust boundary used by the Docker entry point."""
from fastapi.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from mecobi.web.app import create_app
from mecobi.web.jobs import RateLimiter


def test_untrusted_forwarded_addresses_cannot_bypass_rate_limit():
    app = create_app()
    app.state.rate = RateLimiter(1, 60)
    client = TestClient(ProxyHeadersMiddleware(app, trusted_hosts=['127.0.0.1']),
                        client=('203.0.113.10', 1234))
    assert client.get('/api/whoami', headers={'X-Forwarded-For': '198.51.100.1'}).json()['client'] == '203.0.113.10'
    assert client.post('/api/jobs', json={'complexes': []},
                       headers={'X-Forwarded-For': '198.51.100.1'}).status_code == 400
    assert client.post('/api/jobs', json={'complexes': []},
                       headers={'X-Forwarded-For': '198.51.100.2'}).status_code == 429


def test_trusted_proxy_separates_clients_and_ignores_spoofed_prefix():
    app = create_app()
    app.state.rate = RateLimiter(1, 60)
    client = TestClient(ProxyHeadersMiddleware(app, trusted_hosts=['203.0.113.10']),
                        client=('203.0.113.10', 1234))
    headers = {'X-Forwarded-For': '192.0.2.99, 198.51.100.1'}
    assert client.get('/api/whoami', headers=headers).json()['client'] == '198.51.100.1'
    assert client.post('/api/jobs', json={'complexes': []}, headers=headers).status_code == 400
    assert client.post('/api/jobs', json={'complexes': []}, headers=headers).status_code == 429
    assert client.post('/api/jobs', json={'complexes': []},
                       headers={'X-Forwarded-For': '198.51.100.2'}).status_code == 400
