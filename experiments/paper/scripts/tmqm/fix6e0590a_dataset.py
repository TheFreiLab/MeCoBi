"""Rebuild the tmQM study inputs for the benchmark structures of the fixed MeCoBi (6e0590a).

    python fix6e0590a_dataset.py

The fix rebuilt 1,965 of the benchmark complexes that are in tmQM (rebuilt_fix6e0590a/structures) and changed which
of them keep their connectivity: 57 drop out and 65 come in (gained_fix6e0590a/.../structures). This script
  1. copies the current inputs to archive_409b273/ (once);
  2. table.csv  from baseline_2d.load_table on the fixed per-structure table (complexes built with the connectivity
     preserved, joined to tmQM);
  3. folds.csv  keeps every existing assignment; a new complex joins the fold of its largest-ligand group, or the
     smallest fold when the group is new (random split: a seeded draw);
  4. inclusion.csv and geometries.pkl: molecular formula and charge against the tmQM entry, drmsd to the tmQM
     geometry; MeCoBi geometry from the rebuilt / gained structure where there is one, else unchanged;
  5. exclude_overlap.txt: included MeCoBi structures with two atoms closer than 0.8 A;
  6. results_soap/floor.pkl: the 2D + RDKit features of the included complexes (baseline_2d.features + rdkit_block),
     which reproduce the stored matrix exactly for the unchanged set.
"""
import gzip
import json
import pickle
import shutil
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

import baseline_2d as b
import desc3d_rdkit_floor as F

HERE = Path(__file__).resolve().parent
TMQM_Y = Path.home() / "Downloads" / "tmQM_y.csv"
TMQM_X = {s: Path.home() / "Downloads" / f"tmQM_{s}.xyz.gz" for s in ("X1", "X2", "X3")}
PER_STRUCTURE = Path(r"<DATA_ROOT>\MeCoBi_Paper\Data\benchmark_fix_2026-10-20"
                     r"\mecobi_30k_final_per_structure.csv")
ARCHIVE = HERE / "archive_409b273"
KEEP = ["table.csv", "folds.csv", "inclusion.csv", "geometries.pkl", "exclude_overlap.txt", "results_soap/floor.pkl"]


def read_xyz(p):
    lines = Path(p).read_text().splitlines()
    n = int(lines[0])
    return [ln.split()[0] for ln in lines[2:2 + n]], np.array([[float(v) for v in ln.split()[1:4]] for ln in lines[2:2 + n]])


def heavy_sorted(sym, xyz):
    y = xyz[[s != "H" for s in sym]]
    d = np.linalg.norm(y[:, None] - y[None], axis=-1)
    return np.sort(d[np.triu_indices(len(y), 1)])


def tmqm_geometries(codes):
    """{refcode: {sym, xyz, q, src}} from the tmQM multi-xyz files, for the codes asked."""
    out = {}
    for src, path in TMQM_X.items():
        with gzip.open(path, "rt") as fh:
            while True:
                head = fh.readline()
                if not head:
                    break
                n = int(head)
                meta = fh.readline()
                block = [fh.readline() for _ in range(n)]
                fh.readline()                                    # blank separator
                code = meta.split("|")[0].split("=")[1].strip()
                if code in codes:
                    q = int(meta.split("|")[1].split("=")[1])
                    out[code] = {"sym": [ln.split()[0] for ln in block],
                                 "xyz": np.array([[float(v) for v in ln.split()[1:4]] for ln in block]), "q": q,
                                 "src": src}
    return out


def main():
    if not ARCHIVE.exists():
        for f in KEEP:
            (ARCHIVE / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(HERE / f, ARCHIVE / f)
    old_t = pd.read_csv(ARCHIVE / "table.csv")
    old_f = pd.read_csv(ARCHIVE / "folds.csv").set_index("refcode")
    old_i = pd.read_csv(ARCHIVE / "inclusion.csv").set_index("refcode")
    G0 = pickle.load(open(ARCHIVE / "geometries.pkl", "rb"))

    df = b.load_table(str(TMQM_Y), str(PER_STRUCTURE))
    # n_hydride of the per-structure table is a scoring count that moved for 10 rebuilt complexes with the same atoms;
    # the 2D features must not depend on the assembly, so the complexes already in the study keep their value
    prev = old_t.set_index("refcode").n_hydride
    df["n_hydride"] = [int(prev[r]) if r in prev.index else int(h) for r, h in zip(df.refcode, df.n_hydride)]
    same = df[df.refcode.isin(old_t.refcode)].set_index("refcode")
    o = old_t.set_index("refcode").loc[same.index, same.columns]
    num = same.select_dtypes("number").columns
    assert np.allclose(same[num].to_numpy(float), o[num].to_numpy(float), equal_nan=True)
    assert (same.drop(columns=num).astype(str) == o.drop(columns=num).astype(str)).all().all()
    new_codes = sorted(set(df.refcode) - set(old_t.refcode))
    lost = sorted(set(old_t.refcode) - set(df.refcode))
    print(f"table: {len(df)} complexes ({len(lost)} out, {len(new_codes)} in)")
    df.to_csv(HERE / "table.csv", index=False)

    # folds: keep, extend
    keys = pd.Series(b.ligand_groups(pd.concat([old_t, df[df.refcode.isin(new_codes)]], ignore_index=True)),
                     index=list(old_t.refcode) + list(df[df.refcode.isin(new_codes)].refcode))
    grp_fold = old_f.groupby("ligand_group").ligand.first()
    key_of_old = keys.loc[old_t.refcode]
    key2group = dict(zip(key_of_old.to_numpy(), old_f.loc[old_t.refcode].ligand_group.to_numpy()))
    fo = old_f.loc[[r for r in df.refcode if r in old_f.index]].copy()
    rng = np.random.RandomState(0)
    nxt = old_f.ligand_group.max() + 1
    for r in new_codes:
        k = keys[r]
        if k in key2group:
            g = key2group[k]
            lf = grp_fold[g]
        else:
            g, nxt = nxt, nxt + 1
            key2group[k] = g
            lf = int(fo.ligand.value_counts().reindex(range(10), fill_value=0).idxmin())
            grp_fold[g] = lf
        fo.loc[r] = {"random": int(rng.randint(10)), "ligand": lf, "ligand_group": g}
    fo = fo.loc[df.refcode].reset_index().rename(columns={"index": "refcode"})
    fo.to_csv(HERE / "folds.csv", index=False)

    # geometries and inclusion
    reb = {p.stem: p for p in (HERE / "rebuilt_fix6e0590a" / "structures").glob("*.xyz")}
    gained = {p.stem: p for p in (HERE / "gained_fix6e0590a").rglob("*.xyz")}
    need_tmqm = set(new_codes) | {r for r in reb if r in set(df.refcode) and r not in G0["tmqm"]}
    TQ = tmqm_geometries(need_tmqm)
    G = {"tmqm": {}, "mecobi": {}}
    rows = []
    for r in df.itertuples():
        rc = r.refcode
        if rc in gained or rc in reb:
            sym, xyz = read_xyz(gained.get(rc, reb.get(rc)))
            ms = {"sym": sym, "xyz": xyz}
        elif rc in G0["mecobi"]:
            ms = G0["mecobi"][rc]
        else:
            ms = None                                     # excluded before, structure unchanged: keep the old row
        tq = G0["tmqm"].get(rc) or TQ.get(rc)
        if ms is None or tq is None:
            row = old_i.loc[rc].to_dict()
            row["refcode"] = rc
            rows.append(row)
            continue
        feq = Counter(ms["sym"]) == Counter(tq["sym"])
        ceq = int(tq["q"]) == int(r.charge)
        dr = (float(np.sqrt(np.mean((heavy_sorted(ms["sym"], ms["xyz"].astype(float))
                                     - heavy_sorted(tq["sym"], tq["xyz"].astype(float))) ** 2))) if feq else np.nan)
        rows.append({"refcode": rc, "src": tq["src"], "natoms": len(ms["sym"]), "formula_equal": feq,
                     "charge_equal": ceq, "drmsd": dr, "metal": r.metal, "cn": r.cn, "n_hydride": r.n_hydride,
                     "include": bool(feq and ceq)})
        if feq and ceq:
            G["tmqm"][rc], G["mecobi"][rc] = tq, ms
    inc = pd.DataFrame(rows)[old_i.reset_index().columns]
    inc.to_csv(HERE / "inclusion.csv", index=False)
    pickle.dump(G, open(HERE / "geometries.pkl", "wb"))
    print(f"inclusion: {int(inc.include.sum())} of {len(inc)} (formula and charge of the tmQM entry); "
          f"drmsd median {inc[inc.include].drmsd.median():.2f}, 90th percentile {inc[inc.include].drmsd.quantile(.9):.2f}")

    # overlapping atoms in the MeCoBi structures
    bad = []
    for rc, g in G["mecobi"].items():
        x = np.asarray(g["xyz"], float)
        d = np.linalg.norm(x[:, None] - x[None], axis=-1)
        if d[np.triu_indices(len(x), 1)].min() < 0.8:
            bad.append(rc)
    (HERE / "exclude_overlap.txt").write_text("\n".join(sorted(bad)) + "\n")
    print(f"exclude_overlap: {len(bad)}")

    # 2D + RDKit features, row order of the included table
    di = df[df.refcode.isin(set(inc[inc.include].refcode))].reset_index(drop=True)
    R = pd.DataFrame([F.rdkit_block(s) for s in di.ligands], columns=["rd_" + n for n in F.NAMES]).astype(float)
    XR = pd.concat([b.features(di), R.replace([np.inf, -np.inf], np.nan).clip(-1e6, 1e6)], axis=1)
    XR.to_pickle(HERE / "results_soap" / "floor.pkl")
    old_XR = pd.read_pickle(ARCHIVE / "results_soap" / "floor.pkl")
    old_di = old_t[old_t.refcode.isin(set(old_i[old_i.include].index))].reset_index(drop=True)
    pos = pd.Series(range(len(old_di)), index=old_di.refcode)
    both = [k for k, rc in enumerate(di.refcode) if rc in pos.index]
    num = [c for c in XR.columns if str(XR[c].dtype) != "category"]
    ok = np.allclose(XR.iloc[both][num].to_numpy(float), old_XR.iloc[pos[di.refcode.iloc[both]].to_numpy()][num]
                     .to_numpy(float), equal_nan=True)
    print(f"floor.pkl: {XR.shape}; unchanged complexes reproduce the old features: {ok}")
    json.dump({"lost": lost, "gained": new_codes}, open(HERE / "fix6e0590a_changes.json", "w"), indent=0)


if __name__ == "__main__":
    main()
