"""Fair-comparison MeCoBi run on pilot 100: the current code, every GUI "Advanced options" guard at
its GUI setting, the crystal geometry + isomer (same targets the other tools get), sharded like the
MetalloGen / molSimplify runs.

Launches SHARDS parallel ``run.py`` processes from the benchmark root and waits for them. Settings:

  * GUI advanced options, all explicit (GUI defaults = build_complex defaults):
      before xtb  orient bulky ligands, reposition loose donors, clear the metal region,
                  de-clash by rotation, MCHammer pre-placement (+ its collapse fallback)
      during xtb  keep linear donors straight, prevent sigma->eta slip, keep flat donors
                  coplanar, undo atom fusion
  * Opt-in escalations:
      metal stand-in relax              ON for every complex (it only acts where GFN2 diverges,
                                        e.g. Y relaxed as Sc; a no-op on every other metal)
      reposition loose chelates   } ON only for a hard crowded sphere: complexes with
      protect terminal oxo/nitrido }   >= --optin-min-atoms atoms, H included (default 150)
  * Same inputs as run.py always uses: ground-truth donors (benchmark_donors.json) and the
    confirmed input corrections (benchmark_overrides.json: HIFZEF, ROQDOQ, MUTSAX in this pilot).
  * --hydrides benchmark_hydrides.json (opt-in): put back the hydrides the mined inputs lost where
    the CIF locates them ([H-] ligands, OS/CN + 1 each, target and sphere re-read with the H).
  * xtb budget --xtb-timeout per structure (default 900 s = MetalloGen's per-complex limit; it is a
    wall-clock budget for the whole relax, shared by GFN-FF + GFN2), 1 xtb thread per shard.
  * --no-preopt: the diagnostic un-relaxed build is skipped, so wall_s/build_s time the real build.

Each row records n_atoms, optin_escalation and build_s (relaxed build alone). Resumable: rerunning
skips refcodes already in the shard JSONLs, so pass a new --out-dir for a new code version.

    python pilot100/mecobi/run_pilot100.py                     # 4 shards -> pilot100/mecobi/fair_<commit>/
    python pilot100/mecobi/run_pilot100.py --shards 4 --out-dir pilot100/mecobi/fair_test --limit 2
    python pilot100/mecobi/progress.py --dir mecobi/fair_<commit> --shards 4     # live progress
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent   # pilot100/mecobi/
PILOT = HERE.parent                      # pilot100/: pilot list + crystal targets
BENCH = PILOT.parent                     # benchmark root: run.py + frozen bundle/spheres/donors

GUI_GUARDS = [  # every GUI advanced-options toggle that is ON by default, passed explicitly
    "--orient-bulky", "--reposition-donors", "--clear-metal-region", "--declash-torsion",
    "--mchammer", "--mchammer-fallback", "--reembed-crowded",
    "--linear-restraint", "--haptic-guard", "--planar-guard", "--antifusion",
]
# Not in the GUI; pinned to the build_complex / GUI build defaults so a run.py default change
# can't silently alter this run.
PINNED = ["--two-stage", "--no-revert-topology", "--no-uff-fallback", "--coord-map",
          "--conformer-ensemble", "1"]


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=BENCH,
                                       text=True).strip()
    except Exception:  # noqa: BLE001 -- not a git checkout
        return "nogit"


def _xtb_version() -> str:
    """'6.7.1 (edcfbbe)' of the xtb on PATH, or 'unknown'. Recorded in run_meta.json: two runs
    made with different xtb versions are not comparable structure by structure."""
    try:
        out = subprocess.run(["xtb", "--version"], capture_output=True, text=True, timeout=30)
        for line in (out.stdout + out.stderr).splitlines():
            if "xtb version" in line.lower():
                return line.split("version", 1)[1].split("compiled")[0].strip().rstrip("*").strip()
    except Exception:  # noqa: BLE001
        pass
    return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", type=int, default=4,
                    help="parallel run.py processes (default 4, as the MetalloGen/molSimplify runs).")
    ap.add_argument("--xtb-timeout", type=int, default=900,
                    help="xtb wall-clock budget per structure, seconds (default 900).")
    ap.add_argument("--optin-min-atoms", type=int, default=150,
                    help="atoms (H incl.) from which the crowded-sphere opt-ins turn on (default 150).")
    ap.add_argument("--xtb-threads", type=int, default=1, help="OpenMP threads per xtb call.")
    ap.add_argument("--refcodes", default="pilot100/pilot_100.json",
                    help="JSON list of refcodes, or 'all' for every scorable complex of the bundle "
                         "(the full 30k benchmark).")
    ap.add_argument("--targets", default="pilot100/benchmark_targets_pilot.json")
    ap.add_argument("--hydrides", default=None, metavar="FILE",
                    help="hydride corrections to apply (benchmark_hydrides.json); default none.")
    ap.add_argument("--out-dir", default=None,
                    help="relative to the benchmark root; default pilot100/mecobi/fair_<git commit> "
                         "(fair_<commit>_hyd with --hydrides).")
    ap.add_argument("--limit", type=int, default=0, help="per-shard cap (smoke test).")
    cfg = ap.parse_args()

    commit = _git_commit()
    out_dir = cfg.out_dir or f"pilot100/mecobi/fair_{commit}{'_hyd' if cfg.hydrides else ''}"
    (BENCH / out_dir).mkdir(parents=True, exist_ok=True)

    env = {**os.environ,
           "OMP_NUM_THREADS": str(cfg.xtb_threads), "MKL_NUM_THREADS": str(cfg.xtb_threads),
           "MECOBI_XTB_THREADS": str(cfg.xtb_threads)}
    env.setdefault("OMP_STACKSIZE", "1G")

    common = [
        "--donors", "benchmark_donors.json", "--targets", cfg.targets,
        *([] if cfg.refcodes == "all" else ["--refcodes", cfg.refcodes]),
        "--out-dir", out_dir, "--xtb-timeout", str(cfg.xtb_timeout), "--no-preopt",
        "--metal-surrogate", "--optin-min-atoms", str(cfg.optin_min_atoms),
        "--no-reposition-polydentates", "--no-oxo-antifusion-floors",   # on only via the size gate
        *GUI_GUARDS, *PINNED,
    ]
    if cfg.limit:
        common += ["--limit", str(cfg.limit)]
    if cfg.hydrides:
        common += ["--hydrides", cfg.hydrides]

    # Provenance next to the results, so the report can state exactly how this run was made.
    meta = {"started": dt.datetime.now().isoformat(timespec="seconds"), "commit": commit,
            "host": platform.node(), "cpu_count": os.cpu_count(), "shards": cfg.shards,
            "xtb_version": _xtb_version(),
            "xtb_threads": cfg.xtb_threads, "xtb_timeout_s": cfg.xtb_timeout,
            "optin_min_atoms": cfg.optin_min_atoms, "hydrides": cfg.hydrides,
            # xtb's OpenBLAS kernel (unset = optimize.py's default); SandyBridge avoids the
            # silent GFN2 segfault on AMD EPYC Zen4/Zen5 (PR #90)
            "openblas_coretype": os.environ.get("OPENBLAS_CORETYPE"),
            "run_py_args": common}
    (BENCH / out_dir / "run_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"MeCoBi {commit} -> {out_dir}/  ({cfg.shards} shards x {cfg.xtb_threads} xtb thread, "
          f"{cfg.xtb_timeout}s budget, opt-ins at >= {cfg.optin_min_atoms} atoms)")

    procs = []
    for i in range(cfg.shards):
        log = open(BENCH / out_dir / f"shard{i}of{cfg.shards}.log", "a", encoding="utf-8")
        cmd = [sys.executable, "run.py", "--shard", f"{i}/{cfg.shards}", *common]
        procs.append((subprocess.Popen(cmd, cwd=BENCH, env=env, stdout=log,
                                       stderr=subprocess.STDOUT), log))
    codes = []
    for p, log in procs:
        codes.append(p.wait())
        log.close()
    meta["finished"] = dt.datetime.now().isoformat(timespec="seconds")
    meta["exit_codes"] = codes
    (BENCH / out_dir / "run_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"done ({meta['finished']}); exit codes {codes}. "
          f"Timing: python pilot100/timing_table.py --mecobi '{out_dir}/_results_shard*of*.jsonl'")
    sys.exit(max(codes) if codes else 0)


if __name__ == "__main__":
    main()
