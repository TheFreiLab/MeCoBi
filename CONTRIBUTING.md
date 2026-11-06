# Contributing to MeCoBi

MeCoBi turns ligand SMILES into optimised 3D structures of the assembled metal complex:

`SMILES -> donor perception (pydentate) -> coordination number -> geometry -> isomer enumeration
-> stk assembly -> MCHammer -> xtb -> .xyz`

This guide is for anyone changing the code, people and coding agents alike. It is meant to be
complete on its own: you should not need any document that is not in the repository.

## Setup

MeCoBi supports Python 3.11, 3.12, 3.13 and 3.14. xtb (only needed for relaxation) is a compiled
binary from conda-forge.

```bash
conda create -n mecobi python=3.12
conda activate mecobi
conda install -c conda-forge xtb                 # optional: only for relaxation
pip install -e ".[web,dev]" -c constraints.txt   # the exact versions CI tests
```

`constraints.txt` is the reproducibility lock. Without it you get the newest compatible releases,
which usually work but can give slightly different structures (RDKit conformers change between
releases). Use the lock when you reproduce a result or a CI failure.

## Before you open a pull request

```bash
ruff check .                  # lint (configuration in pyproject.toml)
pytest -m "not slow"          # fast suite, about two minutes
pytest                        # full suite: also loads the ML models and runs xtb
```

CI runs ruff and the fast suite on Python 3.12 for every pull request, and on 3.11 to 3.14 for
every push to `main`. Pull requests that touch the frontend also check the committed bundle (see
below).

- Branch from `main` and open a pull request; `main` is protected.
- Keep a pull request to one change, and say in its description what changed and why.
- **Every behavioural change needs a regression test**, written so that it fails without the fix.
- Do not weaken a scientific test to make it pass on your machine. If a result depends on the
  platform or a library version, find out why, and document it.
- Match the surrounding code: naming, comment density, line length 100.

## Architecture rules

1. **The core package has no web dependencies.** All chemistry lives in `src/mecobi/` and runs
   locally; FastAPI and uvicorn are only imported under `src/mecobi/web/` (the `web` extra).
2. **One code path.** The CLI and the web app both call `mecobi.pipeline`. The web layer
   validates requests and orchestrates jobs; it contains no chemistry.
3. **The frontend ships as a committed build.** `frontend/` (React + Vite) builds into
   `src/mecobi/web/static/`. After changing the frontend, run `npm ci && npm run build` in
   `frontend/` and commit the regenerated bundle; never hand-edit the minified assets. CI rebuilds
   it and fails if the result differs, and `.gitattributes` keeps line endings identical across
   platforms so the build is byte-for-byte reproducible.

## Scientific invariants

Getting these wrong gives structures that look plausible and are wrong.

- **The oxidation state drives the geometry.** `geometry.propose_geometry` uses the d-electron
  count: CN4 d8 is square planar (otherwise tetrahedral); CN5 d8/d10 is trigonal bipyramidal
  (otherwise square pyramidal). Always pass a real oxidation state. Deriving it by charge balance
  from SMILES with the counter-ions stripped gives 0, which makes Ni/Pd/Pt(II) tetrahedral.
- **xtb always gets the charge and spin:** `--chrg` from the total charge and `--uhf` from the
  spin state. Never drop either. In the web API, `spin` accepts exactly `low` or `high`.
- **Coordination sites are numbered `0` to `CN-1` on fixed axes**, the same in the text isomer
  notation and the 3D assignment view (octahedral: 0=+x 1=-x 2=+y 3=-y 4=+z 5=-z; trans means the
  opposite site on the same axis). Site figures are generated from `SITE_VECTORS`, so they cannot
  drift from the code.
- **A relaxed structure whose bonding changed is flagged, not hidden.** If xtb fuses ligands,
  breaks a bond, collapses an atom onto the metal or unbinds a donor, the result has
  `connectivity_ok=False`, is never ranked as the lowest-energy isomer, and says why in its
  warnings.
- **M-L bond-length restraints** come from a table mined from crystal structures
  (`src/mecobi/data/ml_reference.json`). How it is built is in
  `docs/METHODS_bond_length_mining.md` and its sources in `DATA_PROVENANCE.md`. Change it only by
  re-running the miner, never by hand.
- **Scope:** d-block and main-group metals. Lanthanides and actinides are out of scope.

## Data

Do not commit crystal-structure files, raw database extracts or other third-party data; the
repository ships only derived, aggregated tables, described in `DATA_PROVENANCE.md`. Licences for
redistributed software are in `THIRD_PARTY_NOTICES.md`.
