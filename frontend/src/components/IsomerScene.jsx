import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { CSS2DRenderer, CSS2DObject } from "three/examples/jsm/renderers/CSS2DRenderer.js";
import { api } from "../api.js";
import BusyLabel from "./BusyLabel.jsx";
import { prefersReducedMotion } from "../motion.js";

// Schematic 3D isomer-assembly scene, docked beside the table.
// Metal centre + every numbered coordination SITE (0..CN-1, shared numbering with
// the index mode — invariant 7). Select a ligand, then click/drag its donor(s)
// onto sites: a monodentate takes one site, a bidentate two *cis* sites (live
// validation rejects trans / occupied). Emits a {ligand -> ordered site ids}
// assignment that builds the exact isomer. Indigo structural cues (house §5).
const COL = {
  metal: 0x42535d, empty: 0xbcc4ca, hover: 0xafa9ec,
  pending: 0x9c95f0, bound: 0x5a5ad8, danger: 0xa32d2d, bond: 0x3d3da8, guide: 0xd9dee2,
};
const dentName = (d) => ({ 1: "mono", 2: "bi", 3: "tri", 4: "tetra" }[d] || `${d}`);
const shortSmiles = (s, n = 20) => (s.length > n ? s.slice(0, n - 1) + "…" : s);
const key2 = (a, b) => (a < b ? `${a},${b}` : `${b},${a}`);
const dentWord = (d) => ({ 2: "bidentate", 3: "tridentate", 4: "tetradentate" }[d] || `${d}-dentate`);
// "site 0" / "sites 0 and 2" / "sites 0, 2 and 4"
const siteList = (ss) => (ss.length === 1 ? `site ${ss[0]}`
  : `sites ${ss.slice(0, -1).join(", ")} and ${ss[ss.length - 1]}`);

// Donor-element accent colours. The LETTER is the primary signal (CVD-safe — the
// author has mild deuteranomaly); colour only reinforces, and the hues avoid a
// red/green contrast. C (arene/Cp caps) stays neutral so hetero donors pop.
const ELEM_COL = {
  O: "#c65a2e", N: "#2f6fd0", S: "#b8860b", P: "#d07a1f", Cl: "#1f9e8a",
  Br: "#8a5a2b", I: "#7a3fb0", F: "#2f9e6a", C: "#8a929b",
};
// η-arene/Cp caps are carbon rings: draw them in the carbon grey, not the UI indigo
// (a data colour must not read as the accent).
ELEM_COL["η"] = ELEM_COL.C;
const elemColor = (s) => ELEM_COL[s] || "#5a5ad8";
// Letter colour for text ON an element-coloured disc: white or near-black, whichever
// contrasts more (white failed AA on the lighter S/P/Cl/F/C discs, audit H11).
function inkOn(hex) {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  const L = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  const DARK_L = 0.0118; // #0e1b24
  return 1.05 / (L + 0.05) >= (L + 0.05) / (DARK_L + 0.05) ? "#fff" : "#0e1b24";
}

// Compact 2D skeletal depiction (SVG string) of a ligand from /api/depict data.
// Bonds/heteroatoms use currentColor (the container sets it, so it is theme-aware);
// coordinating (donor) atoms get an indigo disc so you can see how it attaches.
function depictSvg(dep, donors, donorSites, isArene) {
  if (!dep || !dep.atoms || !dep.atoms.length) return null;
  const A = dep.atoms, B = dep.bonds || [];
  const xs = A.map((a) => a.x), ys = A.map((a) => a.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const pad = 1.1, scale = 12;
  const w = (maxX - minX + 2 * pad) * scale, h = (maxY - minY + 2 * pad) * scale;
  const X = (x) => ((x - minX + pad) * scale).toFixed(1);
  const Y = (y) => ((maxY - y + pad) * scale).toFixed(1);
  const don = new Set(donors || []);
  const siteOf = donorSites || {}; // atom idx -> site id it's bound to
  let s = "";
  for (const b of B) {
    const a1 = A[b.a], a2 = A[b.b];
    s += `<line x1="${X(a1.x)}" y1="${Y(a1.y)}" x2="${X(a2.x)}" y2="${Y(a2.y)}" stroke="currentColor" stroke-width="${b.order >= 2 ? 2 : 1.2}" stroke-opacity="0.7"/>`;
  }
  for (const a of A) {
    const isDon = don.has(a.idx);
    // Donor: element-coloured disc with the element letter; if we know which site
    // it is bound to, hang a small numbered badge off it (structure -> site map).
    if (isDon) {
      // η-cap (arene/Cp): every ring atom is part of ONE hapto cap, so colour them
      // uniformly and skip per-atom site badges (the whole cap maps to a facial
      // triad, not donor-per-site). σ-donors keep their element colour + site badge.
      const col = isArene ? ELEM_COL.C : elemColor(a.symbol);
      const r = isArene ? 5.5 : 7;
      s += `<circle cx="${X(a.x)}" cy="${Y(a.y)}" r="${r}" fill="${col}"/>`;
      if (!isArene)
        s += `<text x="${X(a.x)}" y="${Y(a.y)}" font-size="9" font-weight="700" text-anchor="middle" dominant-baseline="central" font-family="monospace" fill="${inkOn(col)}">${a.symbol}</text>`;
      const site = isArene ? null : siteOf[a.idx];
      if (site != null) {
        const bx = (+X(a.x) + 8.5).toFixed(1), by = (+Y(a.y) - 8.5).toFixed(1);
        s += `<circle cx="${bx}" cy="${by}" r="5.5" fill="#fff" stroke="${col}" stroke-width="1.4"/>`;
        // Site number in dark ink on the white badge; the element colour stays on its ring.
        s += `<text x="${bx}" y="${by}" font-size="8" font-weight="700" text-anchor="middle" dominant-baseline="central" font-family="monospace" fill="#0e1b24">${site}</text>`;
      }
    } else if (a.symbol !== "C") {
      s += `<text x="${X(a.x)}" y="${Y(a.y)}" font-size="9" text-anchor="middle" dominant-baseline="central" font-family="monospace" fill="currentColor">${a.symbol}</text>`;
    }
  }
  const W = Math.round(w), H = Math.round(h);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${s}</svg>`;
}

export default function IsomerScene({ complex, geometry, onClose, onBuild }) {
  const wrapRef = useRef(null);
  const rootRef = useRef(null);
  // Below 1100px the scene stacks UNDER the whole table, often a screen or more down, so
  // clicking Assign looked like it did nothing (audit H13): bring it into view on open.
  useEffect(() => {
    if (window.matchMedia("(max-width: 1100px)").matches) {
      rootRef.current?.scrollIntoView({ block: "start", behavior: prefersReducedMotion() ? "auto" : "smooth" });
    }
  }, []);
  const sceneRef = useRef({});
  const [data, setData] = useState(null); // {sites, cis_pairs, default_assignment}
  const [error, setError] = useState("");
  const [active, setActive] = useState(null);       // ligand being placed
  const [pending, setPending] = useState([]);       // sites clicked so far for `active`
  // Why the last click on a site was refused (audit H14). Shown and announced next to the
  // placed counter; cleared by the next successful action, never on a timer.
  const [placeError, setPlaceError] = useState("");
  const [assignment, setAssignment] = useState({}); // committed: ligand -> [site ids]
  const [drag, setDrag] = useState(null);
  const [depictions, setDepictions] = useState(null); // per-ligand /api/depict data
  const [busy, setBusy] = useState(false); // build in flight (keeps scene open with a spinner)
  const [disconnected, setDisconnected] = useState(false); // user clicked "Disconnect all"

  const denticities = complex.ligands.map((l) => l.denticity);
  const areneLigands = complex.ligands
    .map((l, i) => (l.is_arene ? i : -1))
    .filter((i) => i >= 0);
  // Centroid η-cap ligands: a selected ring is ONE site at its centroid (denticity
  // 1), and a cap takes no cis constraint (it can sit trans to anything). /api/sites
  // and the placement validator treat their sites specially.
  const capLigands = complex.ligands
    .map((l, i) => (l.pi_sites && l.pi_sites.length ? i : -1))
    .filter((i) => i >= 0);
  const capSet = new Set(capLigands);

  // Per-site donor "slots" for a ligand — one per coordination site, so slot k maps
  // to site k (matching the assembly donor-group order: centroid caps first, then
  // σ-donors). Each slot is {sym, cap, atoms}. A legacy η-arene facial triad (no
  // pi_sites) is a single "η" slot; a plain ligand is one σ slot per coord atom.
  function donorSlots(lig) {
    const L = complex.ligands[lig];
    const ca = L?.coord_atoms || [];
    const pis = (L?.pi_sites || []).filter((r) => r.length);
    if (L?.is_arene && !pis.length) return [{ sym: "η", cap: true, atoms: ca }];
    const dep = depictions && depictions[lig];
    const byIdx = dep && dep.atoms ? new Map(dep.atoms.map((a) => [a.idx, a.symbol])) : null;
    const slots = pis.map((ring) => ({ sym: "η", cap: true, atoms: ring }));
    const capAtoms = new Set(pis.flat());
    for (const idx of ca) {
      if (capAtoms.has(idx)) continue;
      slots.push({ sym: byIdx ? byIdx.get(idx) || "?" : "?", cap: false, atoms: [idx] });
    }
    return slots;
  }
  const donorSymbols = (lig) => donorSlots(lig).map((s) => s.sym);

  useEffect(() => {
    let cancelled = false;
    api
      .sites(geometry, denticities, areneLigands, capLigands)
      .then((d) => {
        if (cancelled) return;
        if (d.detail) return setError(d.detail);
        setData(d);
        const def = {};
        for (const [k, v] of Object.entries(d.default_assignment)) def[Number(k)] = v;
        setAssignment(def);
      })
      .catch((e) => !cancelled && setError(String(e)));
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fetch a 2D depiction per ligand, to render at its attached position.
  useEffect(() => {
    let cancelled = false;
    Promise.all(complex.ligands.map((l) => api.depict(l.smiles).catch(() => null)))
      .then((ds) => !cancelled && setDepictions(ds));
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cisSet = new Set((data?.cis_pairs || []).map(([a, b]) => key2(a, b)));
  const siteOwner = {};
  for (const [lig, ss] of Object.entries(assignment)) for (const s of ss) siteOwner[s] = Number(lig);

  function selectLigand(i) {
    setPlaceError("");
    if (active === i) { setActive(null); setPending([]); return; }
    if (assignment[i] != null) setAssignment((a) => { const n = { ...a }; delete n[i]; return n; });
    setActive(i);
    setPending([]);
  }

  useEffect(() => {
    if (!data || !wrapRef.current) return;
    const wrap = wrapRef.current;
    let W = wrap.clientWidth, H = wrap.clientHeight;
    const R = Math.max(...data.sites.map((s) => Math.hypot(s.x, s.y, s.z)), 2.5);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, W / H, 0.1, 100);
    // Start pulled back (~5R): the floating 2D ligand depictions sit well outside
    // the coordination sites, so a tight framing clips them / feels cramped.
    camera.position.set(R * 2.5, R * 1.9, R * 3.8);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(window.devicePixelRatio);
    wrap.appendChild(renderer.domElement);

    const labelRenderer = new CSS2DRenderer();
    labelRenderer.setSize(W, H);
    Object.assign(labelRenderer.domElement.style, { position: "absolute", top: "0", left: "0", pointerEvents: "none" });
    wrap.appendChild(labelRenderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = !prefersReducedMotion();
    controls.enablePan = false;
    controls.minDistance = R * 1.4;
    controls.maxDistance = R * 8;

    const ro = new ResizeObserver(() => {
      W = wrap.clientWidth; H = wrap.clientHeight;
      if (!W || !H) return;
      camera.aspect = W / H; camera.updateProjectionMatrix();
      renderer.setSize(W, H); labelRenderer.setSize(W, H);
    });
    ro.observe(wrap);

    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const kl = new THREE.DirectionalLight(0xffffff, 0.85); kl.position.set(6, 9, 7); scene.add(kl);
    const fl = new THREE.DirectionalLight(0xbcc8e0, 0.35); fl.position.set(-6, -3, -5); scene.add(fl);

    const metal = new THREE.Mesh(
      new THREE.SphereGeometry(0.55, 40, 40),
      new THREE.MeshStandardMaterial({ color: COL.metal, metalness: 0.55, roughness: 0.35 })
    );
    scene.add(metal);
    const mdiv = document.createElement("div");
    mdiv.className = "vertex-label metal-label";
    mdiv.textContent = complex.metal;
    metal.add(new CSS2DObject(mdiv));

    const spheres = {}; // siteId -> mesh
    const labels = {};  // siteId -> label div (updated to show the bound ligand)
    const meshList = [];
    data.sites.forEach((s) => {
      const p = new THREE.Vector3(s.x, s.y, s.z);
      const gl = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), p]);
      scene.add(new THREE.Line(gl, new THREE.LineBasicMaterial({ color: COL.guide, transparent: true, opacity: 0.6 })));
      const m = new THREE.Mesh(
        new THREE.SphereGeometry(0.34, 32, 32),
        new THREE.MeshStandardMaterial({ color: COL.empty, metalness: 0.1, roughness: 0.55 })
      );
      m.position.copy(p);
      m.userData = { id: s.id };
      scene.add(m);
      spheres[s.id] = m; meshList.push(m);
      // A real <button> so sites are reachable by Tab and activated by Enter/Space
      // (same action as a click). Its aria-label carries the state (set in the paint effect).
      const div = document.createElement("button");
      div.type = "button";
      div.className = "vertex-label clickable";
      div.dataset.sid = s.id;
      div.textContent = String(s.id);
      div.setAttribute("aria-label", `Site ${s.id}, empty`);
      div.style.pointerEvents = "auto";
      div.style.cursor = "pointer";
      div.onclick = (e) => { e.stopPropagation(); sceneRef.current.assignSite(s.id); };
      labels[s.id] = div;
      const anchor = new THREE.Object3D();
      anchor.position.copy(p.clone().normalize().multiplyScalar(R + 0.55));
      scene.add(anchor);
      anchor.add(new CSS2DObject(div));
    });

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    sceneRef.current = {
      scene, camera, renderer, labelRenderer, controls, ro, spheres, labels, sitePos: spheres,
      bonds: {}, bridges: {}, pulses: {}, R,
      ui: { active, pending, assignment, denticities, cisSet, capSet },
    };

    function flash(sid) {
      spheres[sid].material.color.setHex(COL.danger);
      setTimeout(() => paint(), 260);
    }
    function assignSite(sid) {
      const { ui } = sceneRef.current;
      if (ui.owner && ui.owner[sid] != null) {  // release the occupant
        const lig = ui.owner[sid];
        setAssignment((a) => { const n = { ...a }; delete n[lig]; return n; });
        setPlaceError("");
        return;
      }
      if (ui.active == null) {
        setPlaceError("Select a ligand first (L0, L1 …), then click a site.");
        return;
      }
      const d = ui.denticities[ui.active];
      const cur = ui.pending;
      if (cur.includes(sid)) return;
      // Multidentate placement validity, from the cis (adjacency) graph:
      //  - eta-arene / Cp (facial cap): the new site must be cis to ALL placed
      //    sites, so the three donors form a facial triad;
      //  - chelate (bidentate / meridional tridentate): the new site must be cis
      //    to AT LEAST ONE placed site, so the donors stay connected (a bidentate
      //    is then just the cis check, unchanged).
      // Centroid η-cap ligands: no cis constraint (caps and their σ-legs can span
      // any sites — a metallocene's two caps are trans). Only σ-chelates and legacy
      // facial arenes are validated against the cis graph.
      if (d >= 2 && cur.length > 0 && !(ui.capSet && ui.capSet.has(ui.active))) {
        const arene = !!(complex.ligands[ui.active] && complex.ligands[ui.active].is_arene);
        const cisAll = cur.every((s) => ui.cisSet.has(key2(s, sid)));
        const cisAny = cur.some((s) => ui.cisSet.has(key2(s, sid)));
        if (arene ? !cisAll : !cisAny) {
          flash(sid);
          const L = `L${ui.active}`;
          setPlaceError(arene
            ? `Site ${sid} isn't next to all of ${siteList(cur)}. An η-arene needs three ` +
              "mutually neighbouring sites (one face)."
            : cur.length === 1
              ? `Site ${sid} isn't next to site ${cur[0]}. ${L} (${dentWord(d)}) needs ` +
                "neighbouring (cis) sites."
              : `Site ${sid} isn't next to any of ${L}'s placed sites (${cur.join(", ")}). ` +
                `A ${dentWord(d)} ligand's sites must stay connected.`);
          return;
        }
      }
      setPlaceError("");
      const next = [...cur, sid];
      if (next.length === d) {
        if (!prefersReducedMotion()) for (const s of next) sceneRef.current.pulses[s] = performance.now();
        const act = ui.active;
        const na = { ...ui.assignment, [act]: next };
        setAssignment(na);
        setPending([]);
        // Jump the selection to the next still-unplaced ligand.
        const nxt = complex.ligands.findIndex((_, i) => na[i] == null);
        setActive(nxt >= 0 ? nxt : null);
      } else {
        setPending(next);
      }
    }
    sceneRef.current.assignSite = assignSite;

    function paint() {
      const { ui } = sceneRef.current;
      const owner = {};
      for (const [lig, ss] of Object.entries(ui.assignment)) for (const s of ss) owner[s] = Number(lig);
      for (const [id, m] of Object.entries(spheres)) {
        const sid = Number(id);
        if (owner[sid] != null) m.material.color.setHex(COL.bound);
        else if (ui.pending.includes(sid)) m.material.color.setHex(COL.pending);
        else m.material.color.setHex(COL.empty);
      }
    }
    sceneRef.current.paint = paint;

    const SNAP = 40;
    sceneRef.current.pickAt = (cx, cy) => {
      const r = renderer.domElement.getBoundingClientRect();
      if (cx < r.left || cx > r.right || cy < r.top || cy > r.bottom) return null;
      pointer.x = ((cx - r.left) / r.width) * 2 - 1;
      pointer.y = -((cy - r.top) / r.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hit = raycaster.intersectObjects(meshList, false)[0];
      if (hit) return hit.object.userData.id;
      let best = null, bd = SNAP;
      for (const [id, m] of Object.entries(spheres)) {
        const v = m.position.clone().project(camera);
        const sx = r.left + ((v.x + 1) / 2) * r.width;
        const sy = r.top + ((1 - v.y) / 2) * r.height;
        const dd = Math.hypot(sx - cx, sy - cy);
        if (dd < bd) { bd = dd; best = Number(id); }
      }
      return best;
    };

    function onMove(e) {
      const r = renderer.domElement.getBoundingClientRect();
      pointer.x = ((e.clientX - r.left) / r.width) * 2 - 1;
      pointer.y = -((e.clientY - r.top) / r.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hit = raycaster.intersectObjects(meshList, false)[0];
      renderer.domElement.style.cursor = hit ? "pointer" : "grab";
    }
    function onClick(e) {
      const vid = sceneRef.current.pickAt(e.clientX, e.clientY);
      if (vid != null) assignSite(vid);
    }
    renderer.domElement.addEventListener("pointermove", onMove);
    renderer.domElement.addEventListener("click", onClick);

    let raf;
    const animate = () => {
      raf = requestAnimationFrame(animate);
      controls.update();
      const now = performance.now();
      for (const [id, m] of Object.entries(spheres)) {
        const t0 = sceneRef.current.pulses[id];
        if (t0) {
          const p = (now - t0) / 320;
          m.scale.setScalar(p >= 1 ? 1 : 1 + 0.5 * Math.sin(p * Math.PI));
          if (p >= 1) delete sceneRef.current.pulses[id];
        }
      }
      renderer.render(scene, camera);
      labelRenderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      renderer.domElement.removeEventListener("pointermove", onMove);
      renderer.domElement.removeEventListener("click", onClick);
      controls.dispose();
      renderer.dispose();
      wrap.removeChild(renderer.domElement);
      wrap.removeChild(labelRenderer.domElement);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  // Sync interaction state into the scene + repaint bonds/bridges.
  useEffect(() => {
    const s = sceneRef.current;
    if (!s.spheres) return;
    const owner = {};
    for (const [lig, ss] of Object.entries(assignment)) for (const si of ss) owner[si] = Number(lig);
    s.ui = { active, pending, assignment, denticities, cisSet, capSet, owner };
    s.paint();
    // Show which ligand occupies each site (preview the layout): a bound site
    // reads "<site>·L<lig>", a site being placed reads with the active ligand.
    if (s.labels) {
      // site id -> donor element bound there (donor k aligns with site k).
      const siteSym = {};
      for (const [lig, ss] of Object.entries(assignment)) {
        const syms = donorSymbols(Number(lig)); // slot syms: η for caps, element for σ
        ss.forEach((sid, k) => { siteSym[sid] = syms[k] ?? "?"; });
      }
      const activeSyms = active != null ? donorSymbols(active) : [];
      const label = (sym, sid) =>
        `<b>${sym}</b><sub style="font-weight:400">${sid}</sub>`;
      for (const [id, div] of Object.entries(s.labels)) {
        const sid = Number(id);
        // A bound site shows its donor's element colour as the label's edge (the letter
        // stays in the label's text colour so it always reads); other states reset it.
        const edge = owner[sid] != null ? elemColor(siteSym[sid] ?? "?") : "";
        div.style.borderColor = edge;
        div.style.boxShadow = edge ? `inset 0 0 0 1px ${edge}, 0 1px 3px rgba(14, 27, 36, 0.12)` : "";
        if (owner[sid] != null) {
          div.innerHTML = label(siteSym[sid] ?? "?", sid);
          div.setAttribute("aria-label", `Site ${sid}, bound to L${owner[sid]} (${siteSym[sid] ?? "?"})`);
        } else if (pending.includes(sid)) {
          const sym = activeSyms[pending.indexOf(sid)] ?? "?";
          div.innerHTML = label(sym, sid);
          div.setAttribute("aria-label", `Site ${sid}, being placed for L${active} (${sym})`);
        } else {
          div.textContent = String(sid);
          div.setAttribute("aria-label", `Site ${sid}, empty`);
        }
        div.classList.toggle("bound", owner[sid] != null);
      }
    }
    // η-caps get a ring + one metal->centroid bond (below), not a plain σ bond, so
    // skip their sites in the per-site bond loop. Legacy facial arene: all its sites;
    // centroid caps: the first pi_sites.length slots (caps precede σ-legs in slots).
    const capSites = new Set();
    for (const [lig, ss] of Object.entries(assignment)) {
      const L = complex.ligands[lig];
      const pis = (L?.pi_sites || []).filter((r) => r.length);
      if (L?.is_arene && !pis.length) ss.forEach((sid) => capSites.add(sid));
      else pis.forEach((_, k) => { if (ss[k] != null) capSites.add(ss[k]); });
    }
    // bonds metal->bound site (σ-donors only)
    for (const [id, m] of Object.entries(s.spheres)) {
      const sid = Number(id);
      const want = owner[sid] != null && !capSites.has(sid);
      if (want && !s.bonds[sid]) {
        const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), m.position.clone()]);
        const line = new THREE.Line(g, new THREE.LineBasicMaterial({ color: COL.bond }));
        s.scene.add(line); s.bonds[sid] = line;
      } else if (!want && s.bonds[sid]) {
        s.scene.remove(s.bonds[sid]); delete s.bonds[sid];
      }
    }
    // η-cap rings. Legacy facial η-arene: one circle through its three sites + a bond
    // to their centroid. Centroid η-caps (metallocene/sandwich/ansa): a small ring
    // perpendicular to the axis AT each cap-slot site, plus a metal->site dative bond.
    s.caps = s.caps || {};
    for (const [lig, obj] of Object.entries(s.caps)) { obj.forEach((o) => s.scene.remove(o)); delete s.caps[lig]; }
    const mkRing = (c, u, v, r) =>
      new THREE.Mesh(
        new THREE.TubeGeometry(
          new THREE.CatmullRomCurve3(
            Array.from({ length: 60 }, (_, i) => {
              const a = (i / 60) * Math.PI * 2;
              return c.clone().addScaledVector(u, r * Math.cos(a)).addScaledVector(v, r * Math.sin(a));
            }), true), 80, 0.03, 8),
        new THREE.MeshStandardMaterial({ color: COL.hover, metalness: 0.1, roughness: 0.5,
          transparent: true, opacity: 0.6 }));
    const mkBond = (p) =>
      new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), p.clone()]),
        new THREE.LineBasicMaterial({ color: COL.bond }));
    for (const [lig, ss] of Object.entries(assignment)) {
      const L = complex.ligands[lig];
      const pis = (L?.pi_sites || []).filter((r) => r.length);
      const objs = [];
      if (L?.is_arene && !pis.length && ss.length >= 3) {
        const P = ss.map((sid) => s.spheres[sid].position.clone());
        const c = new THREE.Vector3();
        P.forEach((p) => c.add(p)); c.multiplyScalar(1 / P.length);
        const n = new THREE.Vector3().crossVectors(P[1].clone().sub(P[0]), P[2].clone().sub(P[0])).normalize();
        const u = P[0].clone().sub(c).normalize();
        const v = new THREE.Vector3().crossVectors(n, u).normalize();
        const r = P.reduce((acc, p) => acc + p.distanceTo(c), 0) / P.length;
        objs.push(mkRing(c, u, v, r), mkBond(c));
      } else if (pis.length) {
        pis.forEach((_, k) => {
          const sid = ss[k];
          if (sid == null) return;
          const p = s.spheres[sid].position.clone();
          const dir = p.clone().normalize();
          const t = Math.abs(dir.y) < 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
          const u = new THREE.Vector3().crossVectors(dir, t).normalize();
          const v = new THREE.Vector3().crossVectors(dir, u).normalize();
          objs.push(mkRing(p, u, v, 0.42), mkBond(p));
        });
      }
      if (objs.length) { objs.forEach((o) => s.scene.add(o)); s.caps[lig] = objs; }
    }
    // chelate bridges for bidentate ligands
    for (const [lig, line] of Object.entries(s.bridges)) { s.scene.remove(line); delete s.bridges[lig]; }
    for (const [lig, ss] of Object.entries(assignment)) {
      if (ss.length === 2 && !capSet.has(Number(lig))) {
        const a = s.spheres[ss[0]].position, b = s.spheres[ss[1]].position;
        const mid = a.clone().add(b).multiplyScalar(0.5).normalize().multiplyScalar(s.R * 1.28);
        const curve = new THREE.QuadraticBezierCurve3(a.clone(), mid, b.clone());
        const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 20, 0.06, 8),
          new THREE.MeshStandardMaterial({ color: COL.bound, metalness: 0.1, roughness: 0.5 }));
        s.scene.add(tube); s.bridges[lig] = tube;
      }
    }
    // 2D ligand depiction floating just outside each bound ligand's position.
    s.depictObjs = s.depictObjs || {};
    for (const [lig, obj] of Object.entries(s.depictObjs)) { s.scene.remove(obj); delete s.depictObjs[lig]; }
    if (depictions) {
      for (const [lig, ss] of Object.entries(assignment)) {
        // donor atom idx -> the site it is bound to, so the 2D structure can badge
        // each donor with its site number (structure -> vertex round-trip).
        const L = complex.ligands[lig];
        const ca = L?.coord_atoms || [];
        const pis = (L?.pi_sites || []).filter((r) => r.length);
        const legacyArene = !!L?.is_arene && !pis.length;
        const dsites = {};
        if (!legacyArene) {
          // σ-legs occupy the slots AFTER the caps, so σ-donor j binds site ss[caps+j].
          const capAtoms = new Set(pis.flat());
          const sigmaAtoms = ca.filter((idx) => !capAtoms.has(idx));
          sigmaAtoms.forEach((idx, j) => { const sid = ss[pis.length + j]; if (sid != null) dsites[idx] = sid; });
        }
        const html = depictSvg(depictions[lig], ca, dsites, legacyArene);
        if (!html) continue;
        const c = new THREE.Vector3();
        for (const si of ss) c.add(s.spheres[si].position);
        c.multiplyScalar(1 / ss.length).normalize().multiplyScalar(s.R + 1.4);
        const div = document.createElement("div");
        div.className = "scene-depict";
        div.innerHTML = html;
        const obj = new CSS2DObject(div);
        obj.position.copy(c);
        s.scene.add(obj);
        s.depictObjs[lig] = obj;
      }
    }
  }, [assignment, active, pending, denticities, depictions]);

  function startDrag(e, i) {
    e.preventDefault();
    selectLigand(i);
    const r = e.currentTarget.getBoundingClientRect();
    setDrag({ x0: r.left + r.width / 2, y0: r.top + r.height / 2, x1: e.clientX, y1: e.clientY });
    const move = (ev) => setDrag((d) => (d ? { ...d, x1: ev.clientX, y1: ev.clientY } : d));
    const up = (ev) => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      setDrag(null);
      const el = document.elementFromPoint(ev.clientX, ev.clientY);
      const lab = el && el.closest ? el.closest(".vertex-label[data-sid]") : null;
      const sid = lab ? Number(lab.dataset.sid) : sceneRef.current.pickAt && sceneRef.current.pickAt(ev.clientX, ev.clientY);
      if (sid != null) sceneRef.current.assignSite(sid);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }

  const placed = Object.keys(assignment).length;
  const allPlaced = placed === complex.ligands.length;

  function disconnectAll() {
    setPlaceError("");
    setAssignment({});
    setPending([]);
    setActive(complex.ligands.length ? 0 : null); // highlight the first ligand to place
    setDisconnected(true); // marker the guided tour waits on (see data-tour="assign-cleared")
  }

  async function confirm() {
    const map = {};
    for (const [lig, ss] of Object.entries(assignment)) map[lig] = ss;
    setBusy(true);
    try {
      // Parent closes the scene on success; on error it re-throws so we stay open.
      await onBuild(map);
    } catch {
      setBusy(false);
    }
  }

  return (
    <div className="scene-panel card" data-tour="assign-scene" ref={rootRef}>
      {/* Hidden marker the guided tour waits on: appears only after Disconnect all is
          clicked (not on the scene's initial empty state). */}
      {disconnected && <span data-tour="assign-cleared" aria-hidden="true" style={{ display: "none" }} />}
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
        <h2 style={{ margin: 0 }}>
          Isomer editor — <span className="mono">{complex.name}</span>
        </h2>
        <button className="toggle-btn" onClick={onClose}>Close</button>
      </div>
      {error ? (
        <span className="pill-err">{error}</span>
      ) : (
        <>
          <div className="muted" style={{ marginBottom: 8, fontSize: "var(--text-caption)" }}>
            Select a ligand, then click/drag its donor(s) onto numbered sites: a bidentate needs two cis
            sites, a meridional tridentate three connected sites; a centroid η-cap (Cp/arene, shown η)
            takes any single site — a metallocene's two caps sit trans. Bound sites show the bound donor;
            click a bound site to release it; drag the scene to rotate.
          </div>
          {/* Chips + 3D scene: what the tour's "Place the ligands" step rings, so on a
              phone it can scroll exactly this to the top and keep the card off the sites. */}
          <div data-tour="assign-workspace">
          <div style={{ marginBottom: 10 }} data-tour="assign-palette">
            {complex.ligands.map((l, i) => {
              const at = assignment[i];
              const cls = "palette-chip" + (active === i ? " active" : "") + (at != null ? " assigned" : "");
              return (
                // A <button> for keyboard use. Pointer users select (and drag) on pointerdown,
                // so the click only acts when it came from the keyboard (detail 0); otherwise
                // selectLigand would run twice and toggle the selection straight back off.
                <button type="button" key={i} className={cls} data-smiles={l.smiles}
                  style={{ touchAction: "none" }} aria-pressed={active === i}
                  onPointerDown={(e) => startDrag(e, i)}
                  onClick={(e) => { if (e.detail === 0) selectLigand(i); }}>
                  {active === i ? <span className="place-cue">▶</span> : null}
                  <span className="mono">L{i}</span> · {l.is_arene ? `η${l.coord_atoms?.length ?? ""}` : dentName(l.denticity)}
                  <span className="chip-smiles mono">{shortSmiles(l.smiles)}</span>
                  {l.is_arene ? (
                    at != null ? <span className="mono"> → {at.join(",")}</span> : null
                  ) : (
                    <span style={{ display: "inline-flex", gap: 4, marginLeft: 6, verticalAlign: "middle" }}>
                      {donorSymbols(i).map((sym, k) => (
                        <span key={k} title={`donor ${sym}${at != null && at[k] != null ? ` → site ${at[k]}` : ""}`}
                          style={{
                            display: "inline-flex", alignItems: "center", gap: 2, padding: "0 5px",
                            borderRadius: 9, border: `1.3px solid ${elemColor(sym)}`, color: "inherit",
                            fontFamily: "var(--mono)", fontSize: "var(--text-caption)", fontWeight: 500, lineHeight: 1.35,
                          }}>
                          {sym}{at != null && at[k] != null
                            ? <span style={{ fontWeight: 400 }}>→{at[k]}</span> : null}
                        </span>
                      ))}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
          <div className="scene-wrap" ref={wrapRef} />
          </div>
          <div className="row" style={{ marginTop: 12, justifyContent: "space-between" }}>
            <span className="muted">{placed}/{complex.ligands.length} ligands placed</span>
            <div className="row" style={{ gap: 8 }}>
              <button className="ghost" data-tour="assign-disconnect" disabled={placed === 0 || busy} onClick={disconnectAll}>
                Disconnect all
              </button>
              <button
                className="primary"
                data-tour={allPlaced ? "assign-build" : undefined}
                disabled={!allPlaced || busy}
                onClick={confirm}
              >
                <BusyLabel busy={busy} label="Save this isomer" busyLabel="Saving…" />
              </button>
            </div>
          </div>
          {/* Always mounted (empty when fine) so the refusal reason is announced (H14). */}
          <div className="place-error" role="status">{placeError}</div>
        </>
      )}
      {drag && (
        <svg style={{ position: "fixed", inset: 0, width: "100%", height: "100%", pointerEvents: "none", zIndex: 60 }}>
          <line x1={drag.x0} y1={drag.y0} x2={drag.x1} y2={drag.y1} style={{ stroke: "var(--accent-500)" }} strokeWidth="2" strokeDasharray="5 4" />
          <circle cx={drag.x1} cy={drag.y1} r="5" style={{ fill: "var(--accent-bright)" }} />
        </svg>
      )}
    </div>
  );
}
