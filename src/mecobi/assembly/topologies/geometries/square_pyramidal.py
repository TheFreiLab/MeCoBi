"""Square pyramidal (CN 5): an apical donor (+z) over a square base in the
xy-plane. The C4v default for most d-counts (d8/d10 prefer trigonal-bipyramidal).

Sites: 0 = apex (+z), then the base 1 = +x, 2 = +y, 3 = -x, 4 = -y.
"""
from __future__ import annotations

SITE_VECTORS: tuple[tuple[float, float, float], ...] = (
    (0.0, 0.0, 1.0),
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (-1.0, 0.0, 0.0),
    (0.0, -1.0, 0.0),
)
