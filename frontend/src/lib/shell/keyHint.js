/** Home's number-key hint (components/shell/KeyHint.jsx): which tab its keycap points at next. */

/**
 * Where the keycap goes next: the first tab on show from place `from` on, its key
 * (its place in the strip, so a tab a narrow screen hides is skipped, never
 * renumbered) and the middle of it. `last` once the pass has reached the end.
 * Null when no tab is on show.
 */
export function nextSpot(tabs, from) {
  if (!tabs.some((tab) => tab.offsetWidth > 0)) return null
  let n = from % tabs.length
  while (tabs[n].offsetWidth === 0) n = (n + 1) % tabs.length
  return { n: n + 1, x: tabs[n].offsetLeft + tabs[n].offsetWidth / 2, last: n + 1 >= tabs.length }
}
