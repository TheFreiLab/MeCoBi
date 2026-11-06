"""Hydride corrections for the benchmark -- the CSD-mined inputs carry NO hydrides (0 of 35 956
entries), so a hydrido complex enters with its CN too low and its oxidation state one unit too
low per lost H- (see dataprep/scan_hydrides.py). Where the CIF LOCATES the M-H, this module puts
it back, the same way bench_overrides.py applies its spot fixes: the frozen bundle / spheres /
cores stay immutable and benchmark_hydrides.json (dataprep/build_hydride_corrections.py) is
layered on top at run / score time.

Per refcode the file holds ``{n_h, class, h_rel, mh, ox, cn, target}``:
  ``h_rel``   crystal M->H vectors (A, crystal cartesian frame, metal at the origin);
  ``ox/cn``   the corrected values (mined + n_h);
  ``target``  the geometry + site map re-read from the crystal WITH the hydride as a donor
              (enrich_bundle_geometry.target_for), or absent when no donor row exists;
  ``class``   clean (1-2 H, corrected CN <= 6) | high_cn (1-2 H, CN >= 7) | polyhydride (>= 3 H)
              | h2_mixed (an eta2-H2 next to the hydride) | short_mh (an M-H below 1.2 A).
              Only ``clean`` is applied by default.

A hydride is an H within MH_MAX of the metal that is bonded to nothing else: no non-metal atom
within the covalent-radius bond cutoff (never tighter than 1.25 A). The same test finds the
hydrides of a BUILT structure, so crystal and build spheres are extended like-for-like.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from extract_cores import rcov

HERE = Path(__file__).parent
MH_MAX = 2.0          # A: a located hydride sits within this of the metal (crystal)
MH_MAX_BUILD = 3.0    # A: looser on a build, so a hydride xtb pushed out is scored, not dropped
XH_TOL = 1.30         # bonded if dist <= (rcov(X) + rcov(H)) * XH_TOL ...
XH_MIN = 1.25         # ... and never tighter than this (also the H-H / eta2-H2 cutoff)
DEFAULT_CLASSES = ("clean",)


def metal_only_h(E, X, mc, metals=(), mh_max=MH_MAX, keep_hh=False):
    """H atoms bonded to the metal alone, nearest first: ``(indices into X, n_h2)``.

    ``E``/``X`` elements + cartesian positions (a symmetry-expanded crystal, or a built .xyz),
    ``mc`` the metal position, ``metals`` the symbols that do not make an H a ligand hydrogen
    (a bridging M-H-M still counts). An H whose only bonded neighbour is another H is a possible
    eta2-H2 -- counted in ``n_h2``, not returned (``keep_hh`` returns it as a hydride anyway: on
    a build, where the hydride count is known, a hydride clashing with a ligand H is still the
    hydride). Coincident symmetry images are deduplicated."""
    E = np.asarray(E)
    X = np.asarray(X, float)
    d = np.linalg.norm(X - np.asarray(mc, float), axis=1)
    out, seen, n_h2 = [], [], 0
    for j in np.argsort(d):
        if d[j] >= mh_max:
            break
        if E[j] != "H" or d[j] <= 0.5:
            continue
        if any(np.linalg.norm(X[j] - s) < 0.05 for s in seen):   # symmetry duplicate
            continue
        seen.append(X[j])
        dn = np.linalg.norm(X - X[j], axis=1)
        partners = [E[k] for k in np.where((dn > 0.05) & (dn < 2.0))[0]
                    if E[k] not in metals and dn[k] <= (
                        XH_MIN if E[k] == "H" else max(XH_MIN, (rcov(E[k]) + rcov("H")) * XH_TOL))]
        if not partners or (keep_hh and set(partners) == {"H"}):
            out.append(int(j))
        elif set(partners) == {"H"}:
            n_h2 += 1
    return out, n_h2


def build_hydrides(syms, P, mi, n_h):
    """Indices of the ``n_h`` hydrides of a built structure (metal-only H nearest the metal);
    fewer than ``n_h`` when the build carries none (built from the uncorrected inputs)."""
    if n_h <= 0:
        return []
    idx, _ = metal_only_h(syms, P, P[mi], metals={syms[mi]}, mh_max=MH_MAX_BUILD, keep_hh=True)
    return idx[:n_h]


# ---------------------------------------------------------------------------
# the correction file, layered over the frozen bundle / spheres / cores
# ---------------------------------------------------------------------------
def load(path: str = "benchmark_hydrides.json", classes=DEFAULT_CLASSES) -> dict:
    """``{refcode: correction}`` restricted to ``classes`` (None = all); {} if the file is absent."""
    p = Path(path) if Path(path).is_absolute() else HERE / path
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {rc: h for rc, h in data.items() if classes is None or h.get("class") in classes}


def record(r: dict, h: dict | None) -> dict:
    """Bundle record with the located hydrides added as ``[H-]`` ligands (copy)."""
    if not h:
        return r
    n = h["n_h"]
    out = dict(r)
    out["ligands"] = list(r["ligands"]) + ["[H-]"] * n
    out["charges"] = list(r.get("charges") or []) + [-1] * n
    out["donor_elements"] = list(r.get("donor_elements") or []) + ["H"] * n
    out["ox"], out["cn"] = r["ox"] + n, r["cn"] + n
    return out


def donors(donors_row, h: dict | None):
    """Donor-index row extended with ``[0]`` per hydride (None stays None: pydentate path)."""
    if not h or donors_row is None:
        return donors_row
    return list(donors_row) + [[0]] * h["n_h"]


def sphere(exp: dict, h: dict | None) -> dict:
    """Crystal coordination sphere with the hydrides appended as donors (element ``H``)."""
    if not h:
        return exp
    m = np.asarray(exp["metal_xyz"], float)
    out = dict(exp)
    out["donors"] = list(exp["donors"]) + [(m + np.asarray(v, float)).tolist() for v in h["h_rel"]]
    out["donor_elements"] = (list(exp.get("donor_elements") or ["?"] * len(exp["donors"]))
                             + ["H"] * h["n_h"])
    return out


def core(c: dict, h: dict | None) -> dict:
    """Crystal depth-2 core with the hydrides appended to the donor shell."""
    if not h or not c:
        return c
    m = np.asarray(c["metal"]["xyz"], float)
    out = dict(c)
    out["donors"] = list(c["donors"]) + [{"el": "H", "xyz": (m + np.asarray(v, float)).tolist()}
                                         for v in h["h_rel"]]
    return out


def n_in_sphere(exp: dict) -> int:
    return sum(1 for e in (exp.get("donor_elements") or []) if e == "H")


def n_in_core(c: dict) -> int:
    return sum(1 for a in c["donors"] if a["el"] == "H")


def strip_sphere(exp: dict) -> dict:
    """The heavy-donor sphere again -- for scoring a build that carries no hydride."""
    keep = [i for i, e in enumerate(exp["donor_elements"]) if e != "H"]
    out = dict(exp)
    out["donors"] = [exp["donors"][i] for i in keep]
    out["donor_elements"] = [exp["donor_elements"][i] for i in keep]
    return out


def strip_core(c: dict) -> dict:
    out = dict(c)
    out["donors"] = [a for a in c["donors"] if a["el"] != "H"]
    return out
