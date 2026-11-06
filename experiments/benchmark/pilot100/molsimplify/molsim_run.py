"""molSimplify counterpart to arch_run.py / run.py: generate the SAME pilot-100 complexes
with MIT molSimplify, timed the same way, so the head-to-head covers three builders.

Runs in the **molSimplify** conda env (imports molSimplify + optionally rdkit; never mecobi).
Feeds the ground-truth donor atoms as molSimplify `-smicat` (its designed input for SMILES
ligands), exactly parallel to Architector's `coordList` and MeCoBi's `donor_override` -- so no
tool is advantaged on donor perception. Shardable/resumable; logs `wall_s` per complex.

    python pilot100/molsimplify/molsim_run.py --shard 0/1 --targets benchmark_targets_pilot.json
    # parallel, matching the 4-core Keisan runs (set OMP_NUM_THREADS=1 if using --ff xtb):
    for i in $(seq 0 3); do python pilot100/molsimplify/molsim_run.py --shard $i/4 \n        --targets benchmark_targets_pilot.json & done; wait

Writes molsim_structures/<refcode>.xyz + _molsim_results_shard*.jsonl.

FAIRNESS / METHOD NOTES -- READ BEFORE COMPARING TIMES
------------------------------------------------------
CORRECTION (2026-09-28 audit): molSimplify's `-ffoption` defaults to `N` = NO optimization at all
(`inparse.py:1168` -> `cleaninput` sets `args.ff = False`), so the 2026-08-04 run, which passed
`-ff uff` without `-ffoption`, was most likely unoptimized. This runner now passes `-ffoption`
explicitly (default `ba` = optimize before + after placement). A force-field build is still
NOT a semiempirical relaxation. Architector here ran at GFN2-xTB
defaults and MeCoBi does an xtb relax, so a UFF molSimplify run will look dramatically faster
but is optimizing at a different level of theory -- that is itself a real "how each tool ships"
data point, but it is not like-for-like. For a quality-matched comparison pass `--ff xtb`
(molSimplify then drives xtb as its optimizer; needs xtb on PATH, and is much slower) -- see
run_pilot100_xtb.py. Two as-shipped molSimplify behaviours to state when reporting it:
  * the final optimization freezes the metal + donor atoms (`constopt=1`, an xtb `$fix` block),
    so xtb relaxes the ligand bodies but NOT the coordination sphere;
  * xtb gets `$chrg`/`$spin` only when the complex charge is non-zero, so a NEUTRAL open-shell
    complex is relaxed as closed-shell.
Confirmed input corrections (benchmark_overrides.json) are applied by default, as run.py does
for MeCoBi (--no-overrides reproduces the raw bundle).

Coverage caveats (recorded, not errors):
  * molSimplify's built-in geometries stop at CN 8 -- CN 9 complexes are skipped (no geometry).
  * oxidation state is passed only for ox in 1..8; for ox<=0 molSimplify's default is used
    (ox barely affects the FF geometry, which is covalent-radius driven).
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import multiprocessing as mp
import os
import queue as _queue
import sys
import time
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

from molSimplify.Scripts.generator import startgen_pythonic

try:  # rdkit only powers the optional donor pre-flight gate; molSimplify doesn't need it
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
except ImportError:
    Chem = None

HERE = Path(__file__).resolve().parent   # pilot100/molsimplify/: results + molsim_structures/
PILOT = HERE.parent                      # pilot100/: pilot_100.json + crystal targets
BENCH = PILOT.parent                     # benchmark root: frozen bundle + donors
sys.path.insert(0, str(BENCH))
import bench_overrides  # noqa: E402  -- pure stdlib; same input fixes run.py applies
# molSimplify default geometry per coordination number (globalvars.defaultgeometry); no CN>8.
GEO = {2: "li", 3: "tpl", 4: "thd", 5: "tbp", 6: "oct", 7: "pbp", 8: "sqap"}


def _load_json(path: Path):
    path = Path(path)
    if str(path).endswith(".gz"):
        return json.loads(gzip.open(path, "rt", encoding="utf-8").read())
    return json.loads(path.read_text(encoding="utf-8"))


def _load_bundle(name: str):
    for cand in (BENCH / f"{name}.json.gz", BENCH / f"{name}.json",
                 BENCH / "benchmark_bundle.json" / f"{name}.json"):
        if cand.exists():
            return _load_json(cand)
    raise SystemExit(f"bundle {name} not found near {BENCH}")


# Our (crystal_assign) geometry names -> molSimplify built-in CORE short codes (the names of the
# `.dat` core files that ship in molSimplify/Data, == globalvars.defaultgeometry codes). molSimplify
# resolves `-geometry <code>` to Data/<code>.dat; passing a *full* name ("octahedral") makes it hunt
# for a custom core "octahedral.dat" that doesn't exist (FileNotFoundError) or falls into a broken
# placement path (KeyError '0-1'). molSimplify has NO dodecahedral (-> nearest CN8, square antiprism
# `sqap`) and NO CN9 core at all (tricapped_trigonal_prism has no code -> honest skip).
GEO_NAME = {
    "linear": "li", "trigonal_planar": "tpl",
    "tetrahedral": "thd", "square_planar": "sqp",
    "trigonal_bipyramidal": "tbp", "square_pyramidal": "spy",
    "octahedral": "oct", "pentagonal_bipyramidal": "pbp",
    "square_antiprism": "sqap", "dodecahedral": "sqap",
    # tricapped_trigonal_prism (CN9): no molSimplify core -> intentionally absent (skipped).
}


def build_input(rec: dict, lig_donors: list[list[int]], ff: str,
                geometry: "str | None" = None,
                coord: "int | None" = None, ffoption: str = "ba",
                sort_ligands: bool = True) -> "tuple[dict | None, str | None]":
    """Map a bundle record + per-ligand donor indices to a molSimplify input_dict.
    Returns (input_dict, error); error non-None means skip. `-smicat` is 1-based (molSimplify
    subtracts 1 internally), one bracket per ligand. Donor multiset is checked when rdkit is
    present (the bundle lists donors in crystal order, so compare multisets globally).

    ``geometry`` (a molSimplify geometry name, from the crystal target via GEO_NAME) overrides
    the default per-CN geometry -- so molSimplify builds the crystal's coordination geometry
    (e.g. square pyramidal, not the default tbp) instead of its CN default."""
    cn = rec["cn"]
    if geometry:
        geo = geometry
    elif cn in GEO:
        geo = GEO[cn]
    else:
        return None, f"molSimplify has no default CN{cn} geometry (pass --targets)"
    if Chem is not None:
        got = Counter()
        for smi, idxs in zip(rec["ligands"], lig_donors):
            mol = Chem.MolFromSmiles(smi)
            if mol is None:
                return None, f"unparseable SMILES {smi!r}"
            for ix in idxs:
                if ix >= mol.GetNumAtoms():
                    return None, f"donor index {ix} out of range for {smi!r}"
                got[mol.GetAtomWithIdx(ix).GetSymbol()] += 1
        if got != Counter(rec["donor_elements"]):
            return None, f"donor multiset {dict(got)} != bundle {dict(Counter(rec['donor_elements']))}"

    # Highest-denticity ligand FIRST. molSimplify's distgeom.findshape (2.0.0, lines 513-518, its
    # own TODO) never advances its SMILES-ligand counter, so every SMILES ligand is given the
    # denticity of the FIRST -smicat entry; a multidentate listed after a monodentate is then
    # treated as monodentate and ligand building dies with KeyError '0-1' (34/36 such failures
    # in the 2026-08-04 run). Ligand order carries no chemistry here (no isomer control), so a
    # stable descending-denticity order is just the input format molSimplify works with.
    order = (sorted(range(len(lig_donors)), key=lambda k: -len(lig_donors[k]))
             if sort_ligands else list(range(len(lig_donors))))
    ligands = [rec["ligands"][k] for k in order]
    lig_donors = [lig_donors[k] for k in order]
    smicat = [[i + 1 for i in d] for d in lig_donors]  # 0-based -> molSimplify 1-based
    n_donor = sum(len(d) for d in lig_donors)  # molSimplify validates -coord against this
    inp = {
        "-core": rec["metal"],
        # molSimplify has no hapticity model: -coord must equal the number of connecting donor
        # ATOMS in -smicat, and -geometry a built-in core for that CN. When the crystal is haptic
        # (donor atoms > sites) the site geometry is unrepresentable and the caller has already
        # swapped in the atom-CN default core (flagged haptic_fallback) -- so n_donor is always
        # the right -coord here.
        "-coord": str(n_donor),
        "-geometry": geo,
        "-lig": ",".join(ligands),
        "-ligocc": ",".join(["1"] * len(ligands)),
        "-smicat": str(smicat),
        "-ff": ff,
        "-ffoption": ffoption,    # molSimplify's own default is N = no optimization at all
        "-skipANN": "True",       # skip the ANN gate (only covers some metals; keeps runs uniform)
        "-name": rec["refcode"],
    }
    if 1 <= rec["ox"] <= 8:
        inp["-oxstate"] = str(rec["ox"])
    return inp, None


def _worker(inp: dict, q, seed: int = 0) -> None:
    """Run molSimplify for ONE complex in a child process; put the result on ``q``.

    molSimplify's UFF (OpenBabel) optimisation can enter a non-converging loop on some
    metal/ligand combinations -- an infinite HANG, not an exception, so it can't be caught in
    the parent. Isolating each build in its own process lets the parent kill a hung one on a
    timeout and carry on (see the main loop)."""
    buf = io.StringIO()  # molSimplify is chatty: keep the log clean, but keep its output for errors

    def _tail() -> str:  # e.g. the xtb output molSimplify prints before "XTB calculation failed"
        return buf.getvalue()[-2500:]

    try:
        # molSimplify draws its ligand conformers from the GLOBAL numpy/random RNGs without ever
        # seeding them (distgeom.Metrize is called without a seed), so the same complex can build
        # on one run and fail xtb on the next. Seeding here, per complex, makes a run
        # reproducible without touching molSimplify. (Inside the try: a failure here must reach
        # the queue, or the parent would just wait out the timeout.)
        import random

        import numpy as np
        random.seed(seed)
        np.random.seed(seed)
        with redirect_stdout(buf):
            _, emsg, diag = startgen_pythonic(inp, flag=True, write=False)
        if emsg:
            q.put(("error", str(emsg)[:160], _tail()))
        elif diag is not None and getattr(diag, "mol", False):
            q.put(("ok", diag.mol.writexyz("", writestring=True), diag.mol.natoms))
        else:
            q.put(("error", "molSimplify returned no structure", _tail()))
    except Exception as e:  # noqa: BLE001
        q.put(("error", f"{type(e).__name__}: {e}"[:160], _tail()))


def build_with_timeout(inp: dict, timeout: float, seed: int = 0):
    """Run ``_worker`` in a child process; return ``(status, payload)``. ``status`` is
    ``ok`` | ``error`` | ``timeout``. On timeout the hung child is terminated (then killed)."""
    ctx = mp.get_context("fork") if "fork" in mp.get_all_start_methods() else mp.get_context()
    q = ctx.Queue()
    p = ctx.Process(target=_worker, args=(inp, q, seed), daemon=True)
    p.start()
    try:
        res = q.get(timeout=timeout)  # drains the queue AND detects the hang
    except _queue.Empty:
        res = None
    p.join(2)
    if p.is_alive():
        p.terminate(); p.join(5)
        if p.is_alive():
            p.kill(); p.join()
    return res if res is not None else ("timeout", f"molSimplify hung; killed after {timeout:.0f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1", help="i/N")
    ap.add_argument("--bundle", default="benchmark_bundle")
    ap.add_argument("--donors", default="benchmark_donors.json")
    ap.add_argument("--refcodes", default="pilot_100.json",
                     help="JSON list to restrict to (the frozen pilot). '' = whole mapped bundle.")
    ap.add_argument("--ff", default="uff",
                     help="molSimplify force field / optimizer. 'uff' = shipped default (fast, "
                          "FF-level). 'xtb' = quality-matched to Architector/MeCoBi (slow).")
    ap.add_argument("--ffoption", default="ba",
                     help="when to optimize: b(efore) / a(fter) placement, ba = both (default), "
                          "n = none (molSimplify's own default).")
    # plain store_false, not BooleanOptionalAction: the molSimplify env runs Python 3.8
    ap.add_argument("--no-overrides", dest="overrides", action="store_false",
                     help="do NOT apply benchmark_overrides.json (confirmed OS/ligand/donor "
                          "fixes, applied by default as run.py does for MeCoBi).")
    ap.add_argument("--no-sort-ligands", dest="sort_ligands", action="store_false",
                     help="pass ligands in bundle order instead of highest-denticity first "
                          "(reproduces the KeyError '0-1' failures; see build_input).")
    ap.add_argument("--seed", type=int, default=0,
                     help="numpy/random seed set before each molSimplify build (its ligand "
                          "conformer generation is otherwise unseeded, so runs differ).")
    ap.add_argument("--only", default=None,
                     help="comma-separated refcodes to build (quick checks).")
    ap.add_argument("--hydrides", default=None, metavar="FILE",
                     help="benchmark_hydrides.json (benchmark root): put back the hydrides the "
                          "mined inputs lost -- one [H-] ligand each, OS and CN raised by one per "
                          "hydride, the crystal geometry re-read with the H (same correction run.py "
                          "--hydrides gives MeCoBi). Default: off.")
    ap.add_argument("--hydrides-only", action="store_true",
                     help="with --hydrides: build ONLY the corrected refcodes (the re-run that "
                          "replaces those rows of a finished run).")
    ap.add_argument("--xtb-threads", type=int, default=1,
                     help="OMP_NUM_THREADS for the xtb molSimplify spawns (default 1).")
    ap.add_argument("--targets", default=None,
                     help="benchmark_targets_*.json (enrich_bundle_geometry.py): build the "
                          "crystal-derived GEOMETRY per refcode (mapped via GEO_NAME) instead of "
                          "molSimplify's default per-CN geometry. DETERMINISTIC mode. (Isomer/"
                          "site assignment beyond the geometry is not controllable in this path.)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--timeout", type=float, default=900.0,
                     help="per-complex wall-clock limit (s). molSimplify's UFF opt hangs on "
                          "some inputs; a hung build is killed after this and logged as a "
                          "'timeout' failure so the shard finishes instead of freezing for hours.")
    ap.add_argument("--out-dir", default=None,
                     help="write the results JSONL + molsim_structures/ into this dir. Default: "
                          "'molsimplify_det/' (uff) or 'molsimplify_det_<ff>/' (under "
                          "pilot100/molsimplify/) in deterministic mode (--targets), else "
                          "pilot100/molsimplify/ itself.")
    cfg = ap.parse_args()
    i, n = (int(x) for x in cfg.shard.split("/"))
    # xtb (spawned by molSimplify, inheriting this env) gets a fixed thread count so parallel
    # shards don't oversubscribe.
    os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = str(cfg.xtb_threads)
    os.environ.setdefault("OMP_STACKSIZE", "1G")
    overrides = bench_overrides.load() if cfg.overrides else {}
    hyd = {}
    if cfg.hydrides:
        import hydrides as HY   # numpy only; imported lazily so a plain run needs nothing new
        hyd = HY.load(cfg.hydrides)
        if not hyd:
            raise SystemExit(f"--hydrides {cfg.hydrides}: no corrections loaded")

    bundle = _load_bundle(cfg.bundle)
    donors = _load_json(BENCH / cfg.donors)
    targets = _load_json(PILOT / cfg.targets if not Path(cfg.targets).is_absolute()
                         else cfg.targets) if cfg.targets else None
    keep = set(_load_json(PILOT / cfg.refcodes)) if cfg.refcodes else None
    only = {x.strip() for x in cfg.only.split(",") if x.strip()} if cfg.only else None

    # Deterministic runs (--targets) get their own labelled folder so they never mix with a plain
    # default-geometry run; an explicit --out-dir still wins.
    if cfg.out_dir:
        base = HERE / cfg.out_dir
    elif targets is not None:
        base = HERE / (("molsimplify_det" if cfg.ff == "uff" else f"molsimplify_det_{cfg.ff}")
                       + ("_hyd" if cfg.hydrides else ""))
    else:
        base = HERE
    base.mkdir(parents=True, exist_ok=True)
    structures = base / "molsim_structures"; structures.mkdir(exist_ok=True)
    out = base / f"_molsim_results_shard{i}of{n}.jsonl"
    done = {json.loads(l)["refcode"] for l in out.read_text().splitlines()} if out.exists() else set()

    recs = [r for k, r in enumerate(bundle)
            if k % n == i and r["refcode"] in donors
            and (keep is None or r["refcode"] in keep)
            and (only is None or r["refcode"] in only)
            and (not cfg.hydrides_only or r["refcode"] in hyd)]
    if cfg.limit:
        recs = recs[:cfg.limit]

    fh = out.open("a", encoding="utf-8")
    built = 0
    t0 = time.perf_counter()
    for k, r in enumerate(recs, 1):
        rc = r["refcode"]
        if rc in done:
            continue
        r = bench_overrides.record(r, overrides)          # confirmed OS/charge input fixes
        lig_donors = bench_overrides.donors(rc, donors[rc], overrides)
        h = hyd.get(rc)                                   # located hydrides the mining lost
        if h:
            r, lig_donors = HY.record(r, h), HY.donors(lig_donors, h)
        row = {"refcode": rc, "metal": r["metal"], "ox": r["ox"], "cn": r["cn"],
               "ff": cfg.ff, "ffoption": cfg.ffoption, "override": rc in overrides,
               "sort_ligands": cfg.sort_ligands, "seed": cfg.seed,
               "built": False}
        if h:
            row["hydrides_added"] = h["n_h"]
        geometry = site_cn = None
        default_geo = None  # molSimplify's own per-CN default core; the default_fallback geometry
        # a hydride-corrected complex takes the geometry re-read WITH the H
        tg = None if targets is None else (h.get("target") if h else targets.get(rc))
        if tg and tg.get("geometry"):
            site_cn = tg.get("site_cn")
            row["target_geometry"] = tg["geometry"]
            n_donor = sum(len(d) for d in lig_donors)
            if site_cn is not None and site_cn < n_donor:
                # Haptic/collapsed coordination: more donor atoms than sites (e.g. an eta-arene's
                # 3 atoms share 1 site). molSimplify is atom-based with no site model, so the
                # crystal's site-space geometry can't be built -- fall back to its atom-CN default
                # core (built from all n_donor atoms) and flag it so the report can annotate.
                geometry = GEO.get(n_donor)
                row["haptic_fallback"] = True
                if geometry is None:
                    row["error"] = (f"skip: haptic CN{n_donor}->{site_cn} sites; molSimplify has "
                                    f"no CN{n_donor} core")
                    fh.write(json.dumps(row) + "\n"); fh.flush()
                    continue
            else:
                geometry = GEO_NAME.get(tg["geometry"])
                if geometry is None:
                    row["error"] = f"skip: no molSimplify geometry for {tg['geometry']!r}"
                    fh.write(json.dumps(row) + "\n"); fh.flush()
                    continue
                # The crystal core can trip molSimplify's backbone-combination tables (KeyError
                # '0-1') for multidentate ligands on a non-default core. Keep its OWN per-CN default
                # core as a fallback to retry with -- recovers the cases where the crystal geometry
                # differs from the default and the default has a fuller placement table (e.g.
                # square_planar->thd, square_pyramidal->tbp). Same-as-default geometries (oct, tbp,
                # pbp...) get no second attempt: retrying the identical core would just fail again.
                default_geo = GEO.get(n_donor)
        row["geometry"] = geometry
        inp, err = build_input(r, lig_donors, cfg.ff, geometry=geometry, coord=site_cn,
                               ffoption=cfg.ffoption, sort_ligands=cfg.sort_ligands)
        if err:
            row["error"] = f"skip: {err}"[:160]
            fh.write(json.dumps(row) + "\n"); fh.flush()
            continue
        ts = time.perf_counter()
        status, *payload = build_with_timeout(inp, cfg.timeout, cfg.seed)  # isolated: a hang can't freeze us
        # default_fallback: a crystal-geometry build that ERRORED (not a hang) gets one retry on
        # molSimplify's own default core for this CN. Flagged so the report can keep the strict
        # "built the crystal geometry" comparison separate from raw coverage.
        if status == "error" and default_geo and default_geo != geometry:
            inp2, err2 = build_input(r, lig_donors, cfg.ff, geometry=default_geo, coord=site_cn,
                                     ffoption=cfg.ffoption, sort_ligands=cfg.sort_ligands)
            if not err2:
                s2, *p2 = build_with_timeout(inp2, cfg.timeout, cfg.seed)
                if s2 == "ok":
                    # why the crystal geometry failed, kept before the fallback overwrites it
                    row["primary_error"] = payload[0]
                    if len(payload) > 1:
                        row["primary_log_tail"] = payload[1]
                    status, payload = s2, p2
                    row["default_fallback"] = True
                    row["geometry"] = default_geo
        row["wall_s"] = round(time.perf_counter() - ts, 2)
        if status == "ok":
            xyz, natoms = payload
            (structures / f"{rc}.xyz").write_text(xyz, encoding="utf-8")
            row["built"] = True; built += 1
            row["natoms"] = natoms
        else:  # "error" | "timeout"
            row["error"] = payload[0]
            if len(payload) > 1:
                row["log_tail"] = payload[1]  # molSimplify/xtb output before the failure
            if status == "timeout":
                row["timeout"] = True
                print(f"  shard {i}/{n}: {rc} TIMEOUT ({cfg.timeout:.0f}s) -- killed, continuing",
                      flush=True)
        fh.write(json.dumps(row) + "\n"); fh.flush()
        if k % 10 == 0:
            print(f"  shard {i}/{n}: {k}/{len(recs)} built={built} "
                  f"({(time.perf_counter()-t0)/k:.1f}s/cpx wall)", flush=True)
    fh.close()
    print(f"shard {i}/{n} done: {built} built of {len(recs)} -> {out}")


if __name__ == "__main__":
    main()
