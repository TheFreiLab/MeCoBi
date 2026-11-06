"""Live progress panel for a running benchmark (full 30k or a pilot). Read-only, stdlib only.

Follows the shard JSONLs of a run dir and redraws every few seconds: structures done, build /
connectivity / CN-match / shape-match rates, throughput, and an ETA. The run finishes when its
SLOWEST shard does, so the ETA is the largest per-shard estimate (structures left x that shard's
mean time), not total / rate. Shard totals come from the shard logs (run.py prints ``k/N`` every 25
structures), so they show ``?`` for the first minutes.

    python full30k/progress.py                        # full30k/mecobi_30k, refresh every 10 s
    python full30k/progress.py --run-dir full30k/mecobi_30k_xtb671 --every 5
    python full30k/progress.py --run-dir pilots10/run_r01_f5f1215 --once
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import statistics as st
import time
from collections import deque
from datetime import datetime
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]   # benchmark root
_LOG_RE = re.compile(r"shard \d+/\d+: (\d+)/(\d+) ")
_DONE_RE = re.compile(r"shard \d+/\d+ done: .* of (\d+) ")


class Shard:
    def __init__(self, path: Path):
        self.path, self.pos, self.rows, self.wall = path, 0, 0, 0.0
        self.total, self.finished = None, False

    def read(self, sink):
        """Consume the complete lines appended since the last call."""
        with self.path.open("rb") as fh:
            fh.seek(self.pos)
            chunk = fh.read()
        end = chunk.rfind(b"\n") + 1
        self.pos += end
        for line in chunk[:end].splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            self.rows += 1
            if isinstance(r.get("wall_s"), (int, float)):
                self.wall += r["wall_s"]
            sink(r)
        log = self.path.with_name(self.path.name.replace("_results_", "").replace(".jsonl", ".log"))
        if log.exists():
            tail = log.read_text(encoding="utf-8", errors="ignore")[-4000:]
            if (m := _DONE_RE.search(tail)):
                self.total, self.finished = int(m.group(1)), True
            elif (ms := _LOG_RE.findall(tail)):
                self.total = int(ms[-1][1])

    def eta_s(self):
        if self.finished or self.total is None or not self.rows:
            return 0.0 if self.finished else None
        return max(0, self.total - self.rows) * self.wall / self.rows


def _hms(s):
    if s is None:
        return "?"
    s = int(s)
    return f"{s // 3600}h{s % 3600 // 60:02d}m" if s >= 3600 else f"{s // 60}m{s % 60:02d}s"


def _pct(a, b):
    return f"{100 * a / b:5.1f}%" if b else "    -"


def _bar(frac, width=40):
    n = round(width * min(1.0, max(0.0, frac)))
    return "[" + "#" * n + "." * (width - n) + "]"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", default="full30k/mecobi_30k", help="relative to the benchmark root")
    ap.add_argument("--every", type=float, default=10.0, help="refresh period, seconds")
    ap.add_argument("--once", action="store_true", help="print one snapshot and exit")
    cfg = ap.parse_args()
    run_dir = Path(cfg.run_dir) if Path(cfg.run_dir).is_absolute() else BENCH / cfg.run_dir

    shards: dict[str, Shard] = {}
    c = {"built": 0, "conn": 0, "scored": 0, "shape": 0, "cn_n": 0, "cn_ok": 0, "fallback": 0,
         "error": 0}
    walls, last, slow = [], deque(maxlen=6), []
    history = deque(maxlen=400)   # (time, rows) -> throughput over the last minutes

    def sink(r):
        if r.get("built"):
            c["built"] += 1
            c["conn"] += bool(r.get("connectivity_ok"))
        else:
            c["error"] += 1
        if r.get("shape_match") is not None:
            c["scored"] += 1
            c["shape"] += bool(r["shape_match"])
        if r.get("cn_match") is not None:
            c["cn_n"] += 1
            c["cn_ok"] += bool(r["cn_match"])
        c["fallback"] += str(r.get("build_mode", "")).startswith("heuristic")
        w = r.get("wall_s")
        if isinstance(w, (int, float)):
            walls.append(w)
            slow.append((w, r["refcode"]))
            slow.sort(reverse=True)
            del slow[5:]
        last.append(f"{r['refcode']}({'ok' if r.get('built') else 'FAIL'},{w}s)")

    while True:
        for f in sorted(glob.glob(str(run_dir / "_results_shard*.jsonl"))):
            shards.setdefault(f, Shard(Path(f))).read(sink)
        meta_p = run_dir / "run_meta.json"
        meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
        rows = sum(s.rows for s in shards.values())
        known = [s for s in shards.values() if s.total is not None]
        n_sh = meta.get("shards") or len(shards)
        total = (round(sum(s.total for s in known) * n_sh / len(known)) if known else None)
        now = time.time()
        history.append((now, rows))
        t_old, r_old = next(((t, r) for t, r in history if now - t <= 600), history[0])
        rate = (rows - r_old) / (now - t_old) * 3600 if now > t_old else 0.0
        etas = [s.eta_s() for s in shards.values()]
        eta = max((e for e in etas if e is not None), default=None) if known else None
        running = sum(not s.finished for s in shards.values())
        ended = bool(meta.get("finished")) or (shards and running == 0 and len(known) == len(shards))

        out = ["\x1b[2J\x1b[H" if not cfg.once else "",
               f"MeCoBi benchmark  {run_dir.name}   {time.strftime('%Y-%m-%d %H:%M:%S')}",
               (f"commit {meta.get('commit', '?')}  xtb {meta.get('xtb_version', '?')}  "
               f"host {meta.get('host', '?')}  hydrides {meta.get('hydrides') or 'none'}"), ""]
        if total:
            out.append(f"{_bar(rows / total)} {rows}/{total}  {_pct(rows, total)}"
                       + ("  (total estimated)" if len(known) < n_sh else ""))
        else:
            out.append(f"{rows} structures done (shard totals not in the logs yet)")
        started = meta.get("started")
        if started:
            end = meta.get("finished")   # run_meta times are naive local time
            el = ((datetime.fromisoformat(end) if end else datetime.now())  # noqa: DTZ005
                  - datetime.fromisoformat(started)).total_seconds()
            out.append(f"elapsed {_hms(el)}   rate {rate:.0f}/h (last 10 min)   "
                       f"ETA {'done' if ended else _hms(eta)}   shards running {running}/{n_sh}")
        else:
            out.append(f"rate {rate:.0f}/h   ETA {'done' if ended else _hms(eta)}")
        out += ["",
                f"built         {_pct(c['built'], rows)}  ({c['built']}/{rows}; {c['error']} failed)",
                f"connectivity  {_pct(c['conn'], c['built'])}  of built",
                f"CN match      {_pct(c['cn_ok'], c['cn_n'])}  of scored",
                f"shape match   {_pct(c['shape'], c['scored'])}  of scored",
                f"heuristic fallback (site map did not assemble): {c['fallback']}"]
        if walls:
            out.append(f"time / structure: median {st.median(walls):.1f}s  mean {st.mean(walls):.1f}s"
                       f"  max {max(walls):.0f}s   CPU {sum(walls) / 3600:.1f} h")
        if shards:
            prog = sorted(shards.values(), key=lambda s: (s.eta_s() or 0), reverse=True)[:3]
            out.append("slowest shards: " + "  ".join(
                f"{s.path.stem.replace('_results_', '')} {s.rows}/{s.total or '?'} "
                f"(ETA {_hms(s.eta_s())})" for s in prog))
        if slow:
            out.append("slowest structures: " + "  ".join(f"{rc}({w:.0f}s)" for w, rc in slow))
        if last:
            out.append("last: " + "  ".join(last))
        if not shards:
            out.append(f"no _results_shard*.jsonl in {run_dir} yet")
        print("\n".join(out), flush=True)
        if cfg.once or ended:
            if ended and not cfg.once:
                print("\nrun finished.")
            return
        time.sleep(cfg.every)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
