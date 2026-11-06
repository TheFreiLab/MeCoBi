"""Control for the tmQM case study: is the dipole gain from coordinates, or from the isomer label?

The MeCoBi structures of the benchmark were built with the donors, coordination geometry and isomer
(site map) of the crystal. A 2D model cannot see the isomer, so part of the gain of the 3D models
could be that label and not the coordinates. This script adds the label to the 2D floor, as numbers
and without coordinates:

  geometry  : the coordination polyhedron of the crystal (category)
  trans_X_Y : number of pairs of donor atoms of elements X and Y on opposite sites (angle > 160 deg)
  cis_X_Y   : number of pairs of donor atoms of elements X and Y on neighbouring sites

Models (LightGBM as in baseline_2d.py, folds.csv shared with every other script):
  floor | floor + isomer label | floor + SOAP(tmQM) | floor + isomer label + SOAP(tmQM)
  floor + SOAP(MeCoBi) | floor + isomer label + SOAP(MeCoBi)

Errors are compared by the number of folds in which one model is lower and by a paired bootstrap
over complexes (the paired t-test across folds is anticonservative: training sets overlap).

    python isomer_control.py          # writes results_isomer/metrics.txt, oof.csv, isomer_features.pkl
"""
from __future__ import annotations

import gzip
import json
import sys
from itertools import combinations_with_replacement
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import baseline_2d as b

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
BENCH = HERE.parent / "benchmark"
OUT = HERE / "results_isomer"
sys.path.insert(0, str(HERE.parent.parent / "src"))
from mecobi.assembly.topologies.geometries import SITE_VECTORS  # noqa: E402
from mecobi.model import Geometry  # noqa: E402

TRANS_COS, CIS_COS = -np.cos(np.radians(20)), np.cos(np.radians(135))   # > 160 deg ; < 135 deg
TARGETS = ("dipole_D", "gap_eV")
N_BOOT = 2000


def donor_elements_by_ligand(ligands: list[str], donors: list[list[int]]) -> list[list[str]]:
    out = []
    for smi, idx in zip(ligands, donors):
        m = Chem.MolFromSmiles(smi)
        out.append([m.GetAtomWithIdx(i).GetSymbol() for i in idx])
    return out


def isomer_features(target: dict, ligands: list[str], donors: list[list[int]]) -> dict | None:
    """Label features of one crystal target, or None when the site map does not describe the donors."""
    if not target or not target.get("geometry"):
        return None
    try:
        vecs = np.asarray(SITE_VECTORS[Geometry(target["geometry"])], float)
    except (KeyError, ValueError):
        return None
    f = {"geometry": target["geometry"]}
    if target.get("status") != "ok" or not target.get("site_map"):
        return f | {"label_source": "geometry_only"}
    els = donor_elements_by_ligand(ligands, donors)
    site_el: dict[int, str] = {}
    for seg in target["site_map"].split(";"):
        lig, sites = seg.split(":")
        li = int(lig)
        sites = [int(s) for s in sites.split(",")]
        if li >= len(els) or len(sites) != len(els[li]):
            return f | {"label_source": "geometry_only"}          # haptic ligand: map does not line up
        for s, e in zip(sites, els[li]):
            site_el[s] = e
    if len(site_el) != len(vecs):
        return f | {"label_source": "geometry_only"}
    cos = vecs @ vecs.T
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            a, c = sorted((site_el[i], site_el[j]))
            if cos[i, j] < TRANS_COS:
                f[f"trans_{a}_{c}"] = f.get(f"trans_{a}_{c}", 0) + 1
            elif cos[i, j] > CIS_COS:
                f[f"cis_{a}_{c}"] = f.get(f"cis_{a}_{c}", 0) + 1
    return f | {"label_source": "site_map"}


def build_label_table(df: pd.DataFrame) -> pd.DataFrame:
    targets = json.load(open(BENCH / "_targets30k_merged.json"))
    donors = json.load(open(BENCH / "benchmark_donors.json"))
    rows = [isomer_features(targets.get(r.refcode), r.ligands.split("|"), donors.get(r.refcode, []))
            for r in df.itertuples()]
    L = pd.DataFrame([r or {} for r in rows])
    num = [c for c in L if c.startswith(("trans_", "cis_"))]
    L[num] = L[num].fillna(0).astype(float)
    L["label_source"] = L["label_source"].fillna("none")
    L["geometry"] = L["geometry"].fillna("unknown").astype("category")
    return L


def boot_ci(y, pa, pb, rng):
    """Paired bootstrap over complexes of the MAE reduction MAE(a) - MAE(b): (mean, 2.5%, 97.5%)."""
    d = np.abs(y - pa) - np.abs(y - pb)
    idx = rng.integers(0, len(d), (N_BOOT, len(d)))
    m = d[idx].mean(1)
    return d.mean(), *np.quantile(m, [0.025, 0.975])


def main():
    OUT.mkdir(exist_ok=True)
    inc = pd.read_csv(HERE / "inclusion.csv")
    df = pd.read_csv(HERE / "table.csv")
    df = df[df.refcode.isin(set(inc[inc.include].refcode))].reset_index(drop=True)
    XR = pd.read_pickle(HERE / "results_soap" / "floor.pkl")
    assert len(XR) == len(df)
    L = build_label_table(df)
    L.to_pickle(OUT / "isomer_features.pkl")
    src = L.label_source.value_counts().to_dict()
    feat = L[[c for c in L if c != "label_source"]]
    z = np.load(HERE / "results_soap" / "soap.npz")
    ST, SM = z["tmqm"], z["mecobi"]
    sc = StandardScaler().fit(np.vstack([ST, SM]))
    pca = PCA(64, random_state=0).fit(sc.transform(np.vstack([ST, SM])))
    cols = [f"soap{k}" for k in range(64)]
    PT_, PM_ = (pd.DataFrame(pca.transform(sc.transform(S)), columns=cols) for S in (ST, SM))
    folds = pd.read_csv(HERE / "folds.csv").set_index("refcode").loc[df.refcode].reset_index()
    cat = lambda *p: pd.concat(p, axis=1)
    sets = {"floor": cat(XR), "floor + isomer label": cat(XR, feat),
            "floor + SOAP (tmQM)": cat(XR, PT_), "floor + label + SOAP (tmQM)": cat(XR, feat, PT_),
            "floor + SOAP (MeCoBi)": cat(XR, PM_), "floor + label + SOAP (MeCoBi)": cat(XR, feat, PM_)}
    pairs = [("floor", "floor + isomer label"), ("floor", "floor + SOAP (tmQM)"),
             ("floor + isomer label", "floor + label + SOAP (tmQM)"),
             ("floor + isomer label", "floor + label + SOAP (MeCoBi)"),
             ("floor", "floor + SOAP (MeCoBi)")]
    lines = [f"{len(df)} complexes; label source: {src}; {feat.shape[1]} label features"]
    rng = np.random.default_rng(0)
    oofs = {"refcode": df.refcode}
    for split in ("ligand", "random"):
        for t in TARGETS:
            y = df[t].to_numpy(float)
            lines.append(f"\n[{split} split] {t}")
            oof, fm = {}, {}
            for name, X in sets.items():
                p = np.zeros(len(y))
                for k in range(10):
                    te = (folds[split] == k).to_numpy()
                    p[te] = lgb.LGBMRegressor(**b.PARAMS).fit(X[~te], y[~te]).predict(X[te])
                oof[name] = p
                fm[name] = np.array([np.abs(y[folds[split] == k] - p[folds[split] == k]).mean() for k in range(10)])
                e = y - p
                lines.append(f"  {name:<32} MAE {np.abs(e).mean():.3f} ± {fm[name].std():.3f}  "
                             f"R2 {1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum():.3f}")
                oofs[f"{t}|{split}|{name}"] = p
            for a, c in pairs:
                m, lo, hi = boot_ci(y, oof[a], oof[c], rng)
                lines.append(f"    {a} -> {c}: MAE reduction {m:+.3f}  [95% bootstrap CI {lo:+.3f}, {hi:+.3f}]  "
                             f"lower in {int((fm[c] < fm[a]).sum())}/10 folds")
            print("\n".join(lines[-14:]), flush=True)
    (OUT / "metrics.txt").write_text("\n".join(lines), encoding="utf-8")
    pd.DataFrame(oofs).to_csv(OUT / "oof.csv", index=False)


if __name__ == "__main__":
    main()
