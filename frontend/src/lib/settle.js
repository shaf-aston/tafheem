/**
 * A screen reached by moving around arrives finished, not built in front of you.
 *
 * Each card's entrance (motion.css rise-in) plays when it first appears, and a
 * CSS animation also starts over whenever its element comes back from
 * display:none, which is how App hides a tab it keeps alive. So every switch,
 * of tab or of section inside one, had a dozen or more cards rising in a
 * cascade for up to a second, and after Start over (a reload, nothing cached)
 * every tab cascaded again when its data landed.
 *
 * So moving starts an arrival over the tab panel: entrances jump to their end
 * before paint, and so does every one in content that lands until the reader
 * next presses or types anywhere. What answers that press (a search's results,
 * a step revealed, a quiz's feedback) still moves. One arrival at a time.
 *
 * Only finite animations: a skeleton's shimmer loops forever, and finishing
 * one throws.
 */
import { useLayoutEffect } from 'react'

// What ends an arrival: the reader doing something, anywhere on the page.
const ACTS = ['pointerdown', 'keydown']

export function finishEntrances(root) {
  if (!root?.getAnimations) return
  for (const animation of root.getAnimations({ subtree: true })) {
    if (Number.isFinite(animation.effect?.getComputedTiming().endTime)) animation.finish()
  }
}

let leave = () => {}

/** Settle the tab panel now and whatever lands in it until the reader acts. */
export function arrive() {
  leave()
  const panel = document.querySelector('[role=tabpanel]')
  if (!panel) return
  finishEntrances(panel)
  // A callback runs after React writes the new nodes and before the frame is painted.
  const landing = new MutationObserver(() => finishEntrances(panel))
  landing.observe(panel, { childList: true, subtree: true })
  leave = () => {
    landing.disconnect()
    ACTS.forEach((act) => removeEventListener(act, leave, true))
    leave = () => {}
  }
  ACTS.forEach((act) => addEventListener(act, leave, true))
}

/** A screen arrives on mount and again whenever one of `keys` changes (the section, the topic, the book). */
export function useSettled(...keys) {
  useLayoutEffect(arrive, keys)
}
