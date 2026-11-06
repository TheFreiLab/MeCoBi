"""Table S20: outcome of the SMILES-only build of the 2,000 tmQM complexes, by coordination number of the crystal.

    python smiles_only_table.py RUN_DIR FAILURES_CSV PER_STRUCTURE_CSV OUT_CSV

RUN_DIR holds the _isomers_shard*.jsonl of build_isomers.py; FAILURES_CSV is the output of smiles_only_failures.py
(predicted against crystal coordination number); PER_STRUCTURE_CSV is the benchmark per-structure table (crystal
coordination number). Writes one row per complex (status and reason) and prints the counts of Table S20.
"""
import glob
import json
import sys
from pathlib import Path

import pandas as pd

run_dir, fail_csv, per_structure, out = sys.argv[1:5]
R = {json.loads(l)["refcode"]: json.loads(l)
     for f in glob.glob(str(Path(run_dir) / "_isomers_shard*.jsonl")) for l in open(f, encoding="utf-8")}
ps = pd.read_csv(per_structure).set_index("refcode")
fail = pd.read_csv(fail_csv).set_index("refcode")
rows = []
for rc, r in R.items():
    if not r["built"]:
        status = "not built"
        reason = ("no donor predicted for a ligand" if "No coordinating atoms" in str(r.get("error", ""))
                  else "unsupported coordination number")
    elif r["n_valid"] == 0:
        status, f = "no valid isomer", fail.loc[rc]
        reason = ("predicted CN differs from crystal" if not f.cn_match
                  else "donor left the metal" if f.dissociated else "other connectivity change")
    else:
        status, reason = "valid", ""
    rows.append({"refcode": rc, "metal": r["metal"], "cn": ps.loc[rc, "cn_expected"],
                 "geom": ps.loc[rc, "geometry_label"], "status": status, "reason": reason})
d = pd.DataFrame(rows)
d.to_csv(out, index=False)
d["valid"] = d.status == "valid"
t = d.groupby("cn").agg(complexes=("valid", "size"), valid=("valid", "sum"))
for reason in ("predicted CN differs from crystal", "donor left the metal", "other connectivity change"):
    t[reason] = d[d.reason == reason].groupby("cn").size().reindex(t.index).fillna(0).astype(int)
t["not built"] = d[d.status == "not built"].groupby("cn").size().reindex(t.index).fillna(0).astype(int)
print(t.to_string())
print(d.groupby(["status", "reason"]).size().to_string())
