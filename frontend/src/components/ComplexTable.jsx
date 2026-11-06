import { Fragment, useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import BusyLabel from "./BusyLabel.jsx";
import DonorPanel from "./DonorPanel.jsx";

// The Isomers cell. It enumerates this row's isomers live (via /api/isomers) so
// it can (a) hint which isomers "all" will build, e.g. "cis/trans (2)", and
// (b) offer the Δ/Λ split ONLY when this specific complex actually has enantiomers
// -- not merely when the geometry could (an octahedral M(L)2X4 is octahedral but
// achiral, so no Δ/Λ). Re-fetched as geometry / donors / stereo change.
function IsomerCell({ cx, sel, index, onRowChange, children }) {
  const [opts, setOpts] = useState({ summary: null, stereoSplits: false });
  const cellRef = useRef(null);
  const [visible, setVisible] = useState(false);
  const key = JSON.stringify({ ligands: sel.ligands, geometry: sel.geometry, stereo: sel.stereo });

  // Enumerating isomers costs ~0.5s per complex. Firing it for every row on mount
  // stalls a large table (hundreds of rows = minutes of work + a request storm),
  // so defer it until the row is actually scrolled into view.
  useEffect(() => {
    if (visible) return undefined;
    const el = cellRef.current;
    if (!el) return undefined;
    if (typeof IntersectionObserver === "undefined") {
      setVisible(true); // no observer support -> keep the eager behaviour
      return undefined;
    }
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setVisible(true);
          io.disconnect();
        }
      },
      { rootMargin: "200px" }, // prefetch just before it enters the viewport
    );
    io.observe(el);
    return () => io.disconnect();
  }, [visible]);

  useEffect(() => {
    if (!visible || !cx.supported || !sel.geometry) {
      setOpts({ summary: null, stereoSplits: false });
      return undefined;
    }
    let cancelled = false;
    api
      .isomers({
        metal: cx.metal, oxidation_state: cx.oxidation_state,
        ligands: sel.ligands, geometry: sel.geometry, stereo: sel.stereo,
      })
      .then((d) => !cancelled && setOpts({ summary: d.summary || null, stereoSplits: !!d.stereo_splits }))
      .catch(() => !cancelled && setOpts({ summary: null, stereoSplits: false }));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, cx.supported, visible]);

  return (
    <div ref={cellRef} className="isomer-cell">
      {/* [toggles over hint] [Isomer editor] on one line, as tall as the button; the
          "all" checkbox sits on the cell's top line, level with the Donors checkbox. */}
      <div className="iso-row">
      <div className="iso-toggles">
      <div className="iso-checks">
      <label className="switch">
        <input
          type="checkbox"
          checked={sel.allIsomers}
          onChange={(e) => onRowChange(index, { allIsomers: e.target.checked })}
        />
        all
      </label>
      {sel.allIsomers && opts.stereoSplits && (
        <label
          className="switch"
          title="Split Δ/Λ enantiomers and asymmetric-chelate donor directions"
        >
          <input
            type="checkbox"
            checked={sel.stereo}
            onChange={(e) => onRowChange(index, { stereo: e.target.checked })}
          />
          Δ/Λ
        </label>
      )}
      </div>
      {opts.summary && (
        <div className="iso-hint muted" title="Distinct isomers 'all' will build">
          {opts.summary}
        </div>
      )}
      </div>
      {children /* the Isomer editor button */}
      </div>
      {sel.siteAssignment && (
        <span
          className="chip custom-isomer"
          data-tour={index === 0 ? "custom-isomer-flag" : undefined}
          title="A custom isomer was set in the isomer editor. Build and Build all use it."
        >
          ★ custom
          <button
            type="button"
            className="chip-x"
            title="Clear the custom isomer"
            onClick={() => onRowChange(index, { siteAssignment: null })}
          >
            ×
          </button>
        </span>
      )}
    </div>
  );
}

// A half-sandwich / piano-stool complex is built through the OCTAHEDRAL topology
// registry (the η Cp/arene cap fills 3 fac sites), so its geometry value must stay
// "octahedral" for the backend to route it correctly. But when the complex has an
// η cap we label it "piano-stool" for the chemist — display only, value unchanged.
function geometryLabel(value, isPiano) {
  if (value === "octahedral" && isPiano) return "piano-stool";
  return value.replace("_", " ");
}

// The table hub: CN, geometry dropdown, isomer choice, and the
// "coordinating atoms correct?" checkbox that opens the donor panel.
export default function ComplexTable({ rows, onRowChange, onDonorsChange, onApplyDonorsToAll, onBuild, onRemoveRow, onRemoveAllRows, onAssign, buildingIndex, building, onBuildAll, jobStatus, timerText, jobRunning, jobProgress, canCancel, onCancelJob, onDismissJob, relax, setRelax, spin, setSpin, maxOptTime, setMaxOptTime, advOptions, setAdvOptions, optionGroups, advDefaults }) {
  const [advOpen, setAdvOpen] = useState(false);
  const busy = jobRunning || building; // a build/job is in flight — block new submissions
  // Scroll cues: when the table is wider than its box, a fade marks each edge that has
  // more content beyond it (right: just before the pinned Build column; left: once
  // scrolled). Fades use the panel colour, so they work in both themes.
  const scrollRef = useRef(null);
  const [edges, setEdges] = useState({ left: false, right: false });
  useEffect(() => {
    const el = scrollRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const check = () => {
      const left = el.scrollLeft > 1;
      const right = el.scrollLeft + el.clientWidth < el.scrollWidth - 1;
      setEdges((e) => (e.left === left && e.right === right ? e : { left, right }));
    };
    const ro = new ResizeObserver(check);
    ro.observe(el);
    if (el.firstElementChild) ro.observe(el.firstElementChild);
    el.addEventListener("scroll", check, { passive: true });
    check();
    return () => { ro.disconnect(); el.removeEventListener("scroll", check); };
  }, [rows.length]);
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <h2 style={{ margin: 0 }}>Review &amp; build</h2>
        <button
          className="primary"
          data-tour="build-all-btn"
          onClick={onBuildAll}
          disabled={busy}
          title={busy ? "A build is already running — wait for it or cancel it first" : undefined}
        >
          Build all (queue job)
        </button>
      </div>
      {/* Build controls: xtb relaxation row + collapsible advanced options, one unified bar.
          The advanced-options disclosure sits inline at the right of the same row (not a
          separate box) and expands its panel within this container. */}
      <div className="build-controls" data-tour="build-controls">
        <div className="xtb-bar">
          <span className="switch">
            <input type="checkbox" id="relax" checked={relax} onChange={(e) => setRelax(e.target.checked)} />
            <label htmlFor="relax">Relax with xtb (GFN2)</label>
          </span>
          <span className={"xtb-controls" + (relax ? "" : " disabled")}>
            <label htmlFor="spin">Spin</label>
            <select id="spin" value={spin} disabled={!relax} onChange={(e) => setSpin(e.target.value)}>
              <option value="low">low</option>
              <option value="high">high</option>
            </select>
            <label htmlFor="maxopt" title="Max wall-clock time for each structure's xtb optimisation">
              Max opt time
            </label>
            <input
              type="range" id="maxopt" min={30} max={600} step={30}
              value={maxOptTime} disabled={!relax}
              onChange={(e) => setMaxOptTime(Number(e.target.value))}
            />
            <span className="mono" style={{ minWidth: 42 }}>{maxOptTime}s</span>
          </span>
          {optionGroups && (
            <button
              type="button"
              className="adv-toggle"
              aria-expanded={advOpen}
              onClick={() => setAdvOpen((v) => !v)}
            >
              <span className="adv-caret" aria-hidden="true">{advOpen ? "▾" : "▸"}</span>
              Advanced options
              {(() => {
                const changed = advDefaults
                  ? Object.keys(advOptions).filter((k) => advOptions[k] !== advDefaults[k]).length
                  : 0;
                return changed ? <span className="pill-warn" style={{ marginLeft: 6 }}>{changed} changed</span> : null;
              })()}
            </button>
          )}
        </div>
        {optionGroups && advOpen && (
          <div className="adv-body">
            <div className="adv-head">
              <p className="hint">
                Fine-tune how a structure is built — geometry prep before optimisation, and
                xtb constraints during it. The defaults are the standard build; only change
                these to diagnose a specific complex. Options marked <strong>⚑ opt-in</strong>{" "}
                are off by default (escalations for a hard, crowded sphere) and can cost accuracy
                elsewhere, so leave them off unless a build actually needs them.
              </p>
              {advDefaults && (
                <button
                  type="button"
                  className="adv-reset"
                  onClick={() => setAdvOptions({ ...advDefaults })}
                >
                  Reset to defaults
                </button>
              )}
            </div>
            {optionGroups.map((g) => (
              <div key={g.label} className="adv-group">
                <div className="adv-group-label">{g.label}</div>
                <div className="adv-grid">
                  {g.items.map(([key, label, desc]) => {
                    const optIn = advDefaults && advDefaults[key] === false;
                    return (
                      <label key={key} className="adv-item">
                        <input
                          type="checkbox"
                          checked={!!advOptions[key]}
                          onChange={(e) => setAdvOptions({ ...advOptions, [key]: e.target.checked })}
                        />
                        <span className="adv-label">
                          <span className="adv-label-text">{label}</span>
                          {optIn ? (
                            <span className="adv-optin" title="Off by default — an opt-in escalation for hard, crowded spheres">
                              ⚑ opt-in
                            </span>
                          ) : null}
                        </span>
                        <span className="adv-tip" role="tooltip">{desc}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      {/* One status area: the job bar (or a sync "Building…" line), the build timer, and
          the Cancel (while running) / Dismiss (when idle) control — always co-located. */}
      {(jobStatus || jobRunning || building) ? (
        <div style={{ marginBottom: 10 }}>
          <div className="row" style={{ alignItems: "flex-start", gap: 8 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              {jobStatus || (
                <div className="job-line">
                  <span className="spinner" />
                  <span className="job-title">{building ? "Building…" : "Submitting…"}</span>
                </div>
              )}
            </div>
            {timerText ? (
              <span className="build-timer mono" title="Build time">{timerText}</span>
            ) : null}
            {canCancel && onCancelJob ? (
              <button
                className="toggle-btn"
                title="Cancel this job (a queued job stops immediately; a running one stops after the current structure finishes)"
                onClick={onCancelJob}
              >
                Cancel
              </button>
            ) : null}
            {!jobRunning && jobStatus && onDismissJob ? (
              <button className="toggle-btn" title="Dismiss (also clears the #job link)" onClick={onDismissJob}>
                Dismiss
              </button>
            ) : null}
          </div>
          {/* Full-width progress bar spanning under the status text AND the timer/Cancel. */}
          {(building || jobRunning) ? (
            jobProgress > 0 ? (
              <div className="progress" style={{ marginTop: 8 }} title={`${Math.round(jobProgress * 100)}%`}
                role="progressbar" aria-label="Build progress" aria-valuemin={0} aria-valuemax={100}
                aria-valuenow={Math.round(jobProgress * 100)}>
                <div className="progress-fill" style={{ width: `${Math.round(jobProgress * 100)}%` }} />
              </div>
            ) : (
              <div className="progress indeterminate" style={{ marginTop: 8 }}
                role="progressbar" aria-label="Build progress"><div className="progress-fill" /></div>
            )
          ) : null}
        </div>
      ) : null}
      {/* Final build time after a sync (assembly-only) build, when the row above is gone. */}
      {!jobStatus && !jobRunning && !building && timerText ? (
        <div style={{ marginBottom: 10 }}>
          <span className="build-timer mono">{timerText}</span>
        </div>
      ) : null}
      <div className={"table-scroll-wrap" + (edges.left ? " can-left" : "") + (edges.right ? " can-right" : "")}>
      <div className="table-scroll" ref={scrollRef} data-tour="complex-table">
        <table>
          <thead>
            <tr>
              <th className="remove-col" aria-label="Remove">
                {onRemoveAllRows ? (
                  <button
                    type="button"
                    className="ghost row-remove-all-btn"
                    title="Remove all complexes from the list"
                    aria-label="Remove all complexes"
                    onClick={onRemoveAllRows}
                  >
                    Remove<br />all
                  </button>
                ) : null}
              </th>
              <th>Name</th><th>Metal</th><th>CN</th><th>Charge</th><th>Ligands (denticity)</th>
              <th>Geometry</th>
              <th style={{ whiteSpace: "nowrap" }} data-tour="donors-col" title="Untick to edit the donor atoms">Donors</th>
              <th>Isomers</th><th className="act-col"><span className="sr-only">Build</span></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((cx, i) => {
              const sel = cx.sel;
              // η Cp/arene cap present -> show the octahedral topology as piano-stool.
              const isPiano = sel.ligands?.some((l) => l.is_arene);
              return (
                <Fragment key={i}>
                  <tr className={cx.warning ? "row-warn" : ""}>
                    <td className="remove-col">
                      {onRemoveRow ? (
                        <button
                          type="button"
                          className="ghost row-remove-btn"
                          title="Remove this complex from the list"
                          aria-label={`Remove ${cx.name || "complex"}`}
                          onClick={() => onRemoveRow(i)}
                        >
                          <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">
                            <path d="M1 1L9 9M9 1L1 9" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
                          </svg>
                        </button>
                      ) : null}
                    </td>
                    <td className="mono">{cx.name ?? "—"}</td>
                    <td className="mono">
                      {cx.metal}({cx.oxidation_state ?? "?"})
                      {cx.warning ? (
                        <span className="warn-mark" title={cx.warning}>⚠</span>
                      ) : null}
                    </td>
                    <td>{cx.coordination_number ?? "—"}</td>
                    <td className="mono">{cx.total_charge}</td>
                    <td>
                      {cx.ligands.map((l, k) => (
                        <span className={"chip lig-chip" + (l.warning ? " chip-warn" : "")} key={k}
                          title={l.warning || l.smiles}>
                          <span className="chip-smiles">{l.smiles}</span>
                          <span
                            className="chip-dent"
                            title={l.is_arene
                              ? `η${l.coord_atoms?.length ?? "?"} cap (occupies 3 coordination sites)`
                              : `denticity ${l.denticity ?? "?"}`}
                          >
                            {l.is_arene ? `η${l.coord_atoms?.length ?? "?"}` : (l.denticity ?? "?")}
                          </span>
                          {l.warning ? <span className="chip-warn-mark">⚠</span> : null}
                        </span>
                      ))}
                    </td>
                    <td>
                      {cx.supported ? (
                        <>
                          <select
                            aria-label={`Geometry for ${cx.name}`}
                            value={sel.geometry}
                            onChange={(e) => onRowChange(i, { geometry: e.target.value })}
                          >
                            {cx.geometry_options.map((g) => (
                              <option key={g} value={g}>{geometryLabel(g, isPiano)}</option>
                            ))}
                          </select>
                          {cx.needs_cap_selection ? (
                            <div
                              className="pill-warn"
                              style={{ marginTop: 4, fontSize: "var(--text-caption)" }}
                              title="Looks like a metallocene/sandwich. Untick Donors and select each Cp/arene ring so it counts as one η-cap — otherwise the batch build skips this row."
                            >
                              ⚠ select ring(s) as η-caps · skipped by Build all
                            </div>
                          ) : null}
                        </>
                      ) : (
                        <span className="pill-err">{cx.error || "unsupported"}</span>
                      )}
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`Donor atoms correct for ${cx.name}`}
                        title="Untick to edit the donor atoms"
                        data-tour={i === 1 ? "ferroquine-donors" : undefined}
                        checked={sel.donorsCorrect}
                        onChange={(e) =>
                          onRowChange(
                            i,
                            e.target.checked
                              ? { donorsCorrect: true }
                              : { donorsCorrect: false, donorsSnapshot: sel.ligands },
                          )
                        }
                      />
                    </td>
                    <td>
                      <IsomerCell cx={cx} sel={sel} index={i} onRowChange={onRowChange}>
                      {(() => {
                        // Metallocenes have no coordination-site model, so the isomer
                        // editor can't open for them; grey it out.
                        const noEditor = (sel.geometry || "").startsWith("metallocene");
                        return (
                          <button
                            className="ghost iso-editor-btn"
                            data-tour={i === 0 ? "assign-btn" : undefined}
                            disabled={!cx.supported || noEditor}
                            onClick={() => onAssign(i)}
                            aria-label={`Isomer editor for ${cx.name}`}
                            title={noEditor
                              ? "The isomer editor isn't available for metallocenes"
                              : "Define a specific isomer in 3D"}
                          >
                            Isomer editor
                          </button>
                        );
                      })()}
                      </IsomerCell>
                    </td>
                    <td className="act-col">
                      <button
                        className="primary"
                        disabled={!cx.supported || busy}
                        onClick={() => onBuild(i)}
                        title={busy ? "A build is already running — wait for it or cancel it first" : undefined}
                      >
                        <BusyLabel busy={buildingIndex === i} label="Build" busyLabel="Building…" compact />
                      </button>
                    </td>
                  </tr>
                  {!sel.donorsCorrect && (
                    <tr>
                      <td colSpan={10} style={{ paddingTop: 0 }} data-tour={i === 1 ? "donor-panel" : undefined}>
                        <DonorPanel
                          ligands={sel.ligands}
                          onChange={(li, atoms, isArene) => {
                            const ligands = sel.ligands.map((l, idx) =>
                              idx === li ? { ...l, coord_atoms: atoms, is_arene: isArene } : l
                            );
                            onDonorsChange(i, ligands);
                          }}
                          onApplyToAll={onApplyDonorsToAll}
                          onSave={() => onRowChange(i, { donorsCorrect: true })}
                          onCancel={() => {
                            if (sel.donorsSnapshot) onDonorsChange(i, sel.donorsSnapshot);
                            onRowChange(i, { donorsCorrect: true });
                          }}
                        />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
      </div>
    </div>
  );
}
