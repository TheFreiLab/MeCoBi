"""Why 589 of the 1,946 SMILES-only builds have no valid isomer: predicted vs crystal coordination number (perception only)."""
import glob, gzip, json, sys, collections
from pathlib import Path
import pandas as pd
B = Path(r"<MECOBI_REPO>\experiments\benchmark"); sys.path.insert(0, str(B))
import bench_overrides
from mecobi.model import Complex, Ligand, Metal
from mecobi import perception
R = {json.loads(l)["refcode"]: json.loads(l) for f in glob.glob("fix6e0590a/k671/runs_2000_fix671/_isomers_shard*.jsonl") for l in open(f, encoding="utf-8")}
bundle = {r["refcode"]: r for r in json.load(gzip.open(B / "benchmark_bundle.json.gz")) if r["refcode"] in R}
ov = bench_overrides.load()
ps = pd.read_csv(r"<DATA_ROOT>\MeCoBi_Paper\Data\benchmark_fix_2026-10-20\mecobi_30k_final_per_structure.csv").set_index("refcode")
rows = []
for rc, rec in R.items():
    if not rec.get("built"):
        continue
    r = bench_overrides.record(bundle[rc], ov)
    cx = Complex(metal=Metal(r["metal"], r["ox"]), name=rc, ligands=[Ligand(s) for s in r["ligands"]])
    try:
        perception.perceive_complex(cx); cn_pred = sum(len(l.coord_atoms or []) for l in cx.ligands)
    except Exception as e:
        cn_pred = None
    w = " | ".join(rec.get("warnings", []))
    rows.append({"refcode": rc, "valid": rec["n_valid"] > 0, "cn_pred": cn_pred, "cn_cryst": ps.loc[rc, "cn_expected"] if rc in ps.index else None,
                 "dissociated": "not bonded to the metal" in w, "metal": r["metal"]})
d = pd.DataFrame(rows); d["cn_match"] = d.cn_pred == d.cn_cryst
d.to_csv(sys.argv[1], index=False)
print(len(d), "built; valid", int(d.valid.sum()))
print(pd.crosstab(d.valid, d.cn_match, margins=True))
bad = d[~d.valid]
print("no valid isomer:", len(bad), "| CN predicted wrong:", int((~bad.cn_match).sum()), "| CN right but all isomers failed:", int(bad.cn_match.sum()),
      "| of these, donor dissociated:", int((bad.cn_match & bad.dissociated).sum()))
