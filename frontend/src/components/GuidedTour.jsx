import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { prefersReducedMotion } from "../motion.js";

// A self-contained spotlight tour (no external dependency, so it stays inside the
// committed-bundle + self-hosted deployment constraints). It dims the page and cuts a
// bright ring around the current step's target, while the instruction card stays PINNED
// in one place (bottom-centre) so the reader never has to chase it around the screen.
// Targets resolve live from data-tour="<id>" attributes; a step whose target isn't in
// the DOM is skipped, so navigation adapts as sections open.
//
// Steps can be INTERACTIVE: a step may run an `action` on entry and `waitFor` a
// data-tour target to appear before advancing — during that wait the page stays
// clickable so the user performs the real action (Load sample, Parse, Assign) and the
// tour continues once its result appears. Theme-token styled (.tour-* in styles.css).

const PAD = 8; // bright ring padding around the target
// Move the card off a small control (a button, a checkbox) if it hides ANY of it; off a big
// panel only if it hides more than a quarter (a panel taller than the screen can't be fully
// cleared, and on desktop the usual spot already leaves most of it visible).
const SMALL_TARGET = 120; // px, ring height
const MAX_COVER = 0.25;

// Share (0..1) of the target ring's on-screen area hidden by a card at `top`.
function coverAt(top, h, cardBox, ring) {
  const vx = Math.max(0, Math.min(ring.right, innerWidth) - Math.max(ring.left, 0));
  const vy = Math.max(0, Math.min(ring.bottom, innerHeight) - Math.max(ring.top, 0));
  if (!vx || !vy) return 0;
  const ix = Math.max(0, Math.min(cardBox.right, ring.right) - Math.max(cardBox.left, ring.left));
  const iy = Math.max(0, Math.min(top + h, ring.bottom) - Math.max(top, ring.top));
  return (ix * iy) / (vx * vy);
}

const hasTarget = (id) => !!document.querySelector(`[data-tour="${id}"]`);
const showable = (s) => !!s && (!s.target || hasTarget(s.target));

export default function GuidedTour({ open, steps, actions, onClose }) {
  const [idx, setIdx] = useState(0);
  const [rect, setRect] = useState(null); // current target's viewport rect, or null (centred)
  const [boxTop, setBoxTop] = useState(null); // free-mode (pre-table) card top, px
  const cardRef = useRef(null);
  const [flipTop, setFlipTop] = useState(null); // card top when moved off its target, px

  // Nearest showable step in a direction, skipping steps whose target isn't in the DOM.
  const seek = (dir, from) => {
    let i = from + dir;
    while (i >= 0 && i < steps.length && !showable(steps[i])) i += dir;
    return i;
  };
  function finish() {
    onClose?.();
  }
  function next() {
    const i = seek(+1, idx);
    if (i >= steps.length) finish();
    else setIdx(i);
  }
  function prev() {
    const i = seek(-1, idx);
    if (i >= 0) setIdx(i);
  }

  // On open, land on the first showable step.
  useEffect(() => {
    if (!open) return;
    let i = 0;
    while (i < steps.length && !showable(steps[i])) i += 1;
    setIdx(i < steps.length ? i : 0);
  }, [open, steps]);

  const cur = steps[idx];
  const isLast = seek(+1, idx) >= steps.length;

  // Run an interactive step's on-entry action, then (if it waits) poll and auto-advance
  // when its condition is met: `waitFor` waits for a target to APPEAR, `waitGone` waits
  // for one to DISAPPEAR (e.g. a panel the user closes). The page stays clickable while
  // waiting so the user performs the real action.
  useEffect(() => {
    if (!open || !cur) return undefined;
    if (cur.action && actions?.[cur.action]) actions[cur.action]();
    if (!cur.waitFor && !cur.waitGone) return undefined;
    const check = () => {
      const done = cur.waitFor ? hasTarget(cur.waitFor) : !hasTarget(cur.waitGone);
      if (done) {
        clearInterval(id);
        next();
      }
    };
    const id = setInterval(check, 300);
    check();
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, cur]);

  // Locate the current target (centred in view) and keep the ring glued to it.
  useLayoutEffect(() => {
    if (!open || !cur) return undefined;
    const place = () => {
      const el = cur.target ? document.querySelector(`[data-tour="${cur.target}"]`) : null;
      const r = el ? el.getBoundingClientRect() : null;
      setRect(r ? { top: r.top, left: r.left, width: r.width, height: r.height } : null);
      // Free (pre-table) mode: park the card just below the input card so it never
      // covers the input or Parse, and stays put across the intro steps. It docks to
      // the bottom the moment the parsed table exists.
      if (!hasTarget("complex-table")) {
        const card = document.querySelector('[data-tour="input-card"]');
        const bottom = card ? card.getBoundingClientRect().bottom : window.innerHeight * 0.3;
        setBoxTop(Math.max(80, Math.min(bottom + 16, window.innerHeight - 220)));
      }
    };
    const el = cur.target ? document.querySelector(`[data-tour="${cur.target}"]`) : null;
    if (el) el.scrollIntoView({ block: "center", behavior: prefersReducedMotion() ? "auto" : "smooth" });
    place();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
    };
  }, [open, cur]);

  // Keyboard: Esc skips, Enter / → advance (except while waiting on the user), ← back.
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === "Escape") finish();
      else if ((e.key === "Enter" || e.key === "ArrowRight") && !cur?.waitFor && !cur?.waitGone) next();
      else if (e.key === "ArrowLeft") prev();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  // Keep the card off its target (audit H13). Its usual spot (below the input card, or
  // docked to the bottom) is kept unless it hides too much of the target (see
  // SMALL_TARGET / MAX_COVER), as happens on short screens (phones, 200% zoom); then the
  // candidate that hides the least wins: just below or above the target, or the
  // top/bottom of the window.
  const docked = open && hasTarget("complex-table");
  useLayoutEffect(() => {
    const card = cardRef.current;
    let top = null;
    if (open && card && rect) {
      const h = card.offsetHeight, vh = innerHeight, GAP = 12;
      const box = card.getBoundingClientRect();
      const ring = { top: rect.top - PAD, bottom: rect.top + rect.height + PAD,
        left: rect.left - PAD, right: rect.left + rect.width + PAD };
      const clamp = (t) => Math.max(8, Math.min(vh - h - 8, t));
      const usual = docked ? vh - 28 - h : (boxTop ?? vh * 0.34);
      const limit = ring.bottom - ring.top < SMALL_TARGET ? 0 : MAX_COVER;
      if (coverAt(usual, h, box, ring) > limit) {
        const options = [ring.bottom + GAP, ring.top - GAP - h, 8, vh - h - 8].map(clamp);
        top = options.reduce((best, t) => (coverAt(t, h, box, ring) < coverAt(best, h, box, ring) ? t : best));
        top = Math.round(top);
      }
    }
    if (top !== flipTop) setFlipTop(top);
  });

  if (!open || !cur) return null;

  // Soft "position / total" over the steps currently reachable (grows once an
  // interactive step reveals later sections).
  const reachable = steps.filter(showable);
  const pos = reachable.indexOf(cur) + 1;
  const interactive = !!cur.interactive;
  // The card sits below the input card through the intro, then docks to the bottom the
  // moment the parsed table appears (so it drops out of the way as content arrives);
  // `docked` is computed above, next to the placement effect.

  return (
    <div className="tour-root" role="dialog" aria-modal="true" aria-label="Guided tour">
      {/* Full-screen catcher. On a normal step it just blocks stray page clicks (it does
          NOT abort — only Skip / Esc end the tour); on an interactive step it's
          click-through so the user can act on the page. */}
      <div className={"tour-blocker" + (rect ? "" : " dim") + (interactive ? " pass" : "")} />
      {rect && (
        <div
          className="tour-highlight"
          style={{
            top: rect.top - PAD,
            left: rect.left - PAD,
            width: rect.width + PAD * 2,
            height: rect.height + PAD * 2,
          }}
        />
      )}
      <div
        ref={cardRef}
        className={"tour-tooltip " + (docked ? "docked" : "free")}
        style={flipTop != null ? { top: flipTop, bottom: "auto" }
          : docked ? undefined : { top: boxTop ?? "34%" }}
      >
        <div className="tour-count mono">
          {pos} / {reachable.length}
        </div>
        <h3 className="tour-title">{cur.title}</h3>
        <p className="tour-body">{cur.body}</p>
        <div className="tour-nav">
          <button className="ghost" onClick={finish}>
            Skip
          </button>
          <div className="tour-nav-right">
            {pos > 1 && (
              <button className="ghost" onClick={prev}>
                Back
              </button>
            )}
            {cur.waitFor || cur.waitGone ? (
              <span className="tour-wait">
                <span className="tour-wait-dot" />
                {cur.waitLabel || "Your turn"}
              </span>
            ) : (
              <button className="primary" onClick={next}>
                {isLast ? "Done" : "Next"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
