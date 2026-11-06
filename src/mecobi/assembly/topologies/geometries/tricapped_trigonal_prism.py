"""Tricapped trigonal prism (CN 9): two parallel triangular faces (z = +/-)
plus three equatorial caps over the rectangular prism faces. The common CN9
geometry (e.g. [ReH9]2-, lanthanide aqua ions).

Sites: 0-2 = top triangle (z = +Z), 3-5 = bottom triangle (z = -Z),
6-8 = equatorial caps in the xy-plane.
"""
from __future__ import annotations

_COS120, _SIN120 = -0.5, 0.8660254037844387
_H = 0.816496580927726   # cos(35.26 deg): triangular-face donors' radial component
_Z = 0.5773502691896257  # sin(35.26 deg): their axial (+/- z) component

SITE_VECTORS: tuple[tuple[float, float, float], ...] = (
    # top triangular face (z = +Z)
    (_H, 0.0, _Z),
    (_H * _COS120, _H * _SIN120, _Z),
    (_H * _COS120, -_H * _SIN120, _Z),
    # bottom triangular face (z = -Z)
    (_H, 0.0, -_Z),
    (_H * _COS120, _H * _SIN120, -_Z),
    (_H * _COS120, -_H * _SIN120, -_Z),
    # three equatorial caps
    (0.5, 0.8660254, 0.0),
    (-1.0, 0.0, 0.0),
    (0.5, -0.8660254, 0.0),
)
