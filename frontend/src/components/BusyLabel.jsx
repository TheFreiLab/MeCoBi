// Button content that swaps to "spinner + busy text" while work is running, without the
// button changing size: both labels sit in the same grid cell and the inactive one is
// visibility:hidden, so the button is always as wide as the longer of the two. Hidden text
// is left out of the accessible name, so a busy button reads e.g. "Parsing…", never "".
// `compact` (tight spots like the per-row Build): the busy state shows only the spinner and
// the busy text is screen-reader-only, so the button keeps the idle label's width.
export default function BusyLabel({ busy, label, busyLabel, compact = false }) {
  return (
    <span className="busy-label">
      <span className={busy ? "busy-hide" : undefined}>{label}</span>
      <span className={busy ? undefined : "busy-hide"}>
        <span className="spinner" aria-hidden="true" />
        {compact ? <span className="sr-only">{busyLabel}</span> : busyLabel}
      </span>
    </span>
  );
}
