# MeCoBi structural benchmark — setup & run

MeCoBi builds 3D metal-complex structures from ligand SMILES (pydentate donor
perception → stk assembly → MCHammer → **xtb** relaxation, with a CSD-mined
metal–donor distance restraint). This benchmark rebuilds a frozen set of CSD
complexes and scores each build against the experimental crystal geometry.

## Layout

The **root** holds everything the studies share: the runner (`run.py`), the scoring library
(`metrics.py`, `ckmrmsd.py`, `dmae.py`, `donor_map.py`, `ckm_depth3.py`, `cif_geometry.py`,
`extract_cores.py`,
`crystal_assign.py`, `pre_xtb_report.py`), input fixes (`bench_overrides.py` +
`benchmark_overrides.json`; `hydrides.py` + `benchmark_hydrides.json`, see below), target extraction (`enrich_bundle_geometry.py`), small run utilities
(`aggregate.py`, `render_from_run.py`, `backfill_donor_indices.py`, `smoke_test.py`) and the
**frozen data** (`benchmark_bundle/spheres/cores.json.gz`, `benchmark_donors.json`,
`benchmark_targets.json`, `benchmark_geom_labels.json`). The scoring references are
`benchmark_spheres_elem.json.gz` / `benchmark_cores_elem.json.gz` (the default everywhere): the
crystal donors chosen by the bundle's declared donor elements
(`dataprep/extract_spheres_by_element.py`), since the original nearest-atom spheres let a
backbone atom stand in for a lost I/Cl/H donor in ~3.5% of complexes and predate the
donor-element corrections; refcodes whose CIF lacks a declared donor near the metal keep the
old sphere (`"by_element": false`). Always run `run.py` from here; its
`--refcodes / --targets / --out-dir` paths are relative to this folder.

**CSD coordinates are not distributed.** The crystal spheres and cores
(`benchmark_spheres*.json.gz`, `benchmark_cores*.json.gz`) and the located hydrides
(`benchmark_hydrides.json`) are atomic coordinates from the Cambridge Structural Database, so
the public repository does not include them. With a CSD licence, regenerate them from the CIFs
of the refcodes in `benchmark_bundle.json.gz`: `dataprep/extract_spheres_by_element.py`
(spheres and depth-2 cores), `dataprep/extract_cores_dk.py` (depth-3 cores) and
`dataprep/scan_hydrides.py` + `dataprep/build_hydride_corrections.py` (hydrides), with `--cif-root` or `MECOBI_CIF_ROOT` pointing
at a folder with one sub-folder of CIFs per metal. The tests that need these files skip
without them.

| Folder | Study | Start with |
|---|---|---|
| `full30k/` | the full ~30k CSD benchmark (MeCoBi only): driver, metrics, stratification, summary CSVs | `full30k/run_full30k.sh` |
| `pilot100/` | the frozen 100-complex pilots (`pilot_100.json` = pilot 1, `pilot_2.json`) + their crystal targets and the **4-tool comparison** | `pilot100/compare_tools.py` |
| `pilot100/mecobi/` | MeCoBi pilot runs (`mecobi_det`, `mecobi_det2`, built by the root `run.py`) + `progress.py` | |
| `pilot100/architector/` · `molsimplify/` · `metallogen/` | one runner (+ summary) per competing tool; each writes its results next to itself | `*_run.py` |
| `pilots10/` | the 10×100 stratified pilots (run-to-run variance) | `pilots10/README.md` |
| `top100/` | A/B of build flags on the 100 largest complexes | `top100/run_top100.sh` |
| `dataprep/` | how the frozen bundle / donors / spheres were produced (provenance; not needed to run) | |

Scripts inside a study folder find the shared library and the frozen data through the root
(`BENCH = <script dir>.parent`), so they can be run from anywhere, e.g.
`python pilot100/pilot_metrics.py`. Results, run dirs and big CSVs stay untracked (see
`.gitignore`).

## Metrics

Every tool's build is scored by the same code: `run.score` (sphere metrics) + `ckmrmsd.py` +
`dmae.py`, called per structure by `pilot100/compare_tools.py`. The library's self-consistency
(a structure vs itself, rotated / mirrored / shuffled, scores 0; exact minima) is tested in
`tests/test_benchmark_metrics.py` and `tests/test_benchmark_donors_dmae.py`.

| column | what it measures | where | caveat |
|---|---|---|---|
| `cn_detected`, `cn_match` | atoms bonded to the metal (Cordero radii + 0.4 Å, lengthened per metal–donor pair to the crystal 99th percentile, `benchmark_ml_cutoffs.json`); match = exactly the crystal CN and every scored donor bonded | `donor_map.py` | — |
| `donor_source` | the build's donors are found on its molecular graph (ligand fragments matched to the input SMILES, donor atoms from `benchmark_donors.json`); `nearest` = fallback to the cn nearest atoms | `donor_map.py` | — |
| `shape_match` | crystal and build nearest the same ideal polyhedron (`None` where the CN has no ideal) | `metrics.best_shape` | CN 2, 3, 6, 7, 9 have one candidate only, so a match is automatic |
| `poly_cshm` | CShM of the build polyhedron vs the crystal polyhedron (reflections allowed) | `metrics.shape_deviation` | angular variant (unit vectors, no metal vertex): not SHAPE values |
| `exp_cshm`, `build_cshm` | CShM vs the nearest ideal (SHAPE SPY-5 / SAPR-8 ideals); exact over all permutations for CN ≤ 8 | `metrics.continuous_shape_measure` | as above |
| `dmat_rmsd` | RMSD of the donor–donor distance matrix, optimal pairing (exact for CN ≤ 8) | `metrics.local_distance_matrix_rmsd` | MeCoBi's own metric |
| `bond_rmsd` | M–L bond-length RMSD over sorted lengths, heavy donors | `metrics.bond_rmsd` | lower bound (ignores which donor is which) |
| `ckmrmsd` | Architector's core kmRMSD: metal + donors + their heavy neighbours, element-wise Hungarian + Kabsch, 300 random starts + mirror | `ckmrmsd.py` | H dropped, core found by distance, partial match on composition mismatch (`ckm_n_matched` vs `ckm_core_n`) |
| `dmae3` | MetalloGen's D-MAE₃: mean \|Δd\| over all pairs of the metal and heavy atoms within 3 bonds | `dmae.py` (crystal cores: `dataprep/extract_cores_dk.py`) | vs the raw crystal (the paper uses the xtb-reoptimised CSD structure), heavy atoms only (the paper keeps H), geometric atom correspondence |

Angular metrics run on haptic-collapsed spheres (an η-ring is one site); located hydrides count
as sites (see *Hydride corrections*).

## 1. Prerequisites
- Python ≥ 3.10, git
- conda / mamba (only needed for the compiled **xtb** binary)
- a few GB of scratch disk; more cores = faster (the run parallelises trivially)

## 2. Install
```bash
git clone https://github.com/TheFreiLab/MeCoBi.git   # benchmark is on the default branch (main)
cd MeCoBi
python -m venv .venv && source .venv/bin/activate     # or a conda env
pip install -e .
conda install -c conda-forge xtb                       # the only non-pip dependency
xtb --version                                          # confirm it's on PATH
```
All Python deps (rdkit, stk, stko, MCHammer, torch for pydentate) come from
`pip install -e .`. The CSD distance table ships inside the package
(`src/mecobi/data/ml_reference.json`) — nothing else to download for the build.

## 3. Trial FIRST (~1 minute)
```bash
python experiments/benchmark/smoke_test.py
```
Expect `5/5 built. Environment OK` with a per-complex wall-time (≈1–13 s each).
If any line says **FAIL**, the message tells you what's missing — almost always
xtb not on PATH, or a torch/rdkit install issue. Fix that before the full run.

## 4. Full benchmark run
The benchmark ships two frozen, versioned files here:
- `benchmark_bundle.json.gz` — **35,956 CSD complexes** (metal, oxidation state,
  ligand SMILES) = **35,756 build targets** (CN 2–9) + **200 CN≥10 negative
  controls** (which MeCoBi must reject cleanly). Stratified across CN, oxidation
  state (windowed to −4…+8), and 50 metals. Inputs come from a **charge-corrected
  CSD ligand extraction** (`ligand_charge_fix.py`: per-donor X/L-type charge
  perception over the CSD Generation-3 structures), with data-quality guards
  (flat-nitrate repair, eta-carbocycle charge normalisation so Cp/arene/allyl
  ligands get the correct total charge rather than -1 per metal-bonded carbon,
  embedded-alkali-metal removal, an OS sanity window, and dropping ligands whose
  bond orders were lost in the source SMILES). DART's MetaLig was used
  only as an independent cross-check (~77 % CN agreement; it systematically drops
  ligands for ~1/4 of complexes, which this bundle fixes). See
  `dataprep/build_bundle_from_mecobi.py` for provenance.
- `benchmark_spheres.json.gz` — the experimental coordination sphere (metal +
  donor positions) for each refcode, from the CSD crystal structures (not distributed;
  regenerate as described above).

`run.py` builds each complex with MeCoBi from these inputs, xtb-relaxes it,
and scores the relaxed sphere against the crystal: coordination-number match,
coordination-geometry shape match, continuous shape measure (CShM), donor–donor
distance-matrix RMSD, and metal–donor bond RMSD. It is **shardable + resumable**:

```bash
# quick end-to-end check first (~a few min):
python experiments/benchmark/run.py --shard 0/300 --spheres benchmark_spheres.json.gz

# full run, split across cores/nodes (e.g. 32 shards):
for i in $(seq 0 31); do
  python experiments/benchmark/run.py --shard $i/32 --spheres benchmark_spheres.json.gz &
done; wait
python experiments/benchmark/aggregate.py     # -> benchmark_results.csv + stratified summary
```
Each shard appends to `_results_shard<i>of<N>.jsonl` and resumes where it left off.

### Hydride corrections (opt-in)
The mined ligand SMILES carry **no hydrides**, so a hydrido complex enters with its CN too low
and its oxidation state one unit too low per lost H⁻ (Ni(II)–H mines as Ni(I)).
`dataprep/scan_hydrides.py` flags them (an H within 2.0 Å of the metal bonded to nothing else =
*located*; a low-side odd oxidation state without a located H = *suspected*), and
`dataprep/build_hydride_corrections.py` turns the located ones into `benchmark_hydrides.json`:
per refcode the M→H vectors from the CIF, the corrected OS/CN, and the geometry + site-map target
re-read from the crystal **with** the hydride as a donor. The frozen bundle is not touched;
`hydrides.py` layers the correction on top:

```bash
python run.py --hydrides benchmark_hydrides.json ...             # or run_pilot100.py --hydrides ...
python pilot100/compare_tools.py --hydrides benchmark_hydrides.json
```
With `--hydrides`, a corrected complex is built with one `[H-]` ligand per hydride on the site it
has in the crystal and scored against the crystal sphere including the H (shape / poly / dmat /
c-kmRMSD count it as a site; the bond RMSD stays on the heavy donors, X-ray M–H being
systematically short). Only the `clean` class (1–2 hydrides, site CN ≤ 6) is applied by default;
`--hydride-classes` widens it. *Suspected* complexes are not corrected (nobody knows how many H
or where) — report them as a subgroup.

### Tuning
- `MECOBI_XTB_THREADS=1` (default) gives one core per build so N parallel builds
  don't oversubscribe. Raise it only when running a few large complexes.
- `--xtb-timeout 180` caps a runaway relaxation (seconds).
- **Sizing:** ~5–15 s/complex → 36k ≈ `36000 × 10 s / cores`: ~3–4 h on 32 cores,
  ~14 h on 8. Run a `--shard 0/300` slice first to confirm output.
