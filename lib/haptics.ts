// Tiny haptic helpers — subtle physical feedback that makes confirmations feel
// premium without being noisy. No-ops where the API isn't supported (iOS Safari)
// or the user prefers reduced motion.
function ok(): boolean {
  if (typeof navigator === "undefined" || typeof navigator.vibrate !== "function") return false;
  if (typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return false;
  return true;
}

// A light tap — for taps, toggles, selections.
export function tap(): void {
  if (ok()) navigator.vibrate(12);
}

// A satisfying double-pulse — for a completed action (paid, saved, logged, done).
export function success(): void {
  if (ok()) navigator.vibrate([14, 40, 22]);
}
