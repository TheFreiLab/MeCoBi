"""Web layer tests: fast route checks + slow parse/build round-trip."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mecobi.web import app, jobs
# Direct name import: `mecobi.web.app` is rebound to the FastAPI instance by the
# package __init__, so importing the module under that name would shadow it.
from mecobi.web.app import RATE_MAX_PER_WINDOW, RATE_WINDOW_S

REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_CSV = Path(__file__).resolve().parent / "fixtures" / "test_compounds.csv"

client = TestClient(app)


# --------------------------------------------------------------------------- #
# fast
# --------------------------------------------------------------------------- #

def test_health_reports_queue_liveness():
    with TestClient(app) as c:  # run lifespan, so the queue worker actually exists
        r = c.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "worker": "alive"}


def test_health_is_503_when_the_queue_worker_is_dead():
    """The exact failure this endpoint exists to catch: the site serves, previews
    work, submissions are accepted — and nothing ever builds."""
    with TestClient(app) as c:
        app.state.worker.stop(join_timeout=5.0)
        r = c.get("/api/health")
        assert r.status_code == 503
        assert r.json() == {"status": "degraded", "worker": "dead"}
        assert c.get("/api/workload").json()["worker_alive"] is False


def test_whoami_reports_the_rate_limit_key_and_forwarded_header():
    # Deployment check for running behind a reverse proxy: it must report BOTH the address
    # the rate limiter keys on and the raw X-Forwarded-For, because the two together are
    # what distinguish "header absent" from "header present but not trusted" -- the silent
    # failure that collapses every user into one shared rate-limit bucket.
    d = client.get("/api/whoami").json()
    assert d["forwarded_for"] is None
    assert d["client"]                                   # some address, whatever the peer is
    assert d["rate_limit"] == {"max": RATE_MAX_PER_WINDOW, "window_s": RATE_WINDOW_S}

    # The raw header is echoed back so a misconfigured trust list is diagnosable. (uvicorn
    # rewrites the peer address from it in production; TestClient has no such middleware,
    # so here it only has to surface the header.)
    d = client.get("/api/whoami", headers={"X-Forwarded-For": "198.51.100.7, 203.0.113.9"}).json()
    assert d["forwarded_for"] == "198.51.100.7, 203.0.113.9"


def test_rate_limit_is_configurable_and_enforced():
    # The limit is env-tunable (MECOBI_RATE_MAX / MECOBI_RATE_WINDOW_S) so it can be
    # adjusted under real traffic without rebuilding the image.
    limiter = jobs.RateLimiter(2, 60.0)
    assert limiter.allow("1.2.3.4") and limiter.allow("1.2.3.4")
    assert not limiter.allow("1.2.3.4")          # third in the window is refused
    assert limiter.allow("5.6.7.8")              # a DIFFERENT submitter is unaffected


def test_parse_flags_garbage_csv_row():
    # 1 column -> not a complex. It comes back as a flagged row with a fixable message
    # (it used to 400 with "list index out of range" from the column layout).
    r = client.post("/api/parse", json={"csv": "x"})
    assert r.status_code == 200
    (row,) = r.json()
    assert row["supported"] is False
    assert row["error"].startswith("'x' is not an element symbol")


def test_file_route_404_for_missing():
    assert client.get("/api/file/nojob/none.xyz").status_code == 404


def test_depict_returns_atoms_and_bonds():
    r = client.get("/api/depict", params={"smiles": "c1ccc(-c2ccccn2)nc1"})
    assert r.status_code == 200
    d = r.json()
    assert len(d["atoms"]) == 12 and len(d["bonds"]) == 13
    nitrogens = [a["idx"] for a in d["atoms"] if a["symbol"] == "N"]
    assert nitrogens == [9, 10]  # bipyridine donor atoms


def test_depict_rejects_bad_smiles():
    assert client.get("/api/depict", params={"smiles": "not_a_smiles!!"}).status_code == 400


def test_depict_svg_is_csp_safe():
    # The ligand-library thumbnail: a real RDKit depiction, but with NO inline
    # style="" (a strict CSP strips those in the browser -> blank structures). Colours
    # must survive as SVG presentation attributes recoloured to currentColor.
    r = client.get("/api/depict_svg", params={"smiles": "c1ccc(-c2ccccn2)nc1"})
    assert r.status_code == 200
    svg = r.json()["svg"]
    assert svg.startswith("<svg")
    assert "style=" not in svg  # no inline styles for a CSP to block
    assert "stroke=" in svg and "currentColor" in svg  # colour as presentation attrs


def test_depict_svg_rejects_bad_smiles():
    assert client.get("/api/depict_svg", params={"smiles": "not_a_smiles!!"}).status_code == 400


def test_vertices_numbered_with_denticities():
    r = client.get("/api/vertices", params={"geometry": "octahedral", "denticities": "2,2,1,1"})
    assert r.status_code == 200
    d = r.json()
    assert d["n_sites"] == 6
    assert [(v["id"], v["denticity"]) for v in d["vertices"]] == [(0, 2), (1, 2), (2, 1), (3, 1)]
    # One donor-site position per denticity unit (the scene draws every site).
    assert [len(v["sites"]) for v in d["vertices"]] == [2, 2, 1, 1]


def test_vertices_unsupported_partition():
    r = client.get("/api/vertices", params={"geometry": "octahedral", "denticities": "1,1,1"})
    assert r.status_code == 422  # CN 3 has no topology


def test_sites_endpoint_octahedral():
    r = client.get("/api/sites", params={"geometry": "octahedral", "denticities": "2,2,1,1"})
    assert r.status_code == 200
    d = r.json()
    assert d["n_sites"] == 6 and len(d["sites"]) == 6
    assert [0, 2] in d["cis_pairs"] and [0, 1] not in d["cis_pairs"]  # cis not trans
    used = sorted(s for ss in d["default_assignment"].values() for s in ss)
    assert used == [0, 1, 2, 3, 4, 5]


def test_parse_headerless_single_row():
    # A bare pasted line must not be swallowed as the CSV header row.
    r = client.post("/api/parse", json={"csv": "Ir, 3, [Cl-], [Cl-], [Cl-]"})
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["metal"] == "Ir" and rows[0]["oxidation_state"] == 3
    assert len(rows[0]["ligands"]) == 3


def test_geometries_map():
    r = client.get("/api/geometries")
    assert r.status_code == 200
    d = r.json()
    assert d["2"] == ["linear", "bent"]
    assert d["4"] == ["square_planar", "tetrahedral"]
    assert d["6"] == ["octahedral"]


def test_parse_flags_radical_ligand():
    # [Cl] is a chlorine radical; the anion [Cl-] is clean. Both single-atom (fast).
    r = client.post("/api/parse", json={"csv": "Metal,Charge,L1,L2\nRu,2,[Cl],[Cl-]"})
    assert r.status_code == 200
    ligs = r.json()[0]["ligands"]
    assert ligs[0]["warning"] and "radical" in ligs[0]["warning"]
    assert ligs[1]["warning"] is None


def test_build_rejects_unknown_geometry():
    req = {
        "metal": "Pt", "oxidation_state": 2,
        "ligands": [{"smiles": "[Cl-]"}], "geometry": "cubic",
    }
    with TestClient(app) as c:  # run lifespan (rate-limiter state) for a build POST
        assert c.post("/api/build", json=req).status_code == 400


def test_parse_one_bad_row_does_not_abort_batch():
    # A single unparseable row (empty ligands) must NOT 400 the whole batch — it
    # comes back as a flagged, unbuildable row alongside the good complexes.
    csv = ("Metal,Charge,L1,L2\n"
           "Ru,2,[Cl-],[Cl-]\n"      # good (single-atom, fast)
           "Pt,2,,\n"                 # empty ligands -> flagged
           "Xx,2,[Cl-],[Cl-]\n")     # invalid metal -> flagged
    r = client.post("/api/parse", json={"csv": csv})
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 3
    assert rows[0]["supported"] is True
    assert rows[1]["supported"] is False and rows[1]["error"]
    assert rows[2]["supported"] is False and rows[2]["error"]


# --------------------------------------------------------------------------- #
# eta-cap centroid model (donor-override path) — fast route checks
# --------------------------------------------------------------------------- #

def test_perceive_exposes_pi_sites_for_caps():
    # A selected Cp ring = one centroid site (denticity 1), so ferrocene is a two-cap
    # sandwich (CN2) and the ring is reported as a pi_site (so the Assign scene can draw
    # it). The proposed geometry is METALLOCENE, not linear: it must match the builder's
    # own detect_metallocene so the spin model splits d-electrons on the sandwich field
    # (Fe(II) d6 -> diamagnetic uhf 0), consistent with the bent metallocene (Cp2MXn) case.
    cp = {"smiles": "[cH-]1cccc1", "coord_atoms": [0, 1, 2, 3, 4]}
    d = client.post("/api/perceive", json={
        "metal": "Fe", "oxidation_state": 2, "ligands": [cp, cp]}).json()
    assert d["coordination_number"] == 2
    assert [l["denticity"] for l in d["ligands"]] == [1, 1]
    assert d["ligands"][0]["pi_sites"] == [[0, 1, 2, 3, 4]]
    assert d["proposed_geometry"] == "metallocene"


def test_one_cap_row_is_labelled_a_piano_stool():
    # One centroid cap = a half sandwich, and its CN geometry describes it badly. Worst
    # case is cap + tridentate: only TWO ligands, which trips propose_geometry's "a <=2
    # ligand set is strongly chelating" rule and proposed SQUARE_PLANAR for an
    # (arene)Ru(terpy) piano stool. The label is now the piano stool; the CN geometries
    # stay listed so a placement geometry can still be pinned explicitly.
    # Donors pinned on both ligands so the row is deterministic (the override
    # short-circuits pydentate, whose terpy denticity is order-sensitive).
    cym = {"smiles": "CC1=CC=C(C(C)C)C=C1", "coord_atoms": [1, 2, 3, 4, 8, 9]}
    terpy = {"smiles": "c1ccnc(-c2cccc(-c3ccccn3)n2)c1", "coord_atoms": [3, 15, 16]}
    d = client.post("/api/perceive", json={
        "metal": "Ru", "oxidation_state": 2, "ligands": [cym, terpy]}).json()
    assert d["coordination_number"] == 4
    assert d["proposed_geometry"] == "piano_stool_arene"
    assert "square_planar" in d["geometry_options"]  # still offered, no longer the default


@pytest.mark.xfail(
    strict=True,
    reason="Automatic perception of multiple Cp rings within one ligand is "
    "an accepted limitation (audit point 4); the cap-selection guardrail "
    "does not reliably flag these inputs.",
)
def test_needs_cap_selection_guardrail():
    def flag(metal, ox, ligs):
        return client.post("/api/perceive", json={
            "metal": metal, "oxidation_state": ox,
            "ligands": [l if isinstance(l, dict) else {"smiles": l} for l in ligs],
        }).json()["needs_cap_selection"]

    # A SINGLE ligand with two Cp rings is under-coordinated by auto-perception -> flag.
    assert flag("Fe", 2, ["C1(CCCC2=CC=C[CH-]2)=C[CH-]C=C1"]) is True          # ansa
    assert flag("Zr", 4, ["C1(CC2=NC(CC3=CC=C[CH-]3)=CC=C2)=C[CH-]C=C1",
                          "[Cl-]", "[Cl-]"]) is True                            # Cp+pyridine
    # Ordinary metallocenes = SEPARATE single-ring Cp ligands -> NOT flagged (they
    # perceive correctly and build via the facial-triad metallocene path).
    assert flag("Ti", 4, ["[cH-]1cccc1", "[cH-]1cccc1", "[Cl-]", "[Cl-]"]) is False   # titanocene
    assert flag("Fe", 2, ["CN(C)Cc1cc[cH-]c1CNc2ccnc3cc(Cl)ccc23",
                          "[cH-]1cccc1"]) is False                             # ferroquine
    assert flag("Fe", 2, ["[cH-]1cccc1", "[cH-]1cccc1"]) is False             # ferrocene
    # And a two-Cp ligand clears once both rings are set as centroid caps.
    ansa = {"smiles": "C1(CCCC2=CC=C[CH-]2)=C[CH-]C=C1",
            "coord_atoms": [0, 4, 5, 6, 7, 8, 9, 10, 11, 12]}
    assert flag("Fe", 2, [ansa]) is False


def test_sites_cap_param_allows_denticity2_cap():
    # A CN2 chelate may span the two (trans) linear sites: a trans-spanning ligand on d10...
    r = client.get("/api/sites", params={"geometry": "linear", "denticities": "2"})
    assert r.status_code == 200 and r.json()["default_assignment"] == {"0": [0, 1]}
    # ...and a cap ligand (cap=0) places on any sites -> the same pair.
    r = client.get("/api/sites", params={
        "geometry": "linear", "denticities": "2", "cap": "0"})
    assert r.status_code == 200 and r.json()["default_assignment"] == {"0": [0, 1]}


# --------------------------------------------------------------------------- #
# slow (perception + build)
# --------------------------------------------------------------------------- #

@pytest.mark.slow
def test_build_remaps_metallocene_geometry_for_cap():
    # A stale/offline frontend can propose 'metallocene_bent' for a centroid-cap
    # complex; the build must remap to the CN geometry (site model) and succeed,
    # not KeyError on the facial-triad topology.
    cap = lambda: {"smiles": "[cH-]1cccc1", "coord_atoms": [0, 1, 2, 3, 4], "is_arene": True}
    cl = lambda: {"smiles": "[Cl-]", "coord_atoms": [0]}
    with TestClient(app) as c:  # run lifespan (rate-limiter state) for a build POST
        r = c.post("/api/build", json={
            "metal": "Ti", "oxidation_state": 4, "geometry": "metallocene_bent",
            "relax": False, "ligands": [cap(), cap(), cl(), cl()]})
    assert r.status_code == 200 and r.json()["results"]


@pytest.mark.slow
def test_cymantrene_parse_to_build_remaps_stale_octahedral_geometry():
    """A stale build geometry that no longer matches the post-perception CN is re-proposed.

    Parse represents the Cp as ONE centroid site (CN 4) and labels the row a piano stool.
    A geometry from an older row -- or the pre-centroid facial-Cp convention, which used to
    make this same complex octahedral (CN 6) -- must not put four centroid sites into an
    octahedron; ``build_complex`` re-proposes it instead of failing.
    """
    csv = (
        "Name,Metal,Charge,L1,L2,L3,L4\n"
        "CpMn(CO)3,Mn,1,[cH-]1cccc1,[C-]#[O+],[C-]#[O+],[C-]#[O+]\n"
    )
    with TestClient(app) as c:
        parsed = c.post("/api/parse", json={"csv": csv})
        assert parsed.status_code == 200
        row = parsed.json()[0]
        # Centroid convention: one cap site + three carbonyls, labelled a piano stool.
        assert row["coordination_number"] == 4
        assert row["proposed_geometry"] == "piano_stool_cp"

        built = c.post("/api/build", json={
            "name": row["name"],
            "metal": row["metal"],
            "oxidation_state": row["oxidation_state"],
            "geometry": "octahedral",   # stale: belongs to the old facial-Cp CN 6
            "relax": False,
            "ligands": [
                {
                    "smiles": ligand["smiles"],
                    "coord_atoms": ligand["coord_atoms"],
                    "is_arene": ligand["is_arene"],
                }
                for ligand in row["ligands"]
            ],
        })

    assert built.status_code == 200, built.text
    assert built.json()["results"]


@pytest.mark.slow
@pytest.mark.skipif(not PROTOTYPE_CSV.exists(), reason="legacy prototype folder not present")
def test_parse_prototype_csv():
    r = client.post("/api/parse", json={"csv": PROTOTYPE_CSV.read_text()})
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 24
    sq = next(x for x in rows if x["name"] == "Sq2b_Pt_1")
    assert sq["coordination_number"] == 4
    assert sq["geometry_options"] == ["square_planar", "tetrahedral"]
    assert sq["total_charge"] == 2


@pytest.mark.slow
def _fake_build_with_a_fused_isomer(cx, job_dir, **kwargs):
    """Stand-in for pipeline.build_complex: three relaxed isomers, the numerically
    lowest of which failed the connectivity check."""
    from mecobi import pipeline
    from mecobi.model import BuildResult

    Path(job_dir).mkdir(parents=True, exist_ok=True)  # the real build_complex creates it
    results = []
    for label, energy, ok in [("a", -10.00, True), ("fused", -12.00, False), ("b", -10.01, True)]:
        xyz = Path(job_dir) / f"{label}.xyz"
        xyz.write_text("1\n\nPt 0.0 0.0 0.0\n", encoding="utf-8")
        results.append(BuildResult(cx, label, str(xyz), [str(xyz)], total_energy=energy,
                                   connectivity_ok=ok))
    pipeline._rank_by_energy(results)
    return results


_PT_REQ = {
    "name": "cisplatin", "metal": "Pt", "oxidation_state": 2, "geometry": "square_planar",
    "ligands": [{"smiles": s} for s in ["N", "N", "[Cl-]", "[Cl-]"]], "relax": False,
}


def _assert_fused_isomer_reported_last(files):
    assert [f["isomer_label"] for f in files] == ["b", "a", "fused"]
    assert [f["connectivity_ok"] for f in files] == [True, True, False]
    assert [f["is_lowest_energy"] for f in files] == [True, False, False]
    assert files[2]["relative_energy_kcal"] is None and files[2]["total_energy"] == -12.0


def test_sync_build_reports_connectivity_and_never_ranks_a_broken_isomer(monkeypatch):
    from mecobi import pipeline

    monkeypatch.setattr(pipeline, "build_complex", _fake_build_with_a_fused_isomer)
    with TestClient(app) as c:  # run lifespan (rate-limiter state) for a build POST
        rb = c.post("/api/build", json=_PT_REQ)
    assert rb.status_code == 200, rb.text
    _assert_fused_isomer_reported_last(rb.json()["results"])


def test_queued_build_reports_connectivity_and_never_ranks_a_broken_isomer(monkeypatch, tmp_path):
    from mecobi import pipeline

    monkeypatch.setattr(pipeline, "build_complex", _fake_build_with_a_fused_isomer)
    results, errors = jobs.run_build({"relax": False, "complexes": [_PT_REQ]}, tmp_path)
    assert errors == []
    _assert_fused_isomer_reported_last(results)
    # The stored dicts round-trip through the response model the poll endpoint uses.
    from mecobi.web.app import BuiltFile
    assert [BuiltFile(**r).connectivity_ok for r in results] == [True, True, False]


def test_build_with_explicit_assignment():
    # Isomer defined via the 3D scene: two bidentate ligands -> vertices 0 and 1.
    req = {
        "name": "Sq2b_Pt_1", "metal": "Pt", "oxidation_state": 2,
        "ligands": [
            {"smiles": "c1ccc(-c2ccccn2)nc1", "coord_atoms": [9, 10]},
            {"smiles": "c1ccc(-c2ccccn2)nc1", "coord_atoms": [9, 10]},
        ],
        "geometry": "square_planar", "assignment": {"0": [0], "1": [1]}, "relax": False,
    }
    rb = client.post("/api/build", json=req)
    assert rb.status_code == 200
    f = rb.json()["results"][0]
    assert "custom" in f["name"] and f["total_charge"] == 2


@pytest.mark.slow
@pytest.mark.skipif(not PROTOTYPE_CSV.exists(), reason="legacy prototype folder not present")
def test_build_and_fetch_roundtrip():
    # Lifespan on: /api/build needs the rate limiter and /api/download the job store.
    with TestClient(app) as client:
        parse = client.post("/api/parse", json={"csv": PROTOTYPE_CSV.read_text()}).json()
        row = next(x for x in parse if x["name"] == "Sq2b_Pt_1")
        req = {
            "name": "Sq2b_Pt_1", "metal": row["metal"], "oxidation_state": row["oxidation_state"],
            "ligands": [
                {"smiles": l["smiles"], "coord_atoms": l["coord_atoms"], "is_arene": l["is_arene"]}
                for l in row["ligands"]
            ],
            "geometry": row["proposed_geometry"], "relax": False,
        }
        rb = client.post("/api/build", json=req)
        assert rb.status_code == 200
        res = rb.json()
        assert len(res["results"]) == 1
        f = res["results"][0]
        assert f["total_charge"] == 2 and f["uhf"] == 0
        rf = client.get(f"/api/file/{f['token']}")
        assert rf.status_code == 200
        assert int(rf.text.splitlines()[0]) == 41

        # Batch download: the job's structures come back as a zip of .xyz files.
        import io
        import zipfile

        rz = client.get(f"/api/download/{res['job_id']}")
        assert rz.status_code == 200
        assert rz.headers["content-type"] == "application/zip"
        with zipfile.ZipFile(io.BytesIO(rz.content)) as zf:
            assert any(n.endswith(".xyz") for n in zf.namelist())


def test_download_all_404_for_missing_job():
    assert client.get("/api/download/nosuchjob").status_code == 404


def test_reverse_endpoint_recovers_metal_and_ligands():
    xyz = "3\n\nZn 0 0 0\nCl 2.2 0 0\nCl -2.2 0 0\n"
    r = client.post("/api/reverse", json={"xyz": xyz})
    assert r.status_code == 200
    d = r.json()
    assert d["metal"] == "Zn" and d["coordination_number"] == 2
    assert [l["smiles"] for l in d["ligands"]] == ["[Cl-]", "[Cl-]"]


def test_reverse_endpoint_rejects_bad_input():
    assert client.post("/api/reverse", json={"xyz": "not an xyz"}).status_code == 400


def test_isomer_options_hint():
    # square-planar MA2B2 -> cis/trans, achiral (no Δ/Λ split).
    sp = client.post("/api/isomers", json={
        "metal": "Pt", "oxidation_state": 2, "geometry": "square_planar", "stereo": True,
        "ligands": [{"smiles": "N", "coord_atoms": [0]}, {"smiles": "N", "coord_atoms": [0]},
                    {"smiles": "[Cl-]", "coord_atoms": [0]}, {"smiles": "[Cl-]", "coord_atoms": [0]}],
    }).json()
    assert sp["count"] == 2 and "cis/trans" in sp["summary"] and sp["stereo_splits"] is False

    ma6 = client.post("/api/isomers", json={
        "metal": "Fe", "oxidation_state": 2, "geometry": "octahedral", "stereo": True,
        "ligands": [{"smiles": "N", "coord_atoms": [0]} for _ in range(6)],
    }).json()
    assert ma6["count"] == 1 and ma6["summary"] is None


def test_isomer_options_stereo_splits_flag():
    bipy = {"smiles": "c1ccc(-c2ccccn2)nc1", "coord_atoms": [9, 10]}
    # octahedral M(L)2X4 (monodentate L) has cis/trans but is achiral -> no Δ/Λ.
    achiral = client.post("/api/isomers", json={
        "metal": "Ru", "oxidation_state": 2, "geometry": "octahedral", "stereo": True,
        "ligands": [{"smiles": "N", "coord_atoms": [0]}, {"smiles": "N", "coord_atoms": [0]}]
                   + [{"smiles": "[Cl-]", "coord_atoms": [0]} for _ in range(4)],
    }).json()
    assert achiral["stereo_splits"] is False and "cis/trans" in achiral["summary"]
    # tris-chelate is chiral -> Δ/Λ split.
    chiral = client.post("/api/isomers", json={
        "metal": "Ru", "oxidation_state": 2, "geometry": "octahedral", "stereo": True,
        "ligands": [bipy, bipy, bipy],
    }).json()
    assert chiral["stereo_splits"] is True
