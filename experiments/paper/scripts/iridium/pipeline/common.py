"""Shared helpers for the IrCpSB rerun benchmark (SA activity, corrected labels)."""
import os
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

# --- LOCKED CONVENTIONS (confirmed with user 2026-08-06) ---
# SA value = relative bacterial growth (OD/control): LOW = active.
# Active "hit" (positive class = 1) when value < ACTIVE_CUTOFF.
# Same raw scale across gen0 and gen1/2 (no rescaling).
ACTIVE_CUTOFF = 0.20        # value < 0.20 => active (positive)
CONV_MIN = 40.0             # keep compounds with Conversion >= 40%
COUNTERION = "Cl"           # 3rd fingerprint component used in gen0 training

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def canon(s):
    if not isinstance(s, str) or not s.strip():
        return None
    m = Chem.MolFromSmiles(s.strip())
    return Chem.MolToSmiles(m) if m else None


# imine condensation: aldehyde R-CHO + primary amine R'-NH2 -> R-CH=N-R' (+ H2O)
# Targets the aldehyde carbon only ([CX3H1]=O), never esters/ketones.
# Validated: reproduces gen0 training Schiff 1440/1440 and gen2 242/264
# (the 264 mismatches are cases where the reference condensed onto an ester).
_RXN = AllChem.ReactionFromSmarts("[CX3H1:1]=[OX1:2].[NX3H2:3]>>[C:1]=[N:3]")


_ALD_SMARTS = Chem.MolFromSmarts("[CX3H1]=[OX1]")            # aldehyde
_NH2_SMARTS = Chem.MolFromSmarts("[NX3;H2;!$(NC=O)]")        # primary amine (not amide)
_CP_SMARTS = Chem.MolFromSmarts("C1(~C~C~C~C1)")             # cyclopentadiene 5-ring (Cp)


def assign_roles(parts):
    """Assign (Cp, aldehyde, amine) canonical SMILES to the 3 building blocks by
    functional group, independent of column labels / order. Returns (cp, ald, am);
    any unresolved role is None. Validated 360/360 on the Aug26 gen1/2 file."""
    cans = [c for c in (canon(p) for p in parts) if c]
    cp = ald = am = None
    for c in cans:
        m = Chem.MolFromSmiles(c)
        if m is None:
            continue
        if m.HasSubstructMatch(_CP_SMARTS) and cp is None:
            cp = c
        elif m.HasSubstructMatch(_ALD_SMARTS) and ald is None:
            ald = c
        elif m.HasSubstructMatch(_NH2_SMARTS) and am is None:
            am = c
    return cp, ald, am


def make_schiff(aldehyde, amine):
    """Return canonical Schiff-base SMILES from aldehyde + primary amine, or None."""
    a = Chem.MolFromSmiles(str(aldehyde)) if aldehyde is not None else None
    b = Chem.MolFromSmiles(str(amine)) if amine is not None else None
    if a is None or b is None:
        return None
    outs = set()
    for prod in _RXN.RunReactants((a, b)):
        m = prod[0]
        try:
            Chem.SanitizeMol(m)
            outs.add(Chem.MolToSmiles(m))
        except Exception:
            pass
    if not outs:
        return None
    # deterministic pick: shortest then lexicographic (single product in practice)
    return sorted(outs, key=lambda s: (len(s), s))[0]


def active_label(value):
    """1 = active (value < cutoff), 0 = inactive, NaN if value missing."""
    v = pd.to_numeric(value, errors="coerce")
    if pd.isna(v):
        return np.nan
    return int(v < ACTIVE_CUTOFF)


def fp_smiles(cp_can, schiff_can, counterion=COUNTERION):
    """Assemble the fingerprint SMILES exactly as gen0 training did: Cp . Schiff . Cl."""
    parts = [p for p in [cp_can, schiff_can, counterion] if p]
    return ".".join(parts)


# ---------------- fingerprints & metrics ----------------
import numpy as _np
from rdkit.Chem import rdFingerprintGenerator as _rfg
from rdkit import DataStructs as _DS

_MORGAN = _rfg.GetMorganGenerator(radius=2, fpSize=512)  # ECFP4, 512 bits (matches training)


def ecfp(smiles, n_bits=512):
    m = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
    arr = _np.zeros((n_bits,), dtype=_np.int8)
    if m is None:
        return arr
    _DS.ConvertToNumpyArray(_MORGAN.GetFingerprint(m), arr)
    return arr


def classification_metrics(y_true, y_pred, score):
    """Positive class = active (1). Returns dict incl Hit-Rate = TP/(TP+FP)."""
    from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
    y_true = _np.asarray(y_true).astype(int)
    y_pred = _np.asarray(y_pred).astype(int)
    score = _np.asarray(score, dtype=float)
    TP = int(((y_true == 1) & (y_pred == 1)).sum())
    TN = int(((y_true == 0) & (y_pred == 0)).sum())
    FP = int(((y_true == 0) & (y_pred == 1)).sum())
    FN = int(((y_true == 1) & (y_pred == 0)).sum())
    both = len(set(y_true.tolist())) == 2
    return dict(
        n=len(y_true), n_active=int((y_true == 1).sum()), n_inactive=int((y_true == 0).sum()),
        accuracy=round(accuracy_score(y_true, y_pred), 4),
        precision=round(precision_score(y_true, y_pred, pos_label=1, zero_division=0), 4),
        recall=round(recall_score(y_true, y_pred, pos_label=1, zero_division=0), 4),
        roc_auc=round(roc_auc_score(y_true, score), 4) if both else _np.nan,
        hit_rate=round(TP / (TP + FP), 4) if (TP + FP) > 0 else _np.nan,
        TP=TP, TN=TN, FP=FP, FN=FN,
    )
