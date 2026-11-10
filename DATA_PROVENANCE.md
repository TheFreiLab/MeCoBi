# Data provenance

## `src/mecobi/data/ml_reference.json`

The only dataset shipped inside the MeCoBi package. It supplies experimental
metal-donor (M-L) target distances used to restrain bonds during optimisation,
replacing generic covalent-radius sums. Applying it halved bond RMSD in the A/B
test (roughly 0.21 to 0.09 Angstrom). The table was rebuilt in October 2026 from
every structure of the collection (the first version came from a run stopped
early and had no Zr-N / Zr-O / Zr-Cl or Sn-Cl bins); on the 10 x 100 benchmark
pilots the rebuild took the median bond RMSD from 0.091 to 0.066 Angstrom.

### What the file contains

Aggregate statistics only. Every entry is a summary over many crystal
structures: a mean distance, an observation count `n`, a standard deviation and
a standard error, keyed by a chemical bin. Three nested levels:

| Level | Key | Cells | Observations |
|---|---|---:|---:|
| fine | `metal\|oxidation state\|donor\|CN` | 2,678 | 861,112 |
| marginal | `metal\|oxidation state\|donor` | 1,063 | 868,386 |
| coarse | `metal\|donor` | 747 | 1,965,574 |

`donor` is an element, or one of two carbon classes that MeCoBi looks up
separately: `C_sp` (carbonyl, cyanide, isocyanide) and `C_eta` (a hapto carbon:
Cp, arene, alkene, allyl). Plain `C` holds the remaining, sigma-bonded carbons.

It contains **no CSD records**: no refcodes, no atomic coordinates, no unit
cells, no structures, and nothing that identifies an individual deposition.

### Where it comes from

Derived from the Cambridge Structural Database (CSD), via the CombChemML
Generation-3 collection of mononuclear metal-complex CIFs (311,289 structures
across 50 metal elements). Bond lengths are taken from the
crystallographer-deposited `_geom_bond` loop. The 36 non-f-block metals are
mined by `experiments/benchmark/dataprep/mine_ml_reference.py` from all of their
structures (293,443 with a usable bond loop). An oxidation state is assigned to
172,969 of them by consensus: the metal's formal charge in the xyz2mol_tm
dataset (Rasmussen et al., `csd_smiles.csv`), used only where its two SMILES agree
and, where our own charge balance also gives a value, where that agrees too.
Structures without a confirmed oxidation state still feed the coarse level. The
`metal|C_eta` bins and the sigma-only `metal|C` coarse bins were mined without
oxidation states. The f-block metals are carried over unchanged from the first
version of the table (`FilteredOS` oxidation states, early-stopped mining). The
method is documented in
[`docs/METHODS_bond_length_mining.md`](docs/METHODS_bond_length_mining.md).

### CCDC review

This table is published **following CCDC review**. On 5 November 2026 the CCDC
Data/Science team reviewed the request to publish these aggregates and agreed
that, as no CSD structures are published, this is allowed. CCDC asked that
publications state the table was released following their review.

For the record, the table as reviewed has two properties:

1. **The aggregates are summary statistics, not data records.** No structure can
   be reconstructed from the file, and the observation counts show the bins are
   genuinely aggregated: the coarse level averages over 1.97 million bond
   observations.
2. **Some f-block bins are thin.** In the rebuilt part of the table an
   oxidation-state cell is emitted only with at least 5 distinct structures and
   a coarse cell with at least 3. The f-block cells carried over from the first
   version have no such floor: 2.0% of all fine-level cells (53, all f-block)
   rest on two or fewer observations. Lanthanides and actinides are outside
   MeCoBi's scope, so these cells are not used for any supported build.

### Not shipped

Nothing under `experiments/` is part of the installed package; it is excluded
from the wheel. The repository includes the benchmark's per-refcode inputs
(refcode, ligand SMILES, oxidation state, donor atoms, geometry labels) and the
results behind the paper, but no CSD coordinates: the crystal coordination
spheres, cores and hydride positions (`benchmark_spheres*.json.gz`,
`benchmark_cores*.json.gz`, `benchmark_hydrides.json`) and the CIFs are not
distributed. With a CSD licence they can be regenerated from the CIFs; see
`experiments/benchmark/README.md`.
