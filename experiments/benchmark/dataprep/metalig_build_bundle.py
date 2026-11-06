"""Build the stratified MeCoBi benchmark INPUT bundle from MetaLig.

- OS folded in: parent_metal_os, else parent_complex_charge - sum(ligand charges)
  (self-contained within MetaLig; recovers ~28k complexes and de-biases).
- Eligible = all ligands convert (correct charge) + OS known + CN 2-9 + has a CIF
  in our Generation-3 tree (so every complex is scorable later).
- Stratified CAPPED allocation over (metal, CN, OS): min(cap, available) per cell,
  seeded shuffle within cell -> balanced across metal x CN x OS without being
  bottlenecked by the rarest cell.

Emits benchmark_bundle.json (list of {refcode, metal, ox, cn, ligands, charges,
donor_elements, complex_charge}) + prints a coverage report. Run in the dart venv.
"""
import argparse
import bz2
import json
import math
import os as osmod
import random
import sys
from collections import defaultdict

from metalig_ingest import convert, DB

_DEFAULT_CIF_ROOT = None  # no built-in default: --cif-root or MECOBI_CIF_ROOT


def _resolve_cif_root(cli_value):
    for candidate in (cli_value, osmod.environ.get("MECOBI_CIF_ROOT"), _DEFAULT_CIF_ROOT):
        if candidate and osmod.path.isdir(candidate):
            return candidate
    if sys.stdin.isatty():
        typed = input(
            "CIF root folder not found (expected a 'Generation3'-style folder with one "
            "subfolder per metal, e.g. .../Cu/<REFCODE>.*.cif).\n"
            "Enter the path to your CIF folder: "
        ).strip().strip('"')
        if typed and osmod.path.isdir(typed):
            return typed
    raise SystemExit(
        "Could not find the CIF root folder. Pass --cif-root PATH, set the "
        "MECOBI_CIF_ROOT environment variable, or run this interactively to be prompted."
    )


def nan(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=100, help="max complexes per (metal,CN,OS) cell")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="benchmark_bundle.json")
    ap.add_argument("--no-cif-filter", action="store_true")
    ap.add_argument("--cif-root", default=None,
                     help="Path to the Generation3-style CIF folder (one subfolder per "
                          "metal). Falls back to MECOBI_CIF_ROOT, then an interactive prompt.")
    cfg = ap.parse_args()

    # 1. refcodes present in our CIF tree
    tree = set()
    if not cfg.no_cif_filter:
        cif_root = _resolve_cif_root(cfg.cif_root)
        for d in osmod.scandir(cif_root):
            if d.is_dir():
                for f in osmod.scandir(d.path):
                    if f.name.endswith(".cif"):
                        tree.add(f.name.split(".")[0])
        print(f"CIF-tree refcodes: {len(tree)}")

    # 2. convert unique ligands once; build per-complex records
    uniq = {}   # unique_name -> (smiles_or_None, charge, denticity, donor_elements)
    ref = {}    # refcode -> {metal, mos, cq, ligs:[unique_name]}
    with bz2.open(DB, "rt", encoding="utf-8") as fh:
        for line in fh:
            v = json.loads(line)["value"]
            g = v["global_props"]; li = v["ligand_instances"]; atoms = v["atomic_props"]["atoms"]
            un = g.get("unique_name")
            if un not in uniq:
                uniq[un] = (convert(g.get("smiles"), g.get("charge")), g.get("charge"),
                            g.get("n_denticities"), [atoms[i] for i in v["donor_idc"]])
            for rc, met, mos, cq in zip(li.get("parent_complex_id", []), li.get("parent_metal", []),
                                        li.get("parent_metal_os", []), li.get("parent_complex_charge", [])):
                r = ref.setdefault(rc, {"metal": met, "mos": mos, "cq": cq, "ligs": []})
                r["ligs"].append(un)

    # 3. eligible records
    elig = []
    drop = defaultdict(int)
    for rc, d in ref.items():
        if not cfg.no_cif_filter and rc not in tree:
            drop["no_cif"] += 1; continue
        cn = sum((uniq[u][2] or 0) for u in d["ligs"])
        if not (2 <= cn <= 9):
            drop["bad_cn"] += 1; continue
        lc = [uniq[u][1] for u in d["ligs"]]
        if not nan(d["mos"]):
            ox = int(round(d["mos"]))
        elif not nan(d["cq"]) and all(c is not None for c in lc):
            ox = int(round(d["cq"] - sum(lc)))
        else:
            drop["no_os"] += 1; continue
        smis = [uniq[u][0] for u in d["ligs"]]
        if any(s is None for s in smis):
            drop["convert_fail"] += 1; continue
        elig.append({
            "refcode": rc, "metal": d["metal"], "ox": ox, "cn": cn, "ligands": smis,
            "charges": lc, "donor_elements": [uniq[u][3] for u in d["ligs"]],
            "complex_charge": (None if nan(d["cq"]) else int(round(d["cq"]))),
        })

    print(f"eligible+scorable complexes: {len(elig)}  (dropped: {dict(drop)})")

    # 4. stratified capped allocation over (metal, CN, OS)
    random.seed(cfg.seed)
    cells = defaultdict(list)
    for r in elig:
        cells[(r["metal"], r["cn"], r["ox"])].append(r)
    bundle = []
    for _, recs in cells.items():
        random.shuffle(recs)
        bundle.extend(recs[:cfg.cap])
    random.shuffle(bundle)

    json.dump(bundle, open(cfg.out, "w"), indent=0)
    # 5. coverage report
    bm = defaultdict(int); bc = defaultdict(int); bo = defaultdict(int)
    for r in bundle:
        bm[r["metal"]] += 1; bc[r["cn"]] += 1; bo[r["ox"]] += 1
    print(f"\nBUNDLE: {len(bundle)} complexes  (cap={cfg.cap}/cell, {len(cells)} cells)")
    print(f"  wrote {cfg.out}")
    print("  by CN: " + "  ".join(f"CN{c}:{bc[c]}" for c in sorted(bc)))
    print("  by OS: " + "  ".join(f"{o:+d}:{bo[o]}" for o in sorted(bo)))
    print(f"  metals ({len(bm)}): " + "  ".join(f"{m}:{n}" for m, n in
                                                sorted(bm.items(), key=lambda x: -x[1])[:16]))


if __name__ == "__main__":
    main()
