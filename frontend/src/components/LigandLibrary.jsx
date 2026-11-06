import { useEffect, useState } from "react";
import { api } from "../api.js";
import { LIGAND_LIBRARY } from "../ligandLibrary.js";

// A clickable ligand tile: a proper RDKit 2D structure (served as an SVG that uses
// currentColor, so it follows the theme) over the short name.
function LigandBox({ lig, svg, onInsert }) {
  return (
    <button
      type="button"
      className="lig-box"
      title={`${lig.name} — ${lig.smiles}  (click to insert)`}
      onClick={() => onInsert(lig.smiles)}
    >
      <span className="lig-thumb" aria-hidden="true">
        {svg ? (
          <span className="lig-thumb-svg" dangerouslySetInnerHTML={{ __html: svg }} />
        ) : (
          <span className="lig-thumb-wait" />
        )}
      </span>
      <span className="lig-box-name">{lig.label}</span>
    </button>
  );
}

// An openable, scrollable grid of common ligands. Click a tile to insert its SMILES at
// the cursor (App.onInsert). The grid scrolls only when the user scrolls it (no
// auto-drift, so it respects reduced motion and each ligand is one tab stop).
// Theme-token styled.
export default function LigandLibrary({ onInsert, onClose }) {
  const [svgs, setSvgs] = useState({}); // smiles -> rendered structure SVG string

  // Fetch every structure SVG once (backend-cached).
  useEffect(() => {
    let cancelled = false;
    Promise.all(
      LIGAND_LIBRARY.map((l) =>
        api.depictSvg(l.smiles).then((d) => [l.smiles, d?.svg || null]).catch(() => [l.smiles, null])
      )
    ).then((pairs) => !cancelled && setSvgs(Object.fromEntries(pairs)));
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="ligand-library card" data-tour="ligand-library-panel">
      <div className="lig-lib-head">
        <h2>Ligand library</h2>
        <button className="toggle-btn" onClick={onClose} title="Close the ligand library">Close</button>
      </div>
      <p className="muted lig-lib-hint">Click a ligand to drop its SMILES at the cursor.</p>
      <div className="lig-reel">
        <div className="lig-reel-track">
          {LIGAND_LIBRARY.map((lig) => (
            <LigandBox key={lig.smiles} lig={lig} svg={svgs[lig.smiles]} onInsert={onInsert} />
          ))}
        </div>
      </div>
    </div>
  );
}
