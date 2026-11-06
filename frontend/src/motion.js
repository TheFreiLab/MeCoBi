// The user's OS "reduce motion" setting. Read at call time (not cached) so a change
// while the app is open applies to the next animation.
export function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
