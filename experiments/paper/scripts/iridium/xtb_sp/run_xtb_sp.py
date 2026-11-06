"""GFN2-xTB single points in vacuum, ALPB water and ALPB wet octanol for the structures of a manifest.

    python run_xtb_sp.py --manifest manifest_pilot2000.csv --structures ../runs/full/structures \
        --out results_pilot2000 --workers 8 [--limit 50]

Each (complex, phase) is one xtb run in its own temporary folder, with --chrg and --uhf from the
manifest and one thread per process. Results are appended to <out>/sp.jsonl as they finish, so an
interrupted run resumes where it stopped (failures are not retried unless --retry-failed).
At the end <out>/sp.csv is written and timings are summarised.

The script stops unless `xtb --version` reports 6.7.1 (the version of the builds), and checks
before the batch that the octanol solvent is accepted by this xtb build.
"""
import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

XTB_VERSION = "6.7.1"
PHASES = {"vac": [], "water": ["--alpb", "water"], "octanol": ["--alpb", "woctanol"]}

RE_ENERGY = re.compile(r"::\s*total energy\s+(-?\d+\.\d+)\s+Eh")
RE_GAP = re.compile(r"::\s*HOMO-LUMO gap\s+(-?\d+\.\d+)\s+eV")
RE_GSOLV = re.compile(r"::\s*-> Gsolv\s+(-?\d+\.\d+)\s+Eh")
RE_HOMO = re.compile(r"(-?\d+\.\d+)\s+\(HOMO\)")
RE_LUMO = re.compile(r"(-?\d+\.\d+)\s+\(LUMO\)")
RE_DIPOLE = re.compile(r"molecular dipole:.*?\n\s*full:\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", re.S)


def openblas_coretype() -> str:
    """Same kernel choice as the MeCoBi builds (mecobi.optimize._openblas_coretype)."""
    try:
        from mecobi.optimize import _openblas_coretype
        return _openblas_coretype()
    except Exception:  # noqa: BLE001
        return "Haswell"


def xtb_env() -> dict:
    env = {**os.environ, "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}
    env.setdefault("OMP_STACKSIZE", "4000M")
    env.setdefault("OPENBLAS_CORETYPE", openblas_coretype())
    return env


def check_version(xtb: str) -> str:
    out = subprocess.run([xtb, "--version"], capture_output=True, text=True, errors="replace").stdout
    m = re.search(r"xtb version (\S+)", out)
    found = m.group(1) if m else "unknown"
    if found != XTB_VERSION:
        sys.exit(f"xtb at {shutil.which(xtb) or xtb} is version {found}, expected {XTB_VERSION}. "
                 "Activate the environment used for the builds, or pass --xtb with its path.")
    return m.group(0)


def parse(stdout: str) -> dict:
    def last(rx):
        hits = rx.findall(stdout)
        return float(hits[-1]) if hits else None
    r = {"E_tot": last(RE_ENERGY), "gap_eV": last(RE_GAP), "G_solv": last(RE_GSOLV),
         "homo_eV": last(RE_HOMO), "lumo_eV": last(RE_LUMO), "dipole_D": None}
    m = RE_DIPOLE.search(stdout)
    if m:
        r["dipole_D"] = float(m.group(4))
    return r


def read_charges(path: Path) -> list | None:
    if not path.exists():
        return None
    return [round(float(x), 5) for x in path.read_text().split()]


def read_wbo(path: Path, min_bo: float = 0.1) -> list | None:
    """Wiberg bond orders as [i, j, bo] (0-based atom indices), bonds of order >= min_bo only."""
    if not path.exists():
        return None
    out = []
    for line in path.read_text().splitlines():
        p = line.split()
        if len(p) == 3 and float(p[2]) >= min_bo:
            out.append([int(p[0]) - 1, int(p[1]) - 1, round(float(p[2]), 4)])
    return out


def run_one(task: dict) -> dict:
    rec = {"complex_id": task["complex_id"], "phase": task["phase"], "ok": False, "error": None}
    t0 = time.time()
    work = Path(tempfile.mkdtemp(prefix=f"sp_{task['complex_id']}_{task['phase']}_", dir=task["tmp"]))
    try:
        shutil.copy(task["xyz_path"], work / "mol.xyz")
        cmd = [task["xtb"], "mol.xyz", "--gfn", "2", "--sp", "--chrg", str(task["charge"]),
               "--uhf", str(task["uhf"]), "--parallel", "1", *PHASES[task["phase"]]]
        proc = subprocess.run(cmd, cwd=work, capture_output=True, text=True, errors="replace",
                              timeout=task["timeout"], env=task["env"])
        rec.update(parse(proc.stdout))
        if proc.returncode != 0 or rec["E_tot"] is None:
            tail = " | ".join((proc.stdout + proc.stderr).strip().splitlines()[-4:])
            rec["error"] = f"rc={proc.returncode}: {tail[-400:]}"
        elif task["phase"] != "vac" and rec["G_solv"] is None:
            rec["error"] = "no Gsolv in the output"
        else:
            rec["ok"] = True
            if "SCC not converged" in proc.stdout or "convergence criteria cannot be satisfied" in proc.stdout:
                rec["warning"] = "SCC convergence warning in the output"
        if task["phase"] == "vac":
            q = read_charges(work / "charges")
            rec["charges"] = q
            rec["q_metal"] = q[task["metal_index"]] if q else None
            rec["wbo"] = read_wbo(work / "wbo")
    except subprocess.TimeoutExpired:
        rec["error"] = f"timeout after {task['timeout']} s"
    except Exception as exc:  # noqa: BLE001
        rec["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        shutil.rmtree(work, ignore_errors=True)
    rec["wall_s"] = round(time.time() - t0, 2)
    return rec


def solvent_check(xtb: str, env: dict, tmp: str):
    """Water single point in each solvent before the batch: fails fast on an unknown solvent name."""
    water = "3\n\nO 0.000 0.000 0.117\nH 0.000 0.757 -0.467\nH 0.000 -0.757 -0.467\n"
    work = Path(tempfile.mkdtemp(prefix="sp_check_", dir=tmp))
    (work / "w.xyz").write_text(water)
    try:
        for phase, extra in PHASES.items():
            if not extra:
                continue
            p = subprocess.run([xtb, "w.xyz", "--gfn", "2", "--sp", "--parallel", "1", *extra],
                               cwd=work, capture_output=True, text=True, errors="replace", env=env, timeout=120)
            if p.returncode != 0 or not RE_GSOLV.search(p.stdout):
                sys.exit(f"xtb does not run ALPB with {extra[1]!r} ({phase}); see the output in {work}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def to_csv(jsonl: Path, csv: Path):
    rows = [json.loads(line) for line in open(jsonl, encoding="utf-8")]
    df = pd.DataFrame(rows).drop(columns=["charges", "wbo"], errors="ignore")
    df = df.drop_duplicates(["complex_id", "phase"], keep="last")
    df.to_csv(csv, index=False)
    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--structures", required=True, help="folder with <complex_id>.xyz")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None, help="only the first N complexes (timing test)")
    ap.add_argument("--phases", default="vac,water,octanol")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--xtb", default="xtb")
    ap.add_argument("--tmp", default=None, help="scratch folder for the xtb runs (default: system temp)")
    ap.add_argument("--retry-failed", action="store_true")
    a = ap.parse_args()

    version = check_version(a.xtb)
    env = xtb_env()
    tmp = a.tmp or tempfile.gettempdir()
    Path(tmp).mkdir(parents=True, exist_ok=True)
    solvent_check(a.xtb, env, tmp)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jsonl = out / "sp.jsonl"
    man = pd.read_csv(a.manifest)
    if a.limit:
        man = man.head(a.limit)
    phases = [p for p in a.phases.split(",") if p]
    if set(phases) - set(PHASES):
        sys.exit(f"unknown phase in {phases}; choose from {list(PHASES)}")

    done = set()
    if jsonl.exists():
        for line in open(jsonl, encoding="utf-8"):
            r = json.loads(line)
            if r["ok"] or not a.retry_failed:
                done.add((r["complex_id"], r["phase"]))

    sdir = Path(a.structures)
    tasks, missing = [], []
    for row in man.itertuples():
        xyz = sdir / row.xyz
        if not xyz.exists():
            missing.append(row.complex_id)
            continue
        for ph in phases:
            if (row.complex_id, ph) not in done:
                tasks.append({"complex_id": row.complex_id, "phase": ph, "xyz_path": str(xyz),
                              "charge": int(row.charge), "uhf": int(row.uhf), "metal_index": int(row.metal_index),
                              "xtb": a.xtb, "env": env, "timeout": a.timeout, "tmp": tmp})
    meta = {"xtb": version, "octanol_solvent": PHASES["octanol"][1], "workers": a.workers,
            "OPENBLAS_CORETYPE": env["OPENBLAS_CORETYPE"], "manifest": str(a.manifest),
            "n_complexes": len(man), "missing_xyz": missing, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    (out / "run_meta.json").write_text(json.dumps(meta, indent=1))
    print(f"{version} | octanol = {PHASES['octanol'][1]} | OPENBLAS_CORETYPE = {env['OPENBLAS_CORETYPE']}")
    print(f"{len(man)} complexes, {len(missing)} without .xyz, {len(done)} runs already done, {len(tasks)} to run "
          f"on {a.workers} workers", flush=True)

    t0, n, n_fail = time.time(), 0, 0
    with Pool(a.workers) as pool, open(jsonl, "a", encoding="utf-8") as fh:
        for rec in pool.imap_unordered(run_one, tasks, chunksize=1):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            n += 1
            n_fail += not rec["ok"]
            if n % 100 == 0 or n == len(tasks):
                el = time.time() - t0
                eta = el / n * (len(tasks) - n)
                print(f"{n}/{len(tasks)} done, {n_fail} failed, {el / 60:.1f} min elapsed, "
                      f"about {eta / 60:.0f} min left", flush=True)

    if not jsonl.exists():
        return
    df = to_csv(jsonl, out / "sp.csv")
    print(f"\n{out / 'sp.csv'}: {int(df.ok.sum())} ok, {int((~df.ok).sum())} failed")
    for ph, g in df.groupby("phase"):
        w = sorted(g.wall_s)
        print(f"  {ph:8s} n = {len(g)}, ok = {int(g.ok.sum())}, wall median {statistics.median(w):.1f} s, "
              f"p90 {w[int(.9 * (len(w) - 1))]:.1f} s, max {w[-1]:.1f} s")
    full = len(pd.read_csv(a.manifest)) * len(phases)
    per_run = df.wall_s.mean()
    print(f"  projected wall time for the whole manifest ({full} runs, {a.workers} workers): "
          f"{full * per_run / a.workers / 3600:.1f} h")
    if (~df.ok).any():
        print("\nfailures:")
        print(df.loc[~df.ok, ["complex_id", "phase", "error"]].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
