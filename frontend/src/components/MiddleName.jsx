// A file name that, when space runs out, is cut in the MIDDLE ("cisplatin-ana…_trans_c0.xyz")
// instead of at the end: the head shrinks with an ellipsis while the tail, the isomer and
// conformer suffix that tells results apart, always stays visible (audit H12). Both parts
// are in the DOM, so screen readers and copy-paste still get the full name.
const MAX_TAIL = 20;

// Where the always-visible tail starts: at an underscore, so it reads "_trans_c0.xyz" rather
// than "ing_trans_c0.xyz". Prefer the last two "_" segments (isomer + conformer), else the
// last one, else a plain 16-character tail. -1 = the name is short enough not to split.
function tailStart(s) {
  if (s.length <= MAX_TAIL + 4) return -1;
  const last = s.lastIndexOf("_");
  const prev = last > 0 ? s.lastIndexOf("_", last - 1) : -1;
  if (prev > 0 && s.length - prev <= MAX_TAIL) return prev;
  if (last > 0 && s.length - last <= MAX_TAIL) return last;
  return s.length - 16;
}

export default function MiddleName({ text }) {
  const s = String(text ?? "");
  const cut = tailStart(s);
  if (cut < 0) return <span className="mid-name"><span className="mid-name-head">{s}</span></span>;
  return (
    <span className="mid-name">
      <span className="mid-name-head">{s.slice(0, cut)}</span>
      <span className="mid-name-tail">{s.slice(cut)}</span>
    </span>
  );
}
