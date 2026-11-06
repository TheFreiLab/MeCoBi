# Experimental: CSD-derived metal–donor bond-length reference with convergence-based early stopping

*Draft methods section for the MeCoBi validation manuscript. Code:
`tmp_cifreview_fixed/mine_bond_lengths.py` (miner) and `plot_convergence.py`
(convergence figures). Consumed by `src/mecobi/.../csd_restraint.py`.*

> **October 2026 rebuild.** The shipped table is no longer the output of the early-stopped miner
> described below. It was re-mined from every structure, with consensus oxidation states and
> separate carbon classes; see [Full rebuild](#full-rebuild-october-2026). The sections in
> between describe the first version, which still supplies the f-block bins.

## Rationale

MeCoBi assembles complexes with generic metal–ligand target distances (Cordero
covalent-radius sums applied during the `stk`/MCHammer stage), which leave
metal–donor (M–L) bonds systematically **≈0.13 Å too long** (median bond RMSD
0.21 Å over a 40-complex A/B set). To remove this bias we restrain each M–L bond
during optimisation toward an **experimental average** taken from the Cambridge
Structural Database (CSD), rather than toward a covalent-radius estimate. This
section describes how that reference table of average M–L distances is built.

## Data source

Mononuclear metal-complex CIFs from the CombChemML *Generation-3* collection
(CSD-derived): 311,289 structures across 50 metal elements, one metal per
structure. For each structure we use the crystallographer-deposited
`_geom_bond` loop, taking the bonded-atom labels
(`_geom_bond_atom_site_label_1/2`), the reported distance
(`_geom_bond_distance`, e.s.d. stripped), and the element assignment from the
`_atom_site_type_symbol` loop. Using the deposited bond list means the
coordination sphere is defined by the original crystallographers; we impose no
covalent-radius cutoff and perform no symmetry expansion of our own
(symmetry-generated M–L bonds are retained, as their lengths are physically
valid). Metal–hydrogen contacts are excluded.

Formal oxidation states are read from the curated `FilteredOS` table
(`Extracted_Symbols`, e.g. `+2`); structures whose entry carries only an
unsigned charge are treated as oxidation-state-unknown and contribute solely to
the oxidation-state-independent bins (below).

## Hierarchical binning

Every M–L observation `(metal M, oxidation state q, donor element D,
coordination number CN, distance d)` updates three nested accumulators:

| Level | Key | Purpose |
|-------|-----|---------|
| fine | `(M, q, D, CN)` | most specific restraint target |
| marginal | `(M, q, D)` | fallback when the fine bin is thin |
| coarse | `(M, D)` | oxidation/CN-independent fallback |

At restraint time (`ml_target`) the most specific bin with at least `n_min`
samples is used, falling back through the hierarchy. CN is taken as the number
of non-hydrogen `_geom_bond` contacts to the metal in that structure, so the
same donor element is separated by coordination environment — e.g. mined
Ni(II)–N averages **2.095 Å at CN 6** (octahedral) versus **1.933 Å at CN 4**
(square planar), reproducing the expected square-planar bond contraction.

## Online estimation

Each bin maintains a running count *n*, mean, and sum-of-squares via Welford's
single-pass algorithm, so no per-bond samples are stored. Bin quality is
summarised by the standard error of the mean

    SEM = s / √n,   s = sample standard deviation,

which is the reported uncertainty on each tabulated average. A bin is
**settled** when `n ≥ n_min` and `SEM < tol` (defaults `n_min = 25`,
`tol = 0.01 Å`). Because SEM ∝ 1/√n and intra-bin M–L spreads are ~0.03–0.10 Å,
25–100 samples suffice to fix a bin mean to ±0.01–0.02 Å; exhaustively reading
all 311k CIFs is unnecessary.

## Convergence-based early stopping

CIFs are processed in refcode (alphabetical) order, which is uncorrelated with
molecular geometry, so streaming and stopping early introduces no bias. After
each processed complex the miner evaluates a convergence ("loss") signal per
metal: the maximum drift of any populated coarse-bin mean over a sliding window
of the last `patience` complexes,

    drift = max over coarse bins with n ≥ n_min of | mean_now − mean_(−patience) |.

Mining of a metal folder halts when **all three** hold:

1. at least one coarse bin is populated (`n ≥ n_min`);
2. `drift < delta` across the whole window (defaults `delta = 0.005 Å`,
   `patience = 100`); and
3. no new fine `(M, q, D, CN)` bin has appeared for a full `patience` window
   (guarding against stopping while rare environments are still being
   discovered).

A hard cap (`max_complexes`) is available as a safety stop. The stop reason
(`converged` / `max_complexes` / `exhausted`) is recorded per metal.

This is early stopping by *patience* on a plateau, directly analogous to
validation-loss early stopping in model training: reading continues only while
additional structures still move the estimates.

## Practical execution notes

* **OneDrive files-on-demand.** The corpus is cloud-backed; reading a
  not-yet-downloaded placeholder triggers a ~1 s hydration. The miner detects
  placeholders via the Windows `OFFLINE` / `RECALL_ON_DATA_ACCESS` file
  attributes and **skips** them, so it never drives slow per-file downloads. It
  is resumable (processed refcodes are journalled to `mine_state.json`) and
  writes outputs incrementally after each metal, so it can be re-run repeatedly
  as the local mirror fills.
* **Outputs.** `ml_reference.json` (the three-level table, each entry
  `{mean, n, sd, sem}`); `convergence_trace.json` (per-complex `(n, mean, SEM)`
  history for every coarse bin); `mine_state.json` (resume journal + per-metal
  stop reasons).

## Validation (illustrative: nickel)

Run on the locally mirrored nickel subset, the miner **converged after 675
complexes** (9.9 s), the coarse means having stayed flat for 100 consecutive
complexes. Mined coarse averages follow the expected donor ordering —
Ni–F 1.851 < Ni–N 2.013 < Ni–O 2.039 < Ni–P 2.186 ≈ Ni–S 2.192 < Ni–Cl 2.258 <
Ni–Br 2.378 < Ni–I 2.571 Å — with SEM ≤ 0.006 Å on all well-populated bins
(N, O, S, P, C). Figure `figs/convergence_Ni.png`: (left) running means settling
with ±SEM bands; (right) SEM decay crossing the tolerance for common donors
while rare halide bins (Br, I) remain above tolerance and would continue to
accrue samples. `figs/convergence_overview.png` overlays the s/√n SEM decay for
all bins.

Applied as restraint targets (`csd_restraint.py`) on an independent 40-complex
A/B test, the mined distances cut the median M–L offset versus experiment from
+0.122 to +0.018 Å and the median per-bond RMSD from 0.213 to 0.090 Å
(28/36 complexes improved).

## Full rebuild (October 2026)

Code: `experiments/benchmark/dataprep/mine_ml_reference.py`; table comparison:
`experiments/benchmark/dataprep/compare_ml_tables.py`.

**Why.** The first table was assembled from a run stopped early. Whole metal–donor pairs were
missing (no Zr–N, Zr–O, Zr–Cl; no Sn–Cl), so those bonds fell back to covalent-radius sums
0.25–0.35 Å too long: in the 30k benchmark Zr had a median bond RMSD of 0.32 Å. Its oxidation
states were the metal charge written in the CSD SMILES, which is not an oxidation state when
ligands are drawn covalently ([ZrF6]2- gave Zr(−II) bins).

**What changed.**

* *Every structure is read*, with no early stop, for the 36 non-f-block metals. The three-level
  binning and the CN definition (non-H `_geom_bond` contacts of the metal) are unchanged.
* *Consensus oxidation state.* The metal's formal charge in the xyz2mol_tm dataset (Jensen group,
  `csd_smiles.csv`) is used only where its CSD-API-derived and its Hückel-from-coordinates
  SMILES agree. Where the ligand charge balance (`mecobi_ready_<M>.csv`) also gives a value the
  two must match; for hapto complexes, where the charge balance counts a Cp carbon by carbon, the
  xyz2mol value decides alone. p-block metals, which xyz2mol does not cover, need the charge
  balance to agree with the CSD annotation. A value outside −2…the metal's highest oxidation
  state, or with signs of a lost hydride, is discarded. A structure without a confirmed oxidation
  state still feeds the coarse `metal|donor` level.
* *Carbon classes.* A carbon whose only non-metal neighbour is an O or N within 1.30 Å is
  `C_sp`. A carbon donor bonded to a fellow donor is `C_eta`. Everything else is `C`. Mixed, a
  Cp carbon pulled Ru(II)–C to 2.20 Å against a σ-carbon 2.05 Å; kept out of the oxidation-state
  bins but looked up as `C`, it was restrained to the σ value instead (Ti(IV): 2.14 Å against a
  Ti–Cp of 2.38 Å). The `metal|C_eta` bins of the shipped table are oxidation-state independent:
  over 27,720 hapto bonds of the benchmark the per-oxidation-state mean deviates from the
  per-metal mean by 0.017 Å on average (Pd / Pt alkenes are the exception, about 0.13 Å).
* *Minimum support.* An oxidation-state cell needs 5 distinct structures, a coarse cell 3.
* *f-block* metals are carried over from the first table unchanged.

**Validation.** Restraint target against crystal distance over 19k benchmark bonds (in-sample):
MAE 0.115 → 0.077 Å, bias +0.032 → −0.002 Å. Build A/B on the 10 × 100 stratified pilots
(xtb 6.7.1, 991 complexes built with both tables): median bond RMSD 0.091 → 0.066 Å, 204 complexes
better and 46 worse by more than 0.05 Å; haptic complexes 0.085 → 0.053 Å. c-kmRMSD is essentially
unchanged (0.514 → 0.499 Å).

## Limitations

* Convergence is judged on **coarse** `(M, D)` bins; fine `(M, q, D, CN)` bins
  for rare oxidation states / high coordination numbers may remain under-sampled
  when a metal stops early. For a manuscript-grade table, raise `patience`, set
  `max_complexes`, or judge the stop on fine bins for metals of interest, and
  report per-bin *n* and SEM so under-populated bins are visible.
* Haptic (η) donors enter as multiple M–C contacts and inflate CN; the current
  table records them as `(M, C, CN)` without distinguishing σ- from
  π-coordination. `_geom_bond` completeness varies between depositions, and
  oxidation states inherited from `FilteredOS` are unreliable for redox-non-
  innocent / oxo-rich early transition metals.

## Reproducibility

```bash
# mine specific metals (skips OneDrive placeholders; resumable)
python tmp_cifreview_fixed/mine_bond_lengths.py --metals Nickel Palladium Platinum \
    --n-min 25 --tol 0.01 --delta 0.005 --patience 100 --resume

# mine everything currently on disk
python tmp_cifreview_fixed/mine_bond_lengths.py --resume

# convergence figures
python tmp_cifreview_fixed/plot_convergence.py --tol 0.01
```
