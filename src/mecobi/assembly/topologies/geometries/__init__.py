"""Ideal coordination-site directions (unit vectors) per coordination geometry.

This subpackage is the single source of truth for *where the donors go* in each
geometry -- one module per geometry, each exporting ``SITE_VECTORS`` (a tuple of
unit direction vectors) with its site numbering documented. The site model
(:mod:`mecobi.assembly.sites`) builds an stk topology graph from these for ANY
denticity partition, and the fixed motif classes elsewhere in
:mod:`mecobi.assembly.topologies` are hand-tuned specialisations of the same
geometries for particular partitions (precise chelate bite angles, salen belts,
pincers).

Geometries whose donor layout lives here: linear + bent (CN2), trigonal-planar (CN3),
square-planar + tetrahedral (CN4), square-pyramidal + trigonal-bipyramidal (CN5),
octahedral (CN6), pentagonal-bipyramidal (CN7), square-antiprism + dodecahedral
(CN8), tricapped-trigonal-prism (CN9).
"""
from __future__ import annotations

from mecobi.model import Geometry

from . import (
    bent,
    linear,
    trigonal_planar,
    square_planar,
    tetrahedral,
    square_pyramidal,
    trigonal_bipyramidal,
    octahedral,
    pentagonal_bipyramidal,
    square_antiprism,
    dodecahedral,
    tricapped_trigonal_prism,
)

# geometry -> unit direction of each numbered coordination site
SITE_VECTORS: dict[Geometry, tuple[tuple[float, float, float], ...]] = {
    Geometry.LINEAR: linear.SITE_VECTORS,
    Geometry.BENT: bent.SITE_VECTORS,
    Geometry.TRIGONAL_PLANAR: trigonal_planar.SITE_VECTORS,
    Geometry.SQUARE_PLANAR: square_planar.SITE_VECTORS,
    Geometry.TETRAHEDRAL: tetrahedral.SITE_VECTORS,
    Geometry.SQUARE_PYRAMIDAL: square_pyramidal.SITE_VECTORS,
    Geometry.TRIGONAL_BIPYRAMIDAL: trigonal_bipyramidal.SITE_VECTORS,
    Geometry.OCTAHEDRAL: octahedral.SITE_VECTORS,
    Geometry.PENTAGONAL_BIPYRAMIDAL: pentagonal_bipyramidal.SITE_VECTORS,
    Geometry.SQUARE_ANTIPRISM: square_antiprism.SITE_VECTORS,
    Geometry.DODECAHEDRAL: dodecahedral.SITE_VECTORS,
    Geometry.TRICAPPED_TRIGONAL_PRISM: tricapped_trigonal_prism.SITE_VECTORS,
}
