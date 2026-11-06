"""Build every isomer of tmQM complexes from the SMILES alone, relax them with xTB, and drop duplicates.

    # this folder (build_isomers.py + refcodes2000.json) copied anywhere; --bench = experiments/benchmark of a MeCoBi clone
    python build_isomers.py --bench ~/MeCoBi/experiments/benchmark --limit 3 --out smoke        # smoke test
    for i in $(seq 0 7); do OMP_NUM_THREADS=1 python build_isomers.py --bench ~/MeCoBi/experiments/benchmark --shard $i/8 & done; wait

Inputs: the frozen benchmark bundle (metal, oxidation state, ligand SMILES; with the confirmed input
fixes of bench_overrides) for the refcodes of --refcodes (default: the 2,000 of the SMILES-only sample).
No crystal information is used: donor atoms are predicted and no isomer target is given.

Two levels of duplicate removal:
  1. Combinatorial, by MeCoBi: build_complex(all_isomers=True, stereo=False) enumerates the assignments of
     ligands to sites that differ under the full point group of the polyhedron, so rotations and
     mirror images (enantiomers, which have the same dipole moment and gap) are built once.
  2. Geometric, here: two relaxed isomers are the same structure (xTB took both starting points to the
     same minimum) when the RMSD of their coordination cores is below --core-rmsd (A) and their GFN2
     energies differ by less than --de (kcal/mol); the one of lower energy is kept. The core is the
     metal, the donor atoms and their heavy-atom neighbours; atoms are matched by index (all isomers of
     a complex are built from the same input, so the atom order is the same), with the identical
     ligands permuted and the mirror image allowed. Sorted interatomic distances are not used: for an
     86-atom complex they differed by only 0.08 A between two distinct isomers (ABEYIQ).
Isomers whose connectivity changed during the relaxation are kept in the record but flagged and
not written as structures.

Output (resumable, one line per complex): <out>/_isomers_shard<i>of<n>.jsonl and
<out>/structures/<REFCODE>/<REFCODE>__iso<k>.xyz for the unique isomers, k = 0 for the lowest energy.
"""
import argparse
import gzip
import itertools
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

from mecobi import pipeline
from mecobi.model import Complex, Ligand, Metal


def load_json(p):
    p = Path(p)
    return json.loads(gzip.open(p, "rt", encoding="utf-8").read() if p.suffix == ".gz" else p.read_text(encoding="utf-8"))


def read_xyz(path):
    lines = Path(path).read_text().splitlines()
    n = int(lines[0])
    sym = [l.split()[0] for l in lines[2:2 + n]]
    xyz = np.array([[float(v) for v in l.split()[1:4]] for l in lines[2:2 + n]])
    return sym, xyz


COV = {"H": 0.31, "B": 0.84, "C": 0.76, "N": 0.71, "O": 0.66, "F": 0.57, "Si": 1.11, "P": 1.07, "S": 1.05,
       "Cl": 1.02, "As": 1.19, "Se": 1.20, "Br": 1.20, "Te": 1.38, "I": 1.39}


def ligand_blocks(sym, xyz, metal):
    """Connected components of the bond graph without the metal (one per ligand)."""
    n = len(sym)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    d = np.linalg.norm(xyz[:, None] - xyz[None], axis=-1)
    for i in range(n):
        for j in range(i + 1, n):
            if metal not in (i, j) and d[i, j] < 1.2 * (COV.get(sym[i], 1.5) + COV.get(sym[j], 1.5)):
                parent[find(i)] = find(j)
    comps = {}
    for i in range(n):
        if i != metal:
            comps.setdefault(find(i), []).append(i)
    return list(comps.values()), d


def core_info(sym, xyz, metal, donors):
    """Core atom indices and the index permutations that swap identical ligands."""
    comps, d = ligand_blocks(sym, xyz, metal)
    core = set(donors)
    for i in donors:
        core |= {j for j in range(len(sym)) if j != metal and sym[j] != "H" and d[i, j] < 1.9}
    groups = {}
    for c in comps:
        groups.setdefault(tuple(sym[i] for i in c), []).append(c)
    perms = [list(range(len(sym)))]
    for blocks in groups.values():
        if len(blocks) < 2:
            continue
        new = []
        for p in perms:
            for order in itertools.permutations(blocks):
                q = p[:]
                for c0, c1 in zip(blocks, order):
                    for i, j in zip(c0, c1):
                        q[i] = p[j]
                new.append(q)
        perms = new[:720]                     # cap: six identical ligands
    return [metal] + sorted(core), perms


def kabsch_rmsd(p, q):
    p, q = p - p.mean(0), q - q.mean(0)
    best = np.inf
    for mirror in (1, -1):                    # enantiomers count as the same structure
        qm = q * np.array([1, 1, mirror])
        u, _, vt = np.linalg.svd(p.T @ qm)
        sgn = np.sign(np.linalg.det(vt.T @ u.T))
        r = vt.T @ np.diag([1, 1, sgn]) @ u.T
        best = min(best, float(np.sqrt(((p @ r.T - qm) ** 2).sum(1).mean())))
    return best


def core_rmsd(a, b):
    if a["sym"] != b["sym"]:
        return np.inf
    idx = a["core"]
    return min(kabsch_rmsd(a["xyz"][idx], b["xyz"][[perm[i] for i in idx]]) for perm in a["perms"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bench", required=True, help="experiments/benchmark of a MeCoBi clone (bundle + input fixes)")
    ap.add_argument("--refcodes", default=str(HERE / "refcodes2000.json"))
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--out", default=str(HERE / "runs"))
    ap.add_argument("--max-isomers", type=int, default=12, help="isomers built per complex (lowest enumeration order)")
    ap.add_argument("--max-isomers-high-cn", type=int, default=6, help="tighter cap for coordination numbers above 6")
    ap.add_argument("--xtb-timeout", type=int, default=600)
    ap.add_argument("--core-rmsd", type=float, default=0.25)
    ap.add_argument("--de", type=float, default=0.5)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    bench = Path(a.bench).expanduser().resolve()
    sys.path.insert(0, str(bench))
    import bench_overrides

    i, n = (int(x) for x in a.shard.split("/"))
    keep = set(load_json(a.refcodes))
    bundle = [r for r in load_json(bench / "benchmark_bundle.json.gz") if r["refcode"] in keep]
    recs = [r for k, r in enumerate(sorted(bundle, key=lambda r: r["refcode"])) if k % n == i]
    if a.limit:
        recs = recs[:a.limit]
    out = Path(a.out)
    (out / "structures").mkdir(parents=True, exist_ok=True)
    work = out / f"_work_shard{i}of{n}"
    work.mkdir(exist_ok=True)
    jsonl = out / f"_isomers_shard{i}of{n}.jsonl"
    done = {json.loads(l)["refcode"] for l in jsonl.read_text().splitlines()} if jsonl.exists() else set()
    overrides = bench_overrides.load()
    print(f"shard {i}/{n}: {len(recs)} complexes ({len(done)} already done); bundle has {len(bundle)} of {len(keep)}", flush=True)

    with jsonl.open("a", encoding="utf-8") as fh:
        for k, r in enumerate(recs, 1):
            rc = r["refcode"]
            if rc in done:
                continue
            r = bench_overrides.record(r, overrides)
            row = {"refcode": rc, "metal": r["metal"], "ox": r["ox"], "built": False}
            t0 = time.perf_counter()
            cdir = work / rc
            shutil.rmtree(cdir, ignore_errors=True)
            cdir.mkdir()
            try:
                cx = Complex(metal=Metal(r["metal"], r["ox"]), name=rc, ligands=[Ligand(s) for s in r["ligands"]])
                res = pipeline.build_complex(cx, cdir, all_isomers=True, stereo=False, relax=True,
                                             xtb_timeout_s=a.xtb_timeout, max_isomers=a.max_isomers,
                                             max_isomers_high_cn=a.max_isomers_high_cn)
                row["built"] = True
                row["warnings"] = sorted({w[:120] for b in res for w in (b.warnings or [])})[:10]
                iso = []
                for b in res:
                    sym, xyz = read_xyz(b.xyz_path)
                    metal = b.metal_index if b.metal_index is not None else sym.index(r["metal"])
                    core, perms = core_info(sym, xyz, metal, list(b.donor_indices or []))
                    iso.append({"label": b.isomer_label, "E_h": b.total_energy,
                                "connectivity_ok": bool(getattr(b, "connectivity_ok", True)),
                                "charge": b.total_charge, "uhf": b.uhf, "metal_index": metal,
                                "path": b.xyz_path, "_g": {"sym": sym, "xyz": xyz, "core": core, "perms": perms}})
                valid = sorted([x for x in iso if x["connectivity_ok"] and x["E_h"] is not None], key=lambda x: x["E_h"])
                unique = []
                for x in valid:
                    near = [(core_rmsd(u["_g"], x["_g"]), u) for u in unique]
                    x["min_core_rmsd"] = round(min((d for d, _ in near), default=np.inf), 3) if near else None
                    dup = next((u for d, u in near if d < a.core_rmsd and abs(x["E_h"] - u["E_h"]) * 627.509 < a.de), None)
                    if dup is None:
                        unique.append(x)
                    else:
                        x["duplicate_of"] = dup["label"]
                sdir = out / "structures" / rc
                shutil.rmtree(sdir, ignore_errors=True)
                sdir.mkdir()
                e0 = unique[0]["E_h"] if unique else None
                for j, u in enumerate(unique):
                    u["file"] = f"{rc}__iso{j}.xyz"
                    shutil.copyfile(u["path"], sdir / u["file"])
                for x in iso:
                    x["E_rel_kcal"] = round((x["E_h"] - e0) * 627.509, 3) if (e0 is not None and x["E_h"] is not None) else None
                    x.pop("_g")
                    x.pop("path")
                row.update({"n_built": len(iso), "n_valid": len(valid), "n_unique": len(unique),
                            "n_duplicates": len(valid) - len(unique), "isomers": iso})
            except Exception as e:  # noqa: BLE001
                row["error"] = f"{type(e).__name__}: {e}"[:300]
            finally:
                shutil.rmtree(cdir, ignore_errors=True)
            row["wall_s"] = round(time.perf_counter() - t0, 1)
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            print(f"[{k}/{len(recs)}] {rc}: {row.get('n_unique', 0)} unique of {row.get('n_built', 0)} built "
                  f"({row['wall_s']} s){' ERROR ' + row['error'][:80] if 'error' in row else ''}", flush=True)


if __name__ == "__main__":
    main()
