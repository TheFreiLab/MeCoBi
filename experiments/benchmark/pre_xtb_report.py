"""Pre-xtb sanity report: build a stratified sample of the benchmark WITHOUT xtb
relaxation and render an HTML report comparing the freshly-assembled (pre-relax)
coordination geometry against the experimental X-ray coordination sphere.

Purpose: eyeball assembly-stage issues (wrong CN, wrong shape, dissociated donors,
clashes, mis-perceived donors) BEFORE spending compute on xtb. No xtb needed.

    python experiments/benchmark/pre_xtb_report.py --n 50
    # -> _pre_xtb_report/report.html  (open in a browser)

Each card shows two 3D views (3Dmol.js, lazy-loaded to stay under the browser's
WebGL context cap):
  * LEFT  - the full pre-xtb assembled structure (all atoms), to spot clashes /
            dissociation / obviously wrong connectivity.
  * RIGHT - the coordination sphere overlay: experimental donors (green) vs the
            build's donors (orange) Kabsch-aligned into the crystal frame, metal
            at the origin. Radial (bond-length) and angular mismatch are visible
            directly. A grey stick marks each M-donor vector.
plus a metrics row (CN, shape build/exp, CShM, donor-donor distance-matrix RMSD,
M-L bond RMSD + signed offset) and any warnings.
"""
from __future__ import annotations

import argparse
import gzip
import json
import random
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

import metrics as M
from mecobi import pipeline
from mecobi.model import Complex, Ligand, Metal
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).parent


def _load_json(path: Path):
    if str(path).endswith(".gz"):
        return json.loads(gzip.open(path, "rt", encoding="utf-8").read())
    return json.loads(path.read_text(encoding="utf-8"))


def stratified_sample(bundle, spheres, n, seed=0):
    """Pick ~n build-target complexes (CN 2-9, sphere available), spread evenly
    across CN then varied across metals within each CN bucket."""
    rng = random.Random(seed)
    pool = [r for r in bundle if r["cn"] < 10 and r["refcode"] in spheres]
    by_cn = defaultdict(list)
    for r in pool:
        by_cn[r["cn"]].append(r)
    cns = sorted(by_cn)
    per = max(1, n // len(cns))
    picked = []
    for cn in cns:
        rows = by_cn[cn]
        rng.shuffle(rows)
        # spread across metals: round-robin by metal
        seen, ordered, leftovers = set(), [], []
        for r in rows:
            (ordered if r["metal"] not in seen else leftovers).append(r)
            seen.add(r["metal"])
        ordered += leftovers
        picked += ordered[:per]
    rng.shuffle(picked)
    return picked[:n]


def _align(exp_vecs, build_vecs, iters=30):
    """Kabsch+Hungarian align build donor vectors (metal-centred) onto the exp
    donor vectors; return the rotated build vectors in the exp frame."""
    Q = np.asarray(exp_vecs, float)
    P = np.asarray(build_vecs, float)
    if len(Q) != len(P) or len(Q) == 0:
        return None
    R = np.eye(3)
    perm = np.arange(len(Q))
    # scale build to exp radius so orientation search isn't biased by bond length
    qs = np.linalg.norm(Q, axis=1).mean()
    ps = np.linalg.norm(P, axis=1).mean() or 1.0
    Pw = P * (qs / ps)
    for _ in range(iters):
        _, col = linear_sum_assignment(cdist(Q, Pw @ R.T))
        perm = col
        H = Pw[perm].T @ Q
        U, _, Vt = np.linalg.svd(H)
        d = np.sign(np.linalg.det(Vt.T @ U.T))
        R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    # apply R to the UNSCALED build vectors so real bond lengths are preserved
    return (P @ R.T)[perm]


def build_card(rec, sphere, workdir, relax=False, xtb_timeout=180):
    rc = rec["refcode"]
    card = {"refcode": rc, "metal": rec["metal"], "ox": rec["ox"], "cn": rec["cn"],
            "ligands": rec["ligands"], "donor_elements": rec["donor_elements"],
            "warnings": [], "error": None, "xyz": None}
    try:
        ligs = [Ligand(s) for s in rec["ligands"]]
        dov = rec.get("_donors")  # ground-truth donors (donor-hardcoded mode, no pydentate)
        if dov is not None:
            for lig, atoms in zip(ligs, dov):
                if atoms:
                    lig.donor_override = list(atoms)
        cx = Complex(metal=Metal(rec["metal"], rec["ox"]), name=rc, ligands=ligs)
        t0 = time.perf_counter()
        res = (pipeline.build_complex(cx, workdir, relax=True, xtb_timeout_s=xtb_timeout)
               if relax else pipeline.build_complex(cx, workdir, relax=False))
        card["build_s"] = round(time.perf_counter() - t0, 2)
        xyz = Path(res[0].xyz_path).read_text()
        card["xyz"] = xyz
        if res[0].warnings:
            card["warnings"] += list(res[0].warnings)
    except Exception as e:  # noqa: BLE001
        card["error"] = f"{type(e).__name__}: {e}"[:200]
        return card

    cn = rec["cn"]
    b = M.coordination_sphere(xyz, rec["metal"], cn)
    if not b:
        card["error"] = "metal not found in build / no sphere"
        return card
    m_b, d_b, sym_b = b
    m_e = np.asarray(sphere["metal_xyz"], float)
    d_e = np.asarray(sphere["donors"], float)

    vb = d_b - m_b
    ve = d_e - m_e
    # metrics (same as run.py.score, minus the relaxed comparison)
    dir_e = ve / np.linalg.norm(ve, axis=1, keepdims=True)
    dir_b = vb / np.linalg.norm(vb, axis=1, keepdims=True)
    es, ec = M.best_shape(dir_e, cn)
    bs, bc = M.best_shape(dir_b, cn)
    dmat = M.local_distance_matrix_rmsd(ve, vb)
    brmsd, boff = M.bond_rmsd(d_e, m_e, d_b, m_b)
    poly = M.shape_deviation(dir_b, dir_e)   # label-free build-vs-crystal CShM
    bl_b = sorted(float(np.linalg.norm(v)) for v in vb)

    card.update({
        "exp_shape": es, "exp_cshm": None if np.isnan(ec) else round(ec, 2),
        "build_shape": bs, "build_cshm": None if np.isnan(bc) else round(bc, 2),
        "shape_match": es == bs,
        "poly_cshm": None if np.isnan(poly) else round(poly, 2),
        "dmat_rmsd": None if np.isnan(dmat) else round(dmat, 3),
        "bond_rmsd": None if np.isnan(brmsd) else round(brmsd, 3),
        "bond_offset": None if np.isnan(boff) else round(boff, 3),
        "build_bonds": [round(x, 3) for x in bl_b],
        "build_donor_syms": sym_b,
    })
    # Heuristics for spotting ASSEMBLY-stage trouble at a glance. Note: pre-xtb
    # bond lengths are generic (stk/MCHammer, not yet CSD/xtb-corrected), so the
    # RADIAL (bond-length) error is expected to be large here and is shown as info,
    # not a warning. The meaningful pre-xtb signals are angular/topological:
    if bl_b and bl_b[-1] > 3.0:
        card["warnings"].append(f"long M-donor bond {bl_b[-1]:.2f} A (possible dissociation)")
    if len(sym_b) < cn:
        card["warnings"].append(f"only {len(sym_b)} donors within sphere, expected CN {cn}")
    if not card["shape_match"]:
        card["warnings"].append(f"shape mismatch: build {bs} vs X-ray {es}")
    # Excess distortion over the crystal itself is the real assembly signal: the
    # X-ray spheres are often non-ideal too (chelate bite angles), so compare.
    if card["build_cshm"] is not None and card["exp_cshm"] is not None:
        excess = card["build_cshm"] - card["exp_cshm"]
        card["cshm_excess"] = round(excess, 1)
        if excess > 5.0:
            card["warnings"].append(
                f"build far more distorted than crystal (CShM +{excess:.1f})")

    aligned = _align(ve, vb)
    card["sphere"] = {
        "exp": ve.round(3).tolist(),
        "build": (aligned.round(3).tolist() if aligned is not None else vb.round(3).tolist()),
        "exp_syms": [str(s) for s in sphere.get("donor_syms", card["donor_elements"])],
        "build_syms": sym_b,
    }
    return card


HTML_HEAD = """<!doctype html><html><head><meta charset="utf-8">
<title>MeCoBi pre-xtb geometry review</title>
<script src="https://3Dmol.org/build/3Dmol-min.js"></script>
<style>
 body{font:14px/1.4 system-ui,sans-serif;margin:0;background:#f4f5f7;color:#1a1a1a}
 header{padding:16px 24px;background:#12303a;color:#fff}
 header h1{margin:0 0 4px;font-size:19px}
 header .sub{opacity:.8;font-size:13px}
 .legend{display:inline-block;margin-left:16px}
 .dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin:0 4px 0 12px;vertical-align:middle}
 .wrap{padding:16px 24px;display:grid;grid-template-columns:1fr;gap:16px;max-width:1200px;margin:0 auto}
 .summary{background:#fff;border:1px solid #dde;border-radius:8px;overflow-x:auto;padding:4px}
 table.sumt{border-collapse:collapse;width:100%;font-size:12.5px}
 table.sumt th,table.sumt td{padding:5px 10px;text-align:right;border-bottom:1px solid #eef;white-space:nowrap}
 table.sumt th{background:#eef1f4;color:#334;font-weight:600;position:sticky;top:0}
 table.sumt td.lab,table.sumt th:first-child{text-align:left}
 table.sumt tr:first-child td{border-top:2px solid #ccd}
 .card{background:#fff;border:1px solid #dde;border-radius:8px;overflow:hidden}
 .card.err{border-color:#e2b0b0}
 .card.warn{border-color:#e6c46a}
 .chead{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px;padding:10px 14px;background:#eef1f4;border-bottom:1px solid #dde}
 .chead .rc{font-weight:700;font-size:15px}
 .chead .tag{font-size:12px;background:#12303a;color:#fff;border-radius:10px;padding:1px 8px}
 .chead .tag.cn{background:#3a6ea5}
 .views{display:flex;gap:0;flex-wrap:wrap}
 .view{position:relative;width:50%;min-width:320px;height:320px;box-sizing:border-box;border-right:1px solid #eee}
 .view .lbl{position:absolute;top:6px;left:8px;z-index:5;font-size:11px;color:#556;background:#fffd;padding:1px 6px;border-radius:4px}
 .meta{padding:8px 14px;font-size:12.5px;border-top:1px solid #eee}
 table.m{border-collapse:collapse;margin:2px 0}
 table.m td{padding:1px 10px 1px 0;white-space:nowrap}
 table.m td.k{color:#667;padding-right:6px}
 .bad{color:#b02020;font-weight:600}
 .good{color:#1c7c34;font-weight:600}
 .warns{color:#8a5a00;font-size:12px;margin-top:4px}
 .err-msg{color:#b02020;padding:10px 14px;font-family:monospace;font-size:12px}
 .lig{font-family:monospace;font-size:11px;color:#556;word-break:break-all}
 code{background:#eef;padding:0 3px;border-radius:3px}
</style></head><body>
"""


def _med(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return round((xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2), 3)


def _summary_html(cards, relax):
    """Aggregate scorecard: build/shape rates + median metrics, overall and by CN."""
    tag = "xtb-relaxed" if relax else "pre-xtb (assembly geometry)"
    rows = [
        '<div class="summary"><table class="sumt">',
        '<tr><th>slice</th><th>n</th><th>build%</th><th>shape-match%</th>'
        '<th>poly CShM</th><th>build CShM</th><th>donor-donor RMSD</th>'
        f'<th>M&ndash;L bond RMSD{" (relaxed)" if relax else " (pre-xtb, generic)"}</th></tr>',
    ]

    def line(label, cs):
        s = [c for c in cs if c.get("shape_match") is not None]
        b = sum(1 for c in cs if not c["error"])
        m = sum(bool(c.get("shape_match")) for c in s)
        return (f'<tr><td class="lab">{label}</td><td>{len(cs)}</td>'
                f'<td>{100*b/max(len(cs),1):.0f}%</td>'
                f'<td>{(100*m/len(s)) if s else 0:.0f}%</td>'
                f'<td>{_med([c.get("poly_cshm") for c in s])}</td>'
                f'<td>{_med([c.get("build_cshm") for c in s])}</td>'
                f'<td>{_med([c.get("dmat_rmsd") for c in s])}</td>'
                f'<td>{_med([c.get("bond_rmsd") for c in s])}</td></tr>')

    rows.append(line(f"<b>ALL ({tag})</b>", cards))
    for cn in sorted({c["cn"] for c in cards}):
        rows.append(line(f"CN {cn}", [c for c in cards if c["cn"] == cn]))
    rows.append("</table></div>")
    return "".join(rows)


def render_html(cards, meta, relax=False):
    ok = [c for c in cards if not c["error"]]
    n_warn = sum(1 for c in ok if c["warnings"])
    n_mis = sum(1 for c in ok if not c.get("shape_match", True))
    head = HTML_HEAD
    kind = "structural review" if relax else "pre-xtb geometry review"
    head += (f'<header><h1>MeCoBi {kind} &mdash; {len(cards)} '
             f'stratified complexes</h1>'
             f'<div class="sub">{meta} &nbsp;|&nbsp; '
             f'{len(ok)} built, {len(cards)-len(ok)} build-failed, '
             f'{n_warn} with warnings, {n_mis} shape-mismatch. '
             f'<span class="legend">'
             f'<span class="dot" style="background:#2ca02c"></span>X-ray donors'
             f'<span class="dot" style="background:#ff7f0e"></span>build donors '
             f'(aligned)</span></div></header>')
    head += '<div class="wrap">' + _summary_html(cards, relax)
    body = []
    for i, c in enumerate(cards):
        cls = "card err" if c["error"] else ("card warn" if c["warnings"] else "card")
        rows = [f'<div class="{cls}">']
        rows.append('<div class="chead">'
                    f'<span class="rc">{c["refcode"]}</span>'
                    f'<span class="tag">{c["metal"]}({c["ox"]:+d})</span>'
                    f'<span class="tag cn">CN {c["cn"]}</span>'
                    f'<span class="lig">{"  .  ".join(c["ligands"])}</span></div>')
        if c["error"]:
            rows.append(f'<div class="err-msg">BUILD FAILED &mdash; {c["error"]}</div>')
        else:
            rows.append(
                f'<div class="views">'
                f'<div class="view" id="struct{i}"><span class="lbl">pre-xtb structure</span></div>'
                f'<div class="view" id="sphere{i}"><span class="lbl">coord sphere: '
                f'X-ray vs build</span></div></div>')
            # metrics table
            sm = ('<span class="good">match</span>' if c.get("shape_match")
                  else '<span class="bad">MISMATCH</span>')
            exc = c.get("cshm_excess")
            exc_html = ""
            if exc is not None:
                cls = "bad" if exc > 5 else ("good" if exc <= 1 else "")
                exc_html = f' &nbsp;<span class="{cls}">excess {exc:+.1f}</span>'
            rows.append(
                '<div class="meta"><table class="m">'
                f'<tr><td class="k">shape</td><td>build <b>{c.get("build_shape","?")}</b> '
                f'(CShM {c.get("build_cshm","?")}) vs X-ray <b>{c.get("exp_shape","?")}</b> '
                f'(CShM {c.get("exp_cshm","?")}) &nbsp; {sm}{exc_html}</td></tr>'
                f'<tr><td class="k">poly CShM</td><td>{c.get("poly_cshm","?")} '
                f'<span style="color:#889">(build-vs-crystal, label-free; 0 = matches crystal)</span></td></tr>'
                f'<tr><td class="k">donor-donor RMSD</td><td>{c.get("dmat_rmsd","?")} &Aring;'
                f'</td></tr>'
                f'<tr><td class="k">M-L bond RMSD</td><td>{c.get("bond_rmsd","?")} &Aring; '
                f'(offset {c.get("bond_offset","?")} &Aring;)</td></tr>'
                f'<tr><td class="k">build M-L bonds</td><td>'
                f'{", ".join(f"{x:.2f}" for x in c.get("build_bonds",[]))} &Aring;</td></tr>'
                '</table>')
            if c["warnings"]:
                rows.append('<div class="warns">&#9888; ' +
                            ' &nbsp;&bull;&nbsp; '.join(c["warnings"]) + '</div>')
            rows.append('</div>')
        rows.append('</div>')
        body.append("".join(rows))

    # per-card JS payload
    payload = []
    for i, c in enumerate(cards):
        if c["error"]:
            continue
        payload.append({"i": i, "xyz": c["xyz"], "metal": c["metal"],
                        "sphere": c.get("sphere")})
    script = """
<script>
const DATA = __PAYLOAD__;
const byId = {}; DATA.forEach(d => byId[d.i] = d);
const live = new Map();  // id -> [viewers] ; destroyed when scrolled away (WebGL cap)

function makeStruct(el, d){
  const v = $3Dmol.createViewer(el, {backgroundColor:'white'});
  v.addModel(d.xyz, 'xyz');
  v.setStyle({}, {stick:{radius:0.12}, sphere:{scale:0.25}});
  // highlight the metal
  v.setStyle({elem:d.metal}, {sphere:{scale:0.45, color:'0x9467bd'}});
  v.zoomTo(); v.render();
  return v;
}
function makeSphere(el, d){
  const v = $3Dmol.createViewer(el, {backgroundColor:'white'});
  const s = d.sphere; if(!s){ return v; }
  // metal at origin
  v.addSphere({center:{x:0,y:0,z:0}, radius:0.28, color:'0x9467bd'});
  const draw = (pts, col) => pts.forEach(p=>{
     v.addSphere({center:{x:p[0],y:p[1],z:p[2]}, radius:0.22, color:col});
     v.addCylinder({start:{x:0,y:0,z:0}, end:{x:p[0],y:p[1],z:p[2]},
        radius:0.05, color:col, fromCap:1, toCap:1});
  });
  draw(s.exp, '0x2ca02c');    // X-ray = green
  draw(s.build, '0xff7f0e');  // build = orange
  v.zoomTo(); v.render();
  return v;
}
const io = new IntersectionObserver((ents)=>{
  ents.forEach(e=>{
    const id = +e.target.dataset.card;
    if(e.isIntersecting){
      if(!live.has(id) && byId[id]){
        const d = byId[id];
        const vs = [makeStruct(document.getElementById('struct'+id), d),
                    makeSphere(document.getElementById('sphere'+id), d)];
        live.set(id, vs);
      }
    } else if(live.has(id)){
      live.get(id).forEach(v=>{ try{v.clear();}catch(_){} });
      // free the canvas/context
      document.getElementById('struct'+id).innerHTML='<span class="lbl">pre-xtb structure</span>';
      document.getElementById('sphere'+id).innerHTML='<span class="lbl">coord sphere: X-ray vs build</span>';
      live.delete(id);
    }
  });
}, {rootMargin:'200px'});
DATA.forEach(d=>{
  const card = document.getElementById('struct'+d.i).closest('.card');
  card.dataset.card = d.i;
  io.observe(card);
});
</script>
"""
    script = script.replace("__PAYLOAD__", json.dumps(payload))
    return head + "".join(body) + "</div>" + script + "</body></html>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--bundle", default="benchmark_bundle")
    ap.add_argument("--spheres", default="benchmark_spheres.json.gz")
    ap.add_argument("--relax", action="store_true",
                    help="xtb-relax each build (real MeCoBi output; needs xtb, slower). "
                         "Default off = fast assembly-geometry-only review.")
    ap.add_argument("--xtb-timeout", type=int, default=180)
    ap.add_argument("--out", default="_pre_xtb_report",
                    help="output subdir (default _pre_xtb_report)")
    ap.add_argument("--donors", default=None,
                    help="benchmark_donors.json: hardcode ground-truth donors (bypass "
                         "pydentate); restricts the sample to mapped complexes.")
    cfg = ap.parse_args()

    gz = HERE / f"{cfg.bundle}.json.gz"
    bundle = _load_json(gz if gz.exists() else HERE / f"{cfg.bundle}.json")
    spheres = _load_json(HERE / cfg.spheres)
    donors = _load_json(HERE / cfg.donors) if cfg.donors else None
    if donors is not None:
        bundle = [r for r in bundle if r["refcode"] in donors]  # mapped complexes only
    sample = stratified_sample(bundle, spheres, cfg.n, cfg.seed)
    if donors is not None:
        for rec in sample:
            rec["_donors"] = donors[rec["refcode"]]
    print(f"selected {len(sample)} complexes across CN "
          f"{sorted(set(r['cn'] for r in sample))}"
          f"{' (donors HARDCODED, no pydentate)' if donors else ' (pydentate)'}")

    outdir = HERE / cfg.out
    outdir.mkdir(exist_ok=True)
    work = outdir / "_work"
    work.mkdir(exist_ok=True)

    cards = []
    t0 = time.perf_counter()
    for k, rec in enumerate(sample, 1):
        c = build_card(rec, spheres[rec["refcode"]], work,
                       relax=cfg.relax, xtb_timeout=cfg.xtb_timeout)
        cards.append(c)
        flag = "ERR" if c["error"] else ("warn" if c["warnings"] else "ok")
        print(f"  [{k}/{len(sample)}] {rec['refcode']:8s} CN{rec['cn']} "
              f"{rec['metal']:2s} -> {flag}"
              + (f"  {c['error']}" if c["error"] else ""), flush=True)

    meta = (f"seed {cfg.seed}, bundle {cfg.bundle}, "
            f"donors={'HARDCODED (ground-truth, no pydentate)' if donors else 'pydentate'}, "
            f"relax={'ON (xtb-relaxed output)' if cfg.relax else 'OFF (assembly geometry only)'}, "
            f"built in {time.perf_counter()-t0:.0f}s")
    html = render_html(cards, meta, relax=cfg.relax)
    out = outdir / "report.html"
    out.write_text(html, encoding="utf-8")
    ok = sum(1 for c in cards if not c["error"])
    warn = sum(1 for c in cards if not c["error"] and c["warnings"])
    print(f"\n{ok}/{len(cards)} built, {warn} flagged with warnings")
    print(f"report -> {out}")


if __name__ == "__main__":
    main()
