# Third-party notices

MeCoBi is distributed under the MIT licence: see [`LICENSE`](LICENSE),
Copyright (c) 2026 The Frei Lab. Citation metadata is in
[`CITATION.cff`](CITATION.cff).

This file lists third-party material, separated by how it reaches the user,
because the obligations differ. Code we copy into this repository or into the
container is redistributed by us. Code that pip or conda fetches at install time
is not.

## 1. Code vendored in this repository

These files are committed here and ship inside the wheel or the served bundle,
so their licence terms travel with every copy of MeCoBi.

### pydentate (ligand perception)

- Licence: MIT, Copyright (c) 2024 Kulik Group.
- Location: `src/mecobi/_pydentate/`, with the upstream licence preserved at
  `src/mecobi/_pydentate/LICENSE` and packaged via `pyproject.toml`.
- Includes trained model weights: `src/mecobi/_pydentate/models/*.pt`.
- Upstream: https://github.com/hjkgrp/pydentate
- Please cite:
  - *Graph Neural Networks for Predicting Metal-Ligand Coordination of
    Transition Metal Complexes*, PNAS, https://doi.org/10.1073/pnas.2415658122
  - *Identifying Dynamic Metal-Ligand Coordination Modes with Ensemble
    Learning*, JACS, https://doi.org/10.1021/jacs.5c17169

### 3Dmol.js (3D structure viewer)

- Licence: BSD-3-Clause, David Koes and contributors.
- Version: 2.5.5, pinned exactly in `frontend/package.json` with a lockfile
  integrity hash.
- Location: served from `src/mecobi/web/static/vendor/3Dmol-min.js`, with the
  upstream notice alongside it as `3Dmol-min.js.LICENSE.txt`. The copy is staged
  out of `node_modules` at build time by `frontend/scripts/vendor-3dmol.mjs`.
- Upstream: https://github.com/3dmol/3Dmol.js

### Lucide (UI icons)

- Licence: ISC. Copyright (c) for portions of Lucide are held by Cole Bemis
  2013-2022 as part of Feather (MIT). All other copyright (c) for Lucide are held
  by Lucide Contributors 2022.
- Version: 0.460.0 (`lucide-static`). Only the path data of two icons is used:
  `flask-conical` (Ligand library button) and `timer` (build timer).
- Location: inlined in `frontend/src/components/Icon.jsx`, which carries the
  notice, and from there in the served bundle.
- Upstream: https://github.com/lucide-icons/lucide

### MetalloGen coordination-site table (m-SMILES export)

- Licence: BSD-3-Clause, Copyright (c) 2025, KyunghoonLee.
- Only data is used: the ideal site vectors and the per-CN geometry list
  (`known_geometries_vector_dict` / `CN_known_geometries_dict` from
  `MetalloGen/globalvars.py`, commit fa26e2a), which define the m-SMILES geometry
  tokens and site numbers.
- Location: `src/mecobi/msmiles.py`, whose docstring carries the full licence text.
- Upstream: https://github.com/kyunghoonlee777/MetalloGen
- Please cite: K. Lee, S. Park, M. Park & W. Y. Kim, *MetalloGen: Automated 3D
  Conformer Generation for Diverse Coordination Complexes*, J. Chem. Inf. Model.
  2025, 65, 11878–11891.

## 2. Binaries redistributed in the Docker image

### xtb (semi-empirical QM engine)

- Licence: LGPL-3.0.
- Version 6.7.1, installed from conda-forge inside the production image
  (`Dockerfile`, `ARG XTB_VERSION`). MeCoBi itself does not bundle xtb; a source
  or wheel install expects the user to provide it.
- MeCoBi invokes xtb as a separate process (`subprocess.run` in
  `src/mecobi/optimize.py`) and never links against it, so its LGPL terms impose
  no condition on MeCoBi's own source licence. The distinction matters only for
  the container, which does redistribute the binary and therefore must carry
  xtb's licence text and permit the library to be replaced. The image copies every
  conda package's licence text into `$MAMBA_ROOT_PREFIX/share/licenses` before
  `micromamba clean` deletes the package cache, and CI asserts that xtb's
  `COPYING.LESSER` is present in the built image.
- Upstream: https://github.com/grimme-lab/xtb

## 3. Runtime dependencies (installed, not redistributed)

Resolved by pip or conda at install time. Listed for review convenience; the
authoritative licence is whatever each project ships.

| Package | Licence |
|---|---|
| rdkit | BSD-3-Clause |
| torch | BSD-3-Clause |
| numpy, pandas | BSD |
| tqdm | MPL-2.0 AND MIT |
| fastapi, pydantic | MIT |
| uvicorn | BSD-3-Clause |
| stk | MIT |
| stko | MIT |
| MCHammer | MIT |

Note: stk, stko and MCHammer declare no licence in their PyPI metadata. The MIT
entries above were read from the `LICENSE` file in each upstream repository
(lukasturcani/stk, JelfsMaterialsGroup/stko, andrewtarzia/MCHammer), which is the
authoritative source.

Optional `reverse-tm` extra, imported lazily and not vendored. The production image
installs both, built as wheels from pinned commits (`Dockerfile`, `XYZ2MOL_TM_SHA` /
`TREX_SHA`); each wheel keeps its licence in its `*.dist-info/licenses/`, and the
xyz2mol_tm wheel's `ML` package carries its own MIT notice (`ML/LICENSE_tmQMg_ML`).

| Package | Licence |
|---|---|
| xyz2mol_tm (Rasmussen et al.) | MIT |
| trex-notation | MIT |

## 4. Data

The bundled metal-donor bond-length reference table
(`src/mecobi/data/ml_reference.json`) is derived from the Cambridge Structural
Database. It contains aggregate statistics only, not database records. See
[`DATA_PROVENANCE.md`](DATA_PROVENANCE.md) for what it holds, how it was built,
and the CCDC review that cleared its release.
