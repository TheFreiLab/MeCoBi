"""Triangular dodecahedron / bisdisphenoid (CN 8, D2d): the other common CN8
geometry (e.g. [Mo(CN)8]4- in some salts, [ZrF8]4-, Ti/Zr peroxo and
bidentate-rich 8-coordinate complexes). Two interpenetrating disphenoids
("A" and "B" sites) at different polar angles from the S4 axis (z).

Sites: 0-3 = A vertices (steep, near the axis, colatitude ~36.9 deg),
4-7 = B vertices (shallow, near the equator, colatitude ~69.5 deg). The A
disphenoid lies in the xz-plane above / yz-plane below; the B disphenoid is
rotated 90 deg. Hoard-Silverton ideal MX8 angles; approximate directions only
seed the assembly, MCHammer + xtb relax.
"""
from __future__ import annotations

import math

# Hoard-Silverton "hard-sphere" dodecahedron: A vertices at colatitude thetaA
# from the S4 (z) axis, B vertices at thetaB.
_THETA_A = math.radians(36.9)
_THETA_B = math.radians(69.5)
_SA, _CA = math.sin(_THETA_A), math.cos(_THETA_A)
_SB, _CB = math.sin(_THETA_B), math.cos(_THETA_B)

SITE_VECTORS: tuple[tuple[float, float, float], ...] = (
    # A disphenoid: upper pair in the xz-plane, lower pair in the yz-plane
    (_SA, 0.0, _CA),
    (-_SA, 0.0, _CA),
    (0.0, _SA, -_CA),
    (0.0, -_SA, -_CA),
    # B disphenoid: upper pair in the yz-plane, lower pair in the xz-plane
    (0.0, _SB, _CB),
    (0.0, -_SB, _CB),
    (_SB, 0.0, -_CB),
    (-_SB, 0.0, -_CB),
)
