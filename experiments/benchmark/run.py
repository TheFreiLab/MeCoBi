"""Shardable, resumable MeCoBi structural-benchmark runner.

For each complex in the frozen bundle: build with MeCoBi from the MetaLig inputs
(metal, oxidation state, ligand SMILES) + xtb-relax, then score the relaxed
coordination sphere against the experimental crystal sphere (spheres file) with the
metrics in metrics.py: coordination-number match, coordination-geometry shape match
+ continuous shape measure (CShM), donor-donor distance-matrix RMSD, metal-donor
bond RMSD. Writes per-complex JSONL; aggregate.py combines shards into the table.

    python run.py --shard 0/32 --spheres _spheres_all.json        # one of 32 shards
    for i in $(seq 0 31); do python run.py --shard $i/32 & done; wait
"""
from __future__ import annotations

import argparse
import gzip
import json
import shutil
import time
from pathlib import Path

import numpy as np

import bench_overrides
import donor_map
import hydrides
import metrics as M
from mecobi import assembly, isomers, pipeline
from mecobi.model import Complex, Geometry, Ligand, Metal
from rdkit import Chem, RDLogger
RDLogger.DisableLog("rdApp.*")

HERE = Path(__file__).parent


def _dirs(m, d):
    v = np.asarray(d) - np.asarray(m)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def n_atoms_total(ligands) -> int:
    """Atoms in the assembled complex, H included (metal + every ligand) -- the size gate for
    --optin-min-atoms. Unparseable ligand SMILES count 0 (the build will fail on them anyway)."""
    n = 1
    for smi in ligands:
        mol = Chem.MolFromSmiles(smi)
        n += Chem.AddHs(mol).GetNumAtoms() if mol is not None else 0
    return n


def score(build_xyz, sym, cn, exp, donor_idx=None):
    """metrics comparing the relaxed build to the experimental sphere `exp`.

    An eta5/6-arene or eta2/3 pi-cap is ONE coordination SITE in MeCoBi's model, but a
    crystallographic CN counts every M-C contact (a piano-stool reads as a 7-9-vertex
    solid), so scoring the raw spheres penalises the chemically-free ring rotation and
    inflates the angular metrics (PEZTIX poly 29 -> 0, MALXII 19 -> 0.1 collapsed). Score
    the ANGULAR/site metrics (shape, poly, dmat) on the haptic-COLLAPSED spheres — caps
    reduced to centroids on both build and crystal, like-for-like — and fall back to the
    raw spheres only when the two collapse to different site counts (rare; flagged).

    A hydride-corrected sphere (hydrides.sphere: located M-H appended as ``H`` donors) is scored
    with the build's own hydrides as sites: they count for shape / poly / dmat, but NOT for the
    bond RMSD (X-ray M-H distances are systematically short). ``cn`` is then read off the sphere.
    A build that carries no hydride (made from the uncorrected inputs) falls back to the heavy
    donors alone, exactly as before.

    ``donor_idx`` (donor_map.donor_indices): the build's heavy donors identified from its
    molecular graph; without it (or when the build's ligands could not be matched) the nearest
    non-H atoms are taken. Either way the CN is also MEASURED: ``cn_detected`` counts the atoms
    bonded to the metal, and ``cn_match`` is True only when that equals the target CN and every
    scored donor is actually bonded -- so a wrong sphere is visible instead of being scored as
    if it had the target CN."""
    n_h = hydrides.n_in_sphere(exp)
    if n_h:
        cn = len(exp["donors"])
        b = M.coordination_sphere(build_xyz, sym, cn, n_h, donor_idx)
        if b is not None and len(b[1]) < cn:      # no hydride in the build -> heavy-only score
            exp, n_h = hydrides.strip_sphere(exp), 0
            cn = len(exp["donors"])
    b = M.coordination_sphere(build_xyz, sym, cn, n_h, donor_idx)
    if not b:
        return None
    syms, P = M.parse_xyz(build_xyz)
    mi = syms.index(sym)
    graph = donor_idx is not None and len(donor_idx) == cn - n_h
    heavy_idx = M._heavy_donors(syms, P, mi, cn - n_h, donor_idx)
    cn_det = donor_map.detected_cn(syms, P, mi, count_h=n_h > 0)
    bonded = all(donor_map.ml_bonded(sym, syms[j], float(np.linalg.norm(P[j] - P[mi])))
                 for j in heavy_idx)
    m_b, d_b, _ = b
    m_e, d_e = np.asarray(exp["metal_xyz"]), np.asarray(exp["donors"])
    heavy = len(d_e) - n_h                         # hydrides are appended last on both sides
    brmsd, boff = M.bond_rmsd(d_e[:heavy], m_e, d_b[:heavy], m_b)  # radial: raw M-X, heavy only
    # Collapse haptic caps to centroid sites on both sides for the angular metrics.
    cb = M.hapticity_collapsed_sphere(build_xyz, sym, cn, n_h, donor_idx)
    m_e2, d_e2 = M.collapse_crystal_sphere(exp)
    collapsed = cb is not None and len(cb[1]) == len(d_e2) and len(d_e2) >= 2
    cap_mismatch = cb is not None and len(cb[1]) != len(d_e2)
    if collapsed:
        m_b, d_b = cb[0], cb[1]
        m_e, d_e = m_e2, d_e2
    scn = len(d_b)                       # effective (site) CN the angular metrics run at
    dir_e, dir_b = _dirs(m_e, d_e), _dirs(m_b, d_b)
    es, ec = M.best_shape(dir_e, scn)
    bs, bc = M.best_shape(dir_b, scn)
    dmat = M.local_distance_matrix_rmsd(d_e - m_e, d_b - m_b)
    # Label-free geometry fidelity: how far the build polyhedron is from the crystal
    # polyhedron itself. Fair where the ideal-shape label is ambiguous (CN5, CN8).
    poly = M.shape_deviation(dir_b, dir_e)
    return {"exp_shape": es, "exp_cshm": round(ec, 2), "build_shape": bs,
            # no ideal shape for this CN ('' on both sides) is "not scorable", not a match
            "build_cshm": round(bc, 2), "shape_match": (es == bs) if es and bs else None,
            "poly_cshm": None if np.isnan(poly) else round(poly, 2),
            "dmat_rmsd": None if np.isnan(dmat) else round(dmat, 3),
            "bond_rmsd": None if np.isnan(brmsd) else round(brmsd, 3),
            "bond_offset": None if np.isnan(boff) else round(boff, 3),
            "site_cn": scn, "cap_collapsed": bool(collapsed and scn != cn),
            "cap_mismatch": bool(cap_mismatch), "n_hydride": n_h,
            "cn_expected": cn, "cn_detected": cn_det, "cn_match": bonded and cn_det == cn,
            "donor_source": "graph" if graph else "nearest"}


def _load_json(path):
    """Read a .json or .json.gz file."""
    path = Path(path)
    if str(path).endswith(".gz"):
        return json.loads(gzip.open(path, "rt", encoding="utf-8").read())
    return json.loads(path.read_text(encoding="utf-8"))


def _load_bundle(name):
    gz = HERE / f"{name}.json.gz"
    return _load_json(gz if gz.exists() else HERE / f"{name}.json")


def _isomer_spec(cx, tgt):
    """Pick the isomer to build from a crystal target: (IsomerSpec | None, mode).

    ``ok`` target  -> the exact crystal donor->site map (deterministic isomer).
    ``geometry_only`` -> that geometry's default isomer, when it fits the perceived
    denticities (else fall back to the heuristic -- e.g. a metallocene mis-labelled by the
    collapsed-shape read). No target / absent -> None (MeCoBi's heuristic pick).

    The crystal site_map counts an eta-cap / eta2-diene by its CARBON contacts (a COD reads as
    4 sites), but perception collapses each pi-bond to ONE site. When that leaves the map's site
    count out of step with the perceived denticities (ROSJIU/NARNUP: COD -> denticity 2, so the
    6-site octahedral map no longer fits the CN4 [2,2] set), the map is stale -- drop it and let
    MeCoBi pick the geometry itself (CN4 square planar), the same path the clean COD cases take.
    """
    if not tgt:
        return None, "heuristic"
    n_dent = sum(l.denticity or 0 for l in cx.ligands)
    if tgt.get("status") == "ok" and tgt.get("site_map"):
        n_sites = sum(len(seg.split(",")) for seg in tgt["site_map"].split(";") if ":" in seg)
        if n_sites == n_dent:
            return isomers.parse_topology_spec(tgt["site_map"], Geometry(tgt["geometry"])), "site_map"
        return None, "heuristic_cn_mismatch"   # stale map (hapticity collapsed the CN) -> heuristic
    geom = tgt.get("geometry")
    if geom:
        try:
            return assembly.default_isomer(cx, Geometry(geom)), "geometry_only"
        except Exception:  # noqa: BLE001 -- assigned geometry doesn't fit -> heuristic
            return None, "heuristic_fallback"
    return None, "heuristic"


def _assembles(make_cx, work, override) -> bool:
    """True if the isomer in ``override`` assembles without xtb (relax=False)."""
    try:
        pipeline.build_complex(make_cx(), work, relax=False, **override)
        return True
    except Exception:  # noqa: BLE001
        return False


def _geometry_fallback(cx, tgt):
    """``(override, mode)`` for a target whose site map does not assemble: the target geometry's
    default isomer (mode ``site_map_unbuildable``), or MeCoBi's own pick when even that does not
    fit the perceived denticities (``heuristic_fallback``)."""
    try:
        spec = assembly.default_isomer(cx, Geometry(tgt["geometry"]))
        return {"isomers_override": [spec]}, "site_map_unbuildable"
    except Exception:  # noqa: BLE001
        return {}, "heuristic_fallback"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--spheres", default="benchmark_spheres_elem.json.gz")
    ap.add_argument("--bundle", default="benchmark_bundle",
                     help="bundle basename to read (.json.gz or .json), e.g. benchmark_bundle_v2")
    ap.add_argument("--xtb-timeout", type=int, default=180)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--donors", default=None,
                     help="benchmark_donors.json: hardcode ground-truth donors (bypass "
                          "pydentate, isolates the builder). Restricts to mapped complexes.")
    ap.add_argument("--refcodes", default=None,
                     help="JSON list of refcodes to restrict to (e.g. pilot100/pilot_100.json), so "
                          "MeCoBi builds exactly the same set as the Architector runner.")
    ap.add_argument("--only", default=None,
                     help="comma-separated refcodes to build (e.g. ZEYCOV,MEKBUZ) -- a quick "
                          "inline filter on top of --refcodes, for spot-checking a few cases.")
    # relax-strategy toggles (feature/relax-clash-guard); applied to the SCORED (relaxed) build.
    ap.add_argument("--two-stage", action=argparse.BooleanOptionalAction, default=True,
                     help="GFN-FF pre-relax -> GFN2 (default on; --no-two-stage for the legacy "
                          "single-GFN2 baseline).")
    ap.add_argument("--revert-topology", action=argparse.BooleanOptionalAction, default=False,
                     help="revert xtb when it changes the connectivity (new/broken bond or metal "
                          "collapse). Default OFF -- letting xtb re-form bonds repairs bad initial "
                          "placements; --revert-topology restores the old guard for A/B.")
    ap.add_argument("--linear-restraint", action=argparse.BooleanOptionalAction, default=True,
                     help="180 deg restraint on end-on linear donors (CN-/CO/...). Default on.")
    ap.add_argument("--uff-fallback", action=argparse.BooleanOptionalAction, default=False,
                     help="when every xtb tier fails (Y/Sc/lanthanide GFN2 divergence), relax with "
                          "a metal-excluded UFF force field instead of the raw assembly. Default "
                          "OFF (it worsened the Y cases; prefer metal substitution); --uff-fallback "
                          "to test.")
    ap.add_argument("--orient-bulky", action=argparse.BooleanOptionalAction, default=True,
                     help="when a bulky monodentate (phosphine) clashes with a neighbour, UFF "
                          "de-clash the ligand shell, kept only if it reduces the overlap (IFASOA "
                          "PPh3 clash). Default on; --no-orient-bulky to disable.")
    ap.add_argument("--reposition-donors", action=argparse.BooleanOptionalAction, default=True,
                     help="slide a stranded monodentate (a bulky phenoxide pushed to ~3 A by the "
                          "generic 2.5 A site shell + sterics, OGOLAX) rigidly in to its CSD M-L "
                          "reference, so xtb starts from a correct sphere. Default on.")
    ap.add_argument("--reposition-polydentates", action=argparse.BooleanOptionalAction,
                     default=False,
                     help="OPT-IN escalation: slide stranded chelates/pincers in to their CSD M-L "
                          "reference too (build_complex reposition_polydentates). Default OFF.")
    ap.add_argument("--oxo-antifusion-floors", action=argparse.BooleanOptionalAction,
                     default=False,
                     help="OPT-IN escalation: pre-floor terminal oxo/nitrido donors against fusion "
                          "before the relax (build_complex oxo_antifusion_floors). Default OFF.")
    ap.add_argument("--clear-metal-region", action=argparse.BooleanOptionalAction, default=True,
                     help="rotate a monodentate whose backbone folded into the metal-donor region "
                          "so its body points outward (bonder stays on its site). Default on.")
    ap.add_argument("--declash-torsion", action=argparse.BooleanOptionalAction, default=True,
                     help="spin crowded bulky monodentates about their M-donor axis to mesh "
                          "interpenetrating substituent arms (VOFRAJ). Rigid, cone-preserving. "
                          "Default on.")
    ap.add_argument("--haptic-guard", action=argparse.BooleanOptionalAction, default=True,
                     help="pin sigma aryl-carbon donors' ortho M-C distances so xtb can't slip "
                          "them to eta-arene (UMIZOG mesityl). Default on.")
    ap.add_argument("--planar-guard", action=argparse.BooleanOptionalAction, default=True,
                     help="pin sp2 N/O donors (pyridine, phenol) coplanar with the metal so xtb "
                          "can't bend them pseudo-sp3 (HUJCAR, MOFGEU). Default on.")
    ap.add_argument("--mchammer", action=argparse.BooleanOptionalAction, default=True,
                     help="run MCHammer at all. --no-mchammer turns it OFF entirely: xtb starts "
                          "from the raw stk placement (donors on the ideal site vectors), never "
                          "running the optimiser. Default on.")
    ap.add_argument("--reembed-crowded", action=argparse.BooleanOptionalAction, default=True,
                    help="re-embed a collapsed sphere of monodentates/chelates (bulky ligands "
                         "threaded through each other: Pt(PPh3)4, Pt(BINAP)2) jointly by "
                         "distance geometry with the donors pinned. Default on.")
    ap.add_argument("--mchammer-fallback", action=argparse.BooleanOptionalAction, default=True,
                     help="skip MCHammer and hand the raw stk placement to xtb when MCHammer "
                          "collapses the assembly (bad M-L / angles / a fused or on-metal atom). "
                          "Default on; thresholds via env MECOBI_MCH_* (BADNESS_TOL, METAL_CLASH, "
                          "FUSE, ML_MIN/MAX, ANGLE).")
    ap.add_argument("--antifusion", action=argparse.BooleanOptionalAction, default=True,
                     help="if xtb fuses two donors of DIFFERENT ligands (a NEW inter-ligand donor-"
                          "donor bond -- cis carbonyls -> C-C, oxo onto a thiolate, iodide onto an "
                          "amide), re-relax ONCE from the assembly with distance floors on exactly "
                          "those pairs and keep it if the fusion cleared. Self-selecting: a second "
                          "xtb runs only for the few %% that fuse; clean spheres are untouched. "
                          "Default ON; --no-antifusion to A/B.")
    ap.add_argument("--metal-surrogate", action=argparse.BooleanOptionalAction, default=False,
                     help="relax metals whose GFN2 diverges (Y) as an xtb-friendly surrogate of "
                          "the same charge/d-count (Y(III)->Sc(III)), restoring the real metal "
                          "after. Default OFF; --metal-surrogate to test. Env MECOBI_XTB_SURROGATE "
                          "overrides the map (e.g. 'Y:Sc,La:Sc').")
    ap.add_argument("--conformer-ensemble", type=int, default=1, metavar="N",
                     help="embed N conformers per sigma-chelate (denticity>=2) and keep the "
                          "least-strained after coordination-directed pre-organisation. "
                          "Default 1 = single deterministic embed (proven); use e.g. 10 to A/B "
                          "the ensemble (its net effect is still unproven on a clean xtb).")
    ap.add_argument("--coord-map", action=argparse.BooleanOptionalAction, default=True,
                     help="for a flexible high-denticity wrapper, pin its donors to the target "
                          "sites and let RDKit distance geometry fold the backbone around them "
                          "(MetalloGen-style), instead of a free embed + rigid placement. Default "
                          "on (TIZJUI 32->5); --no-coord-map to A/B.")
    ap.add_argument("--registry-topology", action="store_true",
                     help="build site_map complexes through the hand-tuned fixed topology (the GUI "
                          "path) when one exists for the denticity partition. Reproduces the crystal "
                          "only for unique-isomer partitions (square-planar 1bi+2mono, ...); may "
                          "build the wrong isomer for cis/trans partitions. Off by default.")
    ap.add_argument("--optin-min-atoms", type=int, default=0, metavar="N",
                     help="hard-crowded-sphere escalation: for a complex with >= N atoms (H "
                          "included) also turn on the two size-driven opt-ins, "
                          "--reposition-polydentates and --oxo-antifusion-floors, for THAT "
                          "complex only. 0 (default) = never; the global flags still apply.")
    ap.add_argument("--preopt", action=argparse.BooleanOptionalAction, default=True,
                     help="also build + score the un-relaxed assembly (pre_* columns, "
                          "structures_preopt/). Diagnostic only; --no-preopt skips it so wall_s "
                          "is the relaxed build alone. build_s always times just the relaxed build.")
    ap.add_argument("--hydrides", default=None, metavar="FILE",
                     help="benchmark_hydrides.json (dataprep/build_hydride_corrections.py): put "
                          "back the hydrides the mined inputs lost where the CIF locates them -- "
                          "[H-] ligands, OS and CN raised by one per hydride, the crystal sphere "
                          "and the geometry/site-map target re-read WITH the H. Default off (the "
                          "mined inputs as they are).")
    ap.add_argument("--hydride-classes", default=",".join(hydrides.DEFAULT_CLASSES),
                     help="comma-separated classes of --hydrides to apply (clean, high_cn, "
                          "polyhydride, h2_mixed, short_mh; 'all' for every one). Default: clean.")
    ap.add_argument("--out-dir", default=None,
                     help="write the results JSONL + structures/ (+ scratch) into this dir "
                          "(e.g. mecobi/); default = the benchmark root.")
    ap.add_argument("--targets", default=None,
                     help="benchmark_targets.json (enrich_bundle_geometry.py): build the "
                          "crystal-derived geometry + isomer site-map for each refcode instead "
                          "of MeCoBi's heuristic pick. This is the DETERMINISTIC mode -- no "
                          "oracle. Refcodes with an 'ok' target build that exact isomer; "
                          "'geometry_only' targets build that geometry's default isomer; "
                          "refcodes absent from the file fall back to the heuristic.")
    cfg = ap.parse_args()
    import os
    os.environ["MECOBI_N_CONFORMERS"] = str(cfg.conformer_ensemble)  # read lazily in _chem
    os.environ["MECOBI_COORD_MAP"] = "1" if cfg.coord_map else "0"
    i, n = (int(x) for x in cfg.shard.split("/"))

    bundle = _load_bundle(cfg.bundle)
    spheres = _load_json(HERE / cfg.spheres if not Path(cfg.spheres).is_absolute() else cfg.spheres)
    donors = (_load_json(HERE / cfg.donors if not Path(cfg.donors).is_absolute() else cfg.donors)
              if cfg.donors else None)
    targets = (_load_json(HERE / cfg.targets if not Path(cfg.targets).is_absolute() else cfg.targets)
               if cfg.targets else None)
    keep = set(_load_json(HERE / cfg.refcodes if not Path(cfg.refcodes).is_absolute()
                          else cfg.refcodes)) if cfg.refcodes else None
    only = {x.strip() for x in cfg.only.split(",") if x.strip()} if cfg.only else None
    relax_opts = {"two_stage_relax": cfg.two_stage, "linear_restraint": cfg.linear_restraint,
                  "uff_fallback": cfg.uff_fallback, "orient_bulky": cfg.orient_bulky,
                  "reposition_donors": cfg.reposition_donors,
                  "reposition_polydentates": cfg.reposition_polydentates,
                  "oxo_antifusion_floors": cfg.oxo_antifusion_floors,
                  "clear_metal_region": cfg.clear_metal_region,
                  "declash_torsion": cfg.declash_torsion,
                  "haptic_guard": cfg.haptic_guard,
                  "planar_guard": cfg.planar_guard,
                  "mchammer": cfg.mchammer,
                  "mchammer_fallback": cfg.mchammer_fallback,
                  "reembed_crowded": cfg.reembed_crowded,
                  "antifusion_guard": cfg.antifusion, "metal_surrogate": cfg.metal_surrogate,
                  "revert_on_bond_change": cfg.revert_topology,
                  "registry_for_sites": cfg.registry_topology}
    overrides = bench_overrides.load()
    # ground-truth donor atoms, used to find the build's donors by graph when SCORING (also when
    # --donors is not given: the build itself still perceives its donors)
    score_donors = donors if donors is not None else _load_json(HERE / "benchmark_donors.json")
    hyd = {}
    if cfg.hydrides:
        classes = (None if cfg.hydride_classes == "all"
                   else tuple(c.strip() for c in cfg.hydride_classes.split(",") if c.strip()))
        hyd = hydrides.load(cfg.hydrides, classes)
        if not hyd:
            raise SystemExit(f"--hydrides {cfg.hydrides}: no corrections loaded (missing file, "
                             f"or no entry of class {cfg.hydride_classes})")
    base = (HERE / cfg.out_dir) if cfg.out_dir else HERE
    base.mkdir(parents=True, exist_ok=True)
    work = Path(base / f"_run_shard{i}of{n}"); work.mkdir(exist_ok=True)
    structures = base / "structures"; structures.mkdir(exist_ok=True)   # relaxed .xyz kept
    structures_pre = base / "structures_preopt"; structures_pre.mkdir(exist_ok=True)  # assembled
    out = base / f"_results_shard{i}of{n}.jsonl"
    done = {json.loads(l)["refcode"] for l in out.read_text().splitlines()} if out.exists() else set()

    recs = [r for k, r in enumerate(bundle) if k % n == i and r["refcode"] in spheres
            and (donors is None or r["refcode"] in donors)
            and (keep is None or r["refcode"] in keep)
            and (only is None or r["refcode"] in only)]
    if cfg.limit:
        recs = recs[:cfg.limit]
    fh = out.open("a", encoding="utf-8")
    built = scored = 0
    t0 = time.perf_counter()
    for k, r in enumerate(recs, 1):
        rc = r["refcode"]
        if rc in done:
            continue
        r = bench_overrides.record(r, overrides)          # confirmed OS/charge input fixes
        donors_row = bench_overrides.donors(rc, donors[rc] if donors else None, overrides)
        h = hyd.get(rc)                                   # located hydrides the mining lost
        r, donors_row = hydrides.record(r, h), hydrides.donors(donors_row, h)
        score_spec = hydrides.donors(
            bench_overrides.donors(rc, score_donors.get(rc), overrides), h)
        exp = hydrides.sphere(spheres[rc], h)
        row = {"refcode": rc, "metal": r["metal"], "ox": r["ox"], "cn": r["cn"], "built": False}
        if h:
            row["hydrides_added"] = h["n_h"]
        cx_opts = relax_opts
        if cfg.optin_min_atoms > 0:
            row["n_atoms"] = n_atoms_total(r["ligands"])
            row["optin_escalation"] = row["n_atoms"] >= cfg.optin_min_atoms
            if row["optin_escalation"]:
                cx_opts = {**relax_opts, "reposition_polydentates": True,
                           "oxo_antifusion_floors": True}
        ts = time.perf_counter()

        def _make_cx():
            ligs = [Ligand(s) for s in r["ligands"]]
            if donors_row is not None:
                for lig, atoms in zip(ligs, donors_row):
                    if atoms:
                        lig.donor_override = list(atoms)
            return Complex(metal=Metal(r["metal"], r["ox"]), name=rc, ligands=ligs)

        try:
            cx = _make_cx()
            spec, mode = (None, "heuristic")
            # a hydride-corrected complex takes the target re-read with the H (the frozen one is
            # for the hydride-less sphere); none stored -> MeCoBi's heuristic pick
            tg = None if targets is None else (h.get("target") if h else targets.get(rc))
            if targets is not None:
                pipeline.resolve_perception(cx)  # default_isomer needs perceived denticities
                spec, mode = _isomer_spec(cx, tg)
            row["build_mode"] = mode
            if tg:
                row["target_geometry"] = tg.get("geometry")
            override = {"isomers_override": [spec]} if spec is not None else {}
            # 1) PRE-OPT: the assembled isomer, no xtb -- so a bad post-relax score can be told
            #    apart (right isomer vs xtb drift/collapse). Score + keep it.
            if cfg.preopt:
                try:
                    pre = pipeline.build_complex(_make_cx(), work, relax=False, **override,
                                                 registry_for_sites=cfg.registry_topology)
                    pre_xyz = Path(pre[0].xyz_path).read_text()
                    shutil.copyfile(pre[0].xyz_path, structures_pre / f"{rc}.xyz")
                    sc_pre = score(pre_xyz, r["metal"], r["cn"], exp, donor_map.from_xyz(
                        pre_xyz, r["metal"], r["ligands"], score_spec))
                    if sc_pre:
                        row.update({f"pre_{kk}": vv for kk, vv in sc_pre.items()})
                except Exception as e:  # noqa: BLE001 -- pre-opt is diagnostic; don't fail the row
                    row["pre_error"] = f"{type(e).__name__}: {e}"[:120]
            # 2) RELAXED build (the scored one) + its connectivity guard flag.
            tb = time.perf_counter()
            try:
                try:
                    res = pipeline.build_complex(_make_cx(), work, relax=True,
                                                 xtb_timeout_s=cfg.xtb_timeout, **override,
                                                 **cx_opts)
                except Exception:  # noqa: BLE001
                    # A crystal site map that does not ASSEMBLE (a chelate that cannot span the
                    # sites it is given): build that geometry's default isomer instead -- what
                    # the target extraction's build check used to decide up front, so targets
                    # can be extracted without it (CIF-only, minutes instead of hours for 30k).
                    # When that isomer does not assemble either, MeCoBi's own pick is tried.
                    # A failure that is not the map's (xtb; the map does assemble) stays an error.
                    if mode != "site_map" or _assembles(_make_cx, work, override):
                        raise
                    override, mode = _geometry_fallback(cx, tg)
                    if override and not _assembles(_make_cx, work, override):
                        override, mode = {}, "heuristic_fallback"   # that geometry does not fit
                    row["build_mode"] = mode
                    res = pipeline.build_complex(_make_cx(), work, relax=True,
                                                 xtb_timeout_s=cfg.xtb_timeout, **override,
                                                 **cx_opts)
            finally:  # time the relaxed build alone (no pre-opt, no scoring), even when it fails
                row["build_s"] = round(time.perf_counter() - tb, 2)
            row["built"] = True; built += 1
            row["connectivity_ok"] = bool(getattr(res[0], "connectivity_ok", True))
            # the actual bonder atom indices (global, in the .xyz order) so the report can draw the
            # metal-donor bonds exactly, not a distance guess.
            row["donor_indices"] = [int(x) for x in (res[0].donor_indices or [])]
            build_xyz = Path(res[0].xyz_path).read_text()
            shutil.copyfile(res[0].xyz_path, structures / f"{rc}.xyz")   # keep for re-analysis / release
            sc = score(build_xyz, r["metal"], r["cn"], exp, donor_map.from_xyz(
                build_xyz, r["metal"], r["ligands"], score_spec))
            if sc:
                row.update(sc); scored += 1
        except Exception as e:  # noqa: BLE001
            row["error"] = f"{type(e).__name__}: {e}"[:120]
        row["wall_s"] = round(time.perf_counter() - ts, 2)  # per-complex build time (incl. xtb)
        fh.write(json.dumps(row) + "\n"); fh.flush()
        if k % 25 == 0:
            print(f"  shard {i}/{n}: {k}/{len(recs)} built={built} scored={scored} "
                  f"({(time.perf_counter()-t0)/k:.1f}s/cpx)", flush=True)
    fh.close()
    print(f"shard {i}/{n} done: {built} built, {scored} scored of {len(recs)} -> {out}")


if __name__ == "__main__":
    main()
