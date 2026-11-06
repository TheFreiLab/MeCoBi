"""Live terminal panel for a running metallogen_run.py sweep.

Run in a SECOND terminal on the same machine while the shards run; it tails the
_metallogen_results_shard*.jsonl files and reprints progress in place until done (Ctrl-C to stop).
Read-only -- it never touches the run.

    python metallogen_monitor.py                    # dir metallogen_det, refresh 5s
    python metallogen_monitor.py --interval 10 --dir metallogen_det

Shows: overall progress vs the m-SMILES total, built/failed, run-status breakdown, generation-time
stats, live throughput + ETA (measured between refreshes, so it reflects the real parallel rate),
and the last few completions.
"""
from __future__ import annotations

import argparse
import glob
import json
import statistics as st
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
CLR = "\033[2J\033[H"  # clear screen + home


def load(dirp: Path):
    by = {}
    for f in sorted(glob.glob(str(dirp / "_metallogen_results_shard*.jsonl"))):
        try:
            lines = Path(f).read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue  # a half-written last line; picked up next refresh
            by[r["refcode"]] = r
    return list(by.values())


def bar(frac: float, width: int = 34) -> str:
    frac = max(0.0, min(1.0, frac))
    n = int(round(frac * width))
    return "[" + "#" * n + "-" * (width - n) + "]"


def fmt_hms(sec: float) -> str:
    sec = int(max(0, sec))
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h:d}h{m:02d}m" if h else f"{m:d}m{s:02d}s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="metallogen_det")
    ap.add_argument("--msmiles", default="benchmark_msmiles_pilot.json")
    ap.add_argument("--interval", type=float, default=5.0)
    cfg = ap.parse_args()

    dirp = HERE / cfg.dir
    total = len(json.loads((HERE / cfg.msmiles).read_text()))

    prev_t, prev_done = None, None
    rate_ema = None  # complexes/sec, smoothed
    try:
        while True:
            recs = load(dirp)
            done = len(recs)
            built = [r for r in recs if r.get("built")]
            walls = [r["wall_s"] for r in recs if r.get("wall_s") is not None]
            now = time.time()

            # live throughput between refreshes -> ETA (captures the real parallel rate)
            if prev_t is not None and now > prev_t and done >= prev_done:
                inst = (done - prev_done) / (now - prev_t)
                rate_ema = inst if rate_ema is None else 0.5 * rate_ema + 0.5 * inst
            prev_t, prev_done = now, done
            eta = (total - done) / rate_ema if rate_ema and rate_ema > 1e-9 and done < total else None

            lines = []
            lines.append("  MetalloGen run monitor        " + time.strftime("%H:%M:%S"))
            lines.append("  " + "-" * 52)
            frac = done / total if total else 0
            lines.append(f"  {bar(frac)}  {done}/{total}  ({frac*100:.0f}%)")
            fail = done - len(built)
            lines.append(f"  built {len(built)}    failed {fail}    remaining {total-done}")
            if walls:
                lines.append(f"  gen-time/complex : median {st.median(walls):5.1f}s   "
                             f"mean {st.mean(walls):5.1f}s   max {max(walls):5.1f}s")
                lines.append(f"  total gen-time   : {sum(walls)/60:.1f} min (summed over complexes)")
            if rate_ema:
                lines.append(f"  throughput       : {rate_ema*60:.1f} complexes/min"
                             + (f"    ETA {fmt_hms(eta)}" if eta is not None else ""))
            status = Counter(r.get("run_status", "?") for r in recs)
            if status:
                lines.append("  run-status       : "
                             + "   ".join(f"{k} {v}" for k, v in status.most_common()))
            # last few completions (by file order ~ completion order)
            lines.append("  " + "-" * 52)
            lines.append("  recent:")
            for r in recs[-6:]:
                mark = "OK " if r.get("built") else "xx "
                lines.append(f"    {mark}{r['refcode']:8} CN{r.get('cn','?'):<2} "
                             f"{r.get('geometry',''):22} {r.get('wall_s','?'):>6}s "
                             f"{r.get('run_status','')}")
            if done >= total and total:
                lines.append("  " + "-" * 52)
                lines.append("  >>> ALL COMPLETE <<<   (Ctrl-C to exit)")

            print(CLR + "\n".join(lines), flush=True)
            time.sleep(cfg.interval)
    except KeyboardInterrupt:
        print("\nmonitor stopped.")


if __name__ == "__main__":
    main()
