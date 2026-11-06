"""Extract GROUND-TRUTH donor atom indices for every benchmark complex from the CSD
`ComplexSmiles` (the metal is bonded explicitly to its donor atoms there -- the bundle's
CoordinationNumber was derived by counting exactly those bonds). Maps each donor onto the
bundle's charge-corrected free-ligand SMILES via an element-only canonical-skeleton match
(isomorphism-invariant, so the coordinated<->free charge/bond-order/aromaticity differences
don't matter). Writes `benchmark_donors.json` = {refcode: [[donor idx...] per ligand]}.

Purpose: feed these as `Ligand.donor_override` so the benchmark tests MeCoBi's STRUCTURE
BUILDER with donors known -- isolating assembly fidelity from pydentate's donor prediction,
and matching Architector's input regime (it takes coordinating atoms as input too).

    python experiments/benchmark/extract_donors.py
    # -> benchmark_donors.json  (+ coverage report)

Only maps verified by (sum of per-ligand donor counts == crystal CN) are written; the rest
fall back to pydentate at build time.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
from collections import defaultdict
from pathlib import Path

from rdkit import Chem
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")
BENCH = Path(__file__).resolve().parents[1]   # benchmark root: frozen bundle in, donors out

_DEFAULT_READY = None  # no built-in default: pass --ready or set MECOBI_READY_CSV
# metals/metalloids that appear as the coordination centre in the benchmark
METALS = set(
    "Sc Ti V Cr Mn Fe Co Ni Cu Zn Y Zr Nb Mo Tc Ru Rh Pd Ag Cd Hf Ta W Re Os Ir "
    "Pt Au Hg Al Ga In Tl Ge Sn Pb Sb Bi Be Mg Ca Sr Ba Na K Li".split()
)


def _skel(mol):
    """element-only, single-bond skeleton + canonical atom ranks. Isomorphism-
    invariant: two graphs are isomorphic iff their canonical skeleton SMILES match,
    and atoms of equal canonical rank correspond."""
    rw = Chem.RWMol()
    for a in mol.GetAtoms():
        rw.AddAtom(Chem.Atom(a.GetAtomicNum()))
    for b in mol.GetBonds():
        rw.AddBond(b.GetBeginAtomIdx(), b.GetEndAtomIdx(), Chem.BondType.SINGLE)
    sk = rw.GetMol()
    for a in sk.GetAtoms():
        a.SetNoImplicit(True)
    Chem.GetSymmSSSR(sk)
    ranks = list(Chem.CanonicalRankAtoms(sk, breakTies=True, includeChirality=False))
    return Chem.MolToSmiles(sk, canonical=True), ranks


def _ligand_skels(ligands):
    out = []
    for L in ligands:
        m = Chem.MolFromSmiles(L)
        out.append(None if m is None else _skel(m))
    return out


def donor_map(csmiles, ligands, lig_skels):
    """[[donor atom idx per ligand]] aligned to `ligands`, or None if unmapped.
    Donor indices are 0-based heavy-atom indices into each ligand's own SMILES
    (exactly what Ligand.donor_override expects)."""
    m = Chem.MolFromSmiles(csmiles, sanitize=False)
    if m is None:
        return None
    try:
        m.UpdatePropertyCache(strict=False)
    except Exception:
        pass
    mi = [a.GetIdx() for a in m.GetAtoms() if a.GetSymbol() in METALS]
    if len(mi) != 1:
        return None
    mi = mi[0]
    donors = {n.GetIdx() for n in m.GetAtomWithIdx(mi).GetNeighbors()}
    em = Chem.RWMol(m)
    for d in list(donors):
        em.RemoveBond(mi, d)
    em.RemoveAtom(mi)
    fm = em.GetMol()
    sh = lambda d: d if d < mi else d - 1  # noqa: E731
    donors_sh = {sh(d) for d in donors}
    try:
        fm.UpdatePropertyCache(strict=False)
    except Exception:
        pass
    result = [[] for _ in ligands]
    used = [False] * len(ligands)
    for fr in Chem.GetMolFrags(fm, asMols=False, sanitizeFrags=False):
        sub = Chem.RWMol()
        amap = {}
        for old in fr:
            amap[old] = sub.AddAtom(Chem.Atom(fm.GetAtomWithIdx(old).GetAtomicNum()))
        for b in fm.GetBonds():
            if b.GetBeginAtomIdx() in amap and b.GetEndAtomIdx() in amap:
                sub.AddBond(amap[b.GetBeginAtomIdx()], amap[b.GetEndAtomIdx()],
                            Chem.BondType.SINGLE)
        try:
            fcanon, franks = _skel(sub.GetMol())
        except Exception:
            continue
        dloc = [amap[d] for d in fr if d in donors_sh]  # submol-local donor idx
        for j, ls in enumerate(lig_skels):
            if used[j] or ls is None or ls[0] != fcanon:
                continue
            rank_to_idx = {ls[1][i]: i for i in range(len(ls[1]))}
            result[j] = sorted(rank_to_idx[franks[dl]] for dl in dloc
                               if franks[dl] in rank_to_idx)
            used[j] = True
            break
    return result if all(used) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ready", default=None, help="mecobi_ready_all.csv (env MECOBI_READY_CSV)")
    ap.add_argument("--bundle", default="benchmark_bundle.json.gz")
    ap.add_argument("--out", default="benchmark_donors.json")
    cfg = ap.parse_args()

    ready = cfg.ready or os.environ.get("MECOBI_READY_CSV") or _DEFAULT_READY
    if not ready:
        raise SystemExit("Pass --ready PATH or set MECOBI_READY_CSV (mecobi_ready_all.csv).")
    bundle = json.loads(gzip.open(BENCH / cfg.bundle, "rt").read())
    with open(ready, encoding="utf-8", errors="replace") as f:
        cs = {row["Name"].strip(): row["ComplexSmiles"]
              for row in csv.DictReader(f) if row.get("charge_ok") == "Y"}

    donors = {}
    by_cn = defaultdict(lambda: [0, 0])  # cn -> [mapped, total]
    no_csmiles = unmapped = 0
    for r in bundle:
        cn = r.get("cn")
        if cn is None or cn > 9:
            continue
        by_cn[cn][1] += 1
        rc = r["refcode"]
        if rc not in cs:
            no_csmiles += 1
            continue
        dmap = donor_map(cs[rc], r["ligands"], _ligand_skels(r["ligands"]))
        # quality gate: donor count must equal the crystal CN
        if dmap is not None and sum(len(x) for x in dmap) == cn:
            donors[rc] = dmap
            by_cn[cn][0] += 1
        else:
            unmapped += 1

    (BENCH / cfg.out).write_text(json.dumps(donors), encoding="utf-8")
    tot_m = sum(v[0] for v in by_cn.values())
    tot_t = sum(v[1] for v in by_cn.values())
    print(f"donor maps written: {tot_m}/{tot_t} CN2-9 complexes = {100*tot_m/tot_t:.1f}%")
    print(f"  (no ComplexSmiles: {no_csmiles}, unmapped/failed gate: {unmapped})")
    print(f"{'CN':>3}{'mapped':>8}{'total':>7}{'cov%':>7}")
    for cn in sorted(by_cn):
        m, t = by_cn[cn]
        print(f"{cn:>3}{m:>8}{t:>7}{100*m/t:>6.0f}%")
    print(f"-> {BENCH / cfg.out}")


if __name__ == "__main__":
    main()
