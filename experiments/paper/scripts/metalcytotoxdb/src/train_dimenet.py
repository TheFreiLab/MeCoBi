"""DimeNet++ 3D model (Models 3 & 4): geometric GNN on the generated Ru structures.

The molecular encoder (DimeNet++) sees ONLY the 3D graph (atom types + coordinates). Its embedding is
concatenated with non-3D features at the classification head:

    mode=context  (Model 4): embedding + descriptors(LogP/TPSA/MW) + charge + exposure time + cell line
    mode=mol_only (Model 3): embedding + descriptors + charge          (no cell line, no exposure time)

Both include the physicochemical scalars, per the fair-comparison decision.

*** encode-once training ***
A complex appears in many measurement rows (different cell line / exposure time), but its 3D structure
is identical. So each UNIQUE complex graph is encoded ONCE per epoch and its embedding is broadcast to
all its rows (which differ only in the cheap context vector). The optimizer steps over batches of
complexes; every row's BCE loss is still computed. This cuts the expensive geometric message passing
from ~11k encodes/epoch (one per row) to ~4k (one per complex) -- the difference between feasible and
not on CPU.

Same shared DOI folds as LightGBM/MLP, same target, per-fold StandardScaler on continuous context
features (fit on train), pos_weight for imbalance, early stopping on an inner grouped split. Only
complexes with a usable structure (ru_structure_map.csv quality_ok) are included; used row_ids are saved
so LightGBM/MLP can be re-scored on the SAME rows. Uses dimenet_shim (pure-torch radius_graph/triplets).

Usage (Keisan, CPU):
    python -u src/train_dimenet.py --mode context --folds 0 1 2 \
        --cutoff 3.5 --num-spherical 2 --num-radial 4 --hidden-channels 32   # pilot
    python -u src/train_dimenet.py --mode context                            # full 10-fold
    python src/train_dimenet.py --selftest                                    # mechanical check
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

import dimenet_shim
dimenet_shim.patch()  # must precede DimeNetPlusPlus use
from torch_geometric.data import Data, Batch  # noqa: E402
from torch_geometric.nn.models import DimeNetPlusPlus  # noqa: E402
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
                             f1_score, roc_auc_score, roc_curve, confusion_matrix)  # noqa: E402
from sklearn.model_selection import GroupShuffleSplit  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from run_guard import guard_run, check_signature, signature  # noqa: E402
from feature_engineering import load_features  # noqa: E402
from splitting import iter_folds  # noqa: E402

PROJECT_ROOT = _HERE.parent
DATASET = PROJECT_ROOT / "data" / "processed" / "ru_article.parquet"
STRUCT_MAP = PROJECT_ROOT / "data" / "processed" / "ru_structure_map.csv"
SPLITS = PROJECT_ROOT / "splits"
REPORTDIR = PROJECT_ROOT / "results" / "reports"
TABLEDIR = PROJECT_ROOT / "results" / "tables"
FIGDIR = PROJECT_ROOT / "results" / "figures"
CKPTDIR = PROJECT_ROOT / "results" / "checkpoints"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

DIME_DEFAULT = dict(hidden_channels=64, num_blocks=4, int_emb_size=64, basis_emb_size=8,
                    out_emb_channels=64, num_spherical=7, num_radial=6, cutoff=5.0,
                    envelope_exponent=5, max_num_neighbors=32)

_SYM2Z = {"H": 1, "B": 5, "C": 6, "N": 7, "O": 8, "F": 9, "Na": 11, "Mg": 12, "Al": 13, "Si": 14,
          "P": 15, "S": 16, "Cl": 17, "K": 19, "Ca": 20, "Ti": 22, "V": 23, "Cr": 24, "Mn": 25,
          "Fe": 26, "Co": 27, "Ni": 28, "Cu": 29, "Zn": 30, "Ga": 31, "Ge": 32, "As": 33, "Se": 34,
          "Br": 35, "Rb": 37, "Sr": 38, "Y": 39, "Zr": 40, "Nb": 41, "Mo": 42, "Tc": 43, "Ru": 44,
          "Rh": 45, "Pd": 46, "Ag": 47, "Cd": 48, "In": 49, "Sn": 50, "Sb": 51, "Te": 52, "I": 53,
          "Cs": 55, "Ba": 56, "La": 57, "W": 74, "Re": 75, "Os": 76, "Ir": 77, "Pt": 78, "Au": 79,
          "Hg": 80, "Tl": 81, "Pb": 82, "Bi": 83}


def read_xyz(path: str) -> Data:
    lines = Path(path).read_text().splitlines()
    n = int(lines[0].split()[0])
    zs, ps = [], []
    for ln in lines[2:2 + n]:
        p = ln.split()
        z = _SYM2Z.get(p[0]) or _SYM2Z.get(p[0].capitalize())
        if z is None:
            raise ValueError(f"unknown element '{p[0]}' in {path}")
        zs.append(z)
        ps.append([float(p[1]), float(p[2]), float(p[3])])
    return Data(z=torch.tensor(zs, dtype=torch.long), pos=torch.tensor(ps, dtype=torch.float32))


class MLPHead(nn.Module):
    def __init__(self, in_dim, hidden, p):
        super().__init__()
        layers, d = [], in_dim
        for h in hidden:
            layers += [nn.Linear(d, h), nn.ReLU(), nn.Dropout(p)]
            d = h
        layers += [nn.Linear(d, 1)]
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x).squeeze(-1)


class DimeNetClassifier(nn.Module):
    def __init__(self, emb_dim, ctx_dim, dime_kwargs, head_hidden, dropout):
        super().__init__()
        self.enc = DimeNetPlusPlus(out_channels=emb_dim, **dime_kwargs)
        self.head = MLPHead(emb_dim + ctx_dim, head_hidden, dropout)

    def encode(self, batch):
        return self.enc(batch.z, batch.pos, batch.batch)   # [n_graphs, emb_dim]

    def classify(self, emb_rows, ctx_rows):
        return self.head(torch.cat([emb_rows, ctx_rows], dim=1))


def set_seed(s):
    np.random.seed(s); torch.manual_seed(s)


def _rows_by_comp(rows, row_local):
    """dict {complex_local_idx -> [row indices]} restricted to `rows`."""
    d = {}
    for r in rows:
        d.setdefault(int(row_local[r]), []).append(int(r))
    return d


def _encode_rows(model, uniq_graphs, rows, row_local, ctx, enc_bs, tta=True):
    """No-grad embeddings for `rows`; each complex's embedding is the MEAN over its isomers when
    tta=True (test-time augmentation), else just the first isomer (fast, for early-stopping eval).
    uniq_graphs[c] is a list of isomer Data. Returns [len(rows), emb]."""
    comps = sorted({int(row_local[r]) for r in rows})
    pos_in = {c: j for j, c in enumerate(comps)}
    flat_data, flat_comp = [], []
    for c in comps:
        for g in (uniq_graphs[c] if tta else uniq_graphs[c][:1]):
            flat_data.append(g); flat_comp.append(pos_in[c])
    embs = []
    model.eval()
    with torch.no_grad():
        for i in range(0, len(flat_data), enc_bs):
            b = Batch.from_data_list(flat_data[i:i + enc_bs]).to(DEVICE)
            embs.append(model.encode(b).cpu())
    E = torch.cat(embs, 0)                       # [n_isomers_total, emb]
    d = E.shape[1]
    comp_emb = torch.zeros(len(comps), d)
    counts = torch.zeros(len(comps), 1)
    fc = torch.tensor(flat_comp)
    comp_emb.index_add_(0, fc, E)
    counts.index_add_(0, fc, torch.ones(len(fc), 1))
    comp_emb = comp_emb / counts                 # mean over isomers per complex
    idx = torch.tensor([pos_in[int(row_local[r])] for r in rows])
    return comp_emb[idx], torch.tensor(ctx[rows], dtype=torch.float32)


def _predict(model, uniq_graphs, rows, row_local, ctx, enc_bs, tta=True):
    er, cr = _encode_rows(model, uniq_graphs, rows, row_local, ctx, enc_bs, tta=tta)
    with torch.no_grad():
        return torch.sigmoid(model.classify(er.to(DEVICE), cr.to(DEVICE))).cpu().numpy()


def _auc(model, uniq_graphs, rows, row_local, ctx, y, enc_bs, tta=True):
    p = _predict(model, uniq_graphs, rows, row_local, ctx, enc_bs, tta=tta)
    yy = y[rows]
    return roc_auc_score(yy, p) if len(np.unique(yy)) > 1 else 0.5


def train_one(uniq_graphs, tr_rows, iv_rows, row_local, ctx, y, ctx_dim, args):
    model = DimeNetClassifier(args.emb_dim, ctx_dim, args.dime,
                              tuple(args.head_hidden), args.dropout).to(DEVICE)
    ytr = y[tr_rows]
    pos_w = torch.tensor([(ytr == 0).sum() / max(1, (ytr == 1).sum())], dtype=torch.float32,
                         device=DEVICE)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_w)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    rbc = _rows_by_comp(tr_rows, row_local)
    train_comps = np.array(sorted(rbc))
    ctx_t = torch.tensor(ctx, dtype=torch.float32)
    y_t = torch.tensor(y, dtype=torch.float32)

    # training UNITS: stochastic -> one (complex, random isomer) per complex per epoch;
    # full -> every (complex, isomer) pair each epoch (each isomer a separate instance, same label).
    if args.aug_mode == "full":
        units = [(int(c), j) for c in train_comps for j in range(len(uniq_graphs[int(c)]))]
    else:
        units = [(int(c), None) for c in train_comps]
    units = np.array(units, dtype=object)

    best_auc, best_state, bad = -1.0, None, 0
    for _ep in range(args.epochs):
        model.train()
        order = np.random.permutation(len(units))
        for i in range(0, len(units), args.comp_batch):
            ub = units[order[i:i + args.comp_batch]]
            sel = [uniq_graphs[c][(j if j is not None else np.random.randint(len(uniq_graphs[c])))]
                   for c, j in ub]
            b = Batch.from_data_list(sel).to(DEVICE)
            emb = model.encode(b)                       # [len(ub), emb] (with grad)
            rows, emb_idx = [], []
            for bi, (c, _j) in enumerate(ub):
                for r in rbc[c]:
                    rows.append(r); emb_idx.append(bi)
            if not rows:
                continue
            er = emb[torch.tensor(emb_idx, device=DEVICE)]
            cr = ctx_t[rows].to(DEVICE)
            logit = model.classify(er, cr)
            loss = loss_fn(logit, y_t[rows].to(DEVICE))
            opt.zero_grad(); loss.backward(); opt.step()

        # early stopping uses a single isomer per complex (fast); TTA is applied at final predict
        auc = _auc(model, uniq_graphs, iv_rows, row_local, ctx, y, args.enc_batch, tta=False)
        if auc > best_auc + 1e-4:
            best_auc, bad = auc, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= args.patience:
                break
    if best_state:
        model.load_state_dict(best_state)
    return model


_SHARED = {}  # read-only big data shared with fork workers (set before the pool is created)


def _ckpt_path(ckdir, k, seed):
    return Path(ckdir) / f"fold{k}_seed{seed}.npz"


def _train_task(task):
    """One (fold, seed) training job. Saves its result to a checkpoint (crash-safe) and returns."""
    k, itr, iiv, va, seed = task
    S = _SHARED
    if S["args"].torch_threads > 0:
        torch.set_num_threads(S["args"].torch_threads)
    set_seed(seed)
    ctx = S["ctx_raw"].copy()
    sc = StandardScaler().fit(S["ctx_raw"][itr][:, S["cont_idx"]])
    ctx[:, S["cont_idx"]] = sc.transform(S["ctx_raw"][:, S["cont_idx"]])
    t0 = time.time()
    model = train_one(S["uniq_graphs"], itr, iiv, S["row_local"], ctx, S["y"], S["ctx_dim"], S["args"])
    # encode once, classify from the same embedding, and persist the embedding for LightGBM stacking
    # (out-of-fold: this val embedding comes from a model that never trained on it).
    er, cr = _encode_rows(model, S["uniq_graphs"], va, S["row_local"], ctx, S["args"].enc_batch, tta=True)
    with torch.no_grad():
        p = torch.sigmoid(model.classify(er.to(DEVICE), cr.to(DEVICE))).cpu().numpy()
    emb = er.cpu().numpy().astype(np.float32)
    # atomic checkpoint write: tmp then rename, so a kill mid-write can't corrupt it.
    # tmp must end in .npz (np.savez appends .npz otherwise, breaking the rename).
    dst = _ckpt_path(S["ckdir"], k, seed)
    tmp = dst.with_name(dst.stem + ".tmp.npz")
    np.savez(tmp, va=va, prob=p, emb=emb)
    tmp.replace(dst)
    print(f"    · fold {k} seed {seed} done ({time.time()-t0:.0f}s)", flush=True)
    return k, seed


def _run_jobs(pending, ckdir, workers):
    """Run (fold, seed) jobs resiliently. A plain Pool.map hangs forever if a worker is killed
    (OOM); instead use a ProcessPoolExecutor and, if the pool breaks, re-scan checkpoints (finished
    jobs are already saved) and retry the survivors. Stragglers that keep killing their worker are
    finally run serially so a run can never hang. Checkpoint-based resume makes every retry cheap."""
    if not pending:
        return
    remaining = list(pending)
    if workers > 1:
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor, as_completed
        from concurrent.futures.process import BrokenProcessPool
        ctx = mp.get_context("fork")
        for attempt in range(1, 6):
            remaining = [t for t in remaining if not _ckpt_path(ckdir, t[0], t[4]).exists()]
            if not remaining:
                return
            if attempt > 1:
                print(f"  [retry {attempt}] {len(remaining)} job(s) left after a worker died",
                      flush=True)
            try:
                with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as ex:
                    futs = [ex.submit(_train_task, t) for t in remaining]
                    for f in as_completed(futs):
                        f.result()  # raises BrokenProcessPool if a worker was killed
                return
            except BrokenProcessPool:
                continue  # survivors are checkpointed; loop re-scans and retries the rest
    # serial fallback (also the workers==1 path): no pool to hang
    for t in [t for t in remaining if not _ckpt_path(ckdir, t[0], t[4]).exists()]:
        _train_task(t)


def run_cv(uniq_graphs, row_local, usable, ctx_raw, cont_idx, y, groups, manifest, ctx_dim, args, tag):
    oof_prob = np.full(len(y), np.nan); oof_fold = np.full(len(y), -1)
    usable_set = set(usable.tolist())
    gss = GroupShuffleSplit(1, test_size=args.inner_val_frac, random_state=args.seed)
    ckdir = CKPTDIR / f"dimenet_{tag}"
    ckdir.mkdir(parents=True, exist_ok=True)
    check_signature(ckdir, signature(args, manifest), fresh=args.fresh)

    # precompute each fold's (inner-train, inner-val, val) and build the (fold, seed) task list
    fold_va, tasks = {}, []
    for k, tr, va in iter_folds(manifest, only=args.folds):
        tr = np.array([i for i in tr if i in usable_set])
        va = np.array([i for i in va if i in usable_set])
        if len(tr) == 0 or len(va) == 0:
            continue
        itr_rel, iiv_rel = next(gss.split(tr, y[tr], groups[tr]))
        itr, iiv = tr[itr_rel], tr[iiv_rel]
        fold_va[k] = (va, len(itr))
        for s in range(args.n_seeds):
            tasks.append((k, itr, iiv, va, args.seed + k * 1000 + s))

    # resume: skip (fold, seed) jobs whose checkpoint already exists (unless --fresh)
    pending = [t for t in tasks
               if args.fresh or not _ckpt_path(ckdir, t[0], t[4]).exists()]
    if args.fresh:  # actually discard old checkpoints so they are recomputed (and _run_jobs won't skip them)
        for t in pending:
            _ckpt_path(ckdir, t[0], t[4]).unlink(missing_ok=True)
    done = len(tasks) - len(pending)
    print(f"  [{len(tasks)} jobs total; {done} already checkpointed, {len(pending)} to run "
          f"-> {ckdir}]", flush=True)

    _SHARED.update(uniq_graphs=uniq_graphs, row_local=row_local, ctx_raw=ctx_raw,
                   cont_idx=cont_idx, y=y, ctx_dim=ctx_dim, args=args, ckdir=str(ckdir))
    t0 = time.time()
    _run_jobs(pending, ckdir, args.workers)
    print(f"  [{len(pending)} jobs run in {time.time()-t0:.0f}s on {args.workers} worker(s)]",
          flush=True)

    # collect per fold from checkpoints (old + new), ensemble over seeds
    by_fold = {}; by_fold_emb = {}; have_emb = True
    for k, itr, iiv, va, seed in tasks:
        d = np.load(_ckpt_path(ckdir, k, seed))
        by_fold.setdefault(k, []).append(d["prob"])
        if "emb" in d.files:
            by_fold_emb.setdefault(k, []).append(d["emb"])
        else:
            have_emb = False  # old checkpoint without embeddings -> skip emitting them
    oof_emb = None
    if have_emb and by_fold_emb:
        emb_dim = next(iter(by_fold_emb.values()))[0].shape[1]
        oof_emb = np.full((len(y), emb_dim), np.nan, dtype=np.float32)
    rows_meta = []
    for k in sorted(by_fold):
        va, n_train = fold_va[k]
        seed_probs = by_fold[k]
        seed_aucs = [roc_auc_score(y[va], p) for p in seed_probs]
        prob = np.mean(seed_probs, axis=0)
        pred = (prob >= 0.5).astype(int)
        oof_prob[va], oof_fold[va] = prob, k
        if oof_emb is not None:
            oof_emb[va] = np.mean(by_fold_emb[k], axis=0)  # seed-ensembled, out-of-fold embedding
        rows_meta.append(dict(fold=k, n_train=n_train, n_val=len(va),
                              roc_auc=roc_auc_score(y[va], prob),
                              seed_auc_mean=round(float(np.mean(seed_aucs)), 4),
                              seed_auc_std=round(float(np.std(seed_aucs, ddof=1))
                                                 if args.n_seeds > 1 else 0.0, 4),
                              pr_auc=average_precision_score(y[va], prob),
                              accuracy=accuracy_score(y[va], pred),
                              balanced_accuracy=balanced_accuracy_score(y[va], pred),
                              f1=f1_score(y[va], pred, zero_division=0)))
        sstr = (f" | per-seed {rows_meta[-1]['seed_auc_mean']:.3f}"
                f"±{rows_meta[-1]['seed_auc_std']:.3f}" if args.n_seeds > 1 else "")
        print(f"  fold {k}: ROC-AUC={rows_meta[-1]['roc_auc']:.3f} "
              f"acc={rows_meta[-1]['accuracy']:.3f}{sstr}", flush=True)
    return pd.DataFrame(rows_meta), oof_prob, oof_fold, oof_emb


def aggregate(dfm):
    return {c: {"mean": round(float(dfm[c].mean()), 4), "std": round(float(dfm[c].std(ddof=1)), 4)}
            for c in ["roc_auc", "pr_auc", "accuracy", "balanced_accuracy", "f1"]}


def save_figures(y, oof_prob, oof_fold, tag):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    mask = oof_fold >= 0; yv, pv = y[mask], oof_prob[mask]
    FIGDIR.mkdir(parents=True, exist_ok=True)
    fpr, tpr, _ = roc_curve(yv, pv)
    plt.figure(figsize=(5, 5)); plt.plot(fpr, tpr, label=f"OOF (AUC={roc_auc_score(yv, pv):.3f})")
    plt.plot([0, 1], [0, 1], "--", color="grey"); plt.legend(loc="lower right")
    plt.xlabel("FPR"); plt.ylabel("TPR"); plt.title(f"DimeNet++ {tag} — ROC")
    plt.tight_layout(); plt.savefig(FIGDIR / f"dimenet_{tag}_roc.png", dpi=140); plt.close()
    cm = confusion_matrix(yv, (pv >= 0.5).astype(int))
    plt.figure(figsize=(4, 4)); plt.imshow(cm, cmap="Blues")
    for (i, j), v in np.ndenumerate(cm):
        plt.text(j, i, str(v), ha="center", va="center",
                 color="white" if v > cm.max() / 2 else "black")
    plt.xticks([0, 1], ["nontox", "tox"]); plt.yticks([0, 1], ["nontox", "tox"])
    plt.title(f"DimeNet++ {tag} — confusion")
    plt.tight_layout(); plt.savefig(FIGDIR / f"dimenet_{tag}_confusion.png", dpi=140); plt.close()


def load_graphs(struct_map: pd.DataFrame, feats: pd.DataFrame, allow_unassessed=False,
                isomers_dir=None, max_isomers=8):
    """Build per-complex graph LISTS. uniq_graphs[c] = [isomer Data, ...] (length 1 in the
    single-structure mode). Returns (uniq_graphs, row_local[int array], usable rows, n_isomers_total).

    If isomers_dir is set, all `<isomers_dir>/<bmdb_name>/*.xyz` (capped at max_isomers) are loaded
    for each complex; otherwise the single quality_ok structure from the map is used.
    """
    quality = dict(zip(struct_map.complex_id, struct_map.get("quality_ok", pd.Series(dtype=object))))
    xyzpath = dict(zip(struct_map.complex_id, struct_map.get("xyz_path", pd.Series(dtype=object))))
    name = dict(zip(struct_map.complex_id, struct_map.get("bmdb_name", pd.Series(dtype=object))))
    cid_to_local, uniq_graphs = {}, []
    row_local = np.full(len(feats), -1, dtype=int)
    usable, n_iso = [], 0
    n_from_folder, n_fallback = 0, 0  # corrected isomer folders vs old single-structure fallback
    for i, cid in enumerate(feats.complex_id):
        q = quality.get(cid, None)
        is_true = q is True or q == "True" or q == 1
        is_na = q is None or (isinstance(q, float) and pd.isna(q)) or q == "" or (q is pd.NA)
        if not (is_true or (is_na and allow_unassessed)):
            continue
        if cid not in cid_to_local:
            graphs, from_folder = [], False
            if isomers_dir is not None:
                folder = Path(isomers_dir) / str(name.get(cid, ""))
                if folder.is_dir():
                    files = sorted(folder.glob("*.xyz"))[:max_isomers]
                    graphs = [read_xyz(str(f)) for f in files]
                    from_folder = bool(graphs)
            if not graphs:  # fall back to the single lowest-energy structure
                path = xyzpath.get(cid)
                if not path or not Path(path).exists():
                    continue
                graphs = [read_xyz(path)]
            cid_to_local[cid] = len(uniq_graphs)
            uniq_graphs.append(graphs)
            n_iso += len(graphs)
            n_from_folder += int(from_folder)
            n_fallback += int(not from_folder)
        row_local[i] = cid_to_local[cid]
        usable.append(i)
    if isomers_dir is not None:
        print(f"[isomers] {n_from_folder} complexes from isomer folders, "
              f"{n_fallback} fell back to the single structure (xyz_path)", flush=True)
    return uniq_graphs, row_local, np.array(usable, dtype=int), n_iso


def _selftest(args):
    print("[selftest] 40 synthetic complexes, 120 rows (encode-once path)")
    rng = np.random.default_rng(0)
    n_comp, n_rows = 40, 120
    uniq = []
    for _ in range(n_comp):
        isos = []  # 1-3 synthetic isomers per complex
        for _k in range(rng.integers(1, 4)):
            na = rng.integers(5, 12)
            isos.append(Data(z=torch.tensor([44] + list(rng.choice([6, 7, 8], na - 1)),
                                            dtype=torch.long),
                             pos=torch.tensor(rng.standard_normal((na, 3)) * 1.6,
                                              dtype=torch.float32)))
        uniq.append(isos)
    row_local = rng.integers(0, n_comp, n_rows)
    ctx = rng.standard_normal((n_rows, 6)).astype(np.float32)
    y = rng.integers(0, 2, n_rows)
    args.epochs, args.patience, args.emb_dim, args.comp_batch, args.enc_batch = 2, 5, 16, 16, 32
    args.n_seeds = 2
    args.head_hidden, args.dropout, args.lr, args.weight_decay = [32], 0.2, 5e-4, 1e-5
    args.aug_mode = "full"
    args.dime = dict(DIME_DEFAULT)
    tr, iv, va = np.arange(0, 80), np.arange(80, 100), np.arange(100, 120)
    m = train_one(uniq, tr, iv, row_local, ctx, y, 6, args)
    p = _predict(m, uniq, va, row_local, ctx, args.enc_batch)
    print(f"[selftest] OK — {len(p)} val probs, mean={p.mean():.3f}, encode-once train+eval ran.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scheme", choices=["doi", "smiles"], default="doi")
    ap.add_argument("--mode", choices=["context", "mol_only"], default="context")
    ap.add_argument("--cell-line", default=None,
                    help="restrict to a single cell line (e.g. A549); drops the constant "
                         "cell-line one-hot from the context vector")
    ap.add_argument("--with-ecfp", action="store_true",
                    help="append the 2048-bit ECFP fingerprint to the context vector (raw bits, "
                         "not StandardScaled). Tests whether the paper's fingerprint adds to the "
                         "geometry model; tag gets '_ecfp'.")
    ap.add_argument("--no-rdkit", action="store_true",
                    help="drop the 2D RDKit descriptors (logp/tpsa/mw) from the context vector to "
                         "isolate the geometric embedding from 2D ligand descriptors. Charge, "
                         "exposure and cell-line stay (task context, not ligand descriptors); "
                         "tag gets '_nordkit'.")
    ap.add_argument("--manifest", type=Path, default=None)
    ap.add_argument("--features", type=Path, default=None, help="features parquet (multi-metal)")
    ap.add_argument("--report", type=Path, default=None, help="features report json (multi-metal)")
    ap.add_argument("--dataset", type=Path, default=DATASET, help="curated parquet (for groups)")
    ap.add_argument("--struct-map", type=Path, default=STRUCT_MAP, help="structure map csv")
    ap.add_argument("--folds", type=int, nargs="+", default=None)
    ap.add_argument("--emb-dim", type=int, default=64)
    ap.add_argument("--head-hidden", type=int, nargs="+", default=[128])
    ap.add_argument("--dropout", type=float, default=0.2)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--weight-decay", type=float, default=1e-5)
    ap.add_argument("--comp-batch", type=int, default=64, help="unique complexes encoded per step")
    ap.add_argument("--enc-batch", type=int, default=128, help="complexes per encode batch at eval")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--patience", type=int, default=6)
    ap.add_argument("--inner-val-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-seeds", type=int, default=1,
                    help="deep-ensemble size: models per fold, probs averaged. >1 also reports the "
                         "per-seed spread (the extrapolation/seed uncertainty). Cost scales linearly.")
    ap.add_argument("--tag-suffix", default="",
                    help="extra label appended to output filenames + checkpoint dir, so runs that "
                         "differ only in a detail (e.g. corrected vs old structures) don't collide")
    ap.add_argument("--fresh", action="store_true",
                    help="ignore existing per-job checkpoints and retrain all (fold,seed) jobs. "
                         "Default resumes: an interrupted run continues where it stopped.")
    ap.add_argument("--workers", type=int, default=1,
                    help="parallel (fold×seed) training processes (Linux fork; graphs shared via "
                         "copy-on-write). e.g. on a 45-thread box: --workers 10 --torch-threads 4.")
    ap.add_argument("--torch-threads", type=int, default=0,
                    help="torch intra-op threads PER worker (0=leave default). Set with --workers to "
                         "avoid oversubscription: workers × torch-threads ≲ physical threads.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--allow-unassessed", action="store_true")
    ap.add_argument("--overwrite", action="store_true",
                    help="allow overwriting existing result files of the same tag")
    ap.add_argument("--isomers-dir", type=Path, default=None,
                    help="data augmentation: dir with per-complex isomer subfolders "
                         "<isomers-dir>/<bmdb_name>/*.xyz (e.g. ../mecobi_build/isomers). Samples one "
                         "isomer per complex each epoch; averages embeddings over isomers at eval.")
    ap.add_argument("--max-isomers", type=int, default=8, help="cap isomers per complex")
    ap.add_argument("--aug-mode", choices=["stochastic", "full"], default="stochastic",
                    help="stochastic: 1 random isomer per complex per epoch. full: every isomer is a "
                         "separate training instance with the same label each epoch (cost x avg isomers).")
    ap.add_argument("--hidden-channels", type=int, default=DIME_DEFAULT["hidden_channels"])
    ap.add_argument("--num-blocks", type=int, default=DIME_DEFAULT["num_blocks"])
    ap.add_argument("--cutoff", type=float, default=DIME_DEFAULT["cutoff"])
    ap.add_argument("--num-spherical", type=int, default=DIME_DEFAULT["num_spherical"])
    ap.add_argument("--num-radial", type=int, default=DIME_DEFAULT["num_radial"])
    ap.add_argument("--max-neighbors", type=int, default=DIME_DEFAULT["max_num_neighbors"])
    args = ap.parse_args()

    args.dime = dict(DIME_DEFAULT, hidden_channels=args.hidden_channels, num_blocks=args.num_blocks,
                     cutoff=args.cutoff, num_spherical=args.num_spherical,
                     num_radial=args.num_radial, max_num_neighbors=args.max_neighbors)
    # protect against thread oversubscription: if parallel but no per-worker cap set, auto-divide
    if args.workers > 1 and args.torch_threads == 0:
        import os
        args.torch_threads = max(1, (os.cpu_count() or 8) // args.workers)
        print(f"[parallel] auto torch-threads={args.torch_threads} per worker "
              f"({args.workers} workers)", flush=True)
    if args.selftest:
        return _selftest(args)

    manifest = args.manifest or SPLITS / f"ru_{args.scheme}_10fold.json"
    for pth, name in [(manifest, "manifest"), (args.struct_map, "structure map"),
                      (args.dataset, "dataset")]:
        if not Path(pth).exists():
            raise SystemExit(f"{name} not found: {pth}")

    guard_run(args, default_dataset=DATASET, default_struct_map=STRUCT_MAP,
              default_manifest=SPLITS / f"ru_{args.scheme}_10fold.json")
    feats, meta = load_features(args.features, args.report) if args.features else load_features()
    ds = pd.read_parquet(args.dataset)
    assert feats["row_id"].tolist() == ds["row_id"].tolist(), "feature/dataset row mismatch"
    smap = pd.read_csv(args.struct_map)

    fg = meta["feature_groups"]
    single_cell = args.cell_line is not None
    # --no-rdkit drops the 2D RDKit descriptors (logp/tpsa/mw) so the geometric embedding is not
    # riding alongside 2D ligand descriptors; charge/exposure/cell-line stay (task context, needed
    # to predict IC50 at all, not ligand descriptors).
    desc_cols = [] if args.no_rdkit else fg["descriptors"]
    if args.mode == "context":
        # a single cell line makes the one-hot constant -> drop it, keep exposure + scalars
        cell_cols = [] if single_cell else fg["cell_line"]
        ctx_cols = desc_cols + fg["charge"] + fg["exposure_time"] + cell_cols
        cont_cols = desc_cols + fg["charge"] + fg["exposure_time"]
    else:
        ctx_cols = desc_cols + fg["charge"]
        cont_cols = desc_cols + fg["charge"]
    if args.with_ecfp:
        ctx_cols = ctx_cols + fg["ecfp"]   # raw fingerprint bits (not StandardScaled -> not in cont)
    ctx_raw = feats[ctx_cols].to_numpy(np.float32)
    cont_idx = [ctx_cols.index(c) for c in cont_cols]
    y = feats["y"].to_numpy().astype(int)
    group_col = json.loads(manifest.read_text(encoding="utf-8"))["group_col"]
    groups = ds[group_col].to_numpy()

    print(f"[DimeNet++] device={DEVICE} mode={args.mode} scheme={args.scheme} "
          f"dime={args.dime['cutoff']}A/s{args.dime['num_spherical']}/r{args.dime['num_radial']}/"
          f"h{args.dime['hidden_channels']}", flush=True)
    t_load = time.time()
    uniq_graphs, row_local, usable, n_iso = load_graphs(
        smap, feats, allow_unassessed=args.allow_unassessed,
        isomers_dir=args.isomers_dir, max_isomers=args.max_isomers)
    if single_cell:
        lines = set(ds["Cell_line"].unique())
        if args.cell_line not in lines:
            raise SystemExit(f"cell line '{args.cell_line}' not in dataset. Options include: "
                             f"{sorted(lines)[:8]} ...")
        cell_rows = set(np.where(ds["Cell_line"].to_numpy() == args.cell_line)[0].tolist())
        usable = np.array([r for r in usable if r in cell_rows], dtype=int)
    if len(usable) == 0:
        qcol = smap["quality_ok"] if "quality_ok" in smap else None
        diag = (f"quality_ok column present={qcol is not None}; "
                f"value_counts={dict(qcol.value_counts(dropna=False)) if qcol is not None else 'n/a'}; "
                f"xyz_exists true={int(smap['xyz_exists'].fillna(False).sum()) if 'xyz_exists' in smap else 'n/a'}")
        raise SystemExit(
            "No usable structures found in ru_structure_map.csv.\n  " + diag +
            "\nRegenerate it on the isomer-build machine, e.g.:\n"
            "  python src/structure_mapping.py --structures ../mecobi_build_isomers/structures "
            "--assessment ../biometaldb_assessment.csv --min-contact-ratio 0.6\n"
            "(or pass --allow-unassessed to use xyz-present structures without quality metadata).")
    n_uniq = len({int(v) for v in row_local[usable]})
    aug = args.isomers_dir is not None
    print(f"[data] {len(usable)}/{len(feats)} rows usable"
          f"{f' (cell_line={args.cell_line})' if single_cell else ''}, "
          f"{n_uniq} unique complexes"
          f"{f', {n_iso} isomers total (avg {n_iso/max(1,n_uniq):.1f}/complex)' if aug else ' (1 struct each)'}, "
          f"ctx_dim={len(ctx_cols)} (loaded in {time.time()-t_load:.0f}s)", flush=True)

    tag = f"{args.scheme}_{args.mode}" + (f"_{args.cell_line}" if single_cell else "") \
        + ("_aug" if aug else "") + ("_ecfp" if args.with_ecfp else "") \
        + ("_nordkit" if args.no_rdkit else "") \
        + (f"_{args.tag_suffix}" if args.tag_suffix else "")
    t0 = time.time()
    dfm, oof_prob, oof_fold, oof_emb = run_cv(uniq_graphs, row_local, usable, ctx_raw, cont_idx, y,
                                              groups, manifest, len(ctx_cols), args, tag)
    agg = aggregate(dfm)
    report = {
        "model": "DimeNet++", "mode": args.mode, "scheme": args.scheme,
        "generated_utc": datetime.now(timezone.utc).isoformat(), "device": str(DEVICE),
        "dime_config": args.dime, "training": "encode-once-per-complex",
        "config": {k: getattr(args, k) for k in
                   ["emb_dim", "head_hidden", "dropout", "lr", "comp_batch", "epochs",
                    "patience", "inner_val_frac", "seed", "n_seeds", "folds"]},
        "seed_uncertainty_mean_std": (round(float(dfm["seed_auc_std"].mean()), 4)
                                      if args.n_seeds > 1 else None),
        "n_usable_rows": int(len(usable)), "n_unique_complexes": len(uniq_graphs),
        "n_isomers_total": int(n_iso), "augmentation": aug,
        "isomers_dir": str(args.isomers_dir) if aug else None, "max_isomers": args.max_isomers,
        "n_total_rows": int(len(feats)),
        "per_fold": dfm.to_dict("records"), "aggregate": agg,
        "reference": {"lightgbm_doi": "0.810 +- 0.041", "mlp_doi": "0.776 +- 0.040"},
        "total_seconds": round(time.time() - t0, 1),
    }
    REPORTDIR.mkdir(parents=True, exist_ok=True); TABLEDIR.mkdir(parents=True, exist_ok=True)
    (REPORTDIR / f"dimenet_{tag}_metrics.json").write_text(json.dumps(report, indent=2),
                                                           encoding="utf-8")
    used = oof_fold >= 0
    pd.DataFrame({"row_id": feats["row_id"][used], "complex_id": feats["complex_id"][used],
                  "y": y[used], "prob": oof_prob[used], "fold": oof_fold[used]}).to_csv(
        TABLEDIR / f"dimenet_{tag}_oof.csv", index=False)
    if oof_emb is not None:
        embdf = pd.DataFrame(oof_emb[used], columns=[f"emb_{i}" for i in range(oof_emb.shape[1])])
        embdf.insert(0, "complex_id", feats["complex_id"][used].to_numpy())
        embdf.insert(0, "row_id", feats["row_id"][used].to_numpy())
        embdf.to_csv(TABLEDIR / f"dimenet_{tag}_embeddings.csv", index=False)
        print(f"[written] out-of-fold embeddings -> {TABLEDIR / f'dimenet_{tag}_embeddings.csv'}")
    save_figures(y, oof_prob, oof_fold, tag)

    print(f"\n=== DimeNet++ {tag} — {len(dfm)} folds, {int(used.sum())} rows scored ===")
    print(f"ROC-AUC  {agg['roc_auc']['mean']:.3f} +- {agg['roc_auc']['std']:.3f}")
    print(f"Accuracy {agg['accuracy']['mean']:.3f} +- {agg['accuracy']['std']:.3f}")
    print(f"PR-AUC {agg['pr_auc']['mean']:.3f}  F1 {agg['f1']['mean']:.3f}  "
          f"bal-acc {agg['balanced_accuracy']['mean']:.3f}")
    print("reference: LightGBM 0.810 / MLP 0.776 (DOI) — compare on the SAME rows via the OOF csvs")
    print(f"total: {report['total_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
