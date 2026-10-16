/**
 * Whether motion is off: the reader's own reduce-motion setting, or the in-app
 * Animations switch (which drives --motion-scale to 0). The one check, for the
 * JS that moves things itself: a glide, a canvas, a timed reveal.
 */
export const motionOff = () =>
  globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ||
  Number(getComputedStyle(document.documentElement).getPropertyValue('--motion-scale')) === 0
