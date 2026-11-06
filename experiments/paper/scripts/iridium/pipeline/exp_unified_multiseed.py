"""Multi-seed version of exp_unified.py — quantifies how much the S. aureus classification
varies with the random seed (weight init + batch shuffle + the stratified threshold split).

Same two arms and same models as exp_unified.py, but every model is trained N times with
seeds 42..42+N-1. For each (arm, model, generation, subset) we report:
  * one row per seed (roc_auc / precision / recall / F1 / accuracy / confusion counts),
  * a 'mean' and 'std' row across seeds,
  * an 'ensemble' row = metrics of the mean-over-seeds P_active (threshold = mean of the
    per-seed Youden thresholds).

DimeNet++ is the expensive part; run on a machine with cores to spare (e.g. keisan):
    python exp_unified_multiseed.py --seeds 5
    python exp_unified_multiseed.py --seeds 5 --models ECFP ECFP+Hybrid DimeNet++ --threads 8

Output: outputs/metrics_unified_multiseed.csv
"""
import os
import glob
import json
import random
import argparse
import warnings
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from torch_geometric.loader import DataLoader as GDataLoader
from torch_geometric.data import Data
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_curve, roc_auc_score
from rdkit import Chem
from xyz2graph import MolGraph
warnings.filterwarnings("ignore")

from common import ROOT, ecfp, classification_metrics
from hybrid_train_infer import featurize
from graph_utils import xyz_to_graph, GINEClassifier
import dimenet_shim; dimenet_shim.patch()
from torch_geometric.nn.models import DimeNetPlusPlus

MASTER = os.path.join(ROOT, "outputs", "master_groundtruth_SA.csv")
# Optional overrides, to rerun the structure-based models on another set of structures without touching the
# published outputs or reusing their prediction cache:
#   IRCPSB_STRUCT_ROOT  folder with gen0/ and gen1+2/ (default ../structures)
#   IRCPSB_OUT          output folder (default ../outputs)
STRUCT_ROOT = os.environ.get("IRCPSB_STRUCT_ROOT", os.path.join(ROOT, "structures"))
OUT = os.environ.get("IRCPSB_OUT", os.path.join(ROOT, "outputs"))
CKDIR = os.path.join(OUT, "_sa_multiseed_ckpt")   # per-(arm,model,seed) prediction cache
os.makedirs(CKDIR, exist_ok=True)
print(f"structures: {STRUCT_ROOT} | outputs: {OUT}", flush=True)
PT = Chem.GetPeriodicTable()
SFX = {"ECFP": "ECFP", "ECFP+Hybrid": "Hybrid", "GINE": "GINE", "DimeNet++": "DimeNet"}
ARM_TAG = {"gen0->gen1+2": "A_gen0", "gen0+1->gen2": "B_gen01"}   # filesystem-safe names


def load_or_train(arm, disp, sd, compute):
    """Return (probs_dict, thr), reading from disk if this (arm,model,seed) was already done.
    `compute` is a zero-arg callable returning (probs_dict, thr). Makes the run RESUMABLE:
    a killed run continues where it stopped instead of losing everything."""
    fp = os.path.join(CKDIR, f"{ARM_TAG.get(arm, arm)}_{SFX[disp]}_s{sd}.json")
    if os.path.exists(fp):
        d = json.load(open(fp, encoding="utf-8"))
        print(f"    [{arm}] {disp} seed {sd} CACHED (thr={float(d['thr']):.3f})", flush=True)
        return d["probs"], float(d["thr"])
    probs, thr = compute()
    json.dump({"probs": {str(k): float(v) for k, v in probs.items()}, "thr": float(thr)},
              open(fp, "w", encoding="utf-8"))
    print(f"    [{arm}] {disp} seed {sd} trained (thr={thr:.3f})", flush=True)
    return probs, thr


def set_seed(sd):
    random.seed(sd); np.random.seed(sd); torch.manual_seed(sd)


def youden(y, p):
    if len(set(map(int, y))) < 2:
        return 0.5
    fpr, tpr, t = roc_curve(y, p)
    return float(t[np.argmax(tpr - fpr)])


def stem_paths():
    idx = {}
    for folder in [os.path.join(STRUCT_ROOT, "gen0"),
                   os.path.join(STRUCT_ROOT, "gen1+2")]:
        for f in glob.glob(os.path.join(folder, "*.xyz")):
            idx[os.path.splitext(os.path.basename(f))[0].replace("_OPT", "")] = f
    return idx


STEMS = stem_paths()


# ---------------- fingerprint models ----------------
class FMLP(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d, 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(),
                                 nn.Linear(32, 1))
    def forward(self, x):
        return self.net(x).squeeze(1)


def fp_feat(df, kind):
    if kind == "ECFP":
        return np.stack([ecfp(s) for s in df.fp_smiles]).astype(np.float32)
    return featurize(df.fp_smiles.tolist())


def fp_fit(X, y, kind, sd, epochs=250):
    set_seed(sd)
    imp = SimpleImputer(strategy="median" if kind == "ECFP+Hybrid" else "constant",
                        fill_value=0).fit(X)
    sc = StandardScaler().fit(imp.transform(X))
    Xs = sc.transform(imp.transform(X)).astype(np.float32)
    m = FMLP(Xs.shape[1]); opt = torch.optim.Adam(m.parameters(), lr=3e-4, weight_decay=1e-3)
    lf = nn.BCEWithLogitsLoss()
    dl = DataLoader(TensorDataset(torch.tensor(Xs), torch.tensor(y.astype(np.float32))),
                    batch_size=64, shuffle=True)
    for _ in range(epochs):
        m.train()
        for xb, yb in dl:
            opt.zero_grad(); lf(m(xb), yb).backward(); opt.step()
    return (m, imp, sc)


def fp_prob(bundle, X):
    m, imp, sc = bundle
    m.eval()
    with torch.no_grad():
        return torch.sigmoid(m(torch.tensor(sc.transform(imp.transform(X)).astype(np.float32)))).numpy()


def run_fp(kind, train_df, pred_df, sd):
    Xtr, ytr = fp_feat(train_df, kind), train_df.SA_active.astype(int).values
    Xpr = fp_feat(pred_df, kind)
    itr, iva = train_test_split(np.arange(len(ytr)), test_size=0.2, stratify=ytr, random_state=sd)
    thr = youden(ytr[iva], fp_prob(fp_fit(Xtr[itr], ytr[itr], kind, sd), Xtr[iva]))
    p = fp_prob(fp_fit(Xtr, ytr, kind, sd), Xpr)
    return dict(zip(pred_df.compound_id, p)), thr


# ---------------- graph models ----------------
def build_graph(cid, stem, kind):
    f = STEMS.get(stem)
    if f is None:
        return None
    if kind == "GINE":
        return xyz_to_graph(f, cid)
    mg = MolGraph(); mg.read_xyz(f)
    z = torch.tensor([PT.GetAtomicNumber(e) for e in mg.elements], dtype=torch.long)
    pos = torch.tensor(np.vstack([mg.x, mg.y, mg.z]).T.astype("float32"))
    d = Data(z=z, pos=pos); d.identifier = cid
    return d


def graphs_for(df, kind, with_label):
    out = []
    for _, r in df.iterrows():
        g = build_graph(r.compound_id, r.structure_stem, kind)
        if g is None:
            continue
        if with_label:
            g.y = torch.tensor([float(int(r.SA_active))])
        out.append((r.compound_id, g))
    return out


def gine_fit(graphs, sd, epochs=50):
    set_seed(sd)
    y = np.array([int(g.y.item()) for _, g in graphs])
    pw = torch.tensor([(y == 0).sum() / max(1, (y == 1).sum())], dtype=torch.float)
    m = GINEClassifier(graphs[0][1].x.size(1), hidden=128)
    opt = torch.optim.Adam(m.parameters(), lr=3e-4, weight_decay=1e-3)
    lf = nn.BCEWithLogitsLoss(pos_weight=pw)
    dl = GDataLoader([g for _, g in graphs], batch_size=32, shuffle=True)
    for _ in range(epochs):
        m.train()
        for b in dl:
            opt.zero_grad(); lf(m(b.x, b.edge_index, b.edge_attr, b.batch), b.y.view(-1)).backward(); opt.step()
    return m


def gine_prob(m, graphs):
    m.eval(); out = {}
    with torch.no_grad():
        for cid, g in graphs:
            b = torch.zeros(g.x.size(0), dtype=torch.long)
            out[cid] = float(torch.sigmoid(m(g.x, g.edge_index, g.edge_attr, b)))
    return out


def dimenet_fit(graphs, sd, epochs=25):
    set_seed(sd)
    y = np.array([int(g.y.item()) for _, g in graphs])
    pw = torch.tensor([(y == 0).sum() / max(1, (y == 1).sum())], dtype=torch.float)
    hp = dict(hidden_channels=32, out_channels=1, num_blocks=4, num_spherical=2, num_radial=4,
              cutoff=3.5, envelope_exponent=5, int_emb_size=32, basis_emb_size=32, out_emb_channels=32)
    m = DimeNetPlusPlus(**hp)
    opt = torch.optim.Adam(m.parameters(), lr=1e-3); lf = nn.BCEWithLogitsLoss(pos_weight=pw)
    dl = GDataLoader([g for _, g in graphs], batch_size=16, shuffle=True)
    for _ in range(epochs):
        m.train()
        for b in dl:
            opt.zero_grad(); lf(m(b.z, b.pos, b.batch).squeeze(-1), b.y.view(-1)).backward(); opt.step()
    return m


def dimenet_prob(m, graphs):
    m.eval(); out = {}
    with torch.no_grad():
        for cid, g in graphs:
            out[cid] = float(torch.sigmoid(m(g.z, g.pos, torch.zeros(len(g.z), dtype=torch.long))))
    return out


def run_graph(kind, cache, sd):
    fitf, probf = (gine_fit, gine_prob) if kind == "GINE" else (dimenet_fit, dimenet_prob)
    gtr = cache["train"]; gpr = cache["pred"]
    y = np.array([int(g.y.item()) for _, g in gtr])
    itr, iva = train_test_split(np.arange(len(gtr)), test_size=0.2, stratify=y, random_state=sd)
    m80 = fitf([gtr[i] for i in itr], sd)
    pval = probf(m80, [gtr[i] for i in iva])
    yval = [int(gtr[i][1].y.item()) for i in iva]
    thr = youden(yval, [pval[gtr[i][0]] for i in iva])
    mfull = fitf(gtr, sd)
    return probf(mfull, gpr), thr


# ---------------- driver ----------------
def f1_of(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return round(2 * p * r / (p + r), 4) if p + r else 0.0


def eval_subset(sub, sfx, prob_map, thr):
    """classification metrics for one subset given a P_active map + threshold."""
    s = sub.dropna(subset=["SA_active"]).copy()
    s = s[s.compound_id.isin(prob_map)]
    if len(s) == 0 or s.SA_active.nunique() < 2:
        return None
    score = s.compound_id.map(prob_map).astype(float).values
    yhat = (score >= thr).astype(int)
    met = classification_metrics(s.SA_active.astype(int).values, yhat, score)
    met["f1"] = f1_of(met["TP"], met["FP"], met["FN"])
    return met


def arm_subsets(pred_df, train_keys):
    """Yield (generation, subset_label, sub_df) exactly like exp_unified.metrics_block."""
    for gen in sorted(pred_df.generation.unique()):
        cp = pred_df[(pred_df.generation == gen) & (pred_df.conv_pass) & pred_df.SA_active.notna()]
        yield gen, "conv>=40 (all)", cp
        if gen == "gen2":
            yield gen, "conv>=40 (no leaks)", cp[~cp.bb_key.isin(train_keys)]


def _all_cached(arm, disp, seeds):
    return all(os.path.exists(os.path.join(CKDIR, f"{ARM_TAG.get(arm, arm)}_{SFX[disp]}_s{sd}.json"))
               for sd in seeds)


def run_arm(arm, train_df, pred_df, train_keys, models, seeds):
    # build graph caches ONCE (geometry is seed-independent) — skip if every seed of that
    # graph model is already cached, so a resumed run doesn't rebuild ~1800 graphs for nothing.
    gcache = {}
    for kind in [k for k in models if k in ("GINE", "DimeNet++")]:
        if _all_cached(arm, kind, seeds):
            continue
        gcache[kind] = dict(train=graphs_for(train_df, kind, True),
                            pred=graphs_for(pred_df, kind, False))
    rows = []
    for disp in models:
        sfx = SFX[disp]
        seed_probs, seed_thr = [], []
        for sd in seeds:
            if disp in ("ECFP", "ECFP+Hybrid"):
                probs, thr = load_or_train(arm, disp, sd,
                                           lambda: run_fp(disp, train_df, pred_df, sd))
            else:
                probs, thr = load_or_train(arm, disp, sd,
                                           lambda: run_graph(disp, gcache[disp], sd))
            seed_probs.append(probs); seed_thr.append(thr)
            for gen, label, sub in arm_subsets(pred_df, train_keys):
                met = eval_subset(sub, sfx, probs, thr)
                if met:
                    rows.append(dict(arm=arm, method=disp, generation=gen, subset=label,
                                     seed=sd, thr=round(thr, 4), **met))
        # ensemble = mean P_active over seeds; threshold = mean of per-seed thresholds
        ens = {cid: float(np.mean([sp[cid] for sp in seed_probs if cid in sp]))
               for cid in seed_probs[0]}
        ethr = float(np.mean(seed_thr))
        for gen, label, sub in arm_subsets(pred_df, train_keys):
            met = eval_subset(sub, sfx, ens, ethr)
            if met:
                rows.append(dict(arm=arm, method=disp, generation=gen, subset=label,
                                 seed="ensemble", thr=round(ethr, 4), **met))
    return rows


def summarise(df):
    """Add per-(arm,method,gen,subset) mean/std rows across the numeric seed rows."""
    num = ["roc_auc", "precision", "recall", "f1", "accuracy"]
    per = df[df.seed.apply(lambda s: str(s).isdigit())]
    add = []
    for key, g in per.groupby(["arm", "method", "generation", "subset"]):
        base = dict(zip(["arm", "method", "generation", "subset"], key))
        for tag, fn in [("mean", np.mean), ("std", np.std)]:
            add.append({**base, "seed": tag, "n": g.n.iloc[0], "n_active": g.n_active.iloc[0],
                        **{c: round(float(fn(g[c])), 4) for c in num}})
    return pd.concat([df, pd.DataFrame(add)], ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--models", nargs="+", default=["ECFP", "ECFP+Hybrid", "DimeNet++"],
                    choices=["ECFP", "ECFP+Hybrid", "GINE", "DimeNet++"])
    ap.add_argument("--threads", type=int, default=0)
    args = ap.parse_args()
    if args.threads > 0:
        torch.set_num_threads(args.threads)
    seeds = list(range(42, 42 + args.seeds))
    print(f"models={args.models}  seeds={seeds}  threads={torch.get_num_threads()}", flush=True)

    m = pd.read_csv(MASTER)
    g0_keys = set(m[(m.generation == "gen0") & m.conv_pass].bb_key)
    g01_keys = set(m[(m.generation.isin(["gen0", "gen1"])) & m.conv_pass].bb_key)

    rows = []
    print("### ARM A: train gen0 -> predict gen1+2", flush=True)
    trainA = m[(m.generation == "gen0") & (m.conv_pass) & m.SA_active.notna()].copy()
    predA = m[m.generation.isin(["gen1", "gen2"])].copy()
    rows += run_arm("gen0->gen1+2", trainA, predA, g0_keys, args.models, seeds)

    print("### ARM B: train gen0+1 -> predict gen2", flush=True)
    trainB = m[(m.generation.isin(["gen0", "gen1"])) & (m.conv_pass) & m.SA_active.notna()].copy()
    predB = m[m.generation == "gen2"].copy()
    rows += run_arm("gen0+1->gen2", trainB, predB, g01_keys, args.models, seeds)

    out = summarise(pd.DataFrame(rows))
    keepc = ["arm", "method", "generation", "subset", "seed", "n", "n_active",
             "roc_auc", "precision", "recall", "f1", "accuracy", "thr", "TP", "TN", "FP", "FN"]
    out = out[[c for c in keepc if c in out.columns]]
    dest = os.path.join(OUT, "metrics_unified_multiseed.csv")
    out.to_csv(dest, index=False)
    print(f"\nwrote {dest}")
    # headline: ROC-AUC spread on the no-leaks gen2 subset
    print("\n=== ROC-AUC (gen2, no leaks) — spread across seeds ===")
    v = out[(out.generation == "gen2") & (out.subset == "conv>=40 (no leaks)") &
            (out.seed.isin(["mean", "std", "ensemble"]))]
    print(v.pivot_table(index=["arm", "method"], columns="seed", values="roc_auc").to_string())


if __name__ == "__main__":
    main()
