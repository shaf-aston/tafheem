/**
 * Whether a wait has lasted long enough to be worth telling the reader about.
 *
 * The sarf answer comes back in about a fifth of a second on this machine, so
 * the button changed to "Analysing…", skeletons took the place of the table,
 * and all of it was gone again before the eye had finished reading it. That
 * reads as a flash, not as progress: the page appears to break rather than to
 * work. The answer itself was never slow, only the saying so.
 *
 * So a wait is silent for its first quarter second and only then announced, and
 * once announced it is left up long enough to be read rather than snatched away
 * by an answer landing a moment later. Both numbers are in theme.json.
 *
 * What this must never do is hide a real wait. It delays the saying, it does
 * not shorten it: while the answer has not come, the wait is still on screen.
 * Whether a button can be pressed is a different question and stays with the
 * request itself, so a second press is refused during the silent quarter second
 * as it always was.
 */
import { useEffect, useRef, useState } from 'react'

import { motion } from '../theme'

const PATIENCE_MS = motion['patience-ms']
const HOLD_MS = motion['patience-hold-ms']

export function useSlowPending(pending) {
  const [shown, setShown] = useState(false)
  // When it went up, so the hold below is measured from that and not from the
  // moment the answer arrived.
  const shownAt = useRef(0)

  useEffect(() => {
    if (pending) {
      if (shown) return undefined
      const timer = setTimeout(() => {
        shownAt.current = Date.now()
        setShown(true)
      }, PATIENCE_MS)
      return () => clearTimeout(timer)
    }

    if (!shown) return undefined
    // Whatever is left of the hold, and never a negative wait. A hold already
    // served takes it down on the next tick rather than during this render.
    const left = Math.max(0, HOLD_MS - (Date.now() - shownAt.current))
    const timer = setTimeout(() => setShown(false), left)
    return () => clearTimeout(timer)
  }, [pending, shown])

  return shown
}
