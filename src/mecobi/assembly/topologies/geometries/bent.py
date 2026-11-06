"""Bent (CN 2): two donors 90 degrees apart, for a single chelate on a two-coordinate centre.

Sites: 0 = +x, 1 = +y.

A chelate can only span adjacent sites, and the two linear sites are trans, so a CN2 complex
held by one bidentate (Ge/Sn/Pb(II) and Ga/In/Tl(I) beta-diketiminates, amidinates, ...) has
no linear placement. In the crystal those donors sit 60-100 degrees apart (median 89 over 177
CSD CN2 chelates); 90 is the starting angle, and the relaxation sets the real bite.
"""
from __future__ import annotations

SITE_VECTORS: tuple[tuple[float, float, float], ...] = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
)
