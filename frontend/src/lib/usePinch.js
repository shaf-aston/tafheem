import { useEffect } from 'react'

/**
 * Two fingers on `ref`'s element zoom what is inside it, not the page.
 *
 * Pinching the whole page inside a dialog is fragile on a phone: once zoomed,
 * a swipe goes to whichever scroller is under the finger, so the page often
 * will not move sideways. Here the element keeps one-finger scrolling
 * (touch-action pan-x pan-y, which also stops the page zooming over it) and a
 * pinch calls `onPinch(ratio, x, y)`: how much the fingers spread since the
 * last call, and their midpoint inside the element, so the caller can keep
 * that spot under the fingers. A null `onPinch` leaves the element alone.
 */

/** The new scroll offset that keeps the point `at` px into the view in place when the content grows by `ratio`. */
export function anchoredScroll(scroll, at, ratio) {
  return (scroll + at) * ratio - at
}

/** `zoom` times `by`, kept within [min, max]. */
export function pinchedZoom(zoom, by, min, max) {
  return Math.min(max, Math.max(min, zoom * by))
}

export function usePinch(ref, onPinch) {
  useEffect(() => {
    const el = ref.current
    if (!el || !onPinch) return undefined
    el.style.touchAction = 'pan-x pan-y'
    let last = null

    const spread = (touches) => Math.hypot(
      touches[0].clientX - touches[1].clientX,
      touches[0].clientY - touches[1].clientY,
    )
    const start = (event) => { last = event.touches.length === 2 ? spread(event.touches) : null }
    const move = (event) => {
      if (event.touches.length !== 2 || !last) return
      const now = spread(event.touches)
      const box = el.getBoundingClientRect()
      const x = (event.touches[0].clientX + event.touches[1].clientX) / 2 - box.left
      const y = (event.touches[0].clientY + event.touches[1].clientY) / 2 - box.top
      onPinch(now / last, x, y)
      last = now
    }
    const end = (event) => { if (event.touches.length < 2) last = null }

    el.addEventListener('touchstart', start, { passive: true })
    el.addEventListener('touchmove', move, { passive: true })
    el.addEventListener('touchend', end, { passive: true })
    el.addEventListener('touchcancel', end, { passive: true })
    return () => {
      el.style.touchAction = ''
      el.removeEventListener('touchstart', start)
      el.removeEventListener('touchmove', move)
      el.removeEventListener('touchend', end)
      el.removeEventListener('touchcancel', end)
    }
  }, [ref, onPinch])
}
