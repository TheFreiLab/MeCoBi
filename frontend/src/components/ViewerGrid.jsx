import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import MiddleName from "./MiddleName.jsx";

// Multi-pane 3D viewer. One $3Dmol viewer grid = ONE WebGL
// context no matter how many panes — separate createViewer() canvases would
// hit the browser's ~8-16 context cap and silently kill the oldest viewer.
// control_all links rotation/zoom across panes for isomer comparison.
// On a phone-width screen every structure stacks in a single column so each pane
// stays large enough to read (a 3-up grid would be ~120px wide on a 375px screen).
const dims = (n, narrow) => {
  const cols = narrow ? 1 : n <= 1 ? 1 : n === 2 ? 2 : n <= 4 ? 2 : 3;
  return { cols, rows: Math.ceil(n / cols) };
};

// Track the phone breakpoint so the grid recreates (single column) when crossed.
function useNarrow() {
  const [narrow, setNarrow] = useState(
    () => typeof window !== "undefined" && window.matchMedia("(max-width: 640px)").matches
  );
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 640px)");
    const on = () => setNarrow(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return narrow;
}

const ORGANIC = new Set(["H", "B", "C", "N", "O", "F", "Si", "P", "S", "Cl", "Se", "Br", "I"]);
const COORD_CUTOFF = 2.9; // A; catches eta-cap ring carbons (~2.2-2.5) with margin
const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);

function drawBond(v, m, a) {
  v.addCylinder({
    start: { x: m.x, y: m.y, z: m.z },
    end: { x: a.x, y: a.y, z: a.z },
    radius: 0.12, fromCap: 1, toCap: 1,
    color: "0x9c95f0", // house accent; distinguishes dative bonds from covalent sticks
  });
}

// 3Dmol sometimes auto-bonds the metal to nearby atoms, which clutters the view
// and clashes with the dative bonds we draw. Strip every bond touching the metal
// so we alone own the coordination bonds. (Called before setStyle so sticks obey.)
function stripMetalBonds(atoms, m) {
  for (const a of atoms) {
    if (!a.bonds) continue;
    if (a === m) { a.bonds = []; a.bondOrder = []; continue; }
    for (let i = a.bonds.length - 1; i >= 0; i--) {
      if (a.bonds[i] === m.index) {
        a.bonds.splice(i, 1);
        if (a.bondOrder) a.bondOrder.splice(i, 1);
      }
    }
  }
}

// Connected components of `members` using the (organic) bond graph.
function components(members, byIndex) {
  const set = new Set(members.map((a) => a.index));
  const seen = new Set();
  const out = [];
  for (const a of members) {
    if (seen.has(a.index)) continue;
    const comp = [];
    const stack = [a];
    seen.add(a.index);
    while (stack.length) {
      const cur = stack.pop();
      comp.push(cur);
      for (const bi of cur.bonds || []) {
        if (set.has(bi) && !seen.has(bi)) { seen.add(bi); stack.push(byIndex.get(bi)); }
      }
    }
    out.push(comp);
  }
  return out;
}

// Draw the metal coordination. Seed from the TRUE topology donors (metalIndex /
// donorIndices). We must tell a pi-face apart from a chelate: an eta5-Cp / eta6-
// arene cap is a set of donors DIRECTLY BONDED TO EACH OTHER in a ring, whereas a
// chelate's donors (the two N of a bipyridine, the three N of a terpyridine) are
// NOT bonded to each other — only joined through a backbone. So we group donors by
// donor–donor adjacency FIRST: a group of >=3 mutually bonded donors is a face and
// gets ONE bond to its ring centroid (expanding to complete the ring, since the
// topology may only mark 3 of a Cp's 5 carbons); every other donor is a point
// donor and gets its own bond. Expanding before grouping (the old approach) let a
// chelate's near-metal backbone carbons bridge its two donors into a spurious
// "cap", drawing one bond into the middle of the ligand instead of one per donor.
function addMetalBonds(v, metalIndex, donorIndices) {
  const atoms = v.selectedAtoms({});
  const byIndex = new Map(atoms.map((a) => [a.index, a]));
  const m = metalIndex != null ? byIndex.get(metalIndex) : atoms.find((a) => !ORGANIC.has(a.elem));
  if (!m) return;
  stripMetalBonds(atoms, m);

  const heavy = atoms.filter((a) => a !== m && a.elem !== "H" && ORGANIC.has(a.elem));
  const near = (a) => dist(a, m) <= COORD_CUTOFF;
  const seed = donorIndices && donorIndices.length
    ? donorIndices.map((i) => byIndex.get(i)).filter(Boolean)
    : heavy.filter(near);

  for (const comp of components(seed, byIndex)) {
    if (comp.length >= 3) {
      // A genuine pi-face: complete the ring by pulling in near-metal atoms bonded
      // into it, so the centroid is the true ring centre, then draw one bond.
      const inSet = new Set(comp.map((a) => a.index));
      for (let changed = true; changed; ) {
        changed = false;
        for (const a of heavy) {
          if (inSet.has(a.index) || !near(a)) continue;
          if ((a.bonds || []).some((bi) => inSet.has(bi))) { inSet.add(a.index); changed = true; }
        }
      }
      const ring = [...inSet].map((i) => byIndex.get(i)).filter(Boolean);
      const c = ring.reduce((s, a) => ({ x: s.x + a.x, y: s.y + a.y, z: s.z + a.z }),
        { x: 0, y: 0, z: 0 });
      drawBond(v, m, { x: c.x / ring.length, y: c.y / ring.length, z: c.z / ring.length });
    } else {
      for (const a of comp) drawBond(v, m, a);
    }
  }
}

export default function ViewerGrid({ items }) {
  const elRef = useRef(null);
  const narrow = useNarrow();
  const tokens = items.map((it) => it.token).join(",");

  useEffect(() => {
    const el = elRef.current;
    if (!el || !window.$3Dmol || !items.length) return;
    let cancelled = false;
    Promise.all(items.map((it) => api.fileText(it.token))).then((texts) => {
      if (cancelled) return;
      el.innerHTML = ""; // rebuild the grid; the single shared context goes with it
      const { rows, cols } = dims(items.length, narrow);
      const grid = window.$3Dmol.createViewerGrid(
        el,
        { rows, cols, control_all: true },
        { backgroundColor: "0x0E1B24" } // house dark blue-grey, CPK-friendly
      );
      texts.forEach((xyz, i) => {
        const v = grid[Math.floor(i / cols)][i % cols];
        v.addModel(xyz, "xyz");
        // Strip metal auto-bonds + draw dative bonds BEFORE setStyle, so the stick
        // style doesn't redraw the metal's auto-bonds we just removed.
        addMetalBonds(v, items[i].metalIndex, items[i].donorIndices);
        v.setStyle({}, { stick: { radius: 0.14 }, sphere: { scale: 0.25 } });
        v.zoomTo();
        v.render();
      });
    });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tokens, narrow]);

  if (!items.length) return null;
  const { rows, cols } = dims(items.length, narrow);
  return (
    <div className="viewer-grid" style={{ height: (narrow ? 130 : 180) + rows * (narrow ? 220 : 240) }}>
      <div className="viewer-grid-canvas" ref={elRef} />
      {items.map((it, i) => (
        <span
          className="viewer-grid-label mono"
          key={it.token}
          style={{
            left: `calc(${(i % cols) * (100 / cols)}% + 8px)`,
            top: `calc(${Math.floor(i / cols) * (100 / rows)}% + 8px)`,
            maxWidth: `calc(${100 / cols}% - 16px)`, // its own pane, not 40% of the grid
          }}
        >
          {it.isomer_label ? <span className="vg-iso">{it.isomer_label} · </span> : null}
          <MiddleName text={it.name} />
        </span>
      ))}
    </div>
  );
}
