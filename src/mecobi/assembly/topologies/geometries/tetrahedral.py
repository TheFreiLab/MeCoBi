"""Tetrahedral (CN 4): four donors at the vertices of a tetrahedron (109.47 deg).

Sites 0-3 point along alternating cube-corner directions. Unlike square planar,
every pair of sites is equivalent (all 109.47 deg apart), so there is no cis/trans
distinction; an MABCD complex is chiral (two enantiomers).
"""
from __future__ import annotations

_T = 0.5773502691896258  # 1/sqrt(3)

SITE_VECTORS: tuple[tuple[float, float, float], ...] = (
    (_T, _T, _T),
    (_T, -_T, -_T),
    (-_T, _T, -_T),
    (-_T, -_T, _T),
)
