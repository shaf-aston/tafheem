/** The map's two timing hooks: how wide a vine may grow, and a tier's unlock. */
import { useEffect, useLayoutEffect, useRef, useState } from 'react'

import config from '../../grow.json'
import { motionOff as still } from '../../lib/motion'

const BEATS = config['unlock-ms']


/** The width of an element, kept current as the page resizes. */
export function useWidth() {
  const ref = useRef(null)
  const [width, setWidth] = useState(0)
  useLayoutEffect(() => {
    // Read once now, before the first paint, so the vine is there when its tab
    // is shown rather than growing a frame later.
    const box = ref.current
    const pad = getComputedStyle(box)
    setWidth(Math.floor(box.clientWidth - parseFloat(pad.paddingLeft) - parseFloat(pad.paddingRight)))
    const watch = new ResizeObserver(([entry]) => setWidth(Math.floor(entry.contentRect.width)))
    watch.observe(box)
    return () => watch.disconnect()
  }, [])
  return [ref, width]
}

/**
 * A tier opening, in beats (grow.json unlock-ms): 1 the gate shut, 2 it opens,
 * 3 the vine draws, 4 the steps appear. Starts on the frame `open` turns true,
 * told during render so the tier never flashes open before its gate. `plays`
 * changes per unlock so the tier's vine is drawn afresh and grows in.
 */
export function useUnlock(open) {
  const [was, setWas] = useState(open)
  const [beat, setBeat] = useState(0)
  const [plays, setPlays] = useState(0)
  if (open !== was) {
    setWas(open)
    if (open && !still()) {
      setPlays(plays + 1)
      setBeat(1)
    }
  }
  useEffect(() => {
    if (!beat) return undefined
    const wait = setTimeout(() => setBeat(beat < BEATS.length ? beat + 1 : 0), BEATS[beat - 1])
    return () => clearTimeout(wait)
  }, [beat])
  return { beat, plays }
}
