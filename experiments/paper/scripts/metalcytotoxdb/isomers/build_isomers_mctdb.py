"""All geometric isomers of the MetalCytoToxDB complexes that have more than one, for the DimeNet++ isomer test.

    python build_isomers_mctdb.py --shard 0/24            # one of 24 workers (Keisan, xtb 6.7.1, MeCoBi 6e0590a)
    for i in $(seq 0 23); do python build_isomers_mctdb.py --shard $i/24 & done; wait
    python build_isomers_mctdb.py --summary               # after the shards: counts and isomers/README

Reads ../biometaldb_mecobi.csv (the same input as the library build) and multi_isomer_names.txt (the 1,253 complexes
with two or more geometric isomers, from the isomer count of Figure S1). Each complex is built with
all_isomers=True, stereo=False (at most 12 isomers, 6 above six-coordination, as for tmQM) and GFN2-xTB
relaxation, otherwise as in biometaldb_build.py. Isomers whose
connectivity changed during the relaxation are dropped; the others are written as

    isomers/<bmdb_name>/<rank>_<isomer>.xyz       rank 00 = lowest GFN2-xTB energy

which is the layout train_dimenet.py --isomers-dir reads (sorted file names, so the lowest-energy isomer is first).
Complexes with a single isomer have no folder there and fall back to their structure of the library build.
Shardable and resumable (one JSONL line per complex).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
from pathlib import Path

from mecobi import inputs, pipeline

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(HERE.parent / "biometaldb_mecobi.csv"))
    ap.add_argument("--names", default=str(HERE / "multi_isomer_names.txt"))
    ap.add_argument("--out-dir", default=str(HERE / "build"))
    ap.add_argument("--shard", default="0/1", help="i/N (round-robin)")
    ap.add_argument("--xtb-timeout", type=int, default=300)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--summary", action="store_true")
    cfg = ap.parse_args()
    base = Path(cfg.out_dir)
    iso_root = base / "isomers"
    if cfg.summary:
        return summary(base)

    names = set(Path(cfg.names).read_text().split())
    complexes = [c for c in inputs.parse_csv(Path(cfg.input)) if c.name in names]
    i, n = (int(x) for x in cfg.shard.split("/"))
    complexes = [c for k, c in enumerate(complexes) if k % n == i]
    if cfg.limit:
        complexes = complexes[:cfg.limit]
    iso_root.mkdir(parents=True, exist_ok=True)
    work = base / f"_work_shard{i}of{n}"
    work.mkdir(exist_ok=True)
    out = base / f"_results_shard{i}of{n}.jsonl"
    done = {json.loads(ln)["name"] for ln in out.read_text().splitlines()} if out.exists() else set()
    fh = out.open("a", encoding="utf-8")
    t0 = time.perf_counter()
    for k, cx in enumerate(complexes, 1):
        if cx.name in done:
            continue
        rec = {"name": cx.name, "metal": cx.metal.symbol, "ox": cx.metal.oxidation_state}
        t = time.perf_counter()
        try:
            res = pipeline.build_complex(cx, work / cx.name, relax=True, all_isomers=True, stereo=False, max_isomers=12,
                                         max_isomers_high_cn=6, xtb_bin=os.environ.get("XTB_BIN", "xtb"),
                                         xtb_timeout_s=cfg.xtb_timeout)
            ok = sorted([r for r in res if r.connectivity_ok and r.total_energy is not None],
                        key=lambda r: r.total_energy)
            dst = iso_root / cx.name
            dst.mkdir(exist_ok=True)
            for rank, r in enumerate(ok):
                label = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(r.isomer_label or rank))[:60]
                shutil.copyfile(r.xyz_path, dst / f"{rank:02d}_{label}.xyz")
            e0 = ok[0].total_energy if ok else None
            rec.update({"n_built": len(res), "n_kept": len(ok),
                        "e_rel_kcal": [round((r.total_energy - e0) * 627.5095, 2) for r in ok]})
        except Exception as exc:  # noqa: BLE001  (keep the batch going)
            rec["error"] = f"{type(exc).__name__}: {exc}"[:200]
        rec["wall_s"] = round(time.perf_counter() - t, 1)
        fh.write(json.dumps(rec) + "\n")
        fh.flush()
        shutil.rmtree(work / cx.name, ignore_errors=True)
        if k % 10 == 0:
            print(f"  shard {i}/{n}: {k}/{len(complexes)} ({(time.perf_counter() - t0) / k:.1f} s/complex)", flush=True)
    fh.close()
    shutil.rmtree(work, ignore_errors=True)
    print(f"shard {i}/{n}: done ({len(complexes)} complexes)")


def summary(base: Path):
    recs = [json.loads(ln) for p in sorted(base.glob("_results_shard*.jsonl")) for ln in p.read_text().splitlines()]
    kept = [r.get("n_kept", 0) for r in recs]
    multi = sum(1 for x in kept if x >= 2)
    lines = [f"{len(recs)} complexes; failed {sum('error' in r for r in recs)}; isomers kept {sum(kept)}; "
             f"complexes with >= 2 kept isomers {multi}; with 1 {sum(1 for x in kept if x == 1)}; "
             f"with 0 {sum(1 for x in kept if x == 0)}",
             f"wall time {sum(r['wall_s'] for r in recs) / 3600:.1f} CPU-h"]
    (base / "SUMMARY.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
