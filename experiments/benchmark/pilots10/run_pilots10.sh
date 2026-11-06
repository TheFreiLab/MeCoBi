#!/usr/bin/env bash
# Run the 10x100 stratified benchmark (Linux / Keisan, where xtb + pydentate work).
#
# No CCDC CIFs are needed here: the crystal geometry+site-map targets were extracted LOCALLY (where
# the CIFs live) into pilots10/targets.json, which is committed. This driver just builds each pilot
# into its own out-dir; the bundle/spheres/cores/donors JSONs it reads are all committed too.
#
# Every pilot is built by pilot100/mecobi/run_pilot100.py -- the SAME settings as the pilot-100
# tool comparison (all GUI guards, metal stand-in, size-gated opt-ins at >= 150 atoms, 900 s xtb
# budget, no diagnostic pre-opt build, 1 xtb thread per shard), so the ten pilots and pilot 100
# are directly comparable. Each run dir gets a run_meta.json (commit, host, settings, timings).
#
# Prereqs: pilots10/pilot_r01..r10.json and pilots10/targets.json (both committed). Metrics come
# from pilots10/pilots10_metrics.py afterwards.
#
#   ./pilots10/run_pilots10.sh [SHARDS]
#     SHARDS   parallel worker processes per pilot (default 8)
#   TAG=_v2 ./pilots10/run_pilots10.sh 8     # -> pilots10/run_rNN_v2/ (new code = new run dirs)
#
#   HYDRIDES=benchmark_hydrides.json TAG=_hyd ./pilots10/run_pilots10.sh 8   # hydrides put back
#
# A run dir that already holds results is refused (the runner RESUMES, so re-using it would mix
# two code versions); pass a new TAG, or RESUME=1 to deliberately finish an interrupted run.
# On AMD EPYC Zen4/Zen5 (9xxx) set OPENBLAS_CORETYPE=SandyBridge until PR #90 is merged, or xtb
# can segfault silently and leave unrelaxed geometries.
set -euo pipefail
cd "$(dirname "$0")/.."   # benchmark root: run.py + the frozen bundle/spheres/donors live there

SHARDS="${1:-8}"
TAG="${TAG:-}"
PDIR="pilots10"
TARGETS="${PDIR}/targets.json"

[ -f "${TARGETS}" ] || { echo "missing ${TARGETS} (extract it locally with enrich_bundle_geometry.py, see pilots10/README.md)"; exit 1; }

for pi in $(seq -w 1 10); do
  out="${PDIR}/run_r${pi}${TAG}"
  if [ -z "${RESUME:-}" ] && compgen -G "${out}/_results_shard*.jsonl" > /dev/null; then
    echo "${out}/ already has results -- use a new TAG (or RESUME=1 to finish that run)"; exit 1
  fi
done

for pi in $(seq -w 1 10); do
  out="${PDIR}/run_r${pi}${TAG}"
  echo "=== building pilot r${pi} -> ${out} ==="
  python pilot100/mecobi/run_pilot100.py --shards "${SHARDS}" \
    --refcodes "${PDIR}/pilot_r${pi}.json" --targets "${TARGETS}" --out-dir "${out}" \
    ${HYDRIDES:+--hydrides "${HYDRIDES}"}
done

echo "=== done. now score: python pilots10/pilots10_metrics.py --run-tmpl 'run_r{:02d}${TAG}' ==="
