/**
 * One screen of a tab that steps down a tree (Grow: home → world → part → lesson;
 * Colloquial: dialects → units → topics → a topic). The one way such a screen
 * changes, so every tab that has them moves the same:
 *
 * - It opens at its top, as a fresh page would. The address does not reload the
 *   page, so the browser keeps the old scroll: a unit clicked low on a long list
 *   opened its topics with the reader left at their foot. Going back up a level
 *   lands where that level was left (lib/motion/scrollToEl useOpenAtTopKeepBack).
 * - It arrives as one piece: one short fade from motion.screen-from
 *   (styles/motion.css .screen), not each card rising in after the one before.
 *   Only a step inside the tab fades it; a tab opening already fades as a whole
 *   (shell/TabPane), and two fades at once would dim the page twice. The fade is
 *   dropped once played, so a hidden tab shown again does not replay it.
 *
 * `id` names the screen (a new one is a new screen), `depth` how far down the
 * tree it sits.
 */
import { useState } from 'react'

import { useOpenAtTopKeepBack } from '../../../lib/motion/scrollToEl'

export default function Screen({ id, depth, className = '', children }) {
  useOpenAtTopKeepBack(id, depth)
  // The screen whose arrival has been seen: the first is the tab's own.
  const [seen, setSeen] = useState(id)
  const arriving = id !== seen
  // Its own fade only: the moves of what is inside it bubble here too.
  const settle = (e) => { if (e.target === e.currentTarget) setSeen(id) }
  return (
    <div key={id} className={['screen', arriving && 'fade-in', className].filter(Boolean).join(' ')}
      onAnimationEnd={settle} onAnimationCancel={settle}>
      {children}
    </div>
  )
}
