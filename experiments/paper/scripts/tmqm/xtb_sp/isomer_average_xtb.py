"""tmQM, structures from SMILES alone: xTB values of one isomer against averages over all isomers.

    python isomer_average_xtb.py                  # ligand split (folds.csv)
    python isomer_average_xtb.py --split random   # random split

Inputs: ../isomers/manifest_isomers_xtb.csv and ../isomers/results_xtb/sp.csv (single points on every unique
isomer built by build_isomers.py from the SMILES alone), results/sp.csv (xTB of the crystal-isomer structures,
used to train), and the files of analyze_tmqm_xtb.py.

As in smiles_only_xtb.py, for each fold k the LightGBM model is trained on the other folds with the xTB
values of the crystal-isomer structures and applied to the complexes of fold k with these descriptors:
  lowest energy   : the isomer of lowest GFN2-xTB energy
  uniform mean    : mean of the xTB values over the isomers
  Boltzmann mean  : mean weighted by exp(-E_rel / RT), T = 298.15 K
  crystal isomer  : the crystal-isomer structure of the same complex (reference)
A complex is kept when at least one isomer has the tmQM molecular formula and an xTB result, and when its
crystal-isomer structure is usable. Isomers with another formula are dropped from the averages.
"""
import json
import os
import pickle
import sys
from collections import Counter
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
TM = HERE.parent
sys.path.insert(0, str(TM))
import baseline_2d as b  # noqa: E402
from analyze_tmqm_xtb import SEEDS, XTB, boot_ci, load  # noqa: E402

RT = 0.0019872 * 298.15     # kcal/mol


def heavy_sorted(sym, xyz):
    h = np.array([s != "H" for s in sym])
    y = xyz[h]
    d = np.linalg.norm(y[:, None] - y[None], axis=-1)
    return np.sort(d[np.triu_indices(len(y), 1)])


def read_xyz(p):
    lines = Path(p).read_text().splitlines()
    n = int(lines[0])
    return [l.split()[0] for l in lines[2:2 + n]], np.array([[float(v) for v in l.split()[1:4]] for l in lines[2:2 + n]])


def main():
    split = sys.argv[sys.argv.index("--split") + 1] if "--split" in sys.argv else "ligand"
    tag = "" if split == "ligand" else f"_{split}"
    df, x = load()
    XM = x["mecobi"].add_prefix("xtb_")
    XR = pd.read_pickle(TM / "results_soap" / "floor.pkl").reset_index(drop=True)
    folds = pd.read_csv(TM / "folds.csv").set_index("refcode").loc[df.refcode, split].to_numpy()
    excl = set((TM / "exclude_overlap.txt").read_text().split())
    train_ok = ~df.refcode.isin(excl).to_numpy() & XM.notna().all(1).to_numpy()

    iso_dir = Path(os.environ.get("ISO_DIR", TM / "isomers"))   # another build_isomers.py run (prepare_isomer_sp.py)
    man = pd.read_csv(iso_dir / "manifest_isomers_xtb.csv").set_index("complex_id")
    sp = pd.read_csv(iso_dir / "results_xtb" / "sp.csv")
    sp = sp[sp.ok].set_index("complex_id").join(man[["refcode", "E_rel_kcal"]], how="inner")
    G = pickle.load(open(TM / "geometries.pkl", "rb"))
    keep, agree_rows = [], []
    for cid, r in sp.iterrows():
        sym, xyz = read_xyz(iso_dir / "xtb_structures" / f"{cid}.xyz")
        ref = G["tmqm"].get(r.refcode)
        if ref is None or Counter(sym) != Counter(ref["sym"]):
            continue
        keep.append(cid)
        cry = G["mecobi"].get(r.refcode)
        if cry is not None:
            a, c = heavy_sorted(sym, xyz), heavy_sorted(cry["sym"], cry["xyz"].astype(float))
            agree_rows.append((cid, r.refcode, float(np.sqrt(np.mean((a - c) ** 2))) if len(a) == len(c) else np.inf))
    sp = sp.loc[keep]
    agree = pd.DataFrame(agree_rows, columns=["cid", "refcode", "drmsd"]).set_index("cid")
    sp["drmsd_crystal"] = agree.drmsd
    # E_rel was taken against the lowest isomer of the build; re-reference within the kept isomers
    sp["E"] = sp.E_rel_kcal - sp.groupby("refcode").E_rel_kcal.transform("min")
    sp["w"] = np.exp(-sp.E / RT)

    def per_complex(how):
        if how == "lowest":
            return sp.loc[sp.groupby("refcode").E.idxmin()].set_index("refcode")[XTB]
        if how == "uniform":
            return sp.groupby("refcode")[XTB].mean()
        return sp.groupby("refcode")[XTB + ["w"]].apply(lambda g: pd.Series(np.average(g[XTB], axis=0, weights=g.w), index=XTB))

    variants = {k: per_complex(k).reindex(df.refcode).reset_index(drop=True).add_prefix("xtb_")
                for k in ("lowest", "uniform", "boltzmann")}
    # the isomer chosen by the default rules (smiles_only_xtb.py), for the complexes of the 500-sample
    so = pd.read_csv(HERE / "results_smiles_only" / "sp.csv")
    sman = pd.read_csv(HERE / "manifest_smiles_only.csv").set_index("complex_id")
    formula = pd.read_csv(TM / "smiles_only" / "geometry_comparison.csv").set_index("refcode").formula_equal
    so = so[so.ok & so.complex_id.map(sman.dmin).ge(0.8) & so.complex_id.map(formula).eq(True)].set_index("complex_id")
    variants["rule"] = so[XTB].reindex(df.refcode).reset_index(drop=True).add_prefix("xtb_")
    n_iso = sp.groupby("refcode").size().reindex(df.refcode).to_numpy()
    use = train_ok & variants["lowest"].notna().all(1).to_numpy()
    if "--subset" in sys.argv:            # only the complexes that also have the rule-chosen structure
        use &= variants["rule"].notna().all(1).to_numpy()
    low = sp.loc[sp.groupby("refcode").E.idxmin()].set_index("refcode")
    any_agree = sp.groupby("refcode").drmsd_crystal.min().lt(0.2)
    low_agree = low.drmsd_crystal.lt(0.2)
    lines = [f"split: {split} (folds.csv)", f"{sp.refcode.nunique()} complexes with at least one isomer of the tmQM formula; {len(sp)} isomers; "
             f"evaluated: {use.sum()}",
             f"isomers per complex: {dict(sorted(Counter(np.nan_to_num(n_iso[use]).astype(int).clip(max=6)).items()))} (6 = 6 or more)",
             f"an isomer agrees with the crystal-isomer structure (< 0.2 A): {any_agree.mean():.1%}; "
             f"the lowest-energy isomer does: {low_agree.mean():.1%}; "
             f"among complexes with more than one isomer, lowest energy agrees: "
             f"{low_agree[sp.groupby('refcode').size().gt(1)].mean():.1%}"]
    rng = np.random.default_rng(0)
    oof = {}
    for t in ("dipole_D", "gap_eV"):
        y = df[t].to_numpy(float)
        runs = []
        for seed in SEEDS:                    # mean prediction of three seeds, as in Table 5
            prm = {**b.PARAMS, "random_state": seed}
            pred = {k: np.full(len(y), np.nan) for k in ("floor", "crystal isomer", "rule", "lowest", "uniform", "boltzmann")}
            for k in range(10):
                tr, te = (folds != k) & train_ok, (folds == k) & use
                if not te.any():
                    continue
                pred["floor"][te] = lgb.LGBMRegressor(**prm).fit(XR[tr], y[tr]).predict(XR[te])
                m = lgb.LGBMRegressor(**prm).fit(pd.concat([XR, XM], axis=1)[tr], y[tr])
                pred["crystal isomer"][te] = m.predict(pd.concat([XR, XM], axis=1)[te])
                for v, X in variants.items():
                    ok = te & X.notna().all(1).to_numpy()
                    if ok.any():
                        pred[v][ok] = m.predict(pd.concat([XR, X], axis=1)[ok])
            runs.append(pred)
        pred = {v: np.mean([r[v] for r in runs], axis=0) for v in runs[0]}
        oof[t] = pred
        lines.append(f"\n{t}  (n = {use.sum()})")
        for name, p in pred.items():
            if np.isnan(p[use]).any():
                continue
            line = f"  {name:<16} MAE {np.abs(y[use] - p[use]).mean():.3f}"
            if name != "floor":
                mm, lo, hi = boot_ci(y[use], pred["floor"][use], p[use], rng)
                line += f"   vs floor {-mm:+.3f} [{-hi:+.3f}, {-lo:+.3f}]"
            lines.append(line)
        for lab, g in (("one isomer", use & (n_iso == 1)), ("more than one", use & (n_iso > 1))):
            parts = [f"{v} {np.nanmean(np.abs(y[g] - pred[v][g])):.3f}" for v in ("floor", "rule", "lowest", "uniform", "boltzmann", "crystal isomer")]
            lines.append(f"    {lab:<14} n = {g.sum():<5} " + " | ".join(parts))
    txt = "\n".join(lines)
    print(txt)
    name = "metrics_isomer_average_subset481" if "--subset" in sys.argv else "metrics_isomer_average"
    (iso_dir / "results_xtb" / f"{name}{tag}.txt").write_text(txt, encoding="utf-8")
    # out-of-fold predictions of the evaluated complexes, with the number of isomers of each
    out = pd.DataFrame({"refcode": df.refcode[use], "n_isomers": n_iso[use].astype(int)})
    for t, pred in oof.items():
        for v, p in pred.items():
            out[f"{t}|{v}"] = p[use]
    out.to_csv(iso_dir / "results_xtb" / f"oof_{name}{tag}.csv", index=False)


if __name__ == "__main__":
    main()
