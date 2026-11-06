"""Merge a partial rerun (e.g. the CN2 complexes) into a full 30k run directory.

Writes a NEW run directory: every result row of the base run, except those the rerun rebuilt,
plus all rows of the rerun; ``structures/`` likewise (rerun files win). The base and rerun
directories are left untouched, so the merge can be repeated or discarded. The scorer then reads
the merged directory like any other run:

    python full30k/merge_rerun.py --base mecobi_30k --rerun mecobi_30k_cn2 --out mecobi_30k_final
    python full30k/full30k_score.py --run-dir mecobi_30k_final --workers 16

``run_meta.json`` of the merged run records both sources. Paths are relative to full30k/.
"""
from __future__ import annotations

import argparse
import glob
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _rows(run_dir: Path) -> list[dict]:
    rows = []
    for f in sorted(glob.glob(str(run_dir / "_results_shard*.jsonl"))):
        rows += [json.loads(l) for l in Path(f).read_text(encoding="utf-8").splitlines() if l.strip()]
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="full run directory (relative to full30k/)")
    ap.add_argument("--rerun", required=True, help="partial rerun directory (relative to full30k/)")
    ap.add_argument("--out", required=True, help="merged run directory to create (must not exist)")
    cfg = ap.parse_args()
    base, rerun, out = (HERE / cfg.base, HERE / cfg.rerun, HERE / cfg.out)
    if out.exists():
        raise SystemExit(f"{out} exists; pick a new --out")
    new_rows = _rows(rerun)
    if not new_rows:
        raise SystemExit(f"no _results_shard*.jsonl rows in {rerun}")
    redone = {r["refcode"] for r in new_rows}
    old_rows = _rows(base)
    kept = [r for r in old_rows if r["refcode"] not in redone]
    missing = redone - {r["refcode"] for r in old_rows}

    (out / "structures").mkdir(parents=True)
    with open(out / "_results_shard0of1.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for r in kept + new_rows:
            fh.write(json.dumps(r) + "\n")
    n_xyz = 0
    for src, keep in ((base, lambda rc: rc not in redone), (rerun, lambda rc: True)):
        for f in (src / "structures").glob("*.xyz"):
            if keep(f.stem):
                shutil.copy2(f, out / "structures" / f.name)
                n_xyz += 1
    meta = {"merged_from": {"base": cfg.base, "rerun": cfg.rerun},
            "base_meta": json.loads((base / "run_meta.json").read_text()) if (base / "run_meta.json").exists() else None,
            "rerun_meta": json.loads((rerun / "run_meta.json").read_text()) if (rerun / "run_meta.json").exists() else None,
            "n_rows": len(kept) + len(new_rows), "n_replaced": len(redone) - len(missing),
            "n_added": len(missing)}
    # settings both sources share stay readable at the top level (full30k_score.py reads
    # "hydrides" there to pick the crystal references)
    for key in ("hydrides", "xtb_version", "xtb_timeout_s", "optin_min_atoms"):
        vals = [m.get(key) for m in (meta["base_meta"], meta["rerun_meta"]) if m]
        if vals and all(v == vals[0] for v in vals):
            meta[key] = vals[0]
    (out / "run_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"{len(old_rows)} base rows, {len(new_rows)} rerun rows -> {meta['n_rows']} merged "
          f"({meta['n_replaced']} replaced, {meta['n_added']} not in the base run); "
          f"{n_xyz} structures -> {out}")


if __name__ == "__main__":
    main()
