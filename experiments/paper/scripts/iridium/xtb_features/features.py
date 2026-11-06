"""xTB and surface descriptors of the IrCpSB complexes, from the single points of run_xtb_sp.py.

    python features.py [--sp results/sp.jsonl] [--structures <IrCpSB_gen>/ML/rerun/structures]
                       [--manifest manifest.csv] [--out xtb_features.csv]

Sites from the geometry: coordinated Cl = the Cl closest to Ir, chelate N = the two N closest to Ir, Cp = the five
C closest to Ir. Per complex:
  electronic (vacuum)  gap, HOMO, LUMO; charges of Ir, of the coordinated Cl, mean of the two N; Wiberg bond orders
                       Ir-Cl, sum Ir-N, sum Ir-Cp
  solvation            G_solv water and wet octanol (ALPB), LUMO in water
  geometry             Ir-Cl and mean Ir-N distance
  surface              SASA of the coordinated Cl and of Ir (probe 0.5 A), percent buried volume at 5 A around
                       Ir, solid-angle coverage of Ir, CPSA (metallipo_ml/xtb_sp/cpsa_features.py)
The dipole is not used: for a cation it depends on the coordinate origin.
Writes xtb_features.csv (index = structure_stem).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "metallipo_ml" / "xtb_sp"))
from cpsa_features import BONDI, CPSA, one, read_xyz, sasa  # noqa: E402

OLD = Path(r"<DATA_ROOT>\York\Data\IrCpSB_gen\ML\rerun\structures")
ELEC = ["gap_vac", "homo_vac", "lumo_vac", "q_Ir", "q_Cl", "q_N", "wbo_IrCl", "wbo_IrN", "wbo_IrCp"]
SOLV = ["G_water", "G_octanol", "lumo_water"]
GEOM = ["d_IrCl", "d_IrN"]
SURF = ["sasa_Cl", "sasa_Ir_p05", "Vbur50", "coverage"] + CPSA


def per_complex(sym, xyz, q, wbo):
    ir = sym.index("Ir")
    d = np.linalg.norm(xyz - xyz[ir], axis=1)
    near = lambda el, k: [i for i in np.argsort(d) if sym[i] == el][:k]
    cl, ns, cp = near("Cl", 1)[0], near("N", 2), near("C", 5)
    bo = {}
    for i, j, v in wbo:
        if ir in (i, j):
            bo[j if i == ir else i] = v
    rad = np.array([BONDI.get(s, 2.0) for s in sym])
    s = one(sym, xyz, q, ir)
    return {"q_Ir": q[ir], "q_Cl": q[cl], "q_N": np.mean([q[i] for i in ns]),
            "wbo_IrCl": bo.get(cl, 0.0), "wbo_IrN": sum(bo.get(i, 0.0) for i in ns),
            "wbo_IrCp": sum(bo.get(i, 0.0) for i in cp), "d_IrCl": d[cl], "d_IrN": np.mean(d[ns]),
            "sasa_Cl": sasa(xyz, rad)[cl], "sasa_Ir_p05": s["metal_sasa_p05"], "Vbur50": s["Vbur50"],
            "coverage": s["coverage"], **{k: s[k] for k in CPSA}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sp", default=str(HERE / "results" / "sp.jsonl"))
    ap.add_argument("--structures", default=str(OLD))
    ap.add_argument("--manifest", default=str(HERE / "manifest.csv"))
    ap.add_argument("--out", default=str(HERE / "xtb_features.csv"))
    a = ap.parse_args()
    man = pd.read_csv(a.manifest).set_index("complex_id")
    recs = {}
    for line in open(a.sp, encoding="utf-8"):
        r = json.loads(line)
        if r["ok"]:
            recs.setdefault(r["complex_id"], {})[r["phase"]] = r
    rows = {}
    for cid, ph in recs.items():
        if not {"vac", "water", "octanol"} <= set(ph) or not ph["vac"].get("charges"):
            continue
        sym, xyz = read_xyz(Path(a.structures) / man.xyz[cid])
        v = ph["vac"]
        f = per_complex(sym, xyz, v["charges"], v["wbo"] or [])
        f.update(gap_vac=v["gap_eV"], homo_vac=v["homo_eV"], lumo_vac=v["lumo_eV"],
                 G_water=ph["water"]["G_solv"], G_octanol=ph["octanol"]["G_solv"], lumo_water=ph["water"]["lumo_eV"])
        rows[cid] = f
    out = pd.DataFrame.from_dict(rows, orient="index")[ELEC + SOLV + GEOM + SURF]
    out.index.name = "structure_stem"
    out.to_csv(a.out)
    print(f"{len(out)} of {len(man)} complexes -> {a.out}")
    print(out.describe().T[["mean", "min", "max"]].round(3).to_string())


if __name__ == "__main__":
    main()
