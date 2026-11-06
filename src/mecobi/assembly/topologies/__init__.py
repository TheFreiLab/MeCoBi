"""Custom stk topology graphs, one module per (geometry, denticity-partition).

Each module defines a :class:`~.metal_complex.MetalComplex` subclass whose metal
+ ligand vertex prototypes and edges lay out one coordination motif; shared
vertex classes live in :mod:`.vertices`. :mod:`mecobi.assembly.registry` maps a
(geometry, denticity partition) to the right class and imports these lazily, so
nothing here is loaded until a build needs it.

Two kinds of thing live here:

* **Fixed motif classes** (one ``.py`` per module) — hand-tuned vertex/edge
  geometry for a specific (geometry, denticity partition): linear (2mono);
  square-planar (4mono, 2bi, 1bi+2mono, 3+1 pincer); octahedral (6mono,
  1bi+4mono, 2bi+2mono cis, 3bi, 3+3 bis-tridentate, 4+1+1 salen/porphyrin);
  and the half-sandwich piano stools (:mod:`.piano_stool`).
* **Coordination-geometry definitions** (:mod:`.geometries` subpackage) — the
  ideal donor directions (``SITE_VECTORS``) for each geometry, one module each,
  including CN3/5/7/9 which have no fixed motif class. The generic site model
  (:mod:`mecobi.assembly.sites`) builds a topology from these for any partition.
"""
