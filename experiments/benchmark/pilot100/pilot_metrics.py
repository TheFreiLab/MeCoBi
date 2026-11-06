"""Per-structure metric table for the pilot runs (mecobi_det = pilot1, mecobi_det2 = pilot2).

Joins, ONE ROW PER STRUCTURE, the two metric sources that today live apart:

  * shape / CShM / distance metrics -- already in each run's ``_results_shard*.jsonl``
    (shape_match, exp/build/poly_cshm, dmat_rmsd, bond_rmsd, cn, connectivity_ok, ...);
  * c-kmRMSD (depth-2 Kuhn-Munkres-matched Kabsch) + depth-1 core RMSD -- recomputed here
    from the built ``<run>/structures/<refcode>.xyz`` against the crystal core
    (benchmark_cores.json.gz), using the SAME ckmrmsd.py the shipped scorer uses. This is
    pure geometry (no xtb / no torch), so it runs locally.

Writes one CSV per run, e.g. ``pilot1_metrics.csv`` and ``pilot2_metrics.csv``.

    python pilot100/pilot_metrics.py        # default: mecobi/mecobi_det->pilot1, mecobi/mecobi_det2->pilot2
    python pilot100/pilot_metrics.py --runs mecobi/mecobi_det:pilot1 mecobi/mecobi_det2:pilot2 --out .
"""
from __future__ import annotations

import argparse
import csv
import glob
import gzip
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent   # pilot100/: metric CSVs; MeCoBi runs under mecobi/
BENCH = HERE.parent                      # benchmark root: shared harness + frozen data
sys.path.insert(0, str(BENCH))

import metrics as M  # noqa: E402
from ckmrmsd import build_core_like, ckmrmsd  # noqa: E402

# Columns pulled straight from the shard row (per-structure build metrics).
SHARD_COLS = [
    "refcode", "metal", "ox", "cn", "built", "connectivity_ok", "build_mode",
    "target_geometry", "shape_match", "exp_shape", "build_shape",
    "exp_cshm", "build_cshm", "poly_cshm", "dmat_rmsd", "bond_rmsd", "bond_offset",
    "site_cn", "cap_collapsed", "cap_mismatch",
]
# Columns computed here from the built .xyz vs the crystal core.
CKM_COLS = ["ckmrmsd", "n_matched", "core_rmsd", "crystal_core_n", "build_core_n", "ckm_error"]


def _load_json(path: Path):
    if str(path).endswith(".gz"):
        return json.loads(gzip.open(path, "rt", encoding="utf-8").read())
    return json.loads(path.read_text(encoding="utf-8"))


def _core_n(core) -> int:
    return 1 + len(core["donors"]) + len(core["depth2"])


def _core_rmsd_depth1(xyz_text, metal, cn, crystal_core):
    """depth-1 donor-sphere RMSD (metal-centred Kabsch), same as score_ckmrmsd.py."""
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


def _shard_rows(run_dir: Path) -> dict[str, dict]:
    """All shard rows in ``run_dir``, keyed by refcode (last write wins on duplicates)."""
    rows: dict[str, dict] = {}
    for f in sorted(glob.glob(str(run_dir / "_results_shard*.jsonl"))):
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rows[r["refcode"]] = r
    return rows


def _ckm_for(refcode, run_dir, bundle, cores) -> dict:
    """c-kmRMSD + depth-1 core RMSD for one built structure, or an error note."""
    out = {c: None for c in CKM_COLS}
    b = bundle.get(refcode)
    cc = cores.get(refcode)
    xyz = run_dir / "structures" / f"{refcode}.xyz"
    if b is None or cc is None:
        out["ckm_error"] = "no crystal core / bundle entry"
        return out
    if not xyz.exists():
        out["ckm_error"] = "no built .xyz"
        return out
    try:
        txt = xyz.read_text(encoding="utf-8")
        cc, bc = build_core_like(cc, txt, b["metal"])   # hydride-aware, as compare_tools.py
        if bc is None:
            out["ckm_error"] = "no build core (metal not found / too few donors)"
            return out
        ck, nm = ckmrmsd(cc, bc)
        d1 = _core_rmsd_depth1(txt, b["metal"], b["cn"], cc)
        out.update({
            "ckmrmsd": round(ck, 4), "n_matched": nm,
            "core_rmsd": None if d1 is None else round(d1, 4),
            "crystal_core_n": _core_n(cc), "build_core_n": _core_n(bc),
        })
    except Exception as e:  # noqa: BLE001
        out["ckm_error"] = f"{type(e).__name__}: {e}"[:140]
    return out


def process(run_dir: Path, label: str, bundle, cores, out_dir: Path) -> Path:
    rows = _shard_rows(run_dir)
    out_path = out_dir / f"{label}_metrics.csv"
    n_ckm = 0
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SHARD_COLS + CKM_COLS, extrasaction="ignore")
        w.writeheader()
        for rc in sorted(rows):
            row = {c: rows[rc].get(c) for c in SHARD_COLS}
            ckm = _ckm_for(rc, run_dir, bundle, cores)
            row.update(ckm)
            n_ckm += ckm["ckmrmsd"] is not None
            w.writerow(row)
    print(f"{label}: {len(rows)} structures -> {out_path.name}  (c-kmRMSD scored {n_ckm}/{len(rows)})")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", default=["mecobi/mecobi_det:pilot1", "mecobi/mecobi_det2:pilot2"],
                    help="run_dir:label pairs, relative to pilot100/ (dir holds "
                         "_results_shard*.jsonl + structures/).")
    ap.add_argument("--cores", default="benchmark_cores_elem.json.gz")
    ap.add_argument("--bundle", default="benchmark_bundle.json.gz")
    ap.add_argument("--out", default=".", help="output directory for the CSVs.")
    cfg = ap.parse_args()

    def _resolve(p):
        return Path(p) if Path(p).is_absolute() else HERE / p

    def _data(p):  # frozen reference data lives in the benchmark root
        return Path(p) if Path(p).is_absolute() else BENCH / p

    cores = _load_json(_data(cfg.cores))
    bundle = {r["refcode"]: r for r in _load_json(_data(cfg.bundle))}
    out_dir = _resolve(cfg.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for spec in cfg.runs:
        run_dir, _, label = spec.partition(":")
        label = label or Path(run_dir).name
        process(_resolve(run_dir), label, bundle, cores, out_dir)


if __name__ == "__main__":
    main()
