"""Coordination number -> geometry proposal.

CN = sum of ligand denticities. Supported CN are the keys of
``CN_TO_GEOMETRIES`` (currently 2, 3, 4, 5, 6, 7, 8, 9). Where a CN maps to
multiple geometries (CN 4 -> {square_planar, tetrahedral}, CN 8 ->
{square_antiprism, dodecahedral}) both are offered as options rather than
silently chosen. If the summed denticity matches no supported geometry ->
**hard error**, never silent nearest-fit (invariant 3).

The registry is data-driven (``CN_TO_GEOMETRIES``), never a hardcoded "only
2/4/6": new coordination numbers slot in by adding a key. CN 10+ (bicapped
square-antiprism / other high-CN families) remain to be added.
"""

from __future__ import annotations

from .model import Geometry

# CN -> geometries offered (first is the default). Where a CN has two common
# geometries both are offered rather than silently chosen.
CN_TO_GEOMETRIES: dict[int, tuple[Geometry, ...]] = {
    2: (Geometry.LINEAR, Geometry.BENT),
    3: (Geometry.TRIGONAL_PLANAR,),
    4: (Geometry.SQUARE_PLANAR, Geometry.TETRAHEDRAL),
    5: (Geometry.TRIGONAL_BIPYRAMIDAL, Geometry.SQUARE_PYRAMIDAL),
    6: (Geometry.OCTAHEDRAL,),
    7: (Geometry.PENTAGONAL_BIPYRAMIDAL,),
    8: (Geometry.SQUARE_ANTIPRISM, Geometry.DODECAHEDRAL),
    9: (Geometry.TRICAPPED_TRIGONAL_PRISM,),
}


class DenticityMismatchError(ValueError):
    """Raised when a CN has no supported geometry (invariant 3: hard error)."""


def geometries_for_cn(cn: int) -> tuple[Geometry, ...]:
    """Return the geometries offered for a coordination number.

    Raises:
        DenticityMismatchError: if ``cn`` is unsupported.
    """
    if cn not in CN_TO_GEOMETRIES:
        cns = sorted(CN_TO_GEOMETRIES)
        raise DenticityMismatchError(
            f"No supported geometry for coordination number {cn} "
            f"(supported: {cns[0]} to {cns[-1]})."
        )
    return CN_TO_GEOMETRIES[cn]


def propose_geometry(
    cn: int, d_count: int | None = None, denticities: "list[int] | None" = None,
    lone_pair: bool = False,
) -> Geometry:
    """Return the default proposed geometry for a CN.

    Most CNs have a single geometry; **CN 4** is the one where an input-only rule
    materially beats chance (validated on the CSD structural benchmark):

    * **CN 4** — square-planar when the centre is **d8** (Ni(II), Pd(II), Pt(II),
      Au(III), Rh(I), Ir(I)) **or** the four donors come from a strongly chelating
      set (**≤2 ligands** — a single tetradentate or a bis-bidentate/tridentate+mono
      pair: salen, porphyrin, cyclam, bis-acac …) **on a d4–d9 centre**. Everything
      else — four separate monodentates, and chelates on d0–d3, d10 or main-group
      centres (Ti(IV) bis(ene-diamide), Zn(acac)2) — defaults to **tetrahedral**. On the
      6,402 CN4 benchmark crystals this scores 80.7% (d8 alone 71.4%, the d-count-blind
      chelate rule 73.0%). Both are still offered, so the user/isomer model can
      override. ``denticities`` is the per-ligand denticity list; when it is not
      supplied the rule falls back to d8-only.
    * **CN 2** — linear for two monodentates. A single chelating ligand (``denticities``
      holds a 2) is **bent** on main-group and d8 centres (Ge(II)/Sn(II) beta-diketiminates,
      Tl(I) amidinates: donor-M-donor median 84 deg over 143 CSD crystals) and **linear,
      trans-spanning** on d10 centres (Ag(I), Cu(I), Au(I), Pd(0), Pt(0) with long
      diphosphines or macrocycles: median 163 deg over 32).
    * **CN 5** — trigonal-bipyramidal vs square-pyramidal is **not** predictable
      from 2D inputs for transition metals (Berry pseudorotation; benchmark shows
      every cheap feature splits ~50/50), so we default to the **majority
      (trigonal-bipyramidal)**. The exception is a main-group centre with a
      stereochemically active ns² lone pair (``lone_pair=True``: Bi(III), Sn(II),
      Sb(III), Pb(II), Te(IV) …): the lone pair caps an octahedron, so the five
      donors are **square-pyramidal** (BiCl3Br2). This one IS predictable from the
      metal, so we honour it.

    ``d_count`` is the metal's d-electron count (:func:`mecobi.spin.d_electron_count`,
    or ``None`` when it cannot be determined — main-group / unlisted metals).
    ``lone_pair`` flags a stereochemically active ns² lone pair
    (:func:`mecobi.spin.has_stereo_active_lone_pair`).
    """
    options = geometries_for_cn(cn)
    if cn == 2 and denticities is not None and any(d >= 2 for d in denticities):
        return Geometry.LINEAR if d_count == 10 else Geometry.BENT
    if cn == 4:
        # The chelate rule only holds for d4-d9: on the CSD benchmark's 6,402 CN4 crystals,
        # <=2-ligand complexes are square planar 931:332 at d4-d9 but tetrahedral at d0 (63:0),
        # d1-d3 (29:8), d10 (260:177) and main group (336:8). Ti(IV) bis(ene-diamide) (HOLMEC)
        # was built square planar. Accuracy 73.0% -> 80.7%.
        chelated = (denticities is not None and len(denticities) <= 2
                    and d_count is not None and 4 <= d_count <= 9)
        return Geometry.SQUARE_PLANAR if (d_count == 8 or chelated) else Geometry.TETRAHEDRAL
    if cn == 5 and lone_pair:
        return Geometry.SQUARE_PYRAMIDAL
    return options[0]


def detect_metallocene(denticities, cap_flags) -> Geometry | None:
    """Detect a metallocene from its ligand set, else return ``None``.

    A metallocene has exactly two η-bound caps (Cp/arene, each ONE centroid coordination site,
    denticity 1). With no other donors it is a parallel sandwich (:attr:`Geometry.METALLOCENE`,
    e.g. ferrocene); with only monodentate legs besides the two caps it is a bent metallocene
    (:attr:`Geometry.METALLOCENE_BENT`, e.g. Cp2TiCl2). Any other mix returns ``None``.

    ``cap_flags[i]`` marks ligand *i* as an η-cap (a π-site of ≥ 3 atoms). Metallocenes route by
    this detector rather than by coordination number: the two-cap sandwich has its own placement.
    """
    caps = [i for i, is_cap in enumerate(cap_flags) if is_cap]
    if len(caps) != 2:
        return None
    others = [d for i, d in enumerate(denticities) if i not in caps]
    if not others:
        return Geometry.METALLOCENE
    if all(d == 1 for d in others):
        return Geometry.METALLOCENE_BENT
    return None


def detect_piano_stool(cap_ring_sizes) -> Geometry | None:
    """The piano-stool geometry for a ONE-cap ligand set, else ``None``.

    A single centroid η-cap plus its legs is a piano stool (half sandwich):
    :attr:`Geometry.PIANO_STOOL_CP` for a 5-ring cap, :attr:`Geometry.PIANO_STOOL_ARENE`
    for anything larger. ``cap_ring_sizes`` is one ring size per η-cap.

    This is a *label*, not a placement geometry — see :func:`spin_geometry` for the spin
    model, and note that neither member appears in any site-vector or topology table. A
    build request carrying one is re-proposed onto its CN geometry by ``build_complex``.
    """
    if len(cap_ring_sizes) != 1:
        return None
    return (Geometry.PIANO_STOOL_CP if cap_ring_sizes[0] == 5
            else Geometry.PIANO_STOOL_ARENE)


def spin_geometry(placement: Geometry, cap_ring_sizes, cn: int) -> Geometry:
    """The geometry whose crystal-field splitting applies, which is NOT always the one a
    centroid-cap complex is *placed* on.

    A centroid η-cap is one coordination site for placement but donates three (a facial
    triad) to the metal's d-orbital field, so a capped complex's CN understates its field
    and the CN-derived geometry splits the d electrons on the wrong pattern:

    * **two caps, bare** — placed LINEAR (the centroid model has no (1,1) sandwich topology),
      but split as a :attr:`Geometry.METALLOCENE`; else ferrocene Fe(II) d6 comes out a
      linear (2,2,1) triplet (uhf 2) instead of diamagnetic (uhf 0).
    * **one cap** — a piano stool. Placed on its CN geometry (CN 4 for Cp*Ir(N^O)Cl or
      CpMn(CO)3 → tetrahedral), but the cap's facial triad makes it *pseudo-octahedral*, so
      it splits (3, 2). Without this, every Cp/arene half-sandwich reaches xtb as a spurious
      triplet — d6 Ir(III)/Ru(II)/Mn(I) piano stools are diamagnetic.

    Two caps carrying legs already route to :attr:`Geometry.METALLOCENE_BENT` via
    :func:`detect_metallocene`, which splits (3, 2) — those pass through unchanged.

    ``cap_ring_sizes`` is one ring size per η-cap (5 → Cp, otherwise arene); it only picks
    which piano-stool member to name, both splitting pseudo-octahedrally. Placement is never
    affected: these geometries appear in no site/topology table, only in the spin model.
    """
    if len(cap_ring_sizes) == 2 and cn == 2:
        return Geometry.METALLOCENE
    return detect_piano_stool(cap_ring_sizes) or placement
