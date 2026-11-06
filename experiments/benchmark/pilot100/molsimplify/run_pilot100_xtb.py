"""Fair-comparison molSimplify run on pilot 100 with xtb as the optimizer.

Launches SHARDS parallel ``molsim_run.py`` processes (run it in the molSimplify conda env, with the
``xtb`` binary on PATH) and waits for them. Settings, matched to the MeCoBi run
(pilot100/mecobi/run_pilot100.py) wherever molSimplify allows:

  * crystal geometry per refcode (``--targets``); molSimplify has no site-level isomer control,
    so only the geometry is fixed (haptic complexes fall back to the atom-CN default core);
  * ground-truth donors as ``-smicat`` + the confirmed input corrections (benchmark_overrides.json);
  * ``-ff xtb -ffoption ba``: xtb optimizes the free ligands before placement and the complex
    after (molSimplify freezes the metal + donors in that final xtb run -- as shipped);
  * 1 xtb thread per shard, 900 s wall-clock limit per complex (the MetalloGen / MeCoBi budget).

Results -> pilot100/molsimplify/molsimplify_det_xtb/ (resumable; a new --out-dir for a fresh run).

    conda activate molsimp
    python pilot100/molsimplify/run_pilot100_xtb.py                # 4 shards
    python pilot100/molsimplify/run_pilot100_xtb.py --limit 1      # smoke test, 1 complex per shard
    python pilot100/molsimplify/molsim_summary.py pilot100/molsimplify/molsimplify_det_xtb
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent   # pilot100/molsimplify/


def _version() -> str:
    try:
        from importlib.metadata import version
        return version("molsimplify")
    except Exception:  # noqa: BLE001
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", type=int, default=4)
    ap.add_argument("--timeout", type=float, default=900.0, help="per-complex limit, seconds.")
    ap.add_argument("--xtb-threads", type=int, default=1)
    ap.add_argument("--ff", default="xtb", help="xtb (default) or gfnff.")
    ap.add_argument("--ffoption", default="ba")
    ap.add_argument("--targets", default="benchmark_targets_pilot.json",
                    help="relative to pilot100/.")
    ap.add_argument("--out-dir", default=None,
                    help="relative to pilot100/molsimplify/; default molsimplify_det_<ff>.")
    ap.add_argument("--limit", type=int, default=0, help="per-shard cap (smoke test).")
    ap.add_argument("--hydrides", default=None, metavar="FILE",
                    help="benchmark_hydrides.json: re-run ONLY the complexes with a located "
                         "hydride, built with their [H-] ligands (-> <out-dir>_hyd/). "
                         "compare_tools.py lays those rows over the full run.")
    cfg = ap.parse_args()

    if shutil.which("xtb") is None:
        sys.exit("xtb not on PATH -- molSimplify's -ff xtb shells out to it.")
    # Fail fast (with the real error) if this interpreter can't import molSimplify -- e.g. the
    # MeCoBi env was active instead of the molSimplify one -- rather than 4 shards dying silently.
    probe = subprocess.run([sys.executable, "-c",
                            "from molSimplify.Scripts.generator import startgen_pythonic"],
                           capture_output=True, text=True)
    if probe.returncode != 0:
        sys.exit(f"molSimplify is not importable from {sys.executable} (activate the molSimplify "
                 f"env):\n{probe.stderr.strip()[-1500:]}")
    out_dir = cfg.out_dir or f"molsimplify_det_{cfg.ff}{'_hyd' if cfg.hydrides else ''}"
    (HERE / out_dir).mkdir(parents=True, exist_ok=True)

    args = ["--targets", cfg.targets, "--ff", cfg.ff, "--ffoption", cfg.ffoption,
            "--timeout", str(cfg.timeout), "--xtb-threads", str(cfg.xtb_threads),
            "--out-dir", out_dir]   # overrides are on by default in molsim_run.py
    if cfg.limit:
        args += ["--limit", str(cfg.limit)]
    if cfg.hydrides:
        args += ["--hydrides", cfg.hydrides, "--hydrides-only"]
    env = {**os.environ, "OMP_NUM_THREADS": str(cfg.xtb_threads),
           "MKL_NUM_THREADS": str(cfg.xtb_threads)}

    meta = {"started": dt.datetime.now().isoformat(timespec="seconds"), "host": platform.node(),
            "cpu_count": os.cpu_count(), "molsimplify": _version(), "shards": cfg.shards,
            "xtb_threads": cfg.xtb_threads, "timeout_s": cfg.timeout, "molsim_run_args": args}
    meta_path = HERE / out_dir / "run_meta.json"
    meta_path.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"molSimplify {meta['molsimplify']} -ff {cfg.ff} -ffoption {cfg.ffoption} -> "
          f"{out_dir}/ ({cfg.shards} shards x {cfg.xtb_threads} xtb thread, {cfg.timeout:.0f}s)")

    procs = []
    for i in range(cfg.shards):
        log = open(HERE / out_dir / f"shard{i}of{cfg.shards}.log", "a", encoding="utf-8")
        cmd = [sys.executable, str(HERE / "molsim_run.py"), "--shard", f"{i}/{cfg.shards}", *args]
        procs.append((subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT), log))
    codes = []
    for p, log in procs:
        codes.append(p.wait())
        log.close()
    meta["finished"] = dt.datetime.now().isoformat(timespec="seconds")
    meta["exit_codes"] = codes
    meta_path.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"done ({meta['finished']}); exit codes {codes}")
    for i, code in enumerate(codes):  # surface why a shard died instead of just its exit code
        if code:
            log = HERE / out_dir / f"shard{i}of{cfg.shards}.log"
            tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-15:]
            print(f"\n--- shard {i} failed (exit {code}); last lines of {log}:\n" + "\n".join(tail))
    sys.exit(max(codes) if codes else 0)


if __name__ == "__main__":
    main()
