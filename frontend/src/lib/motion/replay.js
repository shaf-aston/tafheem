/**
 * Play an element's own CSS animations again from the start, at once.
 *
 * The one way to replay a move (the header ayah's gold sheen on hover): a second
 * copy of the keyframes under another name, swapped in by :hover, used to play the
 * pass twice, once as the pointer arrived and again as it left, when the name
 * swapped back. Here nothing in the stylesheet changes; the animation already
 * running is rewound. Its delay is dropped, since a replay answers the reader now.
 * With Animations off the durations are 0, so a replay is a no-op the reader never sees.
 */
export function replay(el) {
  for (const animation of el?.getAnimations?.() ?? []) {
    animation.effect?.updateTiming?.({ delay: 0 })
    animation.currentTime = 0
    animation.play()
  }
}
