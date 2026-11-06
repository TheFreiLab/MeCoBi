"""Extract the crystal GEOMETRY + ISOMER site-map target for each benchmark refcode,
deterministically from its CIF (no oracle, no RMSD search).

For each complex: perceive the ligands (donor overrides from benchmark_donors, so the SITE
denticities match what the builder will use), read the crystal geometry + donor->site map
straight from the CIF with :mod:`crystal_assign` (haptic-collapsed into MeCoBi's site space),
then -- crucially -- **build-check** the extracted site map with a real ``relax=False``
assembly. A site map that does not assemble is downgraded to ``geometry_only`` (the geometry
is still recorded; the builder falls back to that geometry's default isomer). So every
``status="ok"`` target is guaranteed buildable.

Output: benchmark_targets.json = {refcode: {geometry, site_cn, site_map, shape_cshm,
geom_ambiguous, status}}. Shardable + resumable; skips OneDrive placeholders. run.py reads
this file (``--targets``) to build the crystal isomer instead of its heuristic pick.

    python enrich_bundle_geometry.py --refcodes pilot100/pilot_100.json --donors benchmark_donors.json
    for i in $(seq 0 7); do python enrich_bundle_geometry.py --shard $i/8 \
        --donors benchmark_donors.json & done; wait          # full tree later
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import tempfile
from pathlib import Path

from rdkit import Chem, RDLogger

import bench_overrides
import crystal_assign as CA
from cif_geometry import SYM2NAME
from mecobi import isomers, pipeline, spin
from mecobi.model import Complex, Geometry, Ligand, Metal

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).parent
_DEFAULT_CIF_ROOT = None  # no built-in default: --cif-root or MECOBI_CIF_ROOT
_OFFLINE = 0x1000 | 0x400000


def _bundle(name="benchmark_bundle"):
    gz = HERE / f"{name}.json.gz"
    if gz.exists():
        return json.loads(gzip.open(gz, "rt", encoding="utf-8").read())
    return json.loads((HERE / f"{name}.json").read_text())


def is_placeholder(path):
    try:
        return bool(os.stat(path).st_file_attributes & _OFFLINE)
    except (AttributeError, OSError):
        return False


def _perceive(r, donor_row):
    """Complex with donors overridden (bypasses pydentate/torch); returns the perceived cx."""
    ligs = [Ligand(smi) for smi in r["ligands"]]
    if donor_row is not None:
        for lig, atoms in zip(ligs, donor_row):
            if atoms:
                lig.donor_override = list(atoms)
    cx = Complex(metal=Metal(r["metal"], r["ox"]), name=r["refcode"], ligands=ligs)
    pipeline.resolve_perception(cx)
    return cx


def _lig_specs(cx):
    """Per ligand ``(site_count, sorted raw donor-atom elements, smiles, donor_idx)``:
    the site count (structure-perceived denticity), the raw donor-atom elements (for matching
    crystal components), and the SMILES + donor atom indices (for donor-ordering the site
    tuple, so donor k -> site tuple[k])."""
    specs = []
    for l in cx.ligands:
        m = Chem.MolFromSmiles(l.smiles)
        atoms = list(l.effective_donors or [])
        els = tuple(sorted(m.GetAtomWithIdx(i).GetSymbol() for i in atoms)) if m else ()
        specs.append((l.denticity, els, l.smiles, atoms))
    return specs


def _builds(cx, geometry, site_map):
    """True if ``site_map`` assembles (relax=False) for this complex."""
    try:
        spec = isomers.parse_topology_spec(site_map, Geometry(geometry))
        with tempfile.TemporaryDirectory() as tmp:
            pipeline.build_complex(cx, Path(tmp), isomers_override=[spec], relax=False)
        return True
    except Exception:  # noqa: BLE001
        return False


def target_for(r, cif_text, donor_row, build_check=True, h_rel=None):
    """Extract + (optionally) build-check one target record; never raises. ``h_rel``: located
    hydrides (hydrides.py) -- ``r`` / ``donor_row`` must already carry them as ``[H-]`` ligands."""
    try:
        cx = _perceive(r, donor_row)
        try:
            lone_pair = bool(spin.has_stereo_active_lone_pair(r["metal"], r["ox"]))
        except Exception:  # noqa: BLE001
            lone_pair = False
        res = CA.build_site_map(cif_text, r["metal"], r["cn"], _lig_specs(cx),
                                lone_pair=lone_pair, h_rel=h_rel,
                                donor_elements=r.get("donor_elements"))
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": f"{type(e).__name__}: {e}"[:120]}
    if res.get("status") == "ok" and build_check and not _builds(cx, res["geometry"], res["site_map"]):
        # extracted map does not assemble -> keep the geometry, drop the isomer
        res["status"] = "geometry_only"
        res["site_map"] = None
        res["build_check"] = "failed->geometry_only"
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1", help="i/N")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--bundle", default="benchmark_bundle")
    ap.add_argument("--donors", default=None,
                    help="benchmark_donors.json: donor overrides so SITE denticities match "
                         "the builder (bypasses pydentate). Restricts to mapped complexes.")
    ap.add_argument("--refcodes", default=None,
                    help="JSON list (e.g. pilot100/pilot_100.json) to restrict to.")
    ap.add_argument("--cif-root", default=None)
    ap.add_argument("--out", default="benchmark_targets.json")
    ap.add_argument("--no-build-check", action="store_true",
                    help="skip the relax=False assembly check (faster, less safe).")
    cfg = ap.parse_args()
    cif_root = cfg.cif_root or os.environ.get("MECOBI_CIF_ROOT") or _DEFAULT_CIF_ROOT
    if not cif_root or not os.path.isdir(cif_root):
        raise SystemExit(f"CIF root not found: {cif_root} (pass --cif-root)")
    i, n = (int(x) for x in cfg.shard.split("/"))
    donors = json.loads((HERE / cfg.donors).read_text()) if cfg.donors else None
    overrides = bench_overrides.load()
    keep = set(json.loads((HERE / cfg.refcodes).read_text())) if cfg.refcodes else None
    out = Path(cfg.out) if Path(cfg.out).is_absolute() else HERE / cfg.out
    done = json.loads(out.read_text()) if out.exists() else {}

    recs = [r for k, r in enumerate(_bundle(cfg.bundle))
            if k % n == i and (keep is None or r["refcode"] in keep)
            and (donors is None or r["refcode"] in donors)]
    if cfg.limit:
        recs = recs[:cfg.limit]

    from collections import Counter
    tally = Counter()
    got = missing = skipped = 0
    for k, r in enumerate(recs, 1):
        rc = r["refcode"]
        if rc in done:
            tally[done[rc].get("status", "?")] += 1
            continue
        folder = SYM2NAME.get(r["metal"])
        cifs = glob.glob(f"{cif_root}/{folder}/{rc}.*.cif") if folder else []
        if not cifs:
            missing += 1
            continue
        if is_placeholder(cifs[0]):
            skipped += 1
            continue
        r = bench_overrides.record(r, overrides)  # confirmed OS/charge input fixes
        donor_row = bench_overrides.donors(rc, donors[rc] if donors else None, overrides)
        rec = target_for(r, Path(cifs[0]).read_text(errors="ignore"),
                         donor_row, build_check=not cfg.no_build_check)
        rec = {"refcode": rc, "metal": r["metal"], "cn": r["cn"], **rec}
        done[rc] = rec
        tally[rec.get("status", "?")] += 1
        got += 1
        if got % 50 == 0:
            out.write_text(json.dumps(done))
            print(f"  [{k}/{len(recs)}] got={got} {dict(tally)}", flush=True)
    out.write_text(json.dumps(done))
    print(f"shard {i}/{n}: targets={len(done)} (+{got})  missing={missing} "
          f"placeholder-skipped={skipped}\n  status: {dict(tally)}  -> {out}")


if __name__ == "__main__":
    main()
