import { useEffect, useState } from "react";
import { api } from "../api.js";
import MoleculeDepiction from "./MoleculeDepiction.jsx";

// Selecting a whole 5-/6-membered all-carbon ring means an η5-Cp / η6-arene cap
// (denticity 3), not that many σ donors. Mirrors the backend perception rule
// (perception._selected_carbocyclic_ring) so the CN updates live on donor edits.
function isCarbocyclicRing(dep, sel) {
  if (!dep || (sel.length !== 5 && sel.length !== 6)) return false;
  const S = new Set(sel);
  const byIdx = {};
  for (const a of dep.atoms) byIdx[a.idx] = a;
  if (![...S].every((i) => byIdx[i]?.symbol === "C")) return false;
  const deg = {};
  let edges = 0;
  for (const b of dep.bonds || []) {
    const ia = dep.atoms[b.a]?.idx, ib = dep.atoms[b.b]?.idx;
    if (S.has(ia) && S.has(ib)) { deg[ia] = (deg[ia] || 0) + 1; deg[ib] = (deg[ib] || 0) + 1; edges++; }
  }
  // a single cycle over the selection: |edges| == |nodes| and every node degree 2
  return edges === sel.length && [...S].every((i) => deg[i] === 2);
}

// Donor-correction panel: a flat 2D depiction of each ligand with
// clickable atoms to fix which are the coordinating (donor) atoms. Opened when
// "coordinating atoms correct?" is unticked.
function LigandPicker({ ligand, onChange, onApplyToAll }) {
  const [depiction, setDepiction] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setDepiction(null);
    setError("");
    api
      .depict(ligand.smiles)
      .then((d) => {
        if (cancelled) return;
        if (d.detail) setError(d.detail);
        else setDepiction(d);
      })
      .catch((e) => !cancelled && setError(String(e)));
    return () => {
      cancelled = true;
    };
  }, [ligand.smiles]);

  const donors = ligand.coord_atoms || [];
  const toggle = (idx) => {
    const next = donors.includes(idx) ? donors.filter((i) => i !== idx) : [...donors, idx].sort((a, b) => a - b);
    onChange(next, isCarbocyclicRing(depiction, next));
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, padding: "4px 0" }}>
      <div>
        <div className="mono" style={{ fontSize: "var(--text-caption)", marginBottom: 4, wordBreak: "break-all" }}>
          {ligand.smiles}
        </div>
        <div className="muted" style={{ fontSize: "var(--text-caption)" }}>
          donors: <span className="mono">[{donors.join(", ")}]</span>
          {ligand.is_arene ? (
            <span className="chip" style={{ marginLeft: 6 }} title="η-cap (occupies 3 coordination sites)">
              η{ligand.coord_atoms?.length ?? ""}
            </span>
          ) : null}
        </div>
        {onApplyToAll ? (
          <button
            className="ghost"
            style={{ marginTop: 6, fontSize: "var(--text-caption)" }}
            disabled={!donors.length}
            title="Set these donor atoms on every complex that uses this same ligand"
            onClick={() => onApplyToAll(ligand.smiles, donors)}
          >
            Apply to all matching
          </button>
        ) : null}
      </div>
      {error ? (
        <span className="pill-err">{error}</span>
      ) : depiction ? (
        <MoleculeDepiction
          atoms={depiction.atoms}
          bonds={depiction.bonds}
          selected={donors}
          onToggle={toggle}
        />
      ) : (
        <span className="spinner" />
      )}
    </div>
  );
}

// Atom edits apply live (so CN/geometry update as you click); Save just closes the
// panel keeping them, Cancel reverts to the selection from when it opened. Both are a
// clickable alternative to the row's Donors checkbox.
export default function DonorPanel({ ligands, onChange, onApplyToAll, onSave, onCancel, tourId }) {
  return (
    <div className="donor-panel" data-tour={tourId}>
      <div className="donor-panel-head">
        <div className="muted">
          Click atoms to set the coordinating (donor) atoms for each ligand:
        </div>
        {(onSave || onCancel) && (
          <div className="donor-panel-actions">
            {onSave && (
              <button className="icon-btn save" title="Save this selection" aria-label="Save selection" onClick={onSave}>
                <svg viewBox="0 0 20 20" width="15" height="15" aria-hidden="true">
                  <path d="M4 10.5 L8 14.5 L16 5.5" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            )}
            {onCancel && (
              <button className="icon-btn" title="Cancel (discard changes)" aria-label="Cancel" onClick={onCancel}>
                <svg viewBox="0 0 20 20" width="15" height="15" aria-hidden="true">
                  <path d="M5 5 L15 15 M15 5 L5 15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
                </svg>
              </button>
            )}
          </div>
        )}
      </div>
      <div className="donor-grid">
        {ligands.map((l, i) => (
          <LigandPicker
            key={i}
            ligand={l}
            onChange={(atoms) => onChange(i, atoms)}
            onApplyToAll={onApplyToAll}
          />
        ))}
      </div>
    </div>
  );
}
