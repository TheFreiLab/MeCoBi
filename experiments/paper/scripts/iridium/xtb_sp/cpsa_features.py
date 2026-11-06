"""logP: charged partial surface areas (CPSA) and exposure of the metal as extra features.

    python cpsa_features.py MetalLipoDB.csv

Per complex (the 3,396 structures of results_full; charges from the vacuum GFN2-xTB single point, sp.jsonl):
  per-atom SASA by Shrake-Rupley (Bondi radii, metals 2.0 A, probe 1.4 A, 240 points per atom)
  CPSA (Stanton and Jurs) PPSA1/PNSA1 area of positive/negative atoms, PPSA2/PNSA2 area x total positive/negative
                          charge, PPSA3/PNSA3 sum of q x area, DPSA1, FPSA1/FNSA1 (fractions of the total), total
                          SASA, polar SASA (N, O, S and the H on them), charge-weighted surface (sum q x area / SASA)
  metal exposure          SASA of the metal (probe 1.4 A and probe 0.5 A), percent buried volume in spheres of
                          3.5 and 5 A around the metal (Bondi x 1.17, metal excluded, 0.1/0.2 A grid; as in
                          SambVca), and the solid-angle coverage of the metal (fraction of 2,000 rays from the
                          metal that hit an atom sphere of Bondi radius)
Feature sets on top of the 2D table: + CPSA, + metal exposure, + CPSA + metal + donors (shape_donor_features.py).
LightGBM and the MLP of xtb_features_mlp.py, smiles and doi splits, same folds.
"""
import json
import sys
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.spatial import cKDTree
from scipy.stats import ttest_rel

from analyze_logp import HERE, b, xtb_table
from shape_donor_features import DON, fold_fit
from shape_donor_features import features as shape_donor
from xtb_features_mlp import mlp

warnings.filterwarnings("ignore")
BONDI = {"H": 1.20, "B": 1.92, "C": 1.70, "N": 1.55, "O": 1.52, "F": 1.47, "Si": 2.10, "P": 1.80, "S": 1.80,
         "Cl": 1.75, "As": 1.85, "Se": 1.90, "Br": 1.85, "Te": 2.06, "I": 1.98}
PROBE = 1.4
CPSA = ["PPSA1", "PNSA1", "PPSA2", "PNSA2", "PPSA3", "PNSA3", "DPSA1", "FPSA1", "FNSA1", "SASA", "SASA_polar",
        "q_surface"]
METAL = ["metal_sasa", "metal_sasa_p05", "Vbur35", "Vbur50", "coverage"]


def sphere(n=240):
    k = np.arange(n) + 0.5
    phi, th = np.arccos(1 - 2 * k / n), np.pi * (1 + 5 ** 0.5) * k
    return np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)]


UNIT = sphere()
RAYS = sphere(2000)


def grid(r, h):
    g = np.arange(-r, r + 1e-6, h)
    pts = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3)
    return pts[np.linalg.norm(pts, axis=1) <= r]


GRIDS = {3.5: grid(3.5, 0.1), 5.0: grid(5.0, 0.2)}


def read_xyz(p):
    lines = p.read_text().splitlines()
    n = int(lines[0])
    return ([ln.split()[0] for ln in lines[2:2 + n]],
            np.array([[float(v) for v in ln.split()[1:4]] for ln in lines[2:2 + n]]))


def sasa(xyz, rad, probe=PROBE):
    tree, out = cKDTree(xyz), np.zeros(len(xyz))
    big = rad + probe
    for i in range(len(xyz)):
        nb = [j for j in tree.query_ball_point(xyz[i], big[i] + big.max()) if j != i]
        pts = xyz[i] + big[i] * UNIT
        free = np.ones(len(pts), bool)
        if nb:
            d = np.linalg.norm(pts[:, None] - xyz[nb][None], axis=-1)
            free = ~(d < big[nb][None]).any(1)
        out[i] = 4 * np.pi * big[i] ** 2 * free.mean()
    return out


def one(sym, xyz, q, mi):
    rad = np.array([BONDI.get(s, 2.0) for s in sym])
    a = sasa(xyz, rad)
    q = np.asarray(q)
    pos, neg = q > 0, q < 0
    heavy_polar = np.array([s in ("N", "O", "S") for s in sym])
    tree = cKDTree(xyz)
    polar = heavy_polar.copy()
    for i, s in enumerate(sym):
        if s == "H":
            polar[i] = heavy_polar[tree.query(xyz[i], k=2)[1][1]]
    tot = a.sum()
    f = {"PPSA1": a[pos].sum(), "PNSA1": a[neg].sum(), "PPSA2": a[pos].sum() * q[pos].sum(),
         "PNSA2": a[neg].sum() * q[neg].sum(), "PPSA3": (q * a)[pos].sum(), "PNSA3": (q * a)[neg].sum(),
         "SASA": tot, "SASA_polar": a[polar].sum(), "q_surface": (q * a).sum() / tot}
    f["DPSA1"], f["FPSA1"], f["FNSA1"] = f["PPSA1"] - f["PNSA1"], f["PPSA1"] / tot, f["PNSA1"] / tot
    others = np.delete(np.arange(len(sym)), mi)
    for r, key in ((3.5, "Vbur35"), (5.0, "Vbur50")):
        near = others[np.linalg.norm(xyz[others] - xyz[mi], axis=1) < r + 1.17 * rad.max()]
        d = np.linalg.norm((GRIDS[r] + xyz[mi])[:, None] - xyz[near][None], axis=-1)
        f[key] = 100 * (d < 1.17 * rad[near][None]).any(1).mean()
    c = xyz[others] - xyz[mi]
    proj = c @ RAYS.T
    perp2 = (c ** 2).sum(1)[:, None] - proj ** 2
    f["coverage"] = ((proj > 0) & (perp2 < rad[others][:, None] ** 2)).any(0).mean()
    f["metal_sasa"], f["metal_sasa_p05"] = a[mi], sasa(xyz, rad, 0.5)[mi]
    return f


def _run(sdir, cid, q, mi):
    sym, xyz = read_xyz(sdir / f"{cid}.xyz")
    return cid, one(sym, xyz, q, mi)


def features():
    cache = HERE / "results_full" / "cpsa_features.csv"
    if cache.exists():
        return pd.read_csv(cache, index_col=0)
    man = pd.read_csv(HERE / "manifest_full.csv").set_index("complex_id")
    sdir = HERE.parent / "runs" / "full" / "structures"
    jobs = []
    for line in open(HERE / "results_full" / "sp.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r["phase"] == "vac" and r["ok"] and r.get("charges"):
            jobs.append((r["complex_id"], r["charges"], int(man.metal_index[r["complex_id"]])))
    res = Parallel(n_jobs=8)(delayed(_run)(sdir, *j) for j in jobs)
    f = pd.DataFrame({c: v for c, v in res}).T[CPSA + METAL].astype(float)
    f.to_csv(cache)
    return f


def main():
    feat = features().join(shape_donor()[DON])
    xt = xtb_table(HERE / "results_full" / "sp.csv")
    df, X = b.build_table(sys.argv[1])
    rec = pd.read_csv(HERE.parent / "inputs" / "records_to_complex.csv").set_index("record_id").complex_id
    cid = df.record_id.map(rec)
    keep = (cid.isin(xt.index) & cid.isin(feat.index)).to_numpy()
    df, X, cid = df[keep].reset_index(drop=True), X[keep].reset_index(drop=True), cid[keep].reset_index(drop=True)
    F = feat.loc[cid].reset_index(drop=True)
    sets = {"2D": X, "2D + CPSA": pd.concat([X, F[CPSA]], axis=1),
            "2D + metal exposure": pd.concat([X, F[METAL]], axis=1),
            "2D + CPSA + metal + donors": pd.concat([X, F[CPSA + METAL + DON]], axis=1)}
    y = df.value.to_numpy(float)
    lines = [f"{len(df)} measurements, {cid.nunique()} complexes",
             "Vbur50 median %.1f [10th %.1f, 90th %.1f]; corr(SASA, heavy atoms) %.3f; corr(SASA_polar, TPSA) %.3f" % (
                 F.Vbur50.median(), F.Vbur50.quantile(.1), F.Vbur50.quantile(.9),
                 np.corrcoef(F.SASA, X.L_heavy.fillna(0))[0, 1], np.corrcoef(F.SASA_polar, X.L_tpsa.fillna(0))[0, 1])]
    print("\n".join(lines), flush=True)
    for split, gr in {"smiles": pd.factorize(df.metal + "|" + df.smiles_ligands)[0], "doi": b.components(df)}.items():
        folds = b.make_folds(gr)
        for model in ("LightGBM", "MLP"):
            lines.append(f"[{split} split, {model}]")
            print(lines[-1], flush=True)
            fm = {}
            for name, Fx in sets.items():
                oof = np.zeros(len(y))
                if model == "LightGBM":
                    for tr, te in folds:
                        oof[te] = lgb.LGBMRegressor(**{**b.PARAMS, "n_jobs": 8}).fit(Fx.iloc[tr], y[tr]).predict(Fx.iloc[te])
                else:
                    for te, p in Parallel(n_jobs=8)(delayed(fold_fit)(lambda: mlp(Fx), Fx, y, tr, te) for tr, te in folds):
                        oof[te] = p
                fm[name] = np.array([np.abs(y[te] - oof[te]).mean() for _, te in folds])
                extra = ""
                if name != "2D":
                    d = fm[name] - fm["2D"]
                    extra = (f" | vs 2D {d.mean():+.3f} (lower in {int((d < 0).sum())}/10, "
                             f"P = {ttest_rel(fm[name], fm['2D']).pvalue:.3f})")
                lines.append(f"  {name:<28} MAE {np.abs(y - oof).mean():.3f} ± {fm[name].std():.3f}{extra}")
                print(lines[-1], flush=True)
    (HERE / "results_full" / "metrics_cpsa.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
