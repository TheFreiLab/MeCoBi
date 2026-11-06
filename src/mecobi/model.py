"""Core data model for MeCoBi.

Mononuclear only for v1 (exactly one metal centre), but the model leaves room
for polynuclear later. Heteroleptic is supported: multiplicity is
expressed by repeating a ligand entry, never by a count field.

These dataclasses are the shared contract between every pipeline stage and
between the local library and the web layer. Keep them free of stk/rdkit/torch
imports so they stay cheap to construct and serialise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Geometry(str, Enum):
    """Supported coordination geometries.

    Covers CN 2-9; the enum/registry is data-driven,
    never a hardcoded "only 2/4/6" — new coordination numbers slot in as
    members here.
    """

    LINEAR = "linear"                    # CN 2
    BENT = "bent"                        # CN 2, one chelate (the linear sites are trans)
    TRIGONAL_PLANAR = "trigonal_planar"  # CN 3
    SQUARE_PLANAR = "square_planar"      # CN 4
    TETRAHEDRAL = "tetrahedral"          # CN 4
    SQUARE_PYRAMIDAL = "square_pyramidal"            # CN 5
    TRIGONAL_BIPYRAMIDAL = "trigonal_bipyramidal"    # CN 5
    OCTAHEDRAL = "octahedral"            # CN 6
    PENTAGONAL_BIPYRAMIDAL = "pentagonal_bipyramidal"        # CN 7
    SQUARE_ANTIPRISM = "square_antiprism"                    # CN 8
    DODECAHEDRAL = "dodecahedral"                            # CN 8
    TRICAPPED_TRIGONAL_PRISM = "tricapped_trigonal_prism"    # CN 9
    # Metallocenes: two eta-bound Cp/arene caps sandwiching the metal. Each cap
    # is a facial triad (denticity 3), so the summed CN (6, or 8 with two legs)
    # would mislabel them — they route via a dedicated geometry, not CN.
    METALLOCENE = "metallocene"              # parallel sandwich, M(cap)2
    METALLOCENE_BENT = "metallocene_bent"    # bent Cp2M(X)(Y), e.g. Cp2TiCl2
    # Half-sandwich / piano-stool: arene or Cp occupies 3 sites (hardcoded
    # denticity 3) alongside other donors.
    PIANO_STOOL_CP = "piano_stool_cp"
    PIANO_STOOL_ARENE = "piano_stool_arene"


class Spin(str, Enum):
    """Spin state. Default low spin; override surfaced in UI/API.

    Resolved to the number of unpaired electrons passed to xtb via ``--uhf``.
    """

    LOW = "low"
    HIGH = "high"


@dataclass(frozen=True)
class Metal:
    """The single metal centre.

    Attributes:
        symbol: Element label, e.g. ``"Ir"``.
        oxidation_state: Required; used for total-charge maths.
    """

    symbol: str
    oxidation_state: int


@dataclass
class Ligand:
    """One ligand entry (free-ligand SMILES; the system infers binding).

    Repetition expresses multiplicity — two pyridines are two Ligand entries
    with the same SMILES. ``coord_atoms``/``denticity`` are filled
    in by the perception stage; ``donor_override`` lets the 2D donor-correction
    panel or a caller pin the donors, bypassing the trim rule.
    """

    smiles: str
    coord_atoms: list[int] | None = None      # 0-based, no explicit Hs
    denticity: int | None = None
    is_arene: bool = False
    formal_charge: int = 0
    donor_override: list[int] | None = None
    # Pi-hapticity: each entry is the atom indices of one eta-bonded pi-site
    # (an eta2 alkene/alkyne = a [C, C] pair) that occupies a SINGLE coordination
    # site at the bond midpoint. Set by perception; assembly binds the pair as one
    # functional group (bonder centroid -> the vertex). Empty for pure-sigma ligands.
    pi_sites: list[list[int]] = field(default_factory=list)

    @property
    def effective_donors(self) -> list[int] | None:
        return self.donor_override if self.donor_override is not None else self.coord_atoms


@dataclass
class Complex:
    """One whole complex = one CSV row.

    A geometry and isomer choice are attached downstream. ``name`` base-source
    is DEFERRED: optional here, auto-derived if absent.
    """

    metal: Metal
    ligands: list[Ligand]
    spin: Spin = Spin.LOW
    name: str | None = None
    geometry: Geometry | None = None
    index: int | None = None
    # Optional donor-index isomer notation ("mode 3"): pins which
    # SMILES atoms coordinate and/or which coordination site each donor takes, so
    # one specific isomer is built. Parsed lazily by the pipeline once perception
    # and geometry are resolved. See :func:`mecobi.isomers.parse_isomer_notation`.
    isomer_spec: str | None = None

    @property
    def coordination_number(self) -> int | None:
        """CN = sum of all ligand denticities."""
        if any(l.denticity is None for l in self.ligands):
            return None
        return sum(l.denticity for l in self.ligands)  # type: ignore[misc]

    @property
    def total_charge(self) -> int:
        """Total charge = metal oxidation state + sum of ligand formal charges."""
        return self.metal.oxidation_state + sum(l.formal_charge for l in self.ligands)


@dataclass
class BuildResult:
    """Result of building one isomer of one complex.

    When multiple isomers are relaxed with xtb, the pipeline fills the energy
    fields and orders results lowest-energy first: ``total_energy`` is the GFN2
    total energy (Hartree), ``relative_energy_kcal`` is the energy above the
    lowest isomer (kcal/mol; 0.0 for the winner), and ``is_lowest_energy`` marks
    it. All stay ``None``/``False`` when relaxation is off or the energy could not
    be read (e.g. a dissociated isomer, whose energy is not comparable). An isomer
    with ``connectivity_ok=False`` keeps its ``total_energy`` but is not ranked:
    it is ordered after the valid isomers, with ``relative_energy_kcal=None``.
    """

    complex: Complex
    isomer_label: str | None
    xyz_path: str | None = None
    # Extra structure files written beside the .xyz (``.mol`` / ``.pdb``), one path per requested
    # format including the .xyz itself. Empty unless ``build_complex(formats=...)`` asked for more
    # than xyz. See :func:`mecobi.export.write_formats`.
    extra_paths: list[str] = field(default_factory=list)
    total_charge: int = 0
    uhf: int = 0
    warnings: list[str] = field(default_factory=list)
    total_energy: float | None = None
    relative_energy_kcal: float | None = None
    is_lowest_energy: bool = False
    # True coordination bonds from the assembled topology (0-based indices into the
    # .xyz), so the 3D viewer can draw exactly the metal-donor bonds instead of
    # guessing them by distance.
    metal_index: int | None = None
    donor_indices: list[int] = field(default_factory=list)
    # False when xtb relaxation changed the molecular connectivity vs the assembled
    # graph (a ligand-ligand fusion or a fragmentation/collapse) -- the build is still
    # returned, but flagged so callers/benchmarks can reject it. True when relaxation
    # preserved the graph or was not run. See pipeline._new_or_broken_bonds.
    connectivity_ok: bool = True
