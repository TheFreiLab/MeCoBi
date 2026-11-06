# MeCoBi production image — FastAPI + job queue + xtb/PyTorch in one container.
#
# Deployment shape (as at mecobi.york.ac.uk): a web server on the host (Apache)
# terminates TLS and reverse-proxies to this container on a fixed internal port.
# Everything MeCoBi needs lives in here.
#
#   docker build -t mecobi:latest .
#   docker run -d --name mecobi --restart unless-stopped \
#       --cpus=3 --memory=6g --memory-swap=6g --pids-limit=256 \
#       --stop-timeout=30 \
#       --log-opt max-size=10m --log-opt max-file=3 \
#       --mount type=volume,source=mecobi-data,target=/tmp/mecobi_data \
#       -p 127.0.0.1:8000:8000 \
#       -e FORWARDED_ALLOW_IPS=<docker bridge subnet, see below> \
#       mecobi:latest
#
# Resource values above are starting examples for a 4-vCPU/8-GB host,
# not validated capacity. Configure a host filesystem quota/low-disk monitor
# for the volume and Docker logs; memory/PID limits do not constrain disk use.
# The named volume preserves the queue/results across container replacement;
# application cleanup expires finished outputs after 24 hours (checked hourly).
# The 30-second container stop grace exceeds the app's 10-second worker wait,
# but a longer complex can still be interrupted and recovered as failed on boot.
#
# NOTE (data persistence): this deployment is PERSISTENT, not ephemeral. With the
# named volume above, job results and the SQLite queue survive container restart
# AND replacement — they are not wiped on restart. The only thing that removes them
# is the application's own retention sweep: finished/failed outputs expire 24 hours
# after completion (checked hourly): persistent storage with a 24-hour data lifetime.
# For a truly ephemeral deployment instead, drop the --mount flag (data then lives
# in the container's writable layer and is lost on removal).
#
# Two network flags matter and are easy to get wrong:
#
#   -p 127.0.0.1:8000:8000   Publish to loopback ONLY, so the app is reachable
#                            solely through Apache. Binding 0.0.0.0 would expose
#                            uvicorn directly on the VM's public interface.
#   FORWARDED_ALLOW_IPS      The address Apache's traffic arrives FROM, so uvicorn
#                            trusts its X-Forwarded-For and the rate limiter keys on
#                            real client IPs. With host Apache -> bridged container
#                            that is the Docker gateway, NOT 127.0.0.1. Get it wrong
#                            and uvicorn silently ignores the header, collapsing every
#                            user into ONE shared rate-limit bucket. Verify after
#                            deploy by curling /api/whoami THROUGH Apache: "client"
#                            must be a real public address.
#                            The gateway is deployment-specific (docker network
#                            inspect bridge): the default is 172.17.0.1, but a managed
#                            daemon may use another range. Trust the whole bridge
#                            SUBNET rather than one address: uvicorn accepts CIDR, so
#                            a reconfigured daemon cannot silently break the rate limiter.
#
#   --log-opt max-size       The container log is otherwise uncapped. A vulnerability
#                            scan alone can add thousands of lines, and a full disk
#                            stops the queue worker.
#
# Wheel-only builder for the optional `reverse-tm` backends (Jensen's xyz2mol_tm ->
# "Complex SMILES", Kevlishvili's trex -> "T-REX notation"). Neither is on PyPI, and
# xyz2mol_tm only packages its subpackages through setuptools-scm's git file finder: a
# source tarball installs WITHOUT xyz2mol_tm.huckel_to_smiles and fails to import. So the
# wheels are built here from pinned commits, with git, and only the two pure-Python wheels
# reach the production image (no git in it). Bump a SHA to take an upstream update.
FROM python:3.12-slim AS reverse-tm-wheels
ARG XYZ2MOL_TM_SHA=db2734b084045ef895528c7a3d5040d38da23983
ARG TREX_SHA=66dc90d38406790df75b2a11d0d6ffb6ae5b5802
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip wheel --no-cache-dir --no-deps -w /wheels \
        "xyz2mol_tm @ git+https://github.com/jensengroup/xyz2mol_tm@${XYZ2MOL_TM_SHA}" \
        "trex-notation @ git+https://github.com/iliak14/trex@${TREX_SHA}"

# micromamba base: xtb is the one dependency with no wheel — it is a compiled Fortran
# binary distributed through conda-forge. Everything else is pip, pinned by
# constraints.txt. Pinning xtb to the version the test suite runs against (6.7.1)
# keeps relaxed geometries reproducible.
FROM mambaorg/micromamba:2-debian12-slim

# Pinned here rather than inline so a version bump is a one-line, reviewable change.
ARG XTB_VERSION=6.7.1
ARG PYTHON_VERSION=3.12

# No apt layer at all: every runtime dependency comes from conda-forge or pip, and the
# HEALTHCHECK below uses conda's own python rather than a system curl. That keeps the
# image smaller and, more importantly, keeps LD_LIBRARY_PATH (set below) from steering
# a system binary onto conda's libssl/libz.

# libstdcxx-ng is explicit, not incidental: conda-forge's libicu (pulled in by Python's
# sqlite3, which stk/atomlite import) is built against a newer toolchain than Debian 12
# ships, so without a modern libstdc++ INSIDE the env the loader falls back to the system
# one and `import sqlite3` dies with "CXXABI_1.3.15 not found".
# Licence texts are preserved before `clean`, not as tidiness but as a redistribution
# obligation: this image ships the xtb binary, and xtb is LGPL-3.0. conda-forge puts
# licence text ONLY in the package cache (pkgs/<pkg>/info/licenses), never in the
# installed prefix, and `micromamba clean --all` deletes that cache — so without this
# copy the image would carry an LGPL binary with no licence at all. pip packages need
# no equivalent step; they keep their own licence in site-packages/*.dist-info.
# They land in the conda prefix (writable by $MAMBA_USER; /opt itself is not) and
# `clean` does not touch it. The final `ls` fails the build loudly if xtb's text ever
# stops arriving, which is the one outcome worse than a larger image.
#
# The source is discovered with `find` rather than assumed to be
# $MAMBA_ROOT_PREFIX/pkgs: micromamba does not necessarily put its package cache
# there, and hard-coding the path failed the build with an empty glob. Searching for
# */info/licenses is location-independent and cheap on an image this size.
#
# The find result goes through a file, not a pipe, on purpose. This image's shell
# wrapper runs with pipefail, and `find /` as a non-root user exits 1 on the
# permission errors it hits along the way even with stderr silenced, which killed the
# whole chain before anything was copied. The counts printed here are what makes the
# next failure, if any, readable from the build log alone.
#
# xorg-libxrender/xorg-libxext: RDKit's compiled drawing extension (rdMolDraw2D, used
# by /api/depict_svg for the ligand-library thumbnails) links against libXrender.so.1
# / libXext.so.6. The slim base omits them, so importing rdMolDraw2D would ImportError
# and the endpoint 500s. Pulling them via conda puts the .so in /opt/conda/lib, which
# is already on LD_LIBRARY_PATH. Even the SVG path needs the shared libs to LOAD.
RUN micromamba install -y -n base -c conda-forge \
        python=${PYTHON_VERSION} \
        xtb=${XTB_VERSION} \
        libstdcxx-ng \
        xorg-libxrender \
        xorg-libxext \
        pip \
    && echo "MAMBA_ROOT_PREFIX=${MAMBA_ROOT_PREFIX:-<unset>}" \
    && echo "package cache: $(ls -d "$MAMBA_ROOT_PREFIX"/pkgs 2>/dev/null || echo '<none>')" \
    && mkdir -p "$MAMBA_ROOT_PREFIX/share/licenses" \
    && { find / -xdev -type d -path "*/info/licenses" 2>/dev/null || true; } > /tmp/licence_dirs \
    && echo "licence dirs found: $(wc -l < /tmp/licence_dirs)" \
    && head -3 /tmp/licence_dirs \
    && while read -r src; do \
           pkg=$(basename "$(dirname "$(dirname "$src")")"); \
           mkdir -p "$MAMBA_ROOT_PREFIX/share/licenses/$pkg"; \
           cp -a "$src/." "$MAMBA_ROOT_PREFIX/share/licenses/$pkg/"; \
       done < /tmp/licence_dirs \
    && echo "packages with licence text: $(ls "$MAMBA_ROOT_PREFIX/share/licenses" | wc -l)" \
    && ls "$MAMBA_ROOT_PREFIX"/share/licenses/xtb-*/COPYING.LESSER \
    && rm -f /tmp/licence_dirs \
    && micromamba clean --all --yes

# Activate the env for the remaining RUN steps (micromamba does not do this by default).
ARG MAMBA_DOCKERFILE_ACTIVATE=1

WORKDIR /app

# PyTorch FIRST, from the CPU-only index. Plain `pip install torch` on Linux pulls the
# CUDA build — several GB of NVIDIA libraries for a VM with no GPU, which would roughly
# double the image on a 15 GB disk. Installing the CPU wheel at the pinned version means
# the constraints-driven install below sees it as already satisfied.
COPY --chown=$MAMBA_USER:$MAMBA_USER constraints.txt ./
# tr -d '\r' guards against a CRLF checkout leaking a carriage return into the version.
RUN TORCH_VERSION="$(sed -n 's/^torch==//p' constraints.txt | tr -d '\r' | head -n1)" \
    && echo "pinning torch==${TORCH_VERSION} (CPU build)" \
    && python -m pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        "torch==${TORCH_VERSION}"

# Source last: the layers above change rarely, so edits to src/ reuse the cached
# dependency layers instead of reinstalling PyTorch every build.
COPY --chown=$MAMBA_USER:$MAMBA_USER pyproject.toml README.md ./
COPY --chown=$MAMBA_USER:$MAMBA_USER src ./src
RUN python -m pip install --no-cache-dir ".[web]" -c constraints.txt

# The reverse-tm wheels, installed --no-deps on purpose: trex pins rdkit==2025.3.5, which
# would fight the locked rdkit in constraints.txt, but both tools run on the locked one and
# need nothing the image lacks (numpy, pandas, networkx, pydantic, tqdm). The image used to
# skip them entirely, so the live site silently lost Complex SMILES and T-REX: the GUI only
# offers what /api/reverse/backends reports. The import check fails the BUILD instead.
COPY --from=reverse-tm-wheels /wheels /tmp/reverse-tm-wheels
RUN python -m pip install --no-cache-dir --no-deps /tmp/reverse-tm-wheels/*.whl \
    && LD_LIBRARY_PATH=/opt/conda/lib python -c "from mecobi import reverse; \
reverse._import_xyz2mol_tm(); reverse._import_trex(); \
keys = {r['key'] for r in reverse.available_representations()}; \
assert keys >= {'complex_smiles', 'trex', 'msmiles'}, keys; print('reverse representations:', sorted(keys))"

# Create the mount point as the application user. A new named volume inherits
# its ownership; existing/bind-mounted storage must also be writable by that user.
RUN mkdir -p /tmp/mecobi_data

# Results and the SQLite job DB live in /tmp/mecobi_data. Without a mount they
# survive stop/start of the same container, but are lost on container removal.
# The named volume in the example preserves restart recovery and private links.
# LD_LIBRARY_PATH is load-bearing, not tidiness. conda-forge's libicu (reached via
# Python's sqlite3, which stk/atomlite import) needs CXXABI_1.3.15, which Debian 12's
# libstdc++ does not have; the env's own libstdc++ does. Env activation sets this for a
# login shell, so `docker run ... bash -lc` worked while `docker run ... python` failed
# with "CXXABI_1.3.15 not found" — the loader fell back to the system library. Setting
# it in the image makes every entry path behave the same.
ENV LD_LIBRARY_PATH=/opt/conda/lib \
    XTB_BIN=xtb \
    OMP_NUM_THREADS=4 \
    MECOBI_XTB_THREADS=4 \
    PYTHONUNBUFFERED=1 \
    FORWARDED_ALLOW_IPS=127.0.0.1

EXPOSE 8000

# Which commit the image was built from, and that commit's date: the GUI footer shows
# "last updated <date>" from these (there is no .git inside the image). Pass both with
# --build-arg; a `docker build` without them just shows the version string.
# Declared last so a new commit only rebuilds these metadata layers.
ARG MECOBI_COMMIT=""
ARG MECOBI_BUILD_DATE=""
ENV MECOBI_COMMIT=$MECOBI_COMMIT     MECOBI_BUILD_DATE=$MECOBI_BUILD_DATE

# Report HTTP liveness only. Docker restart policies act on process exit, not
# on an unhealthy status; external monitoring/recovery is still required.
# This probe does not certify worker progress.
# Use the conda python by ABSOLUTE path: the HEALTHCHECK runs in a bare `/bin/sh -c`
# that does NOT activate the env (only the entrypoint does), so a plain `python` is
# "not found" and every probe fails -> a false "unhealthy" on a perfectly live app.
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD /opt/conda/bin/python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/api/health', timeout=4)" || exit 1

# Runs as $MAMBA_USER (uid 1000), never root.
# Single worker on purpose: the job queue is an in-process serial worker and the
# in-memory rate limiter is per-process, so a second worker would double both.
# The trusted-proxy list is NOT passed as a flag: uvicorn reads FORWARDED_ALLOW_IPS
# from the environment itself (config.py: os.environ.get("FORWARDED_ALLOW_IPS",
# "127.0.0.1")), so `docker run -e ...` is enough. An exec-form CMD would not expand
# ${FORWARDED_ALLOW_IPS} anyway — it would pass the literal string.
CMD ["uvicorn", "mecobi.web:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", \
     "--proxy-headers"]
