"""Async job layer: job store + serial worker + cleanup.

The web service is "submit & come back": a submission becomes a job with an
unguessable id; a single serial worker (v1 concurrency, §10.4) runs it; the user
polls a private job URL (no accounts — §10.3, the id is the key). Completed jobs
and their files auto-delete after 24 h (§10.6). Each build runs in an isolated
per-job directory with xtb timeouts (§10.5, invariant 5); OS-level resource caps
belong to the Linux deployment (ulimit/cgroups) and are a deploy-time concern.

"Who submitted this" is abstracted behind :func:`submitter_id` — the seam where a
Google login (§10.3, DEFERRED) slots in later without rearchitecting.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import sqlite3
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path

from .. import pipeline
from ..model import Complex, Geometry, Ligand, Metal, Spin

RESULT_TTL = timedelta(hours=24)          # §10.6
CLEANUP_INTERVAL_S = 3600
# Rough cost of ONE structure (one isomer of one complex): relaxed vs assembly-only.
_SECONDS_PER_STRUCTURE = {True: 30.0, False: 3.0}
# One process owns the queue. Synchronous builds must use this same slot.
BUILD_SLOT = threading.Lock()


class QueueFull(ValueError):
    """Admission would exceed the configured unfinished-structure budget."""


def isomer_caps() -> tuple[int, int]:
    """The per-complex isomer caps ``(max_isomers, max_isomers_high_cn)`` (CN > 6).

    Read from the environment (same variables and defaults as app.MAX_ISOMERS_PER_COMPLEX /
    MAX_ISOMERS_HIGH_CN) to avoid a jobs<->app import cycle.
    """
    return (int(os.environ.get("MECOBI_MAX_ISOMERS", "64")),
            int(os.environ.get("MECOBI_MAX_ISOMERS_HIGH_CN", "16")))


def workload_units(cspec: dict, *, enumerate_isomers: bool = True) -> int:
    """How many structures one complex spec will build: the queue's unit of work.

    1 unless the row asks for all isomers (and does not pin one with an explicit
    assignment). An all-isomers row costs its enumerated isomer count, the same
    enumeration ``/api/isomers`` runs (no assembly), capped like the build itself:
    MECOBI_MAX_ISOMERS, or MECOBI_MAX_ISOMERS_HIGH_CN above CN 6. Without a geometry
    and donor atoms on every ligand (perceiving them would load the ML models), or
    when the enumeration fails, it costs the full cap, so the figure is never below
    what the build can do. ``enumerate_isomers=False`` charges the cap straight away.
    """
    if not cspec.get("all_isomers") or cspec.get("assignment") or cspec.get("site_assignment"):
        return 1
    max_isomers, max_isomers_high_cn = isomer_caps()
    if not enumerate_isomers or not cspec.get("geometry") or not all(l.get("coord_atoms") for l in cspec.get("ligands") or []):
        return max_isomers
    from .. import isomers, perception

    try:
        cx = _reconstruct(cspec)
        for lig in cx.ligands:
            perception.perceive(lig)  # cheap: the donor override short-circuits pydentate
        cap = (min(max_isomers, max_isomers_high_cn) if cx.coordination_number > 6
               else max_isomers)
        try:
            specs = isomers.enumerate_site_isomers(
                cx, cx.geometry, stereo=cspec.get("stereo", True), max_isomers=cap + 1)
        except isomers.StereoNotSupported:
            try:
                specs = isomers.enumerate_isomers(cx, cx.geometry, max_isomers=cap + 1)
            except (isomers.UnsupportedTopology, KeyError):
                return 1  # the build falls back to the single canonical isomer too
    except Exception:  # noqa: BLE001 - an unreadable row is charged in full, never for free
        return max_isomers
    return max(1, min(len(specs), cap))
# The web always materialises the extra structure formats beside each .xyz: job directories are
# ephemeral (per-job, auto-deleted after RESULT_TTL) and never globbed by tooling, so there is no
# clutter cost, and the UI can then offer any format as an instant download. Conversion is a few ms
# per complex (bonds from the assembled graph, coords from the built .xyz) — negligible vs xtb.
WEB_FORMATS = ("xyz", "mol", "pdb")


class BuildInterrupted(RuntimeError):
    """Shutdown reached a boundary between complexes."""


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clean_error(exc: Exception) -> str:
    """Human-readable one-liner for a build failure.

    RDKit/Boost surface argument-type mismatches as a multi-line C++ signature
    dump that is meaningless to a chemist — collapse those to a plain message.
    """
    msg = str(exc).strip()
    if "did not match C++ signature" in msg or "Python argument types" in msg:
        return ("could not construct this molecule — check the ligand SMILES, "
                "formal charges, and oxidation state")
    return msg.splitlines()[0] if msg else exc.__class__.__name__


# --------------------------------------------------------------------------- #
# Reconstruction + build (the worker's unit of work)
# --------------------------------------------------------------------------- #

def _reconstruct(cspec: dict) -> Complex:
    ligands = [
        Ligand(smiles=l["smiles"], donor_override=l.get("coord_atoms"), is_arene=l.get("is_arene", False))
        for l in cspec["ligands"]
    ]
    return Complex(
        metal=Metal(cspec["metal"], int(cspec["oxidation_state"])),
        ligands=ligands,
        # Same contract as the request model: a stored value that is not a Spin fails the
        # complex (ValueError) instead of quietly building it low spin.
        spin=Spin(cspec.get("spin", Spin.LOW.value)),
        name=cspec.get("name"),
        geometry=Geometry(cspec["geometry"]) if cspec.get("geometry") else None,
        isomer_spec=cspec.get("isomer_spec") or None,
    )


# Pre-xtb geometry guards + xtb constraints the GUI's "Advanced options" can toggle. Each maps to a
# build_complex keyword; all default ON in build_complex (except metal_surrogate), so an omitted /
# empty options dict reproduces the standard build. Unknown keys are ignored (forward-compatible).
BUILD_OPTION_KEYS = (
    "orient_bulky", "reposition_donors", "clear_metal_region", "declash_torsion",  # pre-xtb
    "reembed_crowded",                                                             # pre-xtb
    "mchammer", "linear_restraint", "haptic_guard", "planar_guard",                # placement + constraints
    "antifusion_guard", "metal_surrogate",                                         # relax-time guards
    # Opt-in escalation for a hard, crowded sphere (the Re(V) dioxo bis-PNP class):
    # both default OFF in build_complex, so omitting them reproduces the standard build.
    "reposition_polydentates", "oxo_antifusion_floors",
)


def _build_options(spec: dict) -> dict:
    """The subset of ``spec['options']`` that maps to build_complex toggles (bools only)."""
    opts = spec.get("options") or {}
    return {k: bool(opts[k]) for k in BUILD_OPTION_KEYS if k in opts}


def _build_one(cspec: dict, job_dir: Path, relax: bool, xtb_timeout_s: int,
               options: dict | None = None) -> list[dict]:
    """Build a single complex spec; return its result-file descriptors."""
    cx = _reconstruct(cspec)
    site_asg = None
    if cspec.get("site_assignment"):
        site_asg = {int(k): tuple(v) for k, v in cspec["site_assignment"].items()}
    override = None
    if cspec.get("assignment") and site_asg is None:
        from ..isomers import IsomerSpec

        assignment = {int(k): tuple(v) for k, v in cspec["assignment"].items()}
        override = [IsomerSpec(geometry=Geometry(cspec["geometry"]), label="custom", assignment=assignment)]
    # Same per-complex isomer cap as the sync path (app.MAX_ISOMERS_PER_COMPLEX).
    max_isomers, max_isomers_high_cn = isomer_caps()
    results = pipeline.build_complex(
        cx, job_dir, all_isomers=cspec.get("all_isomers", False),
        stereo=cspec.get("stereo", True),
        isomers_override=override, site_assignment=site_asg, relax=relax,
        xtb_bin=os.environ.get("XTB_BIN", "xtb"), xtb_timeout_s=xtb_timeout_s,
        max_isomers=max_isomers, max_isomers_high_cn=max_isomers_high_cn,
        formats=WEB_FORMATS, **(options or {}),
    )
    out: list[dict] = []
    for r in results:
        name = Path(r.xyz_path).name
        out.append({
            "name": name, "token": f"{job_dir.name}/{name}",
            "complex": cspec.get("name"),
            "total_charge": r.total_charge, "uhf": r.uhf, "warnings": r.warnings,
            "isomer_label": r.isomer_label, "total_energy": r.total_energy,
            "relative_energy_kcal": r.relative_energy_kcal,
            "is_lowest_energy": r.is_lowest_energy,
            "connectivity_ok": r.connectivity_ok,
            "metal_index": r.metal_index, "donor_indices": r.donor_indices,
            "formats": [Path(p).suffix.lstrip(".") for p in r.extra_paths],
        })
    return out


def run_build(spec: dict, job_dir: Path, on_progress=None, on_result=None, should_stop=None) -> tuple[list[dict], list[dict]]:
    """Build every complex in a job spec; return ``(results, errors)``.

    Each complex is built independently: one that fails (bad SMILES, unsupported
    metal, xtb blow-up, …) is recorded in ``errors`` and the batch continues, so a
    single bad row never discards the whole job's results. ``errors`` entries are
    ``{"complex": name, "error": message}``.

    ``on_progress(fraction, stage)`` (optional) is called as each complex starts
    so the job store can report progress to the polling client.
    ``on_result(results_so_far, errors_so_far)`` (optional) is called after each
    complex FINISHES, so the store can publish partial results and the client can
    show complexes as they are generated instead of waiting for the whole batch.
    ``should_stop()`` is checked before starting each complex; shutdown raises
    BuildInterrupted after earlier results have been published through on_result.
    """
    relax = spec.get("relax", True)
    xtb_timeout_s = int(spec.get("xtb_timeout_s", 300))
    options = _build_options(spec)
    complexes = spec["complexes"]
    total = len(complexes)
    # Progress is reported in structures (an all-isomers row weighs its isomer count), so
    # the queue's remaining-time estimate drains at the rate the work actually does.
    weights = spec.get("workload_units")
    if not isinstance(weights, list) or len(weights) != total:
        weights = [1] * total
    total_units = sum(weights) or 1
    out: list[dict] = []
    errors: list[dict] = []
    for done, cspec in enumerate(complexes):
        if should_stop is not None and should_stop():
            raise BuildInterrupted("Interrupted by server shutdown. Completed results are retained; "
                                   "please resubmit only unfinished complexes.")
        label = cspec.get("name") or cspec.get("metal") or "complex"
        if on_progress is not None:
            on_progress(sum(weights[:done]) / total_units, f"building {done + 1}/{total}: {label}")
        try:
            # Job-level options apply to every complex; a complex's own (explicitly set)
            # options override them key by key.
            opts = {**options, **_build_options(cspec)}
            out.extend(_build_one(cspec, job_dir, relax, xtb_timeout_s, opts))
        except Exception as exc:  # fault-isolate: one bad complex must not sink the job
            errors.append({"complex": label, "error": _clean_error(exc)})
        if on_result is not None:
            on_result(out, errors)      # publish partial results after each complex completes
    return out, errors


# Wall-time budget for costing one submission's all-isomers rows: the enumeration takes up
# to ~0.6 s for six different monodentates, so a 1000-row batch must not hold the request
# for minutes. Rows still uncosted when it runs out are charged the full cap.
UNITS_BUDGET_S = 5.0


def workload_units_for(cspecs: list[dict], budget_s: float = UNITS_BUDGET_S) -> list[int]:
    """:func:`workload_units` for every row of a submission, within ``budget_s``.

    Identical rows (same metal, donors, geometry, stereo flag) are enumerated once.
    """
    deadline = time.monotonic() + budget_s
    memo: dict[str, int] = {}
    out = []
    for c in cspecs:
        key = json.dumps([c.get(k) for k in ("metal", "oxidation_state", "geometry", "ligands",
                                              "all_isomers", "stereo", "assignment",
                                              "site_assignment")], sort_keys=True, default=str)
        if key not in memo:
            memo[key] = workload_units(c, enumerate_isomers=time.monotonic() < deadline)
        out.append(memo[key])
    return out


def estimate_seconds(n_structures: int, relax: bool) -> float:
    """Rough wall time for ``n_structures`` structures (see :func:`workload_units`)."""
    return n_structures * _SECONDS_PER_STRUCTURE[relax]


def spec_units(spec: dict) -> int:
    """A job's size in structures: its stored ``workload_units``, else one per complex."""
    units = spec.get("workload_units")
    n = len(spec.get("complexes", []))
    if isinstance(units, list) and len(units) == n:
        return sum(int(u) for u in units)
    return n


# --------------------------------------------------------------------------- #
# Job store (SQLite)
# --------------------------------------------------------------------------- #

class JobStore:
    def __init__(self, db_path: str | Path, results_dir: str | Path):
        self.db_path = Path(db_path)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        # Job ids whose RUNNING build the user asked to cancel. The worker checks this
        # between complexes (it never kills xtb mid-structure), so cancel takes effect at
        # the next complex boundary; the in-progress structure finishes first.
        self._cancels: set[str] = set()
        self._cancel_lock = threading.Lock()
        with self._conn() as c:
            c.execute(
                """CREATE TABLE IF NOT EXISTS jobs(
                    id TEXT PRIMARY KEY, status TEXT, submitter TEXT,
                    created_at TEXT, updated_at TEXT, spec TEXT,
                    n_complexes INTEGER, estimate_s REAL, results TEXT, error TEXT)"""
            )
            # Migrate older DBs: progress fraction (0..1) + current stage message.
            cols = {r[1] for r in c.execute("PRAGMA table_info(jobs)")}
            if "progress" not in cols:
                c.execute("ALTER TABLE jobs ADD COLUMN progress REAL DEFAULT 0")
            if "stage" not in cols:
                c.execute("ALTER TABLE jobs ADD COLUMN stage TEXT")
            # Per-complex build errors (JSON list) for a job that otherwise
            # completed — distinct from `error` (a whole-job fatal failure).
            if "complex_errors" not in cols:
                c.execute("ALTER TABLE jobs ADD COLUMN complex_errors TEXT")
            if "started_at" not in cols:
                c.execute("ALTER TABLE jobs ADD COLUMN started_at TEXT")
            # Job size in structures (all-isomers rows count each isomer); NULL on rows
            # from before it existed, read as n_complexes.
            if "n_units" not in cols:
                c.execute("ALTER TABLE jobs ADD COLUMN n_units INTEGER")
            if "finished_at" not in cols:
                c.execute("ALTER TABLE jobs ADD COLUMN finished_at TEXT")
                c.execute("UPDATE jobs SET finished_at=updated_at WHERE status IN (?,?)",
                          (JobStatus.DONE.value, JobStatus.FAILED.value))

    @contextlib.contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        """A connection that commits like sqlite3's own context manager — and closes.

        `with sqlite3.connect(...)` commits or rolls back but never closes, leaving
        every connection's file descriptor to refcounting. One connection per call
        is fine; relying on the collector to release them under load is not.
        """
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def create(self, spec: dict, submitter: str, *, max_pending: int | None = None,
               start_running: bool = False) -> str:
        jid = uuid.uuid4().hex
        n = len(spec.get("complexes", []))
        units = spec_units(spec)
        est = estimate_seconds(units, spec.get("relax", True))
        now = _now().isoformat()
        with self._lock, self._conn() as c:
            # Lock admission across connections, not just threads using this object.
            c.execute("BEGIN IMMEDIATE")
            if max_pending is not None:
                pending = c.execute(
                    "SELECT COALESCE(SUM(COALESCE(n_units, n_complexes)), 0) FROM jobs "
                    "WHERE status IN (?,?)",
                    (JobStatus.QUEUED.value, JobStatus.RUNNING.value),
                ).fetchone()[0]
                if pending + units > max_pending:
                    raise QueueFull(
                        f"The server queue is full (maximum {max_pending} unfinished structures; "
                        f"this job needs {units} and {pending} are already queued or running; "
                        "with 'all isomers' every isomer counts). Please try again after current "
                        "jobs finish or submit a smaller batch.")
            c.execute(
                """INSERT INTO jobs
                   (id, status, submitter, created_at, updated_at, spec,
                    n_complexes, n_units, estimate_s, results, error, progress, stage, started_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (jid, JobStatus.RUNNING.value if start_running else JobStatus.QUEUED.value,
                 submitter, now, now, json.dumps(spec), n, units, est, None, None, 0.0, None,
                 now if start_running else None),
            )
        return jid

    def workload(self) -> dict:
        """Public aggregate only: never disclose identifiers, inputs or submitters."""
        with self._conn() as c:
            rows = c.execute(
                "SELECT status, n_complexes, COALESCE(n_units, n_complexes) AS n_units, "
                "estimate_s, progress, started_at FROM jobs "
                "WHERE status IN (?,?)", (JobStatus.QUEUED.value, JobStatus.RUNNING.value),
            ).fetchall()
        return {
            "queued_jobs": sum(r["status"] == JobStatus.QUEUED.value for r in rows),
            "running_jobs": sum(r["status"] == JobStatus.RUNNING.value for r in rows),
            "pending_complexes": sum(r["n_complexes"] for r in rows),
            # The admission budget's unit: structures (all-isomers rows count each isomer).
            "pending_structures": sum(r["n_units"] for r in rows),
            "estimated_wait_s": sum(
                r["estimate_s"] * (1 - (r["progress"] or 0)) for r in rows),
            "longest_running_s": max((
                max(0.0, (_now() - datetime.fromisoformat(r["started_at"])).total_seconds())
                for r in rows if r["status"] == JobStatus.RUNNING.value and r["started_at"]
            ), default=0.0),
        }

    def set_progress(self, jid: str, fraction: float, stage: str | None) -> None:
        """Update a running job's progress fraction (0..1) and stage message."""
        with self._lock, self._conn() as c:
            c.execute(
                "UPDATE jobs SET progress=?, stage=?, updated_at=? WHERE id=?",
                (max(0.0, min(1.0, fraction)), stage, _now().isoformat(), jid),
            )

    def set_partial_results(self, jid: str, results: list[dict], errors: list[dict]) -> None:
        """Publish results accumulated so far WITHOUT ending the job (status stays running), so a
        polling client can render complexes as they finish. ``finish`` writes the final set + DONE."""
        with self._lock, self._conn() as c:
            c.execute(
                "UPDATE jobs SET results=?, complex_errors=?, updated_at=? WHERE id=? AND status=?",
                (json.dumps(results), json.dumps(errors) if errors else None,
                 _now().isoformat(), jid, JobStatus.RUNNING.value),
            )

    def get(self, jid: str) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        return dict(row) if row else None

    def request_cancel(self, jid: str) -> str | None:
        """Cancel a job. A QUEUED job is failed immediately (never starts); a RUNNING job
        is flagged so the worker stops at the next complex boundary (its in-progress
        structure finishes — xtb is never killed mid-run). Returns the pre-cancel status,
        or None if the job is unknown or already terminal."""
        with self._lock, self._conn() as c:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute("SELECT status FROM jobs WHERE id=?", (jid,)).fetchone()
            if row is None:
                return None
            status = row["status"]
            if status == JobStatus.QUEUED.value:
                now = _now().isoformat()
                c.execute(
                    "UPDATE jobs SET status=?, error=?, updated_at=?, finished_at=? WHERE id=?",
                    (JobStatus.FAILED.value, "Cancelled before it started.", now, now, jid))
            elif status == JobStatus.RUNNING.value:
                # Flag the running job WHILE holding self._lock. finish()/fail() also take
                # self._lock, so the worker cannot terminate this job between our status read
                # and the add: either we add first and the worker's finally-clear_cancel runs
                # after finish() (removing it), or the worker set a terminal status first and
                # we take this branch's else and never add. Prevents a stale, un-cleared entry.
                with self._cancel_lock:
                    self._cancels.add(jid)
            else:
                return None  # already done/failed
        return status

    def is_cancel_requested(self, jid: str) -> bool:
        with self._cancel_lock:
            return jid in self._cancels

    def clear_cancel(self, jid: str) -> None:
        with self._cancel_lock:
            self._cancels.discard(jid)

    def claim_next(self) -> dict | None:
        """Atomically move the oldest queued job to running; return it."""
        with self._lock, self._conn() as c:
            row = c.execute(
                "SELECT * FROM jobs WHERE status=? ORDER BY created_at LIMIT 1",
                (JobStatus.QUEUED.value,),
            ).fetchone()
            if row is None:
                return None
            c.execute(
                "UPDATE jobs SET status=?, updated_at=?, started_at=? WHERE id=?",
                (JobStatus.RUNNING.value, _now().isoformat(), _now().isoformat(), row["id"]),
            )
        return dict(row)

    def finish(self, jid: str, results: list[dict], errors: list[dict] | None = None) -> None:
        with self._lock, self._conn() as c:
            c.execute(
                "UPDATE jobs SET status=?, results=?, complex_errors=?, progress=?, stage=?, updated_at=?, finished_at=? WHERE id=?",
                (JobStatus.DONE.value, json.dumps(results),
                 json.dumps(errors) if errors else None, 1.0, "done",
                 _now().isoformat(), _now().isoformat(), jid),
            )

    def fail(self, jid: str, error: str) -> None:
        with self._lock, self._conn() as c:
            c.execute(
                "UPDATE jobs SET status=?, error=?, updated_at=?, finished_at=? WHERE id=?",
                (JobStatus.FAILED.value, error, _now().isoformat(), _now().isoformat(), jid),
            )

    def recover_interrupted(self) -> int:
        """Called once at startup, before any worker or request starts building."""
        now = _now().isoformat()
        with self._lock, self._conn() as c:
            cursor = c.execute(
                "UPDATE jobs SET status=?, error=?, updated_at=?, finished_at=? WHERE status=?",
                (JobStatus.FAILED.value,
                 "Interrupted by server restart. Completed results are retained; "
                 "please resubmit only unfinished complexes.", now, now, JobStatus.RUNNING.value))
        return cursor.rowcount

    def track_legacy_outputs(self) -> int:
        """Give old untracked individual-build directories 24 hours from upgrade."""
        now = _now().isoformat()
        added = 0
        root = self.results_dir.resolve()
        with self._lock, self._conn() as c:
            for path in self.results_dir.iterdir():
                # The old synchronous route generated exactly 12 lowercase hex digits.
                if (not re.fullmatch(r"[a-f0-9]{12}", path.name) or not path.is_dir()
                        or path.is_symlink() or path.resolve().parent != root):
                    continue
                added += c.execute(
                    "INSERT OR IGNORE INTO jobs "
                    "(id,status,created_at,updated_at,finished_at,spec,n_complexes,"
                    "estimate_s,results,progress,stage) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (path.name, JobStatus.DONE.value, now, now, now, "{}", 0, 0,
                     "[]", 1.0, "legacy individual-build output")).rowcount
        return added

    def cleanup(self, ttl: timedelta = RESULT_TTL) -> int:
        """Expire terminal jobs from completion time; never remove active work."""
        cutoff = (_now() - ttl).isoformat()
        removed = 0
        with self._lock, self._conn() as c:
            rows = c.execute(
                "SELECT id FROM jobs WHERE status IN (?,?) AND finished_at < ?",
                (JobStatus.DONE.value, JobStatus.FAILED.value, cutoff)).fetchall()
            for row in rows:
                try:
                    if (self.results_dir / row["id"]).resolve().parent != self.results_dir.resolve():
                        raise OSError("Result directory is outside the results root")
                    _rmtree(self.results_dir / row["id"])
                except OSError:
                    logging.getLogger(__name__).exception("Result cleanup failed; will retry")
                    continue
                c.execute("DELETE FROM jobs WHERE id=?", (row["id"],))
                removed += 1
        return removed


def _rmtree(path: Path) -> None:
    import shutil

    root = path.parent.resolve()
    target = path.resolve()
    if target.parent != root or path.is_symlink():
        raise OSError("Refusing to clean a result directory outside the results root")
    try:
        shutil.rmtree(target)
    except FileNotFoundError:
        pass


# --------------------------------------------------------------------------- #
# Serial worker
# --------------------------------------------------------------------------- #

class Worker(threading.Thread):
    """Single background thread that drains the queue serially (§10.4)."""

    def __init__(self, store: JobStore):
        super().__init__(daemon=True)
        self.store = store
        # NB: named `_stop_event`, not `_stop` — `threading.Thread._stop` is an
        # internal method (called during join/teardown); shadowing it with an
        # Event breaks join() and raises at thread exit.
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.is_set():
            if not BUILD_SLOT.acquire(blocking=False):
                self._stop_event.wait(0.4)
                continue
            job = None
            try:
                job = self.store.claim_next()
                if job is not None:
                    self._process(job)
            except Exception:
                # ONE thread owns the queue, so an error out here is terminal for the
                # whole service: every later submission sits queued forever while the
                # site keeps serving perfectly. That is not hypothetical — a transient
                # sqlite "unable to open database file" (a full disk) killed this
                # thread in production on 2026-09-15 and the queue stayed dead for
                # four days. `_process` fault-isolates one bad job; this catches the
                # store itself failing. Treat the iteration as idle and poll again.
                logging.getLogger(__name__).exception(
                    "Queue worker iteration failed; continuing")
                job = None
            finally:
                BUILD_SLOT.release()
            if job is None:
                self._stop_event.wait(0.4)

    def _process(self, job: dict) -> None:
        jid = job["id"]
        try:
            spec = json.loads(job["spec"])

            def on_progress(fraction: float, stage: str) -> None:
                self.store.set_progress(jid, fraction, stage)

            def on_result(results: list[dict], errors: list[dict]) -> None:
                self.store.set_partial_results(jid, results, errors)

            # Stop for a server shutdown OR a user cancel of THIS job (checked between
            # complexes; the in-progress structure always finishes — xtb isn't killed).
            def should_stop() -> bool:
                return self._stop_event.is_set() or self.store.is_cancel_requested(jid)

            results, errors = run_build(
                spec, self.store.results_dir / jid, on_progress, on_result,
                should_stop=should_stop)
            self.store.finish(jid, results, errors)
        except BuildInterrupted as exc:
            if self.store.is_cancel_requested(jid):
                self.store.fail(jid, "Cancelled by user. Any completed structures are retained.")
            else:
                self.store.fail(jid, _clean_error(exc))  # server shutdown
        except Exception as exc:  # never let the worker die on one bad job
            self.store.fail(jid, _clean_error(exc))
        finally:
            self.store.clear_cancel(jid)

    def stop(self, join_timeout: float | None = None) -> None:
        """Signal the loop to exit and (optionally) wait for it.

        An idle worker exits within one poll (~0.4 s). If a build is in flight the
        current complex runs to completion — we never kill xtb mid-run, to avoid
        corrupt partial output — so `join_timeout` bounds the wait and, as a daemon
        thread, an overlong build may be interrupted by process exit. Startup
        recovery marks its record failed while retaining published results.
        """
        self._stop_event.set()
        if join_timeout is not None:
            self.join(join_timeout)


class Cleaner(threading.Thread):
    """Expire finished results even while the serial worker is busy."""

    def __init__(self, store: JobStore, interval_s: float = CLEANUP_INTERVAL_S):
        super().__init__(daemon=True)
        self.store = store
        self.interval_s = interval_s
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.wait(self.interval_s):
            try:
                self.store.cleanup()
            except Exception:
                logging.getLogger(__name__).exception("Result cleanup failed; will retry")

    def stop(self, join_timeout: float = 5.0) -> None:
        self._stop_event.set()
        self.join(join_timeout)


# --------------------------------------------------------------------------- #
# Rate limiting + submitter identity (auth seam)
# --------------------------------------------------------------------------- #

class RateLimiter:
    """In-memory sliding window per submitter (v1, single process — §10.5)."""

    def __init__(self, max_per_window: int = 20, window_s: float = 60.0):
        self.max = max_per_window
        self.window = window_s
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.max:
                return False
            hits.append(now)
            return True


def submitter_id(request) -> str:
    """Identify the submitter (auth seam, §10.3). For v1: client IP.

    A Google login would replace this with the authenticated user id without
    touching the rest of the job machinery.
    """
    client = getattr(request, "client", None)
    return client.host if client else "anonymous"
