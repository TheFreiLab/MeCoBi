"""Timing report for a MetalloGen pilot run (metallogen_run.py output), done carefully.

Reads the shard JSONLs and writes a Markdown report + a per-structure CSV. What it takes care of:

  * **Retries.** A resumed sweep leaves several rows per refcode. Launch failures (run_status
    'error', wall_s 0.0 -- the CLI never started) are counted separately. Each refcode keeps its
    LAST real attempt (ok / timeout / no_result).
  * **Censoring.** A 'timeout' row's wall_s is the kill time (the --timeout cap + ~2 s grace), not
    a generation time: the true time is only known to be >= the cap. So:
      - "completed" timings use run_status == 'ok' only (the honest per-structure speed, but
        biased LOW because the slowest complexes were cut off);
      - the median over ALL attempts, counting timeouts at the cap, is a LOWER BOUND on the true
        median (valid while fewer than half the attempts time out).
  * **Partial builds.** metallogen_run.py keeps the finished result_*.xyz even from a killed run.
    Each is a fully relaxed conformer, but the conformer search is INCOMPLETE. A timeout that
    still left a structure counts as built. It is flagged
    'timeout_partial' and kept apart from the completed builds.
  * **Parallel cost.** CPU time = sum of wall_s over all real attempts (shard-count independent).
    Elapsed time is estimated as the largest per-shard sum (this assumes the shards started
    together on one machine). Parallel efficiency = CPU / (shards x elapsed).
  * **Input caveats.** Flags refcodes whose MetalloGen input differs from what the MeCoBi runner
    now uses (benchmark_overrides.json corrections that MetalloGen never received, plus the known
    post-run data fixes in KNOWN_INPUT_CHANGES).

    python pilot100/metallogen/metallogen_timing_report.py
    python pilot100/metallogen/metallogen_timing_report.py --dir ../arch_comparison/metallogen
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent   # pilot100/metallogen/
PILOT = HERE.parent                      # pilot100/
BENCH = PILOT.parent                     # benchmark root
REPO = BENCH.parents[1]

# Data fixes committed AFTER the 2026-08-04 MetalloGen run, which its m-SMILES therefore lack.
KNOWN_INPUT_CHANGES = {
    "KILHAO": "donors fixed 2026-08-10 (7d2aa71: bonds through the two aryl carbanion carbons)",
}


def _default_dir() -> Path:
    for d in (HERE / "metallogen_det", REPO / "arch_comparison" / "metallogen"):
        if glob.glob(str(d / "_metallogen_results_shard*.jsonl")):
            return d
    return HERE / "metallogen_det"


def load(run_dir: Path):
    """-> ({refcode: final attempt row}, n_raw_rows, n_launch_errors, [shard files])."""
    files = sorted(glob.glob(str(run_dir / "_metallogen_results_shard*.jsonl")))
    final: dict[str, dict] = {}
    n_raw = n_launch = 0
    for f in files:
        shard = Path(f).stem.replace("_metallogen_results_", "")
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            r["shard"] = shard
            n_raw += 1
            if r.get("run_status") == "error":
                n_launch += 1
                final.setdefault(r["refcode"], r)       # only if no real attempt ever lands
                continue
            final[r["refcode"]] = r                     # last real attempt wins
    return final, n_raw, n_launch, files


def outcome(r: dict) -> str:
    s = r.get("run_status")
    if s == "ok":
        return "completed"
    if s == "timeout":
        return "timeout_partial" if r.get("built") else "timeout_empty"
    if s == "no_result":
        return "no_result"
    return "launch_error"


def summary(vals):
    vals = sorted(float(v) for v in vals)
    if not vals:
        return None
    q = st.quantiles(vals, n=4, method="inclusive") if len(vals) > 1 else [vals[0]] * 3
    return {"n": len(vals), "median": st.median(vals), "mean": st.fmean(vals), "p25": q[0],
            "p75": q[2], "min": vals[0], "max": vals[-1], "sum": sum(vals)}


def fmt_s(s, keys=("n", "median", "mean", "p25", "p75", "min", "max")):
    if not s:
        return "| " + " | ".join("–" for _ in keys) + " |"
    return "| " + " | ".join(str(s[k]) if k == "n" else f"{s[k]:.1f}" for k in keys) + " |"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None, help="run dir with the shard JSONLs.")
    ap.add_argument("--msmiles", default=str(HERE / "benchmark_msmiles_pilot.json"))
    ap.add_argument("--pilot", default=str(PILOT / "pilot_100.json"))
    ap.add_argument("--timeout", type=float, default=900.0,
                    help="the --timeout the run used (metallogen_run.py default 900 s).")
    ap.add_argument("--out", default=str(HERE / "metallogen_timing_report.md"))
    ap.add_argument("--csv", default=str(HERE / "metallogen_timing_per_structure.csv"))
    cfg = ap.parse_args()

    run_dir = Path(cfg.dir).resolve() if cfg.dir else _default_dir()
    rows, n_raw, n_launch, files = load(run_dir)
    if not rows:
        raise SystemExit(f"no _metallogen_results_shard*.jsonl in {run_dir}")
    msm = json.loads(Path(cfg.msmiles).read_text()) if Path(cfg.msmiles).exists() else {}
    pilot = json.loads(Path(cfg.pilot).read_text()) if Path(cfg.pilot).exists() else []
    overrides = json.loads((BENCH / "benchmark_overrides.json").read_text())

    for rc, r in rows.items():
        r["outcome"] = outcome(r)
        r["geometry"] = r.get("geometry") or msm.get(rc, {}).get("geometry")
        caveats = []
        if rc in overrides:
            caveats.append("benchmark_overrides correction not in MetalloGen input: "
                           + (overrides[rc].get("note", "") or "see benchmark_overrides.json")[:90])
        if rc in KNOWN_INPUT_CHANGES:
            caveats.append(KNOWN_INPUT_CHANGES[rc])
        if r.get("note"):
            caveats.append(r["note"])
        r["caveat"] = "; ".join(caveats)

    real = [r for r in rows.values() if r["outcome"] != "launch_error"]
    by_out = Counter(r["outcome"] for r in rows.values())
    t_done = summary(r["wall_s"] for r in real if r["outcome"] == "completed")
    t_all = summary(min(r["wall_s"], cfg.timeout) if r["run_status"] == "timeout" else r["wall_s"]
                    for r in real)
    t_built = summary(min(r["wall_s"], cfg.timeout) if r["run_status"] == "timeout" else r["wall_s"]
                      for r in real if r.get("built"))
    n_to = by_out["timeout_partial"] + by_out["timeout_empty"]
    shards = defaultdict(list)
    for r in real:
        shards[r["shard"]].append(r["wall_s"])
    shard_sum = {k: sum(v) for k, v in shards.items()}
    cpu = sum(shard_sum.values())
    elapsed = max(shard_sum.values()) if shard_sum else 0.0
    n_sh = len(shard_sum)
    missing = [rc for rc in pilot if rc not in rows]

    L = []
    L.append("# MetalloGen — pilot 100 timing report\n")
    L.append(f"Run dir: `{run_dir}`  ")
    L.append(f"Shard files: {len(files)} ({', '.join(sorted(shard_sum))})  ")
    L.append(f"Timeout cap: {cfg.timeout:.0f} s per complex (+ ~2 s kill grace)\n")
    L.append("## Coverage\n")
    L.append(f"- Pilot refcodes: **{len(pilot)}**; attempted by MetalloGen: **{len(rows)}**; "
             f"never attempted (no deterministic m-SMILES): **{len(missing)}**"
             + (f" — {', '.join(missing)}" if missing else ""))
    L.append(f"- Raw JSONL rows: {n_raw}, of which **{n_launch} launch failures** "
             "(run_status `error`, wall_s 0.0: the CLI never started, the refcode was retried). "
             "They are excluded from every timing below.\n")
    L.append("## Outcomes (last real attempt per refcode)\n")
    L.append("| outcome | n | meaning |\n|---|---|---|")
    meaning = {"completed": "finished inside the cap, structure written",
               "timeout_partial": "killed at the cap; fully relaxed conformer(s) exist but the "
                                  "conformer search is INCOMPLETE (counted as built)",
               "timeout_empty": "killed at the cap, no structure",
               "no_result": "finished inside the cap without any structure",
               "launch_error": "only launch failures recorded"}
    for k in ("completed", "timeout_partial", "timeout_empty", "no_result", "launch_error"):
        if by_out[k]:
            L.append(f"| {k} | {by_out[k]} | {meaning[k]} |")
    n_built = sum(1 for r in real if r.get("built"))
    L.append(f"\nBuilt: **{n_built}/{len(real)}** "
             f"({by_out['completed']} completed + {by_out['timeout_partial']} partial). "
             f"Timeouts: **{n_to}/{len(real)}** ({n_to / len(real) * 100:.0f} %).\n")

    L.append("## Per-structure wall time (s)\n")
    L.append("| set | n | median | mean | p25 | p75 | min | max |\n|---|---|---|---|---|---|---|---|")
    L.append("| completed only (honest speed; biased low, the slowest were cut off) "
             + fmt_s(t_done))
    L.append("| all real attempts, timeouts at the cap (median = LOWER BOUND) " + fmt_s(t_all))
    L.append("| all built (completed + partial; partial = cap) " + fmt_s(t_built))
    if n_to * 2 >= len(real):
        L.append("\n> ≥ 50 % of attempts timed out: even the lower-bound median is undefined.")
    L.append("\nReport the **completed-only median** as MetalloGen's per-structure time, and "
             "state the timeout fraction next to it. The all-attempts median is a lower bound, "
             "not an estimate.\n")

    L.append("## Compute cost (shard-count independent)\n")
    L.append(f"- CPU time (Σ wall_s, all real attempts): **{cpu / 3600:.2f} h** "
             f"({cpu / 60:.0f} min); of which timeouts {sum(min(r['wall_s'], cfg.timeout + 2) for r in real if r['run_status'] == 'timeout') / 3600:.2f} h")
    L.append(f"- CPU time for completed builds only: {t_done['sum'] / 3600:.2f} h" if t_done else "")
    L.append(f"- Estimated elapsed (largest shard sum, shards assumed concurrent): "
             f"**{elapsed / 3600:.2f} h** on {n_sh} shards; parallel efficiency "
             f"{cpu / (n_sh * elapsed) * 100:.0f} %" if elapsed else "")
    L.append("\n| shard | attempts | Σ wall (h) |\n|---|---|---|")
    for k in sorted(shard_sum):
        L.append(f"| {k} | {len(shards[k])} | {shard_sum[k] / 3600:.2f} |")
    L.append("\nThe JSONLs record no host, core count or thread settings. MetalloGen hard-codes "
             "ORCA `nproc=1`, and the xtb it spawns inherits the environment (OMP_NUM_THREADS "
             "was not set by metallogen_run.py). Record the machine next to the timings.\n")

    for key, title in (("cn", "By coordination number"), ("geometry", "By crystal geometry")):
        L.append(f"## {title}\n")
        L.append(f"| {key} | n | completed | timeout | no_result | median completed (s) | "
                 "median all, capped (s) |\n|---|---|---|---|---|---|---|")
        groups = defaultdict(list)
        for r in real:
            groups[r.get(key)].append(r)
        for g in sorted(groups, key=lambda x: (x is None, str(x))):
            rs = groups[g]
            done = [r["wall_s"] for r in rs if r["outcome"] == "completed"]
            allc = [min(r["wall_s"], cfg.timeout) for r in rs]
            L.append(f"| {g} | {len(rs)} | {len(done)} | "
                     f"{sum(r['run_status'] == 'timeout' for r in rs)} | "
                     f"{sum(r['outcome'] == 'no_result' for r in rs)} | "
                     f"{st.median(done):.1f} | " if done else
                     f"| {g} | {len(rs)} | 0 | {sum(r['run_status'] == 'timeout' for r in rs)} | "
                     f"{sum(r['outcome'] == 'no_result' for r in rs)} | – | ")
            L[-1] += f"{st.median(allc):.1f} |"
        L.append("")

    cav = [(rc, r) for rc, r in sorted(rows.items()) if r["caveat"]]
    L.append("## Caveats (input differs from the current benchmark input, or approximate "
             "site mapping)\n")
    if cav:
        L.append("| refcode | outcome | caveat |\n|---|---|---|")
        for rc, r in cav:
            L.append(f"| {rc} | {r['outcome']} | {r['caveat']} |")
        L.append("\nExclude these from a paired MeCoBi/MetalloGen comparison, or rerun them "
                 "with regenerated m-SMILES (`make_metallogen_msmiles.py`).")
    else:
        L.append("None.")
    Path(cfg.out).write_text("\n".join(x for x in L if x is not None) + "\n", encoding="utf-8")

    cols = ["refcode", "metal", "cn", "geometry", "shard", "run_status", "outcome", "built",
            "wall_s", "censored", "natoms", "n_results", "picked_result", "caveat"]
    with open(cfg.csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for rc, r in sorted(rows.items()):
            r["censored"] = r.get("run_status") == "timeout"
            w.writerow([r.get(c, "") for c in cols])
    print(f"{len(real)} attempted, {n_built} built, {n_to} timeouts, {n_launch} launch errors "
          f"skipped\n-> {cfg.out}\n-> {cfg.csv}")


if __name__ == "__main__":
    main()
