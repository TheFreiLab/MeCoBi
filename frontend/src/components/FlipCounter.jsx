import { useEffect, useState } from "react";
import { api } from "../api.js";

// Split-flap "structures built" counter for the footer (the old-web hit counter, in house
// indigo). The server keeps anonymous daily totals (GET /api/stats); this reads the total on
// load and again whenever new results arrive, and rolls each digit up to it one flap at a
// time, as a real split-flap drum does.
const DIGITS = 7;
const GROUPS = [1, 3, 3]; // 0 012 483
const REFRESH_DELAY_MS = 1500;

const reducedMotion = () =>
  typeof window !== "undefined" &&
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

function Flap({ target }) {
  const [cur, setCur] = useState("0");
  const [next, setNext] = useState(null); // digit the current flip lands on

  useEffect(() => {
    if (next !== null || cur === target) return;
    if (reducedMotion()) {
      setCur(target);
      return;
    }
    setNext(String((Number(cur) + 1) % 10));
  }, [cur, next, target]);

  const done = () => {
    setCur(next);
    setNext(null);
  };

  return (
    <span className="flap">
      <span className="flap-half flap-top"><span>{next ?? cur}</span></span>
      <span className="flap-half flap-bot"><span>{cur}</span></span>
      {next !== null && (
        <>
          <span className="flap-leaf flap-top flap-fall"><span>{cur}</span></span>
          <span className="flap-leaf flap-bot flap-land" onAnimationEnd={done}>
            <span>{next}</span>
          </span>
        </>
      )}
    </span>
  );
}

function monthYear(iso) {
  const d = new Date(`${iso}T00:00:00Z`);
  return Number.isNaN(d.getTime())
    ? null
    : d.toLocaleDateString("en-GB", { month: "long", year: "numeric", timeZone: "UTC" });
}

export default function FlipCounter({ refreshKey }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    let live = true;
    const t = setTimeout(
      () => api.stats().then((s) => live && setStats(s)).catch(() => {}),
      refreshKey ? REFRESH_DELAY_MS : 0
    );
    return () => {
      live = false;
      clearTimeout(t);
    };
  }, [refreshKey]);

  if (!stats || typeof stats.structures_built !== "number") return null;
  const n = Math.max(0, Math.floor(stats.structures_built));
  const digits = String(n).padStart(DIGITS, "0").slice(-DIGITS).split("");
  const since = stats.since ? monthYear(stats.since) : null;
  const caption = since ? `structures built since ${since}` : "structures built";

  let i = 0;
  return (
    <div className="flip-counter">
      <span className="sr-only">{`${n.toLocaleString("en-GB")} ${caption}`}</span>
      <span className="flip-board" aria-hidden="true">
        {GROUPS.map((size, g) => (
          <span className="flip-group" key={g}>
            {digits.slice(i, (i += size)).map((d, k) => (
              <Flap key={k} target={d} />
            ))}
          </span>
        ))}
      </span>
      <span aria-hidden="true">{caption}</span>
    </div>
  );
}
