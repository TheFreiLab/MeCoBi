"""Trigonal bipyramidal (CN 5): two axial donors (+/- z) + a trigonal equatorial
belt at 120 deg. The D3h alternative to square-pyramidal, preferred for d8/d10.

Sites: 0 = +z axial, 1 = -z axial, then equatorial 2 = +x, 3 = +120 deg,
4 = -120 deg.
"""
from __future__ import annotations

_COS120, _SIN120 = -0.5, 0.8660254037844387

SITE_VECTORS: tuple[tuple[float, float, float], ...] = (
    (0.0, 0.0, 1.0),
    (0.0, 0.0, -1.0),
    (1.0, 0.0, 0.0),
    (_COS120, _SIN120, 0.0),
    (_COS120, -_SIN120, 0.0),
)
