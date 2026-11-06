"""Square planar (CN 4): four donors at 90 deg in the xy-plane.

Sites: 0 = +x, 1 = +y, 2 = -x, 3 = -y (adjacent ids are cis, opposite are trans).
"""
from __future__ import annotations

SITE_VECTORS: tuple[tuple[float, float, float], ...] = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (-1.0, 0.0, 0.0),
    (0.0, -1.0, 0.0),
)
