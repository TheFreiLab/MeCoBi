"""Manifest and centred structures for the GFN2-xTB single points on every isomer of a build_isomers.py run.

    python prepare_isomer_sp.py --run fix6e0590a/runs_2000_fix --out fix6e0590a
    cd fix6e0590a && python ../../../metallipo_ml/xtb_sp/run_xtb_sp.py --manifest manifest_isomers_xtb.csv \
        --structures xtb_structures --out results_xtb --workers 6 --phases vac

Writes <out>/manifest_isomers.csv (one row per unique isomer, as the run recorded it), <out>/xtb_structures/
(each structure translated to its centre of nuclear charge: the dipole of an ion depends on the origin) and
<out>/manifest_isomers_xtb.csv with the charge of the tmQM table (../table.csv), uhf from the electron count,
and the shortest interatomic distance (dmin) as a check. The same steps as the first run (isomers_2000).
"""
import argparse
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit.Chem import GetPeriodicTable

HERE = Path(__file__).resolve().parent
PT = GetPeriodicTable()

ap = argparse.ArgumentParser()
ap.add_argument("--run", required=True, help="build_isomers.py output (_isomers_shard*.jsonl + structures/)")
ap.add_argument("--out", required=True)
ap.add_argument("--table", default=str(HERE.parent / "table.csv"), help="tmQM table with the charge per refcode")
a = ap.parse_args()
run, out = Path(a.run), Path(a.out)
(out / "xtb_structures").mkdir(parents=True, exist_ok=True)

recs = [json.loads(line) for f in sorted(glob.glob(str(run / "_isomers_shard*.jsonl")))
        for line in open(f, encoding="utf-8") if line.strip()]
m = pd.DataFrame([{"complex_id": i["file"][:-4], "xyz": f"{r['refcode']}/{i['file']}", "refcode": r["refcode"],
                   "charge": i["charge"], "uhf": i["uhf"], "metal_index": i["metal_index"],
                   "E_rel_kcal": i["E_rel_kcal"]}
                  for r in recs for i in r.get("isomers", []) if i.get("file")])
m.to_csv(out / "manifest_isomers.csv", index=False)
print(len(recs), "complexes in the run;", len(m), "isomer structures of", m.refcode.nunique(), "complexes")

table = pd.read_csv(a.table).set_index("refcode")
rows, diffq = [], 0
for r in m.itertuples():
    lines = (run / "structures" / r.xyz).read_text().split("\n")
    n = int(lines[0])
    sym = [ln.split()[0] for ln in lines[2:2 + n]]
    x = np.array([[float(v) for v in ln.split()[1:4]] for ln in lines[2:2 + n]])
    z = np.array([PT.GetAtomicNumber(s) for s in sym], float)
    x = x - (z[:, None] * x).sum(0) / z.sum()
    q = int(table.loc[r.refcode, "charge"])
    diffq += q != r.charge
    d = np.linalg.norm(x[:, None] - x[None], axis=-1)
    (out / "xtb_structures" / f"{r.complex_id}.xyz").write_text(
        "\n".join([str(n), r.complex_id] + [f"{s} {p:.6f} {u:.6f} {w:.6f}" for s, (p, u, w) in zip(sym, x)]) + "\n")
    rows.append({"complex_id": r.complex_id, "xyz": f"{r.complex_id}.xyz", "refcode": r.refcode, "charge": q,
                 "uhf": int((z.sum() - q) % 2), "metal_index": r.metal_index, "E_rel_kcal": r.E_rel_kcal,
                 "dmin": round(float(d[np.triu_indices(n, 1)].min()), 3), "n_atoms": n})
mm = pd.DataFrame(rows)
mm.to_csv(out / "manifest_isomers_xtb.csv", index=False)
print(len(mm), "structures; charge differs from the tmQM table:", diffq, "; odd electrons:", int(mm.uhf.sum()),
      "; atoms closer than 0.8 A:", int((mm.dmin < 0.8).sum()))
