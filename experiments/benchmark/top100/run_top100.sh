#!/usr/bin/env bash
# Rebuild the 100 LARGEST benchmark complexes (by total atoms incl. H; top100_largest.json) under
# several build configurations, to A/B the large-ligand embed fallback and the opt-in escalation
# flags against the original full-30k run. Linux / Keisan, same inputs as full30k/run_full30k.sh.
#
#   ./top100/run_top100.sh [SHARDS] [CONFIG ...]     # from experiments/benchmark/
#   ./top100/run_top100.sh 6                         # all configs, 6 workers each (24 procs)
#   ./top100/run_top100.sh 8 fallback repoly         # just these two
#   TAG=_232fd3e ./top100/run_top100.sh 24 both      # -> top100/runs/both_232fd3e/ (a new code
#                                                    #    version must NOT resume an old run dir)
#   TAG=_t3600 XTB_TIMEOUT=3600 XTB_THREADS=2 ./top100/run_top100.sh 12 both
#                                                    # let GFN2 actually finish on 200-490 atoms
#
# XTB_TIMEOUT (default 180, as the 30k run) is the TOTAL xtb budget per structure (GFN-FF + GFN2);
# when it runs out the build keeps the GFN-FF (or assembled) geometry, so a spin/--uhf change
# can't show. XTB_THREADS (default 1) = threads per xtb call; keep SHARDS * XTB_THREADS <= cores.
#
# Configs (each -> top100/runs/<config>${TAG}/, resumable: rerunning skips refcodes already done):
#   fallback  current code (embed fallback) + default flags -- the new baseline
#   repoly    + --reposition-polydentates
#   oxo       + --oxo-antifusion-floors
#   both      + both opt-in flags
# Score afterwards:  python top100/compare_top100.py
set -euo pipefail
cd "$(dirname "$0")/.."

SHARDS="${1:-6}"; shift || true
TAG="${TAG:-}"
XTB_TIMEOUT="${XTB_TIMEOUT:-180}"
XTB_THREADS="${XTB_THREADS:-1}"
CONFIGS=("$@"); [ ${#CONFIGS[@]} -eq 0 ] && CONFIGS=(fallback repoly oxo both)

declare -A FLAGS=(
  [fallback]=""
  [repoly]="--reposition-polydentates"
  [oxo]="--oxo-antifusion-floors"
  [both]="--reposition-polydentates --oxo-antifusion-floors"
)

export OMP_NUM_THREADS="${XTB_THREADS}" MKL_NUM_THREADS="${XTB_THREADS}" OMP_STACKSIZE=1G
export MECOBI_XTB_THREADS="${XTB_THREADS}"   # optimize.py sets xtb's OMP threads from this

for c in "${CONFIGS[@]}"; do
  [ -n "${FLAGS[$c]+x}" ] || { echo "unknown config: $c (known: ${!FLAGS[*]})"; exit 1; }
  out="top100/runs/${c}${TAG}"
  echo "=== ${c}: ${SHARDS} shards x ${XTB_THREADS} thr, xtb budget ${XTB_TIMEOUT}s," \
       "flags: ${FLAGS[$c]:-(defaults)} -> ${out}/ ==="
  for i in $(seq 0 $((SHARDS - 1))); do
    # shellcheck disable=SC2086  # FLAGS[$c] is an intentional word-split flag list
    python run.py --shard "${i}/${SHARDS}" \
      --donors benchmark_donors.json --targets benchmark_targets.json \
      --refcodes top100/top100_largest.json --out-dir "${out}" \
      --xtb-timeout "${XTB_TIMEOUT}" ${FLAGS[$c]} \
      > "top100/runs_${c}${TAG}_shard${i}.log" 2>&1 &
  done
done
wait
echo "=== done. score: python top100/compare_top100.py ==="
