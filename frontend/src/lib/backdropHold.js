/**
 * Holding the backdrop still while a tab switches.
 *
 * The backdrop redraws the whole screen every frame, under a blurred glass
 * panel, and a switch is the busiest frame there is: a new panel laid out and
 * the tint repainted. Paused for the switch, the browser has one less thing to
 * do in the frames the eye is on. Module state, one backdrop per page.
 */
let until = 0

/** Hold for `ms` from `now`; a hold already longer is kept. */
export function holdBackdrop(ms, now = performance.now()) {
  until = Math.max(until, now + ms)
}

/** How long the hold has left at `now`, 0 when there is none. */
export const heldFor = (now = performance.now()) => Math.max(0, until - now)
