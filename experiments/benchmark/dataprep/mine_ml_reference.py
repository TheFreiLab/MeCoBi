"""Rebuild MeCoBi's M-L distance reference (src/mecobi/data/ml_reference.json) from every local CIF.

The shipped table came from an early-stopped miner run (tmp_cifreview_fixed/mine_bond_lengths.py)
and was assembled from a different snapshot than that run's output: Zr, for one, kept only
Zr|C / Zr|N / Zr|C_sp, so Zr-Cl/O/N fell back to covalent-radius sums 0.25-0.35 A too long. Its
oxidation states came from FilteredOS ``Extracted_Symbols`` alone -- the formal charge written on
the metal in the CSD SMILES, which is not an oxidation state when ligands are drawn covalently
([ZrF6]2- gave Zr|-2 bins).

This miner reads EVERY CIF (no early stop) and keeps the three-level binning and the CN
definition of the original (non-H ``_geom_bond`` contacts of the metal atom):

    metal|OS|donor|CN   metal|OS|donor   metal|donor

Carbon donors are split as MeCoBi looks them up (optimize._donor_key): an sp carbon (carbonyl,
cyanide, isocyanide: its only listed non-metal neighbour an O/N within 1.30 A) goes to ``C_sp``,
every other carbon to ``C``. The old ``C`` bins averaged both, and with correct oxidation states
the carbonyl-rich low-valent bins are CO-dominated (Mo(0) C CN6 2.01 A), so an aryl / alkyl /
carbene on those metals would be held at a carbonyl distance.

An oxidation state is used only when it is CONSISTENT and shows no sign of a lost hydride:
  * from mecobi_ready_<M>.csv, every row of the refcode giving one OS value, each row either
    ``os_confidence == "high"`` (charge-balance OS == CSD-annotated FilteredOS) or, with
    ``--os-source derived`` (the default), FilteredOS-silent (``unchecked``) with clean ligand
    charges (``charge_ok == "Y"``); a FilteredOS ``mismatch`` always excludes the refcode.
    ``--os-source agree`` keeps only the agreeing rows: most conservative, but the CSD seldom
    writes a metal charge for early metals or Ir (8 Zr, 22 Ir structures), so their OS bins
    vanish and Ir(III)-C falls back to a Cp*/aryl mix (2.12 vs 2.02 A);
  * no hapto-bonded ligand (two of the metal's bonded atoms bonded to each other): the charge
    balance counts an eta-Cp / allyl / arene carbon by carbon (Cp2ZrCl2 -> "Zr(12)", ferrocenes
    -> "Fe(8-10)"), and a plausible-looking wrong value (CpFe(CO)2Cl -> "Fe(6)") cannot be
    caught by range, so these never give an OS;
  * the OS within -2..MAX_OS of the metal (a safety net for any other extraction error);
  * no hydride evidence (a lost H- lowers the OS by one in both sources): no located M-H in the
    CIF (scan_hydrides.located) and not an odd / low-rare OS (scan_hydrides.os_flags).
Any other structure still feeds the OS-independent metal|donor bins.

``--os-source consensus`` takes the OS from xyz2mol_tm instead (Jensen group,
https://github.com/jensengroup/xyz2mol_tm, ``csd_smiles.csv``, ~230k CSD refcodes; not in git,
63 MB): the metal's formal charge in its dative-bond SMILES, used only where the CSD-API-derived
and the Hückel-from-coordinates SMILES agree. Where the charge balance above also gives an OS it
must match, except for hapto complexes, where the charge balance is known wrong and xyz2mol
decides alone; a located M-H is no reason to drop the OS when xyz2mol drew the hydride. xyz2mol
has no p-block metals, so those keep the ``agree`` rule.

A hapto carbon (a carbon donor bonded to a fellow donor: Cp / arene / alkene / allyl C) is its
own class, ``C_eta``, at all three levels, as MeCoBi looks it up (optimize._donor_key): mixed
into ``C`` it pulled Ru(II)-C to 2.20 A and Ir(III)-C to 2.12 A, against sigma-carbon 2.05 /
2.02 A, and left OUT of the OS bins a Cp carbon was looked up under the sigma value instead
(Ti(IV)-C(Cp) 0.2 A short; pilot A/B: haptic complexes 22 better / 40 worse). Any other hapto
atom (side-on N-N, O-O) still feeds only the metal|donor bins.

A bin's ``n`` counts bonds, so a few structures can fill it; OS bins are emitted only with
>= MIN_STRUCT_OS distinct structures (``n_struct`` is stored). f-block metals (out of scope; xtb
is skipped for them) are copied from the current table unchanged, with their C_sp bins
(mine_sp_carbon_reference.py); the mined metals' C_sp bins come from the CIFs here.

    python dataprep/mine_ml_reference.py                  # writes ml_reference.json + a report
    python dataprep/mine_ml_reference.py --dry-run        # report only
    python dataprep/mine_ml_reference.py --os-source consensus
        --report dataprep/ml_reference_consensus_report.json     # (one command; the shipped table)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]
REPO = BENCH.parents[1]
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(BENCH / "dataprep"))
sys.path.insert(0, str(REPO / "src"))

from cif_geometry import SYM2NAME  # noqa: E402
from scan_hydrides import located, os_flags  # noqa: E402

from mecobi.inputs import is_f_block  # noqa: E402

# No built-in defaults: pass --cif-root / --ready-root or set the environment variables.
CIF_ROOT = os.environ.get("MECOBI_CIF_ROOT")
READY_ROOT = os.environ.get("MECOBI_READY_ROOT")
TABLE = REPO / "src" / "mecobi" / "data" / "ml_reference.json"
LEVELS = ("metal_os_donor_cn", "metal_os_donor", "metal_donor")
MIN_STRUCT_OS = 5        # distinct structures before an OS bin is emitted
MIN_STRUCT_COARSE = 3    # ... before a metal|donor bin is emitted
NO_DONOR = {"H", "D"}    # hydride / deuteride contacts never enter a bin (as in the original)
SP_CARBON = "C_sp"       # optimize.SP_CARBON
ETA_CARBON = "C_eta"     # optimize.ETA_CARBON
# Highest oxidation state each metal reaches (group valence; Fe/Ru/Os/Ir/Pt/Au per known
# compounds). Outside -2..MAX_OS the charge-balance OS is an extraction error.
MAX_OS = {"Sc": 3, "Y": 3, "Ti": 4, "Zr": 4, "Hf": 4, "V": 5, "Nb": 5, "Ta": 5, "Cr": 6, "Mo": 6,
          "W": 6, "Mn": 7, "Tc": 7, "Re": 7, "Fe": 6, "Ru": 8, "Os": 8, "Co": 5, "Rh": 6,
          "Ir": 6, "Ni": 4, "Pd": 4, "Pt": 6, "Cu": 4, "Ag": 3, "Au": 5, "Zn": 2, "Cd": 2,
          "Hg": 2, "Ga": 3, "In": 3, "Tl": 3, "Ge": 4, "Sn": 4, "Pb": 4, "Bi": 5}
SP_PARTNER_MAX = 1.30    # A: optimize._SP_PARTNER_MAX (C#O / C#N 1.13-1.18; C=O, C=N >= 1.20)

_ELEM_RE = re.compile(r"^([A-Z][a-z]?)")
_DIST_RE = re.compile(r"^\d+(\.\d+)?")


def parse_loops(text):
    """Yield (tags, rows) for every ``loop_`` block; wrapped / malformed rows are skipped."""
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        if lines[i].strip() == "loop_":
            i += 1
            tags = []
            while i < n and lines[i].lstrip().startswith("_"):
                tags.append(lines[i].strip())
                i += 1
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


def cif_bonds(text, metal):
    """``[(donor_key, cn, distance)]`` from the deposited ``_geom_bond`` loop, per metal atom
    (CN = its non-H bonded contacts, as in the original miner). ``donor_key`` is the element,
    or ``C_sp`` for a carbon whose ONLY listed non-metal, non-H neighbour is an O or N within
    ``SP_PARTNER_MAX`` (carbonyl, cyanide, isocyanide) -- the class optimize._donor_key looks
    up, so the ``C`` bins hold only the carbons that are looked up as ``C``."""
    label2el, bonds = {}, None
    for tags, rows in parse_loops(text):
        if "_atom_site_label" in tags and "_atom_site_type_symbol" in tags:
            li, ti = tags.index("_atom_site_label"), tags.index("_atom_site_type_symbol")
            for r in rows:
                m = _ELEM_RE.match(r[ti])
                if m:
                    label2el[r[li]] = m.group(1)
        if all(t in tags for t in ("_geom_bond_atom_site_label_1",
                                   "_geom_bond_atom_site_label_2", "_geom_bond_distance")):
            a1 = tags.index("_geom_bond_atom_site_label_1")
            a2 = tags.index("_geom_bond_atom_site_label_2")
            di = tags.index("_geom_bond_distance")
            bonds = [(r[a1], r[a2], r[di]) for r in rows]
    if not label2el or bonds is None:
        return [], False
    metals = {lab for lab, el in label2el.items() if el == metal}
    per = {m: [] for m in metals}
    nbr = defaultdict(list)
    for l1, l2, dtxt in bonds:
        m = _DIST_RE.match(dtxt)
        if not m:
            continue
        d = float(m.group())
        nbr[l1].append((l2, d))
        nbr[l2].append((l1, d))
        for a, b in ((l1, l2), (l2, l1)):
            if a in metals and b not in metals:
                el = label2el.get(b)
                if el and el not in NO_DONOR:
                    per[a].append((b, el, d))

    def key(lab, el):
        if el != "C":
            return el
        partners = [(x, d) for x, d in nbr[lab]
                    if x not in metals and label2el.get(x) not in NO_DONOR]
        if (len(partners) == 1 and label2el.get(partners[0][0]) in ("O", "N")
                and partners[0][1] <= SP_PARTNER_MAX):
            return SP_CARBON
        return el

    donor_labels = {lab for dl in per.values() for lab, _, _ in dl}
    eta = {lab for lab in donor_labels if any(x in donor_labels for x, _ in nbr[lab])}
    def cls(lab, el):   # a hapto carbon is its own class; an sp carbon keeps C_sp
        k = key(lab, el)
        return ETA_CARBON if k == "C" and lab in eta else k

    obs = [(cls(lab, el), len(dl), d, lab in eta) for dl in per.values() for lab, el, d in dl]
    return obs, bool(eta)


def load_os(sym, source="derived", ready_root=None):
    """refcode -> OS, where every row of the refcode qualifies and all give one OS value.

    ``agree``: os_confidence=high (charge-balance OS == FilteredOS). ``derived``: also the
    charge-balance OS of clean rows (charge_ok=Y) that FilteredOS does not cover; a mismatch
    with FilteredOS still excludes the refcode."""
    f = Path(ready_root or READY_ROOT) / f"mecobi_ready_{sym}.csv"
    rows = defaultdict(list)
    if f.exists():
        with open(f, newline="", encoding="utf-8", errors="ignore") as fh:
            for r in csv.DictReader(fh):
                rows[r["Name"].strip().upper()].append(r)
    out = {}
    for ref, rs in rows.items():
        ok = (lambda r: r.get("os_confidence") == "high") if source == "agree" else (
            lambda r: r.get("os_confidence") == "high"
            or (r.get("os_confidence") == "unchecked" and r.get("charge_ok") == "Y"))
        if all(ok(r) for r in rs):
            vals = {r.get("OxidationState") for r in rs}
            if len(vals) == 1:
                try:
                    ox = float(vals.pop())
                except (TypeError, ValueError):
                    continue
                if ox.is_integer():
                    out[ref] = int(ox)
    return out


_BRACKET = re.compile(r"\[(\d*)([A-Z][a-z]?)(@{0,2})(H\d*)?([+-]+\d*)?(:\d+)?\]")


def _charge(tok):
    if not tok:
        return 0
    sign = 1 if tok[0] == "+" else -1
    return sign * (int(tok[1:]) if tok[1:].isdigit() else len(tok))


def _smiles_metal(smi, metals):
    """``(metal, formal charge, n_hydride)`` if the SMILES holds exactly one metal atom."""
    if not isinstance(smi, str):
        return None
    hits, nh = [], 0
    for m in _BRACKET.finditer(smi):
        el, q = m.group(2), _charge(m.group(5))
        if el in metals:
            hits.append((el, q, m.group(4)))
        elif el == "H" and q == -1:
            nh += 1
    if len(hits) != 1:
        return None
    el, q, hcount = hits[0]
    if hcount:                                   # [IrH2+3]: hydrides written on the metal
        nh += int(hcount[1:] or 1)
    return el, q, nh


def load_xyz2mol(path, metals):
    """symbol -> {refcode: (OS, n_hydride)} from xyz2mol_tm's csd_smiles.csv, where the metal's
    formal charge (its OS: ligands carry their own charges, donor bonds are dative) is the same
    in the CSD-API-derived and the Hückel-from-coordinates SMILES."""
    out = defaultdict(dict)
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            a = _smiles_metal(r["smiles_csd_api_fixed"], metals)
            b = _smiles_metal(r["huckel_smiles_CSD_xyz"], metals)
            if a and b and a[0] == b[0] and a[1] == b[1]:
                out[a[0]][r["IDs"].strip().upper()] = (a[1], max(a[2], b[2]))
    return out


def mine_metal(args):
    """All CIFs of one metal -> {level: {key: [n, mean, M2, set(refcodes)]}} plus counters."""
    sym, folder, source, xtab, ready = args
    if source == "consensus":
        ours = load_os(sym, "derived" if xtab else "agree", ready)
    else:
        ours = load_os(sym, source, ready)
    acc = {lv: {} for lv in LEVELS}
    stats = defaultdict(int)

    def add(lv, key, d, ref):
        a = acc[lv].setdefault(key, [0, 0.0, 0.0, set()])
        a[0] += 1
        delta = d - a[1]
        a[1] += delta / a[0]
        a[2] += delta * (d - a[1])
        a[3].add(ref)

    for path in sorted(Path(folder).glob("*.cif")):
        ref = path.name.split(".")[0].upper()
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            stats["unreadable"] += 1
            continue
        obs, haptic = cif_bonds(text, sym)
        if not obs:
            stats["no_bonds"] += 1
            continue
        stats["used"] += 1
        ox = ours.get(ref, ours.get(re.sub(r"\d+$", "", ref)))
        x = None
        if source == "consensus" and xtab:
            x = xtab.get(ref, xtab.get(re.sub(r"\d+$", "", ref)))
            if x is None:
                if ox is not None:
                    stats["os_dropped_no_xyz2mol"] += 1
                ox = None
            elif haptic or ox is None or ox == x[0]:
                # hapto ligands: the charge balance is known wrong there, xyz2mol alone decides
                stats["os_from_xyz2mol_only" if ox is None or haptic and ox != x[0]
                      else "os_consensus"] += 1
                ox = x[0]
            else:
                stats["os_dropped_disagree"] += 1
                ox = None
        elif ox is not None and haptic:
            stats["os_dropped_haptic"] += 1
            ox = None
        if ox is not None and not -2 <= ox <= MAX_OS.get(sym, 8):
            stats["os_dropped_range"] += 1
            ox = None
        if ox is not None:
            if any(os_flags(sym, ox)):
                stats["os_dropped_odd"] += 1
                ox = None
            else:
                try:
                    res = located(text, sym)
                except Exception:  # noqa: BLE001 -- unparseable cell: cannot rule a hydride out
                    res = None
                # a located M-H is fine when xyz2mol drew the hydride (its OS then counts it)
                if res is None or (res[1] and not (x and x[1] >= len(res[1]))):
                    stats["os_dropped_hydride" if res else "os_dropped_unparsed"] += 1
                    ox = None
        if ox is not None:
            stats["os_used"] += 1
        for el, cn, d, eta in obs:
            add("metal_donor", f"{sym}|{el}", d, ref)
            # a hapto carbon has its own class (C_eta); any other hapto atom (side-on N-N,
            # O-O) is no sigma bond of its element, so it stays out of the OS bins
            if ox is not None and (not eta or el == ETA_CARBON):
                add("metal_os_donor", f"{sym}|{ox}|{el}", d, ref)
                add("metal_os_donor_cn", f"{sym}|{ox}|{el}|{cn}", d, ref)
    out = {lv: {k: (n, mean, m2, len(refs)) for k, (n, mean, m2, refs) in tab.items()}
           for lv, tab in acc.items()}
    return sym, out, dict(stats)


def entry(n, mean, m2, n_struct):
    sd = math.sqrt(m2 / (n - 1)) if n > 1 else 0.0
    return {"mean": round(mean, 4), "n": n, "sd": round(sd, 4),
            "sem": round(sd / math.sqrt(n), 4), "n_struct": n_struct}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--metals", nargs="*", help="element symbols (default: every non-f-block)")
    ap.add_argument("--dry-run", action="store_true", help="write the report, not the table")
    ap.add_argument("--os-source", choices=("agree", "derived", "consensus"), default="derived",
                    help="which oxidation states to trust (see load_os; consensus: xyz2mol_tm)")
    ap.add_argument("--xyz2mol", default=str(REPO / "csd_smiles.csv"),
                    help="xyz2mol_tm csd_smiles.csv, for --os-source consensus")
    ap.add_argument("--cif-root", default=CIF_ROOT, required=CIF_ROOT is None,
                    help="folder with one sub-folder of CIFs per metal (element name); "
                         "env MECOBI_CIF_ROOT")
    ap.add_argument("--ready-root", default=READY_ROOT, required=READY_ROOT is None,
                    help="folder with the mecobi_ready_<M>.csv ligand-charge files; "
                         "env MECOBI_READY_ROOT")
    ap.add_argument("--out", default=str(TABLE), help="table to write")
    ap.add_argument("--report", default=str(BENCH / "dataprep" / "ml_reference_rebuild.json"))
    a = ap.parse_args()

    name2sym = {v: k for k, v in SYM2NAME.items()}
    xyz2mol = {}
    if a.os_source == "consensus":
        xyz2mol = load_xyz2mol(a.xyz2mol, set(name2sym.values()))
        print("xyz2mol OS (both SMILES agree):",
              {s: len(v) for s, v in sorted(xyz2mol.items())}, flush=True)
    jobs = []
    for d in sorted(p for p in Path(a.cif_root).iterdir() if p.is_dir()):
        sym = name2sym.get(d.name)
        if sym and not is_f_block(sym) and (not a.metals or sym in a.metals):
            jobs.append((sym, str(d), a.os_source, xyz2mol.get(sym), a.ready_root))
    print(f"mining {len(jobs)} metals with {a.workers} workers", flush=True)

    old = json.loads(TABLE.read_text())
    new = {lv: {} for lv in LEVELS}
    report = {}
    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        for sym, tabs, stats in ex.map(mine_metal, jobs):
            for lv in LEVELS:
                floor = MIN_STRUCT_COARSE if lv == "metal_donor" else MIN_STRUCT_OS
                for k, (n, mean, m2, ns) in tabs[lv].items():
                    if ns >= floor:
                        new[lv][k] = entry(n, mean, m2, ns)
            report[sym] = stats
            print(f"  {sym:3s} {stats} ({time.time() - t0:.0f}s)", flush=True)

    mined = {j[0] for j in jobs}
    for lv in LEVELS:                                  # carry over the unmined (f-block) metals
        for k, v in old[lv].items():
            if k.split("|")[0] not in mined:
                new[lv].setdefault(k, v)

    Path(a.report).write_text(json.dumps({"stats": report}, indent=1))
    if not a.dry_run:
        Path(a.out).write_text(json.dumps({lv: dict(sorted(new[lv].items())) for lv in LEVELS},
                                          indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {a.out}")
    print(f"done in {time.time() - t0:.0f}s; report {a.report}")


if __name__ == "__main__":
    main()
