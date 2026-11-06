"""Cached donor indices must always refer to the caller's SMILES atom order."""

import concurrent.futures
import multiprocessing

import pytest
from rdkit import Chem

from mecobi import perception
from mecobi.model import Ligand


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch):
    monkeypatch.setattr(perception, "_PYDENTATE_CACHE", {})


@pytest.mark.parametrize("smiles", [
    ("n1ccccc1", "c1ccncc1"),
    ("c1ccncc1", "n1ccccc1"),
])
@pytest.mark.parametrize("mode", ["lazy", "serial", "parallel"])
def test_cache_preserves_donor_indices_and_probabilities(monkeypatch, smiles, mode):
    calls = []

    def infer(s):
        calls.append(s)
        mol = Chem.MolFromSmiles(s)
        donors = [a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == "N"]
        probs = [0.99 if a.GetSymbol() == "N" else 0.01 for a in mol.GetAtoms()]
        return 1, donors, probs

    monkeypatch.setattr(perception, "_compute_pydentate", infer)
    if mode == "parallel":
        # Exercise the pool dispatch/result-association path on Windows too,
        # without launching fork workers or loading torch in subprocesses.
        class InlinePool:
            def __init__(self, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def map(self, fn, values, **kwargs):
                return map(fn, values)

        monkeypatch.setattr(concurrent.futures, "ProcessPoolExecutor", InlinePool)
        monkeypatch.setattr(multiprocessing, "get_context", lambda method: None)
        monkeypatch.setattr(perception, "_resolve_perception_workers", lambda workers, n: 2)

    if mode != "lazy":
        perception.prewarm_pydentate([*smiles, *smiles], workers=1 if mode == "serial" else 2)

    for s in [*smiles, *smiles]:
        mol = Chem.MolFromSmiles(s)
        n, donors, probs = perception._run_pydentate(s)
        assert n == 1
        assert donors == [a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == "N"]
        assert probs == [0.99 if a.GetSymbol() == "N" else 0.01 for a in mol.GetAtoms()]
        lig = perception.perceive(Ligand(s))
        assert lig.coord_atoms == donors

    # Repeated strings still reuse their own predictions, including a second prewarm.
    perception.prewarm_pydentate(smiles, workers=1)
    assert calls == list(smiles)


@pytest.mark.slow
@pytest.mark.parametrize("smiles", [
    ("n1ccccc1", "c1ccncc1"),
    ("c1ccncc1", "n1ccccc1"),
])
def test_csv_parse_keeps_equivalent_pyridines_n_bound(smiles):
    from fastapi.testclient import TestClient

    from mecobi.web.app import create_app

    client = TestClient(create_app())
    csv = "Name,Metal,Charge,L1,L2,L3,L4\n" + "\n".join(
        f"row{i},Pt,2,{s},{s},[Cl-],[Cl-]" for i, s in enumerate(smiles)
    )
    # Batch prewarming, then a separate request sharing the populated cache.
    for _ in range(2):
        response = client.post("/api/parse", json={"csv": csv})
        assert response.status_code == 200
        for row in response.json():
            assert row["supported"]
            assert row["coordination_number"] == 4
            for ligand in row["ligands"][:2]:
                mol = Chem.MolFromSmiles(ligand["smiles"])
                assert ligand["coord_atoms"] == [
                    atom.GetIdx() for atom in mol.GetAtoms() if atom.GetSymbol() == "N"
                ]
