"""FastAPI application for MeCoBi.

Endpoints (all orchestration; chemistry is in the core):
    POST /api/parse            — CSV -> parsed + perceived rows for the table.
    POST /api/build            — one complex -> built .xyz (synchronous; simple use).
    POST /api/jobs             — submit a batch build (async).
    GET  /api/jobs/{job_id}    — job status + results (the private job URL).
    GET  /api/file/{job}/{name} — download / stream an .xyz.
    GET  /                     — the static frontend.

The async job store, serial worker, rate limiting and 24 h cleanup live in
:mod:`mecobi.web.jobs`; heavier OS-level sandboxing is a Linux deploy concern.
"""

from __future__ import annotations

import os
import re
import tempfile
import threading
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from pydantic import BaseModel, Field

from .. import geometry, inputs, perception, pipeline, spin
from ..model import Complex, Geometry, Ligand, Metal, Spin
from . import jobs
from .limits import BodySizeLimit

_STATIC = Path(__file__).resolve().parent / "static"
_DATA = Path(tempfile.gettempdir()) / "mecobi_data"
_RESULTS = _DATA / "results"
_DATA.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Public-API resource limits. Centralized here and env-overridable.
# IMPORTANT: these are application-level guards, NOT a substitute for deployment
# isolation — production must still cap CPU, memory, filesystem and subprocess use
# at the process/container level (e.g. cgroups/ulimit/systemd, an xtb wall-clock
# and core cap, and a read-only/quota'd results volume).
# --------------------------------------------------------------------------- #

def _env_int(name: str, default: int) -> int:
    import os
    try:
        return int(os.environ[name])
    except (KeyError, ValueError):
        return default


MAX_COMPLEXES_PER_JOB = _env_int("MECOBI_MAX_COMPLEXES", 1000)
# Unfinished work the queue admits, in STRUCTURES (one isomer of one complex): an all-isomers
# row counts each isomer it will build (jobs.workload_units). The old complex-count variable
# is still read as a fallback so an existing deployment keeps its configured size.
MAX_PENDING_STRUCTURES = _env_int("MECOBI_MAX_PENDING_STRUCTURES",
                                  _env_int("MECOBI_MAX_PENDING_COMPLEXES", 1000))
LONG_JOB_SECONDS = _env_int("MECOBI_LONG_JOB_SECONDS", 600)
MAX_LIGANDS_PER_COMPLEX = _env_int("MECOBI_MAX_LIGANDS", 16)
MAX_SMILES_LEN = _env_int("MECOBI_MAX_SMILES_LEN", 2000)
MAX_ATOMS_PER_LIGAND = _env_int("MECOBI_MAX_ATOMS_PER_LIGAND", 400)
MAX_ATOMS_PER_COMPLEX = _env_int("MECOBI_MAX_ATOMS_PER_COMPLEX", 1000)
XTB_TIMEOUT_MIN_S = 5
XTB_TIMEOUT_MAX_S = _env_int("MECOBI_XTB_TIMEOUT_MAX_S", 1800)
MAX_ISOMERS_PER_COMPLEX = _env_int("MECOBI_MAX_ISOMERS", 64)
# CN > 6 only: a CN8/9 isomer takes ~12 s just to assemble, so one "all isomers" click at 64
# would tie up the single build worker for ~13 min before any xtb.
MAX_ISOMERS_HIGH_CN = _env_int("MECOBI_MAX_ISOMERS_HIGH_CN", 16)
MAX_CSV_BYTES = _env_int("MECOBI_MAX_CSV_BYTES", 4_000_000)
MAX_XYZ_BYTES = _env_int("MECOBI_MAX_XYZ_BYTES", 5_000_000)
MAX_REVERSE_EXPORT_ITEMS = _env_int("MECOBI_MAX_EXPORT_ITEMS", 1000)
MAX_BODY_BYTES = _env_int("MECOBI_MAX_BODY_BYTES", 8_000_000)
# "Download all" archive bounds, checked BEFORE compressing. A full queue is 1000 structures x
# three formats of a few kB each, so the defaults leave ample room for any real job.
MAX_ZIP_FILES = _env_int("MECOBI_MAX_ZIP_FILES", 5000)
MAX_ZIP_BYTES = _env_int("MECOBI_MAX_ZIP_BYTES", 250_000_000)  # total uncompressed
ZIP_CONCURRENCY = _env_int("MECOBI_ZIP_CONCURRENCY", 2)
# A finished job's archive is built once and kept in its directory (removed with it by the
# 24-hour retention sweep); later downloads are served from disk without recompressing.
_ARCHIVE_NAME = "_download.zip"
_STRUCTURE_SUFFIXES = {".xyz", ".mol", ".pdb"}
# Interactive preview concurrency (the donor panel fires one /api/depict per
# ligand at once — up to MAX_LIGANDS_PER_COMPLEX in a single burst). The cap
# bounds CPU use; requests over it QUEUE for up to the timeout rather than being
# rejected, so a normal per-ligand burst (each depiction is milliseconds) always
# renders. Only a sustained overload past the timeout returns 503.
PREVIEW_CONCURRENCY = _env_int("MECOBI_PREVIEW_CONCURRENCY", 4)
PREVIEW_SLOT_TIMEOUT_S = _env_int("MECOBI_PREVIEW_SLOT_TIMEOUT_S", 10)
# Per-submitter request budget. Tunable without rebuilding the image: the right
# value only shows up under real traffic, and behind a reverse proxy it is only
# meaningful once forwarded client IPs are trusted (see /api/whoami).
RATE_MAX_PER_WINDOW = _env_int("MECOBI_RATE_MAX", 20)
RATE_WINDOW_S = _env_int("MECOBI_RATE_WINDOW_S", 60)
# How long a synchronous build waits for the shared build slot before giving up.
# The queue worker takes the same slot on every poll (every 0.4 s) just to look
# for work, so a non-blocking grab loses that race at random even on an idle
# server. Waiting out one poll cycle costs nothing and only a genuinely occupied
# slot — another build actually running — still 503s.
BUILD_SLOT_TIMEOUT_S = _env_int("MECOBI_BUILD_SLOT_TIMEOUT_S", 2)


def _heavy_atom_count(smiles: str) -> int:
    """Heavy-atom count of a ligand SMILES (0 if unparseable — bad SMILES are
    caught leniently downstream; here we only need a size guard)."""
    from rdkit import Chem
    mol = Chem.MolFromSmiles(smiles, sanitize=False)
    return mol.GetNumAtoms() if mol is not None else 0


def _validate_build_request(req: "BuildRequest") -> None:
    """Enforce per-complex resource limits before any assembly/relax work.

    Raises HTTP 400 with a specific message on the first breach.
    """
    if not XTB_TIMEOUT_MIN_S <= req.xtb_timeout_s <= XTB_TIMEOUT_MAX_S:
        raise HTTPException(
            status_code=400,
            detail=f"xtb_timeout_s must be between {XTB_TIMEOUT_MIN_S} and {XTB_TIMEOUT_MAX_S} s.",
        )
    _validate_ligands(req.ligands)


def _validate_geometry(name: str) -> Geometry:
    """Resolve a requested geometry name, or raise HTTP 400.

    Kept separate from the build itself so a request can be rejected as invalid
    before it competes for the build slot: a malformed request must not depend
    on how busy the server is.
    """
    try:
        return Geometry(name)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown geometry {name!r}")


def _validate_ligands(ligands) -> None:
    """Shared size validation before inference, enumeration or assembly."""
    if len(ligands) > MAX_LIGANDS_PER_COMPLEX:
        raise HTTPException(
            status_code=400, detail=f"Too many ligands (max {MAX_LIGANDS_PER_COMPLEX}).")
    total_atoms = 0
    for lig in ligands:
        if len(lig.smiles) > MAX_SMILES_LEN:
            raise HTTPException(
                status_code=400, detail=f"Ligand SMILES too long (max {MAX_SMILES_LEN} chars).")
        n = _heavy_atom_count(lig.smiles)
        if n > MAX_ATOMS_PER_LIGAND:
            raise HTTPException(
                status_code=400, detail=f"Ligand too large (max {MAX_ATOMS_PER_LIGAND} atoms).")
        total_atoms += n
    if total_atoms > MAX_ATOMS_PER_COMPLEX:
        raise HTTPException(
            status_code=400, detail=f"Complex too large (max {MAX_ATOMS_PER_COMPLEX} atoms).")


def _preview_guard(request: Request):
    """Bound interactive perception work separately from build submissions.

    The donor panel opens one preview per ligand simultaneously, so a normal
    complex bursts several /api/depict|perceive calls at once — more than the
    concurrency cap. Those excess requests QUEUE for up to PREVIEW_SLOT_TIMEOUT_S
    (each preview is milliseconds, so the burst drains almost immediately) rather
    than being rejected; only a genuine sustained overload past the timeout 503s.
    """
    if not request.app.state.preview_rate.allow(jobs.submitter_id(request)):
        raise HTTPException(429, "Too many preview requests; try again shortly.")
    slot = request.app.state.preview_slots
    if not slot.acquire(timeout=PREVIEW_SLOT_TIMEOUT_S):
        raise HTTPException(503, "The server is processing other previews; try again shortly.",
                            headers={"Retry-After": "2"})
    try:
        yield
    finally:
        slot.release()


def _check_xyz_size(xyz: str) -> None:
    if len(xyz.encode("utf-8", "ignore")) > MAX_XYZ_BYTES:
        raise HTTPException(status_code=413, detail=f"XYZ too large (max {MAX_XYZ_BYTES} bytes).")


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #

class LigandOut(BaseModel):
    smiles: str
    denticity: int | None = None
    coord_atoms: list[int] | None = None
    is_arene: bool = False
    # Centroid η-caps: each inner list is one ring bound as a single site at its
    # centroid (denticity 1). The Assign scene reads this to render a cap as ONE
    # "η" donor slot rather than N σ-donors, and to skip the cis rule for its site.
    pi_sites: list[list[int]] = []
    formal_charge: int = 0
    warning: str | None = None


class ComplexOut(BaseModel):
    name: str | None = None
    metal: str
    oxidation_state: int | None = None  # None only for a row that failed to parse
    ligands: list[LigandOut]
    coordination_number: int | None = None
    geometry_options: list[str] = Field(default_factory=list)
    proposed_geometry: str | None = None
    total_charge: int = 0
    supported: bool = True
    error: str | None = None
    warning: str | None = None
    # True when a SINGLE ligand carries two Cp rings (an ansa-metallocene, a
    # Cp+pyridine ligand) that aren't set as centroid η-caps: auto-perception marks
    # only one ring, silently under-coordinating it, so a batch (Build all) would
    # build a wrong structure. The user should select both rings as caps first;
    # Build all skips these. Ordinary metallocenes (separate single-ring Cp ligands)
    # perceive fine and are NOT flagged.
    needs_cap_selection: bool = False


class ParseRequest(BaseModel):
    csv: str


class LigandIn(BaseModel):
    smiles: str
    coord_atoms: list[int] | None = None  # donor override from the correction panel
    is_arene: bool = False


class BuildOptions(BaseModel):
    """GUI "Advanced options": pre-xtb geometry guards + xtb constraints. Each maps to a
    build_complex toggle; defaults mirror build_complex, so leaving them alone is the standard build.
    """
    # pre-xtb placement guards
    orient_bulky: bool = True
    reposition_donors: bool = True
    reposition_polydentates: bool = False
    clear_metal_region: bool = True
    declash_torsion: bool = True
    mchammer: bool = True
    reembed_crowded: bool = True
    # xtb-time constraints / guards
    linear_restraint: bool = True
    haptic_guard: bool = True
    planar_guard: bool = True
    antifusion_guard: bool = True
    oxo_antifusion_floors: bool = False
    metal_surrogate: bool = False


class BuildRequest(BaseModel):
    name: str | None = None
    metal: str
    oxidation_state: int
    ligands: list[LigandIn]
    geometry: str
    all_isomers: bool = False
    # Split stereoisomers (Delta/Lambda enantiomers + asymmetric-chelate donor
    # direction) when enumerating all isomers. Ignored unless all_isomers.
    stereo: bool = True
    # Explicit isomer from the 3D scene: ligand index -> vertex ids (legacy,
    # fixed-topology). Overrides all_isomers/default when present.
    assignment: dict[str, list[int]] | None = None
    # Explicit isomer as coordination-site ids: ligand index -> ordered site ids
    # (dynamic site model, §7.2). Takes precedence over `assignment`.
    site_assignment: dict[str, list[int]] | None = None
    # Donor-index isomer notation string ("mode 3"), e.g.
    # "0:0,2;1:1,3;2:4;3:5". Used only when no explicit assignment/site_assignment
    # is given; pins donors and/or the specific isomer.
    isomer_spec: str | None = None
    relax: bool = True
    # Exactly "low" or "high" (the Spin enum); anything else is a 422, never a silent low spin,
    # because it sets xtb's --uhf and so the scientific result.
    spin: Spin = Spin.LOW
    # Wall-clock budget per structure, shared across the xtb tiers (GFN-FF pre-relax,
    # GFN2, and the GFN2 retry) rather than granted afresh to each. A hard case that
    # exceeds it keeps the assembled/last geometry (graceful).
    xtb_timeout_s: int = 300
    # Advanced options, same set the queued route takes. The pre-xtb placement guards
    # change the ASSEMBLED geometry, so they apply to this route's assembly-only builds
    # too; the xtb-time guards are simply inert when this route runs without relaxation.
    options: BuildOptions = Field(default_factory=BuildOptions)


class JobRequest(BaseModel):
    complexes: list[BuildRequest]
    relax: bool = True
    xtb_timeout_s: int = 300
    options: BuildOptions = Field(default_factory=BuildOptions)


class IsomerOptionsRequest(BaseModel):
    metal: str
    oxidation_state: int
    ligands: list[LigandIn]
    geometry: str
    stereo: bool = True


class PerceiveRequest(BaseModel):
    metal: str
    oxidation_state: int
    ligands: list[LigandIn]


class IsomerOptionsOut(BaseModel):
    count: int
    summary: str | None = None
    # True only if enumerating WITH stereo yields more isomers than without, i.e.
    # this specific complex actually has Δ/Λ enantiomers (vs. the geometry merely
    # being able to). Drives whether the Δ/Λ toggle is offered.
    stereo_splits: bool = False
    # Set only when enumeration failed UNEXPECTEDLY (not merely "not enumerable"):
    # a distinguishable state so a real bug is not reported as a legitimate count=1.
    error: str | None = None


class ReverseRequest(BaseModel):
    xyz: str
    backend: str = "builtin"          # "builtin" | "xyz2mol_tm"
    notation: str = "isomer"          # "isomer" | "trex" | "none"
    overall_charge: int | None = None  # required by the xyz2mol_tm backend


class ReverseLigandOut(BaseModel):
    smiles: str
    donor_atoms: list[int]
    charge: int


class ReverseOut(BaseModel):
    metal: str
    coordination_number: int
    ligands: list[ReverseLigandOut]
    isomer_notation: str
    backend: str
    complex_smiles: str | None = None   # whole-complex SMILES (xyz2mol_tm)
    trex: str | None = None             # T-REX notation, if requested


class ReverseBackendsOut(BaseModel):
    backends: list[str]
    notations: list[str]
    representations: list[dict]  # [{key, label}] for the CSV export / output menu


class ExportItem(BaseModel):
    name: str
    xyz: str
    overall_charge: int | None = None


class ReverseExportRequest(BaseModel):
    items: list[ExportItem]
    columns: list[str]  # representation keys, e.g. ["complex_smiles", "trex"]


class ReverseExportOut(BaseModel):
    csv: str


class ReverseRepresentRequest(BaseModel):
    xyz: str
    key: str  # a representation key from available_representations()
    overall_charge: int | None = None


class ReverseRepresentOut(BaseModel):
    key: str
    label: str
    value: str


class BuiltFile(BaseModel):
    name: str
    token: str
    complex: str | None = None
    total_charge: int
    uhf: int
    isomer_label: str | None = None
    warnings: list[str] = Field(default_factory=list)
    total_energy: float | None = None
    relative_energy_kcal: float | None = None
    is_lowest_energy: bool = False
    # False when xtb relaxation changed the connectivity (fusion, fragment, collapse, unbound
    # donor); such a result is listed after the valid isomers and never ranked lowest.
    connectivity_ok: bool = True
    metal_index: int | None = None
    donor_indices: list[int] = Field(default_factory=list)
    # Which structure formats were written for this result (e.g. ["xyz", "mol", "pdb"]); the UI
    # offers each as a download via /api/file/<token-with-that-suffix>.
    formats: list[str] = Field(default_factory=lambda: ["xyz"])


class BuildResponse(BaseModel):
    job_id: str
    results: list[BuiltFile]


class ComplexError(BaseModel):
    complex: str | None = None
    error: str


class JobOut(BaseModel):
    job_id: str
    status: str
    n_complexes: int
    # The job's size in structures (all-isomers rows count each isomer): what the queue
    # admits, estimates and reports progress in. Equals n_complexes without all-isomers rows.
    n_structures: int = 0
    estimate_s: float
    progress: float = 0.0
    stage: str | None = None
    results: list[BuiltFile] = Field(default_factory=list)
    error: str | None = None
    # Per-complex build failures on a job that otherwise completed (fault-isolated
    # batch: the other complexes still built). Distinct from `error` (fatal job).
    complex_errors: list[ComplexError] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

JOB_NOT_FOUND = (
    "This job link has expired or doesn't exist (results are kept for "
    f"{int(jobs.RESULT_TTL.total_seconds() // 3600)} hours after a build finishes). "
    "Build the complexes again."
)


def _describe(cx: Complex) -> ComplexOut:
    """Perceive a complex and package the table row (never raises for bad CN)."""
    try:
        perception.perceive_complex(cx)
    except Exception as exc:
        error = (str(exc) if isinstance(exc, perception.SmilesParseError)
                 else f"perception failed: {exc}")
        return ComplexOut(
            name=cx.name, metal=cx.metal.symbol, oxidation_state=cx.metal.oxidation_state,
            ligands=[LigandOut(smiles=l.smiles) for l in cx.ligands],
            supported=False, error=error,
        )
    ligands = [
        LigandOut(smiles=l.smiles, denticity=l.denticity, coord_atoms=l.coord_atoms,
                  is_arene=l.is_arene, pi_sites=[list(s) for s in (l.pi_sites or [])],
                  formal_charge=l.formal_charge,
                  warning=inputs.radical_warning(l.smiles))
        for l in cx.ligands
    ]
    cn = cx.coordination_number
    out = ComplexOut(
        name=cx.name, metal=cx.metal.symbol, oxidation_state=cx.metal.oxidation_state,
        ligands=ligands, coordination_number=cn, total_charge=cx.total_charge,
    )
    if inputs.is_f_block(cx.metal.symbol):
        out.warning = (f"{cx.metal.symbol} is f-block — xtb relaxation is skipped; "
                       f"the assembled geometry is returned.")
    # Multi-Cp-ligand guardrail: auto-perception marks at most ONE ring per ligand as
    # an η-cap, so a SINGLE ligand carrying two Cp rings (an ansa-metallocene, a
    # Cp+pyridine ligand) is silently under-coordinated — only one ring binds. Flag
    # those so a batch build doesn't produce a wrong structure; clears once the user
    # sets the rings as centroid caps (pi_sites populated). A normal metallocene /
    # sandwich (each Cp a SEPARATE single-ring ligand — titanocene, ferrocene,
    # ferroquine) perceives correctly and builds via the facial-triad metallocene
    # path, so it is NOT flagged.
    if any(not l.pi_sites and len(perception.cyclopentadienyl_cap_rings(l.smiles)) >= 2
           for l in cx.ligands):
        out.needs_cap_selection = True
    # A centroid-cap metallocene (exactly two η-caps) builds by a dedicated geometry,
    # not its summed CN: a bare two-cap sandwich is METALLOCENE (parallel rings, e.g.
    # ferrocene), a BENT metallocene (Cp2MXn) with ancillary ligands. This MUST match
    # geometry.detect_metallocene — the proposed geometry is passed back as an explicit
    # build geometry, so a mismatch (previously LINEAR here) would override the builder's
    # own detection and split the d-electrons on the wrong field (ferrocene Fe(II) d6 ->
    # a spurious uhf=2 triplet instead of the diamagnetic uhf=0, and a linear build).
    cap_sites = sum(1 for l in cx.ligands for s in (l.pi_sites or []) if len(s) >= 3)
    if cap_sites == 2:
        sandwich = Geometry.METALLOCENE if cn == 2 else Geometry.METALLOCENE_BENT
        out.geometry_options = [sandwich.value]
        out.proposed_geometry = sandwich.value
        return out
    # A metallocene (two eta-caps) routes by a dedicated geometry, not CN — its
    # denticity-sum CN (6, or 8 with legs) would offer the wrong/no geometry.
    options: list[str] = []
    metallo = geometry.detect_metallocene(
        [l.denticity for l in cx.ligands], [l.is_arene for l in cx.ligands]
    )
    if metallo is not None:
        options.append(metallo.value)
    try:
        options += [g.value for g in geometry.geometries_for_cn(cn)]
    except Exception as exc:
        if not options:  # neither a metallocene nor a supported CN
            out.supported = False
            out.error = str(exc)
            return out
    # One centroid η-cap = a piano stool (half sandwich). Offer it as the honest label
    # and default: its CN geometry is a poor description — a 3-legged piano stool reads
    # as "tetrahedral" (built angles are ~125°/90°, not 109.5°), and cap + tridentate
    # trips the "≤2 ligands are strongly chelating" rule into "square_planar". This is a
    # LABEL only: it carries no site vectors, so build_complex re-proposes it onto the CN
    # geometry (the same path that absorbs a stale geometry from an older row). The CN
    # options stay listed so the user can still pin a placement geometry explicitly.
    piano = geometry.detect_piano_stool(
        [len(s) for l in cx.ligands for s in (l.pi_sites or []) if len(s) >= 3])
    if piano is not None:
        options.insert(0, piano.value)
    out.geometry_options = options
    # Default geometry: a metallocene keeps its dedicated geometry; otherwise use
    # the input-aware default (CN4 square-planar for d8 or a strongly-chelating ≤2
    # ligand set, else tetrahedral; CN5 defaults to trigonal-bipyramidal). Both
    # CN4/CN5 options stay in geometry_options so the user can override.
    if metallo is not None or piano is not None:
        out.proposed_geometry = options[0]
    else:
        d_count = spin.d_count_or_none(cx.metal.symbol, cx.metal.oxidation_state)
        out.proposed_geometry = geometry.propose_geometry(
            cn, d_count, denticities=[l.denticity for l in cx.ligands],
            lone_pair=spin.has_stereo_active_lone_pair(
                cx.metal.symbol, cx.metal.oxidation_state
            ),
        ).value
    return out


def _build_one_sync(req: BuildRequest, job_dir: Path) -> list[BuiltFile]:
    geom = _validate_geometry(req.geometry)
    ligands = [
        Ligand(smiles=l.smiles, donor_override=l.coord_atoms, is_arene=l.is_arene)
        for l in req.ligands
    ]
    cx = Complex(
        metal=Metal(req.metal, req.oxidation_state), ligands=ligands,
        spin=req.spin, name=req.name, geometry=geom,
        isomer_spec=req.isomer_spec or None,
    )
    site_asg = None
    if req.site_assignment:
        site_asg = {int(k): tuple(v) for k, v in req.site_assignment.items()}
    override = None
    if req.assignment and site_asg is None:
        from ..isomers import IsomerSpec

        assignment = {int(k): tuple(v) for k, v in req.assignment.items()}
        override = [IsomerSpec(geometry=geom, label="custom", assignment=assignment)]
    try:
        results = pipeline.build_complex(
            cx, job_dir, all_isomers=req.all_isomers, stereo=req.stereo,
            isomers_override=override, site_assignment=site_asg, relax=req.relax,
            xtb_timeout_s=req.xtb_timeout_s, max_isomers=MAX_ISOMERS_PER_COMPLEX,
            max_isomers_high_cn=MAX_ISOMERS_HIGH_CN,
            formats=jobs.WEB_FORMATS,
            **jobs._build_options({"options": req.options.model_dump()}),
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Build failed: {jobs._clean_error(exc)}")
    return [
        BuiltFile(name=Path(r.xyz_path).name, token=f"{job_dir.name}/{Path(r.xyz_path).name}",
                  complex=req.name, total_charge=r.total_charge, uhf=r.uhf,
                  isomer_label=r.isomer_label, warnings=r.warnings,
                  total_energy=r.total_energy, relative_energy_kcal=r.relative_energy_kcal,
                  is_lowest_energy=r.is_lowest_energy, connectivity_ok=r.connectivity_ok,
                  metal_index=r.metal_index, donor_indices=r.donor_indices,
                  formats=[Path(p).suffix.lstrip(".") for p in r.extra_paths])
        for r in results
    ]


# Column names that mark a first line as a header. Without one of these, a
# pasted row like "Ir, 3, <smiles>..." would silently become the header and
# the row count would drop by one (to zero for a single-line paste).
_L_SLOT_TOKEN = re.compile(r"^l\d+$")


def _read_csv(text: str):
    import csv
    import io

    import pandas as pd

    # Standards-compliant CSV so a double-quoted `isomer` cell (whose donor-index
    # notation contains commas, per README/QUICKSTART) stays ONE field. Still
    # tolerates ragged rows (complexes with different ligand counts) by padding
    # short rows below — which pandas.read_csv would not.
    try:
        parsed = []
        for row in csv.reader(io.StringIO(text)):
            if not any(c.strip() for c in row):
                continue
            if len(row) > MAX_LIGANDS_PER_COMPLEX + 8:
                raise ValueError("Too many CSV columns.")
            if any(len(c) > MAX_SMILES_LEN for c in row):
                raise ValueError(f"CSV field too long (max {MAX_SMILES_LEN} chars).")
            parsed.append(row)
            if len(parsed) > MAX_COMPLEXES_PER_JOB + 1:
                raise ValueError(f"Too many rows (max {MAX_COMPLEXES_PER_JOB}).")
    except csv.Error as exc:
        raise ValueError(f"malformed CSV: {exc}")
    rows = [[c.strip() for c in r] for r in parsed if any(c.strip() for c in r)]
    if not rows:
        raise ValueError("No data rows.")

    has_header = inputs.is_header_row(rows[0])  # same rule as the CLI reader
    header = rows[0] if has_header else None
    data = rows[1:] if has_header else rows
    if not data:
        raise ValueError("No data rows.")

    width = max(len(r) for r in rows)
    if has_header:
        # Extend a short header with fresh L-slots so extra ligand columns are
        # still perceived as ligands (parse_dataframe keys ligands off L\d+ names).
        used = [int(re.search(r"\d+", c).group())
                for c in header if _L_SLOT_TOKEN.match(c.lower())]
        next_l = (max(used) + 1) if used else 1
        cols = list(header)
        while len(cols) < width:
            cols.append(f"L{next_l}"); next_l += 1
    else:
        cols = [f"col{i}" for i in range(width)]  # ints break parse_dataframe

    data = [r + [""] * (width - len(r)) for r in data]
    return pd.DataFrame(data, columns=cols)


def _isomer_summary(labels: list[str | None]) -> str | None:
    """Short hint of the isomer types among enumerated labels, e.g. 'cis/trans (2)'
    or 'Δ/Λ (2)'. Returns None for a single isomer (nothing to enumerate)."""
    n = len(labels)
    if n <= 1:
        return None
    tokens: set[str] = set()
    for lab in labels:
        if not lab:
            continue
        for part in lab.split("_"):
            tokens.add(re.sub(r"\d+$", "", part))  # strip the uniquifying counter
    kinds = []
    if {"cis", "trans"} & tokens:
        kinds.append("cis/trans")
    if {"fac", "mer"} & tokens:
        kinds.append("fac/mer")
    if {"Delta", "Lambda"} & tokens:
        kinds.append("Δ/Λ")
    return f"{', '.join(kinds)} ({n})" if kinds else f"{n} isomers"


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #

@asynccontextmanager
async def _lifespan(app: FastAPI):
    store = jobs.JobStore(_DATA / "jobs.db", _RESULTS)
    store.recover_interrupted()
    store.track_legacy_outputs()
    store.cleanup()  # expire terminal jobs from their completion time
    worker = jobs.Worker(store)
    worker.start()
    cleaner = jobs.Cleaner(store)
    cleaner.start()
    app.state.store = store
    app.state.worker = worker
    app.state.rate = jobs.RateLimiter(RATE_MAX_PER_WINDOW, float(RATE_WINDOW_S))
    try:
        yield
    finally:
        # Signal + join so the worker exits deliberately on shutdown (an in-flight
        # build is allowed to finish; bounded by the timeout, then abandoned as a
        # daemon thread at process exit).
        worker.stop(join_timeout=10.0)
        cleaner.stop()


_VERSION_INFO: "dict | None" = None


def _version_info() -> dict:
    """Running package version + git branch/short-commit + commit date, computed once and
    cached. In the Docker image there is no .git, so commit and date come from the
    ``MECOBI_COMMIT`` / ``MECOBI_BUILD_DATE`` build args instead; any field still unknown is
    ``None`` and the GUI just leaves it out."""
    global _VERSION_INFO
    if _VERSION_INFO is None:
        import subprocess

        from .. import __version__

        branch = commit = None
        root = str(Path(__file__).resolve().parents[3])

        def _git(*args):
            try:
                out = subprocess.run(["git", "-C", root, *args], capture_output=True,
                                     text=True, timeout=3)
                return out.stdout.strip() or None if out.returncode == 0 else None
            except Exception:  # noqa: BLE001 - git absent / not a repo → just skip
                return None

        branch = _git("rev-parse", "--abbrev-ref", "HEAD")
        commit = (_git("rev-parse", "--short", "HEAD")
                  or (os.environ.get("MECOBI_COMMIT") or "")[:7] or None)
        updated = os.environ.get("MECOBI_BUILD_DATE") or _git("log", "-1", "--format=%cs")
        _VERSION_INFO = {"version": __version__, "branch": branch, "commit": commit,
                         "updated": updated}
    return _VERSION_INFO


def create_app() -> FastAPI:
    app = FastAPI(title="MeCoBi", version="0.1.0", lifespan=_lifespan)
    app.add_middleware(BodySizeLimit, max_bytes=lambda: MAX_BODY_BYTES)
    app.state.preview_rate = jobs.RateLimiter(max_per_window=120)
    app.state.preview_slots = threading.BoundedSemaphore(PREVIEW_CONCURRENCY)
    # Archive builds (a cached archive costs neither): per-submitter rate + global concurrency.
    app.state.zip_rate = jobs.RateLimiter(max_per_window=30)
    app.state.zip_slots = threading.BoundedSemaphore(ZIP_CONCURRENCY)

    def _worker_alive() -> bool:
        worker = getattr(app.state, "worker", None)
        return bool(worker is not None and worker.is_alive())

    @app.get("/api/health")
    def health(response: Response) -> dict:
        """Health of the *queue*, not just of the web process.

        A dead serial worker is invisible from outside: the site serves, previews
        work, submissions are accepted with 202 — and nothing ever builds. Reporting
        503 here is what lets the container HEALTHCHECK (and any uptime monitor)
        notice, instead of a green site quietly building nothing for days.
        """
        alive = _worker_alive()
        if not alive:
            response.status_code = 503
        return {"status": "ok" if alive else "degraded",
                "worker": "alive" if alive else "dead"}

    @app.get("/api/workload")
    def workload() -> dict:
        summary = app.state.store.workload()
        return {
            # Busy means work is actually queued or running — NOT that the build
            # lock happens to be held, which the idle queue worker does on every
            # poll and would flash a spurious "server busy" notice at users.
            **summary,
            "busy": bool(summary["running_jobs"] or summary["pending_structures"]),
            # Polled by the GUI anyway: a queue that cannot drain is worth seeing
            # next to the numbers that will otherwise sit still forever.
            "worker_alive": _worker_alive(),
            "max_complexes_per_job": MAX_COMPLEXES_PER_JOB,
            "max_pending_structures": MAX_PENDING_STRUCTURES,
            "long_job_seconds": LONG_JOB_SECONDS,
        }

    @app.get("/api/whoami")
    def whoami(request: Request) -> dict:
        """The caller's own address as the rate limiter sees it — a deployment check.

        Behind a reverse proxy every request reaches the app from the proxy, so the
        per-submitter rate limit collapses into ONE shared bucket for the whole internet
        unless the real client address is recovered from ``X-Forwarded-For``. uvicorn does
        that only for peers in ``--forwarded-allow-ips`` (default: 127.0.0.1 alone) — and
        when the peer is not trusted it silently ignores the header rather than erroring.
        A container behind a host Apache is exactly that case: the peer is the Docker
        bridge gateway (~172.17.0.1), not 127.0.0.1.

        The failure is invisible from inside, so it needs checking from outside: curl this
        THROUGH the proxy and read ``client``. Your public address means the chain works;
        a gateway/localhost address with ``forwarded_for`` populated means the header is
        arriving but is not trusted (set ``FORWARDED_ALLOW_IPS``); a gateway address with
        ``forwarded_for`` null means the proxy is not sending it at all.

        Callers learn only their own address, which they already know.
        """
        return {
            "client": jobs.submitter_id(request),        # the rate-limit key
            "forwarded_for": request.headers.get("x-forwarded-for"),
            "rate_limit": {"max": RATE_MAX_PER_WINDOW, "window_s": RATE_WINDOW_S},
        }

    @app.get("/api/version")
    def version() -> dict:
        """Version + git branch/commit of the running build, for the GUI footer."""
        return _version_info()

    @app.get("/api/stats")
    def stats() -> dict:
        """Public usage counter for the GUI footer: ``{"structures_built", "since"}``.

        Anonymous running totals only (see :mod:`mecobi.web.usage`); ``since`` is the first
        day counted (ISO date) or null before the first build.
        """
        return app.state.store.usage_totals()

    @app.get("/api/geometries")
    def geometries() -> dict[str, list[str]]:
        """CN -> geometry options; lets the client refresh the table when donor
        edits change a complex's coordination number."""
        return {str(cn): [g.value for g in opts]
                for cn, opts in geometry.CN_TO_GEOMETRIES.items()}

    @app.post("/api/parse", response_model=list[ComplexOut], dependencies=[Depends(_preview_guard)])
    def parse(req: ParseRequest) -> list[ComplexOut]:
        if len(req.csv.encode("utf-8", "ignore")) > MAX_CSV_BYTES:
            raise HTTPException(status_code=413, detail=f"CSV too large (max {MAX_CSV_BYTES} bytes).")
        try:
            df = _read_csv(req.csv)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not read CSV: {exc}")
        if len(df) > MAX_COMPLEXES_PER_JOB:
            raise HTTPException(status_code=400, detail=f"Too many rows (max {MAX_COMPLEXES_PER_JOB}).")
        try:
            # Lenient: a single malformed row becomes a flagged, unbuildable table
            # row instead of aborting the whole batch (one bad line no longer loses
            # the other 999 complexes).
            items = inputs.parse_dataframe(df, lenient=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}")
        for item in items:
            if not isinstance(item, inputs.RowParseError):
                _validate_ligands(item.ligands)
        # Warm the pydentate cache for every ligand up front (deduped by exact
        # SMILES, and run in parallel when MECOBI_PERCEPTION_WORKERS is set on a fork
        # platform), so the per-row perceive() below hits a warm cache. Skip the
        # malformed rows — they carry no parsed ligands.
        perception.prewarm_pydentate(
            l.smiles for item in items
            if not isinstance(item, inputs.RowParseError) for l in item.ligands
        )
        out: list[ComplexOut] = []
        for item in items:
            if isinstance(item, inputs.RowParseError):
                # oxidation_state=None (shown as "Pt(?)"), never a made-up 0: Pt(0)
                # is a real oxidation state the user did not enter.
                out.append(ComplexOut(
                    name=item.name or f"row {item.position + 1}",
                    metal=inputs._as_symbol(item.metal) or item.metal or "?",
                    oxidation_state=None, ligands=[],
                    supported=False, error=item.message,
                ))
            else:
                out.append(_describe(item))
        return out

    @app.post("/api/build", response_model=BuildResponse)
    def build(req: BuildRequest, request: Request) -> BuildResponse:
        # /api/build runs a synchronous assembly (+ optional xtb): validate and
        # rate-limit it like the queued path, before doing any work.
        if not app.state.rate.allow(jobs.submitter_id(request)):
            raise HTTPException(status_code=429, detail="Rate limit exceeded; try again shortly.")
        _validate_build_request(req)
        _validate_geometry(req.geometry)  # 400 before competing for the slot, not after
        if not jobs.BUILD_SLOT.acquire(timeout=BUILD_SLOT_TIMEOUT_S):
            raise HTTPException(503, "The server is building another job. Use Build all to queue "
                                "your request, or try again later.", headers={"Retry-After": "10"})
        try:
            # Do not let new synchronous requests jump ahead of admitted batches.
            if app.state.store.workload()["pending_structures"]:
                raise HTTPException(503, "The server has queued work. Use Build all to join "
                                    "the queue, or try again later.", headers={"Retry-After": "10"})
            cspec = req.model_dump()
            job_id = app.state.store.create(
                {"complexes": [cspec], "relax": req.relax,
                 "workload_units": [jobs.workload_units(cspec)]},
                jobs.submitter_id(request), start_running=True)
            try:
                results = _build_one_sync(req, _RESULTS / job_id)
                app.state.store.finish(job_id, [r.model_dump() for r in results])
            except Exception as exc:
                detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
                app.state.store.fail(job_id, str(detail))
                raise
        finally:
            jobs.BUILD_SLOT.release()
        return BuildResponse(job_id=job_id, results=results)

    @app.post("/api/jobs", response_model=JobOut, status_code=202)
    def submit_job(req: JobRequest, request: Request) -> JobOut:
        if not app.state.rate.allow(jobs.submitter_id(request)):
            raise HTTPException(status_code=429, detail="Rate limit exceeded; try again shortly.")
        if not req.complexes:
            raise HTTPException(status_code=400, detail="No complexes submitted.")
        if len(req.complexes) > MAX_COMPLEXES_PER_JOB:
            raise HTTPException(status_code=400, detail=f"Too many complexes (max {MAX_COMPLEXES_PER_JOB}).")
        if not XTB_TIMEOUT_MIN_S <= req.xtb_timeout_s <= XTB_TIMEOUT_MAX_S:
            raise HTTPException(
                status_code=400,
                detail=f"xtb_timeout_s must be between {XTB_TIMEOUT_MIN_S} and {XTB_TIMEOUT_MAX_S} s.")
        for c in req.complexes:
            _validate_build_request(c)
        def _complex_spec(c: BuildRequest) -> dict:
            # Keep only the per-complex option keys the caller actually set: model_dump()
            # would fill every unset key with its default, and those defaults would then
            # masquerade as per-complex choices (e.g. a stored oxo_antifusion_floors=False
            # beside a job-level True). run_build overlays these on the job-level options.
            d = c.model_dump()
            d["options"] = c.options.model_dump(exclude_unset=True)
            return d

        complexes = [_complex_spec(c) for c in req.complexes]
        units = jobs.workload_units_for(complexes)
        if sum(units) > MAX_PENDING_STRUCTURES:
            # Could never be admitted, however empty the queue: say so instead of "try later".
            raise HTTPException(
                status_code=400,
                detail=f"This job would build {sum(units)} structures (with 'all isomers' every "
                       f"isomer counts); the server limit is {MAX_PENDING_STRUCTURES}. Submit fewer "
                       "rows or fewer all-isomers rows.")
        spec = {
            "complexes": complexes,
            "workload_units": units,
            "relax": req.relax,
            "xtb_timeout_s": req.xtb_timeout_s,
            "options": req.options.model_dump(),
        }
        try:
            job_id = app.state.store.create(
                spec, jobs.submitter_id(request), max_pending=MAX_PENDING_STRUCTURES)
        except jobs.QueueFull as exc:
            raise HTTPException(429, str(exc), headers={"Retry-After": "60"})
        job = app.state.store.get(job_id)
        return _job_out(job)

    @app.get("/api/jobs/{job_id}", response_model=JobOut)
    def get_job(job_id: str) -> JobOut:
        job = app.state.store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=JOB_NOT_FOUND)
        return _job_out(job)

    @app.post("/api/jobs/{job_id}/cancel", response_model=JobOut)
    def cancel_job(job_id: str) -> JobOut:
        """Cancel a queued job (never starts) or ask a running one to stop at the next
        complex boundary. Idempotent: cancelling a finished/unknown job just returns it."""
        app.state.store.request_cancel(job_id)
        job = app.state.store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=JOB_NOT_FOUND)
        return _job_out(job)

    @app.get("/api/reverse/backends", response_model=ReverseBackendsOut)
    def reverse_backends() -> ReverseBackendsOut:
        """Which perception backends / notations are installed (for the UI menu)."""
        from .. import reverse

        return ReverseBackendsOut(
            backends=reverse.available_backends(),
            notations=reverse.available_notations(),
            representations=reverse.available_representations(),
        )

    @app.post("/api/reverse/export", response_model=ReverseExportOut)
    def reverse_export(req: ReverseExportRequest, request: Request) -> ReverseExportOut:
        """Batch-reverse many structures into a CSV, one column per representation.

        A cell that fails to convert holds ``ERROR: <reason>`` rather than aborting
        the whole export, so one bad structure never loses the rest.
        """
        import csv as _csv
        import io

        from .. import reverse

        if not app.state.rate.allow(jobs.submitter_id(request)):
            raise HTTPException(status_code=429, detail="Rate limit exceeded; try again shortly.")
        if len(req.items) > MAX_REVERSE_EXPORT_ITEMS:
            raise HTTPException(
                status_code=400, detail=f"Too many items (max {MAX_REVERSE_EXPORT_ITEMS}).")
        for item in req.items:
            _check_xyz_size(item.xyz)
        valid = {r["key"] for r in reverse.available_representations()}
        columns = [c for c in req.columns if c in valid]
        if not columns:
            raise HTTPException(status_code=400, detail="No available representation columns requested.")
        labels = {r["key"]: r["label"] for r in reverse.available_representations()}

        buf = io.StringIO()
        writer = _csv.writer(buf)
        writer.writerow(["name"] + [labels[c] for c in columns])
        for item in req.items:
            row = [item.name]
            for col in columns:
                try:
                    row.append(reverse.render_representation(item.xyz, col, item.overall_charge))
                except Exception as exc:  # noqa: BLE001 - keep the batch going
                    row.append(f"ERROR: {exc}")
            writer.writerow(row)
        return ReverseExportOut(csv=buf.getvalue())

    @app.post("/api/reverse/represent", response_model=ReverseRepresentOut)
    def reverse_represent(req: ReverseRepresentRequest, request: Request) -> ReverseRepresentOut:
        """Render one registry representation of a structure (drives the row menu)."""
        from .. import reverse

        if not app.state.rate.allow(jobs.submitter_id(request)):
            raise HTTPException(status_code=429, detail="Rate limit exceeded; try again shortly.")
        _check_xyz_size(req.xyz)
        labels = {r["key"]: r["label"] for r in reverse.available_representations()}
        if req.key not in labels:
            raise HTTPException(status_code=400, detail=f"Unknown representation {req.key!r}.")
        try:
            value = reverse.render_representation(req.xyz, req.key, req.overall_charge)
        except reverse.ReverseError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Could not reverse structure: {exc}")
        return ReverseRepresentOut(key=req.key, label=labels[req.key], value=value)

    @app.post("/api/reverse", response_model=ReverseOut)
    def reverse_structure(req: ReverseRequest, request: Request) -> ReverseOut:
        """Recover metal + ligand SMILES (and donor atoms) from an uploaded .xyz.

        ``backend`` selects the perception engine; ``notation`` optionally adds a
        T-REX string. Both third-party backends are optional (see mecobi.reverse).
        """
        from .. import reverse

        if not app.state.rate.allow(jobs.submitter_id(request)):
            raise HTTPException(status_code=429, detail="Rate limit exceeded; try again shortly.")
        _check_xyz_size(req.xyz)
        try:
            rc = reverse.reverse_xyz(
                req.xyz, backend=req.backend, overall_charge=req.overall_charge,
            )
            trex = (
                reverse.to_trex(req.xyz, req.overall_charge)
                if req.notation == "trex" else None
            )
        except reverse.ReverseError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:  # unexpected -> keep the generic wrapper
            raise HTTPException(status_code=400, detail=f"Could not reverse structure: {exc}")
        return ReverseOut(
            metal=rc.metal, coordination_number=rc.coordination_number,
            ligands=[ReverseLigandOut(smiles=l.smiles, donor_atoms=l.donor_atoms, charge=l.charge)
                     for l in rc.ligands],
            isomer_notation=rc.to_isomer_notation(),
            backend=rc.backend, complex_smiles=rc.complex_smiles, trex=trex,
        )

    @app.get("/api/depict", dependencies=[Depends(_preview_guard)])
    def depict(smiles: str) -> dict:
        """2D atom coords + bonds for a ligand, for the donor-correction panel (§7.1).

        Atom indices are heavy-atom, 0-based (no explicit H) — matching the
        coord_atoms the perception layer produces, so clicked atoms map directly
        to donor overrides.
        """
        from rdkit import Chem
        from rdkit.Chem import AllChem

        _validate_ligands([LigandIn(smiles=smiles)])
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise HTTPException(status_code=400, detail=f"Could not parse SMILES {smiles!r}")
        AllChem.Compute2DCoords(mol)
        conf = mol.GetConformer()
        atoms = [
            {"idx": a.GetIdx(), "symbol": a.GetSymbol(), "aromatic": a.GetIsAromatic(),
             "x": conf.GetAtomPosition(a.GetIdx()).x, "y": conf.GetAtomPosition(a.GetIdx()).y}
            for a in mol.GetAtoms()
        ]
        bonds = [
            {"a": b.GetBeginAtomIdx(), "b": b.GetEndAtomIdx(), "order": b.GetBondTypeAsDouble()}
            for b in mol.GetBonds()
        ]
        return {"smiles": smiles, "atoms": atoms, "bonds": bonds}

    @app.get("/api/depict_svg", dependencies=[Depends(_preview_guard)])
    def depict_svg(smiles: str) -> dict:
        """A proper 2D structure of a ligand as an SVG string (RDKit's drawer).

        Unlike ``/api/depict`` (raw coords for the clickable donor panel), this returns
        a publication-style depiction — real double/triple bonds, aromatic rings and
        formal charges — for a static thumbnail (the ligand library). Drawn in a black
        (monochrome) palette on a transparent background, then recoloured to
        ``currentColor`` so it adapts to the light/dark theme in the browser.
        """
        import re

        from rdkit import Chem
        from rdkit.Chem import AllChem
        from rdkit.Chem.Draw import rdMolDraw2D

        _validate_ligands([LigandIn(smiles=smiles)])
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise HTTPException(status_code=400, detail=f"Could not parse SMILES {smiles!r}")
        AllChem.Compute2DCoords(mol)
        drawer = rdMolDraw2D.MolDraw2DSVG(240, 150)
        opts = drawer.drawOptions()
        opts.clearBackground = False  # transparent, so it sits on any theme surface
        opts.useBWAtomPalette()  # monochrome; recoloured to currentColor below
        opts.bondLineWidth = 2
        opts.padding = 0.12
        rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
        drawer.FinishDrawing()
        svg = drawer.GetDrawingText()
        # Drop the XML prolog (we inline the SVG) and let the theme drive the colour.
        svg = svg.replace("<?xml version='1.0' encoding='iso-8859-1'?>", "").lstrip()
        svg = svg.replace("#000000", "currentColor").replace("#000", "currentColor")
        # RDKit styles every path with an inline `style='fill:..;stroke:..'`. A strict
        # Content-Security-Policy (no 'unsafe-inline' for styles, as a reverse proxy may
        # set) strips those in the browser -> blank structures. Convert each style block
        # to equivalent SVG PRESENTATION ATTRIBUTES (fill=, stroke=, ...), which CSP does
        # not govern, so the depiction renders on any deployment.
        def _style_to_attrs(m: "re.Match") -> str:
            attrs = []
            for decl in m.group(1).split(";"):
                decl = decl.strip()
                if ":" in decl:
                    key, val = decl.split(":", 1)
                    attrs.append(f'{key.strip()}="{val.strip()}"')
            return " ".join(attrs)

        svg = re.sub(r"style='([^']*)'", _style_to_attrs, svg)
        return {"smiles": smiles, "svg": svg}

    @app.get("/api/vertices")
    def vertices(geometry: str, denticities: str) -> dict:
        """Numbered coordination vertices for the 3D isomer scene (§7.2).

        The vertex ids are the SAME numbering the index/topology mode uses
        (invariant 7). ``denticities`` is a comma-separated list of ligand
        denticities; the (geometry, partition) selects the topology.
        """
        from ..assembly import registry

        try:
            geom = Geometry(geometry)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown geometry {geometry!r}")
        try:
            dents = [int(x) for x in denticities.split(",") if x.strip() != ""]
        except ValueError:
            raise HTTPException(status_code=400, detail="denticities must be integers.")
        try:
            entry = registry.lookup(geom, dents)
        except KeyError:
            raise HTTPException(
                status_code=422,
                detail=f"No topology for {geometry} with denticities {registry.partition(dents)}.",
            )
        positions = registry.vertex_positions(entry)
        sites = registry.vertex_sites(entry)
        verts = [
            {
                "id": i, "x": float(p[0]), "y": float(p[1]), "z": float(p[2]), "denticity": d,
                "sites": [[float(s[0]), float(s[1]), float(s[2])] for s in ss],
            }
            for i, (p, d, ss) in enumerate(zip(positions, entry.vertex_denticities, sites))
        ]
        return {"geometry": geom.value, "n_sites": entry.n_sites, "vertices": verts}

    @app.get("/api/sites")
    def sites(geometry: str, denticities: str, arene: str = "", cap: str = "") -> dict:
        """Canonical numbered coordination sites for the dynamic site model (§7.2).

        Returns every site (0..CN-1) with its position, the cis site pairs a
        bidentate may span, and a default {ligand -> site ids} assignment. Site
        numbering is shared with the index mode (invariant 7). ``arene`` is a
        comma-separated list of ligand indices that are eta-arene / Cp facial caps,
        so the default places them on a facial triad (a proper piano stool).
        """
        from ..assembly import sites as sites_mod

        try:
            geom = Geometry(geometry)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown geometry {geometry!r}")
        try:
            dents = [int(x) for x in denticities.split(",") if x.strip() != ""]
            arenes = {int(x) for x in arene.split(",") if x.strip() != ""}
            caps = {int(x) for x in cap.split(",") if x.strip() != ""}
        except ValueError:
            raise HTTPException(status_code=400, detail="denticities/arene/cap must be integers.")
        try:
            positions = sites_mod.site_positions(geom)
            cis = sites_mod.cis_pairs(geom)
            default = sites_mod.default_assignment(
                geom, dents, arene_ligands=arenes, cap_ligands=caps)
        except sites_mod.SiteAssignmentError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return {
            "geometry": geom.value,
            "n_sites": len(positions),
            "sites": [{"id": i, "x": float(p[0]), "y": float(p[1]), "z": float(p[2])}
                      for i, p in enumerate(positions)],
            "cis_pairs": [list(p) for p in cis],
            "default_assignment": {str(k): list(v) for k, v in default.items()},
        }

    @app.post("/api/perceive", response_model=ComplexOut, dependencies=[Depends(_preview_guard)])
    def perceive_row(req: PerceiveRequest) -> ComplexOut:
        """Re-perceive a row after a donor edit → cap-aware denticity, coordination
        number and geometry options. The frontend can't compute centroid-cap
        denticity locally (a selected ring = 1 site), so it calls this as the single
        source of truth whenever the donor selection changes."""
        _validate_ligands(req.ligands)
        ligands = [
            Ligand(smiles=l.smiles, donor_override=l.coord_atoms, is_arene=l.is_arene)
            for l in req.ligands
        ]
        cx = Complex(metal=Metal(req.metal, req.oxidation_state), ligands=ligands)
        return _describe(cx)

    @app.post("/api/isomers", response_model=IsomerOptionsOut, dependencies=[Depends(_preview_guard)])
    def isomer_options(req: IsomerOptionsRequest) -> IsomerOptionsOut:
        """How many distinct isomers 'all' would build for this row, and a short
        type hint (e.g. 'cis/trans (2)', 'Δ/Λ (2)'). Enumeration only — no build.

        Uses the donor atoms already on the row (no pydentate/torch reload), so it
        is cheap enough to call live as the geometry / donors / stereo change.
        """
        from ..isomers import StereoNotSupported, enumerate_isomers, enumerate_site_isomers

        _validate_ligands(req.ligands)
        try:
            geom = Geometry(req.geometry)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown geometry {req.geometry!r}")
        ligands = []
        for l in req.ligands:
            lig = Ligand(smiles=l.smiles, donor_override=l.coord_atoms, is_arene=l.is_arene)
            if l.coord_atoms:
                # cap-aware denticity (a selected ring is one centroid site, not N);
                # cheap — the override short-circuits pydentate.
                perception.perceive(lig)
            else:
                lig.coord_atoms = l.coord_atoms
                lig.denticity = 3 if l.is_arene else None
            ligands.append(lig)
        cx = Complex(metal=Metal(req.metal, req.oxidation_state), ligands=ligands, geometry=geom)

        def enum(stereo: bool):
            # StereoNotSupported (no site model / denticity out of range) falls back
            # to the plain enumerator, which raises KeyError for an unsupported
            # geometry+denticity combo. Both mean "not enumerable" -> handled below
            # as a legitimate single isomer; any OTHER exception is a real bug and
            # is allowed to propagate rather than be masked as count=1.
            try:
                return enumerate_site_isomers(cx, geom, stereo=stereo)
            except StereoNotSupported:
                return enumerate_isomers(cx, geom)

        try:
            with_stereo, without_stereo = enum(True), enum(False)
        except (StereoNotSupported, KeyError):
            # Legitimately not enumerable: the single canonical isomer is correct.
            return IsomerOptionsOut(count=1)
        except Exception as exc:  # noqa: BLE001 - unexpected: surface, don't fake "1"
            return IsomerOptionsOut(count=1, error=f"isomer enumeration failed: {exc}")
        splits = without_stereo is not None and len(with_stereo) > len(without_stereo)
        shown = with_stereo if req.stereo or without_stereo is None else without_stereo
        return IsomerOptionsOut(
            count=len(shown), summary=_isomer_summary([s.label for s in shown]),
            stereo_splits=splits,
        )

    @app.get("/api/file/{job_id}/{name}")
    def get_file(job_id: str, name: str) -> FileResponse:
        if "/" in name or "\\" in name or ".." in job_id or ".." in name:
            raise HTTPException(status_code=400, detail="Invalid file token.")
        path = (_RESULTS / job_id / name).resolve()
        if not path.is_file() or _RESULTS.resolve() not in path.parents:
            raise HTTPException(status_code=404, detail="File not found.")
        media = {
            ".xyz": "chemical/x-xyz",
            ".mol": "chemical/x-mdl-molfile",
            ".pdb": "chemical/x-pdb",
        }.get(path.suffix.lower(), "application/octet-stream")
        return FileResponse(path, media_type=media, filename=name)

    @app.get("/api/download/{job_id}")
    def download_all(job_id: str, request: Request) -> FileResponse:
        """Bundle all structures of a job (sync build or async queue) into a single zip for
        batch download — every written format (.xyz plus any .mol/.pdb).

        The archive is written to a temporary file in the job directory (never held in
        memory) after the file-count and size limits are checked. A finished job's archive
        is kept and served again; an unfinished job's is deleted once sent. Only regular
        files directly in the job directory are included, never symlinks.
        """
        if not re.fullmatch(r"[A-Za-z0-9_-]+", job_id):
            raise HTTPException(status_code=400, detail="Invalid job id.")
        root = _RESULTS.resolve()
        job_dir = (_RESULTS / job_id).resolve()
        if not job_dir.is_dir() or job_dir.parent != root:
            raise HTTPException(status_code=404, detail="Job not found.")
        headers = {"Content-Disposition": f'attachment; filename="mecobi_{job_id}.zip"'}
        job = app.state.store.get(job_id)
        finished = job is not None and job["status"] in (jobs.JobStatus.DONE.value,
                                                         jobs.JobStatus.FAILED.value)
        cached = job_dir / _ARCHIVE_NAME
        if finished and cached.is_file() and not cached.is_symlink():
            return FileResponse(cached, media_type="application/zip", headers=headers)

        files = sorted(f for f in job_dir.iterdir()
                       if f.suffix.lower() in _STRUCTURE_SUFFIXES
                       and not f.is_symlink() and f.is_file())
        if not files:
            raise HTTPException(status_code=404, detail="No structures to download.")
        total = sum(f.stat().st_size for f in files)
        if len(files) > MAX_ZIP_FILES or total > MAX_ZIP_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"This job has too many files to bundle ({len(files)} files, "
                       f"{total / 1e6:.0f} MB; limit {MAX_ZIP_FILES} files / "
                       f"{MAX_ZIP_BYTES / 1e6:.0f} MB). Download structures individually.")
        if not app.state.zip_rate.allow(jobs.submitter_id(request)):
            raise HTTPException(429, "Too many downloads; try again shortly.")
        if not app.state.zip_slots.acquire(timeout=0):
            raise HTTPException(503, "The server is preparing other downloads; try again shortly.",
                                headers={"Retry-After": "5"})
        try:
            fd, tmp_name = tempfile.mkstemp(prefix=".download-", suffix=".zip.tmp", dir=job_dir)
            tmp = Path(tmp_name)
            try:
                with os.fdopen(fd, "wb") as fh, zipfile.ZipFile(fh, "w", zipfile.ZIP_DEFLATED) as zf:
                    for f in files:
                        zf.write(f, arcname=f.name)
            except BaseException:
                tmp.unlink(missing_ok=True)
                raise
        finally:
            app.state.zip_slots.release()
        if finished:
            os.replace(tmp, cached)  # atomic: a concurrent download never sees a partial archive
            return FileResponse(cached, media_type="application/zip", headers=headers)
        return FileResponse(tmp, media_type="application/zip", headers=headers,
                            background=BackgroundTask(tmp.unlink, missing_ok=True))

    if _STATIC.is_dir():
        app.mount("/", StaticFiles(directory=_STATIC, html=True), name="static")
    else:
        @app.get("/", response_class=HTMLResponse)
        def index() -> str:
            return "<h1>MeCoBi</h1><p>Frontend not built yet. API is under /api.</p>"

    return app


def _job_out(job: dict) -> JobOut:
    import json

    results = [BuiltFile(**f) for f in json.loads(job["results"])] if job.get("results") else []
    cerrs = [ComplexError(**e) for e in json.loads(job["complex_errors"])] if job.get("complex_errors") else []
    return JobOut(
        job_id=job["id"], status=job["status"], n_complexes=job["n_complexes"],
        n_structures=job.get("n_units") or job["n_complexes"],
        estimate_s=job["estimate_s"], progress=job.get("progress") or 0.0,
        stage=job.get("stage"), results=results, error=job.get("error"),
        complex_errors=cerrs,
    )


app = create_app()
