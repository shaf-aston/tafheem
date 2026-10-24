/**
 * The chart's way to know how wide words draw: the real font, measured on a canvas, once it has loaded.
 *
 * Until then (and where there is no canvas) the estimate in lib/shell/pbsFit stands in, so a chart is always
 * drawn and then settles when the font arrives. The face is read from the element the words are drawn in, so
 * what is measured is what is shown.
 */
import { useLayoutEffect, useState } from 'react'

import { estimate } from './pbsFit'

const REFERENCE_PX = 100 // measured big and scaled down: a small size rounds its widths

/** `measure(text, weight)` in ems for `face` (a CSS font-family), or null with no canvas to measure on. */
function canvasMeasure(face) {
  const pen = document.createElement('canvas').getContext('2d')
  if (!pen) return null
  const seen = new Map()
  return (text, weight) => {
    const key = `${weight}|${text}`
    if (!seen.has(key)) {
      pen.font = `${weight} ${REFERENCE_PX}px ${face}`
      seen.set(key, pen.measureText(text).width / REFERENCE_PX)
    }
    return seen.get(key)
  }
}

const roughly = (text) => estimate(text)

/** A `measure(text, weight)` for words drawn inside `ref`, settling on the real font once `sample` (the words) can be drawn in it. */
export function useTextMeasure(ref, sample) {
  const [measure, setMeasure] = useState(() => roughly)

  useLayoutEffect(() => {
    const el = ref.current
    if (!el || !document.fonts) return undefined
    let live = true
    const settle = () => {
      if (live) setMeasure(() => canvasMeasure(getComputedStyle(el).fontFamily) ?? roughly)
    }
    const { fontFamily } = getComputedStyle(el)
    settle()
    // Asking for the face is what starts its download; the chart is re-measured once the words can be drawn in it.
    Promise.all([400, 700].map((weight) => document.fonts.load(`${weight} ${REFERENCE_PX}px ${fontFamily}`, sample)))
      .then(settle, settle)
    return () => { live = false }
  }, [ref, sample])

  return measure
}
