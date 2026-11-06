"""Build + xTB-relax the 1,800 [Ir(Cp)(SB)Cl]+ complexes of the IrCpSB library with MeCoBi (sharded, resumable).

    python run_build.py --limit 3 --out-dir runs/smoke                                   # smoke test
    for i in $(seq 0 7); do OMP_NUM_THREADS=1 python run_build.py --shard $i/8 --out-dir runs/full & done; wait

Same relax options as experiments/benchmark/run.py and metallipo_ml/run_build.py (the benchmark configuration),
default isomer, Schiff-base donors fixed to the iminopyridine N,N (inputs/complexes_ircpsb.csv,
prepare_inputs.py). Stops unless xtb is 6.7.1. Output, laid out for the ML pipeline
(IrCpSB_gen/ML/rerun/_pipeline, IRCPSB_STRUCT_ROOT=<out-dir>/structures):
  <out-dir>/structures/gen0/<stem>_OPT.xyz and <out-dir>/structures/gen1+2/<stem>_OPT.xyz
  <out-dir>/_results_shard<i>of<n>.jsonl   one line per complex (built, connectivity, energy, warnings, time)
  <out-dir>/run_meta.json                  MeCoBi version and commit, xtb version
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
XTB_VERSION = "6.7.1"


def xtb_version(xtb):
    out = subprocess.run([xtb, "--version"], capture_output=True, text=True, errors="replace", check=False).stdout
    m = re.search(r"xtb version (\S+)", out)
    return m.group(1) if m else "unknown"


def mecobi_commit():
    import mecobi
    root = Path(mecobi.__file__).resolve().parents[2]
    try:
        c = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True, check=False).stdout.strip()
        return c + (" (with uncommitted changes)" if dirty else "")
    except OSError:
        return "unknown"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--complexes", default=str(HERE / "inputs" / "complexes_ircpsb.csv"))
    ap.add_argument("--shard", default="0/1", help="i/n: this process builds rows k with k %% n == i")
    ap.add_argument("--out-dir", default="runs/full")
    ap.add_argument("--xtb-timeout", type=int, default=600)
    ap.add_argument("--xtb-bin", default="xtb")
    ap.add_argument("--expect-xtb", default=XTB_VERSION,
                    help="xtb version required (default %(default)s; 6.4.1 for the version test)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default=None, help="file with one structure_stem per line (or a comma list)")
    ap.add_argument("--reposition-polydentates", action="store_true",
                    help="opt-in: slide stranded chelates in to their M-L reference before xtb")
    ap.add_argument("--conformer-ensemble", type=int, default=1, metavar="N",
                    help="assemble N ligand conformers and keep the best (MECOBI_N_CONFORMERS)")
    cfg = ap.parse_args()
    os.environ.setdefault("MECOBI_XTB_THREADS", "1")
    os.environ["MECOBI_N_CONFORMERS"] = str(cfg.conformer_ensemble)

    found = xtb_version(cfg.xtb_bin)
    if found != cfg.expect_xtb:
        sys.exit(f"xtb is {found}, expected {cfg.expect_xtb}: activate the environment used for the benchmark.")

    import mecobi
    from mecobi import pipeline
    from mecobi.model import Complex, Ligand, Metal

    i, n = (int(x) for x in cfg.shard.split("/"))
    df = pd.read_csv(cfg.complexes)
    if cfg.only:
        p = Path(cfg.only)
        keep = set(p.read_text().split()) if p.exists() else {x.strip() for x in cfg.only.split(",")}
        df = df[df.structure_stem.isin(keep)]
    recs = [r for k, r in enumerate(df.itertuples()) if k % n == i]
    if cfg.limit:
        recs = recs[:cfg.limit]
    base = Path(cfg.out_dir)
    work = base / f"_run_shard{i}of{n}"
    for p in (work, base / "structures" / "gen0", base / "structures" / "gen1+2"):
        p.mkdir(parents=True, exist_ok=True)
    meta = base / "run_meta.json"
    if not meta.exists():
        meta.write_text(json.dumps({"mecobi_version": getattr(mecobi, "__version__", "unknown"),
                                    "mecobi_commit": mecobi_commit(), "xtb": found,
                                    "reposition_polydentates": cfg.reposition_polydentates,
                                    "conformer_ensemble": cfg.conformer_ensemble,
                                    "started": time.strftime("%Y-%m-%d %H:%M:%S")}, indent=1))
    out = base / f"_results_shard{i}of{n}.jsonl"
    done = {json.loads(line)["structure_stem"] for line in out.read_text().splitlines()} if out.exists() else set()
    relax_opts = dict(two_stage_relax=True, linear_restraint=True, orient_bulky=True, reposition_donors=True,
                      clear_metal_region=True, declash_torsion=True, haptic_guard=True, planar_guard=True,
                      mchammer=True, mchammer_fallback=True, reembed_crowded=True, antifusion_guard=True,
                      reposition_polydentates=cfg.reposition_polydentates)
    t0, built = time.perf_counter(), 0
    print(f"shard {i}/{n}: {len(recs)} complexes, {len(done)} already done; MeCoBi {mecobi_commit()}, xtb {found}",
          flush=True)
    with out.open("a", encoding="utf-8") as fh:
        for k, r in enumerate(recs, 1):
            if r.structure_stem in done:
                continue
            row = {"compound_id": r.compound_id, "structure_stem": r.structure_stem, "generation": r.generation,
                   "built": False}
            ts = time.perf_counter()
            try:
                schiff = Ligand(r.schiff)
                schiff.donor_override = [int(x) for x in r.schiff_donors.split(",")]
                cx = Complex(metal=Metal(r.metal, int(r.ox)), name=r.structure_stem,
                             ligands=[Ligand(r.cp), schiff, Ligand(r.chloride)])
                res = pipeline.build_complex(cx, work, relax=True, xtb_bin=cfg.xtb_bin,
                                             xtb_timeout_s=cfg.xtb_timeout, **relax_opts)
                b = res[0]
                shutil.copyfile(b.xyz_path, base / "structures" / r.folder / f"{r.structure_stem}_OPT.xyz")
                row.update(built=True, connectivity_ok=bool(b.connectivity_ok), total_charge=b.total_charge,
                           uhf=b.uhf, energy_Eh=b.total_energy, warnings=[w[:160] for w in b.warnings])
                built += 1
            except Exception as e:  # noqa: BLE001 -- record the failure, keep going
                row["error"] = f"{type(e).__name__}: {e}"[:200]
            row["wall_s"] = round(time.perf_counter() - ts, 2)
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            if k % 25 == 0:
                print(f"  shard {i}/{n}: {k}/{len(recs)} built={built} ({(time.perf_counter() - t0) / k:.1f} s/complex)",
                      flush=True)
    shutil.rmtree(work, ignore_errors=True)
    print(f"shard {i}/{n} done: {built} built of {len(recs)} -> {out}")


if __name__ == "__main__":
    main()
