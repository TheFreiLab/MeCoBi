"""MetalloGen counterpart to arch_run.py / molsim_run.py: build the SAME pilot complexes with
MetalloGen (Kang et al.), ORCA/GFN2-xTB backend, timed the same way -- the 4th builder.

Runs in the MetalloGen conda env (shells out to the `metallogen` CLI; never imports mecobi). Reads
the DETERMINISTIC m-SMILES from benchmark_msmiles_pilot.json (make_metallogen_msmiles.py): MetalloGen
builds the crystal's geometry + isomer from the site-labelled m-SMILES (`:N` = coordination site),
exactly parallel to MeCoBi's site_map and molSimplify's -geometry -- no oracle. MetalloGen still does
its own conformer sampling within the fixed isomer and writes every successfully relaxed conformer
as result_<n>.xyz. <n> is the order the relaxations FINISHED in (MetalloGen/run.py relaxes the
Butina-cluster representatives one by one and never ranks them), so result_1 is NOT the best one:
we keep the LOWEST-ENERGY result (energy = 3rd field of the .xyz comment line), the same rule as
the Architector runner. Records wall-clock GENERATION time per complex, plus how many conformers
were relaxed and which one was kept.

On a timeout the finished result_<n>.xyz files are still used: each one is a FULLY relaxed
conformer, only the conformer search is incomplete (the row keeps run_status 'timeout').
metallogen_repick.py re-applies the lowest-energy pick to an existing run's sd/ folders.

Each complex runs as its own subprocess with a wall-clock --timeout: MetalloGen's ORCA relaxation can
hang/stall, and a subprocess is killable where an in-process call is not (same isolation molsim_run
uses). Shardable + resumable.

    python pilot100/metallogen/metallogen_run.py --shard 0/1
    # parallel, matching the 4-core Keisan runs:
    for i in $(seq 0 3); do python pilot100/metallogen/metallogen_run.py --shard $i/4 & done; wait
    python pilot100/metallogen/metallogen_summary.py

Writes pilot100/metallogen/metallogen_det/metallogen_structures/<refcode>.xyz + _metallogen_results_shard*.jsonl.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).parent


def _natoms(path: Path) -> int:
    return int(path.read_text().splitlines()[0].strip())


def _result_energy(path: Path) -> "float | None":
    """Energy MetalloGen writes on the .xyz comment line (``chg<TAB>mult<TAB>energy``), or None."""
    try:
        return float(path.read_text().splitlines()[1].split()[2])
    except (IndexError, ValueError, OSError):
        return None


def _pick_result(sd: Path) -> "tuple[Path | None, dict]":
    """Lowest-energy relaxed conformer in ``sd`` and a summary of the choice.

    MetalloGen numbers result_<n>.xyz in the order the relaxations finished, not by energy, so
    every result is read and the minimum kept. Files without a parsable energy are only used if
    no file has one (then the first, as before)."""
    results = sorted((Path(p) for p in glob.glob(str(sd / "result_*.xyz"))),
                     key=lambda p: int(p.stem.split("_")[1]))
    if not results:
        return None, {"n_results": 0}
    energies = [_result_energy(p) for p in results]
    scored = [(e, p) for e, p in zip(energies, results) if e is not None]
    pick_e, pick = min(scored, key=lambda t: t[0]) if scored else (None, results[0])
    return pick, {"n_results": len(results), "picked_result": pick.stem,
                  "picked_energy": pick_e, "result_1_energy": energies[0]}


def run_one(rc: str, msmiles: str, base: Path, timeout: float, nrelax: int, nconf: int):
    """Run MetalloGen for ONE complex in its own scratch dirs; return (run_status, wall_s, xyz|None).
    run_status: 'ok' (result produced) | 'no_result' (ran, no structure) | 'timeout' | 'error'.
    Also returns the _pick_result summary (n_results, picked_result, energies)."""
    wd, sd = base / "wd" / rc, base / "sd" / rc
    for d in (wd, sd):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)
    cmd = ["metallogen", "-s", msmiles, "-wd", str(wd), "-sd", str(sd),
           "-r", str(nrelax), "-nc", str(nconf), "-c", "orca"]
    t0 = time.perf_counter()
    status = "ok"
    # start_new_session=True puts metallogen in its OWN process group; MetalloGen spawns orca/xtb
    # via os.system (grandchildren), so on a stall we must kill the whole group -- killing just the
    # metallogen PID orphans the running orca/xtb. (POSIX; this runner is Keisan-only.)
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
    except Exception:  # noqa: BLE001  (couldn't even launch)
        return "error", time.perf_counter() - t0, None, {"n_results": 0}
    try:
        p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        status = "timeout"
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            time.sleep(2)
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        p.wait()
    wall = time.perf_counter() - t0
    xyz, pick = _pick_result(sd)
    if xyz is None and status == "ok":
        status = "no_result"
    return status, wall, xyz, pick


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1", help="i/N")
    ap.add_argument("--msmiles", default="benchmark_msmiles_pilot.json")
    ap.add_argument("--timeout", type=float, default=900.0,
                    help="per-complex wall-clock limit (s); a stalled ORCA relax is killed and "
                         "logged as 'timeout' so the shard finishes.")
    ap.add_argument("--num-relax", type=int, default=1,
                    help="metallogen -r (final relaxation on; 1 = yes).")
    ap.add_argument("--num-conformer", type=int, default=10,
                    help="metallogen -nc (conformers sampled; MetalloGen default 10). We keep the "
                         "lowest-energy relaxed one. Lower = faster, less thorough.")
    ap.add_argument("--out-dir", default="metallogen_det")
    ap.add_argument("--limit", type=int, default=0)
    cfg = ap.parse_args()
    i, n = (int(x) for x in cfg.shard.split("/"))

    data = json.loads((HERE / cfg.msmiles).read_text())
    items = sorted(data.items())  # deterministic sharding order
    if cfg.limit:
        items = items[:cfg.limit]

    base = HERE / cfg.out_dir
    structures = base / "metallogen_structures"
    structures.mkdir(parents=True, exist_ok=True)
    out = base / f"_metallogen_results_shard{i}of{n}.jsonl"
    done = ({json.loads(x)["refcode"] for x in out.read_text().splitlines()}
            if out.exists() else set())

    fh = out.open("a", encoding="utf-8")
    built = 0
    t_start = time.perf_counter()
    mine = [(k, rc, rec) for k, (rc, rec) in enumerate(items) if k % n == i]
    for j, (k, rc, rec) in enumerate(mine, 1):
        if rc in done:
            continue
        row = {"refcode": rc, "metal": rec.get("metal"), "cn": rec.get("cn"),
               "geometry": rec["geometry"], "status": rec["status"], "note": rec.get("note", ""),
               "built": False}
        status, wall, xyz, pick = run_one(rc, rec["msmiles"], base, cfg.timeout,
                                    cfg.num_relax, cfg.num_conformer)
        row["wall_s"] = round(wall, 2)
        row["run_status"] = status
        row.update(pick)
        if xyz is not None:
            shutil.copy(xyz, structures / f"{rc}.xyz")
            row["built"] = True
            row["natoms"] = _natoms(xyz)
            built += 1
        else:
            row["error"] = f"{status}: no result_*.xyz"
        fh.write(json.dumps(row) + "\n"); fh.flush()
        print(f"  shard {i}/{n}: {rc} {status} {row['wall_s']:.1f}s "
              f"built={built}/{j}", flush=True)
    fh.close()
    dt = time.perf_counter() - t_start
    print(f"shard {i}/{n} done: {built} built of {len(mine)} in {dt/60:.1f} min -> {out}")


if __name__ == "__main__":
    main()
