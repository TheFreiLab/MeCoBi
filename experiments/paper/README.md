# Results behind the MeCoBi paper

Preprint: G. Clauss, D. R. Husbands, Ç. Özsan, C. Abbehausen and A. Frei, *MeCoBi: A fast and accurate transition metal complex builder that generates 3D structures at scale and enables structure-based machine learning*, ChemRxiv, 2026, [10.26434/chemrxiv.15011867](https://doi.org/10.26434/chemrxiv.15011867/v1).

The results that every figure, table and number of the paper is computed from, organised by section. Only
identifiers, labels, our predictions, our xTB values and the resulting metrics are stored here. No structures, and no
data that belong to the source databases, are included:

- **CSD**: complexes are identified by their refcode; ligand SMILES, oxidation states and coordinates are not
  included (the benchmark set itself is Supplementary Data 1).
- **MetalCytoToxDB**: measurements are identified by the keys of the database entry (DOI, cell line, exposure time,
  ligand SMILES, counterion); IC50 values are not included. `y` is the binary label derived from IC50 as described
  in the Methods (toxic when the IC50 in the dark is below 10 µM).
- **tmQM**: complexes are identified by their CSD refcode; the DFT dipole moments and HOMO–LUMO gaps are not included
  and are needed, from tmQM, to compute the errors.

The iridium library is our own and is given in full (activities, conversions, building blocks).

Supplementary Tables and Figures are numbered as in the submitted Supplementary Information. Supplementary Data 1–9
(the benchmark set, the generated structures and the tool-comparison report) are on Zenodo:
[10.5281/zenodo.24011213](https://doi.org/10.5281/zenodo.24011213).

## `benchmark/`: 30,830 CSD complexes (Figures 2–3, Tables S1–S5, S11)

| File | Content |
|---|---|
| `mecobi_per_structure.csv` | one row per complex: refcode, metal, coordination number, crystal geometry, build outcome, time and the five structural metrics (c-kmRMSD, D-MAE3, poly-CShM, dmat RMSD, bond RMSD) |
| `crystal_geometry.csv` | coordination geometry read from each crystal |
| `score_summary.csv` | summary statistics of the run |
| `run_meta.json` | MeCoBi commit, xtb version and options of the run |
| `random_subsets.csv` | the ten random subsets of 100 complexes (Figure 4d, Table S11) |
| `excluded_heterobimetallic.txt` | the 31 entries removed from the benchmark set |

The run covered 30,861 entries, and `mecobi_per_structure.csv`, `score_summary.csv` and `run_meta.json` include
all of them. The paper uses 30,830: the 31 refcodes in `excluded_heterobimetallic.txt` have uranium or thorium inside
a ligand. They are heterobimetallic complexes listed under their transition metal, and none of them was built
(`built` is False for all 31). Removing them changes only the counts and the build success (99.55% → 99.65%,
139 → 108 failures); every structural metric is unchanged. Two of them are in the random subsets (POTQIA in r02,
UQIWOI in r04), so those two subsets have 99 complexes in Table S11.

## `tool_comparison/`: MeCoBi, MetalloGen, Architector, molSimplify (Figure 4, Table 1, Tables S6–S10)

`per_structure.csv` holds one row per complex and tool: built or not, time and structural metrics. The other files
are the summaries printed in the tables.

## `metalcytotoxdb/`: cytotoxicity (Figure 5, Table 2, Table S12, Figure S2)

- `rows_ruthenium.csv` and `rows_six_metals.csv` map each `row_id` to its MetalCytoToxDB entry.
- `oof/*.csv` hold the out-of-fold predictions: `row_id, complex_id, y, prob, fold`. The folds are the ten-fold
  split by publication. The 3D models and the 2D models retrained on their rows cover only the measurements whose
  structure passed the filter.

| File (`oof/`) | Paper |
|---|---|
| `ru_{lightgbm,mlp,dimenet}_descriptors` | Table 2 (with descriptors), Figure 5b |
| `ru_{lightgbm,mlp,dimenet}_no_descriptors` | Table 2 (without descriptors); consensus without descriptors (0.804) |
| `ru_{lightgbm,mlp}_cell_line_only`, `ru_{lightgbm,mlp}_no_time` | context ablations (text) |
| `ru_dimenet_isomers_one_per_epoch`, `ru_dimenet_isomers_all` | DimeNet++ with every geometric isomer (0.790, 0.791) |
| `six_metals_{lightgbm,mlp,dimenet}` | six-metal comparison on the 21,554 measurements with a structure (Figure 5c, Figure S3, Table S12) |
| `six_metals_dimenet_meridional_re` | the same DimeNet++ model trained before the rhenium tricarbonyls were rebuilt facial (see below) |
| `six_metals_{lightgbm,mlp}_all_rows` | 2D models on all 22,358 measurements (per-metal comparison with the reference study) |

The ROC-AUC is computed per fold on the rows of the corresponding DimeNet++ file and averaged over the ten folds.
The consensus is the mean, per fold, of the two models' ranks scaled to 0–1. For the agreement rule, each model
flags as toxic the top fraction of measurements equal to the toxic fraction of the training folds.

| Other files | Content |
|---|---|
| `metrics/*.json` | the per-fold metrics written by each training run |
| `consensus_summary.txt` | consensus scores and agreement rules (text) |
| `per_metal_difference.csv` | DimeNet++ − LightGBM per metal, 95% interval (Figure 5c) |
| `multimetal_per_metal_retrained.csv` | per-metal ROC-AUC, 2D models retrained on the 21,554 measurements (Table S12) |
| `multimetal_per_metal.csv` | the same with the 2D models trained on all 22,358 measurements |
| `re_tricarbonyl_isomer.csv` | the 148 rhenium tricarbonyls rebuilt facial: outcome and GFN2-xTB energy of the facial minus the meridional structure |
| `families_*.csv`, `family_roc_auc.csv` | structural family of each measurement and ROC-AUC within each family (Figure S2) |

`per_metal_difference.csv`, `multimetal_per_metal*.csv`, the six-metal rows of `family_roc_auc.csv` and the six-metal
consensus in the text are written by `scripts/metalcytotoxdb/six_metal_tables.py` from the `oof/` files.

**Rhenium tricarbonyls.** The library was built with one isomer per complex, chosen by MeCoBi's default rules, which
place the monodentate ligands in the order of the SMILES. This put the three CO ligands meridional in 148 of the 236
Re(CO)3 complexes, whereas such complexes are facial. These were rebuilt with the CO on mutually cis sites
(`scripts/metalcytotoxdb/re_fac/`): 141 kept their connectivity (137 at the first attempt, 4 at a second one); for
the other 7 the meridional structure was kept (`re_tricarbonyl_isomer.csv`). In all 135 complexes where both
structures were relaxed, the facial one is lower in GFN2-xTB energy (median 19.6 kcal/mol). The quality filter keeps
the same 21,554 measurements, and the six-metal DimeNet++ model was retrained on the rebuilt structures
(`six_metals_dimenet`); its ROC-AUC changed by +0.001 over the six metals and +0.002 for rhenium against the model
trained before (`six_metals_dimenet_meridional_re`). `metrics/six_metals_dimenet.json` is from the run before the
rebuild. The ruthenium models are not affected (no rhenium).

## `iridium/`: antibacterial activity of [IrCp(SB)Cl]+ (Figure 6, Table 3, Tables S13–S16, S19, Figures S4–S6)

| File | Content |
|---|---|
| `complexes.csv` | the 1,800 complexes, their generation, building-block key, conversion, growth of S. aureus at 12.5 µM and activity label |
| `building_blocks.csv` | aldehydes and amines |
| `predictions_per_seed.csv` | predicted probability of every model, training set (gen0, or gen0 + gen1) and seed (42–46) for every complex |
| `thresholds_per_seed.csv` | the Youden threshold of each model and seed, chosen on the training data |
| `xtb_values.csv` | the 14 GFN2-xTB values per structure used as descriptors |
| `metrics/` | ROC-AUC and threshold metrics per model and seed |
| `logp*.csv`, `amide_amines.csv`, `metric_panel.csv`, `rocauc_per_seed.csv`, `numbers.txt`, `si_tables.txt` | the values of Tables 3, S13–S16 and S19 and of the text |

The predictions and metrics also include a GINE network that was trained as a control (method `GINE`). It was
removed from the paper (Table 3, the Supplementary tables, Figure 6c, Figure S6 and the Methods) because its ROC-AUC
on gen2 is at chance (0.495 and 0.499) with nearly constant predictions, so it does not work as a control; the rows are
kept here as they were produced.

## `tmqm/`: dipole moments and HOMO–LUMO gaps (Figure 7, Tables S17, S18 and S20, Figure S7)

| File | Content |
|---|---|
| `inclusion.csv` | per tmQM complex in the benchmark set: formula and charge agreement, distance to the tmQM geometry (Figure S7), inclusion (Table S17) |
| `exclude_overlap.txt` | complexes excluded for atoms closer than 0.8 Å |
| `folds.csv` | fold of each complex (`random`: random ten-fold split, Figure 7; `ligand`: split by largest ligand, Table S18) |
| `table_tmqm_random.csv`, `.txt` | the table of Figure 7f and Table S18 (random split): MAE, MAE relative to the mean DFT value, R², and the MAE below 1 D, per model |
| `oof_2d_and_isomer_label.csv`, `oof_2d_and_isomer_label_random.csv` | out-of-fold predictions of the 2D model and of 2D + isomer label (ligand and random split) |
| `oof_xtb.csv`, `oof_xtb_random.csv` | out-of-fold predictions with the xTB values of the crystal-isomer structure, of the tmQM geometry, and both with the isomer label (ligand and random split) |
| `oof_smiles_only_random.csv` | out-of-fold predictions for the 1,246 complexes built from the SMILES alone (random split), with the number of isomers of each |
| `xtb_single_points.csv` | GFN2-xTB values on the crystal-isomer structures and on the tmQM geometries |
| `xtb_single_points_smiles_only_isomers.csv` | GFN2-xTB values on the 1,997 valid isomers built from the SMILES alone for the 2,000-complex sample (MeCoBi 6e0590a, xTB 6.7.1) |
| `smiles_only_status.csv` | outcome of the SMILES-only build of each of the 2,000 complexes and the reason for each failure (Table S20) |
| `smiles_only_failures.csv` | predicted and crystal coordination number of the 1,946 complexes built from the SMILES alone |
| `smiles_only_hydrogen_mismatch.csv` | the 101 valid SMILES-only builds whose isomers all lack hydrogens of the tmQM entry, with the number of hydride ligands (Table S20, column Evaluated) |
| `metrics/` | MAE tables printed by the analysis (`*_random.txt`: random split) |

Predictions are the mean of three LightGBM seeds. The errors are computed against the DFT values of tmQM on the
10,175 complexes that have all inputs (`oof_xtb.csv`).

**From 10,209 to 10,175.** `inclusion.csv` marks the 10,209 complexes whose MeCoBi structure has the atoms and charge
of the tmQM entry, and the 2D models are trained on all of them (`oof_2d_and_isomer_label*.csv`). The models
with xTB values need the single point on the crystal-isomer structure, which is missing for 34 of them:

- 12 have two atoms closer than 0.8 Å in the MeCoBi structure (`exclude_overlap.txt`);
- for 22 others, xTB stopped with an error on the MeCoBi structure (`ok` is False in `xtb_single_points.csv`;
  OSEQUZ is in both groups, so 23 single points failed in all).

The single points on the tmQM geometries succeeded for all 10,209. Every model in Figure 7 and Table S18 is
compared on the same 10,175 complexes.

**From 2,000 to 1,246 (SMILES only).** `smiles_only_status.csv` gives the build outcome. The complexes are lost in
this order:

| Step | Complexes left |
|---|---:|
| sample drawn from the benchmark set | 2,000 |
| at least one isomer built with the connectivity of the SMILES (`valid`; Table S20) | 1,357 |
| in `inclusion.csv` (6 are not: the sample was drawn before the final filters of the benchmark set) | 1,351 |
| at least one isomer with the atoms of the tmQM entry; for the 103 others, every isomer has 1 or 2 hydrogens fewer (see below) | 1,248 |
| in the 10,175 set, so that the model can be trained and its crystal-isomer reference exists (UHIKUS: xTB error; XIXVOP: atoms closer than 0.8 Å) | 1,246 |

Of the 1,357 valid builds, 1,347 are in the 10,175 set. The other 10 are the 6 complexes not in `inclusion.csv`, the 2 above
and 2 that also fail the hydrogen check. Isomers whose atoms differ from the tmQM entry are also left out of the
lowest-energy and Boltzmann choices for the complexes that are kept (`isomer_average_xtb.py`).

**Missing hydrogens are hydride ligands.** The ligand SMILES mined from the CSD contain no hydride ligands. For the
crystal-isomer structures, the hydrides are added back from the crystal (`benchmark_hydrides.json` in
`experiments/benchmark/`); a structure built from the SMILES alone has no crystal and so lacks them. Of the 101
valid builds in the 10,175 set whose isomers all have fewer hydrogens than the tmQM entry
(`smiles_only_hydrogen_mismatch.csv`), 95 miss exactly their hydride ligands (`n_hydride` in `inclusion.csv`: 78
with one, 17 with two). The other 6 (GITVOX, KEDRIU, NOSZIE, RAWXIW, ROZNEA, UZASIZ) have no hydride by that count
and miss one hydrogen. No complex with a hydride ligand is therefore in the 1,246. Per crystal CN, the 101 are
15 (CN 4), 25 (CN 5), 44 (CN 6), 9 (CN 8), 7 (CN 9) and 1 (CN 10).
