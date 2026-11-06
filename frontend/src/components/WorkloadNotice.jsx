import { useEffect, useState } from "react";

export default function WorkloadNotice() {
  const [workload, setWorkload] = useState(null);
  useEffect(() => {
    let cancelled = false;
    let timer;
    const controller = new AbortController();
    async function refresh() {
      try {
        const response = await fetch("/api/workload", { signal: controller.signal });
        if (!response.ok) throw new Error("Workload unavailable");
        const data = await response.json();
        if (!cancelled) setWorkload(data);
      } catch {
        if (!cancelled) setWorkload(null); // Do not leave a stale busy notice on screen.
      } finally {
        if (!cancelled) timer = setTimeout(refresh, 10000);
      }
    }
    refresh();
    return () => { cancelled = true; clearTimeout(timer); controller.abort(); };
  }, []);

  // Only surfaces the "server busy" alert now; the static per-job/server limits live in
  // WebLimitNote under the input. Renders nothing when the server is free.
  if (!workload || !workload.busy) return null;
  const longRunning = workload.longest_running_s >= workload.long_job_seconds;
  const minutes = Math.max(1, Math.ceil(workload.estimated_wait_s / 60));
  return (
    <div style={{ marginBottom: 16 }}>
      <div className="pill-warn" role="status" style={{ display: "block", whiteSpace: "normal" }}>
        <strong>{longRunning ? "A long job is running." : "The server is busy."}</strong>
        {" "}Use Build all to join the queue. Individual builds are available when the server is free.
        {workload.queued_jobs > 0 && <> {workload.queued_jobs} job{workload.queued_jobs === 1 ? "" : "s"} queued.</>}
        {workload.estimated_wait_s > 0 && <> Existing work is estimated at about {minutes} minute{minutes === 1 ? "" : "s"}.</>}
        {" "}Estimates are approximate; large molecules and multiple isomers can take longer.
      </div>
    </div>
  );
}
