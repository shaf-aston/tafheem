/**
 * A sideways strip paged by two round arrows (.rail-arrow) that hide at its ends,
 * no scrollbar: the timeline's rail of cards and the tarkeeb chart.
 *
 * `start` and `end` are the strip's left and right ends as the screen has them.
 * `key` re-measures when what the strip holds changes.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

const PAGE = 0.8 // share of the visible width one arrow press moves
const EDGE = 4   // px of slack before an end counts as reached

export function useRail(key) {
  const strip = useRef(null)
  const [ends, setEnds] = useState({ start: true, end: false })

  const measure = useCallback(() => {
    const el = strip.current
    if (!el) return
    setEnds({ start: el.scrollLeft < EDGE, end: el.scrollLeft + el.clientWidth >= el.scrollWidth - EDGE })
  }, [])

  useEffect(() => {
    measure()
    window.addEventListener('resize', measure)
    return () => window.removeEventListener('resize', measure)
  }, [measure, key])

  const page = (dir) => strip.current.scrollBy({ left: dir * strip.current.clientWidth * PAGE, behavior: 'smooth' })

  return { strip, ends, measure, page }
}
