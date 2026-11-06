"""Interactive HTML report for the pilot-100 tool comparison (MeCoBi / MetalloGen / molSimplify /
Architector), in the spirit of arch_comparison/make_report.py.

Reads compare_tools_per_structure.csv (written by compare_tools.py -- run that first, so both
reports score the same way) and each tool's structures, and writes ONE self-contained HTML file:

  * a card per tool: success %, median time, median c-kmRMSD
  * charts: success (off-target builds hatched), per-structure time on a log axis, the four
    quality metrics as small multiples (paired set <-> own builds toggle), and every tool against
    MeCoBi complex by complex (y = x diagonal)
  * tables: summary, Wilcoxon signed-rank vs MeCoBi on the paired set, by coordination number
  * a structure browser: crystal 2-hop core + the four tools in 3D, aligned on the crystal sphere
  * a gallery: every complex as a card (crystal + the four tools side by side) to scroll through

Colour = Okabe-Ito, validated for CVD with the dataviz validator; each
tool also has its own marker shape, so identity never rests on colour alone. 3Dmol.js is loaded from
arch_comparison/3Dmol-min.js (offline) with a CDN fallback.

    python pilot100/compare_tools.py            # scores -> compare_tools_per_structure.csv
    python pilot100/compare_tools_html.py       # -> pilot100/compare_tools_report.html
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import os
import statistics as st
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

HERE = Path(__file__).resolve().parent   # pilot100/
BENCH = HERE.parent
REPO = BENCH.parents[1]
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(HERE))
import hydrides  # noqa: E402
import metrics as M  # noqa: E402
from compare_tools import DEFAULT_EXCLUDE, discover, xyz_path  # noqa: E402

TOOLS = ["MeCoBi", "MetalloGen", "molSimplify", "Architector"]
METRICS = [("ckmrmsd", "c-kmRMSD", "Å"), ("dmae3", "D-MAE3", "Å"), ("poly_cshm", "poly-CShM", ""),
           ("dmat_rmsd", "dmat RMSD", "Å"), ("bond_rmsd", "bond RMSD", "Å")]


def _f(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def core_to_xyz(core) -> str:
    atoms = [core["metal"]] + core["donors"] + core["depth2"]
    lines = [str(len(atoms)), "crystal 2-hop core"]
    lines += [f"{a['el']} {a['xyz'][0]:.4f} {a['xyz'][1]:.4f} {a['xyz'][2]:.4f}" for a in atoms]
    return "\n".join(lines) + "\n"


def align_to_crystal(xyz_text, metal, cn, exp) -> str:
    """Build rotated/translated so its donor sphere superposes on the crystal's (metal at the
    origin, the crystal core's frame); metal-centred only if donor counts differ."""
    try:
        syms, P = M.parse_xyz(xyz_text)
        P = np.asarray(P, float)
        cs = M.coordination_sphere(xyz_text, metal, cn)
        if not cs:
            return xyz_text
        m_b, d_b, _ = cs
        Pc = P - np.asarray(m_b, float)
        de = np.asarray(exp["donors"], float) - np.asarray(exp["metal_xyz"], float)
        db = np.asarray(d_b, float) - np.asarray(m_b, float)
        R = np.eye(3)
        if len(de) == len(db):
            for _ in range(60):
                _, perm = linear_sum_assignment(cdist(de, db @ R.T))
                R = M._kabsch(db[perm], de)
        Q = Pc @ R.T + np.asarray(exp["metal_xyz"], float)   # into the crystal frame
        out = [str(len(syms)), "aligned"]
        out += [f"{s} {x:.4f} {y:.4f} {z:.4f}" for s, (x, y, z) in zip(syms, Q)]
        return "\n".join(out) + "\n"
    except Exception:  # noqa: BLE001
        return xyz_text


def wilcoxon(a, b):
    try:
        from scipy.stats import wilcoxon as w
        if len(a) < 6 or all(abs(x - y) < 1e-12 for x, y in zip(a, b)):
            return None
        return float(w(a, b).pvalue)
    except Exception:  # noqa: BLE001
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default=str(HERE / "compare_tools_per_structure.csv"))
    ap.add_argument("--mecobi"), ap.add_argument("--molsimplify")
    ap.add_argument("--metallogen"), ap.add_argument("--architector")
    for tool in ("molsimplify", "metallogen", "architector"):   # as compare_tools.py
        ap.add_argument(f"--{tool}-hyd", help="that tool's re-run of the hydride complexes")
    ap.add_argument("--exclude", default=DEFAULT_EXCLUDE,
                    help="refcodes left out of the PAIRED set (same default as compare_tools.py)")
    ap.add_argument("--spheres", default=None)
    ap.add_argument("--no-structures", action="store_true",
                    help="skip the 3D browser (smaller file)")
    ap.add_argument("--out", default=str(HERE / "compare_tools_report.html"))
    cfg = ap.parse_args()

    rows = list(csv.DictReader(open(cfg.csv, encoding="utf-8")))
    tools = [t for t in TOOLS if any(r["tool"] == t for r in rows)]
    exclude = {x.strip() for x in cfg.exclude.split(",") if x.strip()}
    sph_path = Path(cfg.spheres) if cfg.spheres else (
        next(p for p in (BENCH / "benchmark_spheres_elem.json.gz",
                         BENCH / "benchmark_spheres_fixed.json.gz",
                         BENCH / "benchmark_spheres.json.gz") if p.exists()))
    spheres = json.load(gzip.open(sph_path, "rt"))
    cores = json.load(gzip.open(next(p for p in (BENCH / "benchmark_cores_elem.json.gz",
                                                BENCH / "benchmark_cores.json.gz")
                                    if p.exists()), "rt"))
    found = discover(cfg)   # incl. each tool's hydride re-run overlay, as compare_tools.py

    # ---- per-refcode records
    recs = {}
    for r in rows:
        rc, tl = r["refcode"], r["tool"]
        d = recs.setdefault(rc, {"refcode": rc, "metal": r["metal"], "cn": int(r["cn"]),
                                 "tools": {}})
        built = r["built"] == "True"
        d["tools"][tl] = {
            "built": built, "attempted": r["attempted"] == "True",
            "off": r["off_target"] == "True", "timeout": r["timeout"] == "True",
            "t": _f(r["time_s"]), "shape": {"True": True, "False": False}.get(r["shape_match"]),
            "cnm": {"True": True, "False": False}.get(r.get("cn_match")),
            "cnd": r.get("cn_detected") or None,
            **{k: _f(r.get(k)) for k, _, _ in METRICS}, "err": r["error"],
        }
    refcodes = sorted(recs)

    paired = [rc for rc in refcodes if rc not in exclude and all(
        recs[rc]["tools"].get(t, {}).get("built") and recs[rc]["tools"][t].get("ckmrmsd") is not None
        for t in tools)]

    # ---- stats (Python side, so the page and compare_tools_report.md agree)
    stats = {"paired_n": len(paired), "wilcoxon": {}, "summary": {}}
    for tl in tools:
        allr = [recs[rc]["tools"][tl] for rc in refcodes if tl in recs[rc]["tools"]]
        b = [x for x in allr if x["built"]]
        tb = [x["t"] for x in b if x["t"] is not None]
        sh = [x["shape"] for x in b if x["shape"] is not None]
        s = {"built": len(b), "n": len(refcodes), "off": sum(x["off"] for x in b),
             # no geometry was given to the tool (Architector's default mode): not applicable
             "off_na": not any(r["tool"] == tl and r["off_target"] in ("True", "False")
                               and r["built"] == "True" for r in rows),
             "timeouts": sum(x["timeout"] for x in allr),
             "t_med": st.median(tb) if tb else None,
             "cpu_h": sum(x["t"] for x in allr if x["t"] is not None) / 3600 if tb else None,
             "shape_pct": 100 * sum(sh) / len(sh) if sh else None}
        for k, _, _ in METRICS:
            v = [x[k] for x in b if x[k] is not None]
            vp = [recs[rc]["tools"][tl][k] for rc in paired
                  if recs[rc]["tools"][tl][k] is not None]
            s[k] = {"med": st.median(v) if v else None, "mean": st.fmean(v) if v else None,
                    "pmed": st.median(vp) if vp else None}
        stats["summary"][tl] = s
    if "MeCoBi" in tools:
        for tl in tools:
            if tl == "MeCoBi":
                continue
            stats["wilcoxon"][tl] = {}
            for k, _, _ in METRICS:
                pr = [(recs[rc]["tools"]["MeCoBi"][k], recs[rc]["tools"][tl][k]) for rc in paired
                      if recs[rc]["tools"]["MeCoBi"][k] is not None
                      and recs[rc]["tools"][tl][k] is not None]
                stats["wilcoxon"][tl][k] = {
                    "better": sum(a < b for a, b in pr), "worse": sum(a > b for a, b in pr),
                    "p": wilcoxon([a for a, _ in pr], [b for _, b in pr])}

    # ---- structures for the 3D browser + gallery
    hyd = hydrides.load(classes=None)   # located hydrides: shown in the crystal pane + flagged
    if not cfg.no_structures:
        for rc in refcodes:
            d = recs[rc]
            if rc in hyd:
                d["hyd"] = hyd[rc]["n_h"]
            if rc in cores:
                d["crystal"] = core_to_xyz(hydrides.core(cores[rc], hyd.get(rc)))
            for tl in tools:
                p = xyz_path(found[tl], rc) if tl in found else None
                if d["tools"].get(tl, {}).get("built") and p and p.exists():
                    txt = p.read_text(encoding="utf-8")
                    d["tools"][tl]["xyz"] = (align_to_crystal(txt, d["metal"], d["cn"], spheres[rc])
                                             if rc in spheres else txt)

    meta = {"tools": tools, "metrics": METRICS, "paired": paired, "exclude": sorted(exclude),
            "reference": sph_path.name, "stats": stats}
    out = Path(cfg.out)
    js3d = os.path.relpath(REPO / "arch_comparison" / "3Dmol-min.js", out.parent).replace("\\", "/")
    html = (TEMPLATE.replace("__DATA__", json.dumps(list(recs.values()), separators=(",", ":")))
            .replace("__META__", json.dumps(meta, separators=(",", ":")))
            .replace("__3DMOL__", js3d))
    out.write_text(html, encoding="utf-8")
    print(f"{len(refcodes)} refcodes, {len(tools)} tools, paired n={len(paired)} -> {out} "
          f"({out.stat().st_size / 1e6:.1f} MB)")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pilot 100 — tool comparison</title>
<style>
:root{color-scheme:light;
 --surface-0:#F4F6F7;--surface-1:#FFFFFF;--surface-2:#FBFCFC;--border:#D9DEE2;--border-strong:#BCC4CA;
 --text-primary:#0E1B24;--text-secondary:#42535D;--text-muted:#5A6B75;
 --accent:#3D3DA8;--accent-50:#EBEBFA;--grid:#E6EAED;
 --t-MeCoBi:#0072B2;--t-MetalloGen:#E69F00;--t-molSimplify:#009E73;--t-Architector:#882255;}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){color-scheme:dark;
 --surface-0:#0E1B24;--surface-1:#15242F;--surface-2:#1C2E3A;--border:#2A3D49;--border-strong:#3A4E5B;
 --text-primary:#EAF0F3;--text-secondary:#A7B6BF;--text-muted:#7A8A93;
 --accent:#7F77DD;--accent-50:#26215C;--grid:#243541;
 --t-MeCoBi:#3A8FD0;--t-MetalloGen:#C98500;--t-molSimplify:#00A67A;--t-Architector:#BE4A83;}}
:root[data-theme="dark"]{color-scheme:dark;
 --surface-0:#0E1B24;--surface-1:#15242F;--surface-2:#1C2E3A;--border:#2A3D49;--border-strong:#3A4E5B;
 --text-primary:#EAF0F3;--text-secondary:#A7B6BF;--text-muted:#7A8A93;
 --accent:#7F77DD;--accent-50:#26215C;--grid:#243541;
 --t-MeCoBi:#3A8FD0;--t-MetalloGen:#C98500;--t-molSimplify:#00A67A;--t-Architector:#BE4A83;}
*{box-sizing:border-box}
body{margin:0;background:var(--surface-0);color:var(--text-primary);
 font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 4px}
.sub{color:var(--text-secondary);margin:0 0 16px}.note{color:var(--text-muted);font-size:12.5px}
.card{background:var(--surface-1);border:0.5px solid var(--border);border-radius:10px;padding:14px 16px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin-top:12px}
.tile h3{margin:0 0 8px;font-size:15px;display:flex;align-items:center;gap:8px}
.kv{display:grid;grid-template-columns:auto 1fr;gap:2px 12px;font-size:13px}
.kv b{font-variant-numeric:tabular-nums;font-weight:600;text-align:right}
.kv span{color:var(--text-secondary)}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:10px 0}
.seg{display:inline-flex;border:0.5px solid var(--border-strong);border-radius:8px;overflow:hidden}
.seg button{background:var(--surface-1);color:var(--text-primary);border:0;padding:6px 12px;
 font:inherit;cursor:pointer}.seg button[aria-pressed="true"]{background:var(--accent);color:#fff}
select,input[type=search]{font:inherit;color:var(--text-primary);background:var(--surface-1);
 border:0.5px solid var(--border-strong);border-radius:8px;padding:5px 8px}
.themebtn{float:right;background:var(--surface-1);color:var(--text-primary);border:0.5px solid var(--border-strong);
 border-radius:8px;padding:5px 10px;cursor:pointer;font:inherit}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--text-secondary)}
.legend span{display:inline-flex;align-items:center;gap:6px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(520px,1fr));gap:12px}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:12px}
@media (max-width:600px){.grid2,.grid3{grid-template-columns:1fr}}
svg{display:block;width:100%;height:auto;overflow:visible}
svg text{fill:var(--text-secondary);font-size:11px}
svg .title{fill:var(--text-primary);font-size:12.5px;font-weight:600}
svg .val{fill:var(--text-primary);font-size:11.5px;font-variant-numeric:tabular-nums}
svg .axt{fill:var(--text-primary);font-size:11.5px;font-weight:500}
.axis line,.axis path{stroke:var(--border-strong)}.gridl{stroke:var(--grid)}
.tt{position:fixed;pointer-events:none;z-index:10;background:var(--surface-2);color:var(--text-primary);
 border:0.5px solid var(--border-strong);border-radius:8px;padding:6px 9px;font-size:12.5px;
 box-shadow:0 4px 14px rgba(0,0,0,.15);display:none;max-width:280px}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th,td{padding:5px 8px;border-bottom:0.5px solid var(--border);text-align:right;white-space:nowrap}
th{color:var(--text-secondary);font-weight:600;cursor:default}th:first-child,td:first-child{text-align:left}
.scroll{overflow-x:auto}
#structs th{cursor:pointer}#structs tbody tr{cursor:pointer}#structs tbody tr:hover{background:var(--accent-50)}
#structs tr.sel{background:var(--accent-50)}
.viewers{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-top:10px}
.vbox{background:var(--surface-1);border:0.5px solid var(--border);border-radius:10px;overflow:hidden}
.vbox .cap{padding:6px 8px;font-size:12.5px;border-bottom:0.5px solid var(--border);display:flex;gap:6px;align-items:center}
.vbox .v{position:relative;height:230px}.vbox .m{padding:5px 8px;font-size:12px;color:var(--text-secondary)}
.pill{font-size:11px;padding:1px 6px;border-radius:999px;border:0.5px solid var(--border-strong);color:var(--text-secondary)}
.muted{color:var(--text-muted)}
.gcard{margin-top:12px;padding:10px 12px}
.ghead{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;margin-bottom:6px}
.ghead b{font-size:15px}.ghead a{color:var(--accent);font-size:12.5px;cursor:pointer;margin-left:auto}
.gscroll{overflow-x:auto}.ginner{min-width:760px}
.gcols{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:0;font-size:12.5px}
.gcols>div{padding:3px 6px;display:flex;gap:5px;align-items:center;min-width:0}
.gmeta>div{color:var(--text-secondary);font-size:12px;display:block}
.gv{position:relative;height:250px;border:0.5px solid var(--border);border-radius:8px;overflow:hidden;
 background:var(--surface-1)}
.gv .ph{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}
.gdiv{position:absolute;top:0;bottom:0;width:0;border-left:0.5px solid var(--border);pointer-events:none;z-index:2}
</style></head>
<body><main>
<button class="themebtn" id="themebtn" type="button">Theme</button>
<h1>Pilot 100 — tool comparison</h1>
<p class="sub" id="subtitle"></p>
<div class="legend" id="legend"></div>
<div class="tiles" id="tiles"></div>

<h2>Success</h2>
<p class="note">Built out of the 100 pilot complexes. Hatched = built, but in a geometry other than the crystal's (molSimplify default/haptic fallbacks, MeCoBi heuristic builds, Architector builds that kept or fell back to its own search over the cores of the CN). An Architector run in its default mode (no geometry given) has no hatched part.</p>
<div class="card"><svg id="c-success"></svg></div>

<h2>Time per structure</h2>
<p class="note">One dot per built complex, log scale. Tick = median. MeCoBi times the relaxed build (<code>build_s</code>); the others time the whole tool call. MetalloGen timeouts sit at 900 s; Architector had no limit. Architector and MetalloGen may have used several cores per process.</p>
<div class="card"><svg id="c-time"></svg></div>

<h2>Quality</h2>
<div class="row"><span class="seg" id="setsel">
 <button type="button" data-v="paired" aria-pressed="true">Paired set</button>
 <button type="button" data-v="own" aria-pressed="false">Each tool's own builds</button></span>
 <span class="note" id="setnote"></span></div>
<div class="grid2" id="c-quality"></div>

<h2>Against MeCoBi, complex by complex</h2>
<div class="row"><label>Metric <select id="scmetric"></select></label>
 <span class="note">Paired set. Below the diagonal = the tool beats MeCoBi on that complex.</span></div>
<div class="grid3" id="c-scatter"></div>

<h2>Tables</h2>
<div class="grid2">
 <div class="card scroll"><table id="t-summary"></table></div>
 <div class="card scroll"><table id="t-wilcoxon"></table>
  <p class="note">Paired set. MeCoBi better / worse (Wilcoxon signed-rank p). Lower is better for every metric.</p></div>
</div>
<div class="card scroll" style="margin-top:12px"><table id="t-cn"></table>
 <p class="note">Success % · median c-kmRMSD over each tool's own builds. Small groups: read medians with care.</p></div>

<h2 id="structh">Structures</h2>
<div class="row"><input type="search" id="q" placeholder="filter refcode / metal / CN">
 <span class="note">Click a row to view the crystal 2-hop core and the four builds, aligned on the crystal sphere. Values = c-kmRMSD (Å).</span></div>
<div class="card scroll" style="max-height:340px;overflow:auto"><table id="structs"></table></div>
<div class="viewers" id="viewers"></div>

<h2>Gallery</h2>
<div class="row"><label>Sort <select id="gsort">
  <option value="refcode">refcode</option><option value="worst">MeCoBi c-kmRMSD, worst first</option>
  <option value="cn">coordination number</option><option value="metal">metal</option></select></label>
 <input type="search" id="gq" placeholder="filter refcode / metal / CN">
 <label><input type="checkbox" id="ghyd"> hydrido complexes only</label>
 <span class="note" id="gcount"></span></div>
<p class="note">Every complex: crystal 2-hop core + the four builds in one row, aligned on the crystal sphere. Drag in any pane to rotate all five together (right-drag to zoom; the mouse wheel scrolls the page); the 3D loads as a card scrolls into view. “H⁻” = the crystal locates a hydride the mined inputs lost (shown in the crystal pane).</p>
<div id="gallery"></div>
</main>
<div class="tt" id="tt"></div>
<script src="__3DMOL__"></script>
<script>
if(typeof $3Dmol==='undefined'){document.write('<script src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.4.2/3Dmol-min.js"><\/script>');}
</script>
<script>
const DATA=__DATA__, META=__META__;
const TOOLS=META.tools, MET=META.metrics, S=META.stats;
const SHAPES={MeCoBi:'circle',MetalloGen:'square',molSimplify:'triangle',Architector:'diamond'};
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const col=t=>css('--t-'+t);
const NS='http://www.w3.org/2000/svg';
function el(tag,attrs={},parent){const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(parent)parent.appendChild(e);return e;}
function fmt(x,d=2){return x==null||!isFinite(x)?'–':Number(x).toFixed(d);}
function marker(g,shape,x,y,r,fill,extra={}){
 let m;
 if(shape==='circle') m=el('circle',{cx:x,cy:y,r},g);
 else if(shape==='square') m=el('rect',{x:x-r*.9,y:y-r*.9,width:r*1.8,height:r*1.8,rx:1},g);
 else if(shape==='triangle') m=el('path',{d:`M${x},${y-r*1.15}L${x+r*1.05},${y+r*.8}L${x-r*1.05},${y+r*.8}Z`},g);
 else m=el('path',{d:`M${x},${y-r*1.2}L${x+r*1.05},${y}L${x},${y+r*1.2}L${x-r*1.05},${y}Z`},g);
 m.setAttribute('fill',fill);m.setAttribute('stroke',css('--surface-1'));m.setAttribute('stroke-width',1.2);
 for(const k in extra)m.setAttribute(k,extra[k]);return m;}
function swatch(t){return `<svg width="14" height="14" viewBox="-7 -7 14 14" style="display:inline;width:14px">${
 SHAPES[t]==='circle'?`<circle r="5" fill="${col(t)}"/>`:SHAPES[t]==='square'?`<rect x="-4.5" y="-4.5" width="9" height="9" rx="1" fill="${col(t)}"/>`:
 SHAPES[t]==='triangle'?`<path d="M0,-5.5L5,4L-5,4Z" fill="${col(t)}"/>`:`<path d="M0,-6L5.5,0L0,6L-5.5,0Z" fill="${col(t)}"/>`}</svg>`;}
// ---- tooltip
const tt=document.getElementById('tt');
function showTT(ev,html){tt.innerHTML=html;tt.style.display='block';
 const w=tt.offsetWidth,h=tt.offsetHeight;let x=ev.clientX+14,y=ev.clientY+14;
 if(x+w>innerWidth-8)x=ev.clientX-w-14;if(y+h>innerHeight-8)y=ev.clientY-h-14;tt.style.left=x+'px';tt.style.top=y+'px';}
function hideTT(){tt.style.display='none';}
function hover(node,html){node.addEventListener('pointermove',e=>showTT(e,html()));node.addEventListener('pointerleave',hideTT);}
// ---- header
function header(){
 document.getElementById('subtitle').textContent=`${DATA.length} complexes · paired set ${META.paired.length} (every tool built and scored; excluded: ${META.exclude.join(', ')||'none'}) · reference ${META.reference}`;
 document.getElementById('legend').innerHTML=TOOLS.map(t=>`<span>${swatch(t)}${t}</span>`).join('');
 document.getElementById('tiles').innerHTML=TOOLS.map(t=>{const s=S.summary[t];return `<div class="card tile">
  <h3>${swatch(t)}${t}</h3><div class="kv">
  <span>built</span><b>${s.built}/${s.n}</b>
  <span>median time / structure</span><b>${s.t_med==null?'–':fmt(s.t_med,1)+' s'}</b>
  <span>median c-kmRMSD (own)</span><b>${fmt(s.ckmrmsd.med)} Å</b>
  <span>median c-kmRMSD (paired)</span><b>${fmt(s.ckmrmsd.pmed)} Å</b>
  <span>shape match</span><b>${fmt(s.shape_pct,0)} %</b></div></div>`;}).join('');}
// ---- success bars
function success(){
 const svg=document.getElementById('c-success');svg.innerHTML='';
 const W=760,L=110,R=70,rh=30,H=TOOLS.length*rh+54;svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
 const x=v=>L+(W-L-R)*v/100;
 el('text',{x:(L+W-R)/2,y:H-4,'text-anchor':'middle',class:'axt'},svg).textContent=`complexes built, % of the ${DATA.length} in the pilot`;
 const defs=el('defs',{},svg);
 TOOLS.forEach(t=>{const p=el('pattern',{id:'h-'+t,width:6,height:6,patternUnits:'userSpaceOnUse',patternTransform:'rotate(45)'},defs);
  el('rect',{width:6,height:6,fill:css('--surface-1')},p);el('rect',{width:3,height:6,fill:col(t)},p);});
 [0,25,50,75,100].forEach(v=>{el('line',{x1:x(v),x2:x(v),y1:6,y2:H-44,class:'gridl'},svg);
  el('text',{x:x(v),y:H-28,'text-anchor':'middle'},svg).textContent=v+'%';});
 TOOLS.forEach((t,i)=>{const s=S.summary[t],y=10+i*rh,on=s.built-s.off;
  el('text',{x:L-10,y:y+13,'text-anchor':'end',class:'title'},svg).textContent=t;
  el('rect',{x:x(0),y,width:x(100)-x(0),height:18,rx:4,fill:css('--grid')},svg);
  const b1=el('rect',{x:x(0),y,width:Math.max(0,x(on)-x(0)-(s.off?1:0)),height:18,rx:4,fill:col(t)},svg);
  if(s.off){const b2=el('rect',{x:x(on)+1,y,width:x(s.built)-x(on)-1,height:18,rx:4,fill:`url(#h-${t})`,stroke:col(t),'stroke-width':1},svg);
   hover(b2,()=>`<b>${t}</b><br>${s.off} built off-target geometry`);}
  hover(b1,()=>`<b>${t}</b><br>${on} built in the crystal geometry${s.off?`<br>+ ${s.off} off-target`:''}<br>${s.n-s.built} failed or not attempted${s.timeouts?`<br>${s.timeouts} timeouts`:''}`);
  el('text',{x:x(s.built)+8,y:y+13,class:'val'},svg).textContent=`${s.built}%`;});}
// ---- time strip (log)
function jitter(i){return ((Math.sin(i*12.9898)*43758.5453)%1+1)%1-.5;}
function timechart(){
 const svg=document.getElementById('c-time');svg.innerHTML='';
 const W=760,L=110,R=30,rh=46,H=TOOLS.length*rh+60;svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
 el('text',{x:(L+W-R)/2,y:H-4,'text-anchor':'middle',class:'axt'},svg).textContent='wall time per built structure, seconds (log scale) — one marker per complex, bar = median';
 const lo=Math.log10(0.2),hi=Math.log10(10000),x=v=>L+(W-L-R)*(Math.log10(Math.max(v,0.2))-lo)/(hi-lo);
 [0.2,1,10,100,1000,10000].forEach(v=>{el('line',{x1:x(v),x2:x(v),y1:6,y2:H-46,class:'gridl'},svg);
  el('text',{x:x(v),y:H-30,'text-anchor':'middle'},svg).textContent=v>=1000?(v/1000)+'k s':v+' s';});
 TOOLS.forEach((t,i)=>{const yc=10+i*rh+rh/2-6;
  el('text',{x:L-10,y:yc+4,'text-anchor':'end',class:'title'},svg).textContent=t;
  const pts=DATA.map(d=>({d,r:d.tools[t]})).filter(o=>o.r&&o.r.built&&o.r.t!=null);
  if(!pts.length){el('text',{x:L+6,y:yc+4},svg).textContent='no timing recorded';return;}
  const g=el('g',{},svg);
  pts.forEach((o,k)=>{const m=marker(g,SHAPES[t],x(o.r.t),yc+jitter(k+i*97)*22,3.6,col(t),{opacity:.85});
   hover(m,()=>`<b>${o.d.refcode}</b> · ${o.d.metal}, CN ${o.d.cn}<br>${t}: ${fmt(o.r.t,1)} s${o.r.timeout?' (timeout)':''}`);});
  const med=S.summary[t].t_med;
  el('line',{x1:x(med),x2:x(med),y1:yc-16,y2:yc+16,stroke:css('--text-primary'),'stroke-width':2.5,'stroke-linecap':'round'},svg);
  el('text',{x:x(med),y:yc-19,'text-anchor':'middle',class:'val'},svg).textContent=fmt(med,1)+' s';});}
// ---- quality small multiples
let SET='paired';
function qualitySet(t){const P=new Set(META.paired);
 return DATA.filter(d=>d.tools[t]&&d.tools[t].built&&(SET==='own'||P.has(d.refcode)));}
function quality(){
 const box=document.getElementById('c-quality');box.innerHTML='';
 document.getElementById('setnote').textContent=SET==='paired'?`${META.paired.length} complexes built and scored by every tool — like-for-like.`:'Each tool over everything it built — not like-for-like (a tool that skips hard complexes looks better).';
 MET.forEach(([k,lab,unit])=>{
  const card=document.createElement('div');card.className='card';box.appendChild(card);
  const svg=el('svg',{},card);const W=520,L=96,R=24,rh=34,H=TOOLS.length*rh+72;svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  el('text',{x:(L+W-R)/2,y:H-4,'text-anchor':'middle',class:'axt'},svg).textContent=`${lab}${unit?', '+unit:' (unitless)'} — one marker per complex, bar = median`;
  el('text',{x:0,y:14,class:'title'},svg).textContent=`${lab}${unit?' ('+unit+')':''} — lower is better`;
  let all=[];TOOLS.forEach(t=>qualitySet(t).forEach(d=>{const v=d.tools[t][k];if(v!=null)all.push(v);}));
  all.sort((a,b)=>a-b);const vmax=Math.max(all[Math.floor(all.length*.98)]||1,0.1)*1.05;
  const x=v=>L+(W-L-R)*Math.min(v,vmax)/vmax;
  const ticks=niceTicks(vmax);ticks.forEach(v=>{el('line',{x1:x(v),x2:x(v),y1:24,y2:H-46,class:'gridl'},svg);
   el('text',{x:x(v),y:H-30,'text-anchor':'middle'},svg).textContent=v;});
  TOOLS.forEach((t,i)=>{const yc=34+i*rh+rh/2-6;
   el('text',{x:L-10,y:yc+4,'text-anchor':'end'},svg).textContent=t;
   const ds=qualitySet(t).filter(d=>d.tools[t][k]!=null);const g=el('g',{},svg);
   ds.forEach((d,j)=>{const v=d.tools[t][k];const m=marker(g,SHAPES[t],x(v),yc+jitter(j+i*31)*16,3.2,col(t),{opacity:.8});
    hover(m,()=>`<b>${d.refcode}</b> · ${d.metal}, CN ${d.cn}<br>${t}: ${fmt(v,3)}${v>vmax?' (beyond axis)':''}`);});
   if(ds.length){const med=median(ds.map(d=>d.tools[t][k]));
    el('line',{x1:x(med),x2:x(med),y1:yc-13,y2:yc+13,stroke:css('--text-primary'),'stroke-width':2.5,'stroke-linecap':'round'},svg);
    el('text',{x:W-R+4,y:yc+4,class:'val'},svg).textContent='';
    const lab2=el('text',{x:x(med)+5,y:yc-9,class:'val'},svg);lab2.textContent=fmt(med);}});
 });}
function median(a){a=a.slice().sort((x,y)=>x-y);const n=a.length;return n?(n%2?a[(n-1)/2]:(a[n/2-1]+a[n/2])/2):null;}
function niceTicks(max){const step=Math.pow(10,Math.floor(Math.log10(max/4)));const m=[1,2,2.5,5,10].find(f=>max/(f*step)<=5)*step;
 const out=[];for(let v=0;v<=max+1e-9;v+=m)out.push(+v.toFixed(3));return out;}
// ---- scatter vs MeCoBi
function scatter(){
 const box=document.getElementById('c-scatter');box.innerHTML='';const k=document.getElementById('scmetric').value;
 const lab=MET.find(m=>m[0]===k);const P=new Set(META.paired);
 TOOLS.filter(t=>t!=='MeCoBi').forEach(t=>{
  const card=document.createElement('div');card.className='card';box.appendChild(card);
  const pts=DATA.filter(d=>P.has(d.refcode)&&d.tools.MeCoBi[k]!=null&&d.tools[t][k]!=null);
  const vals=pts.flatMap(d=>[d.tools.MeCoBi[k],d.tools[t][k]]).sort((a,b)=>a-b);
  const vmax=Math.max(vals[Math.floor(vals.length*.97)]||1,0.1)*1.05;
  const W=340,H=320,L=44,B=40,T=26,R=12,x=v=>L+(W-L-R)*Math.min(v,vmax)/vmax,y=v=>H-B-(H-B-T)*Math.min(v,vmax)/vmax;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`},card);
  const w=S.wilcoxon[t]&&S.wilcoxon[t][k];
  el('text',{x:0,y:14,class:'title'},svg).textContent=`${t} vs MeCoBi`;
  niceTicks(vmax).forEach(v=>{el('line',{x1:x(v),x2:x(v),y1:T,y2:H-B,class:'gridl'},svg);el('line',{x1:L,x2:W-R,y1:y(v),y2:y(v),class:'gridl'},svg);
   el('text',{x:x(v),y:H-B+14,'text-anchor':'middle'},svg).textContent=v;el('text',{x:L-6,y:y(v)+4,'text-anchor':'end'},svg).textContent=v;});
  el('line',{x1:x(0),y1:y(0),x2:x(vmax),y2:y(vmax),stroke:css('--border-strong'),'stroke-dasharray':'4 4'},svg);
  const un=lab[2]?` (${lab[2]})`:'';
  el('text',{x:(L+W-R)/2,y:H-6,'text-anchor':'middle',class:'axt'},svg).textContent=`MeCoBi ${lab[1]}${un}`;
  const yl=el('text',{x:12,y:(T+H-B)/2,'text-anchor':'middle',class:'axt',transform:`rotate(-90 12 ${(T+H-B)/2})`},svg);yl.textContent=`${t} ${lab[1]}${un}`;
  const g=el('g',{},svg);
  pts.forEach(d=>{const a=d.tools.MeCoBi[k],b=d.tools[t][k];const m=marker(g,SHAPES[t],x(a),y(b),3.6,col(t),{opacity:.85});
   hover(m,()=>`<b>${d.refcode}</b> · ${d.metal}, CN ${d.cn}<br>MeCoBi ${fmt(a,3)} · ${t} ${fmt(b,3)}<br>${a<b?'MeCoBi better':a>b?t+' better':'tie'}`);});
  const p=document.createElement('p');p.className='note';p.style.margin='6px 0 0';
  p.textContent=w?`MeCoBi better in ${w.better}, worse in ${w.worse} · Wilcoxon p = ${w.p==null?'–':w.p.toPrecision(2)}`:'';card.appendChild(p);});}
// ---- tables
function tables(){
 const s=S.summary;
 let h='<thead><tr><th>tool</th><th>built</th><th>off-target</th><th>timeouts</th><th>median s</th><th>CPU h</th><th>shape %</th>'+MET.map(m=>`<th>${m[1]} med / mean</th>`).join('')+'</tr></thead><tbody>';
 TOOLS.forEach(t=>{const r=s[t];h+=`<tr><td>${swatch(t)} ${t}</td><td>${r.built}</td><td>${r.off_na?'–':r.off}</td><td>${r.timeouts}</td><td>${fmt(r.t_med,1)}</td><td>${fmt(r.cpu_h,2)}</td><td>${fmt(r.shape_pct,0)}</td>`+
  MET.map(m=>`<td>${fmt(r[m[0]].med)} / ${fmt(r[m[0]].mean)}</td>`).join('')+'</tr>';});
 document.getElementById('t-summary').innerHTML=h+'</tbody>';
 let w='<thead><tr><th>vs MeCoBi</th>'+MET.map(m=>`<th>${m[1]}</th>`).join('')+'</tr></thead><tbody>';
 TOOLS.filter(t=>t!=='MeCoBi').forEach(t=>{w+=`<tr><td>${swatch(t)} ${t}</td>`+MET.map(m=>{const c=S.wilcoxon[t][m[0]];
  return `<td>${c.better} / ${c.worse} <span class="muted">(p=${c.p==null?'–':c.p.toPrecision(2)})</span></td>`;}).join('')+'</tr>';});
 document.getElementById('t-wilcoxon').innerHTML=w+'</tbody>';
 const cns=[...new Set(DATA.map(d=>d.cn))].sort((a,b)=>a-b);
 let c='<thead><tr><th>CN</th><th>n</th>'+TOOLS.map(t=>`<th>${t}</th>`).join('')+'</tr></thead><tbody>';
 cns.forEach(cn=>{const ds=DATA.filter(d=>d.cn===cn);c+=`<tr><td>${cn}</td><td>${ds.length}</td>`+TOOLS.map(t=>{
  const b=ds.filter(d=>d.tools[t]&&d.tools[t].built);const med=median(b.map(d=>d.tools[t].ckmrmsd).filter(v=>v!=null));
  return `<td>${Math.round(100*b.length/ds.length)} % · ${fmt(med)}</td>`;}).join('')+'</tr>';});
 document.getElementById('t-cn').innerHTML=c+'</tbody>';}
// ---- structure browser
let SORT={k:'refcode',dir:1},SELECTED=null;
function structTable(){
 const q=document.getElementById('q').value.trim().toLowerCase();
 let ds=DATA.filter(d=>!q||d.refcode.toLowerCase().includes(q)||d.metal.toLowerCase()===q||('cn'+d.cn)===q.replace(/\s/g,'')||String(d.cn)===q);
 const key=d=>SORT.k==='refcode'?d.refcode:SORT.k==='cn'?d.cn:(d.tools[SORT.k]&&d.tools[SORT.k].ckmrmsd!=null?d.tools[SORT.k].ckmrmsd:1e9);
 ds.sort((a,b)=>(key(a)>key(b)?1:key(a)<key(b)?-1:0)*SORT.dir);
 let h='<thead><tr><th data-k="refcode">refcode</th><th data-k="cn">metal · CN</th>'+TOOLS.map(t=>`<th data-k="${t}">${swatch(t)} ${t}</th>`).join('')+'</tr></thead><tbody>';
 ds.forEach(d=>{const vals=TOOLS.map(t=>d.tools[t]&&d.tools[t].built?d.tools[t].ckmrmsd:null);const best=Math.min(...vals.filter(v=>v!=null));
  h+=`<tr data-rc="${d.refcode}" class="${d.refcode===SELECTED?'sel':''}"><td>${d.refcode}</td><td>${d.metal} · ${d.cn}</td>`+
  vals.map((v,i)=>{const r=d.tools[TOOLS[i]];return `<td>${r&&!r.built?'<span class="muted">failed</span>':(v===best?'<b>'+fmt(v)+'</b>':fmt(v))}${r&&r.off?' <span class="pill">off</span>':''}</td>`;}).join('')+'</tr>';});
 const t=document.getElementById('structs');t.innerHTML=h+'</tbody>';
 t.querySelectorAll('th').forEach(th=>th.onclick=()=>{const k=th.dataset.k;SORT={k,dir:SORT.k===k?-SORT.dir:1};structTable();});
 t.querySelectorAll('tbody tr').forEach(tr=>tr.onclick=()=>{SELECTED=tr.dataset.rc;structTable();view(SELECTED);});}
function drawMetalBonds(v,metal,cn){const atoms=v.getModel().selectedAtoms({});let mp=null;
 for(const a of atoms)if(a.elem===metal){mp={x:a.x,y:a.y,z:a.z};break;}if(!mp)return;
 atoms.filter(a=>a.elem!=='H'&&a.elem!==metal).map(a=>({a,d:Math.hypot(a.x-mp.x,a.y-mp.y,a.z-mp.z)}))
  .sort((p,q)=>p.d-q.d).slice(0,cn).forEach(o=>v.addCylinder({start:mp,end:{x:o.a.x,y:o.a.y,z:o.a.z},radius:.1,color:'0x888888',fromCap:1,toCap:1}));
 // hydrides: an H within 1.9 A of the metal that is not on a ligand atom
 atoms.filter(a=>a.elem==='H'&&Math.hypot(a.x-mp.x,a.y-mp.y,a.z-mp.z)<1.9&&
   !atoms.some(b=>b!==a&&b.elem!=='H'&&b.elem!==metal&&Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z)<1.3))
  .forEach(a=>v.addCylinder({start:mp,end:{x:a.x,y:a.y,z:a.z},radius:.1,color:'0x888888',fromCap:1,toCap:1}));}
// The five panes (crystal + 4 tools) and their 3Dmol viewers are created ONCE and reused: every
// createViewer opens a WebGL context and browsers keep only ~16, so building fresh viewers per click
// silently blanked the older panes after a few selections.
let PANES=null,VIEWERS=[];
function buildPanes(){
 const box=document.getElementById('viewers');box.innerHTML='';
 const names=[['Crystal (2-hop core)',null]].concat(TOOLS.map(t=>[t,t]));
 PANES=names.map(([name,t])=>{const vb=document.createElement('div');vb.className='vbox';
  vb.innerHTML=`<div class="cap">${t?swatch(t):''}<b>${name}</b></div><div class="v"><p class="note empty" style="position:absolute;inset:0;margin:0;padding:8px;display:none">no structure</p></div><div class="m"></div>`;
  box.appendChild(vb);const host=vb.querySelector('.v');
  const v=$3Dmol.createViewer(host,{backgroundColor:css('--surface-1')});
  if(v.enableFog)v.enableFog(false);   // no depth fog: it hid most of a large complex
  return {t,v,meta:vb.querySelector('.m'),empty:vb.querySelector('.empty')};});
 VIEWERS=PANES.map(p=>p.v);
 // sync rotation/zoom across the panes; the guard stops setView -> callback -> setView recursion
 let syncing=false;
 VIEWERS.forEach(a=>a.setViewChangeCallback&&a.setViewChangeCallback(vw=>{
  if(syncing)return;syncing=true;try{VIEWERS.forEach(b=>{if(b!==a)b.setView(vw);});}finally{syncing=false;}}));}
function view(rc){
 const d=DATA.find(x=>x.refcode===rc);
 if(typeof $3Dmol==='undefined'){document.getElementById('viewers').innerHTML='<p class="note">3Dmol.js did not load (needs arch_comparison/3Dmol-min.js or internet).</p>';return;}
 if(!PANES)buildPanes();
 const bg=css('--surface-1');
 PANES.forEach(p=>{const t=p.t,r=t?d.tools[t]:null,xyz=t?(r&&r.xyz):d.crystal,v=p.v;
  p.meta.textContent=!t?`${d.refcode} · ${d.metal}, CN ${d.cn}`:!r||!r.built?(r&&r.err?'failed: '+r.err.slice(0,60):'not built'):
   `c-km ${fmt(r.ckmrmsd)} · poly ${fmt(r.poly_cshm)} · bond ${fmt(r.bond_rmsd)}${r.off?' · off-target':''}`;
  v.setBackgroundColor(bg);v.removeAllShapes();v.removeAllModels();
  p.empty.style.display=xyz?'none':'block';
  if(xyz){v.addModel(xyz,'xyz');
   v.setStyle({},{stick:{radius:.13},sphere:{scale:.24}});v.setStyle({elem:d.metal},{sphere:{scale:.45}});
   drawMetalBonds(v,d.metal,d.cn);v.zoomTo();}   // fit the WHOLE complex (slab + zoom), not the metal
  v.render();});
 document.getElementById('structh').scrollIntoView({behavior:'smooth'});}
// ---- gallery: one card per complex, one WebGL canvas per card (a 1 x N viewer grid), built when
// the card scrolls into view and released (context lost on purpose) when it leaves -- browsers keep
// only ~16 WebGL contexts, and the browser above already holds five.
const GITEMS=[['Crystal',null]].concat(TOOLS.map(t=>[t,t]));
const GLIVE=new Map();let GIO=null;
function galleryList(){
 const q=document.getElementById('gq').value.trim().toLowerCase(),hy=document.getElementById('ghyd').checked;
 const k=document.getElementById('gsort').value;
 const ds=DATA.filter(d=>(!hy||d.hyd)&&(!q||d.refcode.toLowerCase().includes(q)||d.metal.toLowerCase()===q||String(d.cn)===q||('cn'+d.cn)===q.replace(/\s/g,'')));
 const ck=d=>d.tools.MeCoBi&&d.tools.MeCoBi.ckmrmsd!=null?d.tools.MeCoBi.ckmrmsd:-1;
 ds.sort((a,b)=>k==='worst'?ck(b)-ck(a):k==='cn'?a.cn-b.cn||a.refcode.localeCompare(b.refcode):
  k==='metal'?a.metal.localeCompare(b.metal)||a.refcode.localeCompare(b.refcode):a.refcode.localeCompare(b.refcode));
 return ds;}
function galOff(card){
 if(!GLIVE.has(card))return;GLIVE.delete(card);
 const host=card.querySelector('.gv');
 host.querySelectorAll('canvas').forEach(c=>{try{const gl=c.getContext('webgl2')||c.getContext('webgl');
  const ext=gl&&gl.getExtension('WEBGL_lose_context');if(ext)ext.loseContext();}catch(e){}});
 host.innerHTML='<div class="ph note">scroll to load</div>';}
function galOn(card){
 if(GLIVE.has(card)||typeof $3Dmol==='undefined')return;
 const d=DATA.find(x=>x.refcode===card.dataset.rc),host=card.querySelector('.gv');host.innerHTML='';
 const n=GITEMS.length,bg=css('--surface-1');
 const grid=$3Dmol.createViewerGrid(host,{rows:1,cols:n,control_all:true},{backgroundColor:bg});
 const vs=grid[0];
 GITEMS.forEach(([name,t],j)=>{const v=vs[j],r=t?d.tools[t]:null,xyz=t?(r&&r.xyz):d.crystal;
  if(v.enableFog)v.enableFog(false);
  if(xyz){v.addModel(xyz,'xyz');v.setStyle({},{stick:{radius:.13},sphere:{scale:.24}});
   v.setStyle({elem:d.metal},{sphere:{scale:.45}});drawMetalBonds(v,d.metal,d.cn);v.zoomTo();}
  v.render();});
 for(let j=1;j<n;j++){const dv=document.createElement('div');dv.className='gdiv';dv.style.left=(100*j/n)+'%';host.appendChild(dv);}
 GLIVE.set(card,vs);}
function gallery(){
 const box=document.getElementById('gallery');[...GLIVE.keys()].forEach(galOff);if(GIO)GIO.disconnect();
 const ds=galleryList();document.getElementById('gcount').textContent=`${ds.length} of ${DATA.length} complexes`;
 box.innerHTML=ds.map(d=>{
  const caps=GITEMS.map(([name,t])=>`<div>${t?swatch(t):''}<b>${name}</b>${t&&d.tools[t]&&d.tools[t].off?' <span class="pill">off</span>':''}</div>`).join('');
  const meta=GITEMS.map(([name,t])=>{const r=t?d.tools[t]:null;
   return `<div>${!t?'2-hop core'+(d.hyd?' + H⁻':''):!r||!r.built?'<span class="muted">'+(r&&r.timeout?'timeout':'not built')+'</span>':
    `c-km ${fmt(r.ckmrmsd)} · D-MAE3 ${fmt(r.dmae3)} · poly ${fmt(r.poly_cshm)}<br>bond ${fmt(r.bond_rmsd)} · shape ${r.shape===true?'✓':r.shape===false?'✗':'–'} · CN ${r.cnm===true?'✓':r.cnm===false?'✗ ('+r.cnd+')':'–'}`}</div>`;}).join('');
  return `<div class="card gcard" data-rc="${d.refcode}"><div class="ghead"><b>${d.refcode}</b><span class="muted">${d.metal} · CN ${d.cn}</span>${
   d.hyd?`<span class="pill">${d.hyd} H⁻</span>`:''}<a data-open="${d.refcode}">open in the browser above ↑</a></div>
   <div class="gscroll"><div class="ginner" style="--n:${GITEMS.length}"><div class="gcols">${caps}</div>
   <div class="gv"><div class="ph note">scroll to load</div></div><div class="gcols gmeta">${meta}</div></div></div></div>`;}).join('');
 // the wheel must scroll the page, not zoom the molecules (scrolling the gallery would otherwise
 // zoom every card it passes into the metal): stop it before it reaches 3Dmol's handlers
 box.querySelectorAll('.ginner').forEach(g=>['wheel','mousewheel','DOMMouseScroll'].forEach(ev=>
  g.addEventListener(ev,e=>e.stopPropagation(),{capture:true})));
 box.querySelectorAll('a[data-open]').forEach(a=>a.onclick=()=>{SELECTED=a.dataset.open;structTable();view(SELECTED);});
 GIO=new IntersectionObserver(es=>es.forEach(e=>e.isIntersecting?galOn(e.target):galOff(e.target)),{rootMargin:'250px 0px'});
 box.querySelectorAll('.gcard').forEach(c=>GIO.observe(c));}
// ---- wiring
function renderAll(){header();success();timechart();quality();scatter();tables();structTable();gallery();}
document.getElementById('gsort').onchange=gallery;document.getElementById('gq').oninput=gallery;
document.getElementById('ghyd').onchange=gallery;
document.getElementById('setsel').querySelectorAll('button').forEach(b=>b.onclick=()=>{SET=b.dataset.v;
 document.querySelectorAll('#setsel button').forEach(x=>x.setAttribute('aria-pressed',x===b));quality();});
const sm=document.getElementById('scmetric');MET.forEach(m=>{const o=document.createElement('option');o.value=m[0];o.textContent=m[1];sm.appendChild(o);});
sm.onchange=scatter;document.getElementById('q').oninput=structTable;
document.getElementById('themebtn').onclick=()=>{const cur=document.documentElement.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
 document.documentElement.setAttribute('data-theme',cur==='dark'?'light':'dark');renderAll();if(SELECTED)view(SELECTED);};
renderAll();
</script></body></html>
"""

if __name__ == "__main__":
    main()
