"""Generate the coordination-site figures in ``docs/sites/`` from ``SITE_VECTORS``.

One SVG per geometry: the metal at the centre and every numbered coordination
**site** at its projected position. The site ids match the code, the text isomer
notation, and the 3D "Assign" scene exactly (invariant 7) — so regenerating here
means the docs can never drift from ``SITE_VECTORS``.

The view is a single orthographic camera shared by every figure (so the grid
reads consistently). The camera azimuth/elevation are chosen by a small search
that keeps every site's projection clear of the central metal — a pure 1,1,1
isometric view would drop tetrahedral site 0 (and dodecahedral's axial site)
straight onto the metal.

Run:  python scripts/gen_site_figures.py
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from mecobi.assembly import sites

OUT = Path(__file__).resolve().parents[1] / "docs" / "sites"
SIZE = 300
C = SIZE / 2.0          # centre (metal) at 150,150
FILL_R = 126.0          # the outermost site sits this many px from the centre
MIN_CLEAR = 40.0        # every site must project this far from the central metal
MIN_PAIR = 34.0         # and this far from every other site (labels don't collide)


def _camera(az_deg: float, el_deg: float):
    """Orthographic screen basis (right, up) for an azimuth/elevation view."""
    a, e = math.radians(az_deg), math.radians(el_deg)
    forward = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    right = np.array([-math.sin(a), math.cos(a), 0.0])
    up = np.cross(right, forward)
    return right, up / np.linalg.norm(up)


def _unit_vectors():
    out = {}
    for g, vecs in sites.SITE_VECTORS.items():
        arr = np.array(vecs, dtype=float)
        out[g.value] = np.array([v / np.linalg.norm(v) for v in arr])
    return out


def _metrics(all_vecs, right, up):
    """(scale, min centre-clearance px, min site-site distance px) for a camera."""
    proj = {n: [(float(v @ right), float(v @ up)) for v in arr] for n, arr in all_vecs.items()}
    max_r = max(math.hypot(x, y) for pts in proj.values() for x, y in pts)
    scale = FILL_R / max_r
    clear = min(math.hypot(x, y) for pts in proj.values() for x, y in pts) * scale
    pair = min(
        math.hypot(a[0] - b[0], a[1] - b[1])
        for pts in proj.values() for i, a in enumerate(pts) for b in pts[i + 1:]
    ) * scale
    return scale, clear, pair


def _choose_camera(all_vecs):
    """Pick az/el maximising the worst of (centre-clearance, site spacing) in px."""
    best, best_score = None, -1.0
    for az in range(6, 55):
        for el in range(6, 45):
            right, up = _camera(az, el)
            _, clear, pair = _metrics(all_vecs, right, up)
            score = min(clear, pair)
            if score > best_score:
                best_score, best = score, (az, el)
    return best


def _svg(name: str, arr, right, up, scale: float) -> str:
    pts = [(C + float(v @ right) * scale, C - float(v @ up) * scale) for v in arr]
    cn = len(arr)
    depth = [float(v @ np.cross(right, up)) for v in arr]  # -ve = behind, drawn first
    L = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
        f'viewBox="0 0 {SIZE} {SIZE}">',
        f'  <text x="{C}" y="22" font-family="system-ui,Arial" font-size="15" '
        f'font-weight="600" fill="#8a8a8a" text-anchor="middle">{name} · CN {cn}</text>',
    ]
    for sx, sy in pts:
        L.append(f'  <line x1="{C}" y1="{C}" x2="{sx:.1f}" y2="{sy:.1f}" '
                 f'stroke="#8a8a8a" stroke-width="2"/>')
    L.append(f'  <circle cx="{C}" cy="{C}" r="17" fill="#5a5ad8"/>')
    L.append(f'  <text x="{C}" y="{C}" font-family="system-ui,Arial" font-size="14" '
             f'font-weight="700" fill="#ffffff" text-anchor="middle" '
             f'dominant-baseline="central">M</text>')
    for i in sorted(range(cn), key=lambda k: depth[k]):  # back-to-front so front reads on top
        sx, sy = pts[i]
        L.append(
            f'  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="15" fill="#ffffff" '
            f'stroke="#5a5ad8" stroke-width="2.5"/>'
            f'<text x="{sx:.1f}" y="{sy:.1f}" font-family="system-ui,Arial" '
            f'font-size="16" font-weight="700" fill="#1a1a2a" text-anchor="middle" '
            f'dominant-baseline="central">{i}</text>'
        )
    L.append('</svg>')
    return "\n".join(L) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    all_vecs = _unit_vectors()
    az, el = _choose_camera(all_vecs)
    right, up = _camera(az, el)
    scale, clear, pair = _metrics(all_vecs, right, up)
    print(f"camera az={az} el={el} deg | min centre-clearance {clear:.0f}px "
          f"(>= {MIN_CLEAR:.0f}) | min site spacing {pair:.0f}px (>= {MIN_PAIR:.0f})")
    assert clear >= MIN_CLEAR and pair >= MIN_PAIR, "camera search failed the spacing bounds"
    for name, arr in all_vecs.items():
        (OUT / f"{name}.svg").write_text(_svg(name, arr, right, up, scale), encoding="utf-8")
        print("wrote", name)


if __name__ == "__main__":
    main()
