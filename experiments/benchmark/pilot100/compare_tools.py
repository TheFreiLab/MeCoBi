"""Pilot-100 head-to-head: MeCoBi vs MetalloGen vs molSimplify vs Architector.

Every tool's structures are re-scored HERE, by the same code, against the same crystal reference:
``run.score`` (shape match, poly-CShM, donor-donor distance-matrix RMSD, M-L bond RMSD, on the
haptic-collapsed sphere) + depth-2 c-kmRMSD (``ckmrmsd``). Success and timing come from each
tool's own result JSONL. Writes a Markdown report and two CSVs next to this script.

Reported per tool:
  * coverage   attempted / built out of the 100 pilot refcodes (a tool that never attempts a
               complex -- no m-SMILES, no molSimplify core -- counts as a failure), timeouts
  * timing     per-structure seconds (MeCoBi: build_s = the relaxed build alone; others: wall_s)
               over successful builds, and over all attempts with timeouts at their cap (a lower
               bound); CPU hours = sum over all attempts; shards/threads/host from run_meta.json
  * quality    shape-match % + median/mean of c-kmRMSD, poly-CShM, dmat RMSD, bond RMSD
               (a) over each tool's own builds, and (b) PAIRED over the refcodes every tool built,
               with a Wilcoxon signed-rank test of each tool against MeCoBi

Run dirs (relative to the benchmark root, or absolute) default to:
    MeCoBi       newest pilot100/mecobi/fair_*/            (run_pilot100.py)
    molSimplify  pilot100/molsimplify/molsimplify_det_xtb/ (run_pilot100_xtb.py)
    MetalloGen   pilot100/metallogen/metallogen_det/, else arch_comparison/metallogen/
                 structures: metallogen_structures_minE/ (metallogen_repick.py) if present
    Architector  pilot100/architector/, else arch_comparison/architector/ (.xyz only, no timing)
A tool whose dir is missing is skipped (and said so).

    python pilot100/compare_tools.py
    python pilot100/compare_tools.py --mecobi pilot100/mecobi/fair_7cef10b --exclude ''
"""
from __future__ import annotations

import argparse
import csv
import glob
import gzip
import json
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent   # pilot100/
BENCH = HERE.parent                      # benchmark root: run.py scoring + frozen data
REPO = BENCH.parents[1]
sys.path.insert(0, str(BENCH))
import bench_overrides  # noqa: E402
import run as R  # noqa: E402
import hydrides  # noqa: E402
import dmae  # noqa: E402
import donor_map  # noqa: E402
from ckmrmsd import build_core_like, ckmrmsd, core_size  # noqa: E402
from metrics import parse_xyz  # noqa: E402

METRICS = [("ckmrmsd", "c-kmRMSD (Å)"), ("dmae3", "D-MAE3 (Å)"), ("poly_cshm", "poly-CShM"),
           ("dmat_rmsd", "dmat RMSD (Å)"), ("bond_rmsd", "bond RMSD (Å)")]
# MetalloGen inputs that differ from what MeCoBi/molSimplify now get:
# benchmark_overrides corrections + the KILHAO donor fix, all after the 2026-08-04 MetalloGen run.
DEFAULT_EXCLUDE = "HIFZEF,ROQDOQ,MUTSAX,KILHAO"


# ----------------------------------------------------------------------------- run discovery
def _abs(p: str) -> Path:
    q = Path(p)
    return (q if q.is_absolute() else (BENCH / q)).resolve()


def _newest(pattern: str) -> "Path | None":
    dirs = [Path(d) for d in glob.glob(str(BENCH / pattern)) if Path(d).is_dir()]
    return max(dirs, key=lambda d: d.stat().st_mtime) if dirs else None


def _first(*cands) -> "Path | None":
    for c in cands:
        if c is not None and Path(c).is_dir():
            return Path(c)
    return None


def _overlay(d, structures: str) -> "dict | None":
    """A partial re-run laid over a tool's full run (see discover): its rows + structures dir."""
    if d is None or not Path(d).is_dir():
        return None
    return {"dir": Path(d), "structures": Path(d) / structures}


def xyz_path(s: dict, rc: str) -> Path:
    """Where ``rc``'s structure lives for a discovered tool: the overlay re-run's, when that
    re-run attempted the refcode (even if it failed -- the old build no longer counts)."""
    if rc in s.get("overlay_rows", {}):
        return s["overlay"]["structures"] / f"{rc}.xyz"
    return s["structures"] / f"{rc}.xyz"


def discover(cfg) -> dict:
    """{tool: {dir, jsonl_glob, structures, time_key}} for every tool found.

    A tool may also carry an OVERLAY: a partial re-run (the hydride-corrected complexes, built by
    the tool's runner with --hydrides) whose rows and structures replace the full run's for exactly
    the refcodes it attempted -- so 7 re-built complexes update the comparison without re-running
    the other 93. Found next to the full run (``*_hyd``) or passed as --<tool>-hyd."""
    mg_dir = _abs(cfg.metallogen) if cfg.metallogen else _first(
        HERE / "metallogen" / "metallogen_det", REPO / "arch_comparison" / "metallogen")
    mg_struct = None
    if mg_dir is not None:
        mg_struct = _first(mg_dir / "metallogen_structures_minE", mg_dir / "metallogen_structures")
    ar_dir = _abs(cfg.architector) if cfg.architector else _first(
        HERE / "architector" / "arch_structures", REPO / "arch_comparison" / "architector")
    ar_json = None
    if ar_dir is not None:  # arch_run.py writes the JSONL next to arch_structures/
        ar_json = (ar_dir.parent if ar_dir.name == "arch_structures" else ar_dir)
    specs = {
        "MeCoBi": dict(dir=_abs(cfg.mecobi) if cfg.mecobi else _newest("pilot100/mecobi/fair_*"),
                       jsonl="_results_shard*.jsonl", structures="structures", time_key="build_s"),
        "MetalloGen": dict(dir=mg_dir, jsonl="_metallogen_results_shard*.jsonl",
                           structures=mg_struct, time_key="wall_s"),
        "molSimplify": dict(dir=_abs(cfg.molsimplify) if cfg.molsimplify
                            else HERE / "molsimplify" / "molsimplify_det_xtb",
                            jsonl="_molsim_results_shard*.jsonl", structures="molsim_structures",
                            time_key="wall_s"),
        "Architector": dict(dir=ar_json, jsonl="_arch_results_shard*.jsonl", structures=ar_dir,
                            time_key="wall_s"),
    }
    g = lambda k: getattr(cfg, k, None)  # noqa: E731 -- the HTML report's parser has no *_hyd args
    overlays = {
        "MetalloGen": _overlay(_abs(g("metallogen_hyd")) if g("metallogen_hyd") else _first(
            HERE / "metallogen" / "metallogen_det_hyd", REPO / "arch_comparison" / "metallogen_hyd"),
            "metallogen_structures"),
        "molSimplify": _overlay(_abs(g("molsimplify_hyd")) if g("molsimplify_hyd") else _first(
            HERE / "molsimplify" / "molsimplify_det_xtb_hyd",
            REPO / "arch_comparison" / "molsimplify_hyd"), "molsim_structures"),
        "Architector": _overlay(_abs(g("architector_hyd")) if g("architector_hyd") else _first(
            HERE / "architector" / "arch_hyd", REPO / "arch_comparison" / "architector_hyd"),
            "arch_structures"),
    }
    found = {}
    for tool, s in specs.items():
        d = s["dir"]
        if d is None or not Path(d).is_dir():
            print(f"[skip] {tool}: run dir not found ({d})")
            continue
        sdir = s["structures"]
        sdir = Path(sdir) if isinstance(sdir, Path) else Path(d) / sdir
        if not sdir.is_dir():
            print(f"[skip] {tool}: no structures dir ({sdir})")
            continue
        found[tool] = {**s, "dir": Path(d), "structures": sdir, "overlay": overlays.get(tool),
                       "overlay_rows": (load_rows(overlays[tool]["dir"], s["jsonl"])
                                        if overlays.get(tool) else {})}
    return found


def load_rows(run_dir: Path, pattern: str) -> dict:
    """Final attempt per refcode. Launch failures (run_status 'error', wall_s 0 -- MetalloGen
    retries) never override a real attempt; otherwise the last row wins (resumed runs)."""
    rows: dict[str, dict] = {}
    for f in sorted(glob.glob(str(run_dir / pattern))):
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("run_status") == "error" and r["refcode"] in rows:
                continue
            rows[r["refcode"]] = r
    return rows


def off_target(tool: str, r: dict) -> "bool | None":
    """Was this build made in a geometry OTHER than the crystal one the tool was given?"""
    if tool == "molSimplify":   # retried on its default CN core, or haptic -> atom-CN core
        return bool(r.get("default_fallback") or r.get("haptic_fallback"))
    if tool == "MeCoBi":        # stale/unfit site map -> MeCoBi picked the geometry itself
        return str(r.get("build_mode", "")).startswith("heuristic")
    if tool == "Architector":   # arch_run.py --targets: fell back to (or, haptic, kept) its own
        if "target_geometry" not in r:   # search over the cores of the CN. A default-mode run
            return None                  # always chose the geometry itself: not applicable.
        return r.get("level") == "default"
    return False                # MetalloGen: geometry fixed by the m-SMILES


def run_meta(run_dir: Path) -> dict:
    p = run_dir / "run_meta.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


# ----------------------------------------------------------------------------- scoring
def score(xyz: str, metal: str, cn: int, sphere: dict, core, rec=None, spec=None,
          core3=None) -> dict:
    """Every metric for one build. ``rec`` (bundle record) + ``spec`` (its benchmark_donors row)
    let the build's donors be found on its molecular graph (donor_map); without them, or when a
    ligand cannot be matched, the nearest atoms are used (``donor_source``). ``core3``: the
    crystal depth-3 core for D-MAE3."""
    out = {}
    didx = donor_map.from_xyz(xyz, metal, rec["ligands"], spec) if rec and spec else None
    try:
        sc = R.score(xyz, metal, cn, sphere, didx) or {}
        out.update({k: sc.get(k) for k in ("shape_match", "poly_cshm", "dmat_rmsd", "bond_rmsd",
                                           "n_hydride", "cn_expected", "cn_detected",
                                           "cn_match", "donor_source")})
    except Exception:  # noqa: BLE001 -- unscorable geometry counts as a missing value
        pass
    if core is not None:
        try:
            core, bc = build_core_like(core, xyz, metal, didx)   # hydride-aware when both carry H
            if bc:
                ck, nm = ckmrmsd(core, bc)
                out.update({"ckmrmsd": round(ck, 4), "ckm_n_matched": nm,
                            "ckm_core_n": core_size(core)})
            else:
                out["ckmrmsd"] = None
        except Exception:  # noqa: BLE001
            out["ckmrmsd"] = None
    if core3 is not None:
        try:
            n_heavy = len(sphere["donors"]) - hydrides.n_in_sphere(sphere)
            bc3 = dmae.core_from_xyz(xyz, metal, n_heavy, donor_idx=didx)
            if bc3:
                v, nm = dmae.dmae(core3, bc3)
                out.update({"dmae3": round(v, 4), "dmae3_n_matched": nm,
                            "dmae3_core_n": dmae.core_size(core3)})
        except Exception:  # noqa: BLE001
            out["dmae3"] = None
    p = out.get("poly_cshm")
    if isinstance(p, (int, float)) and (not math.isfinite(p) or p > 100):
        out["poly_cshm"] = 100.0  # same clamp as full30k: collapsed polyhedron = maximally off
    return out


def _vals(rows, key):
    return [r[key] for r in rows if isinstance(r.get(key), (int, float)) and math.isfinite(r[key])]


def _q(v, q):
    return st.quantiles(v, n=4, method="inclusive")[q] if len(v) > 1 else (v[0] if v else None)


def _f(x, nd=2):
    return "–" if x is None else f"{x:.{nd}f}"


def wilcoxon_p(a, b) -> "float | None":
    try:
        from scipy.stats import wilcoxon
        d = [x - y for x, y in zip(a, b)]
        if len(d) < 6 or all(abs(x) < 1e-12 for x in d):
            return None
        return float(wilcoxon(a, b).pvalue)
    except Exception:  # noqa: BLE001
        return None


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mecobi", help="MeCoBi run dir (JSONL + structures/)")
    ap.add_argument("--molsimplify", help="molSimplify run dir (JSONL + molsim_structures/)")
    ap.add_argument("--metallogen", help="MetalloGen run dir (JSONL + metallogen_structures*/)")
    ap.add_argument("--architector", help="dir holding the Architector .xyz files")
    ap.add_argument("--molsimplify-hyd", help="molSimplify re-run of the hydride complexes "
                    "(default: molsimplify/molsimplify_det_xtb_hyd if present)")
    ap.add_argument("--metallogen-hyd", help="MetalloGen re-run of the hydride complexes "
                    "(default: metallogen/metallogen_det_hyd if present)")
    ap.add_argument("--architector-hyd", help="Architector re-run of the hydride complexes "
                    "(default: architector/arch_hyd if present)")
    ap.add_argument("--refcodes", default=str(HERE / "pilot_100.json"))
    ap.add_argument("--cores-d3", default=None,
                    help="crystal depth-3 cores for D-MAE3 (dataprep/extract_cores_dk.py); "
                         "default benchmark_cores_d3_pilot.json.gz")
    ap.add_argument("--spheres", default=None,
                    help="default: benchmark_spheres_elem.json.gz (donors chosen by declared element, "
                         "dataprep/extract_spheres_by_element.py), else _fixed, else the frozen one")
    ap.add_argument("--hydrides", default=None, metavar="FILE",
                    help="benchmark_hydrides.json: score against the crystal sphere WITH its "
                         "located hydrides -- for a refcode only when every tool's build carries "
                         "them (i.e. all were built from the corrected inputs); otherwise that "
                         "refcode keeps the heavy-donor reference for everyone.")
    ap.add_argument("--exclude", default=DEFAULT_EXCLUDE,
                    help="refcodes left out of the PAIRED comparison (comma list; '' = none). "
                         "Default: the MetalloGen input-caveat complexes.")
    ap.add_argument("--strict", action="store_true",
                    help="leave OFF-TARGET builds out of every quality table: molSimplify "
                         "default-core / haptic fallbacks and MeCoBi heuristic-geometry builds (a "
                         "geometry other than the crystal's). Success %% still counts them.")
    ap.add_argument("--timeout", type=float, default=900.0,
                    help="per-complex cap the runs used; timeouts are counted at this value.")
    ap.add_argument("--skip", default="",
                    help="comma list of tools to leave out, e.g. molSimplify (a stale or partial "
                         "run would otherwise shrink the PAIRED set for everyone).")
    ap.add_argument("--out", default=str(HERE / "compare_tools_report.md"))
    cfg = ap.parse_args()

    tools = discover(cfg)
    for tl in (x.strip() for x in cfg.skip.split(",") if x.strip()):
        if tools.pop(tl, None) is not None:
            print(f"[skip] {tl}: left out by --skip")
    if not tools:
        raise SystemExit("no tool results found")
    pilot = json.loads(Path(cfg.refcodes).read_text())
    overrides = bench_overrides.load()
    bundle = {r["refcode"]: bench_overrides.record(r, overrides)
              for r in json.load(gzip.open(BENCH / "benchmark_bundle.json.gz", "rt"))}
    sph_path = Path(cfg.spheres) if cfg.spheres else (
        next(p for p in (BENCH / "benchmark_spheres_elem.json.gz",
                         BENCH / "benchmark_spheres_fixed.json.gz",
                         BENCH / "benchmark_spheres.json.gz") if p.exists()))
    spheres = json.load(gzip.open(sph_path, "rt")) if str(sph_path).endswith(".gz") \
        else json.loads(sph_path.read_text())
    core_path = next(p for p in (BENCH / "benchmark_cores_elem.json.gz",
                                 BENCH / "benchmark_cores.json.gz") if p.exists())
    cores = json.load(gzip.open(core_path, "rt"))
    c3p = Path(cfg.cores_d3) if cfg.cores_d3 else BENCH / "benchmark_cores_d3_pilot.json.gz"
    cores3 = json.load(gzip.open(c3p, "rt")) if c3p.exists() else {}
    donors = json.loads((BENCH / "benchmark_donors.json").read_text())
    exclude = {x.strip() for x in cfg.exclude.split(",") if x.strip()}
    hyd = hydrides.load(cfg.hydrides) if cfg.hydrides else {}

    def carries_hydrides(xyz_p: Path, metal: str, n_h: int) -> bool:
        syms, P = parse_xyz(xyz_p.read_text(encoding="utf-8"))
        return metal in syms and len(hydrides.build_hydrides(syms, P, syms.index(metal), n_h)) == n_h

    n_hyd_ref = 0
    for rc in pilot:   # same reference for every tool: with the H only if all builds have it
        h = hyd.get(rc)
        if not h or rc not in spheres:
            continue
        xyzs = [p for p in (xyz_path(s, rc) for s in tools.values()) if p.exists()]
        if xyzs and all(carries_hydrides(p, bundle[rc]["metal"], h["n_h"]) for p in xyzs):
            spheres[rc] = hydrides.sphere(spheres[rc], h)
            if rc in cores:
                cores[rc] = hydrides.core(cores[rc], h)
            n_hyd_ref += 1
    if hyd:
        print(f"hydride-corrected reference used for {n_hyd_ref} refcodes "
              f"({sum(rc in hyd for rc in pilot)} in the pilot have a located hydride)")

    def usable(r: dict) -> bool:  # a build that enters the quality tables
        return r["built"] and not (cfg.strict and r.get("off_target"))
    print(f"reference spheres: {sph_path.name}")

    per = defaultdict(dict)   # tool -> refcode -> record
    meta = {}
    for tool, s in tools.items():
        rows = {**load_rows(s["dir"], s["jsonl"]), **s["overlay_rows"]}
        meta[tool] = {**run_meta(s["dir"]), "has_jsonl": bool(rows),
                      "dir": str(s["dir"]), "structures": str(s["structures"])}
        print(f"{tool:12} {len(rows):3} JSONL rows, structures: {s['structures']}")
        if s["overlay_rows"]:
            print(f"{'':12} + {len(s['overlay_rows'])} re-run rows laid over it from "
                  f"{s['overlay']['dir']}: {', '.join(sorted(s['overlay_rows']))}")
        for rc in pilot:
            r = rows.get(rc, {})
            rec = bundle[rc]
            xyz_p = xyz_path(s, rc)
            built = xyz_p.exists() and (bool(r.get("built")) if rows else True)
            t = r.get(s["time_key"], r.get("wall_s"))
            timeout = r.get("run_status") == "timeout" or bool(r.get("timeout"))
            d = {"refcode": rc, "tool": tool, "metal": rec["metal"], "cn": rec["cn"],
                 "attempted": (rc in rows) if rows else built, "built": built,
                 "timeout": timeout,
                 "time_s": (min(t, cfg.timeout) if timeout else t)
                 if isinstance(t, (int, float)) else None,
                 "error": (r.get("error") or "")[:80],
                 # built, but NOT in the crystal geometry the tool was given (None = unknown)
                 "off_target": off_target(tool, r) if built else False}
            if built and rc in spheres:
                d.update(score(xyz_p.read_text(encoding="utf-8"), rec["metal"], rec["cn"],
                               spheres[rc], cores.get(rc), rec,
                               bench_overrides.donors(rc, donors.get(rc), overrides),
                               cores3.get(rc)))
            per[tool][rc] = d

    names = list(tools)
    L = ["# Pilot 100 — tool comparison\n",
         f"Reference: `{sph_path.name}` + `{core_path.name}`; all structures re-scored by "
         "the same code (`run.score` + `ckmrmsd`). Pilot: "
         f"{len(pilot)} refcodes.\n"]
    L.append("## Runs\n\n| tool | dir | host | shards × threads | budget (s) |\n|---|---|---|---|---|")
    for tl in names:
        m = meta[tl]
        d = Path(m["dir"])
        L.append(f"| {tl} | `{d.relative_to(REPO) if REPO in d.parents else d}` | "
                 f"{m.get('host', '?')} | {m.get('shards', '?')} × "
                 f"{m.get('xtb_threads', '?')} | "
                 f"{m.get('xtb_timeout_s', m.get('timeout_s', '?'))} |")
    L.append("")

    # --- coverage + timing
    summary = []
    L.append("## Success and timing\n")
    L.append("| tool | attempted | built | success % | off-target geom. | timeouts | "
             "median s (built) | p25–p75 s "
             "(built) | median s (all, t/o at cap) | CPU h (all) |\n|" + "---|" * 10)
    for tl in names:
        rs = list(per[tl].values())
        b = [r for r in rs if r["built"]]
        tb = _vals(b, "time_s")
        ta = _vals([r for r in rs if r["attempted"]], "time_s")
        row = {"tool": tl, "attempted": sum(r["attempted"] for r in rs), "built": len(b),
               "success_pct": round(100 * len(b) / len(pilot), 1),
               "off_target": (None if all(r["off_target"] is None for r in rs if r["built"])
                              else sum(bool(r["off_target"]) for r in rs)),
               "timeouts": sum(r["timeout"] for r in rs),
               "time_median_built": st.median(tb) if tb else None,
               "time_median_all": st.median(ta) if ta else None,
               "cpu_h": sum(ta) / 3600 if ta else None}
        summary.append(row)
        L.append(f"| {tl} | {row['attempted']} | {len(b)} | {row['success_pct']:.0f} | "
                 f"{'–' if row['off_target'] is None else row['off_target']} | "
                 f"{row['timeouts']} | {_f(row['time_median_built'], 1)} | "
                 f"{(_f(_q(tb, 0), 0) + '–' + _f(_q(tb, 2), 0)) if tb else '–'} | "
                 f"{_f(row['time_median_all'], 1)} | "
                 f"{_f(row['cpu_h'], 2)} |")
    L.append("\nMeCoBi time = `build_s` (relaxed build alone; `wall_s` for older runs without "
             "it); others = `wall_s` of the whole "
             "tool call. A timeout is counted at the cap, so the all-attempts median is a lower "
             "bound. Tools without a JSONL have no timing.\n")

    # --- paired timing: each tool vs MeCoBi on the refcodes BOTH built (like-for-like complexes)
    if "MeCoBi" in names:
        L.append("## Paired timing vs MeCoBi (refcodes both built)\n")
        L.append("| tool | n | MeCoBi median s | tool median s | median ratio tool/MeCoBi | "
                 "MeCoBi faster in | tool threads/process |\n|" + "---|" * 7)
        for tl in names:
            if tl == "MeCoBi":
                continue
            pairs = [(per["MeCoBi"][rc]["time_s"], per[tl][rc]["time_s"]) for rc in pilot
                     if per["MeCoBi"][rc]["built"] and per[tl][rc]["built"]
                     and isinstance(per["MeCoBi"][rc]["time_s"], (int, float))
                     and isinstance(per[tl][rc]["time_s"], (int, float))
                     and per["MeCoBi"][rc]["time_s"] > 0]
            thr = meta[tl].get("xtb_threads", "unknown")
            if not pairs:
                L.append(f"| {tl} | 0 | – | – | – | – | {thr} |")
                continue
            ratio = [b / a for a, b in pairs]
            L.append(f"| {tl} | {len(pairs)} | {st.median(a for a, _ in pairs):.1f} | "
                     f"{st.median(b for _, b in pairs):.1f} | {st.median(ratio):.1f}× | "
                     f"{sum(a < b for a, b in pairs)}/{len(pairs)} | {thr} |")
        L.append("\nRatio > 1 = the tool is slower than MeCoBi on the same complex. Timings are "
                 "only comparable at equal cores per build: MeCoBi and molSimplify run 1 xtb "
                 "thread per shard (run_meta.json). MetalloGen hard-codes ORCA nproc=1, but its "
                 "xtb inherited OMP_NUM_THREADS (unset). Architector runs xtb-python in process and "
                 "writes no run_meta.json: it used 1 thread only if OMP_NUM_THREADS=1 was exported "
                 "for the run (the runs given the crystal geometry were; the earlier default-mode "
                 "run was not, so each of its processes could use every core and its times are "
                 "optimistic per core).\n")

    # --- quality, own builds
    L.append("## Quality over each tool's own builds\n")
    hdr = "| tool | scored | CN match % | shape match % | " + " | ".join(
        f"{lab} median / mean" for _, lab in METRICS) + " |"
    L.append(hdr + "\n|" + "---|" * (4 + len(METRICS)))
    for tl, row in zip(names, summary):
        b = [r for r in per[tl].values() if usable(r)]
        sh = [r["shape_match"] for r in b if r.get("shape_match") is not None]
        row["shape_pct"] = round(100 * sum(sh) / len(sh), 1) if sh else None
        cm = [r["cn_match"] for r in b if r.get("cn_match") is not None]
        row["cn_match_pct"] = round(100 * sum(cm) / len(cm), 1) if cm else None
        cells = []
        for k, _ in METRICS:
            v = _vals(b, k)
            row[f"{k}_median"] = st.median(v) if v else None
            row[f"{k}_mean"] = st.fmean(v) if v else None
            cells.append(f"{_f(row[f'{k}_median'])} / {_f(row[f'{k}_mean'])}")
        L.append(f"| {tl} | {len(sh)} | {_f(row['cn_match_pct'], 0)} | "
                 f"{_f(row['shape_pct'], 0)} | " + " | ".join(cells) + " |")
    partial = []
    for tl in names:
        ck = [r for r in per[tl].values() if usable(r) and r.get("ckm_core_n")]
        short = sum(1 for r in ck if r["ckm_n_matched"] < r["ckm_core_n"])
        partial.append(f"{tl} {short}/{len(ck)}")
    graph = []
    for tl in names:
        rs = [r for r in per[tl].values() if usable(r) and r.get("donor_source")]
        graph.append(f"{tl} {sum(r['donor_source'] == 'graph' for r in rs)}/{len(rs)}")
    L.append("\n**CN match** = the build has exactly the crystal CN of atoms bonded to the metal "
             "(Cordero radii + 0.4 Å, lengthened per metal–donor pair to the crystal reference's "
             "99th percentile) and every scored donor is one of them. Donors are found on each "
             "build's molecular graph (ligand fragments matched to the input SMILES; builds "
             f"where that worked: {'; '.join(graph)}), else the nearest atoms. **D-MAE3** = mean "
             "|Δd| over all pairs of the metal and heavy atoms within 3 bonds (MetalloGen's "
             "metric; geometric atom correspondence, see `dmae.py`).")
    L.append("\nc-kmRMSD is computed over the matched atoms only. Builds whose depth-2 core matched "
             "fewer atoms than the crystal core (missing atoms or a different composition): "
             + "; ".join(partial) + ".\n")

    # --- paired
    common = [rc for rc in pilot if rc not in exclude
              and all(usable(per[tl][rc]) and per[tl][rc].get("ckmrmsd") is not None
                      for tl in names)]
    L.append(f"## Paired: the {len(common)} refcodes every tool built and scored\n")
    if exclude:
        L.append(f"Excluded: {', '.join(sorted(exclude))} (input caveats).\n")
    L.append("| tool | shape match % | " + " | ".join(f"{lab} median" for _, lab in METRICS)
             + " |\n|" + "---|" * (2 + len(METRICS)))
    paired = {}
    for tl in names:
        rs = [per[tl][rc] for rc in common]
        sh = [r["shape_match"] for r in rs if r.get("shape_match") is not None]
        paired[tl] = {k: [per[tl][rc].get(k) for rc in common] for k, _ in METRICS}
        L.append(f"| {tl} | {_f(100 * sum(sh) / len(sh) if sh else None, 0)} | " + " | ".join(
            _f(st.median(_vals(rs, k)) if _vals(rs, k) else None) for k, _ in METRICS) + " |")
    if "MeCoBi" in names and len(names) > 1 and common:
        L.append("\n**Against MeCoBi** (same refcodes): count where MeCoBi is better (lower) / "
                 "worse, and the Wilcoxon signed-rank p-value.\n")
        L.append("| tool | " + " | ".join(lab for _, lab in METRICS) + " |\n|"
                 + "---|" * (1 + len(METRICS)))
        for tl in names:
            if tl == "MeCoBi":
                continue
            cells = []
            for k, _ in METRICS:
                pairs = [(a, b) for a, b in zip(paired["MeCoBi"][k], paired[tl][k])
                         if isinstance(a, (int, float)) and isinstance(b, (int, float))]
                better = sum(a < b for a, b in pairs)
                worse = sum(a > b for a, b in pairs)
                p = wilcoxon_p([a for a, _ in pairs], [b for _, b in pairs])
                cells.append(f"{better} / {worse} (p={'–' if p is None else f'{p:.2g}'})")
            L.append(f"| {tl} | " + " | ".join(cells) + " |")
    L.append("")

    # --- by CN (own builds)
    L.append("## By coordination number (own builds): success % · c-kmRMSD median\n")
    cns = sorted({bundle[rc]["cn"] for rc in pilot})
    L.append("| CN | n | " + " | ".join(names) + " |\n|" + "---|" * (2 + len(names)))
    for cn in cns:
        rcs = [rc for rc in pilot if bundle[rc]["cn"] == cn]
        cells = []
        for tl in names:
            b = [per[tl][rc] for rc in rcs if per[tl][rc]["built"]]
            v = _vals([r for r in b if usable(r)], "ckmrmsd")
            cells.append(f"{100 * len(b) / len(rcs):.0f} % · {_f(st.median(v) if v else None)}")
        L.append(f"| {cn} | {len(rcs)} | " + " | ".join(cells) + " |")

    L.append("\n## Notes\n")
    if "MetalloGen" in tools and not str(tools["MetalloGen"]["structures"]).endswith("_minE"):
        L.append("- MetalloGen structures are `result_1.xyz` picks (first-finished conformer), not "
                 "the lowest-energy one: run `metallogen/metallogen_repick.py` if `sd/` survives.")
    if "Architector" in tools and not meta["Architector"]["has_jsonl"]:
        L.append("- Architector: only .xyz files found (no JSONL), so no timing and success = "
                 "a structure exists. It ran in its default mode (no geometry/isomer given).")
    L.append("- molSimplify fixes only the geometry (no isomer control) and freezes metal + donors "
             "in its final xtb optimization (as shipped).")
    L.append("- Success % is out of all pilot refcodes: complexes a tool cannot even attempt count "
             "as failures.")
    Path(cfg.out).write_text("\n".join(L) + "\n", encoding="utf-8")

    out_ps = Path(cfg.out).with_name("compare_tools_per_structure.csv")
    cols = ["refcode", "tool", "metal", "cn", "attempted", "built", "off_target", "timeout",
            "time_s",
            "cn_expected", "cn_detected", "cn_match", "donor_source",
            "shape_match"] + [k for k, _ in METRICS] + ["ckm_n_matched", "ckm_core_n",
                                                         "dmae3_n_matched", "dmae3_core_n",
                                                         "n_hydride", "error"]
    with open(out_ps, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for tl in names:
            for rc in pilot:
                w.writerow(per[tl][rc])
    out_sum = Path(cfg.out).with_name("compare_tools_summary.csv")
    with open(out_sum, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    print(f"paired n={len(common)}\n-> {cfg.out}\n-> {out_ps}\n-> {out_sum}")


if __name__ == "__main__":
    main()
