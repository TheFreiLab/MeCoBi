"""Compare MeCoBi M-L reference tables (ml_reference.json format).

1. Usable bins per level (n >= optimize._ML_NMIN), and how many carry an impossible OS.
2. For every metal-donor bond of the benchmark (benchmark_bundle.json + benchmark_spheres_elem),
   the restraint target each table would give (optimize._ml_target's lookup order, covalent-sum
   fallback) against the crystal distance: MAE / bias / RMSE, per metal and per donor class.
   Scored: complexes whose bundle OS equals the xyz2mol_tm OS (so no table is judged against a
   wrong OS), no hapto ligand (MeCoBi builds those as centroid caps), carbon donors split
   C / C_sp from the ligand SMILES (complexes mixing both are skipped for C). In-sample: the
   tables are mined from the same CSD.

    python dataprep/compare_ml_tables.py --table other=path/to/table.json ...

The shipped table is the consensus rebuild since October 2026. To repeat the comparison that
motivated the swap, pass the first version of the table:
``git show de7b94d:src/mecobi/data/ml_reference.json > old.json`` and ``--table old=old.json``.
"""
import argparse
import ast
import gzip
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

BENCH = Path(__file__).resolve().parents[1]
REPO = BENCH.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(BENCH / "dataprep"))
from mecobi import optimize as O  # noqa: E402
import mine_ml_reference as M  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
ap.add_argument("--table", action="append", default=[], metavar="NAME=PATH",
                help="extra table to compare (repeatable)")
ap.add_argument("--xyz2mol", default=str(REPO / "csd_smiles.csv"))
ap.add_argument("--bonds-csv", default=None, help="write the per-bond targets here")
a = ap.parse_args()
TABLES = {"shipped": M.TABLE}
for t in a.table:
    k, p = t.split("=", 1)
    TABLES[k] = Path(p)
T = {k: json.loads(Path(p).read_text()) for k, p in TABLES.items()}
NMIN = O._ML_NMIN
MAXOS = M.MAX_OS

# ---------------------------------------------------------------- bin stats
print("== usable bins (n >= %d); impossible = OS outside -2..MAX_OS" % NMIN)
for name, t in T.items():
    row = []
    for lv in M.LEVELS:
        u = {k: v for k, v in t[lv].items() if v.get("n", 0) >= NMIN}
        bad = sum(1 for k in u if lv != "metal_donor" and k.split("|")[0] in MAXOS
                  and not -2 <= int(k.split("|")[1]) <= MAXOS[k.split("|")[0]])
        row.append(f"{lv.replace('metal_', '')} {len(u)}" + (f" (impossible {bad})" if bad else ""))
    print(f"  {name:11s} " + " | ".join(row))


def lookup(t, m, ox, el, cn):
    oxs = "" if ox is None else str(ox)
    for e in ((el, "C") if el == "C_sp" else (el,)):
        for lv, key, tag in (("metal_os_donor_cn", f"{m}|{oxs}|{e}|{cn}", "os+cn"),
                             ("metal_os_donor", f"{m}|{oxs}|{e}", "os"),
                             ("metal_donor", f"{m}|{e}", "any-os")):
            v = t[lv].get(key)
            if v and v.get("n", 0) >= NMIN and v.get("mean") is not None:
                return float(v["mean"]), tag
    r1, r2 = O._cov_radius(m), O._cov_radius("C" if el == "C_sp" else el)
    return ((r1 + r2) if r1 and r2 else None), "covalent"


# ---------------------------------------------------------------- benchmark bonds
xyz = M.load_xyz2mol(a.xyz2mol, set(M.SYM2NAME))
xos = {ref: v[0] for d in xyz.values() for ref, v in d.items()}
spheres = json.load(gzip.open(BENCH / "benchmark_spheres_elem.json.gz"))
bundle = json.load(open(BENCH / "benchmark_bundle.json"))
SP_LIG = re.compile(r"^\[C-\]#\[O\+\]$|^\[C-\]#N$|^N#\[C-\]$|^\[O\+\]#\[C-\]$")
stat = defaultdict(int)
bonds = []
for e in bundle:
    m, ref = e["metal"], e["refcode"]
    if M.is_f_block(m) or ref not in spheres:
        continue
    stat["complexes"] += 1
    x = xos.get(ref, xos.get(re.sub(r"\d+$", "", ref)))
    try:
        ox = int(float(e["ox"]))
    except (TypeError, ValueError):
        continue
    if x is None or x != ox:
        stat["os_untrusted"] += 1
        continue
    sp = spheres[ref]
    mp = np.array(sp["metal_xyz"])
    D = np.array(sp["donors"])
    els = sp["donor_elements"]
    if len(D) > 1:
        dd = np.linalg.norm(D[:, None] - D[None], axis=-1)
        np.fill_diagonal(dd, 9)
        if (dd < 1.75).any():
            stat["hapto_skipped"] += 1
            continue
    ligs, dels = (v if isinstance(v, list) else ast.literal_eval(v)
                  for v in (e["ligands"], e["donor_elements"]))
    nC = sum(1 for L in dels for el in L if el == "C")
    nCsp = sum(1 for L, s in zip(dels, ligs) for el in L if el == "C" and SP_LIG.match(s))
    if nC and 0 < nCsp < nC:
        cclass = None                    # mixed sp / other carbons: cannot tell which is which
    else:
        cclass = "C_sp" if nCsp else "C"
    stat["scored"] += 1
    cn = int(e["cn"])
    for el, p in zip(els, D):
        key = el
        if el == "C":
            if cclass is None:
                stat["C_mixed_skipped"] += 1
                continue
            key = cclass
        bonds.append((ref, m, ox, cn, key, float(np.linalg.norm(p - mp))))
print("\n==", dict(stat), "bonds", len(bonds))

rows = []
for ref, m, ox, cn, el, d in bonds:
    r = dict(ref=ref, metal=m, ox=ox, cn=cn, donor=el, d=d)
    for name, t in T.items():
        tgt, tag = lookup(t, m, ox, el, cn)
        r[name] = tgt
        r[name + "_lv"] = tag
    rows.append(r)
B = pd.DataFrame(rows)
if a.bonds_csv:
    B.to_csv(a.bonds_csv, index=False)

print("\n== restraint target vs crystal M-L distance (all scored bonds)")
print(f"  {'table':11s} {'MAE':>6s} {'bias':>7s} {'RMSE':>6s} {'|err|>0.15':>10s}   level used")
for name in T:
    err = B[name] - B.d
    lv = B[name + "_lv"].value_counts(normalize=True).round(3).to_dict()
    rmse = math.sqrt((err**2).mean())
    print(f"  {name:11s} {err.abs().mean():6.3f} {err.mean():+7.3f} {rmse:6.3f}"
          f" {(err.abs() > 0.15).mean():10.3f}   {lv}")

print("\n== MAE per metal (bonds), sorted by the gain of the last table over the first")
def mae_by(col):
    g = B.groupby(col)
    out = pd.DataFrame({n: g.apply(lambda s, n=n: (s[n] - s.d).abs().mean(), include_groups=False)
                        for n in T})
    out["bonds"] = g.size()
    return out


P = mae_by("metal")
_names = list(T)
P["gain"] = P[_names[0]] - P[_names[-1]]
print(P.sort_values("gain", ascending=False).round(3).to_string())

print("\n== MAE by donor class")
Q = mae_by("donor")
print(Q[Q.bonds >= 200].sort_values("bonds", ascending=False).round(3).to_string())
