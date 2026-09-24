/**
 * The one way the app scrolls something into view: always a glide, unless the
 * reader asked for reduced motion. Presets name the intent, not the browser flag.
 */
const ALIGN = { nearest: 'nearest', top: 'start', center: 'center' }

export function scrollToEl(el, align = 'nearest') {
  if (!el) return
  const reduce = globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  el.scrollIntoView({ block: ALIGN[align], behavior: reduce ? 'auto' : 'smooth' })
}
