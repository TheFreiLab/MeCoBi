"""Square antiprism (CN 8, D4d): two parallel square faces (z = +/-H) twisted
45 degrees relative to each other. The most common CN8 geometry (e.g.
[Zr(ox)4]4-, [Mo(CN)8]4-, many lanthanide 8-aqua/nitrate ions).

Sites: 0-3 = top square (z = +H, azimuth 0/90/180/270),
4-7 = bottom square (z = -H, azimuth 45/135/225/315).

Radial/axial split is the ideal equal-edge antiprism (all 16 edges equal):
solving square-edge = slant-edge with r^2 + H^2 = 1 gives r ~ 0.8596,
H ~ 0.5111. Approximate directions only seed the assembly; MCHammer + xtb relax.
"""
from __future__ import annotations

import math

# ideal equal-edge square antiprism: square-edge^2 = 2 r^2 set equal to the
# slant-edge^2 = r^2*((1-cos45)^2 + cos45^2) + (2H)^2, with r^2 + H^2 = 1.
_C = math.cos(math.pi / 4)                       # 45 deg twist, = sin(45)
_R = math.sqrt(1.0 / (1.0 + (2.0 - 2.0 * _C)))   # radial component ~0.859536
_H = math.sqrt(1.0 - _R * _R)                    # axial component  ~0.511103
_RC = _R * _C

SITE_VECTORS: tuple[tuple[float, float, float], ...] = (
    # top square (z = +H), azimuth 0 / 90 / 180 / 270
    (_R, 0.0, _H),
    (0.0, _R, _H),
    (-_R, 0.0, _H),
    (0.0, -_R, _H),
    # bottom square (z = -H), azimuth 45 / 135 / 225 / 315 (twisted 45 deg)
    (_RC, _RC, -_H),
    (-_RC, _RC, -_H),
    (-_RC, -_RC, -_H),
    (_RC, -_RC, -_H),
)
