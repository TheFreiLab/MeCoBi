import { useEffect, useState } from "react";
import { api } from "../api.js";
import BusyLabel from "./BusyLabel.jsx";
import MiddleName from "./MiddleName.jsx";
import ViewerGrid from "./ViewerGrid.jsx";

// 3x3 is the legibility limit on a card-width canvas; the shared-context grid
// itself could take more panes.
export const MAX_RENDER = 9;

export default function Results({ files, viewTokens, onViewTokens, onRemove, onRemoveAll }) {
  // Per-token result state: { loading, error, result:{label,value} } keyed by token.
  const [smiles, setSmiles] = useState({});
  // Which token's output-type menu is open (only one at a time).
  const [menuToken, setMenuToken] = useState(null);
  // Which token's download-format menu is open (only one at a time).
  const [dlToken, setDlToken] = useState(null);
  // Which CSV-export choice menu is open (header control).
  const [exportOpen, setExportOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  // Which results have their build-warning list expanded (click the ⚠ to toggle).
  const [warnOpen, setWarnOpen] = useState({});
  // Installed representations (Complex SMILES / T-REX / ...). Empty until probed;
  // drives both the per-row menu and the CSV export, so a newly published notation
  // added to the server registry shows up in both automatically.
  const [reps, setReps] = useState([]);

  useEffect(() => {
    api.reverseBackends().then((c) => setReps(c.representations || [])).catch(() => {});
  }, []);

  if (!files?.length) return null;

  const atCap = viewTokens.length >= MAX_RENDER;
  const toggle = (token) => {
    if (viewTokens.includes(token)) return onViewTokens(viewTokens.filter((t) => t !== token));
    if (atCap) return;
    const chosen = new Set([...viewTokens, token]);
    onViewTokens(files.filter((f) => chosen.has(f.token)).map((f) => f.token)); // keep list order
  };

  // Render one representation (Complex SMILES / T-REX / ...) of a built structure.
  const getRepr = async (token, file, rep) => {
    setMenuToken(null);
    setSmiles((s) => ({ ...s, [token]: { loading: true } }));
    try {
      const xyz = await api.fileText(token);
      const result = await api.represent(xyz, rep.key, file?.total_charge ?? 0);
      setSmiles((s) => ({ ...s, [token]: { result } }));
    } catch (e) {
      setSmiles((s) => ({ ...s, [token]: { error: e.message } }));
    }
  };

  // Export every result to a CSV, one column per chosen representation. Fetches
  // each structure's xyz, then the server converts them in one batch.
  const exportCsv = async (columns) => {
    setExportOpen(false);
    setExporting(true);
    try {
      const items = await Promise.all(
        files.map(async (f) => ({
          name: f.name,
          xyz: await api.fileText(f.token),
          overall_charge: f.total_charge ?? 0,
        }))
      );
      const { csv } = await api.reverseExport(items, columns);
      const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
      const a = document.createElement("a");
      a.href = url;
      // Datestamp (YYYY-MM-DD_HHMMSS, local time) so repeated exports don't overwrite.
      const d = new Date();
      const p = (n) => String(n).padStart(2, "0");
      const ts = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}_` +
        `${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
      a.download = `mecobi_smiles_${ts}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      window.alert(`Export failed: ${e.message}`);
    } finally {
      setExporting(false);
    }
  };

  // All results of one submission share a job-id prefix in their token; the
  // batch-download endpoint zips that whole job directory.
  const jobId = files[0].token.split("/")[0];

  const removeAll = () => {
    const n = files.length;
    if (window.confirm(`Clear ${n} result${n === 1 ? "" : "s"} from this list? Download them first if you need them.`)) {
      onRemoveAll?.();
    }
  };

  return (
    <div className="card" data-tour="results-card">
      <div className="results-head">
        <h2 style={{ margin: 0 }}>Results</h2>
        <span className="results-count muted">
          rendering {viewTokens.length} of {files.length}
          {atCap ? ` · max ${MAX_RENDER}` : ""}
        </span>
        <span className="grow" />
        <span className="result-actions">
          <span className="actions-label muted" aria-hidden="true">All structures:</span>
          <a className="ghost" href={api.downloadAllUrl(jobId)} download title="Download all structures as a zip">
            Download all (zip)
          </a>
          {reps.length ? (
            <span className="smiles-btn">
              <button
                className="ghost"
                title="Export SMILES / notation for all results as a CSV"
                disabled={exporting}
                onClick={() =>
                  reps.length === 1
                    ? exportCsv([reps[0].key])
                    : setExportOpen((v) => !v)
                }
              >
                <BusyLabel busy={exporting} label="Export CSV ▾" busyLabel="Exporting…" />
              </button>
              {exportOpen ? (
                <div className="smiles-menu" onMouseLeave={() => setExportOpen(false)}>
                  {reps.map((r) => (
                    <button
                      key={r.key}
                      className="smiles-item"
                      title={r.cite || undefined}
                      onClick={() => exportCsv([r.key])}
                    >
                      <span>{r.label}</span>
                      {r.ref ? <em className="ref">{r.ref}</em> : null}
                    </button>
                  ))}
                  {reps.length > 1 ? (
                    <button
                      className="smiles-item"
                      onClick={() => exportCsv(reps.map((r) => r.key))}
                    >
                      All columns
                    </button>
                  ) : null}
                </div>
              ) : null}
            </span>
          ) : null}
          {onRemoveAll ? (
            <button className="ghost" title="Clear all results" onClick={removeAll}>
              Remove all
            </button>
          ) : null}
        </span>
      </div>
      {files.map((f) => {
        const rev = smiles[f.token];
        return (
          <div className="result-item-wrap" key={f.token}>
            <div className="result-item">
              <input
                type="checkbox"
                checked={viewTokens.includes(f.token)}
                disabled={!viewTokens.includes(f.token) && atCap}
                onChange={() => toggle(f.token)}
                title={`Show in the 3D grid (up to ${MAX_RENDER})`}
              />
              <span className="name" title={f.name}>
                <MiddleName text={f.name} />
                {f.is_lowest_energy ? <span className="chip chip-star" title="lowest GFN2 energy">★</span> : null}
                {f.relative_energy_kcal != null ? (
                  <span className="res-energy" title="relative GFN2 energy">
                    +{f.relative_energy_kcal.toFixed(1)} kcal/mol
                  </span>
                ) : null}
              </span>
              {f.warnings?.length ? (
                <button
                  type="button"
                  className={`res-warn${warnOpen[f.token] ? " open" : ""}`}
                  aria-expanded={!!warnOpen[f.token]}
                  title={`${f.warnings.length} build warning${f.warnings.length > 1 ? "s" : ""}: click to ${warnOpen[f.token] ? "hide" : "show"}`}
                  onClick={() => setWarnOpen((o) => ({ ...o, [f.token]: !o[f.token] }))}
                >
                  ⚠
                </button>
              ) : (
                <span />
              )}
              <span className="result-actions">
                <button className="ghost" onClick={() => onViewTokens([f.token])}>
                  View
                </button>
                {reps.length ? (
                  <span className="smiles-btn">
                    <button
                      className="ghost"
                      title="Get SMILES / notation for this structure"
                      disabled={rev?.loading}
                      onClick={() =>
                        reps.length === 1
                          ? getRepr(f.token, f, reps[0])
                          : setMenuToken(menuToken === f.token ? null : f.token)
                      }
                    >
                      <BusyLabel busy={!!rev?.loading}
                        label={reps.length === 1 ? "Get SMILES" : "Get SMILES ▾"} busyLabel="Getting…" />
                    </button>
                    {menuToken === f.token ? (
                      <div className="smiles-menu" onMouseLeave={() => setMenuToken(null)}>
                        {reps.map((r) => (
                          <button
                            key={r.key}
                            className="smiles-item"
                            title={r.cite || undefined}
                            onClick={() => getRepr(f.token, f, r)}
                          >
                            <span>{r.label}</span>
                            {r.ref ? <em className="ref">{r.ref}</em> : null}
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </span>
                ) : null}
                {f.formats && f.formats.length > 1 ? (
                  <span className="smiles-btn">
                    <button
                      className="ghost"
                      title="Download this structure (choose a format)"
                      onClick={() => setDlToken(dlToken === f.token ? null : f.token)}
                    >
                      Download ▾
                    </button>
                    {dlToken === f.token ? (
                      <div className="smiles-menu" onMouseLeave={() => setDlToken(null)}>
                        {f.formats.map((ext) => (
                          <a
                            key={ext}
                            className="smiles-item"
                            href={api.fileUrlAs(f.token, ext)}
                            download
                            onClick={() => setDlToken(null)}
                          >
                            <span>{ext.toUpperCase()}</span>
                          </a>
                        ))}
                      </div>
                    ) : null}
                  </span>
                ) : (
                  <a className="ghost" href={api.fileUrl(f.token)} download>
                    Download
                  </a>
                )}
                {onRemove ? (
                  <button className="ghost" title="Remove from results" onClick={() => onRemove(f.token)}>
                    Remove
                  </button>
                ) : null}
              </span>
            </div>
            {warnOpen[f.token] && f.warnings?.length ? (
              <ul className="res-warn-list">
                {[...new Set(f.warnings)].map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            ) : null}
            {rev?.error ? (
              <div style={{ marginTop: 4 }}><span className="pill-err">{rev.error}</span></div>
            ) : null}
            {rev?.result ? (
              <div className="reverse-out">
                <span className="muted">
                  {rev.result.label}
                  {reps.find((r) => r.key === rev.result.key)?.ref ? (
                    <em className="ref"> {reps.find((r) => r.key === rev.result.key).ref}</em>
                  ) : null}
                  :
                </span>
                <span className="mono reverse-lig">{rev.result.value}</span>
              </div>
            ) : null}
          </div>
        );
      })}
      <div style={{ marginTop: 14 }}>
        <ViewerGrid
          items={viewTokens.map((t) => {
            const f = files.find((x) => x.token === t);
            return {
              token: t,
              name: f?.name || "",
              isomer_label: f?.isomer_label ?? null,
              metalIndex: f?.metal_index ?? null,
              donorIndices: f?.donor_indices || null,
            };
          })}
        />
      </div>
    </div>
  );
}
