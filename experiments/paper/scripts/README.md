# Analysis scripts behind the paper

The scripts that produced the predictions, metrics and in-text numbers in `../`, as they were run. Figure-drawing
scripts are not included, except the one that draws Figure 7 and its table. The structural benchmark and the tool comparison are in `experiments/benchmark/`.

The scripts are as they were run (on a Windows workstation and the Keisan cluster), except that local paths are
replaced by placeholders: `<DATA_ROOT>` (the folder holding the paper's input data), `<MECOBI_REPO>` (a clone of
this repository) and `<BIOMETALDB_ML>` (the MetalCytoToxDB working folder). To rerun a script, point those
constants at your copies of the inputs. Sibling imports assume the folder layout below.

## `metalcytotoxdb/`: cytotoxicity (Table 2, Figure 5, Figure S2)

| Script | Role |
|---|---|
| `src/data_curation.py`, `src/curate_multimetal.py` | ruthenium and six-metal datasets from MetalCytoToxDB; toxic label (IC50 < 10 µM); `row_id` |
| `src/splitting.py`, `splits/*_doi_10fold.json` | ten-fold split by publication |
| `src/feature_engineering.py` | ECFP, RDKit descriptors and context features |
| `src/structure_mapping.py` | links each measurement to its MeCoBi structure and applies the quality filter |
| `src/train_lightgbm.py`, `src/train_mlp.py` | 2D baselines (`--context` for the context ablations) |
| `src/make_3d_rows_subset.py`, `splits/*_3drows_fix_doi_10fold.json` | 2D baselines retrained on the measurements with a structure |
| `src/run_guard.py` | refuses to overwrite results or resume from checkpoints of another run |
| `src/train_dimenet.py`, `src/dimenet_shim.py` | DimeNet++ (`--no-rdkit` for the run without descriptors; `--isomers-dir --aug-mode stochastic/full` for the isomer runs) |
| `src/per_metal_auc.py` | per-metal ROC-AUC |
| `isomers/build_isomers_mctdb.py` | every geometric isomer of the ruthenium complexes |
| `consensus/make_prob_parity.py` | rank-average consensus and agreement rule |
| `consensus/ru_classes.py` | structural family of each complex and ROC-AUC per family |
| `six_metal_tables.py` | per-metal tables (Table S12, Figure 5c), six-metal family ROC-AUC and consensus from the `oof/` files |
| `re_fac/rebuild_re_fac.py`, `re_fac/pick_attempts.py`, `re_fac/check_fac.py` | rebuild of the 148 meridional rhenium tricarbonyls (`re_mer_names.txt`) with the CO facial; retries (`retry_names.txt`) and choice of the facial build per complex |

## `iridium/`: antibacterial activity (Table 3, Figure 6, Tables S13–S16, S19)

| Script | Role |
|---|---|
| `prepare_inputs.py`, `run_build.py` | MeCoBi inputs and build of the 1,800 complexes |
| `pipeline/build_master.py`, `pipeline/common.py` | master table, activity label, fingerprints |
| `pipeline/exp_unified_multiseed.py` | ECFP and ECFP+RDKit MLPs, DimeNet++ and GINE (a control no longer in the paper); five seeds, Youden threshold on a held-out 20% |
| `pipeline/exp_extra_lgbm.py`, `pipeline/exp_extra_rdkit_gine.py` | LightGBM baselines and the RDKit-descriptor MLP |
| `xtb_sp/run_xtb_sp.py`, `xtb_features/make_manifest.py`, `xtb_features/features.py` | GFN2-xTB single points and the 14 xTB values |
| `xtb_features/ml.py` | LightGBM with the xTB values |
| `numbers_fix2.py`, `si_tables_fix2.py` | every number of the iridium section and its SI tables |

## `tmqm/`: dipole moments and HOMO–LUMO gaps (Figure 7, Tables S17–S18, Figure S7)

| Script | Role |
|---|---|
| `fix6e0590a_dataset.py` | inclusion, folds and 2D feature table |
| `baseline_2d.py`, `desc3d_rdkit_floor.py` | 2D features and the LightGBM model |
| `isomer_control.py`, `table5_block1.py` | 2D and 2D + isomer label (`--split random` for the random folds) |
| `xtb_sp/prepare_tmqm_sp.py`, `xtb_sp/analyze_tmqm_xtb.py` | xTB single points; models with xTB values (`--split random`) |
| `isomers/build_isomers.py`, `isomers/prepare_isomer_sp.py`, `xtb_sp/isomer_average_xtb.py` | SMILES-only isomers, their single points, lowest-energy and Boltzmann predictions (`--split random`; `ISO_DIR` points at the run) |
| `isomers/smiles_only_failures.py` | predicted against crystal coordination number of the SMILES-only builds (Table S20) |
| `isomers/smiles_only_table.py` | outcome of each SMILES-only build and the counts of Table S20 (`../tmqm/smiles_only_status.csv`) |
| `isomers/smiles_only_hydrogen_check.py` | valid SMILES-only builds that lack hydrogens (hydride ligands) of the tmQM entry (`../tmqm/smiles_only_hydrogen_mismatch.csv`, Table S20) |
| `tmqm_table.py` | the table of Figure 7f and Table S18: absolute and relative errors, controls |
| `figures/make_tmqm_figure_v4.py` | Figure 7 (table f with the MAE only; colours mark the source of each structure) |
