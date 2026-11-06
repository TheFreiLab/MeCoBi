"""Extract experimental coordination spheres from our CIF tree for the benchmark
bundle refcodes (the scoring reference). Shardable + resumable; skips CIFs that are
still OneDrive placeholders (re-run as they hydrate). Runs in the MeCoBi env.

    python dataprep/extract_spheres.py --shard 0/1 --limit 50      # smoke test
    python dataprep/extract_spheres.py --shard 0/8 &  ... --shard 7/8   # parallel full run

CIF root folder resolution (Generation3, one subfolder per metal): --cif-root flag
> MECOBI_CIF_ROOT env var > interactive prompt (only when running with a real terminal, so parallel/background
shards never hang waiting on stdin).
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # benchmark root: shared harness
from cif_geometry import SYM2NAME, coordination_sphere

BENCH = Path(__file__).resolve().parents[1]   # benchmark root: bundle in, sphere shards out
_DEFAULT_CIF_ROOT = None  # no built-in default: --cif-root or MECOBI_CIF_ROOT
_OFFLINE = 0x1000 | 0x400000


def _resolve_cif_root(cli_value):
    for candidate in (cli_value, os.environ.get("MECOBI_CIF_ROOT"), _DEFAULT_CIF_ROOT):
        if candidate and os.path.isdir(candidate):
            return candidate
    if sys.stdin.isatty():
        typed = input(
            "CIF root folder not found (expected a 'Generation3'-style folder with one "
            "subfolder per metal, e.g. .../Cu/<REFCODE>.*.cif).\n"
            "Enter the path to your CIF folder: "
        ).strip().strip('"')
        if typed and os.path.isdir(typed):
            return typed
    raise SystemExit(
        "Could not find the CIF root folder. Pass --cif-root PATH, set the "
        "MECOBI_CIF_ROOT environment variable, or run this interactively to be prompted."
    )


def _bundle(name="benchmark_bundle"):
    gz = BENCH / f"{name}.json.gz"
    if gz.exists():
        return json.loads(gzip.open(gz, "rt", encoding="utf-8").read())
    return json.loads((BENCH / f"{name}.json").read_text())


def is_placeholder(path):
    try:
        return bool(os.stat(path).st_file_attributes & _OFFLINE)
    except (AttributeError, OSError):
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1", help="i/N")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--bundle", default="benchmark_bundle",
                     help="bundle basename to read (.json.gz or .json), e.g. benchmark_bundle_v2")
    ap.add_argument("--cif-root", default=None,
                     help="Path to the Generation3-style CIF folder (one subfolder per "
                          "metal). Falls back to MECOBI_CIF_ROOT, then an interactive prompt.")
    cfg = ap.parse_args()
    cif_root = _resolve_cif_root(cfg.cif_root)
    i, n = (int(x) for x in cfg.shard.split("/"))
    out = Path(cfg.out) if cfg.out else BENCH / f"_spheres_{cfg.bundle}_shard{i}of{n}.json"

    done = {}
    if out.exists():
        done = json.loads(out.read_text())

    recs = [r for k, r in enumerate(_bundle(cfg.bundle)) if k % n == i]
    if cfg.limit:
        recs = recs[:cfg.limit]

    got = skipped_ph = missing = fail = 0
    for k, r in enumerate(recs, 1):
        rc = r["refcode"]
        if rc in done:
            continue
        folder = SYM2NAME.get(r["metal"])
        if not folder:
            missing += 1; continue
        cifs = glob.glob(f"{cif_root}/{folder}/{rc}.*.cif")
        if not cifs:
            missing += 1; continue
        if is_placeholder(cifs[0]):
            skipped_ph += 1; continue
        try:
            sph = coordination_sphere(Path(cifs[0]).read_text(errors="ignore"), r["metal"], r["cn"])
        except Exception:
            sph = None
        if not sph:
            fail += 1; continue
        done[rc] = {"metal_xyz": sph[0], "donors": sph[1], "donor_elements": sph[2],
                    "cn_contacts": len(sph[1])}
        got += 1
        if got % 200 == 0:
            out.write_text(json.dumps(done))
            print(f"  [{k}/{len(recs)}] got={got} skip_placeholder={skipped_ph} "
                  f"missing={missing} fail={fail}", flush=True)

    out.write_text(json.dumps(done))
    print(f"shard {i}/{n}: spheres={len(done)} (+{got} new)  "
          f"placeholder-skipped={skipped_ph} missing={missing} parse-fail={fail}  -> {out}")


if __name__ == "__main__":
    main()
