"""Build the stratified MeCoBi benchmark INPUT bundle from the charge-corrected
`mecobi_ready` tables (the author's own CSD ligand-charge pipeline) instead of DART's
MetaLig.

Why: MetaLig's own per-refcode ligand linkage silently drops whole ligands for a
sizeable fraction of complexes (~34% get a lower CN than the truth; e.g. KUVNEX loses
its tridentate N,N,N ligand, EKOFIW loses its two imidazole-carboxylates). Confirmed by
querying the raw MetaLig DB directly: the missing ligands are simply not linked to the
refcode upstream. `mecobi_ready_<M>.csv` is built from the same source CSD complex SMILES
but keeps the full coordinated ligand set (only counter-ions/solvate dropped) with correct
donor charges, so it is the trustworthy input source.

- Source: mecobi_ready_all.csv, `charge_ok=Y` rows only (correct per-atom charges).
- Per complex: metal, ox=OS_Derived, ligands=LigandSmiles split on '.', cn=CoordinationNumber
  (= number of real metal-donor bonds in the source SMILES), plus provenance fields.
- Eligible = CN in 2-9 (MeCoBi range) + integer OS + has a CIF in the Generation-3 tree
  (so every complex is scorable later against its crystal sphere).
- MetaLig is used ONLY as an optional cross-check (--metalig-crosscheck): it reports per-
  refcode CN/OS agreement so we can quantify the disagreement, but never filters or
  overrides mecobi_ready.
- Stratified CAPPED allocation over (metal, CN, OS): min(cap, available) per cell, seeded
  shuffle within cell -> balanced across metal x CN x OS.

Emits benchmark_bundle_v2.json (+ .gz) with the SAME record schema the existing harness
consumes (run.py / extract_spheres.py use refcode, metal, ox, cn, ligands) plus provenance
(charges, donor_elements, os_confidence, complex_charge, metalig_cn, metalig_os).

    python dataprep/build_bundle_from_mecobi.py --cif-root <Generation3> --cap 100
"""
from __future__ import annotations

import argparse
import bz2
import csv
import gzip
import json
import os
import random
import sys
from collections import defaultdict

from rdkit import Chem
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")

# benchmark root (one up from dataprep/): the bundle is written next to the other frozen data
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# No built-in defaults: pass the flags or set MECOBI_READY_CSV / MECOBI_CIF_ROOT.
_DEFAULT_MECOBI_READY = None
_DEFAULT_CIF_ROOT = None

# minimal atomic-number -> symbol map for donor elements (provenance only)
_PT = Chem.GetPeriodicTable()


def _resolve_dir(cli_value, env_name, default, what):
    for candidate in (cli_value, os.environ.get(env_name), default):
        if candidate and os.path.isdir(candidate):
            return candidate
    if sys.stdin.isatty():
        typed = input(f"{what} not found. Enter the path: ").strip().strip('"')
        if typed and os.path.isdir(typed):
            return typed
    raise SystemExit(f"Could not find {what}. Pass the flag or set {env_name}.")


def _resolve_file(cli_value, env_name, default, what):
    for candidate in (cli_value, os.environ.get(env_name), default):
        if candidate and os.path.isfile(candidate):
            return candidate
    if sys.stdin.isatty():
        typed = input(f"{what} not found. Enter the path: ").strip().strip('"')
        if typed and os.path.isfile(typed):
            return typed
    raise SystemExit(f"Could not find {what}. Pass the flag or set {env_name}.")


# nitrate written flat as [O-]N([O-])[O-] is NO3(3-) (charge -3), a charge bug in
# the upstream extraction (real nitrate is NO3-, [O-][N+](=O)[O-], charge -1). It
# sanitizes cleanly (neutral trivalent N + three O-), so repair_hypervalent never
# catches it, inflating the ligand charge by +2 per nitrate and thus the derived OS.
# _FLAT_NITRATE matches N bonded to exactly three terminal O-, all single bonds.
_FLAT_NITRATE = Chem.MolFromSmarts("[NX3;!+;!-]([OX1;-1])([OX1;-1])[OX1;-1]")


def fix_flat_nitrate(smiles):
    """Return (fixed_smiles, n_fixed): rewrite each flat NO3(3-) motif to real
    nitrate NO3- ([O-][N+](=O)[O-]). n_fixed = number of nitrates repaired (each
    shifts the fragment charge by +2, so the caller lowers OS by 2 per fix)."""
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return smiles, 0
    matches = m.GetSubstructMatches(_FLAT_NITRATE)
    if not matches:
        return smiles, 0
    rw = Chem.RWMol(m)
    n_fixed = 0
    for match in matches:
        n_idx, o1 = match[0], match[1]
        n_atom = rw.GetAtomWithIdx(n_idx)
        if n_atom.GetFormalCharge() != 0:
            continue  # already touched (shared atom across overlapping matches)
        n_atom.SetFormalCharge(1)
        rw.GetBondBetweenAtoms(n_idx, o1).SetBondType(Chem.BondType.DOUBLE)
        o_atom = rw.GetAtomWithIdx(o1)
        o_atom.SetFormalCharge(0)
        o_atom.SetNoImplicit(True)
        n_fixed += 1
    if not n_fixed:
        return smiles, 0
    fixed = rw.GetMol()
    try:
        Chem.SanitizeMol(fixed)
    except Exception:
        return smiles, 0
    return Chem.MolToSmiles(fixed), n_fixed


def normalize_eta_carbocycle(smiles):
    """Collapse eta-multihapto carbocycle/polyene over-charging: ligand_charge_fix
    assigns -1 to EVERY metal-bonded carbon, so an eta5-Cp comes out C5(5-), an
    eta6-arene C6(6-), an eta3-allyl C3(3-), an eta4-diene C4(4-) -- all far too
    negative (real: Cp- = -1, arene = 0, allyl = -1, diene = 0). This inflates the
    derived oxidation state (e.g. a Cp'd Co reads +6).

    Operates on each connected component of >=2 artifact-negative carbons (a ring or
    an acyclic pi-system): neutralise all of them, then give the component net -1 if
    it has an ODD number of carbons (Cp, allyl, pentadienyl) or 0 if EVEN (arene,
    diene) -- the aromatic/pi electron-count rule. Returns (new_smiles, delta_charge);
    the caller lowers OS by delta_charge to keep the physical total charge constant.
    Also RESCUES SMILES that would not otherwise parse (C6(6-) etc.)."""
    m = Chem.MolFromSmiles(smiles, sanitize=False)
    if m is None:
        return smiles, 0
    try:
        m.UpdatePropertyCache(strict=False)
    except Exception:
        pass
    Chem.FastFindRings(m)
    neg_c = {a.GetIdx() for a in m.GetAtoms()
             if a.GetSymbol() == "C" and a.GetFormalCharge() < 0}
    if len(neg_c) < 2:
        return smiles, 0
    q_before = sum(a.GetFormalCharge() for a in m.GetAtoms())
    # connected components of negative carbons (bonded to each other)
    comps, seen = [], set()
    for start in neg_c:
        if start in seen:
            continue
        stack, comp = [start], []
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x)
            for nb in m.GetAtomWithIdx(x).GetNeighbors():
                if nb.GetIdx() in neg_c and nb.GetIdx() not in seen:
                    stack.append(nb.GetIdx())
        comps.append(comp)
    changed = False
    for comp in comps:
        if len(comp) < 2:
            continue                              # lone [C-] (acetylide/vinyl) is real
        atoms = [m.GetAtomWithIdx(i) for i in comp]
        for a in atoms:
            a.SetFormalCharge(0)
            a.SetNoImplicit(False)
            a.SetNumExplicitHs(0)
        if len(comp) % 2 == 1:                    # odd pi-system -> anion (-1)
            ch = min(atoms, key=lambda a: a.GetDegree())
            ch.SetFormalCharge(-1)
            if ch.GetDegree() == 2:               # unsubstituted CH carries the H
                ch.SetNumExplicitHs(1)
                ch.SetNoImplicit(True)
        changed = True
    if not changed:
        return smiles, 0
    try:
        Chem.SanitizeMol(m)
        s2 = Chem.MolToSmiles(m)
    except Exception:
        return smiles, 0
    if Chem.MolFromSmiles(s2) is None:
        return smiles, 0
    return s2, Chem.GetFormalCharge(Chem.MolFromSmiles(s2)) - q_before


# a group-1 metal bonded into a ligand SMILES is a data artifact: a crown/cryptand
# captured its counter-cation and the alkali atom was written into the ligand graph
# (e.g. ...[N+][K]12345...). MeCoBi would build the K/Na as part of the organic
# ligand -> wrong. Detect any alkali-metal atom in a coordinated ligand.
_EMBEDDED_ALKALI = Chem.MolFromSmarts("[Li,Na,K,Rb,Cs]")


def has_embedded_alkali(ligand_smiles_list):
    for s in ligand_smiles_list:
        m = Chem.MolFromSmiles(s)
        if m is not None and m.HasSubstructMatch(_EMBEDDED_ALKALI):
            return True
    return False


def _fragment_charges(ligand_smiles_list):
    """Best-effort per-ligand formal charge (provenance). None if a fragment won't parse."""
    charges = []
    for s in ligand_smiles_list:
        m = Chem.MolFromSmiles(s)
        charges.append(None if m is None else Chem.GetFormalCharge(m))
    return charges


def _cif_tree_refcodes(cif_root):
    tree = set()
    for d in os.scandir(cif_root):
        if d.is_dir():
            for f in os.scandir(d.path):
                if f.name.endswith(".cif"):
                    tree.add(f.name.split(".")[0])
    return tree


def _metalig_index(db_path):
    """refcode -> (cn, os_or_None, n_ligands) reconstructed from MetaLig, for cross-check
    ONLY. Mirrors metalig_build_bundle grouping: sum denticities per refcode, OS from
    parent_metal_os else parent_complex_charge - sum(ligand charges)."""
    uniq = {}   # unique_name -> (charge, denticity)
    ref = {}    # refcode -> {mos, cq, ligs:[unique_name]}
    with bz2.open(db_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            v = json.loads(line)["value"]
            g = v["global_props"]; li = v["ligand_instances"]
            un = g.get("unique_name")
            if un not in uniq:
                uniq[un] = (g.get("charge"), g.get("n_denticities"))
            for rc, mos, cq in zip(li.get("parent_complex_id", []),
                                    li.get("parent_metal_os", []),
                                    li.get("parent_complex_charge", [])):
                r = ref.setdefault(rc, {"mos": mos, "cq": cq, "ligs": []})
                r["ligs"].append(un)
    out = {}
    for rc, d in ref.items():
        cn = sum((uniq[u][1] or 0) for u in d["ligs"])
        mos = d["mos"]
        os_ = None
        if mos is not None and not (isinstance(mos, float) and mos != mos):
            os_ = int(round(mos))
        elif d["cq"] is not None:
            lc = [uniq[u][0] for u in d["ligs"]]
            if all(c is not None for c in lc):
                os_ = int(round(d["cq"] - sum(lc)))
        out[rc] = (cn, os_, len(d["ligs"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mecobi-ready", default=None,
                     help="mecobi_ready_all.csv (falls back to MECOBI_READY_CSV env).")
    ap.add_argument("--cif-root", default=None,
                     help="Generation3-style CIF folder (falls back to MECOBI_CIF_ROOT env).")
    ap.add_argument("--no-cif-filter", action="store_true")
    ap.add_argument("--metalig-crosscheck", action="store_true",
                     help="Load MetaLig and report per-refcode CN/OS agreement (report only).")
    ap.add_argument("--metalig-db", default=None,
                     help="MetaLigDB .jsonlines.bz2 (falls back to MECOBI_METALIGDB env).")
    ap.add_argument("--cap", type=int, default=100, help="max complexes per (metal,CN,OS) cell")
    ap.add_argument("--neg-control-cn", type=int, default=10,
                     help="CN >= this becomes a negative control (MeCoBi must reject it).")
    ap.add_argument("--neg-control-cap", type=int, default=200,
                     help="max negative-control complexes to include.")
    ap.add_argument("--os-min", type=int, default=-4, help="drop complexes with OS below this.")
    ap.add_argument("--os-max", type=int, default=8, help="drop complexes with OS above this.")
    ap.add_argument("--keep-embedded-alkali", action="store_true",
                     help="keep complexes whose ligand SMILES embed a group-1 metal (default: drop).")
    ap.add_argument("--keep-unparseable", action="store_true",
                     help="keep build targets with a still-unparseable ligand after "
                          "normalisation (default: drop; CIF re-perception recovers these later).")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="benchmark_bundle_v2.json")
    cfg = ap.parse_args()

    ready = _resolve_file(cfg.mecobi_ready, "MECOBI_READY_CSV", _DEFAULT_MECOBI_READY,
                          "mecobi_ready_all.csv")

    tree = None
    if not cfg.no_cif_filter:
        cif_root = _resolve_dir(cfg.cif_root, "MECOBI_CIF_ROOT", _DEFAULT_CIF_ROOT, "CIF root folder")
        tree = _cif_tree_refcodes(cif_root)
        print(f"CIF-tree refcodes: {len(tree)}")

    # 1. read + dedup charge_ok=Y records into eligible list. CN 2-9 are build
    #    targets; CN >= --neg-control-cn are collected separately as a negative
    #    control (MeCoBi must reject them cleanly, DenticityMismatchError).
    seen = set()
    elig = []
    neg = []
    drop = defaultdict(int)
    n_nitrate_cx = 0
    n_eta_cx = 0
    with open(ready, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if row.get("charge_ok") != "Y":
                drop["not_charge_ok"] += 1; continue
            rc = row["Name"].strip()
            if rc in seen:
                drop["dup_row"] += 1; continue
            try:
                cn = int(float(row["CoordinationNumber"]))
                ox = int(float(row["OxidationState"]))
            except (ValueError, TypeError):
                drop["bad_cn_or_os"] += 1; continue
            ligands = [s for s in row["LigandSmiles"].split(".") if s]
            if not ligands:
                drop["no_ligands"] += 1; continue
            if tree is not None and rc not in tree:
                drop["no_cif"] += 1; continue
            seen.add(rc)

            # repair flat NO3(3-) -> NO3-, correcting the derived OS by -2 per fix
            fixed_ligands, nfix = [], 0
            for s in ligands:
                fs, k = fix_flat_nitrate(s)
                fixed_ligands.append(fs); nfix += k
            if nfix:
                ox -= 2 * nfix
                n_nitrate_cx += 1
            ligands = fixed_ligands

            # collapse eta-carbocycle over-charging (Cp5- -> Cp-, arene6- -> neutral),
            # lowering OS by the total charge removed. Also rescues C6(6-)/C5(5-) SMILES
            # that would not otherwise parse.
            eta_ligands, eta_dq = [], 0
            for s in ligands:
                ns, dq = normalize_eta_carbocycle(s)
                eta_ligands.append(ns); eta_dq += dq
            if eta_dq:
                ox -= eta_dq
                n_eta_cx += 1
            ligands = eta_ligands

            dn = [int(x) for x in row["DonorAtomicNums"].split("|") if x.strip()]
            rec = {
                "refcode": rc, "metal": row["MetalSymbol"].strip(), "ox": ox, "cn": cn,
                "ligands": ligands, "charges": _fragment_charges(ligands),
                "donor_elements": [_PT.GetElementSymbol(z) for z in dn],
                "os_confidence": row.get("os_confidence", ""),
                "nitrate_fixed": nfix, "eta_fixed": bool(eta_dq),
            }
            if 2 <= cn <= 9:
                # data-quality guards (build targets only; the negative control is
                # meant to be odd): drop chemically-impossible OS, ligand-embedded
                # alkali-metal artifacts, and (post-normalisation) unparseable ligands.
                if not (cfg.os_min <= ox <= cfg.os_max):
                    drop["os_out_of_window"] += 1; continue
                if not cfg.keep_embedded_alkali and has_embedded_alkali(ligands):
                    drop["embedded_alkali"] += 1; continue
                if not cfg.keep_unparseable and any(Chem.MolFromSmiles(s) is None for s in ligands):
                    drop["unparseable_ligand"] += 1; continue
                elig.append(rec)
            elif cn >= cfg.neg_control_cn:
                rec["expect_build"] = False   # negative control: must fail cleanly
                neg.append(rec)
            else:
                drop["cn_out_of_range"] += 1
    print(f"eligible+scorable complexes: {len(elig)}  (dropped: {dict(drop)})")
    print(f"  nitrate-repaired complexes: {n_nitrate_cx}")
    print(f"  eta-carbocycle-normalised complexes: {n_eta_cx}")
    print(f"  CN>={cfg.neg_control_cn} negative-control candidates: {len(neg)}")

    # 2. optional MetaLig cross-check (report only)
    if cfg.metalig_crosscheck:
        db = _resolve_file(cfg.metalig_db, "MECOBI_METALIGDB", None, "MetaLigDB .jsonlines.bz2")
        idx = _metalig_index(db)
        both = cn_agree = os_agree = only_ours = 0
        for r in elig:
            ml = idx.get(r["refcode"])
            if ml is None:
                r["metalig_cn"] = None; r["metalig_os"] = None
                only_ours += 1
                continue
            r["metalig_cn"], r["metalig_os"] = ml[0], ml[1]
            both += 1
            if ml[0] == r["cn"]:
                cn_agree += 1
            if ml[1] is not None and ml[1] == r["ox"]:
                os_agree += 1
        print(f"MetaLig cross-check: {both} refcodes in both; "
              f"CN agree {cn_agree}/{both} ({100*cn_agree/max(both,1):.1f}%); "
              f"OS agree {os_agree}/{both}; {only_ours} only in mecobi_ready")

    # 3. stratified capped allocation over (metal, CN, OS)
    random.seed(cfg.seed)
    cells = defaultdict(list)
    for r in elig:
        cells[(r["metal"], r["cn"], r["ox"])].append(r)
    bundle = []
    for _, recs in cells.items():
        random.shuffle(recs)
        bundle.extend(recs[:cfg.cap])

    # negative control: a capped, metal-diverse CN>=neg_control_cn sample that
    # MeCoBi must reject cleanly (kept separate from the stratified build set).
    random.shuffle(neg)
    neg_sample = neg[:cfg.neg_control_cap]
    bundle.extend(neg_sample)
    random.shuffle(bundle)

    out_json = os.path.join(HERE, cfg.out)
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(bundle, fh, indent=0)
    out_gz = out_json + ".gz"
    with gzip.open(out_gz, "wt", encoding="utf-8") as fh:
        json.dump(bundle, fh)

    # 4. coverage report
    bm = defaultdict(int); bc = defaultdict(int); bo = defaultdict(int)
    for r in bundle:
        bm[r["metal"]] += 1; bc[r["cn"]] += 1; bo[r["ox"]] += 1
    build_n = len(bundle) - len(neg_sample)
    print(f"\nBUNDLE v2: {len(bundle)} complexes = {build_n} build targets (CN2-9) "
          f"+ {len(neg_sample)} negative control (CN>={cfg.neg_control_cn})")
    print(f"  (cap={cfg.cap}/cell, {len(cells)} cells)")
    print(f"  wrote {out_json}  +  {out_gz}")
    print("  by CN: " + "  ".join(f"CN{c}:{bc[c]}" for c in sorted(bc)))
    print("  by OS: " + "  ".join(f"{o:+d}:{bo[o]}" for o in sorted(bo)))
    print(f"  metals ({len(bm)}): " + "  ".join(f"{m}:{n}" for m, n in
                                                sorted(bm.items(), key=lambda x: -x[1])[:16]))


if __name__ == "__main__":
    main()
