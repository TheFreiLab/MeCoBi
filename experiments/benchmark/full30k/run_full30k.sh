#!/usr/bin/env bash
# Full 30k CSD structural benchmark -- clean rebuild with the current MeCoBi (Linux / Keisan).
#
# Built by pilot100/mecobi/run_pilot100.py, i.e. with EXACTLY the pilot-100 / 10x100 settings (all
# GUI guards, metal stand-in, size-gated opt-ins at >= 150 atoms, 900 s xtb budget, no diagnostic
# pre-opt build, 1 xtb thread per worker), so the 30k run is directly comparable with the pilots.
# run_meta.json in the out dir records the commit, host, settings and the xtb version.
#
# No CIFs needed here: the crystal geometry + site-map targets (benchmark_targets.json), the
# reference spheres / cores and the hydride corrections were all extracted locally and committed.
#
#   ./full30k/run_full30k.sh [SHARDS]                 # default 48 parallel workers
#   TAG=_v2 ./full30k/run_full30k.sh 48               # -> full30k/mecobi_30k_v2/ (new code = new dir)
#   HYDRIDES= ./full30k/run_full30k.sh 48             # without the hydride corrections
#   python full30k/progress.py --run-dir full30k/mecobi_30k   # live progress, second terminal
#
# The runner RESUMES an out dir that already holds results, so a new code version needs a new TAG.
set -euo pipefail
cd "$(dirname "$0")/.."   # benchmark root: run.py + the frozen bundle/spheres/donors live there

SHARDS="${1:-48}"
TAG="${TAG:-}"
HYDRIDES="${HYDRIDES-benchmark_hydrides.json}"
OUT="full30k/mecobi_30k${TAG}"
TARGETS="benchmark_targets.json"

[ -f "${TARGETS}" ] || { echo "missing ${TARGETS} (extract it locally with enrich_bundle_geometry.py)"; exit 1; }

echo "=== building the full benchmark into ${OUT}/ (${SHARDS} workers, hydrides: ${HYDRIDES:-none}) ==="
python pilot100/mecobi/run_pilot100.py --shards "${SHARDS}" --refcodes all \
  --targets "${TARGETS}" --out-dir "${OUT}" ${HYDRIDES:+--hydrides "${HYDRIDES}"}

echo "=== done. score: python full30k/full30k_score.py --run-dir ${OUT#full30k/} --workers ${SHARDS} ==="
