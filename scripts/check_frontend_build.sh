#!/usr/bin/env bash
# Fail if the committed frontend production bundle is stale.
#
# The React source (frontend/src) and its built bundle (src/mecobi/web/static)
# are BOTH committed — FastAPI serves the built bundle, so a fresh checkout runs
# the GUI with no Node toolchain. This check rebuilds from the pinned toolchain
# (npm ci uses frontend/package-lock.json; Node pinned via .nvmrc) and fails if the
# committed bundle differs, catching a forgotten `npm run build` before it ships a
# stale UI. Do NOT hand-edit the minified assets — regenerate and commit them.
#
# Usage (from repo root, or anywhere): bash scripts/check_frontend_build.sh
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root/frontend"
npm ci
npm run build

cd "$repo_root"
if ! git diff --quiet -- src/mecobi/web/static; then
  echo "ERROR: the committed frontend bundle is stale." >&2
  echo "Run 'npm ci && npm run build' in frontend/ and commit src/mecobi/web/static/." >&2
  git --no-pager diff --stat -- src/mecobi/web/static >&2
  # A --stat alone cannot tell you WHY a build differs across platforms, which is the
  # hard case this check exists to catch. Show the readable files in full; the minified
  # assets are deliberately excluded (a diff of them is unreadable and enormous).
  echo "--- diff of text files (minified assets omitted) ---" >&2
  git --no-pager diff -- 'src/mecobi/web/static/*.html' 'src/mecobi/web/static/**/*.txt' >&2
  exit 1
fi
echo "OK: committed frontend bundle matches a fresh build."
