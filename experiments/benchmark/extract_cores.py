"""Extract the experimental **depth-2 core** for every benchmark refcode from the CCDC CIFs
-- the reference region for Architector's core kmRMSD (c-kmRMSD): the metal center plus every
atom within two graph hops of it on the molecular graph.

  depth 0 : the metal
  depth 1 : its donors (the target_cn nearest non-H, non-metal contacts -- same definition the
            coordination-sphere extractor uses, so the reference matches the build's CN)
  depth 2 : the heavy atoms covalently bonded to those donors (donor-neighbours), metal excluded

Heavy atoms only (crystallographic H is unreliable and the built structures carry their own H);
covalent bonds are perceived by radius contact. Reuses cif_geometry's frac->cartesian + space-
group expansion; its own Cordero covalent radii (no rdkit dependency).

Output: benchmark_cores.json = {refcode: {"metal": {el,xyz},
                                          "donors": [{el,xyz}...],   # depth 1, len target_cn
                                          "depth2": [{el,xyz}...]}}  # depth 2 heavy neighbours
This is the crystal side of c-kmRMSD; score a build by extracting the same core from its .xyz
and doing a Kuhn-Munkres-matched Kabsch RMSD over it. Shardable + resumable; skips OneDrive
placeholders. Runs with numpy only.

    python extract_cores.py --shard 0/1 --limit 100 --cif-root /path/to/CSD/cifs
    for i in $(seq 0 7); do python extract_cores.py --shard $i/8 & done; wait   # full 30k
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
from pathlib import Path

import numpy as np

from cif_geometry import SYM2NAME, _cell_and_atoms

HERE = Path(__file__).parent
_DEFAULT_CIF_ROOT = None  # no built-in default: --cif-root or MECOBI_CIF_ROOT
_OFFLINE = 0x1000 | 0x400000

# Cordero (2008) single-bond covalent radii (A) for the elements that show up as donors and
# donor-neighbours; metals are never bonded *to* here (they're the excluded center), so a light-
# element table + default is enough for perceiving depth-2 bonds.
RCOV = {
    "H": 0.31, "B": 0.84, "C": 0.76, "N": 0.71, "O": 0.66, "F": 0.57, "Si": 1.11, "P": 1.07,
    "S": 1.05, "Cl": 1.02, "As": 1.19, "Se": 1.20, "Br": 1.20, "Te": 1.38, "I": 1.39,
    "Ge": 1.20, "Sb": 1.39, "Al": 1.21, "Ga": 1.22, "Sn": 1.39, "Bi": 1.48, "Pb": 1.46,
}
_TOL = 1.30   # bond if dist <= (rcov(a)+rcov(b)) * _TOL
_RCUT = 5.0   # only expand crystal atoms within this radius of the metal (core is well inside)


def rcov(el):
    return RCOV.get(el, 0.77)


def is_placeholder(path):
    try:
        return bool(os.stat(path).st_file_attributes & _OFFLINE)
    except (AttributeError, OSError):
        return False


def _bundle(name="benchmark_bundle"):
    gz = HERE / f"{name}.json.gz"
    if gz.exists():
        return json.loads(gzip.open(gz, "rt", encoding="utf-8").read())
    return json.loads((HERE / f"{name}.json").read_text())


def depth2_core(text, metal_sym, target_cn, donor_elements=None):
    """metal + donors + heavy donor-neighbours (depth 2), or None.

    Donors: the ``target_cn`` nearest non-H atoms, or -- with ``donor_elements`` (the bundle's
    declared donor atoms) -- for each declared element that many nearest atoms of it (H included
    when declared), so a lost I/Cl/H donor is not replaced by a nearer backbone atom (see
    cif_geometry.coordination_sphere_by_elements). An H donor gets no depth-2 neighbours, as on
    the build side (ckmrmsd.build_core_from_xyz)."""
    M, atoms, symops = _cell_and_atoms(text)
    if M is None:
        return None
    elems, fracs = atoms
    metal_idx = [i for i, e in enumerate(elems) if e == metal_sym]
    if not metal_idx:
        return None
    mc = fracs[metal_idx[0]] @ M.T
    trans = [np.array([i, j, k]) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)]
    xyz_all, el_all = [], []
    for R, t in symops:
        g = fracs @ R.T + t
        for tr in trans:
            xyz_all.append((g + tr) @ M.T)
            el_all.extend(elems)
    IMG = np.vstack(xyz_all)
    IE = np.array(el_all)
    d = np.linalg.norm(IMG - mc, axis=1)
    loc = d <= _RCUT                       # core sits within a few A of the metal
    IMG, IE, d = IMG[loc], IE[loc], d[loc]
    if len(IMG) == 0:
        return None

    # Dedupe coincident symmetry images by rounded position BEFORE picking donors. When the
    # metal sits on a special position (rotation axis / inversion centre) the symop+translation
    # expansion stacks several identical copies of each donor at the same point; without this,
    # cand[:target_cn] gets eaten by duplicate copies of a few atoms (a 3-fold-axis metal picks
    # the same 3 physical donors three times over), so the donor set covers far fewer distinct
    # atoms than target_cn and the depth-2 shell hanging off them is severely under-populated.
    # full_complex() already dedupes the same way; keep the two cores consistent.
    uniq, keep = set(), []
    for j in range(len(IMG)):
        k = tuple(np.round(IMG[j], 1))
        if k not in uniq:
            uniq.add(k)
            keep.append(j)
    IMG, IE, d = IMG[keep], IE[keep], d[keep]

    if donor_elements:
        from collections import Counter

        donor_idx = []
        for el, n in Counter(donor_elements).items():
            pick = [j for _, j in sorted((float(d[j]), j) for j in range(len(IMG))
                                         if d[j] > 0.5 and IE[j] == el)][:n]
            if len(pick) < n:
                return None
            donor_idx += pick
        donor_idx.sort(key=lambda j: d[j])
    else:
        cand = sorted((float(d[j]), j) for j in range(len(IMG))
                      if d[j] > 0.5 and IE[j] not in ("H", metal_sym))
        if len(cand) < target_cn:
            return None
        donor_idx = [j for _, j in cand[:target_cn]]

    def key(p):
        return tuple(np.round(p, 1))

    excl = {key(mc)} | {key(IMG[j]) for j in donor_idx}
    seen, depth2 = set(), []
    for dj in donor_idx:
        dp, de = IMG[dj], IE[dj]
        if de == "H":
            continue
        dd = np.linalg.norm(IMG - dp, axis=1)
        for j in range(len(IMG)):
            ej = IE[j]
            if ej in ("H", metal_sym) or j in donor_idx:
                continue
            if 0.4 < dd[j] <= (rcov(ej) + rcov(de)) * _TOL:
                k = key(IMG[j])
                if k in excl or k in seen:
                    continue
                seen.add(k)
                depth2.append({"el": str(ej), "xyz": IMG[j].tolist()})
    return {
        "metal": {"el": metal_sym, "xyz": mc.tolist()},
        "donors": [{"el": str(IE[j]), "xyz": IMG[j].tolist()} for j in donor_idx],
        "depth2": depth2,
    }


def full_complex(text, metal_sym, target_cn, rcut=18.0, max_atoms=600):
    """.xyz string of the whole isolated complex from the CIF: metal + full coordinated ligands
    (flood-fill along the molecular graph from the donors, never crossing another metal, H kept).
    For visualising the real crystal structure -- returns None if unparseable."""
    M, atoms, symops = _cell_and_atoms(text)
    if M is None:
        return None
    elems, fracs = atoms
    metal_idx = [i for i, e in enumerate(elems) if e == metal_sym]
    if not metal_idx:
        return None
    mc = fracs[metal_idx[0]] @ M.T
    trans = [np.array([i, j, k]) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)]
    xyz_all, el_all = [], []
    for R, t in symops:
        g = fracs @ R.T + t
        for tr in trans:
            xyz_all.append((g + tr) @ M.T)
            el_all.extend(elems)
    IMG = np.vstack(xyz_all)
    IE = np.array(el_all)
    d = np.linalg.norm(IMG - mc, axis=1)
    loc = d <= rcut
    IMG, IE = IMG[loc], IE[loc]
    # dedupe symmetry-image duplicates by rounded position
    seen, keep = set(), []
    for j in range(len(IMG)):
        k = tuple(np.round(IMG[j], 1))
        if k not in seen:
            seen.add(k); keep.append(j)
    IMG, IE = IMG[keep], IE[keep]
    d = np.linalg.norm(IMG - mc, axis=1)
    mi = int(np.argmin(d))
    cand = sorted((float(d[j]), j) for j in range(len(IMG))
                  if j != mi and IE[j] not in ("H", metal_sym))
    if len(cand) < target_cn:
        return None
    donors = [j for _, j in cand[:target_cn]]
    rcov_vec = np.array([rcov(e) for e in IE])
    notmetal = IE != metal_sym
    visited = np.zeros(len(IMG), bool)
    visited[mi] = True
    for dj in donors:
        visited[dj] = True
    comp, frontier = list(donors), list(donors)
    while frontier and int(visited.sum()) < max_atoms:
        nf = []
        for a in frontier:
            dd = np.linalg.norm(IMG - IMG[a], axis=1)
            hit = np.where((dd > 0.3) & (dd <= (rcov_vec + rcov_vec[a]) * _TOL)
                           & notmetal & (~visited))[0]
            for j in hit:
                visited[j] = True; comp.append(int(j)); nf.append(int(j))
        frontier = nf
    order = [mi] + sorted(comp, key=lambda j: d[j])
    lines = [str(len(order)), "crystal full complex"]
    for j in order:
        x, y, z = IMG[j]
        lines.append(f"{IE[j]} {x:.4f} {y:.4f} {z:.4f}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1", help="i/N")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--bundle", default="benchmark_bundle")
    ap.add_argument("--cif-root", default=None)
    ap.add_argument("--out", default=None)
    cfg = ap.parse_args()
    cif_root = cfg.cif_root or os.environ.get("MECOBI_CIF_ROOT") or _DEFAULT_CIF_ROOT
    if not cif_root or not os.path.isdir(cif_root):
        raise SystemExit(f"CIF root not found: {cif_root} (pass --cif-root)")
    i, n = (int(x) for x in cfg.shard.split("/"))
    out = Path(cfg.out) if cfg.out else HERE / f"_cores_shard{i}of{n}.json"
    done = json.loads(out.read_text()) if out.exists() else {}

    recs = [r for k, r in enumerate(_bundle(cfg.bundle)) if k % n == i]
    if cfg.limit:
        recs = recs[:cfg.limit]

    got = skipped = missing = fail = 0
    for k, r in enumerate(recs, 1):
        rc = r["refcode"]
        if rc in done:
            continue
        folder = SYM2NAME.get(r["metal"])
        cifs = glob.glob(f"{cif_root}/{folder}/{rc}.*.cif") if folder else []
        if not cifs:
            missing += 1
            continue
        if is_placeholder(cifs[0]):
            skipped += 1
            continue
        try:
            core = depth2_core(Path(cifs[0]).read_text(errors="ignore"), r["metal"], r["cn"])
        except Exception:
            core = None
        if not core:
            fail += 1
            continue
        done[rc] = core
        got += 1
        if got % 500 == 0:
            out.write_text(json.dumps(done))
            print(f"  [{k}/{len(recs)}] got={got} missing={missing} placeholder={skipped} "
                  f"fail={fail}", flush=True)
    out.write_text(json.dumps(done))
    print(f"shard {i}/{n}: cores={len(done)} (+{got})  missing={missing} "
          f"placeholder-skipped={skipped} parse-fail={fail}  -> {out}")


if __name__ == "__main__":
    main()
