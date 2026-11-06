"""Reconstruct per-complex MeCoBi build inputs from MetaLig.

Groups MetaLig's unique ligands back into their parent CSD complexes (by refcode)
and converts each to a proper free-ligand RDKit SMILES. MetaLig writes coordinated
donors as OPEN-VALENCE radicals (the valence that went to the metal), so a naive
RDKit parse yields radicals, not anions. We resolve each radical to a formal charge
(-1 per open valence, the X-type donor) and REQUIRE the resulting total formal
charge to equal MetaLig's confident `charge` -- otherwise the ligand is dropped, so
every kept ligand carries MetaLig's authoritative charge. Only complexes whose FULL
ligand set converts and whose summed denticity is a MeCoBi CN (2-9) are kept.
Run in the dart venv (has pysmiles).

    python dataprep/metalig_ingest.py --metals Fe Pt Ni Ru Ir --sample 60 --out sample.json
"""
import argparse
import bz2
import glob
import json
import math
import os
from collections import defaultdict

from rdkit import Chem
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")
import pysmiles


def _find_metalig_db():
    """MECOBI_METALIGDB env var, else auto-locate inside an installed
    dartassembler/DARTassembler package (pip install dartassembler bundles
    the DB as package data under <pkg>/data/metalig/*.jsonlines.bz2)."""
    env = os.environ.get("MECOBI_METALIGDB")
    if env:
        return env
    for modname in ("dartassembler", "DARTassembler"):
        try:
            mod = __import__(modname)
        except ImportError:
            continue
        hits = glob.glob(os.path.join(os.path.dirname(mod.__file__),
                                       "data", "metalig", "*.jsonlines.bz2"))
        if hits:
            return hits[0]
    raise FileNotFoundError(
        "MetaLigDB not found. Set MECOBI_METALIGDB or `pip install dartassembler`.")


DB = _find_metalig_db()
_BO = {1: Chem.BondType.SINGLE, 2: Chem.BondType.DOUBLE, 3: Chem.BondType.TRIPLE,
       4: Chem.BondType.QUADRUPLE, 1.5: Chem.BondType.AROMATIC}


def _mol_from_pysmiles(smi):
    try:
        g = pysmiles.read_smiles(smi, explicit_hydrogen=False, reinterpret_aromatic=True)
    except Exception:
        return None
    rw = Chem.RWMol(); idx = {}
    for node, d in g.nodes(data=True):
        if not d.get("element"):
            return None
        a = Chem.Atom(d["element"])
        if d.get("charge"):
            a.SetFormalCharge(int(d["charge"]))
        if d.get("hcount") is not None:
            a.SetNumExplicitHs(int(d["hcount"])); a.SetNoImplicit(True)
        idx[node] = rw.AddAtom(a)
    for u, v, d in g.edges(data=True):
        rw.AddBond(idx[u], idx[v], _BO.get(d.get("order", 1), Chem.BondType.SINGLE))
    return rw.GetMol()


def convert(smi, want_charge):
    """MetaLig ligand SMILES -> RDKit-canonical free-ligand SMILES whose total formal
    charge == want_charge, resolving open-valence (coordinated) donors to anions.
    Returns None if it can't be parsed or the charge can't be reproduced."""
    if not smi:
        return None
    m = Chem.MolFromSmiles(smi)          # default sanitize computes radicals at open valences
    if m is None:
        m = _mol_from_pysmiles(smi)
    if m is None:
        return None
    # each open valence at a donor (radical after sanitize) is a bond to the metal -> -1
    rw = Chem.RWMol(m)
    for a in rw.GetAtoms():
        r = a.GetNumRadicalElectrons()
        if r:
            a.SetFormalCharge(a.GetFormalCharge() - r)
            a.SetNumRadicalElectrons(0)
    m = rw.GetMol()
    try:
        Chem.SanitizeMol(m)
    except Exception:
        return None
    if want_charge is not None and Chem.GetFormalCharge(m) != want_charge:
        return None  # couldn't reproduce MetaLig's confident charge -> drop (conservative)
    return Chem.MolToSmiles(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metals", nargs="*", default=None)
    ap.add_argument("--sample", type=int, default=60)
    ap.add_argument("--out", default="metalig_sample.json")
    cfg = ap.parse_args()
    want = set(cfg.metals) if cfg.metals else None

    ref = {}   # refcode -> {metal, os, ligands:[(smiles, charge, donor_elements, denticity)]}
    with bz2.open(DB, "rt", encoding="utf-8") as f:
        for line in f:
            v = json.loads(line)["value"]
            g = v["global_props"]; li = v["ligand_instances"]; atoms = v["atomic_props"]["atoms"]
            donors = [atoms[d] for d in v["donor_idc"]]
            for rc, met, os_ in zip(li.get("parent_complex_id", []),
                                    li.get("parent_metal", []),
                                    li.get("parent_metal_os", [])):
                if want and met not in want:
                    continue
                ref.setdefault(rc, {"metal": met, "os": os_, "ligands": []})
                ref[rc]["ligands"].append((g.get("smiles"), g.get("charge"),
                                           donors, g.get("n_denticities")))

    out, stats = [], defaultdict(int)
    for rc, d in ref.items():
        if len(out) >= cfg.sample:
            break
        cn = sum((l[3] or 0) for l in d["ligands"])
        if not (2 <= cn <= 9):
            stats["bad_cn"] += 1; continue
        if d["os"] is None or (isinstance(d["os"], float) and math.isnan(d["os"])):
            stats["no_os"] += 1; continue
        smis = [convert(l[0], l[1]) for l in d["ligands"]]
        if any(s is None for s in smis):
            stats["ligand_convert_fail"] += 1; continue
        # sanity: total complex charge should be neutral-ish (metal OS + sum ligand charges)
        lig_charge = sum(l[1] for l in d["ligands"])
        out.append({
            "refcode": rc, "metal": d["metal"], "ox": int(round(d["os"])), "cn": cn,
            "ligands": smis, "charges": [l[1] for l in d["ligands"]],
            "complex_charge": int(round(d["os"])) + lig_charge,
            "donor_elements": [l[2] for l in d["ligands"]],
        })
        stats["kept"] += 1

    json.dump(out, open(cfg.out, "w"), indent=1)
    print(f"reconstructed {len(ref)} complexes for metals={want or 'all'}")
    print(f"kept {stats['kept']}  (dropped: bad_cn={stats['bad_cn']}, "
          f"no_os={stats['no_os']}, ligand_convert_fail={stats['ligand_convert_fail']})")
    print(f"wrote {cfg.out}")
    for r in out[:6]:
        print(f"  {r['refcode']:8} {r['metal']}{r['ox']:+d} CN{r['cn']} "
              f"cplx_q={r['complex_charge']:+d}  {r['ligands']}")


if __name__ == "__main__":
    main()
