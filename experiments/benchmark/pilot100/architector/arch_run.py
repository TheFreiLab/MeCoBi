"""Architector counterpart to run.py: generate the SAME benchmark complexes with
LANL Architector (factory GFN2-xTB defaults) so we can compare generation time,
success rate, and (later) structural fidelity against MeCoBi head-to-head.

Runs in the **architector** conda env (NOT the MeCoBi env) -- imports `architector`
+ rdkit only, never `mecobi`. Reads the frozen bundle + ground-truth donors and,
by default, restricts to the frozen pilot list so both engines build the same set.

Fairness / method notes:
  * Donors are fed as Architector `coordList` from benchmark_donors.json -- the same
    ground-truth coordinating atoms MeCoBi gets via `donor_override`. This is exactly
    Architector's designed input regime (it takes coordinating atoms as user input;
    it does NOT auto-detect them), so neither tool is advantaged on donor perception.
  * metal_ox is passed explicitly (drives spin/charge). Everything else is left at
    Architector's shipped defaults: GFN2-xTB assemble + full method, relax on, the
    default conformer/symmetry search. That measures the tool "as it ships".
  * A cheap pre-flight gate asserts each coordList index really is the expected donor
    element (catches any SMILES-indexing mismatch before spending xTB time).
  * ``--targets`` gives Architector the crystal GEOMETRY (its ``coreType``), as molSimplify,
    MetalloGen and MeCoBi get it; without it Architector searches every core of the CN and keeps
    the lowest energy. ``--pin-sites`` also gives it the crystal ISOMER: the core is passed as
    MeCoBi's ideal site vectors (a user core, ``core.coordList``) and each donor is tied to its
    crystal site (``[atom, site]`` pairs), the input its own tests use. Haptic complexes (more
    donor atoms than sites) have no such input and keep the per-CN default, flagged. A level that
    fails falls back to the next (isomer -> geometry -> default); ``level`` records what was built.

    # one process:
    python pilot100/architector/arch_run.py --shard 0/1
    # parallel (Architector is slow at GFN2-xTB defaults -- shard across cores):
    for i in $(seq 0 7); do python pilot100/architector/arch_run.py --shard $i/8 & done; wait

Writes per-complex JSONL (_arch_results_shard*.jsonl) + lowest-energy .xyz into
arch_structures/. Resumable: re-running skips refcodes already recorded.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from collections import Counter
from pathlib import Path

from architector import build_complex

try:  # rdkit is only needed for the optional donor pre-flight gate, not by Architector
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
except ImportError:  # architector conda env often has no rdkit -- gate is skipped then
    Chem = None
HERE = Path(__file__).resolve().parent   # pilot100/architector/: results + arch_structures/
PILOT = HERE.parent                      # pilot100/: pilot_100.json + crystal targets
BENCH = PILOT.parent                     # benchmark root: frozen bundle + donors


def _load_json(path: Path):
    path = Path(path)
    if str(path).endswith(".gz"):
        return json.loads(gzip.open(path, "rt", encoding="utf-8").read())
    return json.loads(path.read_text(encoding="utf-8"))


def _load_bundle(name: str):
    for cand in (BENCH / f"{name}.json.gz", BENCH / f"{name}.json",
                 BENCH / "benchmark_bundle.json" / f"{name}.json"):
        if cand.exists():
            return _load_json(cand)
    raise SystemExit(f"bundle {name} not found near {BENCH}")


# MeCoBi geometry name -> Architector coreType(s) (architector/geometries.py). Architector has two
# bent cores and no 90-degree one: both are offered and it keeps the lower-energy build.
CORE_TYPE = {
    "linear": ["linear"], "bent": ["bent_109", "bent_120"],
    "trigonal_planar": ["trigonal_planar"], "square_planar": ["square_planar"],
    "tetrahedral": ["tetrahedral"], "square_pyramidal": ["square_pyramidal"],
    "trigonal_bipyramidal": ["trigonal_bipyramidal"], "octahedral": ["octahedral"],
    "pentagonal_bipyramidal": ["pentagonal_bipyramidal"],
    "square_antiprism": ["square_antiprismatic"], "dodecahedral": ["dodecahedral"],
    "tricapped_trigonal_prism": ["tricapped_trigonal_prismatic"],
}
CORE_RADIUS = 2.0   # Angstrom; length of the user-core site vectors (as in Architector's tests)


def _site_map(tg: dict, lig_donors) -> "list[list[int]] | None":
    """The crystal site of every donor, per ligand ('0:2,5;1:4,0,1,3', site order == donor
    order), or None when the target does not give one site per donor atom."""
    try:
        sm = {int(a): [int(x) for x in b.split(",")]
              for a, b in (part.split(":") for part in tg["site_map"].split(";"))}
        sites = [sm[k] for k in range(len(lig_donors))]
    except (KeyError, ValueError, AttributeError, TypeError):
        return None
    flat = [x for seg in sites for x in seg]
    if any(len(a) != len(b) for a, b in zip(sites, lig_donors)) or len(set(flat)) != len(flat):
        return None
    return sites


def input_levels(tg, lig_donors, pin: bool, vectors: dict) -> "tuple[list[str], bool]":
    """The inputs to try for a complex, most specific first, and whether it is haptic."""
    if not tg or not tg.get("geometry"):
        return ["default"], False
    n_donor = sum(len(d) for d in lig_donors)
    if tg.get("site_cn") is not None and tg["site_cn"] < n_donor:
        return ["default"], True
    levels = ["geometry"] if tg["geometry"] in CORE_TYPE else []
    if pin and len(vectors.get(tg["geometry"], ())) == n_donor \
            and _site_map(tg, lig_donors) is not None:
        levels.insert(0, "isomer")
    return levels + ["default"], False


def build_input(rec: dict, lig_donors: list[list[int]], level: str = "default", tg=None,
                vectors=None) -> "tuple[dict, str | None]":
    """Map a bundle record + per-ligand donor indices to an Architector inputDict.
    Returns (inputDict, error) -- error non-None means skip (donor sanity failed).
    ``level``: "default" (every core of the CN), "geometry" (the target's coreType) or "isomer"
    (MeCoBi's site vectors as a user core, each donor tied to its crystal site).

    Pre-flight gate (only when rdkit is importable -- the architector env may lack it):
    every coordList index must be in range, and the *multiset* of elements at all
    coordList indices must equal the bundle's donor_elements. (The bundle lists donors
    in crystal-enumeration order, NOT grouped per ligand, so we compare multisets
    globally rather than zipping element-by-element.)"""
    ligands = [{"smiles": smi, "coordList": list(idxs)}
               for smi, idxs in zip(rec["ligands"], lig_donors)]
    if Chem is not None:
        got = Counter()
        for smi, idxs in zip(rec["ligands"], lig_donors):
            mol = Chem.MolFromSmiles(smi)
            if mol is None:
                return {}, f"unparseable SMILES {smi!r}"
            for ix in idxs:
                if ix >= mol.GetNumAtoms():
                    return {}, f"coordList index {ix} out of range for {smi!r}"
                got[mol.GetAtomWithIdx(ix).GetSymbol()] += 1
        if got != Counter(rec["donor_elements"]):
            return {}, f"donor multiset {dict(got)} != bundle {dict(Counter(rec['donor_elements']))}"
    core = {"metal": rec["metal"], "coreCN": rec["cn"]}
    if level == "geometry":   # coreType alone: a coreCN next to it adds every core of that CN
        core = {"metal": rec["metal"], "coreType": list(CORE_TYPE[tg["geometry"]])}
    elif level == "isomer":
        core = {"metal": rec["metal"],
                "coordList": [[CORE_RADIUS * x for x in v] for v in vectors[tg["geometry"]]]}
        ligands = [{"smiles": smi, "coordList": [[a, s] for a, s in zip(idxs, sites)]}
                   for smi, idxs, sites in zip(rec["ligands"], lig_donors,
                                               _site_map(tg, lig_donors))]
    inp = {
        "core": core,
        "ligands": ligands,
        "parameters": {"metal_ox": rec["ox"], "return_timings": True},
    }
    return inp, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1", help="i/N")
    ap.add_argument("--bundle", default="benchmark_bundle",
                     help="bundle basename; default reads the committed benchmark_bundle.json.gz "
                          "(already holds the corrected 'v2' records).")
    ap.add_argument("--donors", default="benchmark_donors.json")
    ap.add_argument("--refcodes", default="pilot_100.json",
                     help="JSON list of refcodes to restrict to (the frozen pilot). "
                          "Pass '' to run the whole donors-mapped bundle.")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default=None, help="comma-separated refcodes to build.")
    ap.add_argument("--hydrides", default=None, metavar="FILE",
                     help="benchmark_hydrides.json (benchmark root): put back the hydrides the "
                          "mined inputs lost -- one [H-] ligand each, metal_ox and coreCN raised by "
                          "one per hydride (the correction run.py --hydrides gives MeCoBi).")
    ap.add_argument("--hydrides-only", action="store_true",
                     help="with --hydrides: build ONLY the corrected refcodes (the re-run that "
                          "replaces those rows of a finished run).")
    ap.add_argument("--targets", default=None,
                     help="benchmark_targets_*.json (relative to pilot100/): build the crystal "
                          "geometry per refcode instead of searching every core of the CN.")
    ap.add_argument("--pin-sites", action="store_true",
                     help="with --targets: also tie every donor to its crystal site (the isomer), "
                          "on MeCoBi's site vectors (mecobi_site_vectors.json).")
    ap.add_argument("--out-dir", default=None,
                     help="write the results JSONL + arch_structures/ into this dir (relative to "
                          "pilot100/architector/); default = pilot100/architector/ itself "
                          "(arch_hyd/ with --hydrides).")
    cfg = ap.parse_args()
    i, n = (int(x) for x in cfg.shard.split("/"))

    bundle = _load_bundle(cfg.bundle)
    donors = _load_json(BENCH / cfg.donors)
    keep = set(_load_json(PILOT / cfg.refcodes)) if cfg.refcodes else None
    only = {x.strip() for x in cfg.only.split(",") if x.strip()} if cfg.only else None
    if cfg.pin_sites and not cfg.targets:
        raise SystemExit("--pin-sites needs --targets")
    targets = _load_json(PILOT / cfg.targets if not Path(cfg.targets).is_absolute()
                         else cfg.targets) if cfg.targets else None
    vectors = _load_json(HERE / "mecobi_site_vectors.json") if cfg.pin_sites else {}
    hyd = {}
    if cfg.hydrides:
        sys.path.insert(0, str(BENCH))
        import hydrides as HY   # numpy only; imported lazily so a plain run needs nothing new
        hyd = HY.load(cfg.hydrides)
        if not hyd:
            raise SystemExit(f"--hydrides {cfg.hydrides}: no corrections loaded")

    base = (HERE / cfg.out_dir) if cfg.out_dir else (HERE / "arch_hyd" if cfg.hydrides else HERE)
    base.mkdir(parents=True, exist_ok=True)
    structures = base / "arch_structures"; structures.mkdir(exist_ok=True)
    out = base / f"_arch_results_shard{i}of{n}.jsonl"
    done = {json.loads(l)["refcode"] for l in out.read_text().splitlines()} if out.exists() else set()

    recs = [r for k, r in enumerate(bundle)
            if k % n == i and r["refcode"] in donors
            and (keep is None or r["refcode"] in keep)
            and (only is None or r["refcode"] in only)
            and (not cfg.hydrides_only or r["refcode"] in hyd)]
    if cfg.limit:
        recs = recs[:cfg.limit]

    fh = out.open("a", encoding="utf-8")
    built = 0
    t0 = time.perf_counter()
    for k, r in enumerate(recs, 1):
        rc = r["refcode"]
        if rc in done:
            continue
        h, lig_donors = hyd.get(rc), donors[rc]
        if h:                                             # located hydrides the mining lost
            r, lig_donors = HY.record(r, h), HY.donors(lig_donors, h)
        row = {"refcode": rc, "metal": r["metal"], "ox": r["ox"], "cn": r["cn"], "built": False}
        if h:
            row["hydrides_added"] = h["n_h"]
        # a hydride-corrected complex takes the target re-read WITH the H
        tg = None if targets is None else (h.get("target") if h else targets.get(rc))
        levels, haptic = input_levels(tg, lig_donors, cfg.pin_sites, vectors)
        if tg and tg.get("geometry"):
            row["target_geometry"] = tg["geometry"]
        if haptic:
            row["haptic_fallback"] = True
        ts = time.perf_counter()
        for level in levels:
            inp, err = build_input(r, lig_donors, level, tg, vectors)
            if err:                       # donor sanity: the same for every level
                row["error"] = f"skip: {err}"[:160]
                break
            row["level"] = level
            try:
                out_d = build_complex(inp)
                error = None if out_d else "architector returned no structures"
            except Exception as e:  # noqa: BLE001
                out_d, error = None, f"{type(e).__name__}: {e}"[:160]
            if out_d:
                best = list(out_d.values())[0]          # OrderedDict sorted by energy
                best["ase_atoms"].write(str(structures / f"{rc}.xyz"))
                row["built"] = True; built += 1
                row["n_conformers"] = len(out_d)
                row["energy"] = best.get("energy")
                row.pop("error", None)
                break
            row["error"] = error
            row.setdefault("primary_error", f"{level}: {error}"[:160])   # why the target failed
        if "level" in row:
            row["wall_s"] = round(time.perf_counter() - ts, 2)
            if targets is not None and row["built"] and row["level"] != levels[0]:
                row["fallback"] = True
        fh.write(json.dumps(row) + "\n"); fh.flush()
        if k % 10 == 0:
            print(f"  shard {i}/{n}: {k}/{len(recs)} built={built} "
                  f"({(time.perf_counter()-t0)/k:.1f}s/cpx wall)", flush=True)
    fh.close()
    print(f"shard {i}/{n} done: {built} built of {len(recs)} -> {out}")


if __name__ == "__main__":
    main()
