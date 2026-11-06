import { useEffect } from 'react'

import { keepInSight } from '../../lib/motion/scrollToEl'

/**
 * While somebody recites, the word they are on stays on screen.
 *
 * A page is taller than a phone, and the dock sits over its foot, so without
 * this the place slid under the dock a few lines in and the reciter recited
 * blind. Each time the place moves, the word (data-at on its button) is kept
 * between the header and the dock (keepInSight); while it is already there
 * nothing moves, so the page is still between words.
 */
export default function useFollowScroll(card, at, on) {
  useEffect(() => {
    if (!on || at == null || !card.current) return
    const word = card.current.querySelector(`[data-at="${at}"]`)
    const dock = document.querySelector('.reader-dock')
    keepInSight(word, dock ? dock.getBoundingClientRect().top : undefined)
  }, [card, at, on])
}
