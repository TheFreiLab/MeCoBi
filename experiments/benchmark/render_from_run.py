"""Render an HTML review gallery from a (possibly partial) run.py run — WITHOUT
rebuilding. Reads the saved relaxed structures (structures/<refcode>.xyz) + the
per-complex metrics (_results_shard*.jsonl) + the crystal spheres, and draws the same
full-structure + crystal-overlay cards as pre_xtb_report. Safe to run any time,
including mid-run (it only renders complexes already finished).

    python render_from_run.py --n 250            # stratified sample of finished builds
    python render_from_run.py --n 0              # render ALL finished builds (big HTML)
    # -> _run_gallery/report.html

Pairs with a large `run.py --donors` job: Gustavo stops the run whenever, then renders
whatever completed. aggregate.py gives the quantitative table over the same JSONL.
"""
from __future__ import annotations

import argparse
import glob
import json
import random
from collections import defaultdict
from pathlib import Path

import numpy as np

import metrics as M
from pre_xtb_report import _align, _load_json, render_html

HERE = Path(__file__).parent


def _card(rc, row, rec, sphere, xyz_text):
    card = {
        "refcode": rc, "metal": row["metal"], "ox": row["ox"], "cn": row["cn"],
        "ligands": rec.get("ligands", []) if rec else [],
        "donor_elements": rec.get("donor_elements", []) if rec else [],
        "warnings": [], "error": None, "xyz": xyz_text,
        "exp_shape": row.get("exp_shape"), "exp_cshm": row.get("exp_cshm"),
        "build_shape": row.get("build_shape"), "build_cshm": row.get("build_cshm"),
        "shape_match": row.get("shape_match"), "poly_cshm": row.get("poly_cshm"),
        "dmat_rmsd": row.get("dmat_rmsd"), "bond_rmsd": row.get("bond_rmsd"),
        "bond_offset": row.get("bond_offset"),
    }
    if card["build_cshm"] is not None and card["exp_cshm"] is not None:
        card["cshm_excess"] = round(card["build_cshm"] - card["exp_cshm"], 1)
    # coordination-sphere overlay from the SAVED structure
    b = M.coordination_sphere(xyz_text, row["metal"], row["cn"])
    if b:
        m_b, d_b, sym_b = b
        ve = np.asarray(sphere["donors"], float) - np.asarray(sphere["metal_xyz"], float)
        vb = d_b - m_b
        aligned = _align(ve, vb)
        card["build_bonds"] = sorted(float(np.linalg.norm(v)) for v in vb)
        card["sphere"] = {
            "exp": ve.round(3).tolist(),
            "build": (aligned.round(3).tolist() if aligned is not None else vb.round(3).tolist()),
            "exp_syms": [str(s) for s in sphere.get("donor_syms", card["donor_elements"])],
            "build_syms": sym_b,
        }
    return card


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=250, help="gallery sample size (0 = all finished)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--spheres", default="benchmark_spheres.json.gz")
    ap.add_argument("--bundle", default="benchmark_bundle")
    ap.add_argument("--results", default="_results_shard*.jsonl")
    ap.add_argument("--out", default="_run_gallery")
    cfg = ap.parse_args()

    rows = {}
    for f in glob.glob(str(HERE / cfg.results)):
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rows[r["refcode"]] = r
    spheres = _load_json(HERE / cfg.spheres)
    gz = HERE / f"{cfg.bundle}.json.gz"
    bundle = {r["refcode"]: r for r in
              _load_json(gz if gz.exists() else HERE / f"{cfg.bundle}.json")}
    structdir = HERE / "structures"

    # finished + scorable + has a saved structure + a crystal sphere
    finished = [rc for rc, r in rows.items()
                if r.get("built") and (structdir / f"{rc}.xyz").exists() and rc in spheres]
    print(f"finished builds available: {len(finished)} (of {len(rows)} attempted)")

    # stratify the gallery across CN so every coordination number is represented
    by_cn = defaultdict(list)
    for rc in finished:
        by_cn[rows[rc]["cn"]].append(rc)
    rng = random.Random(cfg.seed)
    if cfg.n and cfg.n < len(finished):
        per = max(1, cfg.n // max(len(by_cn), 1))
        picked = []
        for cn in sorted(by_cn):
            g = by_cn[cn][:]
            rng.shuffle(g)
            picked += g[:per]
        rng.shuffle(picked)
        picked = picked[:cfg.n]
    else:
        picked = finished

    cards = []
    for rc in picked:
        xyz = (structdir / f"{rc}.xyz").read_text(encoding="utf-8")
        cards.append(_card(rc, rows[rc], bundle.get(rc), spheres[rc], xyz))
    cards.sort(key=lambda c: (c["cn"], c["refcode"]))

    outdir = HERE / cfg.out
    outdir.mkdir(exist_ok=True)
    meta = (f"donor-hardcoded run.py builds (xtb-relaxed), rendered from saved structures; "
            f"{len(cards)} of {len(finished)} finished shown")
    (outdir / "report.html").write_text(render_html(cards, meta, relax=True), encoding="utf-8")
    print(f"gallery -> {outdir / 'report.html'}  ({len(cards)} cards)")


if __name__ == "__main__":
    main()
