# 10×100 stratified benchmark

Ten disjoint validation pilots of 100 complexes each, stratified by **(coordination number, crystal
geometry)** to mirror the natural distribution of the eligible benchmark pool. Running the *same*
representative sample ten times turns the spread across pilots into a direct estimate of the
benchmark's **run-to-run variance** — the average/median metrics plus how stable they are.

## Files

| File | What it does | Needs |
|------|--------------|-------|
| `make_pilots10.py` | picks the 10×100 refcodes, stratified + disjoint from pilot_1/pilot_2 | numpy/scipy only (no xtb/torch) |
| `run_pilots10.sh` | builds each pilot into `pilots10/run_rNN/` using the committed targets | xtb + pydentate (Keisan) |
| `pilots10_metrics.py` | per-pilot mean/median + by-CN / by-geometry distributions + across-pilot spread | numpy/scipy only |

**No CIFs on the compute host.** The only step that reads the (heavy, local-only) CCDC CIF tree is
extracting the crystal geometry+site-map **targets**; that is done ONCE on the machine that has the
CIFs and the small `pilots10/targets.json` is committed. Everything the build + scoring needs
(`benchmark_bundle/spheres/cores/donors`, the pilot lists, the targets) is already in the repo, so
Keisan only needs to clone + run.

Outputs live under `pilots10/`: `pilot_rNN.json` (the picks), `run_rNN/` (built structures +
`_results_shard*.jsonl`), `pilot_rNN_metrics.csv` (per-structure), `summary.csv` (one row per
pilot), `summary_pooled.csv` (by CN and by geometry over all 1000).

## Run it

```bash
# 1. pick the pilots (once, any machine; no xtb/torch) -- writes pilots10/pilot_r01..r10.json
python pilots10/make_pilots10.py

# 1b. extract crystal targets ONCE where the CIFs live (no torch needed with --no-build-check);
#     commit pilots10/targets.json so the compute host never touches a CIF
python enrich_bundle_geometry.py --refcodes pilots10/all_1000.json \
    --donors benchmark_donors.json --cif-root /path/to/CCDC \
    --out pilots10/targets.json --no-build-check

# 2. build all ten on Keisan (xtb + pydentate). Arg: [parallel shards]
./pilots10/run_pilots10.sh 8

# 3. score
python pilots10/pilots10_metrics.py
```

`--no-build-check` skips the assembly verification (which needs pydentate/torch) so the extraction
runs on a CIF-only machine; a site-map that turns out unbuildable simply falls back to the geometry's
default isomer inside `run.py`, so nothing breaks.

## Stratification

`make_pilots10.py` labels every eligible refcode with its crystal geometry from the coordination
**sphere** (`metrics.best_shape`, pure geometry). CN 2/3/6/7/9 have a unique ideal shape, so their
stratum is just the CN; **CN 4/5/8 split** (square-planar↔tetrahedral, tbp↔square-pyramidal,
antiprism↔dodecahedron), which is where a representative geometry mix matters. Labels are cached in
`benchmark_geom_labels.json` (the first run computes CShM for ~15k CN-4/5/8 complexes, a few
minutes; later runs are instant). The 1000 refcodes are allocated across strata by pool frequency
(largest-remainder), then dealt round-robin so **each pilot is individually representative** and all
ten are disjoint. Eligible = has ground-truth donors + a crystal sphere, non-lanthanide (GFN2 handles
the f-block poorly), and not already in pilot_1/pilot_2. Seed fixed (`--seed 10`) → reproducible.

## Metrics

Per structure: build success, connectivity-ok, shape-class match, `poly_cshm` (angles vs the crystal
polyhedron), `dmat_rmsd` (donor–donor distance matrix), `bond_rmsd` (M–L lengths), and a freshly
computed depth-2 `ckmrmsd` (core Kuhn-Munkres+Kabsch vs the crystal core). Per pilot: the rates plus
**mean and median** of each continuous metric; then the same broken down by CN and by geometry. The
console also prints each headline metric as `mean ± sd` across the ten pilots.
