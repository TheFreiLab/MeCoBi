"""Trigonal planar (CN 3): three donors at 120 deg in the xy-plane.

Sites: 0 = +x, 1 = +120 deg, 2 = -120 deg.
"""
from __future__ import annotations

_COS120, _SIN120 = -0.5, 0.8660254037844387

SITE_VECTORS: tuple[tuple[float, float, float], ...] = (
    (1.0, 0.0, 0.0),
    (_COS120, _SIN120, 0.0),
    (_COS120, -_SIN120, 0.0),
)
