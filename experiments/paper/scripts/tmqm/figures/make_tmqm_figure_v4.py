"""tmQM figure for the paper (04/11): as v3, with the table (f) giving the MAE only (no relative MAE columns).

    python figures/make_tmqm_figure_v4.py            -> figures/Figure_tmqm_v4.{pdf,svg,png} and Figure_tmqm_v4_f.*
                                                         (panel f alone; random split)
    python figures/make_tmqm_figure_v4.py --split ligand

Same scheme as v2, with the parity plots stacked as dipole (top) and gap (bottom), and the table of Figure 7 (from
tmqm_table.py: MAE, error relative to the mean DFT value, the two controls and the literature) in the lower right.

a  where the structures and the values come from: tmQM (CSD -> GFN2-xTB optimisation -> DFT values), MeCoBi with the
   crystal isomer (donors, geometry and isomer from the crystal), MeCoBi from the SMILES alone; GFN2-xTB single points
   on the structures give five values that are added to the 2D features of a LightGBM model.
b-e out-of-fold predictions (10,175 complexes, folds by largest ligand, mean of three seeds) against the DFT values:
   dipole moment and gap, 2D features alone and 2D + xTB of the crystal-isomer structure. Hexagonal bins (log count);
   in b and c the 1,074 complexes with a DFT dipole below 1 D (mostly centrosymmetric) are drawn as points.
Style as Figures 4 and 5 (Arial 7 pt, Okabe-Ito colours, MeCoBi blue #486CAB).
"""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
TM = HERE.parent
mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 7, "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
    "legend.fontsize": 6.5, "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "lines.linewidth": 1.0, "pdf.fonttype": 42,
    "svg.fonttype": "none", "savefig.dpi": 600})
MM = 1 / 25.4
MECOBI, GREY, ORANGE, INK = "#486CAB", "#7F7F7F", "#D55E00", "#1F2328"
# blue, orange and grey mark where a structure comes from (panel a, and the rows of f); the parity plots use a neutral
# black density scale and gold for the complexes with almost no dipole moment, so no colour has two meanings
CMAP = LinearSegmentedColormap.from_list("density", ["#E6E6E6", "#A6A6A6", "#555555", "#111111"])
LOWDIP = "#E6B33C"

import sys
SPLIT = sys.argv[sys.argv.index("--split") + 1] if "--split" in sys.argv else "random"
TAG = "" if SPLIT == "ligand" else f"_{SPLIT}"
xtb = pd.read_csv(TM / "xtb_sp" / "results" / f"oof_tmqm_xtb{TAG}.csv").set_index("refcode")
TABLE = pd.read_csv(TM / "results" / f"table_tmqm{TAG}.csv")
tab = pd.read_csv(TM / "table.csv").set_index("refcode").loc[xtb.index]


def label(ax, s, dx=0.0, dy=0.0):
    ax.text(dx, 1.0 + dy, s, transform=ax.transAxes, fontsize=8, fontweight="bold", va="bottom", ha="left")


def box(ax, x, y, w, h, text, ec, fc="white", bold=False, fs=6.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8", lw=0.6, ec=ec, fc=fc))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK,
            fontweight="bold" if bold else "normal", linespacing=1.15)


def arrow(ax, x0, y0, x1, y1, c):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=6, lw=0.7, color=c,
                                 shrinkA=0, shrinkB=0))


def scheme(ax):
    ax.set_xlim(0, 180); ax.set_ylim(0.5, 46.5); ax.axis("off")
    rows = [  # y, colour, row title, boxes
        (34.5, GREY, "tmQM\n(reference)",
         ["CSD crystal\nstructure", "GFN2-xTB\noptimisation", "DFT single point\n(TPSSh)", "DFT dipole, gap\n(targets)"]),
        (20.0, MECOBI, "Crystal\nisomer",
         ["ligand SMILES\n+ donors, geometry,\nisomer of the crystal", "MeCoBi assembly\n+ GFN2-xTB relaxation",
          "GFN2-xTB\nsingle point", "xTB values (5):\ngap, HOMO, LUMO,\ndipole, q(metal)"]),
        (5.5, ORANGE, "SMILES\nonly",
         ["metal, oxidation state,\nligand SMILES", "MeCoBi: predicted\ndonors, all isomers,\nrelaxation",
          "lowest-energy\nisomer: GFN2-xTB\nsingle point", "xTB values (5)"]),
    ]
    xs, w, h = [17, 45, 73, 101], 24, 9.5
    for y, c, title, texts in rows:
        ax.text(1.0, y + h / 2, title, ha="left", va="center", fontsize=6.3, fontweight="bold", color=c,
                linespacing=1.1)
        for k, (x, t) in enumerate(zip(xs, texts)):
            box(ax, x, y, w, h, t, ec=c, fc="#F6F8FB" if k == 3 else "white", fs=5.6)
            if k:
                arrow(ax, xs[k - 1] + w + 0.4, y + h / 2, x - 0.4, y + h / 2, c)
    # the tmQM geometry is also given a GFN2-xTB single point (upper limit)
    ax.text(57, 32.6, "xTB single point on the tmQM geometry: upper limit", fontsize=5.2, color=GREY,
            ha="center", va="top", style="italic")
    # model
    mx, mw = 140, 37
    box(ax, mx, 27.5, mw, 8.5, "2D features from the SMILES\n(Morgan fingerprints, RDKit\ndescriptors, metal, charge)",
        ec=INK, fs=5.6)
    box(ax, mx, 14.0, mw, 8.5, "LightGBM\nten-fold CV" + ("" if SPLIT == "random" else ",\nfolds by largest ligand"), ec=INK, fs=5.6, bold=False)
    box(ax, mx, 2.0, mw, 7.5, "predicted DFT\ndipole moment and gap", ec=INK, fc="#F6F8FB", fs=5.6)
    arrow(ax, mx + mw / 2, 27.1, mx + mw / 2, 22.9, INK)
    arrow(ax, mx + mw / 2, 13.6, mx + mw / 2, 9.9, INK)
    arrow(ax, 125.4, 24.75, mx - 0.4, 18.6, MECOBI)
    arrow(ax, 125.4, 10.25, mx - 0.4, 16.0, ORANGE)
    ax.text(132.0, 23.6, "train", fontsize=5.2, color=MECOBI, ha="center", rotation=-38)
    ax.text(132.0, 11.6, "apply", fontsize=5.2, color=ORANGE, ha="center", rotation=31)
    arrow(ax, 125.4, 38.0, mx - 0.4, 20.6, GREY)
    ax.text(131.5, 31.0, "labels", fontsize=5.2, color=GREY, ha="center", rotation=-52)


def parity(ax, t, col, lim, unit, title, highlight=False):
    y = tab[t].to_numpy(float)
    p = xtb[f"{t}|{col}"].to_numpy(float)
    hb = ax.hexbin(y, p, gridsize=40, extent=(*lim, *lim), cmap=CMAP, norm=LogNorm(vmin=1, vmax=300), mincnt=1,
                   linewidths=0, rasterized=True)
    if highlight:
        m = y < 1
        ax.scatter(y[m], p[m], s=1.2, color=LOWDIP, alpha=0.45, linewidths=0, rasterized=True, zorder=3)
        ax.text(0.97, 0.05, f"DFT < 1 {unit}:\nMAE {np.abs(y[m] - p[m]).mean():.1f} {unit}", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=5.6, color="#9A7414")   # darker gold: legible on white
    ax.plot(lim, lim, ls="--", lw=0.6, color="#999999", zorder=2)
    ax.set_xlim(lim); ax.set_ylim(lim); ax.set_aspect("equal")
    mae = np.abs(y - p).mean()
    r2 = 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    ax.text(0.04, 0.96, f"MAE {mae:.2f} {unit}\n$R^2$ {r2:.2f}", transform=ax.transAxes, va="top", fontsize=6.2)
    ax.set_title(title, fontsize=6.2, pad=3, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return hb


# rows of the table: (label, block of tmqm_table.py, input), then the literature
ROWS = [("2D features (negative control)", 0, "2D features (negative control)", None),
        ("2D + isomer label", 0, "2D + isomer label", None),
        ("xTB alone (linear fit)", 0, "xTB of the crystal-isomer structure alone", MECOBI),
        ("2D + xTB, MeCoBi (crystal isomer)", 0, "2D + xTB of the crystal-isomer structure", MECOBI),
        ("2D + xTB, MeCoBi (SMILES only)*", 1, "2D + xTB of the lowest-energy SMILES-only isomer", ORANGE),
        ("2D + xTB, tmQM geometry (positive control)", 0, "2D + xTB of the tmQM geometry (positive control)", GREY)]
# colour of a row = the structure its xTB values come from, as in panel a (None: no structure)
# ref. 39, all 108,541 tmQM complexes, random split; relative to the mean gap of tmQM (2.95 eV)
LIT = [("Lit.: XGBoost, composition + RDKit", None, 0.40),
       ("Lit.: DimeNet++, SchNet (tmQM geometry)", None, (0.28, 0.30))]
TMQM_GAP_MEAN = 2.95


def table(ax):
    """MAE only. Two number columns, right-aligned under their headers; the room freed by the relative MAE goes to a
    larger font, wider row spacing and a light band on alternate rows."""
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    blocks = list(dict.fromkeys(TABLE.block))
    cols = [("Dipole\nMAE (D)", "dipole_D", 2), ("Gap\nMAE (eV)", "gap_eV", 3)]
    xs = [0.0, 0.79, 0.99]                      # label | dipole | gap (right edges of the numbers)
    fs, dy = 6.0, 0.080
    tr = ax.transAxes
    y = 0.98
    ax.text(xs[0], y - 0.03, "Model input", fontsize=6.2, fontweight="bold", va="top", transform=tr)
    for k, (c, _, _) in enumerate(cols):
        ax.text(xs[1 + k], y, c, fontsize=6.2, fontweight="bold", va="top", ha="right", transform=tr,
                linespacing=1.15)
    y -= dy * 1.45
    ax.plot([0, 1.0], [y + dy * 0.30] * 2, lw=0.5, color=INK, transform=tr, clip_on=False)
    for i, (lab, b, inp, src) in enumerate(ROWS):
        r = TABLE[(TABLE.block == blocks[b]) & (TABLE.input == inp)].set_index("property")
        if i % 2 == 1:
            ax.add_patch(plt.Rectangle((0, y - dy * 0.72), 1.0, dy, transform=tr, color="#F3F5F8", lw=0, zorder=0))
        if src:
            ax.add_patch(plt.Rectangle((0.0, y - dy * 0.46), 0.018, dy * 0.42, transform=tr, color=src, lw=0))
        tc = src if src in (MECOBI, ORANGE) else INK
        ax.text(xs[0] + 0.03, y, lab, fontsize=fs, va="top", transform=tr, color=tc)
        for k, (_, t, nd) in enumerate(cols):
            ax.text(xs[1 + k], y, f"{r.loc[t, 'MAE']:.{nd}f}", fontsize=fs, va="top", ha="right", transform=tr,
                    color=tc)
        y -= dy
    ax.plot([0, 1.0], [y + dy * 0.30] * 2, lw=0.3, color=GREY, transform=tr, clip_on=False)
    for lab, _, gap in LIT:
        ax.text(xs[0] + 0.03, y, lab, fontsize=fs, va="top", transform=tr, style="italic")
        ax.text(xs[1], y, "–", fontsize=fs, va="top", ha="right", transform=tr)
        g = f"{gap:.2f}" if isinstance(gap, float) else f"{gap[0]:.2f}–{gap[1]:.2f}"
        ax.text(xs[2], y, g, fontsize=fs, va="top", ha="right", transform=tr)
        y -= dy
    ax.plot([0, 1.0], [y + dy * 0.30] * 2, lw=0.5, color=INK, transform=tr, clip_on=False)
    n0 = TABLE[TABLE.block == blocks[0]].n.iloc[0]
    n1 = TABLE[TABLE.block == blocks[1]].n.iloc[0]
    ax.text(xs[0], y - 0.005, f"{n0:,} complexes, {'random' if SPLIT == 'random' else 'ligand-split'} ten-fold CV.\n"
            f"*{n1:,} complexes built from the SMILES alone.\n"
            "Lit.: all 108,541 tmQM complexes, random 70/15/15 split (ref. 39).\n"
            "Coloured mark: structure the xTB values come from, as in a.", fontsize=5.4, va="top",
            transform=tr, color=GREY, linespacing=1.35)


def main():
    fig = plt.figure(figsize=(180 * MM, 150 * MM))
    gs = fig.add_gridspec(2, 1, height_ratios=[0.50, 1.0], left=0.085, right=0.985, top=0.99, bottom=0.07, hspace=0.06)
    axa = fig.add_subplot(gs[0])
    scheme(axa)
    label(axa, "a", dx=-0.045, dy=-0.06)
    low = gs[1].subgridspec(1, 2, width_ratios=[1.0, 0.82], wspace=0.10)
    sub = low[0].subgridspec(2, 2, wspace=0.45, hspace=0.42)
    specs = [("dipole_D", "floor", (0, 20), "D", "Dipole, 2D only", True),
             ("dipole_D", "floor + xTB(MeCoBi)", (0, 20), "D", "Dipole, 2D + xTB", True),
             ("gap_eV", "floor", (0, 6), "eV", r"$\Delta E_\mathrm{HM}$, 2D only", False),
             ("gap_eV", "floor + xTB(MeCoBi)", (0, 6), "eV", r"$\Delta E_\mathrm{HM}$, 2D + xTB", False)]
    for k, (t, col, lim, unit, title, hi) in enumerate(specs):
        ax = fig.add_subplot(sub[k // 2, k % 2])
        hb = parity(ax, t, col, lim, unit, title, hi)
        name = "dipole moment (D)" if t == "dipole_D" else "HOMO–LUMO gap (eV)"
        ax.set_xlabel(f"DFT {name}")
        ax.set_ylabel(f"Predicted {name}" if k % 2 == 0 else "")
        label(ax, "bcde"[k], dx=-0.30, dy=0.06)
    right = low[1].subgridspec(2, 1, height_ratios=[0.16, 1.0], hspace=0.0)
    cax = fig.add_axes([0.63, 0.655, 0.16, 0.008])
    cb = fig.colorbar(hb, cax=cax, orientation="horizontal")
    cb.set_label("complexes per bin (b–e)", fontsize=5.6)
    cb.ax.tick_params(labelsize=5.4, width=0.4, length=2)
    cb.outline.set_linewidth(0.4)
    axt = fig.add_subplot(right[1])
    table(axt)
    label(axt, "f", dx=-0.04, dy=0.02)
    name = f"Figure_tmqm_v4{'' if SPLIT == 'random' else '_' + SPLIT}"
    for ext in ("pdf", "svg", "png"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=600 if ext == "png" else None)
    # panel f alone, to replace it in the assembled figure
    box = axt.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).padded(0.04)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(HERE / f"{name}_f.{ext}", dpi=600 if ext == "png" else None, bbox_inches=box)
    # panels b-f alone (everything below the scheme), to replace them in the assembled figure
    r = fig.canvas.get_renderer()
    boxes = [a.get_tightbbox(r) for a in fig.axes if a is not axa]
    from matplotlib.transforms import Bbox
    box = Bbox.union(boxes).transformed(fig.dpi_scale_trans.inverted()).padded(0.04)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(HERE / f"{name}_bf.{ext}", dpi=600 if ext == "png" else None, bbox_inches=box)
    print("written", HERE / f"{name}.png", HERE / f"{name}_f.png", HERE / f"{name}_bf.png")


if __name__ == "__main__":
    main()
