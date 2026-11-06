"""Score built structures against the crystal with c-kmRMSD (depth-2) over the 30k benchmark.

For each refcode that has BOTH a crystal depth-2 core (benchmark_cores.json.gz, from
extract_cores.py) and a built .xyz (default: structures/<refcode>.xyz, what run.py writes),
extracts the build's depth-2 core and computes the Kuhn-Munkres-matched Kabsch c-kmRMSD against
the crystal core. Shardable + resumable; writes JSONL. Also reports the depth-1 core RMSD (donor
sphere) alongside for continuity with the shipped distance metric.

    python full30k/score_ckmrmsd.py --shard 0/1 --structures full30k/mecobi_30k/structures
    for i in $(seq 0 7); do python full30k/score_ckmrmsd.py --shard $i/8 & done; wait

Output rows: {refcode, metal, cn, ckmrmsd, n_matched, core_rmsd, crystal_core_n, build_core_n}.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent   # full30k/: _ckm_shard*.jsonl output
BENCH = HERE.parent                      # benchmark root: shared harness + frozen data
sys.path.insert(0, str(BENCH))

import metrics as M  # noqa: E402
from ckmrmsd import build_core_from_xyz, ckmrmsd  # noqa: E402


def _load_json(path: Path):
    if str(path).endswith(".gz"):
        return json.loads(gzip.open(path, "rt", encoding="utf-8").read())
    return json.loads(path.read_text(encoding="utf-8"))


def _core_n(core):
    return 1 + len(core["donors"]) + len(core["depth2"])


def _core_rmsd_depth1(xyz_text, metal, cn, crystal_core):
    """depth-1 donor-sphere RMSD (metal-centred Kabsch), for continuity."""
    cs = M.coordination_sphere(xyz_text, metal, cn)
    if not cs:
        return None
    m_b, d_b, _ = cs
    m_e = np.asarray(crystal_core["metal"]["xyz"], float)
    d_e = np.asarray([d["xyz"] for d in crystal_core["donors"]], float)
    if len(d_e) != len(d_b):
        return None
    from scipy.optimize import linear_sum_assignment
    from scipy.spatial.distance import cdist
    Q, P = d_e - m_e, np.asarray(d_b) - np.asarray(m_b)
    R, perm = np.eye(3), np.arange(len(Q))
    for _ in range(50):
        _, perm = linear_sum_assignment(cdist(Q, P @ R.T))
        R = M._kabsch(P[perm], Q)
    return float(np.sqrt(np.mean(np.sum((Q - P[perm] @ R.T) ** 2, axis=1))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1", help="i/N")
    ap.add_argument("--cores", default="benchmark_cores_elem.json.gz")
    ap.add_argument("--bundle", default="benchmark_bundle.json.gz")
    ap.add_argument("--structures", default="structures",
                     help="dir of built <refcode>.xyz, relative to the benchmark root (e.g. full30k/mecobi_30k/structures).")
    ap.add_argument("--limit", type=int, default=0)
    cfg = ap.parse_args()
    i, n = (int(x) for x in cfg.shard.split("/"))

    cores = _load_json(BENCH / cfg.cores if not Path(cfg.cores).is_absolute() else Path(cfg.cores))
    bundle = {r["refcode"]: r for r in _load_json(
        BENCH / cfg.bundle if not Path(cfg.bundle).is_absolute() else Path(cfg.bundle))}
    sdir = Path(cfg.structures) if Path(cfg.structures).is_absolute() else BENCH / cfg.structures

    out = HERE / f"_ckm_shard{i}of{n}.jsonl"
    done = {json.loads(l)["refcode"] for l in out.read_text().splitlines()} if out.exists() else set()

    refs = sorted(rc for rc in cores if rc in bundle and (sdir / f"{rc}.xyz").exists())
    refs = [rc for k, rc in enumerate(refs) if k % n == i]
    if cfg.limit:
        refs = refs[:cfg.limit]

    fh = out.open("a", encoding="utf-8")
    scored = 0
    t0 = time.perf_counter()
    for k, rc in enumerate(refs, 1):
        if rc in done:
            continue
        r, cc = bundle[rc], cores[rc]
        row = {"refcode": rc, "metal": r["metal"], "cn": r["cn"]}
        try:
            txt = (sdir / f"{rc}.xyz").read_text()
            bc = build_core_from_xyz(txt, r["metal"], r["cn"])
            if bc is None:
                row["error"] = "no build core (metal not found / too few donors)"
            else:
                ck, nm = ckmrmsd(cc, bc)
                row.update({"ckmrmsd": round(ck, 4), "n_matched": nm,
                            "crystal_core_n": _core_n(cc), "build_core_n": _core_n(bc)})
                d1 = _core_rmsd_depth1(txt, r["metal"], r["cn"], cc)
                row["core_rmsd"] = None if d1 is None else round(d1, 4)
                scored += 1
        except Exception as e:  # noqa: BLE001
            row["error"] = f"{type(e).__name__}: {e}"[:140]
        fh.write(json.dumps(row) + "\n"); fh.flush()
        if k % 500 == 0:
            print(f"  shard {i}/{n}: {k}/{len(refs)} scored={scored} "
                  f"({(time.perf_counter()-t0)/k*1000:.0f} ms/cpx)", flush=True)
    fh.close()
    print(f"shard {i}/{n}: scored {scored} of {len(refs)} -> {out}")


if __name__ == "__main__":
    main()
