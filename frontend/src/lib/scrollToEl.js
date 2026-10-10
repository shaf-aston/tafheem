/**
 * The one way the app scrolls something into view: always a glide, unless the
 * reader asked for reduced motion or the target is far (motion.glide-screens). Presets name the intent, not the browser flag.
 */
import { useEffect } from 'react'

import theme from '../theme.json'

const ALIGN = { nearest: 'nearest', top: 'start', center: 'center' }

export function scrollToEl(el, align = 'nearest') {
  if (!el) return
  const far = Math.abs(el.getBoundingClientRect().top) > window.innerHeight * theme.motion['glide-screens']
  const reduce = far || globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  el.scrollIntoView({ block: ALIGN[align], behavior: reduce ? 'auto' : 'smooth' })
}

const MOVES = ['wheel', 'touchstart', 'keydown', 'pointerdown']

/**
 * A link landing on `el`: at the top at once (an arrival, not a glide), kept there while the page grows above it,
 * until the reader moves or motion['hold-ms'] passes. Returns the stop.
 */
export function holdAtTop(el) {
  if (!el) return () => {}
  const land = () => el.scrollIntoView({ block: 'start', behavior: 'instant' })
  land()
  const watch = new ResizeObserver(land)
  const stop = () => {
    watch.disconnect()
    clearTimeout(timer)
    MOVES.forEach((m) => removeEventListener(m, stop))
  }
  const timer = setTimeout(stop, theme.motion['hold-ms'])
  watch.observe(document.body)
  MOVES.forEach((m) => addEventListener(m, stop, { passive: true }))
  return stop
}

/** Back to the top of the page at once, as a fresh page would open. */
export function scrollToTop() {
  globalThis.scrollTo?.({ top: 0, behavior: 'instant' })
}

/**
 * A screen that replaces another inside a tab (a book's list after the books, a narrator's page) opens at
 * the top, as a fresh page would: the address does not change (lib/tabUrl), so the browser does not do it.
 * `keys` are what makes it a new screen (the book, the narrator); none means once, on mount.
 */
export function useOpenAtTop(...keys) {
  useEffect(scrollToTop, keys)
}
