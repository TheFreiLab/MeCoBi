"""Vendored copy of pydentate (Kulik Group, MIT licence — see ./LICENSE).

Source: https://github.com/hjkgrp/pydentate  (Copyright (c) 2024 Kulik Group)

GNN-based prediction of metal-ligand coordination (coordinating atoms,
coordination number, hemilability). Bundled so the MeCoBi core is a standalone,
pip-installable package. Only the internal imports were adjusted (made relative);
the model architecture and weights are unmodified.

If you use MeCoBi's perception, please cite:
  - "Graph Neural Networks for Predicting Metal-Ligand Coordination of
    Transition Metal Complexes", PNAS. doi:10.1073/pnas.2415658122
  - "Identifying Dynamic Metal-Ligand Coordination Modes with Ensemble
    Learning", JACS. doi:10.1021/jacs.5c17169
"""
