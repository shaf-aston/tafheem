/**
 * The one way the app scrolls something into view: always a glide, unless the
 * reader asked for reduced motion or the target is far (motion.glide-screens). Presets name the intent, not the browser flag.
 */
import theme from '../theme.json'

const ALIGN = { nearest: 'nearest', top: 'start', center: 'center' }

export function scrollToEl(el, align = 'nearest') {
  if (!el) return
  const far = Math.abs(el.getBoundingClientRect().top) > window.innerHeight * theme.motion['glide-screens']
  const reduce = far || globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  el.scrollIntoView({ block: ALIGN[align], behavior: reduce ? 'auto' : 'smooth' })
}

/** Back to the top of the page at once, as a fresh page would open. */
export function scrollToTop() {
  globalThis.scrollTo?.({ top: 0, behavior: 'instant' })
}
