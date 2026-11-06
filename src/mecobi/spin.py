"""Spin state -> number of unpaired electrons for xtb ``--uhf``.

Default is low spin; an override is exposed via :class:`~mecobi.model.Spin`.
The unpaired-electron count comes from a simple crystal-field model: the metal
d-electron count filled into the geometry's orbital-splitting pattern (low spin
= aufbau with pairing within the splitting; high spin = maximise unpaired, Hund
across all five d orbitals). Closed-shell ligands contribute no unpaired spin
(anionic donors are drawn in their bound protonation state, CO is normalised to
neutral, etc.), so total ``--uhf`` = unpaired d electrons.

This is a pragmatic default, not a substitute for the user knowing their system;
that is exactly why the spin override exists.
"""

from __future__ import annotations

from .model import Geometry, Spin

# Group number (valence electrons of the neutral atom) for supported metals.
_GROUP = {
    # Group 3 (d-block): M(III) -> d0. Sc/Y relax with xtb; La is skipped as f-block
    # (inputs.is_f_block) but is listed so the spin model resolves cleanly instead of
    # falling back to uhf=0 with a warning. True lanthanides (Ce-Lu) have partially
    # filled f shells that the group-minus-oxidation d-count model does not describe,
    # so they are intentionally absent (xtb is skipped for them anyway).
    "Sc": 3, "Y": 3, "La": 3,
    "Ti": 4, "V": 5, "Cr": 6, "Mn": 7, "Fe": 8, "Co": 9, "Ni": 10, "Cu": 11, "Zn": 12,
    "Zr": 4, "Nb": 5, "Mo": 6, "Tc": 7, "Ru": 8, "Rh": 9, "Pd": 10, "Ag": 11, "Cd": 12,
    "Hf": 4, "Ta": 5, "W": 6, "Re": 7, "Os": 8, "Ir": 9, "Pt": 10, "Au": 11, "Hg": 12,
}

# Main-group (p-block) metal / metalloid centres: number of s+p valence electrons
# of the NEUTRAL atom (group 13 -> 3 ... group 16 -> 6). The transition-metal
# crystal-field d-count model does not apply here — these have no partially filled
# d shell — so unpaired electrons come from the parity of the remaining s+p valence
# electrons after ionisation (a closed s2/s2p6 shell -> 0). Covers the p-block
# centres that occur as coordination-complex metals in the CSD (Sn, Pb, Bi, ...).
_MAIN_GROUP_VALENCE = {
    "Al": 3, "Ga": 3, "In": 3, "Tl": 3,   # group 13
    "Ge": 4, "Sn": 4, "Pb": 4,            # group 14
    "As": 5, "Sb": 5, "Bi": 5,            # group 15
    "Se": 6, "Te": 6, "Po": 6,            # group 16
}

# Low-spin d-orbital splitting per geometry: orbital-group sizes in energy order.
_LS_SPLITTING = {
    Geometry.OCTAHEDRAL: (3, 2),          # t2g < eg
    Geometry.TETRAHEDRAL: (2, 3),         # e < t2
    Geometry.SQUARE_PLANAR: (2, 1, 1, 1),  # (dxz,dyz) < dz2 < dxy < dx2-y2
    Geometry.LINEAR: (2, 2, 1),           # (dxz,dyz) < (dxy,dx2-y2) < dz2
    # Approximate (C2v lifts the pairs): bent CN2 centres are almost all d10 or main group,
    # where the ordering does not change the unpaired count.
    Geometry.BENT: (2, 2, 1),
    # CN 3/5/7-9 were missing, so they fell back to five degenerate orbitals: a LOW-spin
    # request came out HIGH spin (Ir(III) CN5 as a quintet, Fe(CO)5 as a triplet).
    Geometry.TRIGONAL_PLANAR: (2, 1, 2),  # e''(dxz,dyz) < a1'(dz2) < e'(dxy,dx2-y2)
    # CN5: the t2g-like (dxz,dyz,dxy) lie close together, so they fill as one group, then dz2,
    # then dx2-y2 (d3 3, d4 2, d5 1, d6 0, d7 1, d8 0, d9 1 unpaired). TBP uses the same LOW-spin
    # pattern: CN5 is fluxional (Berry) and a low-spin centre takes the square-pyramidal pairing;
    # the bare TBP split (e''^4 e'^2) would make d6 a triplet, which is exactly why d6
    # five-coordinates (RuCl2(PPh3)3) are square-pyramidal singlets.
    Geometry.SQUARE_PYRAMIDAL: (3, 1, 1),
    Geometry.TRIGONAL_BIPYRAMIDAL: (3, 1, 1),
    Geometry.PENTAGONAL_BIPYRAMIDAL: (2, 2, 1),  # e1''(dxz,dyz) < e2'(dxy,dx2-y2) < a1'(dz2)
    Geometry.SQUARE_ANTIPRISM: (1, 2, 2),  # a1(dz2) < e2(dxy,dx2-y2) < e3(dxz,dyz)
    Geometry.DODECAHEDRAL: (1, 1, 2, 1),  # b1(dx2-y2) < a1(dz2) < e(dxz,dyz) < b2(dxy)
    # Approximate: one low orbital as for the CN8 polyhedra. Real CN9 d-block centres are
    # almost all d0-d1 ([ReH9]2-, Y/La), where the ordering does not change the count.
    Geometry.TRICAPPED_TRIGONAL_PRISM: (1, 2, 2),
    Geometry.PIANO_STOOL_CP: (3, 2),      # pseudo-octahedral
    Geometry.PIANO_STOOL_ARENE: (3, 2),
    # Metallocenes: three low-lying d orbitals (e2g + a1g) below two high (e1g*),
    # so a pseudo-octahedral (3, 2) split reproduces the familiar counts —
    # ferrocene Fe(II) d6 low-spin -> 0 unpaired; Cp2TiCl2 Ti(IV) d0 -> 0.
    Geometry.METALLOCENE: (3, 2),
    Geometry.METALLOCENE_BENT: (3, 2),
}


class SpinError(ValueError):
    """Raised when the d-electron count cannot be determined for a metal."""


def d_electron_count(symbol: str, oxidation_state: int) -> int:
    """d-electron count = group number − oxidation state."""
    if symbol not in _GROUP:
        raise SpinError(f"No group number for metal {symbol!r}; set spin/uhf explicitly.")
    n = _GROUP[symbol] - oxidation_state
    if not 0 <= n <= 10:
        raise SpinError(f"Implausible d-electron count {n} for {symbol}({oxidation_state}).")
    return n


def _main_group_unpaired(symbol: str, oxidation_state: int) -> int:
    """Unpaired electrons for a p-block (main-group) centre: parity of the s+p
    valence electrons left after ionisation. Even -> closed shell -> 0 unpaired
    (the common case: Sn(II)/Sn(IV), Bi(III), Ga(III), Pb(II) are all diamagnetic);
    odd -> one unpaired (a main-group radical centre)."""
    valence = _MAIN_GROUP_VALENCE[symbol] - oxidation_state
    if valence < 0:
        raise SpinError(
            f"Oxidation state {oxidation_state} removes more than the {symbol} "
            f"valence shell; set spin/uhf explicitly."
        )
    return valence % 2


def has_stereo_active_lone_pair(symbol: str, oxidation_state: int) -> bool:
    """True for a p-block centre carrying a stereochemically active ns² lone pair.

    The classic "inert pair" cations — Sn(II), Pb(II), Ge(II), Sb(III), Bi(III),
    As(III), Se(IV), Te(IV), Tl(I), In(I) — keep their ns² pair after losing only the
    np electrons, i.e. the remaining s+p valence count is exactly 2. That lone pair
    occupies a coordination position (VSEPR), lowering the polyhedron symmetry — e.g.
    CN5 is square-pyramidal, not trigonal-bipyramidal (BiCl3Br2, EPAQOE). Returns
    False for main-group centres with no lone pair (Al(III), Ga(III), Sn(IV), Bi(V))
    and for anything outside the main-group valence table."""
    v = _MAIN_GROUP_VALENCE.get(symbol)
    return v is not None and (v - oxidation_state) == 2


def d_count_or_none(symbol: str, oxidation_state: int) -> int | None:
    """d-electron count, or ``None`` when it can't be determined (main-group /
    unlisted metals, implausible values). Convenience for geometry defaulting,
    which treats an unknown d-count as "not d8" -> the non-square-planar default."""
    try:
        return d_electron_count(symbol, oxidation_state)
    except SpinError:
        return None


def possible_missing_hydrides(symbol: str, oxidation_state: int, n_donors: int) -> int:
    """Estimate hydride ligands likely absent from the mined coordination sphere.

    X-ray CIFs seldom locate M–H, so the CSD-derived donor lists in this dataset carry NO
    hydrides (0 of 35 956 entries) — a hydrido complex comes through with its CN too low and
    sometimes the wrong oxidation state (VOFRAJ, named a Ni(II) hydride, mines as CN3 O,P,P).
    Flag the shortfall by the 18-electron rule (ionic counting: d-count + 2·CN electrons), with
    the standard 16-electron target for a d8 centre (square-planar Ni/Pd/Pt(II), Rh/Ir(I)). A
    non-negative EVEN shortfall of ≥2 is reported as that many candidate M–H (each hydride is one
    2-electron X-donor). A heuristic pointer only — d0–d2 early metals and f-block are exempt (they
    routinely sit below 18e without a hydride), so it is quiet on those rather than crying wolf."""
    d = d_count_or_none(symbol, oxidation_state)
    if d is None or d <= 2:                     # main-group / early d0-d2 -> 18e rule doesn't bite
        return 0
    target = 16 if d == 8 else 18               # d8 saturates at 16e (square planar)
    shortfall = target - (d + 2 * n_donors)
    return shortfall // 2 if shortfall >= 2 and shortfall % 2 == 0 else 0


def _unpaired(n_electrons: int, groups: tuple[int, ...]) -> int:
    """Unpaired electrons after filling ``groups`` (orbital counts, energy order)."""
    remaining = n_electrons
    unpaired = 0
    for g in groups:
        take = min(remaining, 2 * g)
        singly = min(take, g)          # orbitals singly occupied (Hund within group)
        paired = max(take - g, 0)      # electrons that pair up
        unpaired += singly - paired
        remaining -= take
        if remaining <= 0:
            break
    return unpaired


def unpaired_electrons(symbol: str, oxidation_state: int, geometry: Geometry, spin: Spin,
                       n_terminal_multiple: int = 0) -> int:
    """Unpaired electrons for a metal centre in a geometry and spin state.

    Main-group (p-block) centres are closed-shell by valence-electron parity (the
    d-count crystal-field model does not apply and ``spin``/``geometry`` are
    irrelevant to them); transition metals use the d-electron crystal-field model.

    ``n_terminal_multiple`` counts terminal oxo/nitrido donors (M=O / M≡N). Their
    strong π-donation pushes dxz/dyz (M–L π*) far above dxy, so a low-spin d2 centre
    pairs both electrons in dxy: Re(V)=O, Tc(V)=O, trans-[ReO2(PR3)4]+, Os(VI)O2 and
    Re(V)≡N are diamagnetic, not the t2g triplet the plain octahedral split gives
    (the "oxo wall" picture). Occupying the π* instead weakens the M=O bonds."""
    if symbol in _MAIN_GROUP_VALENCE:
        return _main_group_unpaired(symbol, oxidation_state)
    n = d_electron_count(symbol, oxidation_state)
    if spin is Spin.HIGH:
        return _unpaired(n, (5,))  # all five d orbitals treated degenerate
    if n == 2 and n_terminal_multiple > 0:
        return 0                   # d2 paired in the isolated dxy
    groups = _LS_SPLITTING.get(geometry, (5,))
    return _unpaired(n, groups)
