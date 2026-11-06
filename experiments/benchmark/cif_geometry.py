"""Self-contained CIF -> experimental coordination-sphere extractor (benchmark
scoring side). Hand-rolled fractional->cartesian + space-group symmetry expansion
(no gemmi/ase); finds the metal and its donors by covalent-radius contact.
Returns metal + donor cartesian positions to score MeCoBi builds against the crystal.
"""
from __future__ import annotations

import math
import re

import numpy as np

SYM2NAME = {
    "Bi": "Bismuth", "Cd": "Cadmium", "Ce": "Cerium", "Cr": "Chromium", "Co": "Cobalt",
    "Cu": "Copper", "Dy": "Dysprosium", "Er": "Erbium", "Eu": "Europium", "Gd": "Gadolinium",
    "Ga": "Gallium", "Ge": "Germanium", "Au": "Gold", "Hf": "Hafnium", "Ho": "Holmium",
    "In": "Indium", "Ir": "Iridium", "Fe": "Iron", "La": "Lanthanum", "Pb": "Lead",
    "Lu": "Lutetium", "Mn": "Manganese", "Hg": "Mercury", "Mo": "Molybdenum", "Nd": "Neodymium",
    "Ni": "Nickel", "Nb": "Niobium", "Os": "Osmium", "Pd": "Palladium", "Pt": "Platinum",
    "Pr": "Praseodymium", "Re": "Rhenium", "Rh": "Rhodium", "Ru": "Ruthenium", "Sm": "Samarium",
    "Sc": "Scandium", "Ag": "Silver", "Ta": "Tantalum", "Tc": "Technetium", "Tb": "Terbium",
    "Tl": "Thallium", "Tm": "Thulium", "Sn": "Tin", "Ti": "Titanium", "W": "Tungsten",
    "V": "Vanadium", "Yb": "Ytterbium", "Y": "Yttrium", "Zn": "Zinc", "Zr": "Zirconium",
}

_ELEM = re.compile(r"^([A-Z][a-z]?)")
_NUM = re.compile(r"[-+]?\d*\.?\d+")
_PT = None


def _rcov(el):
    global _PT
    if _PT is None:
        from rdkit.Chem import GetPeriodicTable
        _PT = GetPeriodicTable()
    try:
        r = _PT.GetRcovalent(el)
        return r if r and r > 0 else 0.77
    except Exception:
        return 0.77


def element_of(sym):
    m = _ELEM.match(sym or "")
    return m.group(1) if m else None


def _f(x):
    m = _NUM.match(x.strip())
    return float(m.group()) if m else None


def parse_loops(text):
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        if lines[i].strip() == "loop_":
            i += 1
            tags = []
            while i < n and lines[i].lstrip().startswith("_"):
                tags.append(lines[i].strip()); i += 1
            rows = []
            while i < n:
                s = lines[i].strip()
                if not s or s.startswith(("_", "#", "loop_", "data_", ";")):
                    break
                toks = s.split()
                if len(toks) == len(tags):
                    rows.append(toks)
                i += 1
            yield tags, rows
        else:
            i += 1


def _cart_matrix(a, b, c, al, be, ga):
    al, be, ga = map(math.radians, (al, be, ga))
    ca, cb, cg, sg = math.cos(al), math.cos(be), math.cos(ga), math.sin(ga)
    v = math.sqrt(max(1e-9, 1 - ca * ca - cb * cb - cg * cg + 2 * ca * cb * cg))
    return np.array([[a, b * cg, c * cb],
                     [0.0, b * sg, c * (ca - cb * cg) / sg],
                     [0.0, 0.0, c * v / sg]])


def _parse_symop(s):
    R = np.zeros((3, 3)); t = np.zeros(3)
    for i, part in enumerate(s.lower().replace(" ", "").split(",")):
        for m in re.finditer(r"([+-]?\d+/\d+|[+-]?\d*\.\d+|[+-]?\d+)(?![xyz/\d.])", part):
            frac = m.group()
            if "/" in frac:
                num, den = frac.split("/"); t[i] += float(num) / float(den)
            else:
                t[i] += float(frac)
        for ax, col in (("x", 0), ("y", 1), ("z", 2)):
            m = re.search(r"([+-]?)(\d*)" + ax, part)
            if m:
                sign = -1.0 if m.group(1) == "-" else 1.0
                coef = float(m.group(2)) if m.group(2) else 1.0
                R[i, col] += sign * coef
    return R, t


def _cell_and_atoms(text):
    cell = {}
    for tag in ("a", "b", "c"):
        m = re.search(rf"_cell_length_{tag}\s+([-\d.]+)", text)
        if m:
            cell[tag] = float(m.group(1))
    for tag in ("alpha", "beta", "gamma"):
        m = re.search(rf"_cell_angle_{tag}\s+([-\d.]+)", text)
        if m:
            cell[tag] = float(m.group(1))
    if len(cell) < 6:
        return None, None, None
    M = _cart_matrix(cell["a"], cell["b"], cell["c"], cell["alpha"], cell["beta"], cell["gamma"])
    elems, fracs, symops = [], [], []
    for tags, rows in parse_loops(text):
        if any(("_symmetry_equiv_pos_as_xyz" in t or "_space_group_symop_operation_xyz" in t)
               for t in tags):
            ci = next(i for i, t in enumerate(tags) if "xyz" in t and ("symop" in t or "equiv" in t))
            for r in rows:
                symops.append(_parse_symop(" ".join(r[ci:]).strip("'\"")))
        if ("_atom_site_fract_x" in tags and "_atom_site_type_symbol" in tags
                and "_atom_site_label" in tags):
            lx, ly, lz = (tags.index(f"_atom_site_fract_{a}") for a in "xyz")
            ti = tags.index("_atom_site_type_symbol")
            for r in rows:
                fx, fy, fz = _f(r[lx]), _f(r[ly]), _f(r[lz])
                el = element_of(r[ti])
                if None in (fx, fy, fz) or not el:
                    continue
                elems.append(el); fracs.append((fx, fy, fz))
    if not fracs:
        return None, None, None
    if not symops:
        symops = [(np.eye(3), np.zeros(3))]
    return M, (elems, np.array(fracs)), symops


def coordination_sphere(text, metal_sym, target_cn):
    """(metal_xyz, donor_xyz[cn,3], donor_elements) = the metal + its ``target_cn``
    NEAREST non-H, non-same-metal atoms (symmetry-expanded crystal). Using the
    intended CN (from MetaLig) rather than a covalent-contact count keeps the
    experimental sphere the same size as the build's, so the metrics line up (a
    loose covalent cutoff over-counts eta-carbons / backbone atoms on big metals).
    Returns None if unparseable or fewer than target_cn neighbours exist."""
    M, atoms, symops = _cell_and_atoms(text)
    if M is None:
        return None
    elems, fracs = atoms
    metal_idx = [i for i, e in enumerate(elems) if e == metal_sym]
    if not metal_idx:
        return None
    trans = [np.array([i, j, k]) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)]
    imgs_xyz = []
    for R, t in symops:
        g = fracs @ R.T + t
        for tr in trans:
            imgs_xyz.append((g + tr) @ M.T)
    IMG = np.vstack(imgs_xyz)
    IE = elems * (len(IMG) // len(elems))
    mc = fracs[metal_idx[0]] @ M.T
    d = np.linalg.norm(IMG - mc, axis=1)
    cand = sorted((float(d[j]), j) for j in range(len(IMG))
                  if d[j] > 0.5 and IE[j] not in ("H", metal_sym))
    if len(cand) < target_cn:
        return None
    idx = [j for _, j in cand[:target_cn]]
    return (mc.tolist(), [IMG[j].tolist() for j in idx], [IE[j] for j in idx])


def coordination_sphere_by_elements(text, metal_sym, donor_elements):
    """(metal_xyz, donor_xyz, donor_elements) where the donors are, for each element in
    ``donor_elements`` (the bundle's declared donor atoms, a multiset), that many NEAREST atoms of
    that element -- H included when a declared donor is H (H2, agostic B-H/C-H).

    :func:`coordination_sphere` takes the cn nearest non-H atoms whatever their element, so when a
    declared donor is an H, or sits slightly farther than a backbone atom, the next-nearest atom
    (usually a C ~3 A away) stands in for it. Symmetry images that coincide (a metal on a special
    position) are deduplicated first, so one physical donor is never counted twice. None if the
    CIF is unparseable or holds too few atoms of some declared element."""
    from collections import Counter

    M, atoms, symops = _cell_and_atoms(text)
    if M is None:
        return None
    elems, fracs = atoms
    metal_idx = [i for i, e in enumerate(elems) if e == metal_sym]
    if not metal_idx:
        return None
    trans = [np.array([i, j, k]) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)]
    imgs_xyz = []
    for R, t in symops:
        g = fracs @ R.T + t
        for tr in trans:
            imgs_xyz.append((g + tr) @ M.T)
    IMG = np.vstack(imgs_xyz)
    IE = elems * (len(IMG) // len(elems))
    mc = fracs[metal_idx[0]] @ M.T
    d = np.linalg.norm(IMG - mc, axis=1)
    near = np.where((d > 0.5) & (d < 6.0))[0]
    seen, cand = set(), []
    for j in near[np.argsort(d[near])]:
        key = (IE[j], *np.round(IMG[j], 1))
        if key not in seen and IE[j] != metal_sym:
            seen.add(key)
            cand.append(int(j))
    pos, els = [], []
    for el, n in Counter(donor_elements).items():
        pick = [j for j in cand if IE[j] == el][:n]
        if len(pick) < n:
            return None
        pos += [IMG[j].tolist() for j in pick]
        els += [el] * n
    order = np.argsort([np.linalg.norm(np.asarray(p) - mc) for p in pos])
    return mc.tolist(), [pos[k] for k in order], [els[k] for k in order]
