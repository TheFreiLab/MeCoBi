"""Re-apply the lowest-energy conformer pick to a FINISHED MetalloGen run, without re-running it.

Before 2026-09-28 metallogen_run.py kept result_1.xyz, assuming it was MetalloGen's lowest-energy
conformer. It is not: MetalloGen numbers result_<n>.xyz in the order the relaxations finished and
never ranks them. This script reads every result_*.xyz still in <run dir>/sd/<refcode>/, keeps the
lowest-energy one (the rule metallogen_run.py now applies, same as the Architector runner) and
logs what changed. Nothing in MetalloGen is modified; only which of its outputs we score.

Non-destructive by default: the picks go to <run dir>/metallogen_structures_minE/ and
<run dir>/repick_log.csv. With --in-place the originals are first copied to
metallogen_structures_result1/ and metallogen_structures/ is overwritten.

    python pilot100/metallogen/metallogen_repick.py                            # metallogen_det/
    python pilot100/metallogen/metallogen_repick.py --dir /path/to/metallogen_det --in-place
"""
from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

from metallogen_run import _pick_result

HERE = Path(__file__).resolve().parent
HARTREE_TO_KCAL = 627.5094740631


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(HERE / "metallogen_det"),
                    help="run dir holding sd/<refcode>/result_*.xyz (metallogen_run.py --out-dir).")
    ap.add_argument("--in-place", action="store_true",
                    help="overwrite metallogen_structures/ (after backing it up).")
    cfg = ap.parse_args()

    base = Path(cfg.dir).resolve()
    sd_root = base / "sd"
    if not sd_root.is_dir():
        raise SystemExit(f"no sd/ folder in {base}: the per-complex MetalloGen outputs are gone, "
                         "so the pick can't be redone without re-running MetalloGen.")
    src = base / "metallogen_structures"
    if cfg.in_place:
        backup = base / "metallogen_structures_result1"
        if src.is_dir() and not backup.exists():
            shutil.copytree(src, backup)
        dest = src
    else:
        dest = base / "metallogen_structures_minE"
    dest.mkdir(parents=True, exist_ok=True)

    rows, changed = [], 0
    for sd in sorted(p for p in sd_root.iterdir() if p.is_dir()):
        pick, info = _pick_result(sd)
        row = {"refcode": sd.name, **info}
        if pick is not None:
            shutil.copy(pick, dest / f"{sd.name}.xyz")
            e1, ep = info.get("result_1_energy"), info.get("picked_energy")
            row["changed"] = info["picked_result"] != "result_1"
            row["delta_kcal"] = (round((ep - e1) * HARTREE_TO_KCAL, 2)
                                 if e1 is not None and ep is not None else None)
            changed += row["changed"]
        rows.append(row)

    cols = ["refcode", "n_results", "picked_result", "picked_energy", "result_1_energy",
            "delta_kcal", "changed"]
    with open(base / "repick_log.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    with_res = [r for r in rows if r.get("n_results")]
    multi = sum(1 for r in with_res if r["n_results"] > 1)
    print(f"{len(rows)} complexes, {len(with_res)} with results ({multi} with >1 conformer); "
          f"pick changed for {changed}.\n-> {dest}\n-> {base / 'repick_log.csv'}")
    print("delta_kcal = E(picked) - E(result_1): negative = the kept conformer is lower in energy. "
          "Energies are MetalloGen's own (ORCA XTB2, Hartree in the .xyz).")


if __name__ == "__main__":
    main()
