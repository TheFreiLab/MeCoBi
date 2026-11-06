"""Extract depth-k crystal cores (default k = 3) from the CIFs for D-MAE_k (dmae.py).

Each core is the metal + every heavy atom within k bonds of it in the ISOLATED crystal complex
(ckm_depth3.crystal_core: flood-filled molecule, disordered alternate sites merged), stored as
``{refcode: {"metal": {"el", "xyz"}, "atoms": [{"el", "xyz"}, ...]}}``. Donors are, for each
heavy element the bundle declares, that many nearest atoms of it (as for the v2 spheres/cores;
H donors excluded). A core whose
donor shell holds an atom NOT bonded to the metal is rejected (the isolated-complex flood fill
lost a donor -- ICIHAF, NAPMUO -- and a backbone atom 2.9-3.0 A away would stand in for it).
Resumable.

    python dataprep/extract_cores_dk.py --refcodes pilot100/pilot_100.json \\
        --out benchmark_cores_d3_pilot.json.gz
    for i in $(seq 0 7); do python dataprep/extract_cores_dk.py --shard $i/8 & done; wait
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
sys.path.insert(0, str(BENCH))

import numpy as np  # noqa: E402

from cif_geometry import SYM2NAME  # noqa: E402
from ckm_depth3 import crystal_core  # noqa: E402
from donor_map import ml_bonded  # noqa: E402
from extract_cores import _DEFAULT_CIF_ROOT, _bundle, is_placeholder  # noqa: E402


def _read(p: Path) -> dict:
    if not p.exists():
        return {}
    op = gzip.open if p.suffix == ".gz" else open
    with op(p, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def _write(p: Path, d: dict):
    op = gzip.open if p.suffix == ".gz" else open
    with op(p, "wt", encoding="utf-8") as fh:
        json.dump(d, fh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--refcodes", default=None, help="JSON list of refcodes (default: bundle)")
    ap.add_argument("--shard", default="0/1", help="i/N")
    ap.add_argument("--cif-root", default=None)
    ap.add_argument("--out", default=None)
    cfg = ap.parse_args()
    cif_root = cfg.cif_root or os.environ.get("MECOBI_CIF_ROOT") or _DEFAULT_CIF_ROOT
    i, n = (int(x) for x in cfg.shard.split("/"))
    out = Path(cfg.out) if cfg.out else BENCH / f"_cores_d{cfg.depth}_shard{i}of{n}.json"
    if not out.is_absolute():
        out = BENCH / out
    done = _read(out)
    keep = set(json.loads((BENCH / cfg.refcodes).read_text())) if cfg.refcodes else None
    recs = [r for k, r in enumerate(_bundle()) if k % n == i
            and (keep is None or r["refcode"] in keep)]
    got = missing = fail = shell = 0
    for r in recs:
        rc = r["refcode"]
        if rc in done:
            continue
        folder = SYM2NAME.get(r["metal"])
        cifs = glob.glob(f"{cif_root}/{folder}/{rc}.*.cif") if folder else []
        if not cifs or is_placeholder(cifs[0]):
            missing += 1
            continue
        try:
            els, pos = crystal_core(cifs[0], r["metal"], r["cn"], cfg.depth,
                                    r["donor_elements"])
        except Exception:  # noqa: BLE001
            els = None
        if els is None:
            fail += 1
            continue
        n_heavy = sum(1 for e in r["donor_elements"] if e != "H")
        if not all(ml_bonded(els[0], e, float(np.linalg.norm(p - pos[0])))
                   for e, p in zip(els[1:1 + n_heavy], pos[1:1 + n_heavy])):
            shell += 1
            continue
        done[rc] = {"metal": {"el": els[0], "xyz": pos[0].tolist()},
                    "atoms": [{"el": e, "xyz": p.tolist()} for e, p in zip(els[1:], pos[1:])]}
        got += 1
        if got % 200 == 0:
            _write(out, done)
    _write(out, done)
    print(f"depth-{cfg.depth} cores: {len(done)} (+{got})  missing={missing} fail={fail} "
          f"bad-donor-shell={shell} -> {out}")


if __name__ == "__main__":
    main()
