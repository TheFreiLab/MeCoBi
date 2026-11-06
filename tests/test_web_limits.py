"""Web layer: standards-compliant CSV parsing and public-API resource limits."""

import importlib

import pytest
from fastapi.testclient import TestClient
from mecobi.web import jobs

# The package re-exports the FastAPI *instance* as `mecobi.web.app`, so import the
# module explicitly to reach its helpers/constants (`appmod.app` is the instance).
appmod = importlib.import_module("mecobi.web.app")


@pytest.fixture
def client():
    # `with` runs the lifespan (populating app.state), then we install a
    # high-cap rate limiter so the validation tests below never trip the 429 path.
    with TestClient(appmod.app) as c:
        appmod.app.state.rate = jobs.RateLimiter(max_per_window=10_000)
        yield c


def _build_req(ligands, **over):
    req = {"name": "t", "metal": "Pt", "oxidation_state": 2, "geometry": "octahedral",
           "ligands": [{"smiles": s} for s in ligands], "relax": False}
    req.update(over)
    return req


# --------------------------------------------------------------------------- #
# #2 quoted-CSV parsing
# --------------------------------------------------------------------------- #

def test_read_csv_keeps_quoted_isomer_field():
    # exact example from QUICKSTART.md / README.md — the isomer cell has commas.
    text = ('Metal,Charge,L1,L2,L3,L4,isomer\n'
            'Ir,3,c1ccc(-c2ccccn2)nc1,c1ccc(-c2ccccn2)nc1,[Cl-],[Cl-],"0:0,2;1:3,5;2:1;3:4"\n')
    df = appmod._read_csv(text)
    assert df.iloc[0]["isomer"] == "0:0,2;1:3,5;2:1;3:4"


def test_parse_accepts_quoted_isomer_csv(client):
    text = ('Metal,Charge,L1,L2,L3,L4,isomer\n'
            'Ir,3,c1ccc(-c2ccccn2)nc1,c1ccc(-c2ccccn2)nc1,[Cl-],[Cl-],"0:0,2;1:3,5;2:1;3:4"\n')
    r = client.post("/api/parse", json={"csv": text})
    assert r.status_code == 200


def test_read_csv_ragged_and_headerless():
    df = appmod._read_csv("Pt,2,N,N,[Cl-],[Cl-]\nAu,1,[C-]#N,[C-]#N\n")
    assert df.shape == (2, 6)  # short row padded


# --------------------------------------------------------------------------- #
# #3 resource limits
# --------------------------------------------------------------------------- #

def test_csv_too_large_413(client, monkeypatch):
    monkeypatch.setattr(appmod, "MAX_CSV_BYTES", 10)
    r = client.post("/api/parse", json={"csv": "Pt,2,N,N,[Cl-],[Cl-]\n" * 5})
    assert r.status_code == 413


def test_body_too_large_413(client, monkeypatch):
    monkeypatch.setattr(appmod, "MAX_BODY_BYTES", 10)
    r = client.post("/api/parse", json={"csv": "Pt,2,N"})
    assert r.status_code == 413


def test_too_many_ligands_400(client):
    r = client.post("/api/build", json=_build_req(["N"] * 40))
    assert r.status_code == 400 and "ligand" in r.json()["detail"].lower()


def test_xtb_timeout_out_of_range_400(client):
    assert client.post("/api/build", json=_build_req(["N"], xtb_timeout_s=99999)).status_code == 400
    assert client.post("/api/build", json=_build_req(["N"], xtb_timeout_s=0)).status_code == 400


def test_smiles_too_long_400(client):
    r = client.post("/api/build", json=_build_req(["C" * (appmod.MAX_SMILES_LEN + 1)]))
    assert r.status_code == 400 and "long" in r.json()["detail"].lower()


def test_ligand_too_many_atoms_400(client):
    r = client.post("/api/build", json=_build_req(["C" * (appmod.MAX_ATOMS_PER_LIGAND + 1)]))
    assert r.status_code == 400 and "atoms" in r.json()["detail"].lower()


def test_reverse_export_too_many_items_400(client, monkeypatch):
    monkeypatch.setattr(appmod, "MAX_REVERSE_EXPORT_ITEMS", 1)
    items = [{"name": "a", "xyz": "1\n\nZn 0 0 0\n", "overall_charge": 0}] * 2
    r = client.post("/api/reverse/export", json={"items": items, "columns": ["trex"]})
    assert r.status_code == 400 and "items" in r.json()["detail"].lower()


def test_rate_limit_429_on_build(client):
    # First call consumes the single token (and 400s at validation without building);
    # the second is refused by the shared per-submitter limiter.
    appmod.app.state.rate = jobs.RateLimiter(max_per_window=1)
    big = _build_req(["N"] * 40)  # fails validation -> no assembly work
    assert client.post("/api/build", json=big).status_code == 400
    assert client.post("/api/build", json=big).status_code == 429


# --------------------------------------------------------------------------- #
# #8 isomer enumeration: unexpected failure must be distinguishable, not "count 1"
# --------------------------------------------------------------------------- #

def _isomer_req():
    return {"metal": "Fe", "oxidation_state": 2, "geometry": "octahedral",
            "ligands": [{"smiles": "N", "coord_atoms": [0]} for _ in range(6)]}


def test_isomer_unexpected_error_is_surfaced(client, monkeypatch):
    import mecobi.isomers as iso

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(iso, "enumerate_site_isomers", boom)
    r = client.post("/api/isomers", json=_isomer_req())
    assert r.status_code == 200
    body = r.json()
    assert body["error"] and "boom" in body["error"]  # not silently reported as 1


def test_isomer_not_enumerable_is_clean_single(client, monkeypatch):
    import mecobi.isomers as iso

    def not_supported(*a, **k):
        raise iso.StereoNotSupported("no site model")

    def unsupported_combo(*a, **k):
        raise KeyError("no registry entry")

    monkeypatch.setattr(iso, "enumerate_site_isomers", not_supported)
    monkeypatch.setattr(iso, "enumerate_isomers", unsupported_combo)
    body = client.post("/api/isomers", json=_isomer_req()).json()
    assert body["count"] == 1 and body["error"] is None
