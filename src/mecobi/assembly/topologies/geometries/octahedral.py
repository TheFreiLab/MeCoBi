"""Octahedral (CN 6): six donors along the +/- x, y, z axes.

Sites: 0 = +x, 1 = -x, 2 = +y, 3 = -y, 4 = +z, 5 = -z (each axis pair is trans).
"""
from __future__ import annotations

SITE_VECTORS: tuple[tuple[float, float, float], ...] = (
    (1.0, 0.0, 0.0),
    (-1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, -1.0, 0.0),
    (0.0, 0.0, 1.0),
    (0.0, 0.0, -1.0),
)
