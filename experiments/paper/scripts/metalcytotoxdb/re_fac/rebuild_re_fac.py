"""Rebuild the MetalCytoToxDB rhenium tricarbonyls with the three CO ligands facial.

The library build (biometaldb_build.py, all_isomers=False) placed the monodentates of these complexes in the
order of their SMILES, which put the three CO meridional in 148 of the 236 Re(CO)3 complexes (re_mer_names.txt).
Here each is built with an explicit octahedral site assignment: the CO on sites 0, 2, 4 (+x, +y, +z, mutually
cis) and the other donors on 1, 3, 5 (a chelate on 1 and 3, a monodentate on 5, a tridentate on 1, 3, 5), so
that every CO is trans to a donor of another ligand. Everything else as biometaldb_build.py (xtb relaxation,
timeout 300 s), with the same record layout, so merge_mctdb.py and biometaldb_assess.py read the output as is.

    PYTHONPATH=~/MeCoBi-fix/src python rebuild_re_fac.py --shard 0/24 --out-dir ../structures_refac_rerun
    python rebuild_re_fac.py --plan          # only print the site assignment of each complex

Complexes whose donors do not fill an octahedron with three CO (two in re_mer_names.txt are perceived as
seven-coordinate) are skipped, listed in skipped.txt and left out of the results, so they keep their old
structure in the merge.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path

from mecobi import inputs, pipeline

HERE = Path(__file__).parent
CO = {"[C-]#[O+]", "[O+]#[C-]"}


def fac_assignment(cx):
    """{ligand index: sites} with the CO on 0, 2, 4, or None if the donors do not fit this pattern."""
    pipeline.resolve_perception(cx)
    co = [i for i, l in enumerate(cx.ligands) if l.smiles in CO]
    rest = [i for i, l in enumerate(cx.ligands) if l.smiles not in CO]
    dent = sorted((cx.ligands[i].denticity for i in rest), reverse=True)
    if len(co) != 3 or cx.coordination_number != 6 or dent not in ([2, 1], [3], [1, 1, 1]):
        return None
    out = {i: (s,) for i, s in zip(co, (0, 2, 4))}
    free = [1, 3, 5]
    for i in sorted(rest, key=lambda i: -cx.ligands[i].denticity):
        d = cx.ligands[i].denticity
        out[i], free = tuple(free[:d]), free[d:]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(HERE.parent / "biometaldb_mecobi.csv"))
    ap.add_argument("--names", default=str(HERE / "re_mer_names.txt"))
    ap.add_argument("--out-dir", default=str(HERE.parent / "structures_refac_rerun"))
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--xtb-timeout", type=int, default=300)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--no-mchammer", action="store_true", help="retry: hand xtb the raw stk placement")
    ap.add_argument("--reposition-polydentates", action="store_true",
                    help="retry: slide stranded chelate donors in to their reference distance")
    cfg = ap.parse_args()
    i, n = (int(x) for x in cfg.shard.split("/"))
    names = set(Path(cfg.names).read_text().split())
    complexes = [c for c in inputs.parse_csv(Path(cfg.input)) if c.name in names]
    complexes = [c for k, c in enumerate(sorted(complexes, key=lambda c: c.name)) if k % n == i]

    if cfg.plan:
        for cx in complexes:
            a = fac_assignment(cx)
            print(cx.name, "skipped" if a is None else
                  {f"{k}:{cx.ligands[k].smiles[:30]}": v for k, v in sorted(a.items())})
        return

    base = Path(cfg.out_dir)
    structures = base / "structures"
    structures.mkdir(parents=True, exist_ok=True)
    work = base / f"_work_shard{i}of{n}"
    work.mkdir(exist_ok=True)
    out = base / f"_results_shard{i}of{n}.jsonl"
    done = {json.loads(l)["name"] for l in out.read_text().splitlines()} if out.exists() else set()
    with out.open("a", encoding="utf-8") as fh:
        for cx in complexes:
            if cx.name in done:
                continue
            rec = {"name": cx.name, "metal": cx.metal.symbol, "ox": cx.metal.oxidation_state,
                   "n_ligands": len(cx.ligands)}
            t = time.perf_counter()
            try:
                a = fac_assignment(cx)
                if a is None:  # not in the results: merge_mctdb.py keeps the record of the base run
                    with (base / "skipped.txt").open("a") as sk:
                        sk.write(f"{cx.name} cn={cx.coordination_number}\n")
                    continue
                rec.update({"cn": 6, "geometry": "octahedral", "site_assignment": {str(k): v for k, v in a.items()}})
                r = pipeline.build_complex(cx, work, site_assignment=a, relax=True, mchammer=not cfg.no_mchammer,
                                           reposition_polydentates=cfg.reposition_polydentates,
                                           xtb_bin=os.environ.get("XTB_BIN", "xtb"),
                                           xtb_timeout_s=cfg.xtb_timeout)[0]
                shutil.copyfile(r.xyz_path, structures / f"{cx.name}.xyz")
                rec.update({"built": True, "connectivity_ok": r.connectivity_ok, "total_charge": r.total_charge,
                            "uhf": r.uhf, "total_energy": r.total_energy, "warnings": r.warnings})
            except Exception as exc:  # noqa: BLE001
                rec.update({"built": False, "error": f"{type(exc).__name__}: {exc}"[:200]})
            rec["wall_s"] = round(time.perf_counter() - t, 1)
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
    shutil.rmtree(work, ignore_errors=True)
    print(f"shard {i}/{n} done -> {structures}")


if __name__ == "__main__":
    main()
