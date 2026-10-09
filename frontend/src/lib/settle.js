/**
 * A panel shown by a tab switch arrives finished, not built in front of you.
 *
 * Each card's entrance (motion.css rise-in) plays when it first appears, and a
 * CSS animation also starts over whenever its element comes back from
 * display:none, which is how App hides a tab it keeps alive. So every switch
 * had a dozen or more cards rising at once. This jumps them to their end
 * before the frame is painted. Results that land later still rise: they are
 * new on screen, which is what the entrance is for.
 *
 * Only finite animations: a skeleton's shimmer loops forever, and finishing
 * one throws.
 */
export function finishEntrances(root) {
  if (!root?.getAnimations) return
  for (const animation of root.getAnimations({ subtree: true })) {
    if (Number.isFinite(animation.effect?.getComputedTiming().endTime)) animation.finish()
  }
}
