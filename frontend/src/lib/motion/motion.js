/**
 * Whether motion is off. reducedMotion is the reader's own reduce-motion
 * setting alone, for pages outside the app (the landing) where the in-app
 * switch does not exist. motionOff adds the in-app Animations switch (which
 * drives --motion-scale to 0). The one check, for the JS that moves things
 * itself: a glide, a canvas, a timed reveal.
 */
export const reducedMotion = () =>
  Boolean(globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches)

export const motionOff = () =>
  reducedMotion() ||
  Number(getComputedStyle(document.documentElement).getPropertyValue('--motion-scale')) === 0
