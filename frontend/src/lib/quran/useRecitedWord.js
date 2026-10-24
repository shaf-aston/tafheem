/**
 * The word being recited right now in one ayah, or -1 when it is not playing.
 *
 * Every ayah on a page asks this, and only the one actually sounding gets an
 * answer: the rest compare the playing address against their own, see it is not
 * theirs, and settle back to -1. React drops a repeated -1, so a hundred silent
 * ayahs cost a comparison each and no redraw.
 *
 * `url`/`segments` are live props, recomputed from a query that can resolve
 * *after* a press: the reader opens, the address is still the EveryAyah guess,
 * the user presses play, and moments later the measured recording's address
 * arrives and replaces it in props. The sound already started under the old
 * address and is never restarted, so this ayah's session has to keep being
 * judged against whatever address was actually pressed, not the one props hold
 * now. `pinFor` is that rule, kept pure so the race can be proven without a
 * browser.
 */
import { useEffect, useRef, useState } from 'react'

import { watchProgress } from './ayahAudio'
import { wordAt } from './useRecitation'

/**
 * The (url, segments) this ayah's session is judged against.
 *
 * Locks onto `live` the moment it is heard playing, and holds that lock
 * through any later change in `live` until playback moves off this ayah
 * entirely (`pin` stops matching what's playing, so the next real match
 * re-pins fresh) - the moment a delayed fetch is not allowed to move the
 * goalposts mid-session.
 */
export function pinFor(playing, live, pin) {
  return playing === live.url ? live : pin
}

export function useRecitedWord(url, segments) {
  const [word, setWord] = useState(-1)
  const pinned = useRef(null)

  useEffect(() => {
    if (!url) {
      pinned.current = null
      return undefined
    }

    return watchProgress((playing, ms) => {
      pinned.current = pinFor(playing, { url, segments }, pinned.current)
      const pin = pinned.current
      setWord(pin && playing === pin.url ? wordAt(pin.segments, ms) : -1)
    })
  }, [url, segments])

  return word
}
