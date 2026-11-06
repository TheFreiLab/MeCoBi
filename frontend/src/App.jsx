import { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import freilabLogo from "./assets/freilab-logo.png";
import freilabLogoDark from "./assets/freilab-logo-dark.svg";
import mecobiLogo from "./assets/mecobi-logo.svg";
import BusyLabel from "./components/BusyLabel.jsx";
import ComplexTable from "./components/ComplexTable.jsx";
import FlipCounter from "./components/FlipCounter.jsx";
import GuidedTour from "./components/GuidedTour.jsx";
import Icon from "./components/Icon.jsx";
import IsomerScene from "./components/IsomerScene.jsx";
import LigandLibrary from "./components/LigandLibrary.jsx";
import Results, { MAX_RENDER } from "./components/Results.jsx";
import WebLimitNote from "./components/WebLimitNote.jsx";
import WorkloadNotice from "./components/WorkloadNotice.jsx";
import { TOUR_STEPS } from "./tourSteps.js";

// A themed showcase of real metallodrugs spanning Pt/Ti/Ru/Fe, several
// coordination motifs (square planar, bent metallocene, tris-bidentate
// octahedral, ferrocene sandwich) and a bulky pendant ligand (TLD1433's IP-3T).
// Metal = element symbol; Charge = oxidation state; counter-ions are
// stripped, so only the coordinating ligands are listed.
const SAMPLE = `Index,Name,Metal,Charge,L1,L2,L3,L4,L5,L6
1,Cisplatin,Pt,2,N,N,[Cl-],[Cl-],,
2,Titanocene dichloride,Ti,4,[cH-]1cccc1,[cH-]1cccc1,[Cl-],[Cl-],,
3,TLD1433,Ru,2,CC1=CC(=NC=C1)C2=NC=CC(=C2)C,CC1=CC(=NC=C1)C2=NC=CC(=C2)C,C1=CC2=C3C(=C4C=CC=NC4=C2N=C1)N=C(N3)C5=CC=C(S5)C6=CC=C(S6)C7=CC=CS7,,,
4,Ferroquine,Fe,2,CN(C)Cc1cc[cH-]c1CNc2ccnc3cc(Cl)ccc23,[cH-]1cccc1,,,,
5,BOLD-100,Ru,3,[Cl-],[Cl-],[Cl-],[Cl-],c1ccc2c(c1)cn[nH]2,c1ccc2c(c1)cn[nH]2`;

// Curated examples for the guided tour: cisplatin (Pt(II) square-planar — a real
// cis/trans choice, so the Assign scene can build transplatin) and ferroquine (Fe(II)
// with two Cp rings — showcases η5 cap recognition in the donor-atom step).
const TOUR_SAMPLE = `Pt, 2, N, N, [Cl-], [Cl-]
Fe, 2, CN(C)Cc1cc[cH-]c1CNc2ccnc3cc(Cl)ccc23, [cH-]1cccc1`;

// "Advanced options" — geometry-prep guards (before xtb) and xtb constraints (during),
// each a build_complex toggle. Plain-language labels; the full detail is in each tooltip.
// Grouped for the collapsible; defaults mirror the backend (all on except the opt-in three).
const BUILD_OPTION_GROUPS = [
  {
    label: "Before optimisation — fix the starting geometry",
    items: [
      ["orient_bulky", "Orient bulky ligands",
       "Swing bulky ligands (e.g. phosphines) away from the metal before xtb so they don't clash."],
      ["reposition_donors", "Reposition loose donors",
       "Pull a stranded monodentate donor in to its CSD-average metal–ligand distance."],
      ["clear_metal_region", "Clear the metal region",
       "Rotate a monodentate whose backbone folded across the metal out of the way."],
      ["declash_torsion", "De-clash by rotation",
       "Spin crowded bulky monodentates about the metal–donor axis so they mesh together."],
      ["mchammer", "Force-field pre-placement",
       "Run stk's MCHammer force-field placement pass (off = hand xtb the raw ideal placement)."],
      ["reembed_crowded", "Untangle crowded ligands",
       "When bulky ligands (monodentates or chelates) come out threaded through each other (e.g. Pt(PPh₃)₄, Pt(BINAP)₂), re-embed the whole complex at once with the donors held in place."],
      ["reposition_polydentates", "Reposition loose chelates",
       "Pull stranded chelates/pincers in to their CSD metal–ligand distance — helps a crowded sphere xtb can't pull in, but usually washes out after relaxation."],
    ],
  },
  {
    label: "During optimisation — xtb constraints",
    items: [
      ["linear_restraint", "Keep linear donors straight",
       "Hold CN⁻/CO/azide/nitrosyl donors linear (M–C≡N ≈ 180°)."],
      ["haptic_guard", "Prevent σ→η slip",
       "Pin σ aryl-carbon donors so xtb can't slip them to an η-arene interaction."],
      ["planar_guard", "Keep flat donors coplanar",
       "Keep monodentate sp² N/O donors coplanar with the metal."],
      ["antifusion_guard", "Undo atom fusion",
       "Re-relax with floors if xtb fuses two donors together."],
      ["oxo_antifusion_floors", "Protect terminal oxo/nitrido",
       "Last resort: pin terminal oxo/nitrido at their starting distances from nearby ligand atoms from the FIRST relax. Only if the default build fuses an oxo onto a donor — it freezes a poorly seated oxo and can lengthen M=O."],
      ["metal_surrogate", "Metal stand-in relax",
       "Relax a GFN2-divergent metal (e.g. Y) as an xtb-friendly stand-in (Sc), then restore it."],
    ],
  },
];
// Everything defaults ON except these: they are the opt-in escalations, off by default
// in build_complex because they cost accuracy on ordinary complexes.
const OFF_BY_DEFAULT = new Set([
  "metal_surrogate", "reposition_polydentates", "oxo_antifusion_floors",
]);
const DEFAULT_BUILD_OPTIONS = Object.fromEntries(
  BUILD_OPTION_GROUPS.flatMap((g) => g.items).map(([k]) => [k, !OFF_BY_DEFAULT.has(k)])
);

function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem("mecobi-theme") || "light");
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("mecobi-theme", theme);
  }, [theme]);
  return [theme, () => setTheme((t) => (t === "dark" ? "light" : "dark"))];
}

// Chemical identity of a complex, for dedup on parse: metal, oxidation state, and its
// ligand set (SMILES, order-independent). Same signature = the same structure.
function complexSig(cx) {
  const ligs = (cx.ligands || cx.sel?.ligands || []).map((l) => l.smiles);
  return `${cx.metal}|${cx.oxidation_state}|${ligs.slice().sort().join("~")}`;
}

// "2026-10-02" -> "2 Oct 2026" (parsed by hand: new Date("2026-10-02") is UTC midnight and
// can show the previous day west of Greenwich).
function formatUpdated(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  const mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][m - 1];
  return mon ? `${d} ${mon} ${y}` : iso;
}

// Format an elapsed build time: "45s", "3m 12s".
function fmtDuration(s) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return m ? `${m}m ${String(sec).padStart(2, "0")}s` : `${sec}s`;
}

// Upload-CSV guard. The <input accept> is only a file-picker hint ("All files" bypasses
// it), so the file is checked again here before it is read. The size cap mirrors the
// server's MAX_CSV_BYTES default (web/app.py), which still enforces it on /api/parse.
const CSV_MAX_BYTES = 4_000_000;
// Windows reports .csv as application/vnd.ms-excel when Excel is installed; some
// browsers/OSes report no type at all. Anything else (image, pdf, zip, ...) is refused.
const CSV_OK_MIME = new Set(["", "text/csv", "text/plain", "application/csv", "application/vnd.ms-excel"]);

// Return an error message for a file that is not an acceptable CSV upload, else "".
function csvUploadError(file) {
  if (!/\.csv$/i.test(file.name)) return "Please upload a .csv file.";
  if (!CSV_OK_MIME.has(file.type)) return `That doesn't look like a CSV file (type: ${file.type}).`;
  if (file.size > CSV_MAX_BYTES) return `File too large (max ${CSV_MAX_BYTES / 1e6} MB).`;
  return "";
}

function toSel(cx) {
  return {
    geometry: cx.proposed_geometry,
    allIsomers: false,
    stereo: true,
    donorsCorrect: true,
    ligands: cx.ligands.map((l) => ({
      smiles: l.smiles,
      coord_atoms: l.coord_atoms,
      is_arene: l.is_arene,
    })),
  };
}

// Effective denticity: an η-arene/Cp cap coordinates through 3 sites regardless
// of how many ring atoms are selected (matches backend ARENE_DENTICITY).
const ligDenticity = (l) => (l.is_arene ? 3 : (l.coord_atoms?.length || 0));

// Mirror of geometry.detect_metallocene so the geometry option appears live when
// donor edits turn a complex into a two-cap sandwich (it isn't in the CN map).
function metalloceneGeometry(ligands) {
  const caps = ligands.filter((l) => l.is_arene);
  if (caps.length !== 2 || !caps.every((l) => ligDenticity(l) === 3)) return null;
  const others = ligands.filter((l) => !l.is_arene);
  if (others.length === 0) return "metallocene";
  if (others.every((l) => ligDenticity(l) === 1)) return "metallocene_bent";
  return null;
}

function reqFromRow(cx, relax, spin, xtbTimeout) {
  return {
    name: cx.name,
    metal: cx.metal,
    oxidation_state: cx.oxidation_state,
    ligands: cx.sel.ligands,
    geometry: cx.sel.geometry,
    all_isomers: cx.sel.allIsomers,
    stereo: cx.sel.stereo,
    // A custom isomer set in the 3D Assign scene is remembered on the row, so both a
    // single Build and Build all reuse it (the backend builds that exact isomer).
    site_assignment: cx.sel.siteAssignment || null,
    relax,
    spin,
    xtb_timeout_s: xtbTimeout,
  };
}

export default function App() {
  const [theme, toggleTheme] = useTheme();
  const [csv, setCsv] = useState("");
  const [rows, setRows] = useState([]);
  const [relax, setRelax] = useState(true);
  const [spin, setSpin] = useState("low");
  const [maxOptTime, setMaxOptTime] = useState(300); // xtb per-structure timeout (s)
  const [advOptions, setAdvOptions] = useState({ ...DEFAULT_BUILD_OPTIONS });
  const [parseMsg, setParseMsg] = useState("");
  const [parseErr, setParseErr] = useState("");
  // Snapshot of the rows cleared by "Remove all" (every edit, toggle and custom isomer),
  // kept so the status line can offer Undo until the next parse (audit H15).
  const [removedRows, setRemovedRows] = useState(null);
  const [parsing, setParsing] = useState(false);
  const [buildingIndex, setBuildingIndex] = useState(null);
  const [building, setBuilding] = useState(false); // any synchronous build in flight
  // Build timer: ref holds the start timestamp (read by the async pollJob without a stale
  // closure); `timing` drives the live 1s re-render; `buildDuration` is the final seconds.
  const buildStartRef = useRef(null);
  const [timing, setTiming] = useState(false);
  const [buildDuration, setBuildDuration] = useState(null);
  const [, forceTick] = useState(0);
  // A queued/running job is in flight: guards against mashing Build (which would submit
  // several concurrent jobs) and drives the Cancel button. `activeJobRef` is the id of the
  // poll loop allowed to update the UI — superseding it (new job / cancel) stops stale loops.
  const [jobRunning, setJobRunning] = useState(false);
  const [jobProgress, setJobProgress] = useState(null); // 0..1 while running; null when idle
  const [currentJobId, setCurrentJobId] = useState(null);
  const activeJobRef = useRef(null);
  const uploadRef = useRef(null); // hidden <input type=file> behind the Upload CSV button
  const [jobStatus, setJobStatus] = useState("");
  // Screen-reader announcements: two visually hidden live regions that are always mounted
  // (a region created together with its text is not announced). Job milestones only, never
  // the per-poll progress ticks.
  const [announcement, setAnnouncement] = useState("");
  const [alertText, setAlertText] = useState("");
  function announce(text, urgent = false) {
    // Same text twice in a row: add a trailing NBSP so it is still a change and is re-read.
    (urgent ? setAlertText : setAnnouncement)((prev) => (prev === text ? text + " " : text));
  }
  const [files, setFiles] = useState([]);
  const [viewTokens, setViewTokens] = useState([]); // structures shown in the 3D grid
  const [sceneRow, setSceneRow] = useState(null);
  const [geoMap, setGeoMap] = useState(null); // CN -> [geometry, ...]
  const [version, setVersion] = useState(null); // running build (footer badge)
  const [libOpen, setLibOpen] = useState(false); // ligand-library reel open
  const csvRef = useRef(null);
  const [tourOpen, setTourOpen] = useState(false);
  const [showTourHint, setShowTourHint] = useState(false);

  // Insert a ligand's SMILES (followed by ", ") at the caret in the input box, so you
  // can click ligand after ligand to build up a complex. Restores focus + caret after.
  function insertSmiles(smiles) {
    const chunk = `${smiles}, `;
    const el = csvRef.current;
    if (!el) {
      setCsv((c) => c + chunk);
      return;
    }
    const start = el.selectionStart ?? csv.length;
    const end = el.selectionEnd ?? csv.length;
    const next = csv.slice(0, start) + chunk + csv.slice(end);
    setCsv(next);
    requestAnimationFrame(() => {
      el.focus();
      const pos = start + chunk.length;
      el.setSelectionRange(pos, pos);
    });
  }

  // Briefly nudge toward the Tour button (no auto-opening modal), then let it fade.
  // Shown every visit until the user has opened the tour at least once.
  useEffect(() => {
    if (localStorage.getItem("mecobi-tour-opened")) return undefined;
    setShowTourHint(true);
    const t = setTimeout(() => setShowTourHint(false), 7000);
    return () => clearTimeout(t);
  }, []);
  const openTour = () => {
    setShowTourHint(false);
    localStorage.setItem("mecobi-tour-opened", "1");
    setTourOpen(true);
  };
  // The tour's Parse step calls this to load one example — but never clobber the
  // user's own input if they've already typed something.
  const loadTourSample = () => setCsv((c) => (c.trim() ? c : TOUR_SAMPLE));

  // Dark theme uses a purpose-made FreiLab SVG (adapted colours), not a filter
  // invert of the light PNG.
  const freilabSrc = theme === "dark" ? freilabLogoDark : freilabLogo;

  // Once the header scrolls out of view, reveal a small logo pinned in the
  // left gutter (wide screens only — see .floating-logo). IntersectionObserver
  // avoids a per-scroll listener.
  const headerRef = useRef(null);
  const [logoPinned, setLogoPinned] = useState(false);
  useEffect(() => {
    const el = headerRef.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => setLogoPinned(!entry.isIntersecting),
      { threshold: 0 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    api.version().then(setVersion).catch(() => {});
  }, []);

  useEffect(() => {
    api.geometries().then(setGeoMap).catch(() => {});
  }, []);

  async function doParse(text = csv) {
    if (!text.trim()) {
      setParseMsg("Paste a CSV first (or load the sample).");
      return;
    }
    setParsing(true);
    setParseMsg("");
    setParseErr("");
    setRemovedRows(null); // a new parse ends the Undo offer
    try {
      const data = await api.parse(text);
      // Append only what's NEW: re-parsing edited input adds to the list (build a batch up
      // complex-by-complex), but a complex already in the list is silently skipped — dedup by
      // chemical identity (metal, oxidation state, ligand set), also within this paste.
      const seen = new Set(rows.map(complexSig));
      const fresh = [];
      for (const cx of data) {
        const s = complexSig(cx);
        if (seen.has(s)) continue;
        seen.add(s);
        fresh.push(cx);
      }
      setRows((prev) => [...prev, ...fresh.map((cx) => ({ ...cx, sel: toSel(cx) }))]);
      if (fresh.length && !jobRunning && !building) {
        // Adding new complexes starts a fresh batch: clear the previous run's results and
        // its "Done — N structures" status so the panel reflects only what you build next.
        setFiles([]);
        setViewTokens([]);
        setJobStatus("");
        setJobProgress(null);
        setBuildDuration(null);
        setCurrentJobId(null);
        activeJobRef.current = null;
        if (window.location.hash.startsWith("#job=")) {
          history.replaceState(null, "", window.location.pathname + window.location.search);
        }
      }
      const skipped = data.length - fresh.length;
      setParseMsg(
        fresh.length
          ? `${fresh.length} complex${fresh.length === 1 ? "" : "es"} added` +
            `${skipped ? ` (${skipped} already in the list)` : ""}.`
          : "Already in the list — nothing new to add."
      );
    } catch (e) {
      setParseMsg("");
      setParseErr(e.message); // keep any already-parsed rows on a bad re-parse
    } finally {
      setParsing(false);
    }
  }

  function onRowChange(i, patch) {
    // Changing the geometry invalidates a stored 3D-scene isomer (its site ids belong
    // to the old geometry), so drop the custom-isomer flag unless the patch itself
    // sets one.
    const p =
      patch.geometry !== undefined && patch.siteAssignment === undefined
        ? { ...patch, siteAssignment: null }
        : patch;
    setRows((rs) => rs.map((r, idx) => (idx === i ? { ...r, sel: { ...r.sel, ...p } } : r)));
  }

  // Recompute a row after its donor selection changed: donor edits change
  // denticities, hence CN, hence which geometries are legal.
  // Same wording as the core's geometry.geometries_for_cn error.
  function unsupportedCnError(cn) {
    const cns = geoMap ? Object.keys(geoMap).map(Number).sort((a, b) => a - b) : [];
    return `No supported geometry for coordination number ${cn}` +
      (cns.length ? ` (supported: ${cns[0]} to ${cns[cns.length - 1]}).` : ".");
  }

  function recomputeRow(r, ligands) {
    const cn = ligands.reduce((n, l) => n + ligDenticity(l), 0);
    const metallo = metalloceneGeometry(ligands);
    const cnOptions = (geoMap && geoMap[cn]) || [];
    const options = metallo ? [metallo, ...cnOptions] : cnOptions;
    return {
      ...r,
      coordination_number: cn,
      geometry_options: options,
      supported: options.length > 0,
      error: options.length
        ? null
        : unsupportedCnError(cn),
      ligands: r.ligands.map((l, k) => ({
        ...l,
        denticity: ligDenticity(ligands[k]),
        coord_atoms: ligands[k].coord_atoms,
        is_arene: ligands[k].is_arene,
      })),
      sel: {
        ...r.sel,
        ligands,
        geometry: options.includes(r.sel.geometry) ? r.sel.geometry : options[0],
        // Donor edits change denticities/sites, so any stored 3D-scene isomer is stale.
        siteAssignment: null,
      },
    };
  }

  // A selected carbocyclic ring is one centroid η-cap (denticity 1) — which the
  // frontend can't compute locally (needs ring perception) — so re-perceive on the
  // backend for the cap-aware CN, denticities and geometry options. Falls back to
  // the local estimate if the request fails (offline / older backend).
  async function onDonorsChange(i, ligands) {
    const row = rows[i];
    let p = null;
    try {
      p = await api.perceive({
        metal: row.metal,
        oxidation_state: row.oxidation_state,
        ligands: ligands.map((l) => ({
          smiles: l.smiles, coord_atoms: l.coord_atoms, is_arene: l.is_arene,
        })),
      });
    } catch {
      /* fall through to the local estimate */
    }
    setRows((rs) =>
      rs.map((r, idx) => {
        if (idx !== i) return r;
        if (!p) return recomputeRow(r, ligands);
        const options = p.geometry_options || [];
        return {
          ...r,
          coordination_number: p.coordination_number,
          geometry_options: options,
          // Clears once the rings are set as centroid caps (backend recomputes it).
          needs_cap_selection: !!p.needs_cap_selection,
          supported: options.length > 0,
          error: options.length
            ? null
            : p.error || unsupportedCnError(p.coordination_number),
          ligands: r.ligands.map((l, k) => ({
            ...l,
            denticity: p.ligands?.[k]?.denticity ?? ligDenticity(ligands[k]),
            coord_atoms: ligands[k].coord_atoms,
            is_arene: ligands[k].is_arene,
            // Centroid-cap structure from the backend (a selected ring = one site);
            // the Assign scene reads this to place caps without a cis constraint.
            pi_sites: p.ligands?.[k]?.pi_sites ?? l.pi_sites ?? [],
          })),
          sel: {
            ...r.sel,
            ligands,
            geometry: options.includes(r.sel.geometry)
              ? r.sel.geometry
              : p.proposed_geometry || options[0],
          },
        };
      })
    );
  }

  // Bulk donor assignment (S): apply the donor atoms chosen for one ligand SMILES
  // to every row that contains the same ligand — for a long list of complexes
  // sharing similar ligands, set the coordinating atoms once.
  function onApplyDonorsToAll(smiles, atoms) {
    setRows((rs) =>
      rs.map((r) => {
        if (!r.sel.ligands.some((l) => l.smiles === smiles)) return r;
        const ligands = r.sel.ligands.map((l) =>
          l.smiles === smiles ? { ...l, coord_atoms: atoms } : l
        );
        return recomputeRow(r, ligands);
      })
    );
  }

  // Show build results. `append` accumulates across per-row builds (rebuilding a
  // complex replaces just its own entries) instead of wiping the panel each time;
  // a batch "Build all" passes append=false to show the whole set.
  function showResults(newFiles, append = false) {
    setFiles((prev) => {
      const merged = append
        ? [...prev.filter((f) => !newFiles.some((n) => n.complex && n.complex === f.complex)), ...newFiles]
        : newFiles;
      // Render every result (each isomer in its own 3D pane), up to the grid cap.
      setViewTokens(merged.slice(0, MAX_RENDER).map((f) => f.token));
      return merged;
    });
  }

  // Remove a built structure from the results list (Q).
  function onRemoveFile(token) {
    setFiles((fs) => fs.filter((f) => f.token !== token));
    setViewTokens((ts) => ts.filter((t) => t !== token));
  }

  // Clear the whole results list at once (files stay on disk under the 24h TTL).
  function onRemoveAll() {
    setFiles([]);
    setViewTokens([]);
  }

  // Remove one complex from the input list (row × button).
  function onRemoveRow(i) {
    setRows((rs) => rs.filter((_, idx) => idx !== i));
  }

  // Clear the whole input list (header "Remove all"); the CSV box is kept for a re-parse.
  // No confirm: it removes at once and offers Undo, which restores the rows exactly.
  function onRemoveAllRows() {
    const n = rows.length;
    if (!n) return;
    setRemovedRows(rows);
    setRows([]);
    setSceneRow(null); // don't leave a scene open for a row that's gone (or comes back)
    setParseErr("");
    setParseMsg(`${n} complex${n === 1 ? "" : "es"} removed.`);
  }

  function undoRemoveAll() {
    if (!removedRows) return;
    const n = removedRows.length;
    setRows(removedRows);
    setRemovedRows(null);
    setParseMsg(`${n} complex${n === 1 ? "" : "es"} restored.`);
  }

  // Build timer. Start on build submit; finish when the job/build ends. The ref is the
  // source of truth (pollJob reads it); `timing` just drives the live clock.
  function startBuildTimer() {
    buildStartRef.current = Date.now();
    setBuildDuration(null);
    setTiming(true);
  }
  function finishBuildTimer() {
    if (buildStartRef.current == null) return; // e.g. a job resumed from a link
    setBuildDuration(Math.round((Date.now() - buildStartRef.current) / 1000));
    buildStartRef.current = null;
    setTiming(false);
  }

  // Live 1s re-render while a build is timing (so the elapsed clock advances).
  useEffect(() => {
    if (!timing) return undefined;
    const t = setInterval(() => forceTick((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, [timing]);

  // Text for the small timer chip: live elapsed while building, else the final time.
  const timerText = timing
    ? <><Icon name="timer" size={13} />{fmtDuration(Math.round((Date.now() - (buildStartRef.current || Date.now())) / 1000))}</>
    : buildDuration != null
      ? <><Icon name="timer" size={13} />built in {fmtDuration(buildDuration)}</>
      : null;

  // Load a CSV file from disk into the paste box, then parse it immediately.
  function onUploadCsv(file) {
    if (!file) return;
    const err = csvUploadError(file);
    if (err) {
      setParseErr(err);
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result);
      // NUL or undecodable bytes => a binary file renamed to .csv; never paste it in.
      if (/\u0000|�/.test(text)) {
        setParseErr("That file isn't plain text. Please upload a CSV.");
        return;
      }
      setCsv(text);
      doParse(text); // parse the file text directly (not the not-yet-updated state)
    };
    reader.onerror = () => setParseErr("Could not read that file.");
    reader.readAsText(file);
  }

  async function onBuild(i) {
    // A relaxed build is xtb-bound and can run for many minutes. Held open on the
    // SYNCHRONOUS route it outlives the reverse proxy in front of us (Apache's default
    // Timeout/ProxyTimeout is 60 s), so the user gets a 502 while the build runs on
    // regardless -- holding the build slot and 503-ing everyone else until it ends.
    // Queue it instead: identical work, but polled, resumable from the job link and
    // with a progress bar. Assembly-only stays synchronous; it returns in seconds and
    // the immediate result is the point.
    if (relax) {
      if (jobRunning || building) return; // guard: one job at a time (no mashing)
      try {
        setJobRunning(true);
        startBuildTimer();
        const job = await api.submitJob(
          [reqFromRow(rows[i], relax, spin, maxOptTime)], relax, maxOptTime, advOptions);
        activeJobRef.current = job.job_id;
        setCurrentJobId(job.job_id); // enables Cancel immediately, before the first poll
        window.location.hash = "job=" + job.job_id;
        announce(`Build started: ${rows[i].name}.`);
        pollJob(job.job_id, job.estimate_s, 0, true); // append: keep other rows' results
      } catch (e) {
        finishBuildTimer();
        setJobRunning(false);
        setJobStatus(<span className="pill-err">{e.message}</span>);
        announce(e.message, true);
      }
      return;
    }
    if (jobRunning || building) return;
    setBuildingIndex(i);
    setBuilding(true);
    startBuildTimer();
    announce(`Building ${rows[i].name}…`);
    try {
      // Send the advanced options here too: the pre-xtb placement guards change the
      // ASSEMBLED geometry, so they apply to an assembly-only build as much as a relaxed one.
      const data = await api.build(reqFromRow(rows[i], relax, spin, maxOptTime), advOptions);
      showResults(data.results, true); // accumulate per-row builds
      const n = data.results.length;
      announce(`${rows[i].name} built: ${n} structure${n === 1 ? "" : "s"}.`);
    } catch (e) {
      setJobStatus(<span className="pill-err">{e.message}</span>);
      announce(e.message, true);
    } finally {
      finishBuildTimer();
      setBuildingIndex(null);
      setBuilding(false);
    }
  }

  // "Save this isomer" just remembers the 3D-scene placement on the row (shows the
  // custom-isomer flag; Build and Build all reuse it via reqFromRow) and closes the
  // scene. It deliberately does NOT build here — building on save disrupted the flow.
  // The user builds via the row's Build button or Build all.
  function onSaveIsomer(rowIndex, siteAssignment) {
    onRowChange(rowIndex, { siteAssignment });
    setSceneRow(null);
  }

  async function onBuildAll() {
    if (jobRunning || building) return; // guard: one job at a time (no mashing)
    // Skip metallocenes/sandwiches whose rings aren't set as centroid caps: a batch
    // uses auto-perception (which can't cap), so these would fail or mis-build. The
    // user should select the ring(s) as η-caps and build those rows individually.
    const buildable = rows.filter((r) => r.supported && !r.needs_cap_selection);
    const skipped = rows.filter((r) => r.needs_cap_selection).length;
    const complexes = buildable.map((r) => reqFromRow(r, relax, spin, maxOptTime));
    if (!complexes.length) {
      const msg = skipped
        ? `No buildable complexes — ${skipped} need their Cp/arene ring(s) selected as η-caps first (untick Donors).`
        : "None of these rows can be built. Fix the rows marked in red, then build again.";
      setJobStatus(<span className="pill-err">{msg}</span>);
      announce(msg, true);
      return;
    }
    try {
      setJobRunning(true);
      startBuildTimer();
      const job = await api.submitJob(complexes, relax, maxOptTime, advOptions);
      activeJobRef.current = job.job_id;
      setCurrentJobId(job.job_id); // enables Cancel immediately, before the first poll
      window.location.hash = "job=" + job.job_id;
      const n = complexes.length;
      announce(`Build started: ${n} complex${n === 1 ? "" : "es"}.` +
        (skipped ? ` ${skipped} skipped (need η-cap selection).` : ""));
      pollJob(job.job_id, job.estimate_s, skipped);
    } catch (e) {
      finishBuildTimer();
      setJobRunning(false);
      setJobStatus(<span className="pill-err">{e.message}</span>);
      announce(e.message, true);
    }
  }

  // `append` keeps results already on screen (a single queued row must not wipe the
  // grid the way a whole-table Build all does); showResults dedupes by complex name,
  // so re-showing the same job's growing result set each tick stays idempotent.
  async function pollJob(id, estimate, skipped = 0, append = false) {
    // This is now the active job; supersedes any earlier poll loop. jobRunning/currentJobId
    // are set only once a tick confirms a non-terminal status (below), so resuming an already
    // finished job from its link doesn't flash a live "running" UI with an armed Cancel.
    activeJobRef.current = id;
    const tick = async () => {
      if (activeJobRef.current !== id) return; // superseded or cancelled — stop polling
      let j;
      try {
        j = await api.getJob(id);
      } catch {
        // Transient network/server hiccup — keep polling instead of freezing.
        if (activeJobRef.current === id) setTimeout(tick, 1500);
        return;
      }
      if (activeJobRef.current !== id) return; // cancelled while the request was in flight
      if (j.detail) {
        // Unknown/expired job: drop its #job= link too, or every reload repeats the error.
        setJobRunning(false); setJobProgress(null);
        if (window.location.hash === `#job=${id}`) {
          history.replaceState(null, "", window.location.pathname + window.location.search);
        }
        announce(j.detail, true);
        return setJobStatus(<span className="pill-err">{j.detail}</span>);
      }
      if (j.status === "done") {
        finishBuildTimer();
        setJobRunning(false);
        setJobProgress(null);
        activeJobRef.current = null;
        const errs = j.complex_errors || [];
        // Surface WHY each one failed (was console-only) — e.g. an un-capped
        // multi-Cp ligand perceives every ring carbon as a donor -> CN too high.
        setJobStatus(
          <div className="job-bar">
            <div className="job-line">
              <span className="job-title">Done — {j.results.length} structure{j.results.length === 1 ? "" : "s"}</span>
              {errs.length > 0 && <span className="pill-err">{errs.length} failed</span>}
              {skipped > 0 && <span className="pill-warn">{skipped} skipped (need η-cap selection)</span>}
            </div>
            {errs.length > 0 && (
              <ul className="job-errs">
                {errs.map((e, i) => (
                  <li key={i}><span className="mono">{e.complex || e.name || "complex"}</span>: {e.error || "failed"}</li>
                ))}
              </ul>
            )}
          </div>
        );
        showResults(j.results, append);
        const n = j.results.length;
        announce(`Build finished: ${n} structure${n === 1 ? "" : "s"}` +
          (errs.length ? `, ${errs.length} failed` : "") +
          (skipped ? `, ${skipped} skipped` : "") + ".");
        if (errs.length) console.warn("Build-all per-complex errors:", errs);
        return;
      }
      if (j.status === "failed") {
        finishBuildTimer();
        setJobRunning(false);
        setJobProgress(null);
        activeJobRef.current = null;
        if (j.results && j.results.length) showResults(j.results, append);
        announce(`Build stopped: ${j.error}`, true);
        return setJobStatus(<span className="pill-err">Build stopped: {j.error}</span>);
      }
      // Progressive display: the job publishes results as each complex finishes, so show them
      // as they arrive instead of waiting for the whole batch (append=false: j.results is the
      // full accumulated set each tick, so this grows the grid).
      if (j.results && j.results.length) showResults(j.results, append);
      const estimatedSeconds = j.estimate_s || estimate || 0;
      const estMin = estimatedSeconds ? Math.ceil(estimatedSeconds / 60) : 0;
      const longJob = estimatedSeconds >= 600;
      const pct = Math.round((j.progress || 0) * 100);
      const readyN = j.results ? j.results.length : 0;
      const meta = [
        `${pct}%`,
        estMin ? `~${estMin} min` : "",
        readyN ? `${readyN} ready` : "",
        skipped ? `${skipped} skipped` : "",
      ].filter(Boolean).join(" · ");
      // Confirmed non-terminal: now it's safe to show the running UI + enable Cancel.
      setJobRunning(true);
      setCurrentJobId(id);
      setJobProgress(j.progress || 0); // drives the full-width bar rendered by ComplexTable
      setJobStatus(
        <div className="job-bar">
          <div className="job-line">
            <span className="spinner" />
            <span className="job-title">{j.stage || "Building…"}</span>
            <span className="job-meta">{meta}</span>
          </div>
          <div className="job-sub muted">
            <a href={`#job=${id}`}>Keep this link</a> to return to your results
            {longJob ? " — long job: safe to close the page, just don't resubmit" : ""}.
          </div>
        </div>
      );
      setTimeout(tick, 1500);
    };
    tick();
  }

  // Cancel the in-flight job: a queued job never starts; a running one stops at the next
  // complex boundary (its in-progress structure finishes — xtb isn't killed mid-run).
  async function onCancelJob() {
    const id = currentJobId || activeJobRef.current;
    if (!id) return;
    activeJobRef.current = null; // stop this job's poll loop immediately
    setJobStatus(<><span className="spinner" /> Cancelling…</>);
    try {
      await api.cancelJob(id);
    } catch {
      /* best-effort; UI still returns to idle below */
    }
    finishBuildTimer();
    setJobRunning(false);
    setJobProgress(null);
    setCurrentJobId(null);
    setJobStatus(<span className="pill-warn">Build cancelled. Any completed structures are shown below.</span>);
    announce("Build cancelled. Any completed structures are shown below.");
    if (window.location.hash.startsWith("#job=")) {
      history.replaceState(null, "", window.location.pathname + window.location.search);
    }
  }

  // Clear the job banner AND the #job= hash, so a completed job doesn't re-appear
  // on every reload (the hash is what resumes it — see the effect below).
  function dismissJob() {
    setJobStatus("");
    activeJobRef.current = null;
    setJobRunning(false);
    setJobProgress(null);
    setCurrentJobId(null);
    if (window.location.hash.startsWith("#job=")) {
      history.replaceState(null, "", window.location.pathname + window.location.search);
    }
  }

  // Resume a job from the URL hash ("submit & come back").
  useEffect(() => {
    const m = window.location.hash.match(/job=([a-f0-9]+)/);
    if (m) pollJob(m[1]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <img
        className={`floating-logo${logoPinned && sceneRow == null ? " show" : ""}`}
        src={mecobiLogo}
        alt=""
        aria-hidden="true"
      />
      <header ref={headerRef}>
        <div className="brand-row">
          <img className="app-logo" src={mecobiLogo} alt="MeCoBi logo" />
          <div className="brand">
            <div className="wordmark" aria-label="MeCoBi">
              <span className="cap">M</span>e<span className="cap">C</span>o<span className="cap">B</span>i
            </div>
            <div className="tagline">
              <span className="cap">M</span>etal <span className="cap">C</span>omplex{" "}
              <span className="cap">B</span>uilder
            </div>
          </div>
        </div>
        <div className="header-right">
          <a href="https://thefreilab.com" target="_blank" rel="noreferrer" title="TheFreiLab">
            <img className="freilab-logo" src={freilabSrc} alt="TheFreiLab" />
          </a>
          <div className="tour-btn-wrap">
            <button
              className={"toggle-btn" + (showTourHint ? " nudge" : "")}
              onClick={openTour}
              title="Take a guided tour of the interface"
            >
              Tour
            </button>
            {showTourHint && (
              <div className="tour-hint" role="status">
                <span className="tour-hint-icon" aria-hidden="true">🧭</span>
                <div className="tour-hint-text">
                  <strong>New here?</strong>
                  <span>Take a quick guided tour.</span>
                </div>
                <button className="tour-hint-x" aria-label="Dismiss" onClick={() => setShowTourHint(false)}>
                  ×
                </button>
              </div>
            )}
          </div>
          <button className="toggle-btn" onClick={toggleTheme}>
            {theme === "dark" ? "Light" : "Dark"}
          </button>
        </div>
      </header>

      <GuidedTour
        open={tourOpen}
        steps={TOUR_STEPS}
        actions={{ loadSample: loadTourSample }}
        onClose={() => setTourOpen(false)}
      />

      <main className={sceneRow != null ? "with-scene" : ""}>
        <div className="sr-only" role="status">{announcement}</div>
        <div className="sr-only" role="alert">{alertText}</div>
        <p className="intro">
          <strong>MeCoBi</strong> turns a metal, its oxidation state, and the SMILES of its ligands
          into optimised 3D structures. It assembles the coordination geometry, enumerates isomers,
          and optionally relaxes each with GFN2-xtb, quickly and at high throughput. Enter your
          complexes below, or load the sample to see the format.
        </p>
        <WorkloadNotice />
        <div className={"input-row" + (libOpen ? " with-library" : "")}>
        <div className="card" data-tour="input-card">
          <h2>Input</h2>
          <label htmlFor="csv">
            One complex per line. A header row and the named-slot form (Name, Metal,
            Charge, L1…L6) both work — or click <strong>Load sample</strong>.
          </label>
          <div className="csv-hint mono" aria-hidden="true">
            metal, oxidation_state, SMILES 1, SMILES 2, …
          </div>
          <textarea ref={csvRef} id="csv" className="csv-input" spellCheck={false} value={csv} onChange={(e) => setCsv(e.target.value)} />
          <div className="row" style={{ marginTop: 12 }}>
            <button className="primary" data-tour="parse-btn" onClick={() => doParse()} disabled={parsing}>
              <BusyLabel busy={parsing} label="Parse" busyLabel="Parsing…" compact />
            </button>
            {/* A real button (Tab + Enter work) that opens the hidden file input. */}
            <button type="button" className="ghost" title="Upload a .csv file in the same format"
              onClick={() => uploadRef.current?.click()}>
              Upload CSV
            </button>
            <input
              ref={uploadRef}
              type="file"
              accept=".csv,text/csv,application/vnd.ms-excel"
              style={{ display: "none" }}
              tabIndex={-1}
              aria-hidden="true"
              onChange={(e) => {
                onUploadCsv(e.target.files?.[0]);
                e.target.value = ""; // allow re-uploading the same file
              }}
            />
            <button className="ghost" data-tour="sample-btn" onClick={() => setCsv(SAMPLE)}>
              Load sample
            </button>
            <button
              className={"ghost" + (libOpen ? " active" : "")}
              data-tour="ligand-library-btn"
              title="Browse common ligands and click to insert their SMILES"
              onClick={() => setLibOpen((v) => !v)}
            >
              <Icon name="flask" />Ligand library
            </button>
            <span style={{ marginLeft: "auto" }}>
              <WebLimitNote />
            </span>
          </div>
          {parsing ? (
            <div className="progress indeterminate" style={{ marginTop: 10 }} title="Parsing…"
              role="progressbar" aria-label="Parsing">
              <div className="progress-fill" />
            </div>
          ) : null}
          {/* Always mounted (empty when idle) so screen readers announce changes. */}
          <div className="muted status-line" role="status">
            {parseMsg}
            {removedRows ? (
              <button type="button" className="ghost undo-btn" onClick={undoRemoveAll}>Undo</button>
            ) : null}
          </div>
          <div className="status-line" role="alert">
            {parseErr ? <span className="pill-err">{parseErr}</span> : null}
          </div>
        </div>
        {libOpen && <LigandLibrary onInsert={insertSmiles} onClose={() => setLibOpen(false)} />}
        </div>

        {rows.length === 0 && jobStatus && <div>{jobStatus}</div>}
        {rows.length > 0 && (
          <div className="hub-row">
            <ComplexTable
              rows={rows}
              onRowChange={onRowChange}
              onDonorsChange={onDonorsChange}
              onApplyDonorsToAll={onApplyDonorsToAll}
              onBuild={onBuild}
              onRemoveRow={onRemoveRow}
              onRemoveAllRows={onRemoveAllRows}
              onAssign={setSceneRow}
              buildingIndex={buildingIndex}
              building={building}
              onBuildAll={onBuildAll}
              jobStatus={jobStatus}
              timerText={timerText}
              jobRunning={jobRunning}
              jobProgress={jobProgress}
              canCancel={jobRunning && !!currentJobId}
              onCancelJob={onCancelJob}
              onDismissJob={dismissJob}
              relax={relax}
              setRelax={setRelax}
              spin={spin}
              setSpin={setSpin}
              maxOptTime={maxOptTime}
              setMaxOptTime={setMaxOptTime}
              advOptions={advOptions}
              setAdvOptions={setAdvOptions}
              optionGroups={BUILD_OPTION_GROUPS}
              advDefaults={DEFAULT_BUILD_OPTIONS}
            />
            {sceneRow != null && rows[sceneRow] && (
              <IsomerScene
                key={`${sceneRow}:${rows[sceneRow].sel.geometry}`}
                complex={rows[sceneRow]}
                geometry={rows[sceneRow].sel.geometry}
                onClose={() => setSceneRow(null)}
                onBuild={(assignment) => onSaveIsomer(sceneRow, assignment)}
              />
            )}
          </div>
        )}

        <Results
          files={files}
          viewTokens={viewTokens}
          onViewTokens={setViewTokens}
          onRemove={onRemoveFile}
          onRemoveAll={onRemoveAll}
        />
      </main>
      {/* Quiet via the muted text token, not opacity: opacity faded the Disclaimer link to
          ~2.3:1 contrast (audit H11); --text-muted passes AA in both themes. */}
      <footer
        className="mono muted"
        style={{ textAlign: "center", padding: "18px 0 26px", fontSize: "var(--text-caption)" }}
      >
        {/* Public usage counter; re-reads the total whenever new results arrive. */}
        <FlipCounter refreshKey={files.length} />
        {/* Legal disclaimer link is always rendered (not gated behind the version
            fetch) — a public deployment must surface it even if /api/version fails. */}
        <a
          href="https://www.york.ac.uk/about/legal-statements/"
          target="_blank"
          rel="noreferrer"
        >
          Disclaimer
        </a>
        {version
          ? ` · MeCoBi v${version.version}` +
            (version.branch ? ` · ${version.branch}` : "") +
            (version.commit ? ` @ ${version.commit}` : "") +
            (version.updated ? ` · last updated ${formatUpdated(version.updated)}` : "")
          : ""}
      </footer>
    </>
  );
}
