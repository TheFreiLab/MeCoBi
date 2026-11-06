"""Bent-metallocene site directions (Cp2MXn, e.g. titanocene dichloride, Rosenthal's
Cp2Ti(η²-alkyne)).

Two η-cap sites point **up and apart** (Cp–M–Cp ≈ 136°); the ancillary X ligands sit
in the equatorial **wedge below**, in the plane perpendicular to the Cp–M–Cp plane —
the classic Cp2MXn shape, NOT a flat trigonal/tetrahedral arrangement. Site order:
cap 0, cap 1, then the ancillary sites 2…

Unlike the other geometry modules the site count is not fixed: a metallocene may
carry one ancillary (Cp2ML, an η²-alkyne midpoint), two (Cp2MX2, titanocene
dichloride) or three, so :func:`vectors` generates ``2 + (n_sites - 2)`` directions.
"""
from __future__ import annotations

import math

# angles from experimental Cp2MX2 structures: Cp(centroid)-M-Cp ~136, X-M-X ~95.
_CP_HALF = math.radians(136.0 / 2.0)   # each cap 68° off +z, in the xz plane
_X2_HALF = math.radians(95.0 / 2.0)    # each X 47.5° off -z, in the yz plane
_X3_HALF = math.radians(105.0 / 2.0)


def vectors(n_sites: int) -> tuple[tuple[float, float, float], ...]:
    """Unit site directions for a bent metallocene with ``n_sites`` total sites
    (2 caps + the rest ancillary). Caps first, then ancillary."""
    caps = [
        (-math.sin(_CP_HALF), 0.0, math.cos(_CP_HALF)),
        (math.sin(_CP_HALF), 0.0, math.cos(_CP_HALF)),
    ]
    k = max(0, n_sites - 2)
    anc: list[tuple[float, float, float]] = []
    if k == 1:
        anc = [(0.0, 0.0, -1.0)]                                   # Cp2ML: one wedge site
    elif k == 2:
        anc = [                                                    # Cp2MX2: two wedge sites
            (0.0, -math.sin(_X2_HALF), -math.cos(_X2_HALF)),
            (0.0, math.sin(_X2_HALF), -math.cos(_X2_HALF)),
        ]
    elif k >= 3:
        anc = [(0.0, 0.0, -1.0)]
        for i in range(k - 1):
            s = 1.0 if i % 2 == 0 else -1.0
            anc.append((0.0, s * math.sin(_X3_HALF), -math.cos(_X3_HALF)))
    return tuple(tuple(float(v) for v in vec) for vec in (caps + anc))
