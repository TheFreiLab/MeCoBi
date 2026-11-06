"""MeCoBi — Metal Complex Builder.

Core Python package: SMILES ligands -> pydentate perception -> coordination
number / geometry -> isomer enumeration -> stk assembly -> MCHammer -> xtb ->
optimised ``.xyz``.

This package is the real product. It has **zero web dependencies**
and runs fully locally. The web service is a thin orchestration layer that
imports this package; local and web use the *same code path* (invariant 2).

Public surface (stable seams):
    - :mod:`mecobi.model`      — data model (Metal, Ligand, Complex, ...).
    - :mod:`mecobi.perception` — pydentate wrapper (donor atoms, denticity).
    - :mod:`mecobi.geometry`   — CN -> geometry proposal + registry.
    - :mod:`mecobi.isomers`    — isomer enumeration + topology-spec seam.
    - :mod:`mecobi.assembly`   — stk topology graphs + construction.
    - :mod:`mecobi.optimize`   — MCHammer + xtb relaxation.
    - :mod:`mecobi.naming`     — charge/isomer filename conventions.
    - :mod:`mecobi.pipeline`   — end-to-end orchestration.
"""

__version__ = "0.1.1"
