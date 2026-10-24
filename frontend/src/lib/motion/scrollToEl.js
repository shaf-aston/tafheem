/**
 * The one way the app scrolls something into view: always a glide, unless the
 * reader turned motion off (lib/motion/motion) or the target is far (motion.glide-screens). Presets name the intent, not the browser flag.
 */
import { useEffect, useRef } from 'react'

import theme from '../../config/theme.json'
import { motionOff } from './motion'

const ALIGN = { nearest: 'nearest', top: 'start', center: 'center' }

export function scrollToEl(el, align = 'nearest') {
  if (!el) return
  const far = Math.abs(el.getBoundingClientRect().top) > window.innerHeight * theme.motion['glide-screens']
  const reduce = far || motionOff()
  el.scrollIntoView({ block: ALIGN[align], behavior: reduce ? 'auto' : 'smooth' })
}

/** Scroll the page to `top` the same way: a glide, unless motion is off or it is far. */
export function glideTo(top) {
  const far = Math.abs(top - globalThis.scrollY) > window.innerHeight * theme.motion['glide-screens']
  globalThis.scrollTo({ top, behavior: far || motionOff() ? 'auto' : 'smooth' })
}

const MOVES = ['wheel', 'touchstart', 'keydown', 'pointerdown']

/**
 * Keeps a place while the page grows under it: `land` runs now and on every
 * resize, until the reader moves or motion['hold-ms'] passes. Returns the stop.
 */
function hold(land) {
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

/** A link landing on `el`: at the top at once (an arrival, not a glide), held there as the page grows above it. */
export function holdAtTop(el) {
  if (!el) return () => {}
  return hold(() => el.scrollIntoView({ block: 'start', behavior: 'instant' }))
}

/** Back to `top`, held there while a tab coming back grows to its full height, which cut the place short. */
export function holdAt(top) {
  return hold(() => globalThis.scrollTo({ top, behavior: 'instant' }))
}

/** Back to the top of the page at once, as a fresh page would open. */
export function scrollToTop() {
  globalThis.scrollTo?.({ top: 0, behavior: 'instant' })
}

/**
 * A screen that replaces another inside a tab (a book's list after the books, a narrator's page) opens at
 * the top, as a fresh page would: the address does not change (lib/nav/tabUrl), so the browser does not do it,
 * `keys` are what makes it a new screen (the book, the narrator); none means once, on mount.
 */
export function useOpenAtTop(...keys) {
  useEffect(scrollToTop, keys)
}

/**
 * useOpenAtTop for screens one inside another (Grow: home 0 → world 1 → part 2 → lesson 3): going deeper opens at
 * the top; coming back up lands where the reader left that screen, as the browser's back would.
 */
export function useOpenAtTopKeepBack(key, depth) {
  const was = useRef({ depth, places: [] })
  useEffect(() => {
    const { depth: from, places } = was.current
    places[from] = globalThis.scrollY
    was.current.depth = depth
    if (depth < from && places[depth]) return holdAt(places[depth])
    scrollToTop()
  }, [key, depth])
}
