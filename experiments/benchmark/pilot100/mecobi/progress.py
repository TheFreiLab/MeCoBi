"""Live progress panel for the MeCoBi pilot-100 generation run.

Reads the per-complex JSONL run.py writes (_results_shard*of*.jsonl), restricts to the
frozen pilot set, and prints a one-screen snapshot: how many of the 100 are done/built/
failed, per-structure wall-time stats, a rough ETA, and the most recent failures.

Only rows carrying `wall_s` (this timed run) count, so leftover _results_shard*of30.jsonl
from an older untimed run never inflate the progress. Pure stdlib.

    python pilot100/mecobi/progress.py                 # one snapshot
    watch -n 10 python pilot100/mecobi/progress.py     # live panel, refresh every 10 s
    python pilot100/mecobi/progress.py --arch          # same but for the Architector run
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent   # pilot100/mecobi/
PILOT = HERE.parent                      # pilot100/: pilot_100.json + per-tool run folders


def _load(base: Path, pattern: str) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for f in sorted(base.glob(pattern)):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                prev = rows.get(r["refcode"])
                if prev is None or r.get("wall_s") is not None or prev.get("wall_s") is None:
                    rows[r["refcode"]] = r
    return rows


def _bar(pct: float, width: int = 30) -> str:
    fill = int(round(pct / 100 * width))
    return "[" + "#" * fill + "-" * (width - fill) + "]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refcodes", default="pilot_100.json")
    ap.add_argument("--arch", action="store_true",
                     help="track the Architector run (_arch_results_*) instead of MeCoBi.")
    ap.add_argument("--dir", default=None,
                     help="run dir holding the shard JSONLs, relative to pilot100/ (default: "
                          "mecobi/mecobi_det, or architector/ with --arch).")
    ap.add_argument("--shards", type=int, default=1,
                     help="how many parallel processes you launched (divides the ETA).")
    cfg = ap.parse_args()

    pat = "_arch_results_shard*of*.jsonl" if cfg.arch else "_results_shard*of*.jsonl"
    tool = "Architector" if cfg.arch else "MeCoBi"
    base = PILOT / (cfg.dir or ("architector" if cfg.arch else "mecobi/mecobi_det"))
    pilot = set(json.loads((PILOT / cfg.refcodes).read_text(encoding="utf-8")))
    total = len(pilot)

    rows = {rc: r for rc, r in _load(base, pat).items()
            if rc in pilot and r.get("wall_s") is not None}
    done = len(rows)
    built = sum(1 for r in rows.values() if r.get("built"))
    failed = done - built
    remaining = total - done
    walls = [r["wall_s"] for r in rows.values()]
    med = st.median(walls) if walls else 0.0
    mean = st.fmean(walls) if walls else 0.0
    compute_min = sum(walls) / 60
    eta_min = (remaining * med / max(cfg.shards, 1)) / 60 if walls else 0.0
    pct = 100 * done / total if total else 0.0

    print(f"{tool} pilot-{total} progress        {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("-" * 58)
    print(f"done   {done:>3}/{total}  {_bar(pct)}  {pct:.0f}%")
    print(f"built  {built:<4} failed {failed:<4} remaining {remaining}")
    if walls:
        print(f"wall/structure  median {med:.1f}s  mean {mean:.1f}s   "
              f"(compute so far {compute_min:.1f} min)")
        print(f"ETA  ~{eta_min:.1f} min" +
              (f"  (assuming {cfg.shards} shards)" if cfg.shards > 1 else "  (serial)"))
    else:
        print("no timed results yet -- run.py hasn't written a completed complex.")
    fails = [(rc, r.get("error", "")) for rc, r in rows.items() if not r.get("built")]
    if fails:
        print("recent failures:")
        for rc, err in fails[-5:]:
            print(f"  {rc:<8} {err[:70]}")


if __name__ == "__main__":
    main()
