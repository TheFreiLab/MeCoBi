"""Timing report for a MeCoBi pilot-100 run (run_pilot100.py output), MetalloGen-report style.

Reads the run dir's shard JSONLs + run_meta.json + relaxed structures and writes a Markdown report
and a per-structure CSV:

  * setup      commit, host, cores, shards x xtb threads, xtb budget, opt-in size gate, real
               elapsed time (run_meta started -> finished)
  * outcomes   built / failed, with the failure messages
  * timing     build_s = the relaxed build alone (no pre-opt, no scoring); median / mean / p25 /
               p75 / max; CPU hours (sum) vs elapsed -> parallel efficiency
  * budget     which geometry each build kept, read from the .xyz comment line (as
               top100/compare_top100.py does): GFN2 finished, GFN-FF only, or the assembled
               structure. GFN-FF / assembled means the xtb budget ran out or xtb failed -- those
               build times are CAPPED, not real GFN2 times
  * by CN, by size (atoms incl. H) and by opt-in escalation (>= --optin-min-atoms complexes)
  * --baseline RUN_DIR (optional): the same refcodes from an older run, side by side. An older
    run without build_s is compared on wall_s, which also includes the diagnostic pre-opt build
    and scoring, so that column is NOT like-for-like (stated in the report)

    python pilot100/mecobi/mecobi_timing_report.py                        # newest fair_* run
    python pilot100/mecobi/mecobi_timing_report.py --run pilot100/mecobi/fair_d988e1a \
        --baseline pilot100/mecobi/mecobi_det
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import json
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent   # pilot100/mecobi/
BENCH = HERE.parents[1]                  # benchmark root
SIZE_BINS = [(0, 50), (50, 100), (100, 150), (150, 10**6)]


def _abs(p: str) -> Path:
    q = Path(p)
    return (q if q.is_absolute() else BENCH / q).resolve()


def load_rows(run_dir: Path) -> dict:
    rows = {}
    for f in sorted(glob.glob(str(run_dir / "_results_shard*.jsonl"))):
        shard = Path(f).stem.replace("_results_", "")
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                r["shard"] = shard
                rows[r["refcode"]] = r          # last row wins (resumed runs)
    return rows


def relax_level(xyz_path: Path) -> str:
    """GFN2 / GFN-FF / assembled from the .xyz comment line ('energy: <Eh>' written by xtb):
    GFN2 totals are ~-1..-3 Eh/atom, GFN-FF ~-0.1..-0.3; no energy = the assembled geometry."""
    if not xyz_path.exists():
        return "none"
    lines = xyz_path.read_text(encoding="utf-8").split("\n")
    try:
        n = int(lines[0])
    except (ValueError, IndexError):
        return "unknown"
    m = re.search(r"energy:\s*(-?[\d.]+)", lines[1] if len(lines) > 1 else "")
    if not m:
        return "assembled"
    return "GFN2" if float(m.group(1)) / n < -0.5 else "GFN-FF"


def n_atoms(ligands) -> int:
    n = 1
    for smi in ligands:
        mol = Chem.MolFromSmiles(smi)
        n += Chem.AddHs(mol).GetNumAtoms() if mol is not None else 0
    return n


def summ(v):
    v = sorted(float(x) for x in v)
    if not v:
        return None
    q = st.quantiles(v, n=4, method="inclusive") if len(v) > 1 else [v[0]] * 3
    return {"n": len(v), "median": st.median(v), "mean": st.fmean(v), "p25": q[0], "p75": q[2],
            "max": v[-1], "sum": sum(v)}


def row_s(label, s):
    if not s:
        return f"| {label} | 0 | – | – | – | – | – |"
    return (f"| {label} | {s['n']} | {s['median']:.1f} | {s['mean']:.1f} | {s['p25']:.1f} | "
            f"{s['p75']:.1f} | {s['max']:.0f} |")


def time_of(r):
    t = r.get("build_s", r.get("wall_s"))
    return t if isinstance(t, (int, float)) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None, help="run dir (default: newest pilot100/mecobi/fair_*)")
    ap.add_argument("--baseline", default=None, help="optional older run dir to compare against")
    ap.add_argument("--out", default=None, help="default: <run dir>/timing_report.md")
    cfg = ap.parse_args()

    if cfg.run:
        run_dir = _abs(cfg.run)
    else:
        cands = [Path(d) for d in glob.glob(str(HERE / "fair_*")) if Path(d).is_dir()]
        if not cands:
            raise SystemExit("no pilot100/mecobi/fair_* run found; pass --run")
        run_dir = max(cands, key=lambda d: d.stat().st_mtime)
    rows = load_rows(run_dir)
    if not rows:
        raise SystemExit(f"no _results_shard*.jsonl in {run_dir}")
    meta_p = run_dir / "run_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    import gzip
    bundle = {r["refcode"]: r for r in json.load(gzip.open(BENCH / "benchmark_bundle.json.gz", "rt"))}
    gate = meta.get("optin_min_atoms")

    for rc, r in rows.items():
        r["time_s"] = time_of(r)
        r["relax"] = relax_level(run_dir / "structures" / f"{rc}.xyz") if r.get("built") else "none"
        if "n_atoms" not in r and rc in bundle:
            r["n_atoms"] = n_atoms(bundle[rc]["ligands"])
    built = [r for r in rows.values() if r.get("built")]
    failed = [r for r in rows.values() if not r.get("built")]
    t_key = "build_s" if any("build_s" in r for r in rows.values()) else "wall_s"

    L = ["# MeCoBi — pilot 100 timing report\n", f"Run dir: `{run_dir}`\n", "## Setup\n"]
    elapsed = None
    if meta.get("started") and meta.get("finished"):
        elapsed = (dt.datetime.fromisoformat(meta["finished"])
                   - dt.datetime.fromisoformat(meta["started"])).total_seconds()
    for k, lab in (("commit", "MeCoBi commit"), ("host", "host"), ("cpu_count", "cores"),
                   ("shards", "shards"), ("xtb_threads", "xtb threads / shard"),
                   ("xtb_timeout_s", "xtb budget per structure (s)"),
                   ("optin_min_atoms", "opt-in size gate (atoms)"), ("started", "started"),
                   ("finished", "finished")):
        if k in meta:
            L.append(f"- {lab}: **{meta[k]}**")
    if elapsed is not None:
        L.append(f"- elapsed (real wall clock): **{elapsed / 3600:.2f} h**")
    if not meta:
        L.append("- no run_meta.json (not a run_pilot100.py run): setup unknown")
    L.append(f"- time measured: `{t_key}`"
             + (" (relaxed build alone)" if t_key == "build_s"
                else " (includes the pre-opt diagnostic build + scoring)") + "\n")

    L.append("## Outcomes\n")
    L.append(f"Built **{len(built)}/{len(rows)}**. Failed: {len(failed)}.")
    for r in failed:
        L.append(f"- {r['refcode']} ({r.get('metal')}, CN{r.get('cn')}): {r.get('error', '?')}")
    L.append("")

    L.append("## Per-structure time (s), built only\n")
    L.append("| set | n | median | mean | p25 | p75 | max |\n|---|---|---|---|---|---|---|")
    s_all = summ(r["time_s"] for r in built if r["time_s"] is not None)
    L.append(row_s("all built", s_all))
    for lv in ("GFN2", "GFN-FF", "assembled"):
        L.append(row_s(f"kept {lv}", summ(r["time_s"] for r in built
                                          if r["relax"] == lv and r["time_s"] is not None)))
    cpu = sum(r["time_s"] for r in rows.values() if r["time_s"] is not None)
    L.append(f"\n- CPU time (Σ {t_key}, all rows): **{cpu / 3600:.2f} h**")
    if elapsed:
        sh = meta.get("shards") or 1
        L.append(f"- parallel efficiency: CPU / (shards × elapsed) = "
                 f"**{cpu / (sh * elapsed) * 100:.0f} %** (scoring + I/O between builds are "
                 "outside build_s, so this reads a little low)")
    shard_sum = defaultdict(float)
    for r in rows.values():
        if r["time_s"] is not None:
            shard_sum[r["shard"]] += r["time_s"]
    L.append("\n| shard | Σ time (h) |\n|---|---|")
    for k in sorted(shard_sum):
        L.append(f"| {k} | {shard_sum[k] / 3600:.2f} |")

    lv_n = defaultdict(int)
    for r in built:
        lv_n[r["relax"]] += 1
    L.append("\n## Which geometry each build kept (xtb budget)\n")
    L.append("| kept | n | meaning |\n|---|---|---|")
    mean = {"GFN2": "GFN2 relax finished inside the budget",
            "GFN-FF": "budget ran out (or GFN2 failed) after GFN-FF: time is capped",
            "assembled": "no xtb geometry kept (budget/xtb failure): time is capped",
            "unknown": "unreadable .xyz"}
    for lv in ("GFN2", "GFN-FF", "assembled", "unknown"):
        if lv_n[lv]:
            L.append(f"| {lv} | {lv_n[lv]} | {mean[lv]} |")
    L.append("")

    def group_table(title, key_fn, keys):
        L.append(f"## {title}\n")
        L.append("| group | n | built | median s | max s | GFN2 kept |\n|---|---|---|---|---|---|")
        for k in keys:
            rs = [r for r in rows.values() if key_fn(r) == k]
            if not rs:
                continue
            b = [r for r in rs if r.get("built")]
            t = [r["time_s"] for r in b if r["time_s"] is not None]
            L.append(f"| {k} | {len(rs)} | {len(b)} | "
                     f"{st.median(t):.1f} | {max(t):.0f} | " if t else
                     f"| {k} | {len(rs)} | {len(b)} | – | – | ")
            L[-1] += f"{sum(r['relax'] == 'GFN2' for r in b)} |"
        L.append("")

    group_table("By coordination number", lambda r: r.get("cn"),
                sorted({r.get("cn") for r in rows.values()}))

    def size_bin(r):
        n = r.get("n_atoms")
        for lo, hi in SIZE_BINS:
            if n is not None and lo <= n < hi:
                return f"{lo}–{hi - 1}" if hi < 10**6 else f"≥{lo}"
        return "?"
    group_table("By size (atoms, H included)", size_bin,
                [f"{lo}–{hi - 1}" if hi < 10**6 else f"≥{lo}" for lo, hi in SIZE_BINS])
    if gate:
        esc = [r for r in rows.values() if r.get("optin_escalation")]
        L.append(f"Opt-in escalation (≥ {gate} atoms): "
                 + (", ".join(f"{r['refcode']} ({r.get('n_atoms')} at., "
                              f"{'built' if r.get('built') else 'failed'}, "
                              f"{r['time_s']:.0f} s, {r['relax']})" if r['time_s'] is not None
                              else r['refcode'] for r in esc) or "none") + "\n")

    if cfg.baseline:
        b_dir = _abs(cfg.baseline)
        base = load_rows(b_dir)
        common = [rc for rc in rows if rc in base and rows[rc].get("built")
                  and base[rc].get("built")]
        bk = "build_s" if any("build_s" in r for r in base.values()) else "wall_s"
        tb = [time_of(base[rc]) for rc in common]
        tn = [rows[rc]["time_s"] for rc in common]
        pairs = [(a, b) for a, b in zip(tn, tb) if a is not None and b is not None]
        L.append(f"## Against baseline `{b_dir.name}` ({len(pairs)} refcodes built in both)\n")
        if not pairs:
            raise SystemExit(f"baseline {b_dir} shares no built refcode with this run "
                             "(pilot 1 vs pilot 2?)")
        L.append("| run | time field | median s | mean s | Σ h |\n|---|---|---|---|---|")
        L.append(f"| this run | {t_key} | {st.median([a for a, _ in pairs]):.1f} | "
                 f"{st.fmean([a for a, _ in pairs]):.1f} | {sum(a for a, _ in pairs) / 3600:.2f} |")
        L.append(f"| {b_dir.name} | {bk} | {st.median([b for _, b in pairs]):.1f} | "
                 f"{st.fmean([b for _, b in pairs]):.1f} | {sum(b for _, b in pairs) / 3600:.2f} |")
        if bk != t_key:
            L.append(f"\n> Not like-for-like: the baseline's `{bk}` also contains the diagnostic "
                     "pre-opt build and the scoring, and the two runs used different code, "
                     "shard counts and budgets. Read it as an upper bound on the old build time.")
        ratio = [a / b for a, b in pairs if b > 0]
        if ratio:
            L.append(f"\nMedian per-structure ratio this/baseline: **{st.median(ratio):.2f}×**.")
        L.append("")

    out = Path(cfg.out) if cfg.out else run_dir / "timing_report.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    cols = ["refcode", "metal", "cn", "n_atoms", "shard", "built", "time_s", "relax",
            "optin_escalation", "build_mode", "error"]
    with open(out.with_name("timing_per_structure.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(rows.values(), key=lambda r: r["refcode"]))
    print(f"{len(built)}/{len(rows)} built; median {t_key} "
          f"{s_all['median']:.1f} s\n-> {out}" if s_all else f"-> {out}")


if __name__ == "__main__":
    main()
