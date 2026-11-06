"""Backfill donor_indices into an existing benchmark run's JSONL shards.

run.py now records ``donor_indices`` (the actual metal-bonder atom indices, in .xyz order) so the
report draws the metal-donor bonds exactly instead of guessing by distance. For runs made before
that, this recomputes them WITHOUT re-running xtb: it just re-assembles each complex (relax=False,
deterministic, ~0.5 s each) from the same bundle + donors + overrides the run used, and injects the
donor_indices into every row that lacks them. The relaxed .xyz atom order matches the assembly, so
the indices line up with the structures already on disk.

    python backfill_donor_indices.py --run-dir pilot100/mecobi/mecobi_det2 \
        --bundle benchmark_bundle_v2 --donors benchmark_donors.json

Idempotent: rows that already carry donor_indices are left untouched.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import bench_overrides
from mecobi import pipeline
from mecobi.model import Complex, Ligand, Metal
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).parent


def _load_bundle(name):
    import gzip
    # v1 ships as benchmark_bundle.json.gz; v2 lives in the benchmark_bundle.json/ directory.
    for p in (HERE / f"{name}.json.gz", HERE / f"{name}.json",
              HERE / "benchmark_bundle.json" / f"{name}.json", Path(name)):
        if p.exists() and p.is_file():
            text = (gzip.open(p, "rt", encoding="utf-8").read() if str(p).endswith(".gz")
                    else p.read_text(encoding="utf-8"))
            return {e["refcode"]: e for e in json.loads(text)}
    raise SystemExit(f"bundle {name!r} not found (tried .json.gz, .json, benchmark_bundle.json/)")


def _donor_indices(rec, donors_row):
    """Assemble the complex (no xtb) and return its global bonder atom indices."""
    ligs = [Ligand(s) for s in rec["ligands"]]
    if donors_row is not None:
        for lig, atoms in zip(ligs, donors_row):
            if atoms:
                lig.donor_override = list(atoms)
    cx = Complex(metal=Metal(rec["metal"], rec["ox"]), name=rec["refcode"], ligands=ligs)
    with tempfile.TemporaryDirectory() as d:
        res = pipeline.build_complex(cx, d, relax=False)
    return [int(x) for x in (res[0].donor_indices or [])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default="pilot100/mecobi/mecobi_det")
    ap.add_argument("--bundle", default="benchmark_bundle_v2")
    ap.add_argument("--donors", default="benchmark_donors.json")
    ap.add_argument("--overrides", default="benchmark_overrides.json")
    cfg = ap.parse_args()

    run_dir = HERE / cfg.run_dir if not Path(cfg.run_dir).is_absolute() else Path(cfg.run_dir)
    bundle = _load_bundle(cfg.bundle)
    donors = json.loads((HERE / cfg.donors).read_text(encoding="utf-8")) if cfg.donors else {}
    overrides = bench_overrides.load(cfg.overrides)

    shards = sorted(run_dir.glob("_results_shard*.jsonl"))
    if not shards:
        raise SystemExit(f"no _results_shard*.jsonl in {run_dir}")
    total = filled = failed = 0
    for shard in shards:
        rows = [json.loads(x) for x in shard.read_text(encoding="utf-8").splitlines() if x.strip()]
        changed = False
        for row in rows:
            total += 1
            if "donor_indices" in row or not row.get("built"):
                continue
            rc = row["refcode"]
            rec = bundle.get(rc)
            if rec is None:
                continue
            rec = bench_overrides.record(dict(rec), overrides)
            donors_row = bench_overrides.donors(rc, donors.get(rc), overrides)
            try:
                row["donor_indices"] = _donor_indices(rec, donors_row)
                filled += 1
                changed = True
            except Exception as e:  # noqa: BLE001 -- skip a refcode that won't assemble
                failed += 1
                print(f"  ! {rc}: {type(e).__name__}: {e}")
        if changed:
            shard.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
            print(f"  {shard.name}: updated")
    print(f"done: {filled} filled, {failed} failed, {total} rows scanned.")


if __name__ == "__main__":
    main()
