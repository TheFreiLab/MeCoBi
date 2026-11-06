import { useState, useRef, useLayoutEffect, useCallback } from "react";

// Flat 2D depiction with clickable atoms. Click an atom to
// mark/unmark it as a coordinating (donor) atom. Uses indigo structural cues
// per the house style; element letters keep it legible.
//
// Keyboard: the atoms are one tab stop (a roving tabindex). Arrow keys move
// between atoms in index order, Home/End jump to the ends, Space/Enter toggles.
// Each atom is a checkbox named "N, atom 3" (the 0-based index used by the
// donor-index notation).
//
// The SVG keeps a fixed internal coordinate system (viewBox); zoom only changes
// the rendered pixel size, and the viewport scrolls. It opens at a "fit" zoom so
// the whole ligand is visible, and can be zoomed with the buttons or Ctrl+wheel
// to click crowded atoms — instead of being squeezed to an unreadable size or
// clipped by the panel.
const ZOOM_MIN = 0.2, ZOOM_MAX = 5, ZOOM_STEP = 1.25;
const clampZoom = (z) => Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, z));

export default function MoleculeDepiction({ atoms, bonds, selected, onToggle }) {
  const [zoom, setZoom] = useState(1);
  const viewportRef = useRef(null);
  const [focusPos, setFocusPos] = useState(0); // position (in `atoms`) of the one tab stop
  const atomRefs = useRef([]);

  // Whether the user has taken over zoom (buttons / Ctrl+wheel). While false we
  // keep the depiction fitted to the viewport (and re-fit on resize); once the
  // user zooms, we stop auto-fitting until the ligand changes.
  const userZoomed = useRef(false);

  const hasAtoms = !!atoms?.length;
  const xs = hasAtoms ? atoms.map((a) => a.x) : [0];
  const ys = hasAtoms ? atoms.map((a) => a.y) : [0];
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const pad = 1.1, scale = 30;
  const w = (maxX - minX + 2 * pad) * scale;
  const h = (maxY - minY + 2 * pad) * scale;
  const px = (x) => (x - minX + pad) * scale;
  const py = (y) => (maxY - y + pad) * scale; // flip y for SVG

  // Zoom that makes the whole molecule fit the viewport; never upscales a small
  // ligand past its natural size (cap at 1).
  const fitZoom = useCallback(() => {
    const el = viewportRef.current;
    if (!el || !w || !h) return 1;
    const availW = el.clientWidth - 4, availH = el.clientHeight - 4;
    return clampZoom(Math.min(availW / w, availH / h, 1));
  }, [w, h]);

  // On new ligand (w/h change): reset to fit and hand zoom control back to fit.
  useLayoutEffect(() => {
    userZoomed.current = false;
    setZoom(fitZoom());
  }, [fitZoom]);

  // Keep it fitted while the panel is resized, until the user zooms manually.
  useLayoutEffect(() => {
    const el = viewportRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => {
      if (!userZoomed.current) setZoom(fitZoom());
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [fitZoom]);

  // Ctrl+wheel to zoom. Attached natively (non-passive) so preventDefault works
  // and the page/panel doesn't scroll while zooming.
  useLayoutEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const onWheel = (e) => {
      if (!e.ctrlKey) return; // plain scroll pans the viewport
      e.preventDefault();
      userZoomed.current = true;
      setZoom((z) => clampZoom(z * Math.exp(-e.deltaY * 0.0015)));
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  if (!hasAtoms) return null;

  const bump = (factor) => {
    userZoomed.current = true;
    setZoom((z) => clampZoom(z * factor));
  };

  const sel = new Set(selected || []);
  const tabPos = Math.min(focusPos, atoms.length - 1);

  const moveFocus = (pos) => {
    const next = Math.max(0, Math.min(atoms.length - 1, pos));
    setFocusPos(next);
    atomRefs.current[next]?.focus();
  };
  const onAtomKey = (e, k) => {
    const keys = {
      ArrowRight: k + 1, ArrowDown: k + 1, ArrowLeft: k - 1, ArrowUp: k - 1,
      Home: 0, End: atoms.length - 1,
    };
    if (e.key in keys) {
      e.preventDefault();
      moveFocus(keys[e.key]);
    } else if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      onToggle(atoms[k].idx);
    }
  };

  return (
    <div className="depiction">
      <div className="depiction-controls">
        <button
          type="button"
          className="ghost"
          title="Zoom out"
          onClick={() => bump(1 / ZOOM_STEP)}
        >
          −
        </button>

        <button
          type="button"
          className="ghost"
          title="Fit to area"
          onClick={() => {
            userZoomed.current = false;
            setZoom(fitZoom());
          }}
        >
          {Math.round(zoom * 100)}%
        </button>

        <button
          type="button"
          className="ghost"
          title="Zoom in"
          onClick={() => bump(ZOOM_STEP)}
        >
          +
        </button>

        <span className="muted depiction-hint">Ctrl + scroll to zoom</span>
      </div>

      <div className="depiction-viewport" ref={viewportRef}>
        <svg
          width={w * zoom}
          height={h * zoom}
          viewBox={`0 0 ${w} ${h}`}
          style={{ display: "block" }}
          role="group"
          aria-label="Donor atoms. Arrow keys move between atoms, Space marks or unmarks a donor."
        >
          {bonds.map((b, i) => {
            const A = atoms[b.a], B = atoms[b.b];
            return (
              <line
                key={i}
                x1={px(A.x)}
                y1={py(A.y)}
                x2={px(B.x)}
                y2={py(B.y)}
                stroke="var(--text-secondary)"
                strokeWidth={b.order >= 2 ? 3 : 1.5}
              />
            );
          })}

          {atoms.map((a, k) => {
            const on = sel.has(a.idx);
            return (
              <g
                key={a.idx}
                ref={(el) => { atomRefs.current[k] = el; }}
                className="depiction-atom"
                role="checkbox"
                aria-checked={on}
                aria-label={`${a.symbol}, atom ${a.idx}`}
                tabIndex={k === tabPos ? 0 : -1}
                onFocus={() => setFocusPos(k)}
                onKeyDown={(e) => onAtomKey(e, k)}
                onClick={() => onToggle(a.idx)}
                style={{ cursor: "pointer" }}
              >
                <circle
                  cx={px(a.x)}
                  cy={py(a.y)}
                  r={on ? 12 : 9.5}
                  fill={on ? "var(--accent-500)" : "var(--surface-1)"}
                  stroke={on ? "var(--accent-bright)" : "var(--border-strong)"}
                  strokeWidth={1.5}
                />
                <text
                  x={px(a.x)}
                  y={py(a.y)}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize="10.5"
                  fontFamily="var(--mono)"
                  fill={on ? "var(--on-accent)" : "var(--text-primary)"}
                >
                  {a.symbol}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
