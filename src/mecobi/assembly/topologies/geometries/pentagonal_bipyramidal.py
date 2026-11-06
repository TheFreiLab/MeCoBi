"""Pentagonal bipyramidal (CN 7): two axial donors (+/- z) + a pentagonal
equatorial belt at 72 deg spacing.

Sites: 0 = +z axial, 1 = -z axial, then equatorial 2..6 sweeping the belt
(+x, +72 deg, +144 deg, -144 deg, -72 deg).
"""
from __future__ import annotations

_COS72, _SIN72 = 0.30901699437494745, 0.9510565162951535
_COS144, _SIN144 = -0.8090169943749475, 0.5877852522924731

SITE_VECTORS: tuple[tuple[float, float, float], ...] = (
    (0.0, 0.0, 1.0),
    (0.0, 0.0, -1.0),
    (1.0, 0.0, 0.0),
    (_COS72, _SIN72, 0.0),
    (_COS144, _SIN144, 0.0),
    (_COS144, -_SIN144, 0.0),
    (_COS72, -_SIN72, 0.0),
)
