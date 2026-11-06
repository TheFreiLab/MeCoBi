"""tmQM: GFN2-xTB single points on the tmQM and MeCoBi geometries against the DFT values.

    python analyze_tmqm_xtb.py            # after run_xtb_sp.py --phases vac -> results/sp.csv

A. No training. For gap, HOMO, LUMO, dipole and metal charge: xTB(tmQM geometry) vs DFT (error of the
   method), xTB(MeCoBi) vs DFT (method + geometry) and xTB(MeCoBi) vs xTB(tmQM) (geometry only).
   Spearman, Pearson, raw MAE and the MAE of a linear calibration fitted on the other folds of the
   ligand split (folds.csv). The LightGBM floor on the same rows is given for reference.
B. LightGBM (floor of baseline_2d.py, ligand split, folds.csv), on the 10,188 complexes without
   MeCoBi atoms closer than 0.8 A (exclude_overlap.txt), for dipole and gap:
     floor | floor + xTB(tmQM) | floor + xTB(MeCoBi) | floor + isomer label + xTB(MeCoBi)
     delta: floor + xTB(MeCoBi) trained on DFT - xTB(MeCoBi), xTB added back
   Paired bootstrap over complexes and the number of folds with a lower MAE, as in isomer_control.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LinearRegression

HERE = Path(__file__).resolve().parent
TM = HERE.parent
sys.path.insert(0, str(TM))
import baseline_2d as b  # noqa: E402

XTB = ["gap_eV", "homo_eV", "lumo_eV", "dipole_D", "q_metal"]
DFT = {"gap_eV": "gap_eV", "homo_eV": "homo_eV", "lumo_eV": "lumo_eV", "dipole_D": "dipole_D", "q_metal": "metal_q"}
N_BOOT = 2000
SEEDS = (0, 1, 2)


def load():
    inc = pd.read_csv(TM / "inclusion.csv")
    df = pd.read_csv(TM / "table.csv")
    df = df[df.refcode.isin(set(inc[inc.include].refcode))].reset_index(drop=True)   # row order of floor.pkl
    sp = pd.read_csv(HERE / "results" / "sp.csv")
    sp[["refcode", "arm"]] = sp.complex_id.str.split("__", expand=True)
    sp = sp[sp.ok]
    x = {arm: g.set_index("refcode")[XTB].reindex(df.refcode).reset_index(drop=True) for arm, g in sp.groupby("arm")}
    # xtb gives the dipole of an ion about the origin of the coordinates: for the charged complexes take it from
    # the run on structures centred on the centre of nuclear charge (prepare_tmqm_sp.py --charged-centred)
    cc = pd.read_csv(HERE / "results_charged_centred" / "sp.csv")
    cc[["refcode", "arm"]] = cc.complex_id.str.split("__", expand=True)
    charged = (df.charge != 0).to_numpy()
    for arm, g in cc[cc.ok].groupby("arm"):
        d = g.set_index("refcode").dipole_D.reindex(df.refcode).to_numpy(float)
        x[arm].loc[charged, "dipole_D"] = d[charged]
    return df, x


def calibrated(x, y, fold):
    """Predictions of y ~ a*x + c, fitted on the other folds."""
    x, y, p = np.asarray(x, float).reshape(-1, 1), np.asarray(y, float), np.zeros(len(y))
    for k in range(10):
        te = fold == k
        p[te] = LinearRegression().fit(x[~te], y[~te]).predict(x[te])
    return p


def boot_ci(y, pa, pb, rng):
    d = np.abs(y - pa) - np.abs(y - pb)
    m = d[rng.integers(0, len(d), (N_BOOT, len(d)))].mean(1)
    return d.mean(), *np.quantile(m, [0.025, 0.975])


def part_a(df, x, keep, fold, floor_oof):
    lines = ["A. No training (MAE cal. = linear calibration fitted on the other folds)",
             f"{'quantity':<10}{'comparison':<26}{'n':>6}{'Spearman':>9}{'Pearson':>9}{'MAE raw':>9}{'MAE cal.':>9}"]
    for q in XTB:
        y = df[DFT[q]].to_numpy(float)
        for name, a, ref in (("xTB(tmQM) vs DFT", x["tmqm"][q], y), ("xTB(MeCoBi) vs DFT", x["mecobi"][q], y),
                             ("xTB(MeCoBi) vs xTB(tmQM)", x["mecobi"][q], x["tmqm"][q].to_numpy(float))):
            m = keep & np.isfinite(a.to_numpy(float)) & np.isfinite(ref)
            av, rv = a.to_numpy(float)[m], ref[m]
            cal = calibrated(av, rv, fold[m])
            lines.append(f"{q:<10}{name:<26}{m.sum():>6}{spearmanr(av, rv)[0]:>9.3f}{pearsonr(av, rv)[0]:>9.3f}"
                         f"{np.abs(av - rv).mean():>9.3f}{np.abs(cal - rv).mean():>9.3f}")
        if q in floor_oof:
            m = keep
            lines.append(f"{q:<10}{'LightGBM floor (2D)':<26}{m.sum():>6}{'':>9}{'':>9}{'':>9}"
                         f"{np.abs(floor_oof[q][m] - y[m]).mean():>9.3f}")
    return lines


def part_b(df, x, keep, fold, XR, label):
    rng = np.random.default_rng(0)
    XT = x["tmqm"].add_prefix("xtb_")
    XM = x["mecobi"].add_prefix("xtb_")
    cat = lambda *p: pd.concat(p, axis=1)
    sets = {"floor": cat(XR), "floor + xTB(tmQM)": cat(XR, XT), "floor + xTB(MeCoBi)": cat(XR, XM),
            "floor + label + xTB(MeCoBi)": cat(XR, label, XM)}
    lines, oofs = ["\nB. LightGBM, complexes without MeCoBi atoms < 0.8 A"], {"refcode": df.refcode[keep]}
    idx = np.where(keep)[0]
    f = fold[keep]
    for t in ("dipole_D", "gap_eV"):
        y = df[t].to_numpy(float)[keep]
        oof, fm = {}, {}
        runs = dict(sets)
        runs["delta: floor + xTB(MeCoBi)"] = cat(XR, XM)
        for name, X in runs.items():
            X = X.iloc[idx].reset_index(drop=True)
            base = XM[f"xtb_{t}"].to_numpy(float)[keep] if name.startswith("delta") else np.zeros(len(y))
            p = np.zeros(len(y))
            for seed in SEEDS:                    # mean prediction of three seeds, as in table5_block1.py
                for k in range(10):
                    te = f == k
                    p[te] += (base[te] + lgb.LGBMRegressor(**{**b.PARAMS, "random_state": seed}).fit(
                        X[~te], y[~te] - base[~te]).predict(X[te])) / len(SEEDS)
            oof[name] = p
            fm[name] = np.array([np.abs(y[f == k] - p[f == k]).mean() for k in range(10)])
            e = y - p
            line = f"  {t:<9}{name:<32} MAE {np.abs(e).mean():.3f} ± {fm[name].std():.3f}  R2 {1 - (e**2).sum() / ((y - y.mean())**2).sum():.3f}"
            if name != "floor":
                mm, lo, hi = boot_ci(y, oof["floor"], p, rng)
                line += f" | vs floor {-mm:+.3f} [{-hi:+.3f}, {-lo:+.3f}], lower in {int((fm[name] < fm['floor']).sum())}/10 folds"
            lines.append(line)
            print(line, flush=True)
            oofs[f"{t}|{name}"] = p
    return lines, oofs


def main():
    split = sys.argv[sys.argv.index("--split") + 1] if "--split" in sys.argv else "ligand"
    tag = "" if split == "ligand" else f"_{split}"
    df, x = load()
    excl = set((TM / "exclude_overlap.txt").read_text().split())
    ok = np.isfinite(x["tmqm"].gap_eV.to_numpy(float)) & np.isfinite(x["mecobi"].gap_eV.to_numpy(float))
    keep = ~df.refcode.isin(excl).to_numpy() & ok
    fold = pd.read_csv(TM / "folds.csv").set_index("refcode").loc[df.refcode, split].to_numpy()
    # reference 2D model of part A: the three-seed mean of table5_block1.py (first block of Table 5)
    blk = pd.read_csv(TM / "results_isomer" / "oof_block1.csv").set_index("refcode").loc[df.refcode]
    floor_oof = ({t: blk[f"{t}|2D features"].to_numpy(float) for t in ("dipole_D", "gap_eV")}
                 if split == "ligand" else {})            # that reference exists for the ligand split only
    head = [f"split: {split} (folds.csv)"]
    head += [f"{len(df)} complexes; xTB ok in both geometries: {ok.sum()}; analysed (no MeCoBi atoms < 0.8 A): {keep.sum()}"]
    la = part_a(df, x, keep, fold, floor_oof)
    print("\n".join(head + la), flush=True)
    XR = pd.read_pickle(TM / "results_soap" / "floor.pkl").reset_index(drop=True)
    L = pd.read_pickle(TM / "results_isomer" / "isomer_features.pkl")
    label = L[[c for c in L if c != "label_source"]].reset_index(drop=True)
    lb, oofs = part_b(df, x, keep, fold, XR, label)
    (HERE / "results" / f"metrics_tmqm_xtb{tag}.txt").write_text("\n".join(head + la + lb), encoding="utf-8")
    pd.DataFrame(oofs).to_csv(HERE / "results" / f"oof_tmqm_xtb{tag}.csv", index=False)


if __name__ == "__main__":
    main()
