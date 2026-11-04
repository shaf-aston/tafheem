import { scrollToEl } from '../../lib/motion/scrollToEl'

/** Marks a gap box you type into, so the page can find the next one. */
export const GAP = 'input[data-gap]'

/**
 * Enter in a gap goes on to the next gap, as Tab does, so a phone keeps its
 * keyboard up while a page is filled in. Off the last gap it puts the keyboard
 * away, which uncovers the button that marks the page. Put on the page that holds the gaps.
 */
export function nextGapOnEnter(event) {
  const gap = event.target
  // A word still being composed on a phone keyboard uses Enter to finish it.
  if (event.key !== 'Enter' || event.nativeEvent?.isComposing || !gap.matches?.(GAP)) return
  event.preventDefault()
  const gaps = [...event.currentTarget.querySelectorAll(GAP)]
  const next = gaps[gaps.indexOf(gap) + 1]
  if (!next) return gap.blur()
  next.focus({ preventScroll: true })
  scrollToEl(next, 'center')
}
