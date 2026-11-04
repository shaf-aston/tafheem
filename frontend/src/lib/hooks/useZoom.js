import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'

import { anchoredScroll, pinchedZoom, usePinch } from '../map/usePinch'

/** `zoom` moved `dir` steps (+1 in, -1 out), kept within [min, max], rounded so repeated steps do not drift (0.7 + 0.2 + 0.2). */
export const steppedZoom = (zoom, dir, { min, max, step }) =>
  Math.round(Math.min(max, Math.max(min, zoom + dir * step)) * 1000) / 1000

/** Scrolls `el` so the spot `a` ({ x, y, ratio }) stays where it was as the content grows by `a.ratio`; no spot is the frame's middle. */
function keepInPlace(el, { x = el.clientWidth / 2, y = el.clientHeight / 2, ratio }) {
  el.scrollLeft = anchoredScroll(el.scrollLeft, x, ratio)
  el.scrollTop = anchoredScroll(el.scrollTop, y, ratio)
}

/**
 * The zoom of a chart in a scrolling frame: a pinch, Ctrl/⌘ + wheel, the + − 0 keys, or whatever the ZoomBar calls.
 * `frame` is the frame's ref, `knobs` { min, max, step } (config/zoom.json). Every change keeps one spot of the chart
 * in place: between the fingers or under the pointer, else the frame's middle. `active` false leaves the frame alone.
 */
export function useZoom(frame, knobs, active = true) {
  const { min, max } = knobs
  const [zoom, setZoom] = useState(1)
  const [pinching, setPinching] = useState(false)
  const anchor = useRef(null) // { x, y, ratio }: the spot to keep put once the new zoom is drawn

  // `to` gives the next zoom from the last, already kept within [min, max] (pinchedZoom, steppedZoom, the slider's own range).
  const zoomTo = useCallback((to, x, y) => {
    setZoom((z) => {
      const next = to(z)
      anchor.current = { x, y, ratio: next / z }
      return next
    })
  }, [])

  const pinch = useCallback((by, x, y) => {
    setPinching(true)
    zoomTo((z) => pinchedZoom(z, by, min, max), x, y)
  }, [zoomTo, min, max])
  usePinch(frame, active ? pinch : null)

  const step = useCallback((dir, x, y) => zoomTo((z) => steppedZoom(z, dir, knobs), x, y), [zoomTo, knobs])
  const set = useCallback((to) => zoomTo(() => to), [zoomTo])
  const reset = useCallback(() => setZoom(1), [])

  useLayoutEffect(() => {
    const el = frame.current
    const a = anchor.current
    if (!el || !a) return
    keepInPlace(el, a)
    anchor.current = null
  }, [zoom, frame])

  // Ctrl/⌘ + wheel (a trackpad pinch arrives as one) zooms the chart, not the page; the keys work while the frame has focus.
  useEffect(() => {
    const el = frame.current
    if (!el || !active) return undefined
    const wheel = (event) => {
      if (!event.ctrlKey && !event.metaKey) return
      event.preventDefault()
      const box = el.getBoundingClientRect()
      zoomTo((z) => pinchedZoom(z, Math.exp(-event.deltaY / 200), min, max), event.clientX - box.left, event.clientY - box.top)
    }
    const key = (event) => {
      if (event.target !== el || event.ctrlKey || event.metaKey || event.altKey) return
      if (event.key === '+' || event.key === '=') step(1)
      else if (event.key === '-') step(-1)
      else if (event.key === '0') reset()
      else return
      event.preventDefault()
    }
    el.addEventListener('wheel', wheel, { passive: false })
    el.addEventListener('keydown', key)
    return () => {
      el.removeEventListener('wheel', wheel)
      el.removeEventListener('keydown', key)
    }
  }, [frame, active, zoomTo, step, reset, min, max])

  // The width of the drawing in the frame: the frame's own at 100%, never narrower than `minWidth` (a CSS length) draws it.
  const size = (minWidth) => ({
    width: `max(${zoom * 100}%, calc(${zoom} * ${minWidth}))`,
    transition: pinching ? 'none' : 'width calc(var(--motion-base-ms) * 1ms) ease',
  })

  return { zoom, size, endPinch: () => setPinching(false), step, set, reset }
}
