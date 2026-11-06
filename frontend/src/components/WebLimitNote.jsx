import { useEffect, useState } from "react";

// The static per-job / server complex limits, shown as a small italic note under the
// input controls. These are fixed config, so this fetches once (no polling). Renders
// nothing until loaded (or if /api/workload is unavailable).
export default function WebLimitNote() {
  const [limits, setLimits] = useState(null);
  useEffect(() => {
    let cancelled = false;
    fetch("/api/workload")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!cancelled && d) setLimits(d);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  if (limits?.max_complexes_per_job == null || limits?.max_pending_structures == null) return null;
  return (
    <div className="muted web-limit-note">
      Web limit: {limits.max_complexes_per_job.toLocaleString()} complexes per job;
      {" "}{limits.max_pending_structures.toLocaleString()} unfinished structures across the server
      {" "}(with all isomers, each isomer counts).
    </div>
  );
}
