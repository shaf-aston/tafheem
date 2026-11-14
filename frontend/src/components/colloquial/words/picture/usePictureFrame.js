// How the picture sits on the screen, for whatever stands beside it (Callout): its box in pixels,
// the drawing's extent in pixels, and the way between a place in the drawing and a pixel in the box.
import { useLayoutEffect, useState } from 'react'

/**
 * The picture as the screen has it: its box in pixels, the drawing's extent in pixels, and the
 * way between a place in the drawing and a pixel in the box. Null until it can be measured
 * (and in a test, where nothing is laid out), which is how the label stays away.
 */
function measure(svg, art) {
  const ctm = svg.getScreenCTM?.()
  const rect = svg.getBoundingClientRect?.()
  let box = null
  try { box = art?.getBBox?.() } catch { /* a drawing not yet on screen has no extent */ }
  if (!ctm || !ctm.a || !ctm.d || !rect?.width || !rect?.height || !box) return null
  const px = (x, y) => ({ x: ctm.a * x + ctm.e - rect.left, y: ctm.d * y + ctm.f - rect.top })
  const unpx = (x, y) => ({ x: (x + rect.left - ctm.e) / ctm.a, y: (y + rect.top - ctm.f) / ctm.d })
  const from = px(box.x, box.y)
  const to = px(box.x + box.width, box.y + box.height)
  return { box: { w: rect.width, h: rect.height }, art: { x0: from.x, y0: from.y, x1: to.x, y1: to.y }, scale: ctm.a, px, unpx }
}

/** Re-measured whenever the picture changes size (a resize, a rotated phone, the window's height). */
export default function usePictureFrame(svg, art, key) {
  const [frame, setFrame] = useState(null)
  useLayoutEffect(() => {
    const el = svg.current
    if (!el) return undefined
    const read = () => setFrame(measure(el, art.current))
    read()
    if (typeof ResizeObserver === 'undefined') return undefined
    const watch = new ResizeObserver(read)
    watch.observe(el)
    return () => watch.disconnect()
  }, [svg, art, key])
  return frame
}
