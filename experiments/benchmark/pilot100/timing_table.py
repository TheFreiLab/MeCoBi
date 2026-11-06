#!/usr/bin/env python3
"""Clean, shard-proof timing table for the tool comparison.

Reads each tool's per-complex result JSONL (any shard count), de-duplicates by
refcode (re-runs/resumes leave duplicates), separates successful builds from
failures/timeouts, and reports the metrics that are FAIR to compare across tools
regardless of how many shards were used:

  * median / mean wall_s per BUILT structure   -> the tool's per-structure speed
  * CPU-time = sum of wall_s                    -> total compute cost (shard-proof)

Wall-clock TOTAL is deliberately NOT reported: it depends on the number of
parallel shards/cores, so it is not a like-for-like tool comparison.

Result files are auto-discovered across the usual output dirs. Override any tool
with an explicit glob (relative to the current dir or to this script's dir):
  python pilot100/timing_table.py
  python pilot100/timing_table.py --mecobi 'mecobi/mecobi_4shard/_results_shard*of*.jsonl'
  python pilot100/timing_table.py --common
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent            # experiments/benchmark/pilot100
ROOT = HERE.parents[2]                             # repo root

# per-tool result-file name pattern
FILEGLOB = {
    "MeCoBi":      "_results_shard*of*.jsonl",
    "molSimplify": "_molsim_results_shard*of*.jsonl",
    "MetalloGen":  "_metallogen_results_shard*of*.jsonl",
    "Architector": "_arch_results_shard*of*.jsonl",
}
# candidate directories searched for each tool (first hit(s) win); add your own freely
CAND = {
    # a fair_<commit> run is picked with --mecobi (a glob over several run dirs would merge runs)
    "MeCoBi":      ["mecobi/mecobi_4shard", "mecobi/mecobi_det", "mecobi/mecobi_det2", "mecobi"],
    "molSimplify": ["molsimplify/molsimplify_det_xtb", "molsimplify/molsimplify_det", "molsimplify",
                    ROOT / "arch_comparison" / "molsimplify"],
    "MetalloGen":  ["metallogen/metallogen_det", "metallogen", ROOT / "arch_comparison" / "metallogen"],
    "Architector": ["architector/architector_det", "architector",
                    ROOT / "arch_comparison" / "architector"],
}


def resolve_globs(tool: str, override: str | None) -> list[str]:
    if override:                                   # explicit: try as given (CWD) and under HERE
        return [override, str(HERE / override)]
    globs = []
    for d in CAND[tool]:
        base = Path(d) if os.path.isabs(str(d)) else (HERE / d)
        globs.append(str(base / FILEGLOB[tool]))
    return globs


def load(globs: list[str]):
    """Return ({refcode: record}, [files], {shardN}). Uses the FIRST candidate glob
    that matches any file (different dirs are different RUNS, not shards of one run;
    only the shard files WITHIN that dir are merged). Dedup rows by refcode."""
    files = []
    for g in globs:                                # first non-empty candidate wins
        fs = sorted(glob.glob(g))
        if fs:
            files = fs
            break
    best, shards = {}, set()
    for f in files:
        stem = Path(f).stem
        if "of" in stem:
            shards.add(stem.split("of")[-1])
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            rc = d.get("refcode")
            if rc is None:
                continue
            prev = best.get(rc)
            if prev is None or (d.get("built") and not prev.get("built")) \
                    or d.get("built") == prev.get("built"):
                best[rc] = d
    return best, files, shards


def stats(records: dict[str, dict]):
    built = [r for r in records.values() if r.get("built") and r.get("wall_s") is not None]
    all_timed = [r for r in records.values() if r.get("wall_s") is not None]
    bw = [float(r["wall_s"]) for r in built]
    n = len(records)
    row = {
        "n": n, "built": len(built), "rate": (len(built) / n * 100 if n else 0),
        "timeouts": sum(1 for r in records.values() if r.get("run_status") == "timeout"),
        "median": st.median(bw) if bw else None,
        "mean": (sum(bw) / len(bw)) if bw else None,
        "max": max(bw) if bw else None,
        "cpu_built_min": sum(bw) / 60 if bw else 0.0,
        "cpu_all_min": sum(float(r["wall_s"]) for r in all_timed) / 60,
    }
    ffs = {r.get("ff") for r in records.values() if r.get("ff")}
    row["ff"] = "/".join(sorted(ffs)) if ffs else ""
    return row, {rc for rc in records if records[rc].get("built")}


def fmt(v, s="{:.1f}"):
    return "-" if v is None else s.format(v)


def print_table(title, rows):
    print(f"\n{title}")
    print(f"{'tool':<13}{'built/N':>10}{'rate':>7}{'t/o':>5}"
          f"{'median s':>10}{'mean s':>9}{'max s':>8}{'CPU(built)':>12}{'CPU(all)':>10}  notes")
    for name, r in rows:
        note = f"ff={r['ff']}" if r.get("ff") else ""
        print(f"{name:<13}{str(r['built'])+'/'+str(r['n']):>10}{r['rate']:>6.0f}%{r['timeouts']:>5}"
              f"{fmt(r['median']):>10}{fmt(r['mean']):>9}{fmt(r['max'],'{:.0f}'):>8}"
              f"{fmt(r['cpu_built_min']):>10} min{fmt(r['cpu_all_min']):>7} min  {note}")


def main():
    ap = argparse.ArgumentParser()
    for name in FILEGLOB:
        ap.add_argument(f"--{name.lower()}", default=None, help=f"{name} results glob (override)")
    ap.add_argument("--common", action="store_true",
                    help="also print stats restricted to refcodes ALL found tools built")
    cfg = ap.parse_args()

    loaded, rows, built_sets = {}, [], {}
    for name in FILEGLOB:
        recs, files, shards = load(resolve_globs(name, getattr(cfg, name.lower())))
        if not recs:
            print(f"[skip] {name}: no result files found "
                  f"(searched: {', '.join(str(x) for x in CAND[name])})")
            continue
        row, built = stats(recs)
        loaded[name] = recs; built_sets[name] = built; rows.append((name, row))
        sc = "/".join(sorted(shards)) or "?"
        print(f"[{name}] {len(files)} file(s), of{sc} shards, {len(recs)} unique refcodes  "
              f"<- {os.path.dirname(files[0])}")

    if rows:
        print_table("PER-STRUCTURE SPEED (built) + CPU-TIME  (shard-proof; wall-clock total omitted)", rows)
    if cfg.common and len(built_sets) > 1:
        common = set.intersection(*built_sets.values())
        crows = [(name, stats({rc: recs[rc] for rc in common})[0]) for name, recs in loaded.items()]
        print_table(f"COMMON SET - {len(common)} refcodes built by ALL {len(loaded)} tools", crows)
    print("\nReport the MEDIAN s/structure (fair, shard-independent) or CPU-time; "
          "do NOT compare wall-clock total across different shard counts.")


if __name__ == "__main__":
    main()
