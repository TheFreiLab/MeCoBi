"""Build deterministic MetalloGen m-SMILES for the pilot straight from the crystal site_map.

Runs in the mecobi/dev env (needs mecobi.assembly.sites.SITE_VECTORS + rdkit). Writes
``benchmark_msmiles_pilot.json`` {refcode: {msmiles, geometry, status, note}} so the MetalloGen
runner (metallogen_run.py, in the MetalloGen conda env) stays a thin executor with NO mecobi dep --
exactly the split molsim_run.py uses.

Isomer control (no oracle): MetalloGen's m-SMILES ``:N`` labels index fixed coordination-site
vectors (globalvars.known_geometries_vector_dict) -- a site model just like MeCoBi's. We translate
the crystal donor->site assignment (site_map, in MeCoBi's SITE_VECTORS convention) into MetalloGen's
site numbering via a per-geometry congruence permutation (iterated Kabsch+Hungarian between the two
ideal vector sets, residual ~0 since they are the same polyhedron relabelled). So MetalloGen builds
the SAME crystal isomer MeCoBi and molSimplify target -- no RMSD trial-and-error.

    python make_metallogen_msmiles.py            # -> benchmark_msmiles_pilot.json (+ coverage)
    python make_metallogen_msmiles.py --hydrides benchmark_hydrides.json
        # -> benchmark_msmiles_pilot_hyd.json: ONLY the complexes with a located hydride, built with
        #    their [H-] ligands on the crystal site (re-run those with metallogen_run.py --msmiles)
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
from rdkit import Chem, RDLogger
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

from mecobi.assembly.sites import SITE_VECTORS

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent   # pilot100/metallogen/: writes benchmark_msmiles_pilot.json
PILOT = HERE.parent                      # pilot100/: pilot_100.json + crystal targets
BENCH = PILOT.parent                     # benchmark root: frozen bundle + donors
_s3 = np.sqrt(3.0)
_TAU = 2 * np.pi


def _penta(z, r=1.0):  # 5 equatorial points on a pentagon at height z
    return [[r * np.cos(_TAU * k / 5), r * np.sin(_TAU * k / 5), z] for k in range(5)]


# MetalloGen ideal site vectors (globalvars.known_geometries_vector_dict), verbatim keys incl. the
# 'squre' typo. Only the geometries the pilot uses. Order == MetalloGen's 1-based site numbering.
MG_VECTORS = {
    "2_linear": [[0, 0, 1], [0, 0, -1]],
    "3_trigonal_planar": (np.array([[2, 0, 0], [-1, _s3, 0], [-1, -_s3, 0]]) / 2).tolist(),
    "4_tetrahedral": (np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]]) / _s3).tolist(),
    "4_square_planar": [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0]],
    "5_trigonal_bipyramidal": (np.array([[0, 0, 2], [0, 0, -2], [2, 0, 0], [-1, _s3, 0],
                                         [-1, -_s3, 0]]) / 2).tolist(),
    "5_square_pyramidal": [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1]],
    "6_octahedral": [[0, 0, 1], [0, 0, -1], [0, 1, 0], [0, -1, 0], [1, 0, 0], [-1, 0, 0]],
    "7_pentagonal_bipyramidal": [[0, 0, 1], [0, 0, -1]] + _penta(0.0),
    "8_squre_antiprismatic": (np.array([[-1, 1, 1], [1, 1, 1], [-1, -1, 1], [1, -1, 1],
                                        [-1.41, 0, -1], [0, -1.41, -1], [1.41, 0, -1],
                                        [0, 1.41, -1]]) / _s3).tolist(),
    "8_dodecahedral": [[1.289, 0.411, 0], [-1.289, 0.411, 0], [0, -0.411, 1.289],
                       [0, -0.411, -1.289], [1, -1.568, 0], [-1, -1.568, 0], [0, 1.568, 1],
                       [0, 1.568, -1]],
    "9_tricapped_trigonal_prismatic": [[1.511, 0.0, 1.31], [-0.756, 1.309, 1.309],
                                       [-0.756, -1.309, 1.309], [1.511, 0.0, -1.31],
                                       [-0.756, 1.309, -1.309], [-0.756, -1.309, -1.309],
                                       [-2.0, 0.0, 0.0], [1.16, -1.62, 0], [1.16, 1.62, 0]],
}

# crystal_assign geometry name -> MetalloGen m-SMILES geometry key.
GEO_NAME = {
    "linear": "2_linear", "trigonal_planar": "3_trigonal_planar",
    "tetrahedral": "4_tetrahedral", "square_planar": "4_square_planar",
    "trigonal_bipyramidal": "5_trigonal_bipyramidal", "square_pyramidal": "5_square_pyramidal",
    "octahedral": "6_octahedral", "pentagonal_bipyramidal": "7_pentagonal_bipyramidal",
    "square_antiprism": "8_squre_antiprismatic", "dodecahedral": "8_dodecahedral",
    "tricapped_trigonal_prism": "9_tricapped_trigonal_prismatic",
}


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def _kabsch(P, Q):
    U, _, Vt = np.linalg.svd(P.T @ Q)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    return Vt.T @ np.diag([1.0, 1.0, d]) @ U.T


def site_permutation(crystal_geom: str) -> "tuple[list[int], float]":
    """MeCoBi site index (0-based) -> MetalloGen site number (1-based); and the fit residual.

    Both SITE_VECTORS[geom] and MG_VECTORS[key] describe (nominally) the same ideal polyhedron;
    find the rotation+assignment aligning them (iterated Kabsch + Hungarian) and return the
    relabelling. When the two idealisations are truly congruent (residual ~0, all the low-CN
    geometries) the isomer -- every cis/trans relationship -- is preserved exactly. A few high-CN
    shells (dodecahedral/antiprism/tricapped) use slightly different D2d/D4d parametrisations, so
    the residual is nonzero and the mapping is best-effort; main() flags those.
    """
    from mecobi.model import Geometry

    mg = _unit(MG_VECTORS[GEO_NAME[crystal_geom]])
    mc = _unit(SITE_VECTORS[Geometry(crystal_geom)])
    if len(mg) != len(mc):
        raise ValueError(f"{crystal_geom}: {len(mc)} MeCoBi sites vs {len(mg)} MetalloGen")
    R = np.eye(3)
    col = None
    for _ in range(80):
        _, col = linear_sum_assignment(cdist(mg, mc @ R.T))  # mg[i] <-> mc[col[i]]
        R = _kabsch(mc[col], mg)
    resid = float(np.sqrt(np.mean(np.sum((mg - mc[col] @ R.T) ** 2, axis=1))))
    perm = [0] * len(mc)
    for mg_i, mc_j in enumerate(col):
        perm[mc_j] = mg_i + 1  # MetalloGen sites are 1-based
    return perm, resid


def parse_site_map(s: str) -> "dict[int, list[int]]":
    """'0:2,5;1:4,0,1,3' -> {0:[2,5], 1:[4,0,1,3]} (site order == donor order)."""
    out = {}
    for part in s.split(";"):
        li, sites = part.split(":")
        out[int(li)] = [int(x) for x in sites.split(",")]
    return out


def metal_token(metal: str, ox: int) -> str:
    if ox > 0:
        return f"[{metal}+{ox}]"
    if ox < 0:
        return f"[{metal}{ox}]"  # ox already carries the minus
    return f"[{metal}]"


def build_msmiles(rec, donors_rc, geom, site_map, perm):
    """Assemble the full m-SMILES; return (msmiles, error). Donor element multiset is checked."""
    frags = []
    got = []
    for lig_idx, smi in enumerate(rec["ligands"]):
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            return None, f"unparseable SMILES {smi!r}"
        atoms = donors_rc[lig_idx]
        sites = site_map.get(lig_idx)
        if sites is None:
            return None, f"lig {lig_idx}: no site_map entry"
        if len(sites) == 1 and len(atoms) > 1:
            sites = sites * len(atoms)  # haptic: all donor atoms share the one collapsed site (eta-n)
        if len(sites) != len(atoms):
            return None, f"lig {lig_idx}: {len(atoms)} donors vs site_map {sites} (multi-site haptic)"
        for atom_idx, mc_site in zip(atoms, sites):
            if atom_idx >= mol.GetNumAtoms():
                return None, f"donor idx {atom_idx} out of range for {smi!r}"
            mol.GetAtomWithIdx(atom_idx).SetAtomMapNum(perm[mc_site])
            got.append(mol.GetAtomWithIdx(atom_idx).GetSymbol())
        frags.append(Chem.MolToSmiles(mol))
    from collections import Counter
    if Counter(got) != Counter(rec["donor_elements"]):
        return None, f"donor multiset {dict(Counter(got))} != {dict(Counter(rec['donor_elements']))}"
    return "|".join([metal_token(rec["metal"], rec["ox"])] + frags + [GEO_NAME[geom]]), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hydrides", default=None, metavar="FILE",
                    help="benchmark_hydrides.json (benchmark root): write m-SMILES for ONLY the "
                         "hydride-corrected complexes ([H-] ligands, OS + n, the site map re-read "
                         "with the H) to benchmark_msmiles_pilot_hyd.json.")
    cfg = ap.parse_args()
    bundle = {r["refcode"]: r
              for r in json.loads(gzip.open(BENCH / "benchmark_bundle.json.gz", "rt").read())}
    donors = json.loads((BENCH / "benchmark_donors.json").read_text())
    targets = json.loads((PILOT / "benchmark_targets_pilot.json").read_text())
    pilot = json.loads((PILOT / "pilot_100.json").read_text())
    out_name = "benchmark_msmiles_pilot.json"
    if cfg.hydrides:
        sys.path.insert(0, str(BENCH))
        import hydrides as HY
        hyd = HY.load(cfg.hydrides)
        pilot = [rc for rc in pilot if rc in hyd]
        for rc in pilot:   # corrected record / donors / target for exactly these refcodes
            h = hyd[rc]
            bundle[rc] = HY.record(bundle[rc], h)
            if rc in donors:
                donors[rc] = HY.donors(donors[rc], h)
            targets[rc] = h.get("target")
        out_name = "benchmark_msmiles_pilot_hyd.json"

    perm_resid = {g: site_permutation(g) for g in GEO_NAME}
    perms = {g: p for g, (p, _) in perm_resid.items()}
    approx = {g for g, (_, r) in perm_resid.items() if r > 0.05}  # non-congruent idealisations
    print("site permutations (MeCoBi 0-based -> MetalloGen 1-based):")
    for g, (p, r) in perm_resid.items():
        tag = f"  <-- APPROX (residual {r:.2f}, isomer best-effort)" if r > 0.05 else ""
        print(f"  {g:24} resid={r:.3f}  {p}{tag}")

    out, skipped = {}, []
    for rc in pilot:
        t, rec = targets.get(rc), bundle.get(rc)
        if not t or not rec or rc not in donors:
            skipped.append((rc, "no target/bundle/donors")); continue
        geom = t.get("geometry")
        if geom not in GEO_NAME:
            skipped.append((rc, f"no MetalloGen geometry for {geom!r}")); continue
        sm = t.get("site_map")
        if not sm:  # geometry_only: crystal_assign found no deterministic isomer -> out of scope
            skipped.append((rc, "geometry_only: no crystal site_map (can't pin isomer)")); continue
        ms, err = build_msmiles(rec, donors[rc], geom, parse_site_map(sm), perms[geom])
        if err:
            skipped.append((rc, err)); continue
        note = "approx site map (idealisations differ)" if geom in approx else ""
        out[rc] = {"msmiles": ms, "metal": rec["metal"], "cn": rec["cn"],
                   "geometry": geom, "status": "ok", "note": note}

    (HERE / out_name).write_text(json.dumps(out, indent=0))
    print(f"\nm-SMILES built: {len(out)}/{len(pilot)}  -> {out_name}")
    print(f"  ok={sum(v['status']=='ok' for v in out.values())} "
          f"geometry_only={sum(v['status']=='geometry_only' for v in out.values())}")
    if skipped:
        print(f"skipped {len(skipped)}:")
        for rc, why in skipped:
            print(f"  {rc}: {why}")
    # show a couple for eyeballing
    print("\nexamples:")
    for rc in list(out)[:3]:
        print(f"  {rc}: {out[rc]['msmiles']}")


if __name__ == "__main__":
    main()
