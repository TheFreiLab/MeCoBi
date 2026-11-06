# MeCoBi quickstart (terminal, from scratch)

A step-by-step walkthrough to go from a fresh machine to a built metal-complex
`.xyz` on the command line. No prior MeCoBi knowledge assumed. Everything here is
the local core package — the web GUI is optional (see the end).

---

## 1. Prerequisites

- **Python 3.11-3.14** (all four are tested; 3.12 is what MeCoBi is developed and
  deployed on).
- **git**.
- **conda / miniconda** — recommended, because the optional xtb relaxation step
  ships as a compiled binary on conda-forge. If you never need xtb relaxation you
  can skip conda and use a plain `pip` virtualenv (see 3b).

Check what you have:

```bash
python --version      # 3.11 to 3.14
git --version
```

---

## 2. Get the code

```bash
git clone https://github.com/TheFreiLab/MeCoBi.git
cd MeCoBi
```

pydentate (the ligand-perception model) is **vendored inside the repo**, weights
included — there is nothing extra to download for perception to work.

---

## 3a. Install (conda — recommended, includes xtb)

```bash
conda create -n mecobi python=3.12
conda activate mecobi
conda install -c conda-forge xtb          # the only non-pip dependency
pip install -e .                          # installs mecobi + its Python deps
```

## 3b. Install (pip only — no xtb relaxation)

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -e .
```

Without xtb, always build with `--no-relax` (assembly + MCHammer only).

> **Windows + conda note:** put xtb on `PATH` by **appending**, not prepending
> (`export PATH="$PATH:/path/to/miniconda3/Library/bin"`). Prepending conda's
> `Library/bin` ahead of everything can shadow the DLLs RDKit loads and break the
> import.

Confirm the CLI is installed:

```bash
mecobi --help
```

---

## 4. Your first build

Create a CSV — one complex per line, `metal, oxidation_state, ligand SMILES…`
(free-ligand SMILES; MeCoBi infers how each binds):

```bash
cat > my_complexes.csv <<'CSV'
Metal,Charge,L1,L2,L3,L4
Pt,2,N,N,[Cl-],[Cl-]
Ir,3,c1ccc(-c2ccccn2)nc1,c1ccc(-c2ccccn2)nc1,[Cl-],[Cl-]
CSV
```

Build (skip xtb for a quick first run):

```bash
mecobi build my_complexes.csv --output-dir ./out --no-relax
```

You get one `.xyz` per complex under `./out/`. The paths are printed to stdout;
progress, warnings and failures go to stderr. A complex that fails does not stop
the batch, but the exit status tells you: `0` everything built, `1` one or more
complexes failed (the rest are written), `2` bad arguments or unreadable CSV.

Add xtb relaxation (needs xtb installed) by dropping `--no-relax`:

```bash
mecobi build my_complexes.csv --output-dir ./out
```

Also write `.mol` / `.pdb` files (bonds come from the assembled graph, so
metal–donor bonds are explicit):

```bash
mecobi build my_complexes.csv --output-dir ./out --format xyz,mol,pdb
```

Enumerate every isomer instead of one canonical structure:

```bash
mecobi build my_complexes.csv --output-dir ./out --all-isomers
```

When more than one isomer is relaxed with xtb, the output lists them
**lowest-GFN2-energy first**, e.g.:

```
./out/Pt_cis_c0.xyz    (+0.00 kcal/mol  *lowest*)
./out/Pt_trans_c0.xyz  (+6.98 kcal/mol)
```

An isomer whose relaxation changed the bonding (a ligand fusion, a fragment, a
collapse onto the metal, an unbound donor) is a different molecule, so it is
never ranked: it is listed after the valid isomers, marked
`(connectivity changed in relaxation; not ranked)`, with the reason on stderr.
The web API reports the same as `connectivity_ok: false`.

---

## 5. Build one specific isomer (donor-index notation)

For the **CLI**, add an `isomer` column to pin donors and/or the exact isomer.
The web GUI has no notation input (it uses the donor panel and the 3D Assign
scene instead, see step 7). The notation is
`ligIdx[(donorAtoms)][:sites]` per ligand, `;`-separated (site ids are the
canonical coordination-site numbering; atom indices are 0-based heavy-atom
indices of that ligand's SMILES). Because the notation itself contains commas,
**wrap the `isomer` cell in double quotes** so the CSV keeps it as one field:

```bash
cat > cis_trans.csv <<'CSV'
Metal,Charge,L1,L2,L3,L4,isomer
Ir,3,c1ccc(-c2ccccn2)nc1,c1ccc(-c2ccccn2)nc1,[Cl-],[Cl-],"0:0,2;1:3,5;2:1;3:4"
CSV
mecobi build cis_trans.csv --output-dir ./out --no-relax
```

---

## 6. Recover SMILES from a geometry (reverse)

Go the other way — pull metal + ligand SMILES (and coordinating atoms) back out
of an `.xyz`:

```bash
mecobi reverse ./out/Pt_01_c0.xyz --notation
```

Other representations of the same structure (each needs the overall complex
charge):

```bash
mecobi reverse ./out/Pt_01_c0.xyz --charge 0 --msmiles               # MetalloGen m-SMILES (built in)
mecobi reverse ./out/Pt_01_c0.xyz --charge 0 --backend xyz2mol_tm    # whole-complex SMILES
mecobi reverse ./out/Pt_01_c0.xyz --charge 0 --trex                  # T-REX notation
```

The last two need the optional backends: `pip install -e ".[reverse-tm]"`.

---

## 7. Optional: the web GUI

No install needed to try it: the same GUI runs at <https://mecobi.york.ac.uk>.
To run it locally:

```bash
pip install -e ".[web]"
python -m uvicorn mecobi.web:app --port 8000
# open http://127.0.0.1:8000
```

Paste a CSV (or **Load sample**) → **Parse** → pick geometries / correct donors →
**Build** (or **Build all** for a queued batch with a progress bar) → view in 3D,
download individually or as a zip, or export SMILES / Complex SMILES / T-REX /
m-SMILES for the results. The production frontend bundle is committed and served
by FastAPI, so running the GUI needs no Node.

The GUI has no notation input: to build a specific isomer, pick donors in the
row's donor panel and assign sites in the 3D **Assign** scene. An `isomer` column
in a pasted or uploaded CSV is ignored by the GUI; the CLI (step 5) supports it.

### Running the GUI on your own machine

The local GUI is the same application as the public site, with the same defaults.
It listens on `127.0.0.1` only, so nobody else on the network can reach it (leave
`--host` alone unless you mean to share it). Stop it with **Ctrl+C**. Relaxation
needs xtb, exactly as for the CLI (step 3a).

Things that behave as on the public server:

- **Results are deleted after 24 hours.** They are kept in a `mecobi_data` folder
  in the system temp directory (`%TEMP%\mecobi_data` on Windows), and the same
  24-hour cleanup runs locally. Download what you want to keep.
- **Builds run one at a time.** There is a single build worker, so a large job
  uses one core. Restarting the server marks a job that was running as failed;
  the structures it had already finished are kept.
- **Limits:** at most 1,000 complexes per job and 1,000 structures waiting at
  once (with *all isomers*, every isomer counts), and 20 builds, job submissions
  or exports per minute. Clicking **Build** on many rows in quick succession can
  hit that last one; use **Build all** instead.

The limits are environment variables, so you can raise them for your own machine.
Set them in the terminal you start the server from. The structure limit must be
at least as large as your biggest job, or the job is rejected:

```bash
# Linux / macOS
MECOBI_MAX_COMPLEXES=5000 MECOBI_MAX_PENDING_STRUCTURES=20000 MECOBI_RATE_MAX=1000 \
  python -m uvicorn mecobi.web:app --port 8000
```

```powershell
# Windows PowerShell
$env:MECOBI_MAX_COMPLEXES = "5000"
$env:MECOBI_MAX_PENDING_STRUCTURES = "20000"
$env:MECOBI_RATE_MAX = "1000"
python -m uvicorn mecobi.web:app --port 8000
```

For thousands of complexes the CLI (step 4) is usually the better tool: it has no
job limits, writes straight into the folder you choose, and keeps nothing in temp.
It also builds one complex at a time; to use several cores, split the CSV and run
one `mecobi build` per part, each with its own `--output-dir`.

---

## Troubleshooting

- **`xtb executable 'xtb' not found`** — install it (`conda install -c
  conda-forge xtb`) or build with `--no-relax`.
- **RDKit import error on Windows after activating conda** — see the PATH note in
  step 3; append conda's `Library/bin`, don't prepend.
- **A ligand looks mis-perceived** (wrong donors) — in the CLI, pass the `isomer`
  column with explicit donor atoms (step 5). In the GUI, use the donor-correction
  panel after parsing.
